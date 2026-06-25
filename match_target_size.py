"""
Cruza, por app e por tela, os achados de TAMANHO DE ALVO do a11y-argus e do
MotorEase, casando elementos por intersecao de bounds.

Novidades desta versao:
  - DEDUPLICA bounds identicos por tela (os dois lados repetem muito).
  - SEPARA os achados DEGENERADOS do argus (area zero: linhas/pontos de altura
    ou largura 0). Eles nao tem como casar por sobreposicao (interseccao sobre
    area zero = 0) e representam elementos do XML com bounds colapsado, sem
    icone visivel correspondente. Ficam num bucket proprio.

Pre-requisito (mesmo espaco de coordenadas): o MotorEase precisa ter rodado
sobre os MESMOS screenshots/XMLs do argus.

Join key entre as ferramentas: nome do arquivo do MotorEase (<hash>.png) == screen_id do argus.
Metrica: IoMin = interseccao / min(area_A, area_B). Reporta tambem IoU e dist. de centros.

Uso:
  python match_target_size.py <argus_root> <motorease_input> <reports_dir> <saida.json> [--iomin 0.5]
"""
import os, sys, json, glob, argparse, math

ARGUS_TS = {"Target Size Failure", "Target Size Failure (Minimum)"}
ME_TS    = {"Touch Target Size", "Visual Touch Target Size"}


def area(b):  return max(0, b[2]-b[0]) * max(0, b[3]-b[1])
def is_degenerate(b): return (b[2]-b[0]) <= 0 or (b[3]-b[1]) <= 0  # largura ou altura nula

def inter(a, b):
    x0,y0 = max(a[0],b[0]), max(a[1],b[1])
    x1,y1 = min(a[2],b[2]), min(a[3],b[3])
    return (x1-x0)*(y1-y0) if (x1>x0 and y1>y0) else 0
def iou(a,b):
    i=inter(a,b); u=area(a)+area(b)-i; return i/u if u>0 else 0.0
def iomin(a,b):
    i=inter(a,b); m=min(area(a),area(b)); return i/m if m>0 else 0.0
def center_dist(a,b):
    ca=((a[0]+a[2])/2,(a[1]+a[3])/2); cb=((b[0]+b[2])/2,(b[1]+b[3])/2)
    return round(math.hypot(ca[0]-cb[0], ca[1]-cb[1]),1)


def dedup(items):
    """Remove entradas com bounds identico, preservando a primeira."""
    seen, out = set(), []
    for it in items:
        key = tuple(it["bounds"])
        if key in seen: continue
        seen.add(key); out.append(it)
    return out


def argus_ts_by_screen(appdir):
    out = {}
    for ej in glob.glob(os.path.join(appdir,"results","result_*","errors.json")):
        try: d = json.load(open(ej, encoding="utf-8"))
        except Exception: continue
        if not isinstance(d, dict): continue
        sid = d.get("screen_id")
        if not sid: continue
        for e in d.get("errors", []):
            if e.get("type") in ARGUS_TS and e.get("bounds"):
                out.setdefault(sid, []).append({
                    "type": e["type"], "bounds": e["bounds"],
                    "resource_id": e.get("resource_id"), "class": e.get("class")})
    return {k: dedup(v) for k,v in out.items()}


def me_ts_report(reports_dir, app_folder):
    path = os.path.join(reports_dir, "AccessibilityReport_%s.json" % app_folder)
    if not os.path.exists(path): return None
    rep = json.load(open(path, encoding="utf-8"))
    by = {}
    for k, v in rep.items():
        h = k[:-4] if k.lower().endswith(".png") else k
        for e in v.get("errors", []):
            if e.get("guideline") in ME_TS and e.get("bounds"):
                by.setdefault(h, []).append({
                    "guideline": e["guideline"], "bounds": e["bounds"], "source": e.get("source")})
    return {k: dedup(v) for k,v in by.items()}


def match_screen(argus_list, me_list, thr):
    # separa degenerados (area zero) do argus: nao participam do matching por area
    argus_real = [a for a in argus_list if not is_degenerate(a["bounds"])]
    argus_degen = [a for a in argus_list if is_degenerate(a["bounds"])]
    me_real = [m for m in me_list if not is_degenerate(m["bounds"])]
    me_degen = [m for m in me_list if is_degenerate(m["bounds"])]

    cand = []
    for ai,a in enumerate(argus_real):
        for mi,m in enumerate(me_real):
            s = iomin(a["bounds"], m["bounds"])
            if s >= thr: cand.append((s,ai,mi))
    cand.sort(reverse=True)
    used_a, used_m, pairs = set(), set(), []
    for s,ai,mi in cand:
        if ai in used_a or mi in used_m: continue
        used_a.add(ai); used_m.add(mi)
        a,m = argus_real[ai], me_real[mi]
        pairs.append({"argus":a, "motorease":m, "iomin":round(s,3),
                      "iou":round(iou(a["bounds"],m["bounds"]),3),
                      "center_dist_px":center_dist(a["bounds"],m["bounds"])})
    argus_only = [a for i,a in enumerate(argus_real) if i not in used_a]
    me_only    = [m for i,m in enumerate(me_real) if i not in used_m]
    return pairs, argus_only, me_only, argus_degen, me_degen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("argus_root"); ap.add_argument("motorease_input")
    ap.add_argument("reports_dir"); ap.add_argument("out_path")
    ap.add_argument("--iomin", type=float, default=0.5)
    args = ap.parse_args()

    manifest = json.load(open(os.path.join(args.motorease_input,"_manifest.json"), encoding="utf-8"))
    result = {}
    tot = {"pares":0,"argus_only":0,"me_only":0,"argus_degenerados":0,"me_degenerados":0}

    for app_label, info in manifest.items():
        appdir = os.path.join(args.argus_root, info["argus_output_dir"])
        a_by = argus_ts_by_screen(appdir)
        m_by = me_ts_report(args.reports_dir, info["app_folder"])
        if m_by is None:
            print("AVISO: report do MotorEase ausente p/", app_label); m_by = {}
        app_out = {}
        for sid in sorted(set(a_by) | set(m_by)):
            pairs,a_only,m_only,a_deg,m_deg = match_screen(a_by.get(sid,[]), m_by.get(sid,[]), args.iomin)
            if not (pairs or a_only or m_only or a_deg or m_deg): continue
            app_out[sid] = {
                "correspondencias": pairs,
                "somente_argus": a_only,
                "somente_motorease": m_only,
                "argus_degenerados": a_deg,      # area zero, fora do matching
                "motorease_degenerados": m_deg,
                "resumo": {"pares":len(pairs), "argus_only":len(a_only), "me_only":len(m_only),
                           "argus_degen":len(a_deg), "me_degen":len(m_deg)},
            }
            for k in tot:
                tot[k] += app_out[sid]["resumo"].get(
                    {"pares":"pares","argus_only":"argus_only","me_only":"me_only",
                     "argus_degenerados":"argus_degen","me_degenerados":"me_degen"}[k], 0)
        result[app_label] = app_out
        np = sum(s["resumo"]["pares"] for s in app_out.values())
        print(f"{app_label}: telas={len(app_out)} | pares={np}")

    result["_total"] = tot
    json.dump(result, open(args.out_path,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\nTotal (apos dedup) -> correspondencias:", tot["pares"],
          "| so argus:", tot["argus_only"], "| so motorease:", tot["me_only"],
          "| argus degenerados:", tot["argus_degenerados"], "| me degenerados:", tot["me_degenerados"])
    print("Salvo em", args.out_path)


if __name__ == "__main__":
    main()

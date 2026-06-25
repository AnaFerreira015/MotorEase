"""
Prepara a entrada do MotorEase a partir da saida do a11y-argus / droidbot.

Para cada app listado no apks.csv, pega as telas que o argus avaliou
(screen_id em results/result_*/errors.json), localiza na variacao 'default'
o XML (ui_dump_default_<hash>.xml) e o screenshot correspondente, converte o
screenshot de jpg para png e copia o par para:

    <saida>/<app>/<hash>.png
    <saida>/<app>/<hash>.xml

Assim o nome do arquivo (o hash) e exatamente o screen_id do argus, o que
facilita o cruzamento depois. O MotorEase roda uma vez por subpasta de app.

Uso:
    python prepare_motorease_input.py <pasta_argus> <pasta_saida> [--variant default] [--all-screens]

    --all-screens : exporta todas as telas com par completo, nao so as que o argus avaliou.
"""
import os, sys, json, glob, csv, argparse, re
from PIL import Image


def safe_name(s):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('_')


def read_apks(argus_root):
    """Le apks.csv e devolve os nomes base dos apps (sem .apk)."""
    path = os.path.join(argus_root, "apks.csv")
    names = []
    if not os.path.exists(path):
        return names
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if not row:
                continue
            apk = row[0].strip().strip('"')
            if not apk:
                continue
            base = os.path.basename(apk.replace('\\', '/'))
            if base.lower().endswith('.apk'):
                base = base[:-4]
            names.append(base)
    return names


def argus_screen_ids(appdir):
    ids = set()
    for ej in glob.glob(os.path.join(appdir, "results", "result_*", "errors.json")):
        try:
            d = json.load(open(ej, encoding="utf-8"))
            if isinstance(d, dict) and d.get("screen_id"):
                ids.add(d["screen_id"])
        except Exception:
            pass
    return ids


def hash_to_xml(appdir, variant):
    out = {}
    for x in glob.glob(os.path.join(appdir, variant, "xmls", "ui_dump_%s_*.xml" % variant)):
        h = os.path.basename(x).replace("ui_dump_%s_" % variant, "").replace(".xml", "")
        out[h] = x
    return out


def hash_to_screenshot(appdir, variant):
    """Mapeia hash -> screenshot jpg usando os state files (com timestamp e por hash)."""
    out = {}
    states_dir = os.path.join(appdir, variant, "states")
    # 1) state com timestamp: state_<ts>.json -> state_str + screen_<ts>.jpg
    for sj in glob.glob(os.path.join(states_dir, "state_2*.json")):
        try:
            d = json.load(open(sj, encoding="utf-8"))
            h = d.get("state_str")
            ts = os.path.basename(sj).replace("state_", "").replace(".json", "")
            shot = os.path.join(states_dir, "screen_%s.jpg" % ts)
            if h and os.path.exists(shot):
                out.setdefault(h, shot)
        except Exception:
            pass
    # 2) fallback: state por hash -> usa a tag pra achar o screenshot
    for sj in glob.glob(os.path.join(states_dir, "state_%s_*.json" % variant)):
        try:
            d = json.load(open(sj, encoding="utf-8"))
            h = d.get("state_str")
            tag = d.get("tag")
            if h and h not in out and tag:
                shot = os.path.join(states_dir, "screen_%s.jpg" % tag)
                if os.path.exists(shot):
                    out[h] = shot
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("argus_root")
    ap.add_argument("out_dir")
    ap.add_argument("--variant", default="default")
    ap.add_argument("--all-screens", action="store_true")
    args = ap.parse_args()

    apks = read_apks(args.argus_root)
    os.makedirs(args.out_dir, exist_ok=True)
    manifest = {}

    all_app_dirs = [d for d in os.listdir(args.argus_root)
                    if d.startswith("output_dir_") and os.path.isdir(os.path.join(args.argus_root, d))]

    for app_dir_name in sorted(all_app_dirs):
        app_label = app_dir_name[len("output_dir_"):]
        # se houver apks.csv, so processa apps listados nele
        if apks and app_label not in apks:
            continue
        appdir = os.path.join(args.argus_root, app_dir_name)

        xmls = hash_to_xml(appdir, args.variant)
        shots = hash_to_screenshot(appdir, args.variant)
        argus_ids = argus_screen_ids(appdir)

        if args.all_screens:
            target = set(xmls) & set(shots)
        else:
            target = argus_ids & set(xmls) & set(shots)

        app_out = os.path.join(args.out_dir, safe_name(app_label))
        os.makedirs(app_out, exist_ok=True)

        exported, missing = [], []
        for h in sorted(target):
            try:
                Image.open(shots[h]).convert("RGB").save(os.path.join(app_out, h + ".png"))
                with open(xmls[h], "r", encoding="utf-8") as fi, \
                     open(os.path.join(app_out, h + ".xml"), "w", encoding="utf-8") as fo:
                    fo.write(fi.read())
                exported.append(h)
            except Exception as e:
                missing.append((h, str(e)))

        # telas que o argus avaliou mas nao deu pra exportar (sem xml ou sem screenshot)
        nao_exportadas = sorted(argus_ids - set(exported))

        manifest[app_label] = {
            "app_folder": safe_name(app_label),
            "argus_output_dir": app_dir_name,
            "exported_screens": exported,
            "argus_evaluated": sorted(argus_ids),
            "argus_screens_without_pair": nao_exportadas,
        }
        print("APP:", app_label)
        print("  exportadas:", len(exported), "| argus avaliou:", len(argus_ids),
              "| sem par:", len(nao_exportadas))

    with open(os.path.join(args.out_dir, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("\nManifesto salvo em", os.path.join(args.out_dir, "_manifest.json"))


if __name__ == "__main__":
    main()
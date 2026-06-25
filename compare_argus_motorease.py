"""
Cruza os achados do a11y-argus e do MotorEase para a MESMA tela de cada app.

Junta por hash (o screen_id do argus == o nome do arquivo gerado para o MotorEase).

Uso:
    python compare_argus_motorease.py <pasta_argus> <pasta_motorease_input> <pasta_reports_motorease> <saida.json>

  - <pasta_argus>: a pasta da saida do argus (com os output_dir_* e o apks.csv)
  - <pasta_motorease_input>: onde esta o _manifest.json gerado pelo prepare_motorease_input.py
  - <pasta_reports_motorease>: onde estao os AccessibilityReport_<app>.json (um por app)
  - <saida.json>: arquivo de comparacao a ser gerado
"""
import os, sys, json, glob


def load_argus_errors(appdir):
    """screen_id -> lista de erros do argus (compactados)."""
    by_screen = {}
    for ej in glob.glob(os.path.join(appdir, "results", "result_*", "errors.json")):
        try:
            d = json.load(open(ej, encoding="utf-8"))
        except Exception:
            continue
        sid = d.get("screen_id")
        if not sid:
            continue
        for e in d.get("errors", []):
            by_screen.setdefault(sid, []).append({
                "type": e.get("type"),
                "class": e.get("class"),
                "bounds": e.get("bounds"),
                "criterion": e.get("Success Criterion"),
                "level": e.get("Level"),
            })
    return by_screen


def load_motorease_report(reports_dir, app_folder):
    """Le AccessibilityReport_<app_folder>.json -> { '<hash>.png': {errors:[...]} }."""
    path = os.path.join(reports_dir, "AccessibilityReport_%s.json" % app_folder)
    if not os.path.exists(path):
        return None, path
    try:
        return json.load(open(path, encoding="utf-8")), path
    except Exception:
        return None, path


def main():
    argus_root, me_input, me_reports, out_path = sys.argv[1:5]
    manifest = json.load(open(os.path.join(me_input, "_manifest.json"), encoding="utf-8"))

    comparison = {}
    for app_label, info in manifest.items():
        appdir = os.path.join(argus_root, info["argus_output_dir"])
        argus_by_screen = load_argus_errors(appdir)
        me_report, me_path = load_motorease_report(me_reports, info["app_folder"])
        if me_report is None:
            print("AVISO: report do MotorEase nao encontrado para", app_label, "->", me_path)
            me_report = {}

        # normaliza chaves do MotorEase de '<hash>.png' para '<hash>'
        me_by_screen = {}
        for k, v in me_report.items():
            h = k[:-4] if k.lower().endswith(".png") else k
            me_by_screen[h] = v.get("errors", [])

        screens = set(argus_by_screen) | set(me_by_screen)
        app_block = {}
        for h in sorted(screens):
            argus_list = argus_by_screen.get(h, [])
            me_list = me_by_screen.get(h, [])
            app_block[h] = {
                "argus": argus_list,
                "motorease": me_list,
                "summary": {
                    "argus_count": len(argus_list),
                    "motorease_count": len(me_list),
                    "in_both_tools": bool(argus_list) and bool(me_list),
                }
            }
        comparison[app_label] = app_block
        print("APP:", app_label, "| telas comparadas:", len(app_block))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print("\nComparacao salva em", out_path)


if __name__ == "__main__":
    main()
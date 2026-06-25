# Diagnostico: por que o MotorEase saiu vazio para um app.
# Uso (na venv do MotorEase):
#   python diag_app.py "Drive Weather With Live Radar_APKPure"
import json, os, sys

BASE = r"C:\Projetos\MotorEase\ana_MotorEase\MotorEase"
app = sys.argv[1] if len(sys.argv) > 1 else "Drive Weather With Live Radar_APKPure"

inp = os.path.join(BASE, "motorease_input", app)
rep = os.path.join(BASE, "me_reports", "AccessibilityReport_" + app + ".json")

print("APP:", app)

print("\n[1] pasta de entrada do MotorEase:")
print("   ", inp)
if os.path.isdir(inp):
    files = os.listdir(inp)
    pngs = sorted(f for f in files if f.lower().endswith(".png"))
    xmls = sorted(f for f in files if f.lower().endswith(".xml"))
    print(f"    PNGs={len(pngs)}  XMLs={len(xmls)}")
    for f in pngs[:8]:
        print("     ", f)
else:
    print("    >>> NAO EXISTE. O prepare nao gerou entrada para este app.")

print("\n[2] relatorio do MotorEase:")
print("   ", rep)
if os.path.isfile(rep):
    sz = os.path.getsize(rep)
    data = json.load(open(rep, encoding="utf-8"))
    print(f"    tamanho={sz} bytes | telas no relatorio={len(data)}")
    total = 0
    for k, v in data.items():
        errs = v.get("errors", []) if isinstance(v, dict) else (v if isinstance(v, list) else [])
        total += len(errs)
    print(f"    total de erros somados={total}")
    for k in list(data.keys())[:8]:
        v = data[k]
        errs = v.get("errors", []) if isinstance(v, dict) else (v if isinstance(v, list) else [])
        print(f"      {k}: {len(errs)} erros")
    if total == 0:
        print("    >>> relatorio existe mas esta VAZIO (MotorEase rodou e nao achou nada,")
        print("        ou falhou ao carregar as imagens).")
else:
    print("    >>> NAO EXISTE. MotorEase nunca gerou saida para este app")
    print("        (ou foi pulado porque um relatorio antigo ja existia).")

print("\n[3] sugestao:")
print("    Apague o relatorio deste app em me_reports e rode o MotorEase")
print("    direto nele, observando o console:")
print('      python "%s" "%s"' % (os.path.join(BASE,"Code","MotorEase.py"), inp))

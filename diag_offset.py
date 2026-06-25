# Compara a dimensao do PNG (o que o MotorEase enxerga) com a dimensao que o
# XML do argus declara, para detectar offset ou escala entre os dois espacos.
#
# Uso (na venv do MotorEase):
#   python diag_offset.py "Drive_Weather_With_Live_Radar_APKPure"
#   python diag_offset.py "Drive_Weather_With_Live_Radar_APKPure" d5ab581938cbd3f36cf915e17f1ac67a
#
# Sem o segundo argumento ele pega a primeira tela da pasta.
import os, sys, re, struct, glob

BASE = r"C:\Projetos\MotorEase\ana_MotorEase\MotorEase"
app  = sys.argv[1] if len(sys.argv) > 1 else "Drive_Weather_With_Live_Radar_APKPure"
hint = sys.argv[2] if len(sys.argv) > 2 else None

folder = os.path.join(BASE, "motorease_input", app)
if not os.path.isdir(folder):
    print("Pasta nao existe:", folder); sys.exit(1)

# escolhe a tela
pngs = sorted(glob.glob(os.path.join(folder, "*.png")))
if not pngs:
    print("Nenhum PNG em", folder); sys.exit(1)
png = None
if hint:
    for p in pngs:
        if hint in os.path.basename(p): png = p; break
    if png is None:
        print("Nao achei PNG com", hint, "- usando o primeiro");
png = png or pngs[0]
base = os.path.splitext(png)[0]
xml  = base + ".xml"

# dimensao do PNG (le o header IHDR, sem precisar de PIL)
def png_size(path):
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h

# dimensao declarada pelo XML: maior x2/y2 entre todos os bounds
def xml_size(path):
    if not os.path.isfile(path): return None
    txt = open(path, encoding="utf-8", errors="replace").read()
    xs=[]; ys=[]
    for m in re.finditer(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', txt):
        x1,y1,x2,y2 = map(int, m.groups())
        xs.append(x2); ys.append(y2)
    if not xs: return None
    return max(xs), max(ys)

ps = png_size(png)
xs = xml_size(xml)

print("APP :", app)
print("TELA:", os.path.basename(base))
print()
print("PNG  (o que o MotorEase ve) :", f"{ps[0]} x {ps[1]}" if ps else "nao foi possivel ler")
print("XML  (o que o argus declara):", f"{xs[0]} x {xs[1]}" if xs else "nao encontrado / sem bounds")
print()
if ps and xs:
    sx = ps[0]/xs[0]; sy = ps[1]/xs[1]
    print(f"Razao largura PNG/XML = {sx:.3f}")
    print(f"Razao altura  PNG/XML = {sy:.3f}")
    print()
    if abs(sx-1)<0.02 and abs(sy-1)<0.02:
        print(">>> MESMA dimensao. Nao ha escala nem offset de tamanho.")
        print("    O desalinhamento vem de outro lugar (granularidade da deteccao).")
    elif abs(sx-sy)<0.02:
        print(f">>> ESCALA uniforme de ~{sx:.3f}x. O MotorEase esta num espaco maior/menor.")
        print("    Da para corrigir multiplicando os bounds de um lado por esse fator.")
    else:
        dh = ps[1]-xs[1]
        print(f">>> Larguras e alturas escalam diferente. Diferenca de altura = {dh} px.")
        print("    Tipico de status bar / barra de navegacao incluida em um lado so.")
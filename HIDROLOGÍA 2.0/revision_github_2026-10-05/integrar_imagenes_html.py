from pathlib import Path
import re,base64,json,hashlib
ROOT=Path(__file__).resolve().parent
html=ROOT/'informe_interactivo.html'
text=html.read_text(encoding='utf-8')
fixed=[]
def embed(m):
    source=m.group(2)
    if source.startswith(('data:','http:','https:')):return m.group(0)
    image=ROOT/source.split('?')[0]
    if not image.is_file():raise FileNotFoundError(image)
    mime={'.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'}[image.suffix.lower()]
    fixed.append(source)
    return m.group(1)+'data:'+mime+';base64,'+base64.b64encode(image.read_bytes()).decode('ascii')+m.group(3)
updated=re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")',embed,text)
if fixed:
    backup=ROOT/'informe_interactivo_original_github.html'
    if not backup.exists():backup.write_text(text,encoding='utf-8')
    html.write_text(updated,encoding='utf-8')
print('Imágenes integradas:',fixed)
assert not [s for s in re.findall(r'<img[^>]*src="([^"]+)"',updated) if not s.startswith(('data:','http:','https:'))]

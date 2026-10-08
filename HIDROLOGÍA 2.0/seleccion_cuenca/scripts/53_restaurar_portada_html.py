"""Repara el envoltorio HTML de la portada sin regenerar los análisis."""
from pathlib import Path
import shutil,hashlib,json

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
ROOT=DOCS.parents[3];OUT=DOCS/'revision_portada';OUT.mkdir(exist_ok=True)
p=DOCS/'informe_interactivo.html'
h=p.read_text(encoding='utf-8')
backup=OUT/'informe_antes_reparacion.html'
if not backup.exists():shutil.copy2(p,backup)
before_scripts=[]
import re
for s in re.findall(r'<script[^>]*>.*?</script>',h,re.S):before_scripts.append(hashlib.sha256(s.encode()).hexdigest())
h=h[h.lower().index('<!doctype'):]
css='''<style id="portada-institucional-layout">
.portada-institucional{max-width:1100px;margin:28px auto;padding:46px 24px;background:white;border:1px solid #dce5e9;border-top:5px solid #94b43b;border-radius:10px;text-align:center;box-sizing:border-box}
.portada-institucional .escudo{width:148px;height:212px;overflow:hidden;position:relative;margin:0 auto 22px}
.portada-institucional .escudo img{position:absolute;width:897.88px;max-width:none;height:auto;left:-381.42px;top:-67.32px}
.portada-institucional h1{margin:34px 0 14px;font-size:clamp(28px,4vw,42px)}
.portada-institucional .autores{margin:32px 0;line-height:1.9}
.portada-institucional .institucion{font-size:23px;font-weight:700}
@media(max-width:600px){.portada-institucional{margin:12px 10px;padding:26px 16px}.portada-institucional .institucion{font-size:20px}}
@media print{.portada-institucional{break-after:page;box-shadow:none;border:0}}
</style>'''
if 'id="portada-institucional-layout"' not in h:
    if '</head>' in h:h=h.replace('</head>',css+'</head>',1)
    else:
        pos=h.index('<h1>');h=h[:pos]+css+'\n</head><body>\n'+h[pos:]
if '<header class="portada-institucional"' not in h:
    pos=h.index('<h1>');h=h[:pos]+'<!-- PORTADA_INSTITUCIONAL_INICIO --><header class="portada-institucional" aria-label="Portada del informe">\n'+h[pos:]
assert all(h.count(t)==1 for t in ['<head>','</head>','<body>','</body>','<header class="portada-institucional"','</header>'])
after_scripts=[hashlib.sha256(s.encode()).hexdigest() for s in re.findall(r'<script[^>]*>.*?</script>',h,re.S)]
assert before_scripts==after_scripts,'Los análisis JavaScript cambiaron'
p.write_text(h,encoding='utf-8');shutil.copy2(p,ROOT/'Informe_Hidrologia_interactivo.html')
(OUT/'reparacion.json').write_text(json.dumps({'cause':'Missing head/body/header opening and cover CSS, stray text before doctype','scripts_preserved':len(after_scripts),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
print('Portada restaurada; scripts y datos conservados:',len(after_scripts))

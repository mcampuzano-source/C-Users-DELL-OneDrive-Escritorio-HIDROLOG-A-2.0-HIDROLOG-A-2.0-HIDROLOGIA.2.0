from pathlib import Path
import argparse,os,sys,subprocess,shutil,re,base64

BASE=Path(__file__).resolve().parents[1]
DOC=BASE/'la_vieja/documentos'
p=argparse.ArgumentParser();p.add_argument('--tectonic');args=p.parse_args()
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
for name in ['32_comparar_chirps_imerg.py','34_integrar_modelos_informes.py']:
    subprocess.run([sys.executable,str(BASE/'scripts'/name)],check=True,env=env)
h=DOC/'informe_interactivo.html';text=h.read_text(encoding='utf-8')
def embed(m):
    source=m.group(2)
    if source.startswith(('data:','http:','https:')):return m.group(0)
    image=DOC/source.split('?')[0]
    if not image.exists():raise FileNotFoundError(image)
    mime={'.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'}[image.suffix.lower()]
    return m.group(1)+'data:'+mime+';base64,'+base64.b64encode(image.read_bytes()).decode()+m.group(3)
text=re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")',embed,text);h.write_text(text,encoding='utf-8')
compiler=args.tectonic or shutil.which('tectonic') or str(BASE/'herramientas/tectonic/tectonic.exe')
subprocess.run([compiler,'--keep-logs','informe_ordenado.tex'],cwd=DOC/'latex',check=True,env=env)
shutil.copy2(DOC/'latex/informe_ordenado.pdf',DOC/'informe_actualizado.pdf')
print('PDF y HTML actualizados. La reserva 2017-2022 permanece sin evaluar.')

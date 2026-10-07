from pathlib import Path
import argparse,os,sys,subprocess,shutil

BASE=Path(__file__).resolve().parents[1]
DOC=BASE/'la_vieja/documentos'
parser=argparse.ArgumentParser();parser.add_argument('--tectonic');args=parser.parse_args()
env=os.environ.copy();env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
# Evaluate persisted models; do not rerun development or choose new parameters.
subprocess.run([sys.executable,str(BASE/'scripts/36_evaluar_reserva.py')],check=True,env=env)
compiler=args.tectonic or shutil.which('tectonic') or str(BASE/'herramientas/tectonic/tectonic.exe')
subprocess.run([compiler,'--keep-logs','informe_ordenado.tex'],cwd=DOC/'latex',check=True,env=env)
shutil.copy2(DOC/'latex/informe_ordenado.pdf',DOC/'informe_actualizado.pdf')
print('Apartado 2.3 incorporado en PDF y HTML sin reajustar modelos.')

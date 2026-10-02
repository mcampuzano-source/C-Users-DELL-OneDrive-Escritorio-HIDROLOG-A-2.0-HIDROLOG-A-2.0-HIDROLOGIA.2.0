"""Compila el documento editable con Tectonic instalado en la carpeta local."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
engine=ROOT/'herramientas'/'tectonic'/'tectonic.exe'
folder=ROOT/'la_vieja'/'documentos'/'latex'
if not engine.exists():
    raise FileNotFoundError('Instalar Tectonic en herramientas/tectonic o compilar informe.tex con una distribución LaTeX.')
subprocess.run([str(engine),'informe.tex','--keep-logs'],cwd=folder,check=True)
if not (folder/'informe.pdf').exists():
    raise RuntimeError('No se generó informe.pdf')
print(folder/'informe.pdf')

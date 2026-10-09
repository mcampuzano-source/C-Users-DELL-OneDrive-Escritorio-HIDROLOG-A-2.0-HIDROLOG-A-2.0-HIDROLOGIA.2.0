"""Ejecuta este archivo para generar el PDF completo de 486 páginas.

Necesita el proyecto completo descargado. Instala PyMuPDF automáticamente
si falta. La salida se guarda en HIDROLOGÍA 2.0/seleccion_cuenca/salida_informes/.
"""
from pathlib import Path
import importlib.util
import subprocess
import sys

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[2]
PROJECT = REPOSITORY / "HIDROLOGÍA 2.0" / "seleccion_cuenca"
SCRIPTS = PROJECT / "scripts"
if not (SCRIPTS / "informes_actuales.py").is_file():
    raise SystemExit("Descarga el proyecto completo: falta scripts/informes_actuales.py.")
if importlib.util.find_spec("fitz") is None:
    print("Instalando la dependencia PyMuPDF para generar el PDF...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                    str(PROJECT / "requirements_informes.txt")], check=True)
sys.path.insert(0, str(SCRIPTS))
from informes_actuales import main

if __name__ == "__main__":
    main(default="pdf")

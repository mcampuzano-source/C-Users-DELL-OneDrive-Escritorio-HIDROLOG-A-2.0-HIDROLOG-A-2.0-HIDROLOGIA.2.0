"""Ejecuta este archivo para generar el informe interactivo completo.

Necesita el proyecto completo descargado. La salida se guarda en
HIDROLOGÍA 2.0/seleccion_cuenca/salida_informes/.
"""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "HIDROLOGÍA 2.0" / "seleccion_cuenca" / "scripts"
if not (SCRIPTS / "informes_actuales.py").is_file():
    raise SystemExit("Descarga el proyecto completo: falta scripts/informes_actuales.py.")
sys.path.insert(0, str(SCRIPTS))
from informes_actuales import main

if __name__ == "__main__":
    main(default="html")

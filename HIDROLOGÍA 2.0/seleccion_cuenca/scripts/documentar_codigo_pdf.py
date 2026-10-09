"""Crea la vista del código ejecutable del PDF completo actualizado."""
from pathlib import Path
from html import escape
import hashlib

PROJECT = Path(__file__).resolve().parents[1]


def main():
    names = ["../Códigos python/Generar informe PDF.py", "scripts/generar_informe_pdf.py", "scripts/informes_actuales.py",
             "scripts/ejecutar_informes.py", "requirements_informes.txt",
             "fuentes_informes/manifest.json", "EJECUTAR_INFORMES.md"]
    blocks = []
    for name in names:
        path = PROJECT / name
        code = path.read_text(encoding="utf-8-sig")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        blocks.append(f'<section><h2>{escape(name)}</h2><p>SHA256: {digest}</p>'
                      f'<details><summary>Ver código</summary><pre>{escape(code)}</pre></details></section>')
    page = '''<!doctype html><html lang="es"><meta charset="utf-8">
<title>Código del informe PDF actualizado</title>
<style>body{font-family:system-ui;max-width:1100px;margin:30px auto;padding:0 20px}
pre{overflow:auto;background:#f1f4f8;padding:18px}section{margin:24px 0}</style>
<h1>Código del informe PDF actualizado</h1>
<p>Entrada principal: <code>Códigos python/Generar informe PDF.py</code>, dentro de HIDROLOGÍA 2.0.
Ejecute ese archivo directamente con Python.
Reconstruye la edición publicada completa de 486 páginas desde sus fuentes verificadas.
No recalcula las series ni los modelos históricos.</p>
<p><a href="EJECUTAR_INFORMES.md">Instrucciones de instalación y ejecución</a></p>'''
    (PROJECT / "Codigo_informe_PDF_actualizado.html").write_text(
        page + "".join(blocks) + "</html>", encoding="utf-8")
    print("Código documentado del PDF actualizado.")


if __name__ == "__main__":
    main()

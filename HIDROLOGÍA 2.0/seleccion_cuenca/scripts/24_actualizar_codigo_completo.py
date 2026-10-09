"""Actualiza la vista de código completa y conserva su registro histórico."""
from pathlib import Path
from html import escape
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
PAGE = ROOT / 'Codigo_desde_el_inicio.html'
START = '<!-- CODIGO_COMPLETO_ACTUAL_INICIO -->'
END = '<!-- CODIGO_COMPLETO_ACTUAL_FIN -->'


def main():
    previous = PAGE.read_text(encoding='utf-8')
    previous = re.sub(re.escape(START) + '.*?' + re.escape(END), '', previous, flags=re.S)
    files = list((ROOT / 'scripts').glob('*.py'))
    files += list((ROOT.parent / 'Códigos python').glob('*.py'))
    files += [p for p in WORKSPACE.glob('download_files_GPM_3IMERGM_07*.py')]
    files += list((DOC / 'latex' / 'secciones').glob('*.tex'))
    files += [DOC / 'latex' / 'informe.tex', DOC / 'latex' / 'informe_ordenado.tex']
    files += list((DOC / 'imerg_poligono').glob('*.tex'))
    files += list((DOC / 'disponibilidad_mensual').glob('*.tex'))
    files += list(DOC.glob('apartado_*/*.tex'))
    files += [ROOT / 'requirements_informes.txt', ROOT / 'fuentes_informes' / 'manifest.json']
    files += [DOC / 'informe_interactivo.html']
    files = sorted(set(p for p in files if p.is_file()), key=lambda p: p.relative_to(WORKSPACE).as_posix())
    nav, sections = [], []
    for index, path in enumerate(files, 1):
        name = path.relative_to(WORKSPACE).as_posix()
        code = path.read_text(encoding='utf-8-sig')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        anchor = f'codigo-actual-{index:02d}'
        nav.append(f'<a href="#{anchor}">{escape(path.name)}</a>')
        if path.stat().st_size > 2_000_000:
            import os
            link = Path(os.path.relpath(path, ROOT)).as_posix()
            sections.append(f'<section id="{anchor}"><h3>{escape(name)}</h3>'
                            f'<p>SHA256: <code>{digest}</code></p>'
                            f'<p><a href="{escape(link, quote=True)}" download>Descargar el código completo</a>. '
                            'La fuente se enlaza íntegra para no duplicar archivos grandes en esta página.</p></section>')
            continue
        sections.append(f'<section id="{anchor}"><h3>{escape(name)}</h3><p>SHA256: <code>{digest}</code></p>'
                        f'<details><summary>Ver código completo de {escape(path.name)}</summary>'
                        f'<pre><code>{escape(code)}</code></pre></details></section>')
    current = START + '''<section id="estado-actual-codigo"><h2>Trabajo completo: código y fuentes actuales</h2>
<p>Actualizado el 8 de octubre de 2026. Esta sección reúne las versiones actuales de todos los scripts de selección,
descarga, auditoría, análisis y creación de informes, las fuentes LaTeX y el HTML interactivo completo.
Los pasos históricos que aparecen después se conservan íntegros; sus notas sobre IMERG pendiente describen una etapa anterior.</p>
<p>Estado actual: 300 meses IMERG V07B de enero de 1998 a diciembre de 2022 procesados sobre el polígono de La Vieja,
42 celdas intersectadas y ponderación geodésica. Las comparaciones de distribución usan 285 meses comunes.
Se mantienen separados CHIRPS, IMERG del polígono, IMERG histórico de caja, MSWX y ERA5-Land.</p>
<p>El script 21 organiza los informes según la guía y centra las tablas; el 22 calcula IMERG y genera series,
estadísticos, histogramas y cajas; el 23 amplía la descripción del segundo inciso y la resume en dos párrafos.
El contraste de los extremos y sus meses vecinos está en contraste_extremos.tex y se integra en el PDF mediante el script 21.
El script 25 incorpora al informe interactivo la tabla y dos párrafos del contraste de extremos. Las correcciones y el diseño del interactivo
pueden consultarse en su código completo, incluido abajo.</p>
<p>Las dos entradas fáciles de localizar están en la carpeta HIDROLOGÍA 2.0/Códigos python:
Generar informe interactivo.py y Generar informe PDF.py. Ejecutar el archivo correspondiente
genera directamente su informe, sin recorrer los scripts históricos.
Para reconstruir ambos juntos, ejecutar scripts/ejecutar_informes.py.
Los programas generar_informe_interactivo.py y generar_informe_pdf.py generan cada informe por separado.
Las fuentes portables están en fuentes_informes y sus huellas se verifican antes de ejecutar.
El PDF incluye 486 páginas. Este flujo reproduce la edición integrada; no recalcula observaciones ni modelos.
Los scripts numerados anteriores conservan los análisis históricos y no deben ejecutarse todos en secuencia
para actualizar la edición publicada. Véase EJECUTAR_INFORMES.md para instalación y ejecución.
Para actualizar esta vista de código al terminar, ejecutar el script 24.
La generación de esta página solo lee las fuentes: no ejecuta descargas ni recalcula datos.
Los HDF5 originales permanecen locales; GitHub contiene los scripts, informes y resultados procesados.</p>
<p>Fuentes actuales reproducibles:</p><nav>''' + ''.join(nav) + '</nav>' + ''.join(sections) + '</section>' + END
    # Añadir después del índice histórico, sin sustituir ninguno de sus bloques.
    location = previous.index('</nav>') + len('</nav>')
    updated = previous[:location] + current + previous[location:]
    PAGE.write_text(updated, encoding='utf-8')
    # Verificar que la incorporación conserva el documento histórico completo.
    assert re.sub(re.escape(START) + '.*?' + re.escape(END), '', updated, flags=re.S) == previous
    assert len(files) >= 25
    print(f'Código completo actualizado: {len(files)} fuentes; historial conservado.')


if __name__ == '__main__':
    main()

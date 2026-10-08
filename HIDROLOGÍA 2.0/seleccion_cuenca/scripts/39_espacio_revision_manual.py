"""Reserva el espacio autorizado para la revisión manual pendiente."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
TEXT = ('Pendiente de documentar la revisión manual de enero de 1998: archivo utilizado, '
        'comprobación de los 31 días válidos, suma de precipitación, promedio del caudal, '
        'conversión a escorrentía, resultados obtenidos y comparación con el informe. '
        'La conversión y el registro final de la comprobación quedan pendientes.')


def main():
    path=DOC/'informe_interactivo.html'
    text=path.read_text(encoding='utf-8')
    if 'id="revision-manual-pendiente"' not in text:
        start=text.index('id="faltantes"');end=text.index('</section>',start)
        block='<div id="revision-manual-pendiente"><h3>Revisión manual de agregación y conversión</h3><p>'+TEXT+'</p></div>'
        path.write_text(text[:end]+block+text[end:],encoding='utf-8')
    for path in [DOC/'latex/secciones/02_control_faltantes.tex',DOC/'latex/informe_ordenado.tex']:
        text=path.read_text(encoding='utf-8')
        if '% REVISION_MANUAL_PENDIENTE' in text: continue
        heading=r'\subsection{Revisión manual de agregación y conversión}' if path.name=='02_control_faltantes.tex' else r'\subsubsection*{Revisión manual de agregación y conversión}'
        block='\n% REVISION_MANUAL_PENDIENTE\n'+heading+'\n'+TEXT+'\n'
        if path.name=='02_control_faltantes.tex': text+=block
        else:
            start=text.index(r'\subsubsection*{Criterio de completitud}')
            end=text.index(r'\subsection{Climatología, variabilidad y explicación física}',start)
            text=text[:end]+block+text[end:]
        path.write_text(text,encoding='utf-8')


if __name__=='__main__': main()

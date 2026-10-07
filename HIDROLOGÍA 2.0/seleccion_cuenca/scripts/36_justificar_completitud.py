"""Explica el criterio existente sin cambiar datos ni resultados."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
JUSTIFICATION = ('Se exige el 100 % de días válidos para que la lluvia acumulada y el caudal medio representen el mes completo, '
                 'evitando presentar sumas parciales de lluvia como totales mensuales. Este mismo criterio se mantiene '
                 'en los análisis de CHIRPS y caudal; R conserva los mismos meses válidos que Q porque se calcula a partir de él.')


def main():
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    if JUSTIFICATION not in text:
        start = text.index('id="faltantes"')
        end = text.index('</p>', start)
        text = text[:end+4]+'<p>'+JUSTIFICATION+'</p>'+text[end+4:]
        html.write_text(text, encoding='utf-8')
    justification_tex = JUSTIFICATION.replace('%',r'\%')
    for path in [DOC/'latex'/'secciones'/'02_control_faltantes.tex', DOC/'latex'/'informe_ordenado.tex']:
        text = path.read_text(encoding='utf-8')
        if justification_tex not in text:
            anchor = r'\subsubsection*{Criterio de completitud}' if path.name=='informe_ordenado.tex' else r'\subsection{Criterio de completitud}'
            assert text.count(anchor)==1
            path.write_text(text.replace(anchor,anchor+'\n'+justification_tex+'\n'),encoding='utf-8')


if __name__=='__main__': main()

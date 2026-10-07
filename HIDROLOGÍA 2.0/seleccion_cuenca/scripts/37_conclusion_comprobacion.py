"""Incorpora la conclusión acordada sobre los controles revisados del 1.4."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
CONCLUSION = ('Durante la comprobación de las series revisadas no se encontraron inconsistencias en las fechas, duplicados, unidades ni valores negativos de lluvia, caudal o escorrentía. '
              'No fue necesario corregir datos por estos criterios. Sin embargo, los archivos tabulares revisados de CAMELS y lluvia local no incluyen banderas explícitas de calidad, '
              'lo que limita la validación y no permite garantizar la exactitud de todos los valores.')


def main():
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b='<!-- CONCLUSION_COMPROBACION_INICIO -->','<!-- CONCLUSION_COMPROBACION_FIN -->'
    original = re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    start = original.index('id="faltantes"')
    end = original.index('</section>',start)
    block=a+'<h3>Conclusión de la comprobación de datos</h3><p>'+CONCLUSION+'</p>'+b
    updated=original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    a,b='% CONCLUSION_COMPROBACION_INICIO','% CONCLUSION_COMPROBCACION_FIN'
    for path in [DOC/'latex/secciones/02_control_faltantes.tex',DOC/'latex/informe_ordenado.tex']:
        text=path.read_text(encoding='utf-8')
        text=re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
        heading=r'\subsection{Conclusión de la comprobación de datos}' if path.name=='02_control_faltantes.tex' else r'\subsubsection*{Conclusión de la comprobación de datos}'
        block='\n'+a+'\n'+heading+'\n'+CONCLUSION+'\n'+b+'\n'
        if path.name=='02_control_faltantes.tex':
            text+=block
        else:
            start=text.index(r'\subsection{Usar la exploración como control de calidad}')
            end=text.index(r'\subsection{Climatología, variabilidad y explicación física}',start)
            text=text[:end]+block+text[end:]
        path.write_text(text,encoding='utf-8')


if __name__=='__main__': main()

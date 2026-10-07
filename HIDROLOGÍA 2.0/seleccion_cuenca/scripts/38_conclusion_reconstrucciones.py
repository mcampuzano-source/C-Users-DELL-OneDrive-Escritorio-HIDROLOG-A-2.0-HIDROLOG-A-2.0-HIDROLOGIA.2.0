"""Añade los dos párrafos aprobados sobre reconstrucciones y estimaciones."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
PARAGRAPHS = [
    ('Reconstrucción del calendario y ajuste de la geometría de las celdas:', 'se completaron las fechas y se ajustaron los límites de las celdas IMERG, sin rellenar los vacíos ni modificar los valores originales.'),
    ('Estimaciones de modelos y escenario hipotético P95:', 'se generaron valores para evaluar los modelos del punto 2 y la influencia de los extremos. Estos resultados permanecen separados y no sustituyen ni rellenan los datos originales.'),
]


def main():
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b='<!-- CONCLUSION_RECONSTRUCCIONES_INICIO -->','<!-- CONCLUSION_RECONSTRUCCIONES_FIN -->'
    original=re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    start=original.index('id="faltantes"');end=original.index('</section>',start)
    block=a+'<h3>Conclusión sobre reconstrucciones y estimaciones</h3>'
    block+=''.join('<p><strong>'+title+'</strong> '+body+'</p>' for title,body in PARAGRAPHS)+b
    updated=original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    a,b='% CONCLUSION_RECONSTRUCCIONES_INICIO','% CONCLUSION_RECONSTRUCCIONES_FIN'
    for path in [DOC/'latex/secciones/02_control_faltantes.tex',DOC/'latex/informe_ordenado.tex']:
        text=path.read_text(encoding='utf-8')
        text=re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
        heading=r'\subsection{Conclusión sobre reconstrucciones y estimaciones}' if path.name=='02_control_faltantes.tex' else r'\subsubsection*{Conclusión sobre reconstrucciones y estimaciones}'
        block='\n'+a+'\n'+heading+'\n'
        block+='\n\n'.join(r'\textbf{'+title+'} '+body for title,body in PARAGRAPHS)+'\n'+b+'\n'
        if path.name=='02_control_faltantes.tex': text+=block
        else:
            start=text.index(r'\subsection{Usar la exploración como control de calidad}')
            end=text.index(r'\subsection{Climatología, variabilidad y explicación física}',start)
            text=text[:end]+block+text[end:]
        path.write_text(text,encoding='utf-8')


if __name__=='__main__': main()

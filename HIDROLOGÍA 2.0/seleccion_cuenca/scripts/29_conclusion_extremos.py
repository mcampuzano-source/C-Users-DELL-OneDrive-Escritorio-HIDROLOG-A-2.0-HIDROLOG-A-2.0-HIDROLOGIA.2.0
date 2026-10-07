"""Añade respuestas concisas a las dos preguntas del inciso 1.3.3."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
ANSWERS = [
    ('¿Son coherentes entre variables?', 'Sí, en general: los meses lluviosos coinciden con caudales altos o con aumentos posteriores, y los meses secos con caudales bajos. La principal discrepancia aparece en diciembre de 2015, cuando IMERG registra mucha menos lluvia que CHIRPS.'),
    ('¿Son episodios plausibles o problemas de datos?', 'Las secuencias son físicamente plausibles y no encontramos evidencia suficiente para declarar errores. La discrepancia de diciembre de 2015 requiere revisión independiente; los faltantes posteriores a julio de 1992 limitan su comprobación.'),
]


def main():
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b='<!-- CONCLUSION_EXTREMOS_INICIO -->','<!-- CONCLUSION_EXTREMOS_FIN -->'
    original = re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    block = a+'<div id="conclusion-extremos"><h3>Conclusión del contraste de extremos</h3>'
    block += ''.join('<p><strong>'+q+'</strong> '+answer+'</p>' for q,answer in ANSWERS)+'</div>'+b
    start=original.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end=original.index('</section>',start)
    updated=original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    tex=DOC / 'imerg_poligono' / 'contraste_extremos.tex'
    text=tex.read_text(encoding='utf-8')
    ta,tb='% CONCLUSION_EXTREMOS_INICIO','% CONCLUSION_EXTREMOS_FIN'
    original=re.sub(re.escape(ta)+'.*?'+re.escape(tb),'',text,flags=re.S)
    block='\n'+ta+'\n\\subsubsection*{Conclusión del contraste de extremos}\n'
    block+='\n\n'.join('\\textbf{'+q+'} '+answer for q,answer in ANSWERS)+'\n'+tb+'\n'
    tex.write_text(original+block,encoding='utf-8')


if __name__=='__main__': main()

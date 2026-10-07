"""Respuestas breves en lenguaje sencillo para el cuarto inciso del 1.3."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
ANSWERS = [
    ('¿Qué valores describen mejor un mes típico?', 'En lluvia y temperatura, el promedio y la mediana son casi iguales, por lo que ambos sirven. Para caudal y escorrentía, conviene la mediana (el valor central al ordenar los meses), porque unos pocos meses muy altos hacen subir el promedio.'),
    ('¿Cuánto influyen los meses extremos?', 'Influyen más en caudal y escorrentía. Como prueba, si limitamos los valores superiores al percentil 95 a ese umbral, sin cambiar los datos originales, el promedio del caudal baja de 109,83 a 106,25 m³/s y el de escorrentía de 103,27 a 99,76 mm/mes. Esto muestra que esos meses elevan el promedio, pero no significa que sean errores.'),
    ('¿En qué se diferencian CHIRPS e IMERG?', 'Al comparar los mismos 285 meses, IMERG registra 46,05 mm/mes más de lluvia en promedio. CHIRPS muestra valores más dispersos, mientras los de IMERG están más agrupados. Esa diferencia no permite decir cuál mide mejor: necesitamos compararlos con una referencia independiente.'),
]


def main():
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b='<!-- RESPUESTAS_INTERPRETACION_INICIO -->','<!-- RESPUESTAS_INTERPRETACION_FIN -->'
    original=re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    block=a+'<div id="respuestas-interpretacion"><h3>Interpretación de las cifras</h3>'
    block+=''.join('<p><strong>'+q+'</strong> '+answer+'</p>' for q,answer in ANSWERS)
    block+='<p>Esta condición típica reúne meses de todas las estaciones del año; no describe un mes calendario específico.</p></div>'+b
    start=original.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end=original.index('</section>',start)
    updated=original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    tex=DOC / 'imerg_poligono' / 'interpretacion_graficas.tex'
    text=tex.read_text(encoding='utf-8')
    ta,tb='% RESPUESTAS_INTERPRETACION_INICIO','% RESPUESTAS_INTERPRETACION_FIN'
    original=re.sub(re.escape(ta)+'.*?'+re.escape(tb),'',text,flags=re.S)
    block='\n'+ta+'\n\\subsubsection*{Interpretación de las cifras}\n'
    block+='\n\n'.join('\\textbf{'+q+'} '+answer.replace('³',r'$^3$') for q,answer in ANSWERS)
    block+='\n\nEsta condición típica reúne meses de todas las estaciones del año; no describe un mes calendario específico.\n'+tb+'\n'
    tex.write_text(original+block,encoding='utf-8')


if __name__=='__main__': main()

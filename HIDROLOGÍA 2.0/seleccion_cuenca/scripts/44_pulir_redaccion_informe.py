"""Sustituye encabezados de instrucciones por títulos académicos.

Conserva resultados, ecuaciones y figuras; modifica PDF, LaTeX y HTML.
"""
from pathlib import Path
import re
import pymupdf

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
TITLES={
    'Graficar las series de caudal y precipitación':'Variabilidad temporal de la precipitación y del caudal',
    'Incorporar precipitación IMERG para la misma cuenca':'Precipitación satelital y comparación de fuentes',
    'Describir la distribución de los datos mensuales':'Distribución de las variables hidroclimáticas',
    'Usar la exploración como control de calidad':'Calidad y completitud de las series',
    '¿Se pueden construir modelos útiles?':'Modelos estadísticos de lluvia y caudal',
    'Evaluar fuera del periodo de ajuste':'Desempeño de los modelos en la reserva temporal',
    '¿A qué podrían deberse los cambios?':'Interpretación física de la variabilidad hidroclimática',
}
def normalize(t):
    for a,b in {'ﬁ':'fi','ﬂ':'fl','£':'¿'}.items():t=t.replace(a,b)
    return ' '.join(t.split())
for path in [DOCS/'apartado_3/base_portada_punto2.pdf',DOCS/'apartado_3/punto_3_commit_2d27402.pdf']:
    d=pymupdf.open(path)
    for page in d:
        if path.name.startswith('base_') and page.number==1:continue
        changes=[]
        for block in page.get_text('dict')['blocks']:
            if 'lines' not in block:continue
            for line in block['lines']:
                spans=line['spans'];text=normalize(''.join(s['text'] for s in spans))
                for old,new in TITLES.items():
                    if text==old:
                        rect=pymupdf.Rect(line['bbox']);style=spans[0]
                        page.add_redact_annot(rect,fill=(1,1,1))
                        changes.append((rect,new,style))
        if changes:
            page.apply_redactions()
            for rect,text,style in changes:
                size=style['size'];width=page.rect.width-56-rect.x0
                while pymupdf.get_text_length(text,fontname='tibo',fontsize=size)>width:size-=.2
                page.insert_text((rect.x0,rect.y1-2.7),text,fontname='tibo',fontsize=size)
    toc=d.get_toc()
    for row in toc:row[1]=TITLES.get(row[1],row[1])
    d.set_toc(toc)
    temp=path.with_suffix('.academic.tmp.pdf');d.save(temp,garbage=4,deflate=True);d.close();temp.replace(path)
tex=DOCS/'latex/informe_ordenado.tex';s=tex.read_text(encoding='utf-8')
for old,new in TITLES.items():s=s.replace(old,new)
s=s.replace('Para mantener una notación explícita, ','')
tex.write_text(s,encoding='utf-8')
html=DOCS/'informe_interactivo.html';s=html.read_text(encoding='utf-8')
for old,new in TITLES.items():s=s.replace(old,new)
s=s.replace('Hidrología · Documento en construcción · Pasos 1–3','Hidrología · Análisis hidroclimático de la cuenca')
s=s.replace('Documento en construcción','Análisis hidroclimático')
html.write_text(s,encoding='utf-8')
print('Encabezados académicos actualizados; resultados conservados.')

"""Reescribe introducción, metodología y contexto para el informe de entrega."""
from pathlib import Path
import json
import re
import html
import shutil
import pymupdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'la_vieja/documentos'
OUT=DOCS/'redaccion_academica'
OUT.mkdir(exist_ok=True)
intro=[
    'La variabilidad de la precipitación y del caudal condiciona la disponibilidad de agua y la ocurrencia de periodos secos y crecientes en las cuencas andinas. En el río La Vieja, el contraste entre las zonas montañosas y los sectores bajos del valle, junto con la variabilidad del clima tropical, motiva estudiar cómo cambia la respuesta hidrológica a lo largo del año y entre años.',
    'Este informe analiza la cuenca del río La Vieja hasta la estación Cartago mediante series mensuales de precipitación, caudal y temperatura. Se examinan el ciclo anual, las distribuciones y los valores extremos; se comparan CHIRPS e IMERG y se evalúan modelos estadísticos de lluvia–caudal y tendencias temporales. El análisis se complementa con la selección de campos oceánicos y atmosféricos globales para estudiar asociaciones climáticas. Las relaciones estadísticas se interpretan considerando la cobertura de los datos, la topografía y las diferencias entre las fuentes.'
]
methods=[
    'La delimitación de la cuenca y las series hidrológicas de referencia proceden de CAMELS-COL. La precipitación CHIRPS se analiza como promedio de cuenca y el caudal corresponde a Cartago (IDEAM 26127040). IMERG Final Run V07B y la temperatura ERA5-Land se ponderan según el área de intersección de sus celdas con la cuenca. Estos productos representan estimaciones espaciales distintas de una observación pluviométrica puntual.',
    'El registro hidrológico abarca 1981–2022. Los acumulados de lluvia y las medias de caudal se calculan únicamente para meses con todos sus días válidos: se conservan 485 de 504 meses. La comparación entre CHIRPS, IMERG y caudal utiliza 285 meses simultáneos de 1998–2022. Los vacíos se mantienen sin relleno. Las diferencias estacionales se examinan mediante climatologías y anomalías mensuales; la evaluación de modelos distingue el periodo de ajuste de la reserva temporal. Los criterios y las incertidumbres específicos se documentan junto a cada análisis.'
]
context=[
    'La cuenca del río La Vieja se localiza en el centro-occidente de Colombia, en la región del Eje Cafetero, y comprende territorios de Quindío, Risaralda y Valle del Cauca. Su red hidrográfica conecta las vertientes de la cordillera Central con los sectores bajos próximos a Cartago. El río La Vieja se forma por la confluencia de los ríos Quindío y Barragán y desemboca en el río Cauca, de cuya red de drenaje es tributario.',
    'El área de estudio corresponde a la cuenca aguas arriba de la estación Cartago (IDEAM 26127040), delimitada en CAMELS-COL, con una superficie de 2.797,19 km². Esta delimitación define el área sobre la que se promedian los productos de precipitación y temperatura y el territorio cuyos aportes se integran en el caudal observado. Su extensión no debe confundirse con la cuenca administrativa completa descrita en los instrumentos de ordenamiento ambiental.',
    'El relieve presenta un contraste marcado entre las zonas altas de la cordillera y el sector de salida hacia Cartago, con elevaciones del orden de 900 a 4.800 m en la información topográfica analizada. Esta heterogeneidad es relevante para la distribución espacial de la lluvia y la temperatura y para el tránsito y almacenamiento del agua. Las series de cuenca muestran un ciclo de precipitación bimodal, con máximos alrededor de abril–mayo y octubre–noviembre. Por ello, la interpretación de la relación lluvia–caudal distingue el ciclo estacional compartido de las variaciones entre años.'
]
refs=[('CRQ, Plan de Gestión Ambiental Regional 2020–2039','https://crq.gov.co/wp-content/uploads/2021/03/PGARQUINDIO2020-2039.pdf'),('CVC, Balance oferta–demanda de agua: río La Vieja','https://www.cvc.gov.co/sites/default/files/2018-09/Balance_La_Vieja_1.pdf'),('CAMELS-COL','https://doi.org/10.5281/zenodo.18794895')]
(OUT/'textos.json').write_text(json.dumps(dict(introduction=intro,methodology=methods,context=context,sources=refs),ensure_ascii=False,indent=2),encoding='utf-8')

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Academic',parent=styles['BodyText'],fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=11))
styles.add(ParagraphStyle(name='CaptionAcademic',parent=styles['BodyText'],fontName='Helvetica',fontSize=8.5,leading=11,spaceAfter=6))
styles['Heading1'].textColor=colors.HexColor('#193646')
def p(s,style='Academic'):return Paragraph(html.escape(s),styles[style])
map_pdf=DOCS/'latex/figuras/mapa_cuenca_estaciones_geografico.pdf'
md=pymupdf.open(map_pdf);page=md[0];ratio=page.rect.height/page.rect.width
page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5)).save(OUT/'contexto_cuenca.png');md.close()
story=[p('Introducción','Heading1')]+[p(t) for t in intro]+[Spacer(1,12),p('Metodología','Heading1')]+[p(t) for t in methods]
story +=[PageBreak(),p('Área de estudio: cuenca del río La Vieja','Heading1')]+[p(t) for t in context]
story +=[Spacer(1,9),Image(str(OUT/'contexto_cuenca.png'),width=300,height=300*ratio),Spacer(1,8)]
story +=[p('Figura 1. Localización de la cuenca hasta Cartago y estaciones de lluvia inventariadas. El contorno representa la delimitación utilizada en el estudio. Base cartográfica: © OpenStreetMap contributors; delimitación: CAMELS-COL; estaciones: catálogo IDEAM.','CaptionAcademic')]
story +=[Paragraph('Fuentes de contexto: '+ '; '.join(f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>' for label,url in refs)+'.',styles['CaptionAcademic'])]
front=OUT/'introduccion_contexto.pdf'
SimpleDocTemplate(str(front),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=53,title='Introducción y área de estudio').build(story)
d=pymupdf.open(front);assert len(d)==2,'Revisar extensión y disposición del mapa';d.close()

# Idempotent replacement of the earlier page with the drafting notes.
base=DOCS/'apartado_3/base_portada_punto2.pdf'
snapshot=OUT/'base_antes_redaccion.pdf'
if not snapshot.exists():shutil.copyfile(base,snapshot)
old=pymupdf.open(snapshot);new=pymupdf.open();f=pymupdf.open(front)
new.insert_pdf(old,from_page=0,to_page=1);new.insert_pdf(f);new.insert_pdf(old,from_page=3)
toc=old.get_toc()
for row in toc:
    if row[2]>=3:row[2]+=1
new.set_toc(toc);temp=OUT/'base_actualizada.pdf';new.save(temp,garbage=4,deflate=True);new.close();old.close();f.close();shutil.copyfile(temp,base)

tex=DOCS/'latex/informe_ordenado.tex';s=tex.read_text(encoding='utf-8')
a=s.index(r'\section*{Introducción}');b=s.index(r'\subsubsection*{Mapas de la cuenca y topografía}',a)
def esc(s):return s.replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('²',r'$^2$')
block=r'\section*{Introducción}'+'\n'+'\n\n'.join(esc(t) for t in intro)+'\n'
block+=r'\section*{Metodología}'+'\n'+'\n\n'.join(esc(t) for t in methods)+'\n'+r'\clearpage'+'\n'
block+=r'\section*{Área de estudio: cuenca del río La Vieja}'+'\n'+'\n\n'.join(esc(t) for t in context)+'\n'
block+=r'\begin{figure}[H]\centering\includegraphics[width=.82\linewidth]{figuras/mapa_cuenca_estaciones_geografico.pdf}\caption{Localización de la cuenca hasta Cartago y estaciones de lluvia inventariadas. Base: \copyright\ OpenStreetMap contributors; delimitación: CAMELS-COL; estaciones: catálogo IDEAM.}\end{figure}'+'\n'
block+='Fuentes de contexto: '+ '; '.join(r'\href{'+url+'}{'+esc(label)+'}' for label,url in refs)+'.\n'+r'\clearpage'+'\n'
s=s[:a]+block+s[b:];tex.write_text(s,encoding='utf-8')

hpath=DOCS/'informe_interactivo.html';h=hpath.read_text(encoding='utf-8')
para=lambda texts:''.join('<p>'+html.escape(t)+'</p>' for t in texts)
h=re.sub(r"pendiente\(grupo\('guia-introduccion','Introducción'\),'[^']*'\);",lambda _:"grupo('guia-introduccion','Introducción').insertAdjacentHTML('beforeend',"+json.dumps(para(intro),ensure_ascii=False)+");",h)
h=re.sub(r"pendiente\(grupo\('guia-metodologia','Metodología'\),'[^']*'\);",lambda _:"grupo('guia-metodologia','Metodología').insertAdjacentHTML('beforeend',"+json.dumps(para(methods),ensure_ascii=False)+");",h)
h=h.replace("const contexto=grupo('guia-contexto','Contexto geográfico de la cuenca');","const contexto=grupo('guia-contexto','Área de estudio: cuenca del río La Vieja');")
pattern=r'(<section class="panel" id="mapas-geograficos"><h2>).*?(</h2>)<p>.*?</p>'
lead='Localización de la cuenca y red hidrográfica'
ctx=para(context)+'<p>Fuentes: '+ '; '.join('<a href="'+url+'">'+html.escape(label)+'</a>' for label,url in refs)+'.</p>'
h=re.sub(pattern,lambda m:m.group(1)+lead+m.group(2)+ctx,h,count=1,flags=re.S)
h=h.replace('Este segundo mapa usa una base topográfica para facilitar la lectura de relieve y ubicación regional. El polígono y la estación mantienen las mismas coordenadas.','El contraste entre las vertientes altas y el sector de Cartago sitúa la variabilidad hidroclimática en su contexto topográfico. El contorno corresponde al área de estudio y la estrella identifica la estación de salida.')
hpath.write_text(h,encoding='utf-8')
print('Introducción, metodología y área de estudio reescritas con tono académico.')

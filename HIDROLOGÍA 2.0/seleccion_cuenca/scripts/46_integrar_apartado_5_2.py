"""Redacción académica, atlas PDF y mapas interactivos del apartado 5.2."""
from pathlib import Path
import json
import html
import re
import shutil
import pandas as pd
import numpy as np
import pymupdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
OUT=DOCS/'apartado_5_2'
s=json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
diag=pd.read_csv(OUT/'diagnostico_mapas.csv')
regions=pd.read_csv(OUT/'indices_sst_regionales.csv')
sens=pd.read_csv(OUT/'sensibilidad_CHIRPS_IMERG.csv')
months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
responses={'CHIRPS':'Precipitación CHIRPS','Q':'Caudal Cartago','IMERG':'Precipitación IMERG'}
fields={'sst':'SST ERSSTv5','slp':'SLP NCEP/NCAR R1','z500':'Z500 NCEP/NCAR R1'}
summary=diag.groupby(['response','field','lag_months'],sort=False).agg(delta=('mean_abs_difference_weighted','mean'),signs=('sign_disagreement_abs_02','mean'),nmin=('n_min','min'),nmax=('n_max','max')).reset_index()
nino=regions[regions.region=='Niño 3.4']
table_nino=[]
for m in range(1,13):
    row=[months[m-1],str(s['monthly_n'][str(m)])]
    for response,lag in [('CHIRPS',0),('Q',0),('IMERG',0),('Q',1)]:
        a=nino[(nino.month==m)&(nino.response==response)&(nino.lag==lag)].iloc[0]
        row.append(f"{a.pearson:+.2f} / {a.spearman:+.2f}")
    table_nino.append(row)

texts=[
 ('Variabilidad interanual y definición de los mapas','La asociación entre la hidroclimatología de La Vieja y los campos globales se estima mediante correlaciones temporales en cada celda. Para un mes calendario j se comparan los valores de la respuesta de cuenca en todos los años disponibles con los del campo climático correspondientes a ese mismo mes o al mes antecedente definido por el rezago. Cada combinación presenta doce mapas, uno por mes de la respuesta. Las correlaciones no se calculan entre celdas ni a partir de un único mes observado.'),
 ('Respuestas de cuenca y fuentes','La precipitación de referencia corresponde a CHIRPS, promediada sobre la cuenca; el caudal se observa en Cartago. IMERG Final Run V07B permite contrastar la sensibilidad de los patrones a la fuente de precipitación. CHIRPS es un producto espacial combinado, no una medición puntual independiente. La lluvia de Zaragoza dispone de solo 14 meses completos y no permite estimar doce correlaciones interanuales; por ello, no se atribuyen los mapas a esa estación. Se emplean SST ERSSTv5, presión al nivel del mar y altura geopotencial a 500 hPa de NCEP/NCAR R1, manteniendo las rejillas y máscaras del 5.1.'),
 ('Anomalías, rezagos y tamaño efectivo','La referencia comprende las mismas 285 fechas completas de cuenca en 1998–2022. Para cada variable se resta la climatología de su mes calendario; los campos globales y las respuestas conservan sus unidades antes de calcular el coeficiente adimensional. La base tiene rezago cero. Para Q se añade un rezago de un mes como exploración de la persistencia climática y de una respuesta hidrológica con almacenamiento; no se interpreta como tiempo de concentración. Con la convención r_j(lon,lat;ell) = corr[a_X(t),a_Y(lon,lat,t-ell)] para mes(t)=j, ell>0 significa que el campo climático antecede al caudal. Enero de 1998 se empareja con diciembre de 1997 para ell=1. El desplazamiento se hace en el calendario completo; no se usan valores futuros ni se comprimen los huecos.'),
 ('Criterios de cálculo y representación','Pearson es la referencia y Spearman contrasta la sensibilidad a extremos, asimetría y relaciones monotónicas no lineales. Spearman se calcula sobre rangos con promedio para empates y la misma máscara de pares válidos. Cada mapa informa el mínimo y máximo n de sus celdas representadas. Se exige n≥20 y variación no nula en ambas variables; las celdas restantes se muestran grises. Las respuestas aportan entre 22 y 25 años por mes, no 285 observaciones para cada enero. Los campos globales están completos en el calendario seleccionado y el antecedente de diciembre de 1997 está disponible; solo las máscaras de cada celda pueden reducir sus pares. Esta muestra no es la de 274 fechas de los modelos de lluvia antecedente del punto 2, que además necesitaban precipitación de cuenca del mes previo.'),
 ('Lectura física y alcance','Un coeficiente negativo indica que anomalías positivas del campo coinciden con anomalías negativas de la respuesta; un coeficiente positivo indica desviaciones del mismo signo. La interpretación de SLP y Z500 corresponde a patrones de circulación de gran escala, no a mediciones directas de transporte de humedad. La concordancia entre Pearson y Spearman respalda una asociación menos dependiente de la escala o de unos pocos extremos, pero no demuestra causalidad ni constituye una prueba independiente. Los mapas de distintos meses, fuentes y métodos comparten años y forzamientos climáticos. No se eliminó tendencia ni se aplicaron pruebas de significancia: autocorrelación, pruebas múltiples y sensibilidad temporal se evaluarán en 5.3.'),
]
region_text=[]
for response in ('CHIRPS','Q','IMERG'):
    a=nino[(nino.response==response)&(nino.lag==0)]
    negative=int((a.pearson<0).sum())
    region_text.append(f"{responses[response]}: r entre {a.pearson.min():+.2f} y {a.pearson.max():+.2f}; negativo en {negative}/12 meses.")
texts += [('Contraste regional del Pacífico tropical','Como apoyo a los mapas se construye un índice interno de anomalías SST en Niño 3.4 (5°S–5°N, 170°W–120°W), seleccionando centros de celda y ponderando por coseno de latitud. Es un promedio mensual sobre la referencia de este estudio, no el índice ONI ni su promedio móvil trimestral. Las correlaciones del índice con cada respuesta se calculan a través de los años de un mismo mes. '+ ' '.join(region_text)+' Estas cifras son descriptivas y no establecen significancia estadística; el detalle de los doce meses permite examinar la estacionalidad de la asociación sin seleccionar una sola celda extrema.')]
for field in fields:
    a=sens[sens.field==field]
    texts.append((f'Sensibilidad de la precipitación frente a {fields[field]}',f"La diferencia absoluta entre los mapas Pearson de CHIRPS e IMERG, promediada espacialmente con pesos de coseno de latitud, varía de {a.mean_abs_delta.min():.3f} a {a.mean_abs_delta.max():.3f} según el mes. Esta diferencia compara dos estimaciones de precipitación sobre las mismas fechas y rejillas; no mide precisión frente a una verdad observada ni es una correlación espacial de los datos. Los paneles permiten identificar si se conservan el signo y la extensión de los patrones, mientras que Spearman permite contrastar su sensibilidad a los rangos."))

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body52',parent=styles['BodyText'],fontSize=10,leading=14,spaceAfter=8,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle(name='Cell52',parent=styles['BodyText'],fontSize=8,leading=10))
styles['Heading1'].textColor=colors.HexColor('#193646');styles['Heading2'].textColor=colors.HexColor('#193646')
def p(t,st='Body52'):return Paragraph(html.escape(t),styles[st])
def table(heads,rows,widths):
    t=Table([[p(c,'Cell52') for c in heads]]+[[p(str(c),'Cell52') for c in row] for row in rows],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf4f7')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cad9df')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
story=[p('5.2. Correlaciones mensuales con el clima global','Heading1')]
for title,text in texts[:6]:story +=[p(title,'Heading2'),p(text)]
story +=[table(['Mes','n','CHIRPS ell=0','Q ell=0','IMERG ell=0','Q ell=1'],table_nino,[36,28,104,104,104,107]),p('Cada casilla presenta Pearson / Spearman frente al índice SST Niño 3.4 interno. El n corresponde al número de pares de años. Un signo o una magnitud no implican significancia.')]
for title,text in texts[6:]:story +=[p(title,'Heading2'),p(text)]
rows=[[responses[r.response],fields[r.field],str(r.lag_months),f'{r.delta:.3f}',f'{r.nmin}–{r.nmax}'] for r in summary.itertuples()]
story +=[p('Diagnóstico Pearson–Spearman','Heading2'),table(['Respuesta','Campo','ell','Media |r-rho|','n celdas válidas'],rows,[130,143,28,85,97]),p('La diferencia combina promedios espaciales ponderados por coseno de latitud de cada mes y luego promedia los doce meses; no es una correlación calculada con todos los meses juntos.')]
story +=[p('Atlas de mapas mensuales','Heading2'),p('Se presentan nueve láminas Pearson de rezago cero y sus nueve equivalentes Spearman. Las seis láminas restantes corresponden a Q con campo antecedente de un mes, tres por estadístico. Cada lámina incluye doce paneles comparables, con escala fija de -1 a 1, mes de la respuesta y n efectivo. En total se calculan 108 mapas principales por método y 36 adicionales por método para Q con rezago uno (288 mapas). La estrella sitúa aproximadamente La Vieja. Costas: Natural Earth; SST: NOAA ERSSTv5; SLP y Z500: NCEP/NCAR Reanalysis 1, NOAA PSL.')]
summary_pdf=OUT/'texto_5_2.pdf'
SimpleDocTemplate(str(summary_pdf),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=55,title='5.2 - Correlaciones mensuales').build(story)
atlas=pymupdf.open(summary_pdf)
order=[]
for lag,method in [(0,'pearson'),(0,'spearman'),(1,'pearson'),(1,'spearman')]:
    for combo in s['combinations']:
        if combo['lag']!=lag:continue
        name=combo['key']+'_'+method
        page=len(atlas)+1;f=pymupdf.open(OUT/(name+'.pdf'));assert len(f)==1
        rect=f[0].rect;p=atlas.new_page(width=rect.width,height=rect.height+58);p.show_pdf_page(rect,f,0);f.close()
        order.append([1,f"{responses[combo['response']]} · {fields[combo['field']]} · {method} · ell={lag}",page])
atlas.set_toc(order);atlas.save(OUT/'punto_5_2.pdf',garbage=4,deflate=True);atlas.close()

body='<h4>Correlaciones interanuales por mes calendario</h4>'
for title,text in texts:body+='<h4>'+html.escape(title)+'</h4><p>'+html.escape(text)+'</p>'
body+='<div style="overflow:auto"><table><thead><tr>'+''.join('<th>'+c+'</th>' for c in ['Mes','n','CHIRPS ell=0','Q ell=0','IMERG ell=0','Q ell=1'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in table_nino)+'</tbody></table></div><p>Pearson / Spearman frente al índice SST Niño 3.4 interno; no es ONI y no se muestra significancia.</p>'
body+='''<h4>Mapas mensuales interactivos</h4><p>Los doce paneles corresponden a meses de la respuesta, comparados a través de los años. Seleccione una combinación y un método, o amplíe un mes para consultar cada celda. Gris: faltantes, n&lt;20 o ausencia de variación. Escala común de -1 a 1.</p>
<div class="controles52" style="display:flex;gap:14px;flex-wrap:wrap">
<label>Respuesta <select id="respuesta52"><option value="CHIRPS">Precipitación CHIRPS</option><option value="Q">Caudal Cartago</option><option value="IMERG">Precipitación IMERG</option></select></label>
<label>Campo <select id="campo52"><option value="sst">SST ERSSTv5</option><option value="slp">SLP NCEP/NCAR R1</option><option value="z500">Z500 NCEP/NCAR R1</option></select></label>
<label>Coeficiente <select id="metodo52"><option value="r">Pearson</option><option value="rho">Spearman</option><option value="delta">Pearson - Spearman</option><option value="n">Pares válidos (n)</option></select></label>
<label>Rezago <select id="rezago52"><option value="0">0 meses</option><option value="1">1 mes anterior (solo Q)</option></select></label>
<label>Vista <select id="mes52"><option value="0">Doce meses</option>'''+''.join(f'<option value="{i}">{m}</option>' for i,m in enumerate(months,1))+'''</select></label>
</div><p id="nota52"></p><div id="mapas52" style="width:100%;height:1000px"></div>
<button id="exportar52" type="button">Descargar datos del mes seleccionado (CSV)</button><p>Los coeficientes del visor se redondean a tres decimales. Los NetCDF conservan el cálculo completo. El CSV requiere seleccionar un mes individual. No se ha evaluado significancia.</p>'''
payload=(OUT/'mapas_interactivos.json').read_text()
coast=json.loads((DOCS/'apartado_5_1/ne_110m_coastline.geojson').read_bytes());cx=[];cy=[]
for f in coast['features']:
    parts=f['geometry']['coordinates']
    if f['geometry']['type']=='LineString':parts=[parts]
    for part in parts:
        prev=None
        for x,y in part:
            if prev is not None and abs(x-prev)>180:cx.append(None);cy.append(None)
            cx.append(x);cy.append(y);prev=x
        cx.append(None);cy.append(None)
script=r'''<script id="script52">(function(){
const DATA=__PAYLOAD__,MONTHS=__MONTHS__,COAST=__COAST__;
const labels={r:'Pearson r',rho:'Spearman rho',delta:'Pearson - Spearman',n:'Pares válidos'};
const names={CHIRPS:'Precipitación CHIRPS',Q:'Caudal Cartago',IMERG:'Precipitación IMERG',sst:'SST ERSSTv5',slp:'SLP NCEP/NCAR R1',z500:'Z500 NCEP/NCAR R1'};
const el=id=>document.getElementById(id), decode=v=>v<-30000?null:v/1000;
function current(){const response=el('respuesta52').value;if(response!=='Q')el('rezago52').value='0';el('rezago52').disabled=response!=='Q';return DATA[response+'_'+el('campo52').value+'_l'+el('rezago52').value];}
function values(d,m,mode){return d.r[m].map((row,i)=>row.map((v,j)=>{if(decode(v)===null)return null;if(mode==='n')return d.n[m][i][j];if(mode==='delta')return decode(v)-decode(d.rho[m][i][j]);return decode(d[mode][m][i][j]);}));}
function draw(){const d=current(),mode=el('metodo52').value,selected=Number(el('mes52').value);const months=selected?[selected-1]:Array.from({length:12},(_,i)=>i);const traces=[],layout={title:{text:names[d.response]+' frente a '+names[d.field]+' · '+labels[mode]+' · ell='+d.lag,font:{size:17}},margin:{l:45,r:40,t:100,b:80},paper_bgcolor:'#fff',plot_bgcolor:'#eee',showlegend:false,annotations:[],uirevision:d.field+':'+selected};
const min=mode==='n'?20:mode==='delta'?-.5:-1,max=mode==='n'?25:mode==='delta'?.5:1;
months.forEach((m,k)=>{const cols=selected?1:3,rows=selected?1:4,row=Math.floor(k/cols),col=k%cols;const xd=[col/cols+.02,(col+1)/cols-.02],yd=[1-(row+1)/rows+.035,1-row/rows-.04];const suffix=k===0?'':String(k+1),xa='x'+suffix,ya='y'+suffix;
 layout['xaxis'+suffix]={domain:xd,anchor:ya,range:[-180,180],tickvals:[-180,-90,0,90,180],title:row===rows-1?'Longitud (°)':'',tickfont:{size:10}};
 layout['yaxis'+suffix]={domain:yd,anchor:xa,range:[-90,90],tickvals:[-90,-45,0,45,90],title:col===0?'Latitud (°)':'',tickfont:{size:10}};
 let ns=[];d.r[m].forEach((a,i)=>a.forEach((v,j)=>{if(decode(v)!==null)ns.push(d.n[m][i][j]);}));const nmin=Math.min(...ns),nmax=Math.max(...ns);
 layout.annotations.push({text:MONTHS[m]+' · n='+nmin+(nmax===nmin?'':'–'+nmax),x:(xd[0]+xd[1])/2,y:yd[1]+.014,xref:'paper',yref:'paper',showarrow:false,font:{size:12}});
 traces.push({type:'heatmap',x:d.lon,y:d.lat,z:values(d,m,mode),customdata:d.n[m],xaxis:xa,yaxis:ya,zmin:min,zmax:max,colorscale:mode==='n'?'Viridis':'RdBu',reversescale:mode!=='n',showscale:k===0,hoverongaps:false,colorbar:{orientation:'h',x:.5,y:-.08,len:.45,thickness:12,title:labels[mode]},hovertemplate:'Lon %{x}° · Lat %{y}°<br>'+MONTHS[m]+' · '+labels[mode]+': %{z:.3f}<br>n=%{customdata}<extra></extra>'});
 traces.push({type:'scatter',mode:'lines',x:COAST.x,y:COAST.y,xaxis:xa,yaxis:ya,line:{color:'#444',width:.5},hoverinfo:'skip'});
 traces.push({type:'scatter',mode:'markers',x:[-75.7],y:[4.45],xaxis:xa,yaxis:ya,marker:{symbol:'star',size:6,color:'black'},hovertemplate:'Cuenca La Vieja (ubicación aproximada)<extra></extra>'});
 });el('mapas52').style.height=selected?'600px':'1050px';el('nota52').textContent='Respuesta: 1998–2022. ell='+d.lag+(d.lag?' significa campo del mes anterior; enero usa diciembre del año anterior.':' significa campo y respuesta del mismo mes.')+' Correlaciones temporales entre años, no entre celdas. Gris: sin estimación válida.';
 Plotly.react('mapas52',traces,layout,{responsive:true,displaylogo:false,toImageButtonOptions:{format:'png',filename:'correlacion_'+d.response+'_'+d.field+'_l'+d.lag}});
 el('exportar52').disabled=!selected;
}
function init(){if(!el('mapas52')||!window.Plotly)return;['respuesta52','campo52','metodo52','rezago52','mes52'].forEach(id=>el(id).addEventListener('change',draw));el('exportar52').addEventListener('click',()=>{const d=current(),m=Number(el('mes52').value)-1;if(m<0)return;const rows=['respuesta,campo,rezago,mes,latitud,longitud,pearson,spearman,n'];d.lat.forEach((lat,i)=>d.lon.forEach((lon,j)=>{const r=decode(d.r[m][i][j]),rho=decode(d.rho[m][i][j]);if(r!==null)rows.push([d.response,d.field,d.lag,m+1,lat,lon,r,rho,d.n[m][i][j]].join(','));}));const url=URL.createObjectURL(new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=d.response+'_'+d.field+'_l'+d.lag+'_mes'+(m+1)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});draw();}
if(document.readyState==='complete')init();else window.addEventListener('load',init);
})();</script>'''
script=script.replace('__PAYLOAD__',payload).replace('__MONTHS__',json.dumps(months)).replace('__COAST__',json.dumps(dict(x=cx,y=cy),separators=(',',':')))
body+=script
(OUT/'contenido_5_2.html').write_text(body,encoding='utf-8')
hpath=DOCS/'informe_interactivo.html';h=hpath.read_text(encoding='utf-8');block='<!-- PUNTO_5_2_INICIO --><section class="panel" id="mapas-mensuales-52">'+body+'</section><!-- PUNTO_5_2_FIN -->'
if '<!-- PUNTO_5_2_INICIO -->' in h:h=re.sub(r'<!-- PUNTO_5_2_INICIO -->.*?<!-- PUNTO_5_2_FIN -->',lambda _:block,h,flags=re.S)
else:h=h.replace('</main>',block+'</main>',1)
needle="if(n===5&&i===0)mover(se,document.getElementById('seleccion-campos-51'));else pendiente(se,'Pendiente de desarrollar.');"
new="if(n===5&&i===0)mover(se,document.getElementById('seleccion-campos-51'));else if(n===5&&i===1)mover(se,document.getElementById('mapas-mensuales-52'));else pendiente(se,'Pendiente de desarrollar.');"
if needle in h:h=h.replace(needle,new)
else:assert "document.getElementById('mapas-mensuales-52')" in h
hpath.write_text(h,encoding='utf-8')
tex=DOCS/'latex/informe_ordenado.tex';t=tex.read_text(encoding='utf-8')
start=t.index(r'\subsection{Definir y calcular los mapas mensuales}');end=t.index(r'\subsection{Robustez y presentación de los patrones}',start)
esc=lambda x:x.replace('%',r'\%').replace('_',r'\_').replace('&',r'\&').replace('°',r'$^\circ$').replace('≥',r'$\geq$')
part=r'\subsection{Definir y calcular los mapas mensuales}'+'\n'
for title,text in texts:part+=r'\subsubsection*{'+esc(title)+'}\n'+esc(text)+'\n\n'
for item in s['combinations']:
    for figure in item['figures']:part+=r'\begin{figure}[p]\centering\includegraphics[width=\linewidth]{../apartado_5_2/'+figure+'.pdf}'+r'\caption{Doce correlaciones temporales por mes calendario; rezago '+str(item['lag'])+r' mes(es).}\end{figure}'+'\n'
t=t[:start]+part+t[end:];tex.write_text(t,encoding='utf-8')
(OUT/'README.md').write_text('''# Apartado 5.2

Correlaciones por celda y mes calendario, a través de los años. Nueve combinaciones de respuesta/campo con rezago cero; tres para Q con campo antecedente un mes. Pearson y Spearman, n>=20 y varianza no nula. Climatologías fijas sobre 285 meses completos de cuenca, referencia 1998-2022. El rezago desplaza el campo en el calendario completo, con diciembre de 1997 disponible para enero de 1998.

Las matrices NetCDF conservan la precisión completa. El visor redondea coeficientes a tres decimales. No se calcula significancia ni se eliminan tendencias; 5.3 queda pendiente. CHIRPS es referencia espacial de cuenca, no lluvia puntual Zaragoza. Niño 3.4 interno no es ONI.

Reproducir con 45_calcular_mapas_mensuales.py, 46_integrar_apartado_5_2.py y 40_integrar_pdf_punto3.py. La redacción de títulos puede reproducirse con 44_pulir_redaccion_informe.py. El informe conserva los apartados anteriores y la portada.
''',encoding='utf-8')
print('5.2 redactado: atlas PDF y selector interactivo de 288 mapas.',flush=True)

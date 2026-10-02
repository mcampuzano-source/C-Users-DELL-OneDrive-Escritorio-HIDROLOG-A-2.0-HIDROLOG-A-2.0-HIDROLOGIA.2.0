"""Paso 1 de los documentos LaTeX y HTML Plotly sin servidor.
Lee las mismas series auditadas para ambos documentos. No rellena vacios.
"""
from pathlib import Path
import json
import hashlib
import importlib.metadata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
LATEX=DOC/'latex'
FIG=LATEX/'figuras'
for path in [DOC,LATEX,FIG,LATEX/'secciones']:
    path.mkdir(parents=True,exist_ok=True)
source=ROOT/'la_vieja'/'punto_1'/'series_mensuales.csv'
data=pd.read_csv(source,parse_dates=['mes']).set_index('mes')
availability=pd.read_csv(ROOT/'la_vieja'/'punto_1'/'disponibilidad_mensual.csv',parse_dates=['mes']).set_index('mes')
assert data.index.equals(pd.date_range('1981-01-01','2022-12-01',freq='MS'))
assert data.index.equals(availability.index)
assert data.P_mm.notna().equals(availability.dias_validos_P.eq(availability.dias_esperados))
assert data.Q_m3_s.notna().equals(availability.dias_validos_Q.eq(availability.dias_esperados))
panels=[('P_mm','P','Precipitación CHIRPS','mm/mes','#23769b'),('Q_m3_s','Q','Caudal observado','m³/s','#a65424')]

# Figura vectorial para LaTeX: texto y trazos permanecen nitidos al ampliar.
plt.rcParams.update({'font.family':'serif','font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,1,figsize=(6.7,4.6),sharex=True,layout='constrained')
for ax,(var,short,title,unit,color) in zip(axes,panels):
    ax.plot(data.index,data[var],color=color,lw=.65)
    for date in data.index[data[var].isna()]:
        ax.axvspan(date,date+pd.offsets.MonthBegin(1),color='#d0d0d0',alpha=.8,lw=0)
    ax.set_ylabel(f'{title}\n({unit})')
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.2,lw=.5)
    ax.set_title(f'{short}: {data[var].notna().sum()} meses válidos',loc='left',fontsize=9)
axes[-1].set_xlim(pd.Timestamp('1981-01-01'),pd.Timestamp('2023-01-01'))
axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axes[-1].set_xlabel('Año')
fig.savefig(FIG/'series_mensuales.pdf',bbox_inches='tight')
fig.savefig(FIG/'series_mensuales.png',dpi=300,bbox_inches='tight')
plt.close(fig)

# Plotly: los valores ausentes se conservan como null y connectgaps=False.
interactive=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=.12,subplot_titles=['Precipitación mensual · CHIRPS','Caudal medio mensual · estación Cartago'])
for row,(var,short,title,unit,color) in enumerate(panels,1):
    values=[None if pd.isna(v) else float(v) for v in data[var]]
    custom=[[int(a),int(b)] for a,b in zip(availability[f'dias_validos_{short}'],availability.dias_esperados)]
    interactive.add_trace(go.Scatter(x=data.index,y=values,mode='lines',name=title,line={'color':color,'width':1.25},connectgaps=False,customdata=custom,hovertemplate=f'%{{x|%Y-%m}}<br>{short}: %{{y:.2f}} {unit}<br>Días válidos: %{{customdata[0]}}/%{{customdata[1]}}<extra></extra>'),row=row,col=1)
    # Marcadores sobre la linea cero permiten consultar por que se excluyo un mes.
    missing=data[var].isna()
    interactive.add_trace(go.Scatter(x=data.index[missing],y=[0]*int(missing.sum()),mode='markers',name=f'Mes excluido ({short})',marker={'symbol':'x','size':7,'color':'#777'},customdata=[c for c,m in zip(custom,missing) if m],hovertemplate=f'%{{x|%Y-%m}}<br>{short}: mes excluido, NO valor cero<br>Días válidos: %{{customdata[0]}}/%{{customdata[1]}}<extra></extra>',showlegend=False),row=row,col=1)
    for date in data.index[missing]:
        interactive.add_vrect(x0=date,x1=date+pd.offsets.MonthBegin(1),fillcolor='#aaa',opacity=.2,line_width=0,row=row,col=1)
    interactive.update_yaxes(title_text=unit,rangemode='tozero',fixedrange=False,row=row,col=1)
interactive.update_layout(height=730,template='plotly_white',hovermode='x unified',dragmode='zoom',showlegend=False,margin={'l':70,'r':25,'t':65,'b':45},font={'family':'Arial','size':13})
interactive.update_xaxes(range=['1981-01-01','2023-01-01'],matches='x2')
interactive.update_xaxes(rangeselector={'buttons':[{'count':5,'label':'5 años','step':'year','stepmode':'backward'},{'count':10,'label':'10 años','step':'year','stepmode':'backward'},{'step':'all','label':'Todo'}]},row=1,col=1)
interactive.update_xaxes(title_text='Fecha',rangeslider={'visible':True,'thickness':.10},row=2,col=1)
graph=interactive.to_html(full_html=False,include_plotlyjs=True,div_id='series-mensuales',config={'responsive':True,'displaylogo':False,'scrollZoom':True,'toImageButtonOptions':{'format':'svg','filename':'la_vieja_series_mensuales','width':1400,'height':850}})
html='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>La Vieja — informe interactivo</title><style>
body{font:16px/1.6 system-ui,sans-serif;color:#193646;margin:0;background:#f3f6f8}main{max-width:1250px;margin:auto;padding:30px 24px}h1,h2{line-height:1.2}.etiqueta{color:#32758b;font-size:13px;text-transform:uppercase;letter-spacing:.08em}.ficha{display:flex;gap:14px;flex-wrap:wrap}.ficha p{background:white;border:1px solid #dce5e9;padding:12px 20px;border-radius:8px}.panel{background:white;padding:20px;border-radius:10px;margin:20px 0}.nota{border-left:4px solid #cb9541;padding-left:18px}code{font:14px Consolas,monospace}footer{font-size:13px;color:#526976}button{background:#226d87;color:white;border:0;padding:10px 14px;cursor:pointer;border-radius:5px}a{color:#226d87}@media(max-width:600px){main{padding:18px 10px}.panel{padding:10px}}
</style></head><body><main><p class="etiqueta">Hidrología · Documento en construcción · Paso 1</p><h1>Cuenca del río La Vieja</h1><p>Series mensuales de precipitación y caudal hasta la estación Cartago · IDEAM 26127040.</p>
<div class="ficha"><p><b>1981–2022</b><br>Periodo analizado</p><p><b>2.797,19 km²</b><br>Área CAMELS</p><p><b>485 / 504</b><br>Meses completos</p><p><b>19 meses</b><br>Excluidos, sin relleno</p></div>
<section class="panel"><h2>1. Series cronológicas mensuales</h2><p>La precipitación se suma y el caudal se promedia a partir de los registros diarios. Solo se conservan meses con el 100 % de días válidos. Las franjas grises indican meses excluidos; las cruces permiten consultar sus días disponibles y <b>no representan valores cero</b>.</p><p>Selecciona un intervalo con el ratón o con la barra inferior. Ambos paneles comparten el tiempo. Doble clic para restablecer la vista; la cámara exporta un SVG.</p>'''+graph+'''<button onclick="Plotly.relayout('series-mensuales',{'xaxis.range':['1981-01-01','2023-01-01'],'xaxis2.range':['1981-01-01','2023-01-01'],'yaxis.autorange':true,'yaxis2.autorange':true})">Ver todo el periodo</button></section>
<section class="panel"><h2>Cómo se construyeron las series</h2><p><code>P mensual = suma de P diaria</code> (mm/mes). <code>Q mensual = media de Q diaria</code> (m³/s). Hay 255 días ausentes de 15.340 esperados (1,66 %). No se rellenan ni prorratean datos, ni se eliminan extremos por su magnitud.</p><p>Fuente: CAMELS-COL, DOI 10.5281/zenodo.18794895. La lluvia procede de CHIRPS v2 promediada sobre la cuenca; el caudal es observado según la descripción del depósito. Las fechas y valores son los mismos que en el documento LaTeX.</p><p class="nota">Esta primera entrega contiene P de referencia y Q. IMERG permanece pendiente; el panel posterior muestra Tmin, Tmax y Tmedia estimada. Los registros de las estaciones pluviométricas inventariadas no se han incorporado a estas series.</p></section>
<section class="panel"><h2>Lectura inicial</h2><p>Las series muestran oscilaciones estacionales y diferencias entre años. El máximo mensual de lluvia es octubre de 2022 (407,57 mm); el máximo de caudal es noviembre de 2010 (508,77 m³/s). Su falta de coincidencia no constituye un error: son variables distintas y se deben estudiar los aportes previos y la respuesta de la cuenca.</p><p>Los vacíos permanecen visibles para evitar interpretar líneas artificiales como observaciones. Estas gráficas no demuestran tendencias ni causas físicas; los siguientes apartados ampliarán la exploración.</p></section>
<footer>HTML autocontenido: datos y biblioteca Plotly incluidos. Se abre directamente, sin servidor ni conexión a Internet. Documento ampliable por pasos.</footer></main></body></html>'''
(DOC/'informe_interactivo.html').write_text(html,encoding='utf-8')
(DOC/'datos_graficados.csv').write_bytes(source.read_bytes())
(DOC/'proveniencia.json').write_text(json.dumps({'fuente':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'filas':len(data),'P_validos':int(data.P_mm.notna().sum()),'Q_validos':int(data.Q_m3_s.notna().sum()),'html':'Plotly incluido en linea; sin CDN','versiones':{n:importlib.metadata.version(n) for n in ['pandas','matplotlib','plotly']}},indent=2),encoding='utf-8')
(DOC/'requirements.txt').write_text('\n'.join(n+'=='+importlib.metadata.version(n) for n in ['pandas','numpy','matplotlib','plotly'])+'\n',encoding='utf-8')
print('Figura PDF/PNG y HTML autocontenido generados en:',DOC)
# Conservar el segundo apartado al regenerar el documento por pasos.
if (LATEX/'secciones'/'02_control_faltantes.tex').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'13_control_faltantes_documentos.py'),run_name='__main__')
if (LATEX/'secciones'/'03_estadistica_por_ano.tex').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'14_estadisticas_por_ano.py'),run_name='__main__')
if (ROOT/'scripts'/'15_grafica_cobertura_mensual.py').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'15_grafica_cobertura_mensual.py'),run_name='__main__')
if (ROOT/'scripts'/'16_procedencia_alcance.py').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'16_procedencia_alcance.py'),run_name='__main__')
if (ROOT/'la_vieja'/'topografia'/'metadatos_dem.json').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'18_temperatura_dispersion_mapas.py'),run_name='__main__')
if (LATEX/'secciones'/'06_histogramas_estadisticos.tex').exists():
    import runpy
    runpy.run_path(str(ROOT/'scripts'/'19_histogramas_estadisticas.py'),run_name='__main__')

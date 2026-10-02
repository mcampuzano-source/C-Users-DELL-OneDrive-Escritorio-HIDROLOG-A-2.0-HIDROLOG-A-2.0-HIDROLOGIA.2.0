"""Tercera gráfica interactiva: porcentaje de días válidos por mes vs tiempo."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
a=pd.read_csv(ROOT/'la_vieja'/'punto_1'/'disponibilidad_mensual.csv',parse_dates=['mes'])
assert a.dias_validos_P.equals(a.dias_validos_Q)
pct=100*a.dias_validos_P/a.dias_esperados
assert len(pct)==504 and pct.eq(100).sum()==485 and pct.eq(0).sum()==6
custom=list(zip(a.dias_validos_P,a.dias_esperados,a.dias_faltantes_P))
fig=go.Figure(go.Scatter(x=a.mes,y=pct.tolist(),customdata=custom,mode='lines+markers',name='Cobertura P y Q',line={'color':'#287d83','width':1.3},marker={'size':4},hovertemplate='%{x|%Y-%m}<br>Días válidos: %{y:.2f}%<br>%{customdata[0]} de %{customdata[1]} días<br>Faltantes: %{customdata[2]}<extra></extra>'))
fig.add_hline(y=100,line_dash='dot',line_color='#606060')
fig.update_layout(height=410,template='plotly_white',margin={'l':65,'r':25,'t':45,'b':45},hovermode='x unified',showlegend=False,yaxis={'title':'Días válidos del mes (%)','range':[-3,105],'ticksuffix':'%'},xaxis={'title':'Año','tickformat':'%Y','range':['1981-01-01','2023-01-01'],'rangeslider':{'visible':True,'thickness':.12},'rangeselector':{'buttons':[{'count':5,'label':'5 años','step':'year','stepmode':'backward'},{'count':10,'label':'10 años','step':'year','stepmode':'backward'},{'step':'all','label':'Todo'}]}})
plot=fig.to_html(full_html=False,include_plotlyjs=False,div_id='cobertura-mensual-cronologica',config={'responsive':True,'displaylogo':False,'toImageButtonOptions':{'format':'svg','filename':'cobertura_mensual_la_vieja'}})
start='<!-- COBERTURA_CRONO_INICIO -->'; end='<!-- COBERTURA_CRONO_FIN -->'
section=start+'''<section class="panel" id="grafica-cobertura"><h2>Tercera gráfica: cobertura diaria de cada mes</h2><p>Cada punto representa un mes entre 1981 y 2022. Su altura es <b>100 × días válidos / días esperados del mes</b>. La misma curva corresponde a precipitación y caudal, porque sus fechas faltantes coinciden.</p><p>Un 100 % identifica un mes completo; un 0 % indica que todos sus días faltan, <b>no que la lluvia o el caudal sean cero</b>. Los porcentajes intermedios corresponden a meses parciales. Las líneas solo guían la lectura entre puntos mensuales.</p>'''+plot+'''<p>Usa la barra inferior para ampliar un intervalo y pasa el cursor por los puntos para consultar la fecha y los conteos. Hay 485 meses completos, 13 parciales y 6 sin datos.</p></section>'''+end
path=DOC/'informe_interactivo.html'; html=path.read_text(encoding='utf-8')
if start in html:
    left,rest=html.split(start,1); _,right=rest.split(end,1); html=left+right
html=html.replace('</section>','</section>'+section,1)
path.write_text(html,encoding='utf-8')
print('Tercera gráfica añadida: 504 porcentajes mensuales y curva común P/Q.')

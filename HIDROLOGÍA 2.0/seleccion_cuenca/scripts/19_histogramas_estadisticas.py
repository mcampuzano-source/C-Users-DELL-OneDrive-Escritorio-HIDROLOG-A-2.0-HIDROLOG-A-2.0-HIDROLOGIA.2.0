"""Histogramas y estadísticos completos; periodos y unidades explícitos."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT=Path(__file__).resolve().parents[1]; DOC=ROOT/'la_vieja'/'documentos'; LATEX=DOC/'latex'
m=pd.read_csv(DOC/'datos_graficados.csv',parse_dates=['mes']).set_index('mes')
t=pd.read_csv(DOC/'temperaturas_mensuales.csv',parse_dates=['mes']).set_index('mes')
m=m.join(t)
variables=[('P_mm','P CHIRPS','mm/mes'),('Q_m3_s','Q observado','m³/s'),('R_mm','R escorrentía','mm/mes'),('Temperatura_minima','Media mensual Tmin','°C'),('Temperatura_maxima','Media mensual Tmax','°C'),('Tmedia_estimada','Tmedia estimada','°C')]
statrows=[]; bins=[]
fig,axes=plt.subplots(2,3,figsize=(10,6.2),layout='constrained')
plot=make_subplots(rows=2,cols=3,subplot_titles=[v[1] for v in variables],vertical_spacing=.22,horizontal_spacing=.09)
for i,(col,label,unit) in enumerate(variables):
    s=m[col].dropna(); q=s.quantile([.05,.1,.25,.5,.75,.9,.95],interpolation='linear')
    stats={'Variable':label,'Unidad':unit,'Periodo':'1981-01 a 2022-12','Meses válidos':len(s),'Media':s.mean(),'Mediana':s.median(),'Desv. estándar':s.std(ddof=1),'Mínimo':s.min(),'Máximo':s.max(),'Rango':s.max()-s.min(),'Q1 (25%)':q.loc[.25],'Q2 (50%)':q.loc[.5],'Q3 (75%)':q.loc[.75],'IQR':q.loc[.75]-q.loc[.25],'P5':q.loc[.05],'P10':q.loc[.1],'P90':q.loc[.9],'P95':q.loc[.95],'Meses con cero':int(s.eq(0).sum())}
    statrows.append(stats)
    edges=np.histogram_bin_edges(s,bins='fd'); counts,_=np.histogram(s,bins=edges)
    assert counts.sum()==len(s)==485
    bins.append({'variable':label,'unidad':unit,'metodo':'Freedman-Diaconis numpy','limites':edges.tolist(),'conteos':counts.tolist()})
    ax=axes.flat[i]; color=['#277da8','#bd6036','#36836d','#328dc2','#cc6454','#739447'][i]
    ax.bar((edges[:-1]+edges[1:])/2,100*counts/len(s),width=np.diff(edges),color=color,edgecolor='white',linewidth=.5)
    ax.axvline(s.mean(),color='black',ls='--',lw=.8,label='Media')
    ax.axvline(s.median(),color='#812756',ls=':',lw=1,label='Mediana')
    ax.set_title(f'{label} · n={len(s)}',fontsize=9); ax.set_xlabel(unit); ax.set_ylabel('Meses (%)'); ax.legend(fontsize=6)
    row,colidx=i//3+1,i%3+1
    plot.add_trace(go.Bar(x=((edges[:-1]+edges[1:])/2).tolist(),y=(100*counts/len(s)).tolist(),width=np.diff(edges).tolist(),marker_color=color,name=label,customdata=np.column_stack([edges[:-1],edges[1:],counts]).tolist(),hovertemplate='Clase: %{customdata[0]:.2f}–%{customdata[1]:.2f}<br>Meses: %{customdata[2]}<br>Frecuencia: %{y:.2f}%<extra>%{fullData.name}</extra>'),row=row,col=colidx)
    plot.update_xaxes(title_text=unit,row=row,col=colidx); plot.update_yaxes(title_text='Meses (%)',rangemode='tozero',row=row,col=colidx)
fig.suptitle('Distribución mensual · 1981–2022 · solo meses completos\nClases Freedman–Diaconis; se mezclan los meses de todas las estaciones del año',fontsize=10)
fig.savefig(LATEX/'figuras'/'histogramas_completos.pdf',bbox_inches='tight'); fig.savefig(LATEX/'figuras'/'histogramas_completos.png',dpi=200,bbox_inches='tight'); plt.close(fig)
plot.update_layout(height=760,template='plotly_white',showlegend=False,bargap=0)
df=pd.DataFrame(statrows); df.to_csv(DOC/'estadisticos_completos.csv',index=False,encoding='utf-8-sig')
df.to_excel(DOC/'Estadisticos_completos.xlsx',index=False)
(DOC/'histogramas_clases.json').write_text(json.dumps(bins,ensure_ascii=False,indent=2),encoding='utf-8')
inv=pd.read_csv(ROOT/'resultados'/'estaciones_dentro_cuencas.csv',dtype={'codigo':str})
station_codes=['0026120160','0026120150','0026125130','0026125060']
example=inv[(inv.cuenca_codigo==26127040)&inv.codigo.isin(station_codes)][['codigo','nombre','categoria','estado']]
example.to_csv(DOC/'ejemplos_estaciones_insitu.csv',index=False,encoding='utf-8-sig')
method='''<p><b>Periodo:</b> enero de 1981–diciembre de 2022. Todas las variables tienen 485 meses válidos de 504. Se excluyen los meses con cualquier día faltante (19), sin relleno ni eliminación automática de extremos; los ceros se conservan. Las distribuciones reúnen los meses de todas las estaciones del año, no la variabilidad de un único mes calendario.</p><p><b>Unidades y agregación:</b> P es precipitación CHIRPS acumulada (mm/mes), Q es caudal medio (m³/s), R es lámina de escorrentía (mm/mes); Tmin/Tmax son promedios mensuales de extremos diarios MSWX (°C) y Tmedia es estimada. <code>R = 86,4 / 2797,19 × suma(Q_diario)</code>. Si Q ya estuviera expresado en lámina diaria, no se repetiría esa conversión. R es una transformación de Q y no una observación independiente.</p><p><b>Convención de percentiles:</b> interpolación lineal, tipo 7. Ordenados los n valores, se toma <code>h = (n−1)·p</code>, con p entre 0 y 1; se interpola entre las posiciones vecinas de h usando índices desde cero. No hay conversión de unidades para calcular percentiles: mantienen la unidad de la variable. Q1, Q2 y Q3 corresponden a los percentiles 25, 50 y 75; <code>IQR = Q3−Q1</code>. La desviación estándar usa divisor n−1.</p><p><b>Histogramas:</b> clases Freedman–Diaconis, amplitud teórica <code>2·IQR/n^(1/3)</code>; NumPy ajusta el número entero de clases al rango. Las barras muestran porcentaje de meses, no densidad; sus frecuencias suman 100 %. Se guardan límites y conteos. Cuando se incorpore otra fuente de lluvia, se comparará con P usando los mismos meses y bordes de clase.</p>'''
local='''<h3>Precipitación in situ: estaciones identificadas</h3><p>Sí existen registros terrestres distintos de CHIRPS. El POMCA de La Vieja, capítulo de clima, documenta precipitación de estaciones como Salento, Alcalá, Cumbarco y Aeropuerto El Edén. Son mediciones puntuales; para representar toda la cuenca habría que evaluar cobertura espacial, años comunes, faltantes y ponderación.</p>'''+example.to_html(index=False,border=0)+'''<p>Fuente: <a href="https://www.cvc.gov.co/sites/default/files/Planes_y_Programas/Planes_de_Ordenacion_y_Manejo_de_Cuencas_Hidrografica/La%20Vieja%20-%20POMCA%20en%20Ajuste/Fase%20Diagnostico/3_CapituloI_Diagnostico_Clima.pdf">POMCA La Vieja, tabla 3.7</a>. Esas climatologías publicadas no sustituyen una serie cronológica de 25 años. Los histogramas aquí presentados siguen usando CHIRPS: no se han incorporado datos terrestres sin auditar.</p>'''
section='<!-- HISTOGRAMAS_INICIO --><section class="panel" id="histogramas"><h2>7. Histogramas y estadísticos completos</h2>'+method+plot.to_html(full_html=False,include_plotlyjs=False,div_id='histogramas-completos',config={'responsive':True,'displaylogo':False})+'<h3>Tabla descriptiva</h3><div style="overflow:auto">'+df.to_html(index=False,border=0,classes='tabla-estadistica',float_format=lambda v:f'{v:.2f}')+'</div>'+local+'</section><!-- HISTOGRAMAS_FIN -->'
path=DOC/'informe_interactivo.html'; html=path.read_text(encoding='utf-8')
if '<!-- HISTOGRAMAS_INICIO -->' in html:
    left,rest=html.split('<!-- HISTOGRAMAS_INICIO -->',1); _,right=rest.split('<!-- HISTOGRAMAS_FIN -->',1); html=left+right
marker='<!-- PROCEDENCIA_INICIO -->'; html=html.replace(marker,section+marker,1); path.write_text(html,encoding='utf-8')
metrics=['Meses válidos','Media','Mediana','Desv. estándar','Mínimo','Máximo','Rango','Q1 (25%)','Q2 (50%)','Q3 (75%)','IQR','P5','P10','P90','P95','Meses con cero']
tables=[]
for idxs,title in [([0,1,2],r'P (mm/mes), Q (m$^3$/s) y R (mm/mes)'),([3,4,5],r'Tmin, Tmax y Tmedia estimada ($^\circ$C)')]:
    headers=['P','Q','R'] if idxs[0]==0 else ['Tmin','Tmax','Tmedia estimada']
    lines=[r'\subsection*{'+title+'}',r'\begin{center}\small\begin{tabular}{lrrr}\hline','Estadístico & '+' & '.join(headers)+r' \\ \hline']
    for metric in metrics:
        vals=[str(int(df.iloc[i][metric])) if metric in ['Meses válidos','Meses con cero'] else f'{df.iloc[i][metric]:.2f}'.replace('.',',') for i in idxs]
        lines.append(metric.replace('%',r'\%')+' & '+' & '.join(vals)+r' \\')
    lines.append(r'\hline\end{tabular}\end{center}'); tables.append('\n'.join(lines))
tex=r'''\section{Histogramas y estadísticos completos}
Periodo: enero de 1981--diciembre de 2022. Se utilizan 485 meses completos por
variable; se excluyen 19 con faltantes, sin rellenos, prorrateos ni eliminación
automática de extremos. Se conservan los ceros. Se reúnen meses de distintas
estaciones del año, no la variabilidad de un único mes calendario.

P es precipitación CHIRPS acumulada (mm/mes); Q, caudal medio (m$^3$/s);
R, lámina de escorrentía (mm/mes). Se convierte con
$R_m=(86.4/2797.19)\sum Q_d$. R no es una observación independiente de Q.
Tmin/Tmax son medias mensuales de extremos diarios MSWX y Tmedia es estimada.

La desviación estándar es muestral, con divisor $n-1$. Para percentiles se utiliza
interpolación lineal (tipo 7): ordenados los valores, $h=(n-1)p$, con índices
desde cero, interpolando entre los vecinos de $h$. Se mantienen las unidades;
no hay una conversión de unidades para percentiles. Q1, Q2 y Q3 son los
percentiles 25, 50 y 75, e IQR = Q3--Q1.

Los histogramas usan Freedman--Diaconis, amplitud teórica $2\,IQR/n^{1/3}$;
NumPy ajusta el número entero de clases al rango. Se muestran porcentajes de
meses, no densidades; las frecuencias suman 100\,\%. Se guardan bordes y conteos.
Cuando se disponga de otra fuente de lluvia, se usarán meses comunes y clases
iguales para comparar sus distribuciones.
\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{figuras/histogramas_completos.pdf}
\caption{Distribuciones de meses válidos, 1981--2022; unidades indicadas en cada panel.}
\end{figure}
'''+ '\n'.join(tables)+r'''
\subsection{Precipitación in situ: existencia y alcance}
Sí existen mediciones terrestres distintas de CHIRPS. El POMCA La Vieja,
capítulo 3, tabla 3.7, documenta registros de Salento (26120160), Alcalá
(26120150), Cumbarco (26125130) y Aeropuerto El Edén (26125060).
Son mediciones puntuales; un promedio de cuenca requiere evaluar periodos,
faltantes, distribución espacial y ponderación. Fuente:
\href{https://www.cvc.gov.co/sites/default/files/Planes_y_Programas/Planes_de_Ordenacion_y_Manejo_de_Cuencas_Hidrografica/La%20Vieja%20-%20POMCA%20en%20Ajuste/Fase%20Diagnostico/3_CapituloI_Diagnostico_Clima.pdf}{POMCA La Vieja, capítulo Clima}.

Las climatologías publicadas no sustituyen una serie cronológica de 25 años.
No se han incorporado registros terrestres sin auditar: los histogramas de
precipitación de este documento corresponden a CHIRPS.
'''
(LATEX/'secciones'/'06_histogramas_estadisticos.tex').write_text(tex,encoding='utf-8')
main=LATEX/'informe.tex'; text=main.read_text(encoding='utf-8')
if r'\input{secciones/06_histogramas_estadisticos}' not in text:
    text=text.replace(r'\input{secciones/04_procedencia_alcance}',r'\input{secciones/06_histogramas_estadisticos}'+'\n'+r'\clearpage'+'\n'+r'\input{secciones/04_procedencia_alcance}')
main.write_text(text,encoding='utf-8')
print(df[['Variable','Meses válidos','Media','P5','P95']].to_string(index=False))

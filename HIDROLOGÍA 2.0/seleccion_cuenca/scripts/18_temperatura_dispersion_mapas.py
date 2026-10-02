"""Añade temperatura, dispersión disponible y mapas sin sustituir IMERG ausente."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from shapely.geometry import shape
from pyproj import Geod
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'; LATEX=DOC/'latex'; FIG=LATEX/'figuras'
TOPO=ROOT/'la_vieja'/'topografia'
meta=json.loads((TOPO/'metadatos_dem.json').read_text(encoding='utf-8'))
monthly=pd.read_csv(DOC/'datos_graficados.csv',parse_dates=['mes']).set_index('mes')
daily=pd.read_csv(ROOT/'la_vieja'/'punto_1'/'diario_calendario_completo.csv',parse_dates=['fecha']).set_index('fecha')
t=daily[['Temperatura_minima','Temperatura_maxima']].copy()
assert not (t.Temperatura_minima>t.Temperatura_maxima).any()
t['Tmedia_estimada']=(t.Temperatura_minima+t.Temperatura_maxima)/2
temp=t.resample('MS').mean()
count=t.resample('MS').count()
temp=temp.where(count.eq(count.index.days_in_month,axis=0))
assert temp.notna().sum().eq(485).all()
assert np.allclose(temp.Tmedia_estimada,(temp.Temperatura_minima+temp.Temperatura_maxima)/2,equal_nan=True)
temp.to_csv(DOC/'temperaturas_mensuales.csv',index_label='mes')
paired=monthly[['P_mm','Q_m3_s']].dropna()
r=float(paired.P_mm.corr(paired.Q_m3_s))
rho=float(paired.P_mm.rank().corr(paired.Q_m3_s.rank()))
(DOC/'dispersion_CHIRPS_Q.json').write_text(json.dumps({'n':len(paired),'periodo':'1981-2022','Pearson':r,'Spearman':rho,'rezago_meses':0,'precipitacion':'CHIRPS, no estación en tierra','IMERG':'no descargado; acceso NASA sin autenticar: HTTP 401','lluvia_estaciones':'sin series descargadas; inventario no es registro'},indent=2),encoding='utf-8')
plt.rcParams.update({'font.size':9,'pdf.fonttype':42})
def save(fig,name):
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(FIG/(name+'.png'),dpi=200,bbox_inches='tight')
    plt.close(fig)

fig,ax=plt.subplots(figsize=(7,3.4),layout='constrained')
temp_fig=go.Figure()
for var,label,color in [('Temperatura_minima','Media mensual de Tmin','#2a78ac'),('Temperatura_maxima','Media mensual de Tmax','#c25336'),('Tmedia_estimada','Tmedia estimada: (Tmin + Tmax)/2','#4b854b')]:
    ax.plot(temp.index,temp[var],label=label,color=color,lw=.75)
    temp_fig.add_trace(go.Scatter(x=temp.index,y=[None if pd.isna(v) else float(v) for v in temp[var]],name=label,connectgaps=False,line={'color':color},hovertemplate='%{x|%Y-%m}<br>%{y:.2f} °C<extra>%{fullData.name}</extra>'))
for date in temp.index[temp.Tmedia_estimada.isna()]:
    ax.axvspan(date,date+pd.offsets.MonthBegin(1),color='#aaa',alpha=.2,lw=0)
ax.set_ylabel('Temperatura (°C)'); ax.set_xlabel('Año'); ax.legend(fontsize=7,ncol=1)
ax.xaxis.set_major_locator(mdates.YearLocator(5)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y')); ax.grid(alpha=.2)
save(fig,'temperaturas_mensuales')
temp_fig.update_layout(template='plotly_white',height=440,hovermode='x unified',yaxis_title='Temperatura (°C)',legend={'orientation':'h','y':1.2},xaxis={'title':'Año','rangeslider':{'visible':True}})

fig,ax=plt.subplots(figsize=(6,4.2),layout='constrained')
sc=ax.scatter(paired.P_mm,paired.Q_m3_s,c=paired.index.month,cmap='twilight',vmin=.5,vmax=12.5,s=15,alpha=.7,edgecolors='none')
ax.set_xlabel('Precipitación CHIRPS (mm/mes)'); ax.set_ylabel('Caudal medio (m³/s)'); ax.grid(alpha=.2)
ax.set_title(f'Meses simultáneos: n={len(paired)}; Pearson={r:.2f}; Spearman={rho:.2f}',fontsize=9)
fig.colorbar(sc,ax=ax,label='Mes calendario',ticks=range(1,13))
save(fig,'dispersion_CHIRPS_caudal')
scatter=go.Figure(go.Scatter(x=paired.P_mm.tolist(),y=paired.Q_m3_s.tolist(),mode='markers',customdata=paired.index.strftime('%Y-%m').tolist(),marker={'color':paired.index.month.tolist(),'colorscale':'Twilight','cmin':.5,'cmax':12.5,'size':7,'opacity':.75,'colorbar':{'title':'Mes','tickvals':list(range(1,13))}},hovertemplate='%{customdata}<br>CHIRPS: %{x:.2f} mm/mes<br>Q: %{y:.2f} m³/s<extra></extra>'))
scatter.update_layout(template='plotly_white',height=470,xaxis_title='Precipitación CHIRPS (mm/mes)',yaxis_title='Caudal medio (m³/s)',title=f'Meses simultáneos · n={len(paired)} · Pearson={r:.2f} · Spearman={rho:.2f}')

# Mapas con coordenadas y elevación locales: no dependen de teselas externas.
geo=json.loads((TOPO/'cuenca_la_vieja.geojson').read_text(encoding='utf-8'))
poly=shape(geo['features'][0]['geometry'])
parts=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
inv=pd.read_csv(ROOT/'resultados'/'estaciones_dentro_cuencas.csv',dtype={'codigo':str})
stations=inv[(inv.cuenca_codigo==26127040)&inv.lluvia_por_categoria&inv.activa].copy()
assert len(stations)==92
catalog=json.loads((ROOT/'datos'/'catalogo_ideam.json').read_text(encoding='utf-8'))
gauge=next(s for s in catalog if int(s['codigo'])==26127040)
gx,gy=float(gauge['longitud']),float(gauge['latitud'])
small=np.load(TOPO/'relieve_visualizacion.npz'); x,y,z=small['x'],small['y'],small['z']
west,south,east,north=poly.bounds
def map_axes(ax):
    for part in parts:
        px,py=part.exterior.xy; ax.plot(px,py,color='#243b44',lw=.8)
        for hole in part.interiors:
            hx,hy=hole.xy; ax.plot(hx,hy,color='#243b44',lw=.5)
    ax.scatter([gx],[gy],marker='*',s=100,color='#c62628',edgecolors='white',label='Cartago · 26127040',zorder=5)
    ax.set_xlim(west-.035,east+.035); ax.set_ylim(south-.035,north+.035)
    ax.set_aspect(1/np.cos(np.deg2rad((south+north)/2)))
    ax.set_xlabel('Longitud (°)'); ax.set_ylabel('Latitud (°)'); ax.grid(alpha=.2)
    ax.annotate('N',xy=(.92,.94),xytext=(.92,.82),xycoords='axes fraction',ha='center',arrowprops={'arrowstyle':'->'})
    startx,starty=west+.035,south+.025
    endx,endy,_=Geod(ellps='WGS84').fwd(startx,starty,90,10000)
    ax.plot([startx,endx],[starty,endy],color='black',lw=2)
    ax.text((startx+endx)/2,starty+.012,'10 km',ha='center',fontsize=7)
    ax.legend(fontsize=7,loc='upper right',bbox_to_anchor=(1,1.12))

fig,ax=plt.subplots(figsize=(6,6.3),layout='constrained')
ax.scatter(stations.longitud_num,stations.latitud_num,s=10,c='#2472a0',alpha=.75,label='92 estaciones activas de lluvia')
map_axes(ax); ax.set_title('La Vieja: delimitación y red terrestre inventariada',fontsize=10)
save(fig,'mapa_cuenca_estaciones')
fig,ax=plt.subplots(figsize=(6,6.3),layout='constrained')
im=ax.imshow(z,extent=[x[0],x[-1],y[-1],y[0]],origin='upper',cmap='terrain',vmin=900,vmax=4800)
map_axes(ax); ax.set_title('Relieve de La Vieja · Copernicus GLO-30',fontsize=10)
fig.colorbar(im,ax=ax,label='Elevación (m, EGM2008)',shrink=.7)
save(fig,'mapa_relieve')

def map_plot(relief=False):
    f=go.Figure()
    if relief:
        zz=[[None if not np.isfinite(v) else round(float(v),1) for v in row] for row in z]
        f.add_trace(go.Heatmap(x=x.tolist(),y=y.tolist(),z=zz,colorscale='Earth',zmin=900,zmax=4800,colorbar={'title':'m'},hovertemplate='Lon %{x:.4f}<br>Lat %{y:.4f}<br>Elevación aproximada: %{z:.0f} m<extra></extra>'))
    else:
        f.add_trace(go.Scatter(x=stations.longitud_num.tolist(),y=stations.latitud_num.tolist(),mode='markers',name='92 estaciones activas de lluvia',marker={'size':6,'color':'#2472a0'},text=(stations.nombre+' · '+stations.categoria).tolist(),hovertemplate='%{text}<br>Lon %{x:.4f}, lat %{y:.4f}<extra></extra>'))
    for i,part in enumerate(parts):
        px,py=part.exterior.xy
        f.add_trace(go.Scatter(x=list(px),y=list(py),mode='lines',name='Límite CAMELS',showlegend=i==0,line={'color':'#20343e','width':1.2},hoverinfo='skip'))
    f.add_trace(go.Scatter(x=[gx],y=[gy],mode='markers',marker={'symbol':'star','size':15,'color':'#d92d29'},name='Cartago · 26127040',hovertemplate='Estación Cartago · 26127040<br>Lon %{x:.5f}, lat %{y:.5f}<extra></extra>'))
    f.update_layout(height=650,template='plotly_white',legend={'orientation':'h','y':1.1},xaxis={'title':'Longitud (°)','range':[west-.035,east+.035]},yaxis={'title':'Latitud (°)','range':[south-.035,north+.035],'scaleanchor':'x','scaleratio':1/np.cos(np.deg2rad((south+north)/2))})
    return f
def embed(fig,id):
    return fig.to_html(full_html=False,include_plotlyjs=False,div_id=id,config={'responsive':True,'displaylogo':False,'toImageButtonOptions':{'format':'svg','filename':id}})

section='''<!-- AMPLIACION_INICIO --><section class="panel" id="temperatura"><h2>4. Temperatura mensual</h2><p>Se añade la media mensual de las temperaturas mínimas y máximas diarias de MSWX, promediadas sobre la cuenca en CAMELS. No son la mínima y máxima absolutas de cada mes.</p><p><b>La temperatura media es estimada:</b> para cada día se calcula (Tmin + Tmax)/2 y después se promedian los días del mes. No equivale necesariamente a una media obtenida de observaciones horarias. Se exigen todos los días válidos: 485 meses por curva, con vacíos conservados.</p>'''+embed(temp_fig,'temperaturas-mensuales')+'''</section><section class="panel" id="dispersiones"><h2>5. Diagramas de dispersión y disponibilidad</h2><p>Se presenta la comparación que puede calcularse con los datos disponibles: <b>CHIRPS frente a caudal</b>, con meses simultáneos y colores por mes calendario. CHIRPS no es una estación terrestre.</p>'''+embed(scatter,'dispersion-chirps-q')+'''<p>La asociación contiene el ciclo anual compartido y no demuestra causalidad ni capacidad de pronóstico. Los coeficientes son descriptivos; no se ha evaluado su significancia considerando dependencia temporal.</p><ul><li><b>IMERG frente a precipitación de estaciones:</b> pendiente de valores IMERG y registros terrestres verificados.</li><li><b>Precipitación terrestre frente a caudal:</b> pendiente de registros terrestres; la gráfica anterior utiliza CHIRPS.</li><li><b>IMERG frente a caudal:</b> pendiente de descargar IMERG. La comprobación del acceso NASA devolvió HTTP 401 y el grupo no dispone de acceso actualmente.</li></ul><p>No se generan puntos ficticios ni se renombra CHIRPS como IMERG. El catálogo de estaciones solo identifica instalaciones, no contiene aquí sus series de lluvia.</p></section><section class="panel" id="mapas"><h2>6. Mapas de la cuenca y topografía</h2><h3>Delimitación y estaciones en tierra</h3><p>Polígono CAMELS transformado de EPSG:3395 a WGS84; ubicación de Cartago según catálogo IDEAM. Los 92 puntos corresponden a estaciones activas de categorías que miden lluvia, según el inventario consultado. No se ha verificado la continuidad de sus registros. Los ejes geográficos y los datos están incluidos en el HTML, sin mapa base externo.</p>'''+embed(map_plot(),'mapa-estaciones')+'''<h3>Relieve Copernicus GLO-30</h3><p>Se descargó el mosaico N04/W076 de Copernicus DEM GLO-30 público y se recortó a toda la cuenca. Se conserva el GeoTIFF a resolución nominal de unos 30 m; la visualización usa un promedio a una malla menor para facilitar la interacción. Copernicus es un modelo de superficie (DSM), que puede incluir vegetación y construcciones, no un terreno desnudo.</p>'''+embed(map_plot(True),'mapa-relieve')+f'''<p>Resumen exploratorio del recorte: elevación mínima {meta['min_m']:.1f} m, media de píxeles {meta['media_pixeles_m']:.1f} m y máxima {meta['max_m']:.1f} m. CAMELS reporta respectivamente 940,54, 1.826,21 y 4.795 m; las diferencias entre modelos, máscara y resolución requieren consideración, no se sustituyen silenciosamente los atributos.</p><p>Referencia horizontal WGS84; alturas en metros respecto a EGM2008. No representa cambios topográficos durante 1981–2022. Fuente: <a href="https://copernicus-dem-30m.s3.amazonaws.com/readme.html">Copernicus DEM público</a>; <a href="https://doi.org/10.5270/ESA-c5d3d65">DOI Copernicus DEM</a>.</p><p style="font-size:12px">{meta['atribucion']}</p></section><!-- AMPLIACION_FIN -->'''
path=DOC/'informe_interactivo.html'; html=path.read_text(encoding='utf-8')
start='<!-- AMPLIACION_INICIO -->'; end='<!-- AMPLIACION_FIN -->'
if start in html:
    left,rest=html.split(start,1); _,right=rest.split(end,1); html=left+right
marker='<!-- PROCEDENCIA_INICIO -->' if '<!-- PROCEDENCIA_INICIO -->' in html else '<footer>'
html=html.replace(marker,section+marker,1)
path.write_text(html,encoding='utf-8')

tex=r'''\section{Temperatura mensual}
Se grafican las medias mensuales de Tmin y Tmax diarias de MSWX incluidas en
CAMELS, no los extremos absolutos del mes. La \textbf{temperatura media es estimada}:
$T_{d,\mathrm{est}}=(T_{d,\min}+T_{d,\max})/2$, seguida del promedio mensual.
No equivale necesariamente a una media de observaciones horarias. Se conservan
485 meses completos por curva y se mantienen los vacíos.
\begin{figure}[H]\centering
\includegraphics[width=\linewidth]{figuras/temperaturas_mensuales.pdf}
\caption{Medias mensuales de Tmin, Tmax y temperatura media estimada de la cuenca.}
\end{figure}

\section{Diagramas de dispersión y disponibilidad}
Con los datos disponibles se compara CHIRPS con caudal, usando meses simultáneos
y colores por mes calendario. \textbf{CHIRPS no es una estación de lluvia terrestre.}
\begin{figure}[H]\centering
\includegraphics[width=.85\linewidth]{figuras/dispersion_CHIRPS_caudal.pdf}
\caption{Relación descriptiva entre precipitación CHIRPS y caudal, sin rezago.}
\end{figure}
La correlación contiene el ciclo anual compartido y no demuestra causalidad ni
capacidad predictiva. No se evaluó significancia considerando dependencia temporal.
Las comparaciones IMERG--estaciones, estaciones--caudal e IMERG--caudal siguen
pendientes: no se dispone de valores descargados de IMERG ni series terrestres
verificadas. El acceso NASA devolvió HTTP 401 y el grupo indicó que no dispone
de acceso. No se crean puntos ficticios ni se sustituye IMERG por CHIRPS.

\clearpage
\section{Mapas de la cuenca y topografía}
\subsection{Delimitación y red terrestre inventariada}
Se utiliza el polígono CAMELS transformado a WGS84 y la ubicación de Cartago del
catálogo IDEAM. Los 92 puntos son estaciones activas de categorías que miden
lluvia; no se ha verificado la continuidad de sus series.
\begin{figure}[H]\centering
\includegraphics[width=.72\linewidth]{figuras/mapa_cuenca_estaciones.pdf}
\caption{Cuenca La Vieja hasta Cartago y estaciones terrestres inventariadas.}
\end{figure}

\subsection{Modelo de elevación descargado}
Se descargó Copernicus DEM GLO-30 público, mosaico N04/W076, y se recortó al
polígono. Se conserva el GeoTIFF a resolución nominal de unos 30 m; la figura
usa una malla reducida por promedio. Es un modelo de superficie (DSM), que puede
incluir vegetación y construcciones, no un modelo de terreno desnudo.
\begin{figure}[H]\centering
\includegraphics[width=.72\linewidth]{figuras/mapa_relieve.pdf}
\caption{Relieve de La Vieja con Copernicus GLO-30. Alturas en metros, EGM2008.}
\end{figure}
'''+f'El recorte presenta mínimo {meta["min_m"]:.1f} m, media de píxeles {meta["media_pixeles_m"]:.1f} m y máximo {meta["max_m"]:.1f} m. '+r'''
CAMELS reporta 940,54, 1826,21 y 4795 m, respectivamente. Las diferencias entre
modelos, máscaras y resolución se documentan y no sustituyen automáticamente los
atributos originales. El DSM no representa cambios durante el periodo 1981--2022.

Fuente: \href{https://doi.org/10.5270/ESA-c5d3d65}{Copernicus DEM} y
\href{https://copernicus-dem-30m.s3.amazonaws.com/readme.html}{distribución pública COG}.

{\footnotesize produced using Copernicus WorldDEM-30 \textcopyright\ DLR e.V.
2010-2014 and \textcopyright\ Airbus Defence and Space GmbH 2014-2018 provided
under COPERNICUS by the European Union and ESA; all rights reserved}
'''
(LATEX/'secciones'/'05_temperatura_dispersion_mapas.tex').write_text(tex,encoding='utf-8')
main=LATEX/'informe.tex'; content=main.read_text(encoding='utf-8')
if r'\input{secciones/05_temperatura_dispersion_mapas}' not in content:
    content=content.replace(r'\input{secciones/04_procedencia_alcance}',r'\input{secciones/05_temperatura_dispersion_mapas}'+'\n'+r'\clearpage'+'\n'+r'\input{secciones/04_procedencia_alcance}')
main.write_text(content,encoding='utf-8')
print(f'Temperatura: 485 meses. Dispersión CHIRPS–Q: n={len(paired)}, r={r:.4f}, rho={rho:.4f}. Mapas y GeoTIFF listos. IMERG/estaciones pendientes.')

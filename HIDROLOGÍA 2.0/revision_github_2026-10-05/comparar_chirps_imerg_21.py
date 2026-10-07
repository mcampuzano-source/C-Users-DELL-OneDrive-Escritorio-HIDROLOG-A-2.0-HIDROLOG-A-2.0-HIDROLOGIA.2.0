from pathlib import Path
import runpy,json,base64,re,html
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
g=runpy.run_path(str(ROOT/'completar_21.py'))
DOC=g['DOC'];OUT=g['OUT'];d=g['d'].copy();d['C']=d['P_CHIRPS_mm']
corr=g['corr'];figure=g['figure'];fmt=g['fmt'];esc=g['esc'];table=g['tex_table']
common=d[['I','C','Q','R']].dropna();assert len(common)==285
clim=common.groupby(common.index.month).mean();a=d[['I','C','Q','R']].copy()
for c in a:a[c]=d[c]-d.index.month.map(clim[c])
clim['n']=common.groupby(common.index.month).size();clim.to_csv(OUT/'climatologia_comparacion.csv',index_label='mes_calendario')
figure(d,[('C','L','CHIRPS frente a lluvia local','CHIRPS cuenca (mm/mes)','Zaragoza-AUT (mm/mes)'),('L','Q','Lluvia local frente a caudal','Zaragoza-AUT (mm/mes)','Caudal medio mensual (m³/s)'),('C','Q','CHIRPS frente a caudal','CHIRPS cuenca (mm/mes)','Caudal medio mensual (m³/s)')],'dispersiones_CHIRPS_21')
figure(a,[('C','Q','Anomalías CHIRPS–caudal','Anomalía CHIRPS (mm/mes)','Anomalía Q (m³/s)'),('C','R','Anomalías CHIRPS–escorrentía','Anomalía CHIRPS (mm/mes)','Anomalía R (mm/mes)')],'anomalias_CHIRPS_21',True)
figure(d,[('C','R','CHIRPS–escorrentía','CHIRPS cuenca (mm/mes)','Escorrentía R (mm/mes)')],'laminas_CHIRPS_21')
stats=[];errors=[];lags=[];influence=[];residuals=[]
for x,name in [('I','IMERG'),('C','CHIRPS')]:
 z=d[[x,'L']].dropna();assert len(z)==14;e=z[x]-z.L
 errors.append(dict(fuente=name,n=14,sesgo=e.mean(),MAE=e.abs().mean(),RMSE=np.sqrt(np.mean(e**2)),SD_error=e.std(ddof=1)))
 for y,ref in [('L','lluvia local'),('Q','caudal Q'),('R','escorrentía R')]:
  z=d[[x,y]].dropna();rr,rs=corr(z,x,y);stats.append(dict(fuente=name,referencia=ref,serie='original',n=len(z),Pearson=rr,Spearman=rs))
  loo=[(date,corr(z.drop(date),x,y)[0]) for date in z.index];date,rloo=max(loo,key=lambda t:abs(t[1]-rr))
  influence.append(dict(relacion=name+'–'+ref,mes=date.strftime('%Y-%m'),r_sin_mes=rloo,r_min=min(t[1] for t in loo),r_max=max(t[1] for t in loo)))
  fit=np.polyfit(z[x],z[y],1);res=z[y]-np.polyval(fit,z[x]);residuals.append(dict(fuente=name,referencia=ref,n=len(z),RMSE_residuo=np.sqrt(np.mean(res**2)),mediana_abs_residuo=np.median(np.abs(res))))
  if y in ['Q','R']:
   z=a[[x,y]].dropna();rr,rs=corr(z,x,y);stats.append(dict(fuente=name,referencia=ref,serie='anomalía',n=len(z),Pearson=rr,Spearman=rs))
   for kind,frame in [('original',d),('anomalía',a)]:
    for k in range(4):
     z=pd.concat([frame[x].shift(k).rename('x'),frame[y].rename('y')],axis=1).dropna();rr,rs=corr(z,'x','y');lags.append(dict(fuente=name,referencia=ref,serie=kind,k=k,n=len(z),Pearson=rr,Spearman=rs))
for name,data in [('correlaciones_comparadas',stats),('errores_comparados',errors),('rezagos_comparados',lags),('influencia_comparada',influence),('dispersion_residual_comparada',residuals)]:pd.DataFrame(data).to_csv(OUT/(name+'.csv'),index=False)
texts=[
('CHIRPS: los mismos diagramas y criterios','Debajo de IMERG se presentan CHIRPS–lluvia local, lluvia local–caudal y CHIRPS–caudal, con idénticas unidades y colores por mes calendario. La gráfica lluvia local–caudal se repite para conservar la estructura de tres paneles: sus datos son exactamente los mismos y no constituyen un resultado independiente. CHIRPS es precipitación espacial promediada sobre la cuenca, no una estación terrestre. La comparación CHIRPS–IMERG usa exclusivamente los mismos 14 meses completos frente a Zaragoza y los mismos 285 meses completos frente a Q/R (1998–2022). No se compara el registro CHIRPS de 485 meses con el registro IMERG de 285 para decidir qué producto se ajusta mejor.'),
('Dirección, forma, dispersión y puntos influyentes en CHIRPS','CHIRPS–lluvia local y CHIRPS–Q muestran asociación positiva. La primera nube es relativamente alineada en esta muestra pequeña, aunque todos los acumulados CHIRPS están por encima de la lluvia local (debajo de 1:1 con la orientación elegida). CHIRPS–Q tiene una nube amplia; a lluvias similares corresponden caudales diferentes y no hay una relación determinista. Los colores se solapan, sin agrupamientos separados que permitan identificar regímenes por sí solos. En ambas fuentes, los caudales altos amplían la dispersión y noviembre de 2010 debe examinarse como valor influyente. La tabla de retirar-un-mes cuantifica la sensibilidad para cada relación; se conservan todos los valores originales.'),
('¿Cuál tiene menor error frente a Zaragoza?','En los mismos 14 meses, CHIRPS tiene sesgo +86,74, MAE 86,74 y RMSE 104,14 mm/mes; IMERG tiene sesgo +109,80, MAE 109,80 y RMSE 119,61 mm/mes. CHIRPS muestra menor discrepancia con la referencia puntual en esta muestra: su RMSE es aproximadamente 12,9 % menor y su MAE 21,0 % menor. Ambos sobreestiman todos los acumulados locales seleccionados. La relación CHIRPS–local es algo más fuerte (Pearson 0,82; Spearman 0,75) que IMERG–local (0,79; 0,71), pero la correlación no mide concordancia ni demuestra mayor exactitud en toda la cuenca. Zaragoza es una referencia puntual de cobertura corta; no basta para declarar un producto superior en general.'),
('¿Cuál es más disperso? Depende de la comparación','La dispersión se cuantifica con unidades y muestras iguales. Frente a la recta 1:1 con Zaragoza, la desviación estándar muestral del error P−local es 59,80 mm/mes para CHIRPS y 49,22 para IMERG: los errores CHIRPS son más variables aunque su sesgo y RMSE totales son menores. Alrededor de la recta lineal ajustada a lluvia local, el RMSE residual es 33,59 mm/mes para CHIRPS y 35,87 para IMERG: la nube CHIRPS es algo más estrecha alrededor de su propia recta. Frente a caudal, el RMSE residual en los mismos 285 meses es 58,89 m³/s para CHIRPS y 56,85 para IMERG: IMERG tiene aproximadamente 3,5 % menos dispersión residual y una asociación algo mayor. Estas rectas son resúmenes descriptivos calculados con todos los pares, no modelos validados ni errores de pronóstico.'),
('Anomalías, rezagos y apoyo con escorrentía para CHIRPS','Se resta la climatología de cada mes calendario construida con los mismos 285 meses de 1998–2022 para CHIRPS, IMERG, Q y R. CHIRPS–Q pasa de Pearson 0,58 y Spearman 0,57 en valores originales a 0,54 y 0,54 en anomalías. IMERG–Q pasa de 0,62 y 0,63 a 0,64 y 0,60. La asociación persiste para ambas fuentes; IMERG es más fuerte en anomalías dentro de este periodo común. Se exploran P(t−k) frente a Q(t)/R(t), con k=0–3 meses, preservando el calendario y excluyendo cada par inválido. La tabla permite contrastar los rezagos sin introducir lluvia futura. R se expresa en mm/mes y deriva de Q, por lo que no constituye evidencia independiente. Para las dos parejas con lluvia local permanece la limitación: los 14 meses no sustentan una climatología local de doce meses adecuada.'),
('Conclusión comparativa del 2.1','CHIRPS se acerca más a Zaragoza en error medio y RMSE durante los 14 meses completos disponibles; IMERG se asocia algo más con el caudal y presenta menos dispersión alrededor de la recta P–Q en los 285 meses comunes, incluso después de retirar el ciclo anual. No hay un único ganador para todas las preguntas: error frente a lluvia local, variabilidad del error y asociación con caudal son criterios distintos. Ninguno de estos resultados demuestra causalidad ni una ventaja predictiva fuera de muestra. La comparación de anomalías locales requiere ampliar los registros completos de estaciones.')]
# Use exact recalculated correlations in the interpretation, rather than inherited rounded values.
cv=next(t for t in stats if t['fuente']=='CHIRPS' and t['referencia']=='caudal Q' and t['serie']=='original')
texts[4]=(texts[4][0],texts[4][1].replace('Spearman 0,57',f'Spearman {fmt(cv["Spearman"])}'))
for kind in ['original','anomalía']:
 for src in ['CHIRPS','IMERG']:
  rows=[t for t in lags if t['serie']==kind and t['fuente']==src and t['referencia']=='caudal Q'];best=max(rows,key=lambda t:t['Pearson'])
  texts[4]=(texts[4][0],texts[4][1]+f' Para {src}, en {kind}, el mayor Pearson explorado está en k={best["k"]} ({fmt(best["Pearson"])}; n={best["n"]}). No es una estimación causal del tiempo de respuesta.')
def image_html(name,caption):return '<img style="width:100%;height:auto" alt="'+caption+'" src="data:image/png;base64,'+base64.b64encode((OUT/(name+'.png')).read_bytes()).decode()+'"><p>'+caption+'</p>'
plot=image_html('dispersiones_CHIRPS_21','Los mismos tres diagramas para CHIRPS; n=14 en parejas locales y n=285 frente a Q.')
plot='<h3>CHIRPS — comparación debajo de IMERG</h3><p>'+texts[0][1]+'</p>'+plot
content='<section id="comparacion-chirps-imerg-21"><h3>CHIRPS e IMERG: desarrollo y comparación del apartado 2.1</h3>'
for idx,(title,text) in enumerate(texts[1:]):
 content+='<h3>'+title+'</h3><p>'+text+'</p>'
 if idx==1:content+=g['table_html'](pd.DataFrame(errors))
 if idx==2:content+=g['table_html'](pd.DataFrame(residuals))
 if idx==3:content+=image_html('anomalias_CHIRPS_21','Anomalías CHIRPS con climatología común.')+image_html('laminas_CHIRPS_21','CHIRPS y escorrentía en mm/mes.')
content+='<h3>Pearson y Spearman: muestras comparables</h3>'+g['table_html'](pd.DataFrame(stats))+'<h3>Influencia: retirar un mes cada vez</h3>'+g['table_html'](pd.DataFrame(influence))
content+='<h3>Rezagos CHIRPS: valores originales y anomalías</h3>'+g['table_html'](pd.DataFrame(lags).query('fuente=="CHIRPS"'))
plots=[]
for frame,kind,specs in [(d,'original',[('C','L','CHIRPS–lluvia local'),('L','Q','Lluvia local–Q (misma referencia)'),('C','Q','CHIRPS–Q'),('C','R','CHIRPS–R')]),(a,'anomalia',[('C','Q','Anomalías CHIRPS–Q'),('C','R','Anomalías CHIRPS–R')])]:
 for x,y,title in specs:
  z=frame[[x,y]].dropna();ident='scatter21-chirps-'+kind+'-'+x+y;content+='<h3>'+title+' — consulta interactiva</h3><div id="'+ident+'" style="width:100%;height:430px"></div>'
  coef=np.polyfit(z[x],z[y],1);xx=[float(z[x].min()),float(z[x].max())]
  data=[dict(x=z[x].tolist(),y=z[y].tolist(),text=z.index.strftime('%Y-%m').tolist(),mode='markers',type='scatter',marker=dict(size=8,color=z.index.month.tolist(),colorscale='Turbo',cmin=1,cmax=12,colorbar=dict(title='Mes',tickvals=list(range(1,13)))),hovertemplate='%{text}<br>x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>'),dict(x=xx,y=np.polyval(coef,xx).tolist(),mode='lines',line=dict(color='red'),hoverinfo='skip')]
  units={'C':'CHIRPS (mm/mes)','L':'Zaragoza-AUT (mm/mes)','Q':'Caudal medio Q (m³/s)','R':'Escorrentía R (mm/mes)'}
  layout=dict(title=title,showlegend=False,xaxis=dict(title=('Anomalía ' if kind=='anomalia' else '')+units[x]),yaxis=dict(title=('Anomalía ' if kind=='anomalia' else '')+units[y]),margin=dict(l=70,r=70,t=55,b=65))
  if y=='L':
   hi=float(max(z.max())*1.08);data.append(dict(x=[0,hi],y=[0,hi],mode='lines',line=dict(color='black',dash='dash'),hoverinfo='skip'));layout['xaxis']['range']=[0,hi];layout['yaxis'].update(range=[0,hi],scaleanchor='x',scaleratio=1)
  plots.append(dict(id=ident,data=data,layout=layout))
content+='<script>window.addEventListener("load",function(){const plots='+json.dumps(plots,ensure_ascii=False)+';plots.forEach(function(p){if(window.Plotly&&document.getElementById(p.id)){Plotly.newPlot(p.id,p.data,p.layout,{responsive:true,displaylogo:false,toImageButtonOptions:{format:"svg"}});}});});</script></section>'
hp=ROOT/'informe_interactivo.html';ht=hp.read_text(encoding='utf-8');marker='Tres diagramas requeridos; meses locales con cobertura completa.</p>';assert marker in ht;ht=ht.replace(marker,marker+plot,1)
end='</section><!-- DISPERSION_REQUERIDA_FIN -->';assert end in ht;ht=ht.replace(end,content+end,1);hp.write_text(ht,encoding='utf-8')
def figtex(name,cap):return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_2_1/'+name+r'.pdf}\caption{'+esc(cap)+r'}\end{figure}'+'\n'
tex=r'\subsubsection*{CHIRPS e IMERG: comparación del apartado 2.1}'+'\n'
for idx,(title,text) in enumerate(texts):
 tex+=r'\subsubsection*{'+esc(title)+'}\n'+esc(text)+'\n'
 if idx==2:tex+=table(pd.DataFrame(errors),['fuente','n','sesgo','MAE','RMSE','SD_error'],['Fuente','n','Sesgo','MAE','RMSE','SD error'])
 if idx==3:tex+=table(pd.DataFrame(residuals),['fuente','referencia','n','RMSE_residuo','mediana_abs_residuo'],['Fuente','Referencia','n','RMSE residual','Mediana abs.'])
 if idx==4:tex+=figtex('anomalias_CHIRPS_21','Anomalías CHIRPS con climatología común 1998--2022.')+figtex('laminas_CHIRPS_21','Apoyo con escorrentía mensual en láminas.')
tex+=r'\subsubsection*{Correlaciones originales y anomalías: muestras comunes}'+'\n'+table(pd.DataFrame(stats),['fuente','referencia','serie','n','Pearson','Spearman'],['Fuente','Referencia','Serie','n','Pearson','Spearman'])
tex+=r'\subsubsection*{Sensibilidad CHIRPS: retirar un mes}'+'\n'+table(pd.DataFrame(influence).query('relacion.str.startswith("CHIRPS")'),['relacion','mes','r_sin_mes','r_min','r_max'],['Relación','Mes','r sin mes','r mínimo','r máximo'])
tex+=r'\subsubsection*{Rezagos CHIRPS: calendario continuo}'+'\n'
for kind in ['original','anomalía']:
 tex+=r'\textbf{'+esc(kind)+r'.}'+table(pd.DataFrame(lags).query('fuente=="CHIRPS" and serie==@kind'),['referencia','k','n','Pearson','Spearman'],['Referencia','k','n','Pearson','Spearman'])
tp=DOC/'latex/informe_ordenado.tex';tt=tp.read_text(encoding='utf-8')
marker=r'\caption{Tres diagramas requeridos con IMERG de polígono y lluvia local completa.}\end{figure}';assert marker in tt;tt=tt.replace(marker,marker+'\n'+r'\subsubsection*{Los mismos diagramas para CHIRPS}'+figtex('dispersiones_CHIRPS_21','CHIRPS--lluvia local, lluvia local--Q y CHIRPS--Q; muestras comunes.'),1)
marker=r'\subsection{¿Se pueden construir modelos útiles?}';tt=tt.replace(marker,tex+'\n'+marker,1);tp.write_text(tt,encoding='utf-8')
(OUT/'comparacion_CHIRPS_IMERG.tex').write_text(tex,encoding='utf-8')
(OUT/'comparacion_CHIRPS_IMERG.json').write_text(json.dumps(dict(errores=errors,correlaciones=stats,dispersion_residual=residuals,influencia=influence,rezagos=lags),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(errores=errors,dispersion=residuals),ensure_ascii=False,indent=2))

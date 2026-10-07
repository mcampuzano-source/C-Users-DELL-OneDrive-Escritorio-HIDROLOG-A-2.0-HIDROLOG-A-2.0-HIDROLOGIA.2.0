from pathlib import Path
import argparse,base64,json,re,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap=argparse.ArgumentParser();ap.add_argument('--docs');args=ap.parse_args()
DOC=Path(args.docs) if args.docs else Path(__file__).resolve().parents[1]/'la_vieja/documentos'
OUT=DOC/'apartado_2_3';OUT.mkdir(exist_ok=True)
parameters=DOC/'apartado_2_2/resultados.json';frozen=parameters.read_bytes();model=json.loads(frozen)
data=pd.read_csv(DOC/'imerg_poligono/series_alineadas.csv',parse_dates=['mes']).set_index('mes').asfreq('MS').loc['1998':'2022']
data=data.rename(columns={'P_IMERG_poligono_mm':'IMERG','P_CHIRPS_mm':'CHIRPS','Q_m3_s':'Q'})
for s in ['IMERG','CHIRPS']:data[s+'_lag1']=data[s].shift(1)
fields=['Q','IMERG','CHIRPS','IMERG_lag1','CHIRPS_lag1'];valid=data[fields].dropna();test=valid.loc['2017':'2022'];dev=valid.loc[:'2016-12']
assert len(test)==68 and len(dev)==206
def metrics(y,p):
 e=np.asarray(p)-np.asarray(y);den=np.sum((y-np.mean(y))**2)
 return dict(n=len(y),RMSE=float(np.sqrt(np.mean(e**2))),MAE=float(np.mean(abs(e))),sesgo=float(np.mean(e)),NSE=float(1-np.sum(e**2)/den) if den else None,PBIAS=float(100*np.sum(e)/np.sum(y)))
def fmt(v,n=2):return f'{v:.{n}f}'.replace('.',',')
pred=test.copy();phys=[];summary=[];year=[];month=[];strata=[]
threshold=float(dev.Q.quantile(.75))
for s in ['IMERG','CHIRPS']:
 a,b,c=model['Q_modelos'][s]['modelo_coef']['coef'];raw=a+b*test[s]+c*test[s+'_lag1'];pred[s+'_estimado']=np.maximum(raw,0)
 outside=(test[s]<dev[s].min())|(test[s]>dev[s].max())|(test[s+'_lag1']<dev[s+'_lag1'].min())|(test[s+'_lag1']>dev[s+'_lag1'].max())
 phys.append(dict(fuente=s,raw_min=float(raw.min()),raw_max=float(raw.max()),negativos_truncados=int((raw<0).sum()),meses_fuera_rango_P=int(outside.sum()),meses_extrapolados=test.index[outside].strftime('%Y-%m').tolist()))
base=model['Q_coeficientes']['IMERG_media'];pred['Media']=base['coef'][0]
clim=model['Q_coeficientes']['IMERG_climatologia']['monthly'];pred['Climatologia']=[clim[str(mm)] for mm in pred.index.month]
for s,col in [('IMERG','IMERG_estimado'),('CHIRPS','CHIRPS_estimado'),('Media','Media'),('Climatologia','Climatologia')]:
 summary.append(dict(fuente=s,**metrics(pred.Q,pred[col])))
 for yr,z in pred.groupby(pred.index.year):year.append(dict(fuente=s,ano=yr,**metrics(z.Q,z[col])))
 for mm,z in pred.groupby(pred.index.month):month.append(dict(fuente=s,mes_calendario=mm,**metrics(z.Q,z[col])))
 for label,mask in [('Q alto (umbral de ajuste)',pred.Q>=threshold),('Q bajo-medio',pred.Q<threshold)]:
  z=pred[mask];strata.append(dict(fuente=s,condicion=label,umbral_Q=threshold,**metrics(z.Q,z[col])))
summary=pd.DataFrame(summary);annual=pd.DataFrame(year);monthly=pd.DataFrame(month);conditions=pd.DataFrame(strata)
cal=pred[['Q','IMERG_estimado','CHIRPS_estimado']].reindex(pd.date_range('2017-01-01','2022-12-01',freq='MS'))
err=cal[['IMERG_estimado','CHIRPS_estimado']].subtract(cal.Q,axis=0)
residual=[]
for s in ['IMERG','CHIRPS']:
 e=err[s+'_estimado'];residual.append(dict(fuente=s,corr_error_lag1=float(e.corr(e.shift(1))),fraccion_subestimada=float(np.mean(pred[s+'_estimado']<pred.Q))))
bootstrap=[]
for length in [6,12]:
 rng=np.random.default_rng(20261006+length);samples=[]
 for _ in range(3000):
  starts=rng.integers(0,len(cal)-length+1,size=int(np.ceil(len(cal)/length)));idx=np.concatenate([np.arange(st,st+length) for st in starts])[:len(cal)];z=err.iloc[idx].dropna();samples.append(float(np.sqrt(np.mean(z.CHIRPS_estimado**2))-np.sqrt(np.mean(z.IMERG_estimado**2))))
 bootstrap.append(dict(bloque_meses=length,repeticiones=3000,delta_RMSE_CHIRPS_menos_IMERG=float(summary.loc[summary.fuente=='CHIRPS','RMSE'].iloc[0]-summary.loc[summary.fuente=='IMERG','RMSE'].iloc[0]),p025=float(np.quantile(samples,.025)),p975=float(np.quantile(samples,.975))))
excluded=data.loc['2017':'2022'].index.difference(test.index).strftime('%Y-%m').tolist()
local_stats=pd.DataFrame(model['local_resultados']);rawlocal=[]
lp=DOC.parent/'datos_fuente/lluvia_local_Zaragoza_mensual_2018_2022.csv';l=pd.read_csv(lp,parse_dates=['mes']).set_index('mes');local=data.join(l.lluvia_local_mm.where(l.n_intervalos==l.esperados).rename('local')).loc['2019'].dropna(subset=['local','IMERG','CHIRPS'])
for s in ['IMERG','CHIRPS']:
 row=local_stats[(local_stats.fuente==s)&(local_stats.modelo=='lineal')].iloc[0]
 rawlocal.append(dict(fuente=s,caso='Sin corrección (diagnóstico previo)',**metrics(local.local,local[s])))
 rawlocal.append(dict(fuente=s,caso='Recta 2018→2019 (diagnóstico previo)',n=7,RMSE=row.temporal_RMSE,MAE=row.temporal_MAE,sesgo=row.temporal_sesgo,NSE=row.temporal_R2,PBIAS=float(100*row.temporal_sesgo/local.local.mean())))
for name,df in [('metricas_reserva',summary),('metricas_por_ano',annual),('metricas_por_mes',monthly),('metricas_por_condicion',conditions),('diagnostico_residuos',pd.DataFrame(residual)),('remuestreo_pareado',pd.DataFrame(bootstrap)),('diagnostico_local_previo',pd.DataFrame(rawlocal))]:df.to_csv(OUT/(name+'.csv'),index=False)
pred.to_csv(OUT/'estimaciones_reserva.csv',index_label='mes');err.to_csv(OUT/'errores_calendario.csv',index_label='mes')
result=dict(periodo=['2017-01','2022-12'],n=68,meses_excluidos=excluded,parametros_reajustados=False,huella_parametros_2_2=hashlib.sha256(frozen).hexdigest(),coeficientes={s:model['Q_modelos'][s]['modelo_coef']['coef'] for s in ['IMERG','CHIRPS']},metricas=summary.to_dict('records'),umbral_Q_alto_ajuste=threshold,fisica=phys,residuos=residual,bootstrap=bootstrap,local_evaluacion_independiente=False)
(OUT/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
# Calendar gaps remain gaps in every time-series plot.
colors={'IMERG':'#d77627','CHIRPS':'#22799a','Climatologia':'#7b6ba8'}
fig,axes=plt.subplots(2,1,figsize=(12,6.5),sharex=True,layout='constrained')
axes[0].plot(cal.index,cal.Q,'k-',lw=1.3,label='Q observado')
for s in ['IMERG','CHIRPS']:
 axes[0].plot(cal.index,cal[s+'_estimado'],color=colors[s],lw=1,label=s)
 axes[1].plot(err.index,err[s+'_estimado'],color=colors[s],lw=1,marker='.',ms=3,label=s)
axes[0].set(ylabel='Caudal (m³/s)',title='Prueba reservada 2017–2022 · parámetros congelados');axes[1].set(ylabel='Estimado − observado (m³/s)',xlabel='Fecha');axes[1].axhline(0,c='grey',lw=.7)
for ax in axes:ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=9)
for ext in ['png','pdf']:fig.savefig(OUT/('reserva_series.'+ext),dpi=180)
plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for i,s in enumerate(['IMERG','CHIRPS']):
 p=pred[s+'_estimado'];e=p-pred.Q;axes[0,i].scatter(pred.Q,p,c=pred.index.month,cmap='twilight',vmin=.5,vmax=12.5,s=28);hi=max(pred.Q.max(),p.max())*1.07;axes[0,i].plot([0,hi],[0,hi],'k--',lw=1);axes[0,i].set(xlim=(0,hi),ylim=(0,hi),xlabel='Q observado (m³/s)',ylabel='Q estimado (m³/s)',title=s+' · observado frente a estimado');axes[1,i].scatter(p,e,c=pred.index.month,cmap='twilight',vmin=.5,vmax=12.5,s=28);axes[1,i].axhline(0,c='red',lw=.8);axes[1,i].set(xlabel='Q estimado (m³/s)',ylabel='Error (m³/s)',title=s+' · residuos frente a estimación')
for ax in axes.flat:ax.grid(alpha=.2)
for ext in ['png','pdf']:fig.savefig(OUT/('reserva_dispersion_residuos.'+ext),dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for s in ['IMERG','CHIRPS','Climatologia']:
 z=monthly[monthly.fuente==s];axes[0].plot(z.mes_calendario,z.sesgo,marker='o',color=colors[s],label=s);axes[1].plot(z.mes_calendario,z.RMSE,marker='o',color=colors[s],label=s)
axes[0].axhline(0,c='grey',lw=.7);axes[0].set(ylabel='Sesgo (m³/s)',title='Estacionalidad del error');axes[1].set(ylabel='RMSE (m³/s)',title='Error por mes calendario')
for ax in axes:ax.set(xlabel='Mes calendario',xticks=range(1,13));ax.grid(alpha=.2);ax.legend(fontsize=8)
for ext in ['png','pdf']:fig.savefig(OUT/('reserva_meses.'+ext),dpi=180)
plt.close(fig)
baseline=float(summary.loc[summary.fuente=='Climatologia','RMSE'].iloc[0]);irow=summary[summary.fuente=='IMERG'].iloc[0];crow=summary[summary.fuente=='CHIRPS'].iloc[0]
high=conditions[(conditions.condicion.str.startswith('Q alto'))&conditions.fuente.isin(['IMERG','CHIRPS'])]
best_high=high.sort_values('RMSE').iloc[0]
texts=[
('Partición temporal y prueba sin reajuste','Se mantienen las decisiones del 2.2: modelos de caudal con lluvia del mismo mes y del mes anterior, ajustados con 206 meses válidos hasta diciembre de 2016. Aquí se abren únicamente los 68 meses comunes de enero de 2017 a diciembre de 2022. No se vuelven a elegir modelos, rezagos, transformaciones ni parámetros a partir de esta prueba. Los años completos definen la partición cronológica, pero se excluyen pares inválidos: junio y julio de 2021 y marzo y abril de 2022. Junio de 2021 y marzo de 2022 carecen de datos mensuales completos; los meses siguientes pierden la lluvia antecedente CHIRPS. No hay mezcla aleatoria de ajuste y prueba ni relleno de huecos. Se usa precipitación original, no anomalías, por lo que no se calcula una nueva climatología de predictores con la reserva.'),
('Ecuaciones congeladas y referencia','Se aplican exactamente las ecuaciones de caudal del 2.2, con salida max(0, expresión): IMERG, −87,269198 + 0,465439 P(t) + 0,433065 P(t−1); CHIRPS, −35,852625 + 0,422155 P(t) + 0,434939 P(t−1). Q está en m³/s y P en mm/mes. La referencia principal es la climatología mensual de Q estimada exclusivamente con los 206 meses de ajuste; también se muestra la media constante de ese ajuste. Se conserva una huella SHA-256 del archivo de parámetros para verificar que no cambió. Como P(t) se conoce al terminar el mes, esta prueba evalúa estimación mensual retrospectiva, no un pronóstico disponible antes de observar la lluvia del mes.'),
('Resultados fuera del ajuste',f'En los mismos 68 meses, CHIRPS obtiene RMSE {fmt(crow.RMSE)} m³/s, MAE {fmt(crow.MAE)}, sesgo {fmt(crow.sesgo)} y NSE {fmt(crow.NSE)}; IMERG obtiene RMSE {fmt(irow.RMSE)}, MAE {fmt(irow.MAE)}, sesgo {fmt(irow.sesgo)} y NSE {fmt(irow.NSE)}. El sesgo se define como estimado−observado: negativo indica subestimación. NSE=1−SSE/SST compara el error con la media del periodo evaluado; no sustituye la comparación explícita con la climatología entrenada. Esta última tiene RMSE {fmt(baseline)}. La reducción de RMSE frente a ella es {fmt(100*(baseline-irow.RMSE)/baseline)} % para IMERG y {fmt(100*(baseline-crow.RMSE)/baseline)} % para CHIRPS.'),
('Estabilidad entre periodos y diferencia entre productos',f'El orden de desempeño se invierte respecto del desarrollo: IMERG tenía RMSE 56,43 frente a 63,87 de CHIRPS; en la reserva CHIRPS es ligeramente mejor. La diferencia RMSE_CHIRPS−RMSE_IMERG es {fmt(crow.RMSE-irow.RMSE)} m³/s, pequeña frente al tamaño de los errores. La tabla anual permite examinar años favorables y desfavorables sin reajustar por año. Se calcula, además, un intervalo descriptivo de la diferencia mediante 3000 remuestreos pareados de bloques calendario de seis meses, manteniendo juntas las dos fuentes y preservando los huecos. Se repite con doce meses como sensibilidad; no se remuestrean meses aislados como si fueran independientes. Son intervalos aproximados con solo seis años, no una prueba de superioridad universal.'),
('Residuos frente al tiempo, al estimado y al mes calendario','Se presentan errores estimado−observado frente al tiempo y al valor estimado, además del sesgo y RMSE por mes calendario. Las curvas temporales conservan los huecos. La tabla mensual tiene solo cuatro a seis observaciones por mes: las diferencias orientan la revisión, pero no justifican correcciones estacionales nuevas ajustadas con esta prueba. Se examina la correlación del error con el mes anterior usando el calendario completo, sin unir artificialmente meses separados por faltantes. Persistencia, dispersión cambiante y errores concentrados en ciertos meses limitan los modelos y evitan tratar una correlación global como garantía predictiva.'),
('Caudales altos, plausibilidad física y extrapolación',f'Para definir caudal alto se usa el percentil 75 del ajuste, {fmt(threshold)} m³/s, sin elegir el umbral con la prueba. Se reportan por separado n, sesgo, MAE y RMSE de esa condición y del resto. En el grupo alto, el menor RMSE corresponde a {best_high.fuente} ({fmt(best_high.RMSE)} m³/s), lo que debe leerse junto con los sesgos y la muestra. Se cuentan salidas negativas antes de aplicar el truncamiento a cero y entradas P(t) o P(t−1) fuera de los rangos del ajuste. El truncamiento asegura no negatividad, pero no conserva masa ni valida magnitudes extremas. No se aplica recorte superior, interpolación ni corrección posterior del sesgo. Cambios de almacenamiento, evapotranspiración, extracción y operación quedan fuera de estas regresiones.'),
('Lluvia local: no existe una reserva independiente adicional','Los catorce meses completos de Zaragoza ya se utilizaron en el desarrollo y en el reajuste local del 2.2; no hay meses locales adicionales para evaluar honestamente esas ecuaciones congeladas. Por eso no se reutilizan como una nueva prueba final. Se conserva, solo como diagnóstico previo ya examinado en 2.2, el corte de siete meses de 2018 para ajustar y siete de 2019 para comprobar. En esa tabla se añade la referencia solicitada: precipitación del producto sin corrección para estimar lluvia local; IMERG es la referencia de la guía y CHIRPS su comparación paralela. Ese diagnóstico también participó en las decisiones del desarrollo y no equivale a una validación final independiente. Para cerrar esa parte se necesitan registros locales nuevos o previamente separados, que no se usen para calibrar ni elegir el modelo.'),
('Fuentes compartidas y alcance de la independencia','La separación temporal evita usar el caudal de prueba para ajustar la regresión, pero no garantiza independencia entre productos de precipitación y estaciones. IMERG Final combina información satelital con análisis de pluviómetros; CHIRPS combina información satelital y estaciones. No se ha verificado si Zaragoza integra las redes de ajuste de estos productos. Tampoco se presenta Q como un balance de agua cerrado ni como una medida causal de la lluvia. Fuentes metodológicas: NASA, IMERG (https://gpm.nasa.gov/data/imerg); Climate Hazards Center, CHIRPS (https://chc.ucsb.edu/data/chirps).'),
('Conclusión del 2.3','Existe una relación aprovechable para estimar caudal mensual a partir de lluvia contemporánea y antecedente: ambas fuentes mejoran la climatología en la prueba reservada. CHIRPS tiene el menor RMSE y MAE globales y un sesgo más cercano a cero en 2017–2022; la ventaja es pequeña y debe contrastarse con años, meses y condiciones de caudal, sin declarar un ganador general. Los modelos siguen siendo herramientas estadísticas retrospectivas de la misma cuenca, con limitaciones en extremos, estabilidad y causalidad. No se recomienda usarlos como pronósticos de crecidas ni extrapolarlos a otras cuencas. Para lluvia local, la utilidad continúa siendo exploratoria: no hay una prueba independiente adicional disponible.')]
texts[3]=(texts[3][0],texts[3][1]+f' El intervalo central del 95 % con bloques de seis meses va de {fmt(bootstrap[0]["p025"])} a {fmt(bootstrap[0]["p975"])} m³/s y con doce meses de {fmt(bootstrap[1]["p025"])} a {fmt(bootstrap[1]["p975"])}; ambos incluyen cero. No hay evidencia sólida aquí de superioridad general de una fuente. CHIRPS tiene menor RMSE en 2017, 2018, 2020 y 2022; IMERG en 2019 y 2021. En 2020 el NSE es negativo para ambos (−0,59 y −0,17), lo que advierte estabilidad limitada respecto de la variabilidad de ese año, sin sustituir la referencia climatológica entrenada.')
texts[4]=(texts[4][0],texts[4][1].replace('cuatro a seis','cinco a seis')+' IMERG subestima en enero, noviembre y diciembre (sesgos −46,14, −50,99 y −38,57 m³/s); CHIRPS muestra sobreestimación marcada en octubre (+33,65) y subestimación en marzo (−23,16). Estos patrones no se corrigen después de mirar la reserva. La correlación del error con el mes anterior es 0,21 para IMERG y 0,18 para CHIRPS: la persistencia se reduce frente al desarrollo, pero no desaparece.')
texts[5]=(texts[5][0],texts[5][1]+' Los dos modelos subestiman caudales altos: sesgo −48,16 m³/s para IMERG y −25,85 para CHIRPS, con 21 meses en el grupo. En los 47 meses bajos-medios, IMERG tiene menor RMSE (31,83 frente a 35,54). No hubo salidas brutas negativas en la reserva. CHIRPS presenta dos meses con predictores fuera del rango de ajuste, octubre y noviembre de 2022; IMERG ninguno. No se descartan esos meses para favorecer un resultado.')
texts[7]=(texts[7][0],texts[7][1]+' El periodo reservado no se usó para ajustar ni seleccionar los modelos del 2.2, aunque sus series ya aparecieron en la exploración de 1.1 y 2.1. Se trata de una evaluación temporal fuera del ajuste, no de un experimento completamente ciego. Una comprobación prospectiva con años nuevos reforzaría la evidencia.')
def table_html(df):return df.to_html(index=False,float_format=lambda v:fmt(v),border=0,classes='tabla-estadistica')
def img(name,cap):return '<img style="width:100%;height:auto" alt="'+cap+'" src="data:image/png;base64,'+base64.b64encode((OUT/(name+'.png')).read_bytes()).decode()+'"><p>'+cap+'</p>'
content='<section class="panel" id="evaluacion-23"><h2>2.3. Evaluación fuera del periodo de ajuste: IMERG y CHIRPS</h2>'
for j,(title,text) in enumerate(texts):
 content+='<h3>'+title+'</h3><p>'+text+'</p>'
 if j==2:content+=table_html(summary)+img('reserva_series','Series y errores en la reserva 2017–2022.')
 if j==3:content+=table_html(annual[['fuente','ano','n','RMSE','MAE','sesgo']])+table_html(pd.DataFrame(bootstrap))
 if j==4:content+=img('reserva_dispersion_residuos','Observado, estimado y residuos; color por mes calendario.')+img('reserva_meses','Sesgo y RMSE por mes calendario.')+table_html(monthly[monthly.fuente.isin(['IMERG','CHIRPS'])][['fuente','mes_calendario','n','RMSE','MAE','sesgo']])+table_html(pd.DataFrame(residual))
 if j==5:content+=table_html(conditions[['fuente','condicion','n','RMSE','MAE','sesgo']])+table_html(pd.DataFrame(phys))
 if j==6:content+=table_html(pd.DataFrame(rawlocal))
seriesid='reserva23-series-Q'
content+='<h3>Caudal observado, modelos y referencia — serie interactiva</h3><div id="'+seriesid+'" style="height:450px;width:100%"></div>'
series=[]
for name,column,color in [('Observado','Q','black'),('IMERG','IMERG_estimado',colors['IMERG']),('CHIRPS','CHIRPS_estimado',colors['CHIRPS']),('Climatologia','Climatologia',colors['Climatologia'])]:
 values=pred[column].reindex(cal.index)
 series.append(dict(type='scatter',mode='lines+markers',name=name,x=cal.index.strftime('%Y-%m-%d').tolist(),y=[None if pd.isna(v) else float(v) for v in values],connectgaps=False,line=dict(color=color,width=1.5),marker=dict(size=4),hovertemplate='%{x|%Y-%m}<br>Q=%{y:.2f} m³/s<extra>%{fullData.name}</extra>'))
plotsets=[dict(id=seriesid,data=series,layout=dict(title='Prueba reservada 2017–2022',xaxis=dict(title='Fecha',rangeslider=dict(visible=True)),yaxis=dict(title='Caudal (m³/s)'),legend=dict(orientation='h'),margin=dict(l=75,r=30,t=50,b=60)))]
for s in ['IMERG','CHIRPS']:
 for mode in ['tiempo','estimado','mes']:
  ident='reserva23-'+s+'-'+mode;content+='<h3>'+s+' · residuos frente a '+mode+' — consulta interactiva</h3><div id="'+ident+'" style="height:420px;width:100%"></div>'
  x=cal.index.strftime('%Y-%m-%d').tolist() if mode=='tiempo' else pred[s+'_estimado'].tolist() if mode=='estimado' else pred.index.month.tolist()
  y=[None if pd.isna(v) else float(v) for v in err[s+'_estimado']] if mode=='tiempo' else (pred[s+'_estimado']-pred.Q).tolist()
  dates=cal.index.strftime('%Y-%m').tolist() if mode=='tiempo' else pred.index.strftime('%Y-%m').tolist()
  trace=dict(type='scatter',mode='lines+markers' if mode=='tiempo' else 'markers',x=x,y=y,text=dates,connectgaps=False,marker=dict(size=7,color=colors[s]),hovertemplate='%{text}<br>Error=%{y:.2f} m³/s<extra></extra>')
  plotsets.append(dict(id=ident,data=[trace],layout=dict(title=s+' · reserva 2017–2022',xaxis=dict(title='Fecha' if mode=='tiempo' else 'Q estimado (m³/s)' if mode=='estimado' else 'Mes calendario'),yaxis=dict(title='Error: estimado−observado (m³/s)'),shapes=[dict(type='line',xref='paper',x0=0,x1=1,y0=0,y1=0,line=dict(color='red',width=1))],margin=dict(l=75,r=30,t=50,b=60))))
content+='<script>window.addEventListener("load",function(){const plots='+json.dumps(plotsets,ensure_ascii=False)+';plots.forEach(function(p){if(window.Plotly&&document.getElementById(p.id)){Plotly.newPlot(p.id,p.data,p.layout,{responsive:true,displaylogo:false,toImageButtonOptions:{format:"svg"}});}});});</script></section>'
hp=DOC/'informe_interactivo.html';ht=hp.read_text(encoding='utf-8');ht=re.sub(r'<!-- EVALUACION_23_INICIO -->.*?<!-- EVALUACION_23_FIN -->','',ht,flags=re.S)
marker='<!-- DISPERSION_REQUERIDA_INICIO -->';assert marker in ht;ht=ht.replace(marker,'<!-- EVALUACION_23_INICIO -->'+content+'<!-- EVALUACION_23_FIN -->'+marker,1)
old="pendiente(sub(p2,'guia-2-3','2.3. Evaluar fuera del periodo de ajuste'));";new="const s23=sub(p2,'guia-2-3','2.3. Evaluar fuera del periodo de ajuste');mover(s23,document.getElementById('evaluacion-23'));";assert old in ht or new in ht;ht=ht.replace(old,new)
def esc(s):
 for x,y in [('−','-'),('–','--'),('→',r'$\rightarrow$'),('³',r'$^3$'),('%',r'\%'),('_',r'\_'),('²',r'$^2$')]:s=s.replace(x,y)
 return s
def tt(df,cols,heads):
 s=r'\begin{center}\small\begin{tabular}{'+'l'+'r'*(len(cols)-1)+r'}\hline'+'\n'+' & '.join(heads)+r' \\ \hline'+'\n'
 for _,row in df.iterrows():s+=' & '.join(esc(str(row[c])) if isinstance(row[c],str) else str(int(row[c])) if c in ['n','ano','mes_calendario','bloque_meses','negativos_truncados','meses_fuera_rango_P'] else fmt(row[c]) for c in cols)+r' \\'+'\n'
 return s+r'\hline\end{tabular}\end{center}'+'\n'
def ft(name,cap):return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_2_3/'+name+r'.pdf}\caption{'+esc(cap)+r'}\end{figure}'+'\n'
tex=r'\subsection{Evaluar fuera del periodo de ajuste}'+'\n'
for j,(title,text) in enumerate(texts):
 if j==7:
  text=text.replace('https://gpm.nasa.gov/data/imerg','NASA_LINK').replace('https://chc.ucsb.edu/data/chirps','CHIRPS_LINK');paragraph=esc(text).replace(r'NASA\_LINK',r'\url{https://gpm.nasa.gov/data/imerg}').replace(r'CHIRPS\_LINK',r'\url{https://chc.ucsb.edu/data/chirps}')
 else:paragraph=esc(text)
 tex+=r'\subsubsection*{'+esc(title)+'}\n'+paragraph+'\n'
 if j==2:tex+=tt(summary,['fuente','n','RMSE','MAE','sesgo','NSE'],['Fuente','n','RMSE','MAE','Sesgo','NSE'])+ft('reserva_series','Series y errores de los modelos congelados, 2017--2022.')
 if j==3:
  tex+=tt(annual[annual.fuente.isin(['IMERG','CHIRPS','Climatologia'])],['fuente','ano','n','RMSE','MAE','sesgo'],['Fuente','Año','n','RMSE','MAE','Sesgo'])+tt(pd.DataFrame(bootstrap),['bloque_meses','delta_RMSE_CHIRPS_menos_IMERG','p025','p975'],['Bloque (meses)','Diferencia RMSE','Percentil 2,5','Percentil 97,5'])
 if j==4:
  tex+=ft('reserva_dispersion_residuos','Predicciones y residuos frente al valor estimado.')+ft('reserva_meses','Estacionalidad residual y RMSE mensual en la reserva.')
  tex+=tt(monthly[monthly.fuente.isin(['IMERG','CHIRPS'])],['fuente','mes_calendario','n','RMSE','MAE','sesgo'],['Fuente','Mes','n','RMSE','MAE','Sesgo'])+tt(pd.DataFrame(residual),['fuente','corr_error_lag1','fraccion_subestimada'],['Fuente','r error antecedente','Fracción subestimada'])
 if j==5:
  for condition in ['Q alto (umbral de ajuste)','Q bajo-medio']:
   tex+=r'\textbf{'+esc(condition)+r'.}'+tt(conditions[conditions.condicion==condition],['fuente','n','RMSE','MAE','sesgo'],['Fuente','n','RMSE','MAE','Sesgo'])
  tex+=tt(pd.DataFrame(phys),['fuente','raw_min','raw_max','negativos_truncados','meses_fuera_rango_P'],['Fuente','Mín. bruto','Máx. bruto','Negativos','Fuera rango P'])
 if j==6:
  localtable=pd.DataFrame(rawlocal).copy();localtable['caso']=localtable.caso.map(lambda s:'Sin corrección' if s.startswith('Sin') else 'Recta: diagnóstico previo');tex+=tt(localtable,['fuente','caso','n','RMSE','MAE','sesgo'],['Fuente','Caso previo','n','RMSE','MAE','Sesgo'])
tp=DOC/'latex/informe_ordenado.tex';t=tp.read_text(encoding='utf-8');start=t.index(r'\subsection{Evaluar fuera del periodo de ajuste}');end=t.index(r'\clearpage',start);t=t[:start]+tex+t[end:]
assert parameters.read_bytes()==frozen,'Los parámetros del 2.2 cambiaron'
hp.write_text(ht,encoding='utf-8');tp.write_text(t,encoding='utf-8');(OUT/'apartado_2_3.tex').write_text(tex,encoding='utf-8')
print(json.dumps(dict(metricas=summary.to_dict('records'),bootstrap=bootstrap,fisica=phys,alto=high.to_dict('records')),ensure_ascii=False,indent=2))

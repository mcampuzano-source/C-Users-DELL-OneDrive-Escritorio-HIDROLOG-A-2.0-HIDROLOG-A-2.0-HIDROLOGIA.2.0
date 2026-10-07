from pathlib import Path
import runpy,contextlib,io,json,re,base64,html
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):g=runpy.run_path(str(ROOT/'modelos_22.py'))
DOC=g['DOC'];OUT=g['OUT'];res=g['result'];cv=g['cv'];sel=g['selected'];d=g['d'];local=g['local'];dev=g['dev']
pred=pd.DataFrame(g['preds']);ls=pd.DataFrame(g['local_stats']);ql=pd.DataFrame(g['qlocal']);fold=pd.DataFrame(g['folds'])
names={'media':'Media constante','climatologia':'Climatología mensual','lineal':'Lineal P(t)','rezago1':'Lineal P(t−1)','lineal_rezago':'P(t) + P(t−1)','raiz':'Raíz de P(t)'}
def f(v,n=2):return f'{v:.{n}f}'.replace('.',',')
chosen=[];diagnostics=[]
for src in ['IMERG','CHIRPS']:
 kind=sel[src]['modelo'];z=pred.query('fuente==@src and modelo==@kind');er=z.estimado-z.observado
 chosen.append(dict(fuente=src,modelo=names[kind],n=len(z),**g['metric'](z.observado.to_numpy(),z.estimado.to_numpy())))
 consecutive=z.copy();consecutive['date']=pd.to_datetime(consecutive.mes);consecutive=consecutive.set_index('date').asfreq('MS');consecutive['e']=consecutive.estimado-consecutive.observado
 diagnostics.append(dict(fuente=src,corr_residuo_mes_anterior=consecutive.e.corr(consecutive.e.shift(1)),RMSE_Q_alto=np.sqrt(np.mean((er[z.observado>=z.observado.quantile(.75)])**2)),sesgo_Q_alto=er[z.observado>=z.observado.quantile(.75)].mean(),negativos_truncados=int(fold.query('fuente==@src and modelo==@kind').negativos_truncados.sum())))
pd.DataFrame(diagnostics).to_csv(OUT/'diagnostico_residuos.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,src in zip(axes,['IMERG','CHIRPS']):
 z=pred.query('fuente==@src and modelo==@sel[@src]["modelo"]') if False else pred[(pred.fuente==src)&(pred.modelo==sel[src]['modelo'])]
 ax.scatter(z.observado,z.estimado,s=22,alpha=.65,c=pd.to_datetime(z.mes).dt.month,cmap='twilight',vmin=.5,vmax=12.5)
 hi=max(z.observado.max(),z.estimado.max())*1.05;ax.plot([0,hi],[0,hi],'k--',lw=1);ax.set(xlim=(0,hi),ylim=(0,hi),xlabel='Q observado (m³/s)',ylabel='Q estimado (m³/s)',title=src+' · validación de desarrollo');ax.grid(alpha=.2)
 rm=next(row['RMSE'] for row in chosen if row['fuente']==src);ax.text(.04,.96,f'n={len(z)}; RMSE={rm:.2f} m³/s',transform=ax.transAxes,va='top',fontsize=9)
for ext in ['png','pdf']:fig.savefig(OUT/('modelos_Q_comparados.'+ext),dpi=190)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,src in zip(axes,['IMERG','CHIRPS']):
 z=pred[(pred.fuente==src)&(pred.modelo==sel[src]['modelo'])];ax.scatter(z.estimado,z.estimado-z.observado,s=22,alpha=.65);ax.axhline(0,c='red',lw=1);ax.set(xlabel='Q estimado (m³/s)',ylabel='Error: estimado − observado (m³/s)',title=src+' · errores de desarrollo');ax.grid(alpha=.2)
for ext in ['png','pdf']:fig.savefig(OUT/('residuos_Q.'+ext),dpi=190)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,src in zip(axes,['IMERG','CHIRPS']):
 z=local;model=g['local_fits'][src+'_lineal'];xx=np.linspace(z[src].min(),z[src].max(),100);yy=np.maximum(0,model['coef'][0]+model['coef'][1]*xx);ax.scatter(z[src],z.local,c=z.index.month,cmap='twilight',vmin=.5,vmax=12.5);ax.plot(xx,yy,c='red',label='Recta ajustada (n=14)');ax.set(xlabel=src+' cuenca (mm/mes)',ylabel='Lluvia local Zaragoza (mm/mes)',title=src+' · calibración local exploratoria');ax.grid(alpha=.2);ax.legend(fontsize=8)
for ext in ['png','pdf']:fig.savefig(OUT/('modelos_lluvia_local.'+ext),dpi=190)
plt.close(fig)
equations=[]
for src in ['IMERG','CHIRPS']:
 a,b=g['local_fits'][src+'_lineal']['coef'];equations.append(('Lluvia local · '+src,f'L_est(t) = max(0, {f(a,4)} + {f(b,6)} P_{src}(t)) [mm/mes]'))
 a,b,c=sel[src]['modelo_coef']['coef'];equations.append(('Caudal · '+src,f'Q_est(t) = max(0, {f(a,4)} + {f(b,6)} P_{src}(t) + {f(c,6)} P_{src}(t−1)) [m³/s]'))
ba,bb=g['qlocal_coefs']['lineal']['coef'];equations.append(('Caudal · lluvia local (solo exploratorio)',f'Q_est(t) = max(0, {f(ba,4)} + {f(bb,6)} L(t)) [m³/s]'))
texts=[
('Objetivos, variables y muestras comunes','Se evalúa (i) estimar lluvia mensual local de Zaragoza-AUT a partir de IMERG o CHIRPS y (ii) estimar el caudal medio mensual Q a partir de cada producto de precipitación; se añade la relación local–Q como ejercicio exploratorio. P(t) es precipitación de cuenca en mm/mes, L(t) lluvia local en mm/mes y Q(t) caudal en m³/s. IMERG es el promedio del polígono exacto. Las dos fuentes usan las mismas fechas para cada comparación. Para modelos con rezago se exige Q, P_IMERG(t), P_CHIRPS(t) y ambas lluvias en t−1 válidas: quedan 274 meses de 1998–2022, once menos que los 285 pares contemporáneos de 2.1. No se rellenan faltantes. Hay 206 meses para desarrollo hasta diciembre de 2016 y 68 meses de 2017–2022 reservados para el 2.3, sin evaluar sus resultados.'),
('Relaciones candidatas y criterio de selección','La nube positiva de 2.1 justifica probar una recta como referencia, sin suponer que determine una respuesta única. Se comparan media constante, climatología mensual, Q=a+bP(t), Q=a+bP(t−1), Q=a+bP(t)+cP(t−1) y Q=a+b√P(t). La raíz cuadrada es una alternativa no lineal sencilla para una posible respuesta sublineal y no transforma el caudal. Se ajusta por mínimos cuadrados con intercepto, sin forzar paso por el origen. La selección usa RMSE agregado de tres validaciones temporales dentro del desarrollo: ajuste hasta 2006→2007–2009, hasta 2009→2010–2012 y hasta 2012→2013–2016 (29, 30 y 46 meses, total 105). Cada coeficiente, media y climatología se estima solo con el pasado de su bloque. Se prefieren dos parámetros si el tercero mejora menos del 5 %; se considera candidato útil si reduce al menos 5 % el RMSE frente al mejor referente sin lluvia. Este umbral es una regla práctica explícita, no una prueba de significancia. La evaluación final independiente de 2017–2022 se realizará en 2.3.'),
('Resultado para caudal: modelos con lluvia actual y antecedente','El modelo con P(t) y P(t−1) es el candidato seleccionado para ambas fuentes: mejora la recta contemporánea y los referentes de media y climatología. IMERG obtiene RMSE 56,43 m³/s, MAE 38,97 y R² 0,52 en los 105 meses de validación de desarrollo; CHIRPS obtiene RMSE 63,87, MAE 45,99 y R² 0,38. La climatología tiene RMSE 77,37; la reducción es 27,1 % para IMERG y 17,4 % para CHIRPS. La raíz de P no supera al modelo con rezago. Esta evidencia respalda utilidad preliminar, no certifica predicción operativa. Las ecuaciones siguientes corresponden al reajuste final con los 206 meses de desarrollo; las métricas anteriores proceden de coeficientes ajustados por separado en cada bloque.'),
('Lluvia local: calibración sencilla y evidencia limitada','Se conserva solo la cobertura 100 %: 14 meses completos. Para cada producto se comparan media, recta y raíz de P. La recta es la referencia elegida por parsimonia: la raíz no muestra una mejora convincente con tan pocos datos. En ajuste sobre los 14 meses, RMSE es 35,87 mm/mes para IMERG y 33,59 para CHIRPS. En un diagnóstico temporal muy corto (siete meses de 2018 para ajustar y siete de 2019 para comprobar), las rectas dan RMSE 41,85 para IMERG y 30,50 para CHIRPS; el referente constante da 58,03. Para IMERG, la raíz apenas mejora ese diagnóstico un 0,9 %, insuficiente para preferirla; para CHIRPS empeora. No se selecciona por correlación ni se presenta el ajuste como validación. Estas ecuaciones calibran un promedio de cuenca hacia una estación puntual; no reconstruyen automáticamente la lluvia verdadera de toda la cuenca ni autorizan extrapolar a otras estaciones. Las ecuaciones mostradas usan los 14 meses, mientras la comprobación temporal usó únicamente coeficientes de 2018.'),
('Caudal a partir de lluvia local: no recomendar todavía','La recta local–Q con 14 pares da RMSE de ajuste 51,13 m³/s. En el diagnóstico temporal de siete meses de 2019, RMSE es 54,31 y R² solo 0,03, con sesgo +39,05 m³/s; el referente constante tiene RMSE 71,01. La raíz empeora a RMSE 57,88 y R² negativo. Aunque la recta reduce error respecto de esa media, la explicación de la variabilidad es escasa, el sesgo es grande y el registro demasiado corto. Se documenta la ecuación exploratoria, pero no se recomienda un modelo operativo local–Q ni añadirle más parámetros o rezagos con esta muestra. No se compara directamente su RMSE de siete meses con los RMSE de 105 meses de IMERG/CHIRPS.'),
('Supuestos, rangos, ceros y transformaciones','El modelo supone una relación aproximadamente estable en el periodo y ámbito de calibración; cambios de medición, uso del suelo, extracciones, humedad antecedente y regulación pueden romperla. Mínimos cuadrados minimiza errores cuadrados y es sensible a extremos. No se supone independencia de meses para calcular p-valores ni intervalos; los residuos pueden ser autocorrelacionados y de varianza cambiante. P(t−1) significa estrictamente el mes anterior del calendario, sin saltar faltantes. Las precipitaciones y caudales cero, si estuvieran observados, serían válidos; en las muestras actuales no hay ceros. La raíz admite cero y evita añadir constantes arbitrarias. Los faltantes nunca se sustituyen por cero. Para evitar estimaciones físicas negativas se publica max(0, expresión), también aplicado durante la comparación; no se recorta el extremo superior. No se recomienda extrapolar fuera de los rangos observados. Las ecuaciones con P(t) estiman el caudal una vez conocida la lluvia del mismo mes: no son pronósticos adelantados.'),
('Interpretación de parámetros y conservación de masa','En lluvia local, el intercepto tiene unidades mm/mes y la pendiente es adimensional. En caudal, el intercepto está en m³/s y las pendientes en (m³/s)/(mm/mes); el coeficiente de √P tendría unidades (m³/s)/√(mm/mes). Una pendiente positiva indica asociación, no una fracción causal de lluvia convertida en caudal. El intercepto negativo y el truncamiento no representan un balance de agua. Q estimado puede convertirse a lámina mensual con R_est=86,4×días_del_mes×Q_est/2797,19, pero la regresión no conserva masa: faltan evapotranspiración, cambios de almacenamiento, aportes, extracciones y controles de operación. No se interpreta P(t−1) como un tiempo de viaje medido.'),
('Comparación y decisión del apartado 2.2','Para lluvia local, la recta CHIRPS tiene mejor desempeño en el diagnóstico disponible, pero la muestra de 14 meses exige tratarla como calibración exploratoria. Para caudal, IMERG con lluvia actual y antecedente tiene menor RMSE y MAE de desarrollo que CHIRPS. Sin embargo, su sesgo es −22,66 m³/s, frente a −2,81 de CHIRPS: menor error cuadrático no implica menor sesgo. Los gráficos de residuos permiten revisar magnitud y persistencia del error; no se prometen intervalos de predicción sin validación. Se proponen dos candidatos de caudal para pasar al 2.3, se mantienen calibraciones locales exploratorias y se descarta afirmar que la lluvia local corta sustenta un modelo operativo. Los 68 meses reservados quedan intactos para comprobar generalización, extremos y estabilidad.')]
param=[]
for src in ['IMERG','CHIRPS']:
 for kind in ['lineal','rezago1','lineal_rezago','raiz']:
  m=g['fits'][src+'_'+kind];co=m['coef'];param.append(dict(fuente=src,modelo=names[kind],a=co[0],b=co[1],c=co[2] if len(co)>2 else 0))
ranges=[]
for src in ['IMERG','CHIRPS']:
 s=sel[src];m=g['local_fits'][src+'_lineal'];ranges.append(dict(fuente=src,Pmin_Q=s['rango_P'][0],Pmax_Q=s['rango_P'][1],Pmin_local=m['rango_P'][0],Pmax_local=m['rango_P'][1]))
def th(df):return df.to_html(index=False,float_format=lambda x:f(x),border=0,classes='tabla-estadistica')
def img(name,caption):return '<img style="width:100%;height:auto" alt="'+caption+'" src="data:image/png;base64,'+base64.b64encode((OUT/(name+'.png')).read_bytes()).decode()+'"><p>'+caption+'</p>'
content='<section class="panel" id="modelos-22"><h2>2.2. ¿Se pueden construir modelos útiles? IMERG y CHIRPS</h2>'
for i,(title,text) in enumerate(texts):
 content+='<h3>'+title+'</h3><p>'+text+'</p>'
 if i==1:dd=cv.copy();dd['modelo']=dd.modelo.map(names);content+=th(dd[['fuente','modelo','n','RMSE','MAE','sesgo','R2']])
 if i==2:
  for title,eq in [row for row in equations if row[0].startswith('Caudal · ') and 'local' not in row[0]]:content+='<p><b>'+title+'</b></p><pre style="white-space:pre-wrap">'+eq+'</pre>'
  content+=img('modelos_Q_comparados','Estimaciones frente a observaciones: validación temporal de desarrollo, no reserva final.')+img('residuos_Q','Errores estimado−observado en los 105 meses de desarrollo.')
  content+='<h4>Parámetros de alternativas, reajustados en 206 meses</h4>'+th(pd.DataFrame(param))
 if i==3:
  for title,eq in equations[:2]:content+='<p><b>'+title+'</b></p><pre style="white-space:pre-wrap">'+eq+'</pre>'
  dd=ls.copy();dd['modelo']=dd.modelo.map(names);content+=th(dd[['fuente','modelo','ajuste_RMSE','temporal_RMSE','temporal_MAE','temporal_sesgo','temporal_R2']])+img('modelos_lluvia_local','Rectas exploratorias de lluvia local, ajustadas en 14 meses completos.')
 if i==4:content+='<pre style="white-space:pre-wrap">'+equations[-1][1]+'</pre>'+th(ql[['modelo','ajuste_RMSE','temporal_RMSE','temporal_sesgo','temporal_R2']])
 if i==5:content+='<p>Rangos de precipitación de aplicación, mm/mes:</p>'+th(pd.DataFrame(ranges))+'<p>Rango de Q en desarrollo: 21,34–508,77 m³/s. No usar estos extremos para garantizar capacidad de reproducir eventos extremos.</p>'
 if i==7:content+=th(pd.DataFrame(diagnostics))
plots=[]
for src in ['IMERG','CHIRPS']:
 z=pred[(pred.fuente==src)&(pred.modelo==sel[src]['modelo'])]
 for residual in [False,True]:
  ident='model22-'+src+('-error' if residual else '-Q');x=z.estimado.tolist() if residual else z.observado.tolist();y=(z.estimado-z.observado).tolist() if residual else z.estimado.tolist();label='Errores' if residual else 'Observado frente a estimado'
  content+='<h3>'+src+' · '+label+' — consulta por mes</h3><div id="'+ident+'" style="height:420px;width:100%"></div>'
  data=[dict(type='scatter',mode='markers',x=x,y=y,text=z.mes.tolist(),marker=dict(size=8,color=pd.to_datetime(z.mes).dt.month.tolist(),colorscale='Turbo',cmin=1,cmax=12,colorbar=dict(title='Mes')),hovertemplate='%{text}<br>x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>')]
  if residual:data.append(dict(x=[min(x),max(x)],y=[0,0],mode='lines',line=dict(color='red'),hoverinfo='skip'))
  else:hi=max(max(x),max(y))*1.05;data.append(dict(x=[0,hi],y=[0,hi],mode='lines',line=dict(color='black',dash='dash'),hoverinfo='skip'))
  plots.append(dict(id=ident,data=data,layout=dict(title=src+' · '+label,showlegend=False,xaxis=dict(title='Q estimado (m³/s)' if residual else 'Q observado (m³/s)'),yaxis=dict(title='Error estimado−observado (m³/s)' if residual else 'Q estimado (m³/s)'),margin=dict(l=70,r=60,b=65,t=55))))
content+='<script>window.addEventListener("load",function(){const plots='+json.dumps(plots,ensure_ascii=False)+';plots.forEach(function(p){if(window.Plotly&&document.getElementById(p.id)){Plotly.newPlot(p.id,p.data,p.layout,{responsive:true,displaylogo:false,toImageButtonOptions:{format:"svg"}});}});});</script></section>'
hp=ROOT/'informe_interactivo.html';ht=hp.read_text(encoding='utf-8');ht=re.sub(r'<!-- MODELOS_22_INICIO -->.*?<!-- MODELOS_22_FIN -->','',ht,flags=re.S);ht=ht.replace('<!-- DISPERSION_REQUERIDA_INICIO -->','<!-- MODELOS_22_INICIO -->'+content+'<!-- MODELOS_22_FIN --><!-- DISPERSION_REQUERIDA_INICIO -->',1)
old="pendiente(sub(p2,'guia-2-2','2.2. ¿Se pueden construir modelos útiles?'));";new="const s22=sub(p2,'guia-2-2','2.2. ¿Se pueden construir modelos útiles?');mover(s22,document.getElementById('modelos-22'));";assert old in ht or new in ht;ht=ht.replace(old,new);hp.write_text(ht,encoding='utf-8')
def esc(s):
 for x,y in [('−','-'),('–','--'),('²',r'$^2$'),('³',r'$^3$'),('√',r'$\sqrt{\vphantom{P}}$'),('→',r'$\rightarrow$'),('×',r'$\times$'),('%',r'\%'),('_',r'\_')]:s=s.replace(x,y)
 return s
def tt(df,cols,heads):
 s=r'\begin{center}\small\begin{tabular}{'+'l'*sum(df[c].dtype=='object' for c in cols)+'r'*sum(df[c].dtype!='object' for c in cols)+r'}\hline'+'\n'+' & '.join(heads)+r' \\ \hline'+'\n'
 for _,row in df.iterrows():s+=' & '.join(esc(str(row[c])) if isinstance(row[c],str) else (str(int(row[c])) if c=='n' else f(row[c])) for c in cols)+r' \\'+'\n'
 return s+r'\hline\end{tabular}\end{center}'+'\n'
def ft(name,cap):return r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_2_2/'+name+r'.pdf}\caption{'+esc(cap)+r'}\end{figure}'+'\n'
def eqtex(src,target):
 if target=='Q':a,b,c=sel[src]['modelo_coef']['coef'];expr=f'{a:.4f}+{b:.6f}P_{{{src},t}}+{c:.6f}P_{{{src},t-1}}'
 elif target=='L':a,b=g['local_fits'][src+'_lineal']['coef'];expr=f'{a:.4f}+{b:.6f}P_{{{src},t}}'
 else:a,b=g['qlocal_coefs']['lineal']['coef'];target='Q';expr=f'{a:.4f}+{b:.6f}L_t'
 return r'\['+r'\widehat{'+target+r'}_t=\max\left(0,'+expr+r'\right).\]'+'\n'
tex=r'\subsection{¿Se pueden construir modelos útiles?}'+'\n'
for i,(title,text) in enumerate(texts):
 tex+=r'\subsubsection*{'+esc(title)+'}\n'+esc(text)+'\n'
 if i==1:
  dd=cv.copy();dd['modelo']=dd.modelo.map(names);tex+=tt(dd,['fuente','modelo','n','RMSE','MAE','sesgo','R2'],['Fuente','Modelo','n','RMSE','MAE','Sesgo',r'$R^2$'])
 if i==2:
  for src in ['IMERG','CHIRPS']:tex+=eqtex(src,'Q')
  tex+=ft('modelos_Q_comparados','Modelos de caudal: validación temporal dentro del desarrollo.')+ft('residuos_Q','Errores de estimación de caudal durante la validación de desarrollo.')
  tex+=tt(pd.DataFrame(param),['fuente','modelo','a','b','c'],['Fuente','Modelo','a','b','c'])
 if i==3:
  for src in ['IMERG','CHIRPS']:tex+=eqtex(src,'L')
  dd=ls.copy();dd['modelo']=dd.modelo.map(names);tex+=tt(dd,['fuente','modelo','ajuste_RMSE','temporal_RMSE','temporal_MAE','temporal_R2'],['Fuente','Modelo','RMSE ajuste','RMSE temporal','MAE temporal',r'$R^2$ temporal'])+ft('modelos_lluvia_local','Calibraciones locales exploratorias, catorce meses de ajuste.')
 if i==4:tex+=eqtex('local','Q_local')+tt(ql,['modelo','ajuste_RMSE','temporal_RMSE','temporal_sesgo','temporal_R2'],['Modelo','RMSE ajuste','RMSE temporal','Sesgo temporal',r'$R^2$ temporal'])
 if i==5:tex+=tt(pd.DataFrame(ranges),['fuente','Pmin_Q','Pmax_Q','Pmin_local','Pmax_local'],['Fuente','P mín. Q','P máx. Q','P mín. local','P máx. local'])+'Rango de Q en desarrollo: 21,34--508,77 m$^3$/s.\n'
 if i==7:tex+=tt(pd.DataFrame(diagnostics),['fuente','corr_residuo_mes_anterior','RMSE_Q_alto','sesgo_Q_alto'],['Fuente','r error antecedente','RMSE Q alto','Sesgo Q alto'])
tp=DOC/'latex/informe_ordenado.tex';text=tp.read_text(encoding='utf-8');start=text.index(r'\subsection{¿Se pueden construir modelos útiles?}');end=text.index(r'\subsection{Evaluar fuera del periodo de ajuste}',start);text=text[:start]+tex+text[end:];tp.write_text(text,encoding='utf-8')
(OUT/'apartado_2_2.tex').write_text(tex,encoding='utf-8');(OUT/'ecuaciones_y_decisiones.json').write_text(json.dumps(dict(ecuaciones=equations,diagnosticos=diagnostics,seleccion=sel),ensure_ascii=False,indent=2),encoding='utf-8')
print('Integrados 2.1 comparativo y 2.2. Reserva no evaluada:',len(g['holdout']))

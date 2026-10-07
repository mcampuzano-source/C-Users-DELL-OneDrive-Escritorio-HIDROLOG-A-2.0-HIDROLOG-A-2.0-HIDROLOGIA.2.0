from pathlib import Path
import base64, json, re, hashlib, html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
DOC=ROOT/'proyecto/la_vieja/documentos'
OUT=DOC/'apartado_2_1'; OUT.mkdir(exist_ok=True)
d=pd.read_csv(DOC/'imerg_poligono/series_alineadas.csv',parse_dates=['mes']).set_index('mes').asfreq('MS').loc['1998':'2022']
local_path=next((ROOT/'proyecto').rglob('*Zaragoza_mensual*.csv'))
l=pd.read_csv(local_path,parse_dates=['mes']).set_index('mes')
d=d.rename(columns={'P_IMERG_poligono_mm':'I','Q_m3_s':'Q','R_mm':'R'})
d['L']=l.lluvia_local_mm.where(l.n_intervalos==l.esperados)
common=d[['I','Q','R']].dropna()
clim=common.groupby(common.index.month).mean()
clim['n']=common.groupby(common.index.month).size()
clim.to_csv(OUT/'climatologia_1998_2022.csv',index_label='mes_calendario')
a=d[['I','Q','R']].copy()
for col in a: a[col]=d[col]-d.index.month.map(clim[col])
def corr(z,x,y):
    return float(z[x].corr(z[y])),float(z[x].rank().corr(z[y].rank()))
pairs=[('I','L','IMERG–lluvia local'),('L','Q','Lluvia local–caudal'),('I','Q','IMERG–caudal'),('I','R','IMERG–escorrentía')]
summary=[];lags=[];influence=[]
for x,y,name in pairs:
    z=d[[x,y]].dropna();r,rho=corr(z,x,y)
    summary.append(dict(relacion=name,n=len(z),Pearson=r,Spearman=rho))
    loo=[]
    for date in z.index:
        rv=corr(z.drop(date),x,y)[0];loo.append((abs(rv-r),date,rv))
    delta,date,rv=max(loo)
    influence.append(dict(relacion=name,mes=date.strftime('%Y-%m'),r_sin_mes=rv,cambio=delta,r_min=min(t[2] for t in loo),r_max=max(t[2] for t in loo)))
    if y in ['Q','R']:
        for k in range(4):
            b=pd.concat([d[x].shift(k).rename('x'),d[y].rename('y')],axis=1).dropna()
            rr,rs=corr(b,'x','y');lags.append(dict(relacion=name,serie='original',rezago=k,n=len(b),Pearson=rr,Spearman=rs))
            if x=='I':
                b=pd.concat([a[x].shift(k).rename('x'),a[y].rename('y')],axis=1).dropna()
                rr,rs=corr(b,'x','y');lags.append(dict(relacion=name,serie='anomalia',rezago=k,n=len(b),Pearson=rr,Spearman=rs))
z=d[['I','L']].dropna();err=z.I-z.L
errors=dict(sesgo=float(err.mean()),MAE=float(err.abs().mean()),RMSE=float(np.sqrt((err**2).mean())))
pd.DataFrame(summary).to_csv(OUT/'correlaciones.csv',index=False)
pd.DataFrame(lags).to_csv(OUT/'rezagos.csv',index=False)
pd.DataFrame(influence).to_csv(OUT/'sensibilidad.csv',index=False)
d[['I','L','Q','R']].to_csv(OUT/'pares_calendario.csv')
a.to_csv(OUT/'anomalias.csv')
def figure(frame, specs, name, anomal=False):
    fig,axes=plt.subplots(1,len(specs),figsize=(12,4.2),layout='constrained')
    axes=np.atleast_1d(axes)
    for ax,(x,y,title,xlabel,ylabel) in zip(axes,specs):
        z=frame[[x,y]].dropna();r,rho=corr(z,x,y)
        sc=ax.scatter(z[x],z[y],c=z.index.month,cmap='twilight',vmin=.5,vmax=12.5,s=21,alpha=.85,edgecolors='none')
        coef=np.polyfit(z[x],z[y],1);xx=np.array([z[x].min(),z[x].max()]);ax.plot(xx,np.polyval(coef,xx),color='red',lw=1,label='Recta descriptiva')
        if x in ['I','C'] and y=='L':
            hi=max(z.max())*1.08;ax.set_xlim(0,hi);ax.set_ylim(0,hi);ax.set_aspect('equal');ax.plot([0,hi],[0,hi],'k--',lw=1,label='1:1');ax.legend(fontsize=8)
        if anomal:ax.axhline(0,c='grey',lw=.5);ax.axvline(0,c='grey',lw=.5)
        ax.set(xlabel=xlabel,ylabel=ylabel,title=title)
        ax.text(.03,.97,f'n={len(z)}\nr={r:.2f}; ρ={rho:.2f}',transform=ax.transAxes,va='top',fontsize=9,bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
        ax.grid(alpha=.2)
    cb=fig.colorbar(sc,ax=axes.tolist(),ticks=range(1,13),shrink=.7,pad=.02);cb.set_label('Mes calendario')
    for ext in ['png','pdf']:fig.savefig(OUT/(name+'.'+ext),dpi=190)
    plt.close(fig)
figure(d,[('I','L','IMERG frente a lluvia local','IMERG cuenca (mm/mes)','Zaragoza-AUT (mm/mes)'),('L','Q','Lluvia local frente a caudal','Zaragoza-AUT (mm/mes)','Caudal medio mensual (m³/s)'),('I','Q','IMERG frente a caudal','IMERG cuenca (mm/mes)','Caudal medio mensual (m³/s)')],'dispersiones_21')
figure(a,[('I','Q','Anomalías IMERG–caudal','Anomalía IMERG (mm/mes)','Anomalía Q (m³/s)'),('I','R','Anomalías IMERG–escorrentía','Anomalía IMERG (mm/mes)','Anomalía R (mm/mes)')],'anomalias_21',True)
figure(d,[('L','R','Lluvia local–escorrentía','Zaragoza-AUT (mm/mes)','Escorrentía R (mm/mes)'),('I','R','IMERG–escorrentía','IMERG cuenca (mm/mes)','Escorrentía R (mm/mes)')],'laminas_21')
def fmt(x):return f'{x:.2f}'.replace('.',',')
paragraphs=[
('Datos, ejes y control de completitud','Se usa IMERG Final V07B promediado por área sobre el polígono exacto de La Vieja, no el promedio histórico de caja. Eje horizontal: precipitación acumulada mensual (mm/mes); eje vertical: lluvia local (mm/mes), caudal medio mensual Q (m³/s) o escorrentía R (mm/mes), según el panel. Los colores identifican los doce meses calendario. IMERG–Q usa 285 meses completos entre enero de 1998 y diciembre de 2022. Zaragoza-AUT solo aporta 14 meses completos entre enero de 2018 y agosto de 2019. El archivo tiene 22 acumulados no vacíos, pero ocho son parciales: se excluyen porque sus intervalos registrados no alcanzan los esperados. No se rellenan ni prorratean datos. Estos conteos y la serie poligonal sustituyen las cifras históricas de este apartado.'),
('Dirección, forma, dispersión y agrupamientos','Las tres nubes muestran asociación positiva; IMERG–lluvia local es la más fuerte en la muestra pequeña, mientras lluvia local–Q e IMERG–Q son moderadas. La nube IMERG–Q es alargada y dispersa, sin una función única: una misma lluvia puede acompañarse de caudales diferentes. Los meses calendario se solapan; el color ayuda a detectar agrupamientos estacionales, pero no establece regímenes separados. No hay soporte para ajustar curvaturas con solo 14 puntos locales. Se observan puntos de Q alto fuera del núcleo de la nube; una mayor amplitud a magnitudes altas puede sugerir variabilidad dependiente de la magnitud, pero no constituye una prueba de heterocedasticidad.'),
('Sesgo, MAE y RMSE frente a la referencia local',f'La línea 1:1 usa límites y escalas iguales. Con lluvia local como referencia y error e = IMERG − local, el sesgo medio es +{fmt(errors["sesgo"])} mm/mes, MAE {fmt(errors["MAE"])} mm/mes y RMSE {fmt(errors["RMSE"])} mm/mes (n=14). El sesgo indica la diferencia media con signo; MAE mide la diferencia absoluta típica; RMSE da más peso a errores grandes. Todos los errores de esta muestra son positivos, por eso sesgo y MAE coinciden. IMERG es un promedio de cuenca y Zaragoza una medición puntual: la diferencia combina representatividad espacial, cobertura y errores de ambas fuentes; no es una validación contra la lluvia verdadera de toda la cuenca. Una correlación alta no garantiza concordancia con 1:1.'),
('Pearson, Spearman y valores influyentes','Pearson resume asociación lineal y es sensible a magnitudes extremas; Spearman correlaciona rangos y resume asociación monótona. Sus diferencias no prueban por sí solas no linealidad. Se comprueba influencia retirando un mes cada vez: la tabla de sensibilidad muestra el mes que más cambia Pearson y el intervalo obtenido. No se eliminan extremos del análisis. Noviembre y diciembre de 2010 destacan por caudales altos en IMERG–Q; diciembre de 2018 combina poca lluvia local y caudal alto, compatible con lluvia antecedente o aportes de otras zonas. Son hipótesis de interpretación que requieren datos adicionales, no causas demostradas.'),
('Rezagos mensuales y apoyo con láminas','Se define k≥0 como correlación entre P del mes t−k y Q del mes t; k=1 significa lluvia del mes anterior. Se preserva el calendario mensual antes de desplazar, para no saltar faltantes. Se exploran 0–3 meses por posible humedad antecedente y almacenamiento; no se invocan nieve ni regulación documentada para explicar esta cuenca. Nunca se usa lluvia futura para explicar caudal pasado. Las muestras cambian por disponibilidad: los máximos de correlación son descriptivos y no estiman automáticamente un tiempo físico de respuesta. La comparación en láminas usa R = 86,4 × días del mes × Q / 2797,19, en mm/mes. R deriva de Q y no aporta evidencia independiente; sus diferencias mensuales incluyen la duración del mes. Los diagramas P–R ayudan a comparar unidades, pero no cierran un balance hídrico sin evapotranspiración y almacenamiento.'),
('Anomalías y persistencia al retirar el ciclo anual','Se define X′(t)=X(t)−promedio de X para el mes calendario de t. Para I, Q y R se calcula una climatología común de enero de 1998–diciembre de 2022 usando exclusivamente los 285 meses simultáneos completos; el archivo de climatología conserva el conteo por mes. La misma definición deberá utilizarse al integrar los apartados 1.5 y 3.2. La asociación IMERG–Q persiste después de retirar el ciclo anual: se reportan Pearson y Spearman de las anomalías y sus rezagos. Esto indica asociación entre desviaciones respecto de lo habitual, sin demostrar causalidad ni capacidad predictiva. No se presenta una climatología local como confiable: Zaragoza tiene solo 14 meses válidos, marzo no tiene ninguno y varios meses tienen un solo año. No es defendible completar la comparación de anomalías de las dos parejas locales con esa cobertura; se necesitan más años de lluvia local verificada.'),
('Alcance del apartado','Quedan desarrollados los tres diagramas, sus ejes y colores, los errores frente a lluvia local, ambas correlaciones, la sensibilidad a puntos influyentes, los rezagos y la comparación de anomalías IMERG–Q con apoyo P–R. La comparación de anomalías que incluye lluvia local queda condicionada a obtener una climatología adecuada. No se calculan p-valores simples suponiendo meses independientes, ni se atribuye causalidad. Una evaluación predictiva necesita separación temporal de ajuste y validación, prevista en 2.2 y 2.3.')]
ra,sa=corr(a[['I','Q']].dropna(),'I','Q')
paragraphs[5]=(paragraphs[5][0],paragraphs[5][1]+f' Sin rezago, las anomalías IMERG–Q dan Pearson {fmt(ra)} y Spearman {fmt(sa)}.')
paragraphs[4]=(paragraphs[4][0],paragraphs[4][1]+' En IMERG–Q, Pearson original es mayor sin rezago (0,62), mientras Spearman es ligeramente mayor a un mes (0,65 frente a 0,63): no hay un único rezago óptimo independiente del indicador. Con anomalías, el mayor valor de ambas correlaciones ocurre sin rezago (Pearson 0,64; Spearman 0,60). Para lluvia local–Q el máximo explorado es un mes (Pearson 0,65; Spearman 0,64), pero solo hay 14 pares y las muestras cambian. La correlación negativa a tres meses puede mezclar estacionalidad y tamaño muestral; no demuestra una respuesta física inversa.')
def table_html(df):return df.to_html(index=False,float_format=lambda v:f'{v:.3f}',border=0,classes='tabla-estadistica')
content=''.join('<h3>'+html.escape(t)+'</h3><p>'+html.escape(p)+'</p>' for t,p in paragraphs[:4])
for name,caption in [('dispersiones_21','Tres diagramas requeridos; meses locales con cobertura completa.'),('laminas_21','Apoyo de interpretación con escorrentía mensual R.')]:
 content+='<img style="width:100%;height:auto" alt="'+caption+'" src="data:image/png;base64,'+base64.b64encode((OUT/(name+'.png')).read_bytes()).decode()+'"><p>'+caption+'</p>'
content+='<h3>Correlaciones originales</h3>'+table_html(pd.DataFrame(summary))+'<h3>Sensibilidad al retirar un mes</h3>'+table_html(pd.DataFrame(influence))
content+=''.join('<h3>'+html.escape(t)+'</h3><p>'+html.escape(p)+'</p>' for t,p in paragraphs[4:6])
content+='<img style="width:100%;height:auto" alt="Anomalías mensuales" src="data:image/png;base64,'+base64.b64encode((OUT/'anomalias_21.png').read_bytes()).decode()+'">'
content+='<h3>Rezagos: P(t−k) frente a Q(t) o R(t)</h3>'+table_html(pd.DataFrame(lags))+'<h3>'+paragraphs[6][0]+'</h3><p>'+paragraphs[6][1]+'</p>'
interactive=[]
for frame,kind,specs in [(d,'original',[('I','L','IMERG–lluvia local'),('L','Q','Lluvia local–Q'),('I','Q','IMERG–Q'),('I','R','IMERG–R')]),(a,'anomalia',[('I','Q','Anomalías IMERG–Q'),('I','R','Anomalías IMERG–R')])]:
 for x,y,title in specs:
  z=frame[[x,y]].dropna();ident='scatter21-'+kind+'-'+x+y
  content+='<h3>'+title+' — consulta interactiva</h3><div id="'+ident+'" style="width:100%;height:430px"></div>'
  traces=[dict(x=z[x].tolist(),y=z[y].tolist(),type='scatter',mode='markers',text=z.index.strftime('%Y-%m').tolist(),marker=dict(size=8,color=z.index.month.tolist(),colorscale='Turbo',cmin=1,cmax=12,colorbar=dict(title='Mes',tickvals=list(range(1,13)))),hovertemplate='%{text}<br>x=%{x:.2f}<br>y=%{y:.2f}<extra></extra>')]
  coef=np.polyfit(z[x],z[y],1);xx=[float(z[x].min()),float(z[x].max())];traces.append(dict(x=xx,y=np.polyval(coef,xx).tolist(),mode='lines',line=dict(color='red'),hoverinfo='skip'))
  units={'I':'IMERG (mm/mes)','L':'Lluvia Zaragoza-AUT (mm/mes)','Q':'Caudal medio Q (m³/s)','R':'Escorrentía R (mm/mes)'}
  layout=dict(title=title,margin=dict(l=70,r=70,t=55,b=65),xaxis=dict(title=('Anomalía ' if kind=='anomalia' else '')+units[x]),yaxis=dict(title=('Anomalía ' if kind=='anomalia' else '')+units[y]),showlegend=False)
  if y=='L':
   hi=float(max(z.max())*1.08);traces.append(dict(x=[0,hi],y=[0,hi],mode='lines',line=dict(color='black',dash='dash'),hoverinfo='skip'));layout['xaxis']['range']=[0,hi];layout['yaxis'].update(range=[0,hi],scaleanchor='x',scaleratio=1)
  interactive.append(dict(id=ident,data=traces,layout=layout))
content+='<script>window.addEventListener("load",function(){const plots='+json.dumps(interactive,ensure_ascii=False)+';plots.forEach(function(p){if(window.Plotly&&document.getElementById(p.id)){Plotly.newPlot(p.id,p.data,p.layout,{responsive:true,displaylogo:false,toImageButtonOptions:{format:"svg"}});}});});</script>'
hp=ROOT/'informe_interactivo.html';ht=hp.read_text(encoding='utf-8')
section='<section class="panel" id="dispersiones-imerg"><h2>Diagramas de dispersión e interpretación — 2.1 actualizado</h2>'+content+'</section>'
ht,n=re.subn(r'(<\!-- DISPERSION_REQUERIDA_INICIO -->).*?(<\!-- DISPERSION_REQUERIDA_FIN -->)',lambda m:m[1]+section+m[2],ht,flags=re.S);assert n==1
ht=re.sub(r'(<\!-- DISPERSION_ANALISIS_INICIO -->).*?(<\!-- DISPERSION_ANALISIS_FIN -->)','',ht,flags=re.S)
hp.write_text(ht,encoding='utf-8')
def esc(s):
 for x,y in [('\\',r'\textbackslash{}'),('%',r'\%'),('_',r'\_'),('≥',r'$\geq$'),('−','-'),('–','--'),('′',"'"),('³',r'$^3$'),('×',r'$\times$'),('ρ',r'$\rho$')]:s=s.replace(x,y)
 return s
def tex_table(df,cols,headers):
 out=r'\begin{center}\small\begin{tabular}{'+'l'+'r'*(len(cols)-1)+r'}\hline'+'\n'+' & '.join(headers)+r' \\ \hline'+'\n'
 for _,row in df.iterrows():out+=' & '.join(esc(str(row[c])) if isinstance(row[c],str) else (str(int(row[c])) if c in ['n','rezago'] else fmt(row[c])) for c in cols)+r' \\'+'\n'
 return out+r'\hline\end{tabular}\end{center}'+'\n'
tex=r'\subsection{Diagramas de dispersión e interpretación}'+'\n'
for idx,(title,p) in enumerate(paragraphs):
 tex+=r'\subsubsection*{'+esc(title)+'}\n'+esc(p)+'\n'
 if idx==0:
  for name,cap in [('dispersiones_21','Tres diagramas requeridos con IMERG de polígono y lluvia local completa.'),('laminas_21','Comparación de precipitación y escorrentía en láminas mensuales.')]:tex+=r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_2_1/'+name+r'.pdf}\caption{'+cap+r'}\end{figure}'+'\n'
 if idx==3:
  tex+=tex_table(pd.DataFrame(summary),['relacion','n','Pearson','Spearman'],['Relación','n','Pearson','Spearman'])
  tex+=tex_table(pd.DataFrame(influence),['relacion','mes','r_sin_mes','r_min','r_max'],['Relación','Mes influyente','r sin mes','r mínimo','r máximo'])
 if idx==4:
  for serie in ['original','anomalia']:
   tex+=r'\textbf{Rezagos: '+serie+r'.} $P(t-k)$ frente a $Q(t)$ o $R(t)$.'+'\n'
   tex+=tex_table(pd.DataFrame(lags).query('serie==@serie'),['relacion','rezago','n','Pearson','Spearman'],['Relación','k','n','Pearson','Spearman'])
 if idx==5:tex+=r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_2_1/anomalias_21.pdf}\caption{Anomalías con climatología común 1998--2022.}\end{figure}'+'\n'
tp=DOC/'latex/informe_ordenado.tex';tt=tp.read_text(encoding='utf-8');start=tt.index(r'\subsection{Diagramas de dispersión e interpretación}');end=tt.index(r'\subsection{¿Se pueden construir modelos útiles?}',start);tt=tt[:start]+tex+tt[end:];tp.write_text(tt,encoding='utf-8')
(OUT/'apartado_2_1.tex').write_text(tex,encoding='utf-8')
(OUT/'resultados.json').write_text(json.dumps(dict(correlaciones=summary,errores=errors,sensibilidad=influence,rezagos=lags,anomalias_I_Q=dict(Pearson=ra,Spearman=sa),n_local=14,huellas={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [local_path,DOC/'imerg_poligono/series_alineadas.csv']}),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(errores=errors,anomalias_I_Q=[ra,sa],sensibilidad=influence),ensure_ascii=False,indent=2))

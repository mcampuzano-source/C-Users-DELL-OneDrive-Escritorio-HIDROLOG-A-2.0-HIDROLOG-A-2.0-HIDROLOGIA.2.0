"""Añade control de faltantes a LaTeX y HTML; ejecución repetible sin duplicados."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
LATEX=DOC/'latex'
a=pd.read_csv(ROOT/'la_vieja'/'punto_1'/'disponibilidad_mensual.csv',parse_dates=['mes']).set_index('mes')
assert a.dias_validos_P.equals(a.dias_validos_Q)
assert a.dias_faltantes_P.sum()==255
assert len(a)==504
excluded=a[a.dias_faltantes_P.gt(0)].copy()
assert len(excluded)==19
table=pd.DataFrame({'Mes':excluded.index.strftime('%Y-%m'),'Días esperados':excluded.dias_esperados.to_numpy(),'Días válidos P y Q':excluded.dias_validos_P.to_numpy(),'Días faltantes P y Q':excluded.dias_faltantes_P.to_numpy()})
table['Completitud (%)']=100*table['Días válidos P y Q']/table['Días esperados']
table.to_csv(DOC/'control_meses_excluidos.csv',index=False,encoding='utf-8-sig')
a.to_csv(DOC/'control_disponibilidad_mensual.csv',index_label='mes')
frame=pd.DataFrame({'ano':a.index.year,'mes':a.index.month,'validos':a.dias_validos_P,'faltantes':a.dias_faltantes_P,'esperados':a.dias_esperados})
frame['porcentaje']=frame.validos/frame.esperados*100
matrix=frame.pivot(index='mes',columns='ano',values='porcentaje')
months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
fig,ax=plt.subplots(figsize=(7,2.65),layout='constrained')
im=ax.imshow(matrix,origin='lower',aspect='auto',vmin=0,vmax=100,cmap='YlGn',extent=[1980.5,2022.5,.5,12.5])
ax.set_yticks(range(1,13),months); ax.tick_params(labelsize=8)
ax.set_xlabel('Año'); ax.set_title('Disponibilidad de P y Q: días válidos por mes',fontsize=10)
fig.colorbar(im,ax=ax,label='Días válidos (%)')
fig.savefig(LATEX/'figuras'/'control_faltantes.pdf',bbox_inches='tight')
fig.savefig(LATEX/'figuras'/'control_faltantes.png',dpi=250,bbox_inches='tight')
plt.close(fig)
custom=np.stack([frame.pivot(index='mes',columns='ano',values=v).to_numpy() for v in ['validos','faltantes','esperados']],axis=-1)
heat=go.Figure(go.Heatmap(x=matrix.columns.tolist(),y=months,z=matrix.to_numpy().tolist(),customdata=custom.tolist(),zmin=0,zmax=100,colorscale='YlGn',colorbar={'title':'Válidos (%)'},hovertemplate='%{y} %{x}<br>Completitud: %{z:.1f}%<br>Válidos: %{customdata[0]} de %{customdata[2]}<br>Faltantes P y Q: %{customdata[1]}<extra></extra>'))
heat.update_layout(height=420,template='plotly_white',margin={'l':50,'r':30,'t':25,'b':45},xaxis_title='Año')
plot=heat.to_html(full_html=False,include_plotlyjs=False,div_id='control-faltantes',config={'responsive':True,'displaylogo':False})
summary='''<p>Se reconstruyeron los <b>15.340 días</b> del calendario 1981–2022, incluidos los años bisiestos. El archivo contiene 15.085 fechas y omite <b>255 días (1,66 %)</b>. P y Q carecen de las mismas fechas; son 255 días por variable, no 510 fechas distintas.</p><p>De 504 meses, se conservan <b>485 (96,23 %)</b> y se excluyen <b>19 (3,77 %)</b>: seis sin ningún día disponible y trece parcialmente completos. Un mes se conserva solo con el <b>100 % de días válidos</b>. Los ceros medidos se conservan, los ausentes no se convierten en ceros y no se rellenan ni prorratean sumas.</p>'''
assert int(excluded.dias_validos_P.eq(0).sum())==6
section='''<!-- CONTROL_FALTANTES_INICIO --><section class="panel" id="faltantes"><h2>2. Control de datos faltantes</h2>'''+summary+plot+'''<h3>Meses excluidos</h3><p>Estos conteos se aplican por igual a P y Q. La tabla muestra únicamente los 19 meses excluidos; los otros 485 están completos.</p><label for="buscar-mes">Buscar año o mes: </label><input id="buscar-mes" placeholder="Ejemplo: 2011" oninput="document.querySelectorAll('#tabla-faltantes tbody tr').forEach(r=>r.hidden=!r.textContent.includes(this.value))" style="padding:8px;margin-bottom:12px"><div style="overflow:auto">'''+table.to_html(index=False,table_id='tabla-faltantes',border=0,float_format=lambda v:f'{v:.2f}')+'''</div><style>#tabla-faltantes{border-collapse:collapse;width:100%}#tabla-faltantes th,#tabla-faltantes td{padding:8px;border-bottom:1px solid #d8e1e7;text-align:left}</style><h3>Distribución temporal y efecto sobre el análisis</h3><p>Los huecos continuos más largos son diciembre de 2007–enero de 2008 (62 días), agosto–septiembre de 1992 (61 días) y 8 de noviembre–31 de diciembre de 2011 (54 días). Los vacíos impiden describir esos intervalos y pueden afectar la representación de temporadas húmedas o secas; no se supone que sean aleatorios.</p><p>Al aceptar meses de caudal con al menos 90 % de días se obtendrían 494 meses y una media de 100,91 m³/s, frente a 98,70 m³/s con el criterio estricto. Es una sensibilidad, no el análisis principal ni una autorización para sumar lluvias parciales.</p><p class="nota">El control corresponde al archivo CAMELS ensamblado. No demuestra que CHIRPS original carezca de esas fechas. Tampoco describe faltantes de IMERG o de las estaciones pluviométricas individuales, cuyos registros aún no están incorporados.</p></section><!-- CONTROL_FALTANTES_FIN -->'''
htmlpath=DOC/'informe_interactivo.html'
html=htmlpath.read_text(encoding='utf-8')
start='<!-- CONTROL_FALTANTES_INICIO -->'; end='<!-- CONTROL_FALTANTES_FIN -->'
if start in html:
    left,rest=html.split(start,1); _,right=rest.split(end,1); html=left+right
html=html.replace('<footer>',section+'<footer>',1).replace('Documento en construcción · Paso 1','Documento en construcción · Pasos 1–2')
htmlpath.write_text(html,encoding='utf-8')
rows='\n'.join(f'{r.iloc[0]} & {int(r.iloc[1])} & {int(r.iloc[2])} & {int(r.iloc[3])} & {r.iloc[4]:.2f}'.replace('.',',')+r' \\' for _,r in table.iterrows())
tex=r'''\section{Control de datos faltantes}
Se reconstruyó el calendario diario completo de 1981--2022, incluidos los años
bisiestos. De 15\,340 días esperados, el archivo contiene 15\,085 fechas y omite
255 días (1,66\,\%) tanto en P como en Q. Son las mismas fechas ausentes para
ambas variables: no se deben sumar como 510 días distintos.

\subsection{Criterio de completitud}
Se retiene únicamente un mes con el 100\,\% de sus días válidos. De 504 meses,
se conservan 485 (96,23\,\%) y se excluyen 19 (3,77\,\%): seis totalmente ausentes
y trece parcialmente completos. Los ceros se conservan y los faltantes permanecen
como vacíos; no se rellena ni se prorratea la precipitación.

\begin{figure}[H]
\centering
\includegraphics[width=\linewidth]{figuras/control_faltantes.pdf}
\caption{Disponibilidad diaria dentro de cada mes. P y Q tienen la misma cobertura
en el archivo CAMELS; 100\,\% indica un mes completo.}
\label{fig:faltantes}
\end{figure}

\begin{center}
\small
\begin{tabular}{lrrrr}
\hline
Mes & Esperados & Válidos P/Q & Faltantes P/Q & Completitud (\%) \\
\hline
'''+rows+r'''
\hline
\end{tabular}
\end{center}

\subsection{Consecuencias para la interpretación}
Los vacíos continuos más largos son diciembre de 2007--enero de 2008 (62 días),
agosto--septiembre de 1992 (61 días) y 8 de noviembre--31 de diciembre de 2011
(54 días). No es posible reconstruir su evolución a partir del archivo analizado;
los faltantes pueden sesgar la representación de temporadas y extremos.

Como sensibilidad, aceptar meses de Q con al menos 90\,\% de días elevaría la
muestra a 494 meses y la media a 100,91~m$^3$/s, frente a 98,70~m$^3$/s con el
criterio estricto. Se mantiene el 100\,\% como resultado principal. Esta comparación
no justifica tratar sumas parciales de precipitación como acumulados completos.

Este control describe el archivo CAMELS ensamblado, no la disponibilidad original
de CHIRPS, IMERG ni de las estaciones pluviométricas individuales. No se supone
que los faltantes ocurran al azar.
'''
(LATEX/'secciones'/'02_control_faltantes.tex').write_text(tex,encoding='utf-8')
main=LATEX/'informe.tex'; content=main.read_text(encoding='utf-8')
if r'\input{secciones/02_control_faltantes}' not in content:
    content=content.replace(r'\end{document}',r'\clearpage'+'\n'+r'\input{secciones/02_control_faltantes}'+'\n'+r'\end{document}')
content=content.replace('Documento en construcción -- Paso 1','Documento en construcción -- Pasos 1 y 2')
main.write_text(content,encoding='utf-8')
print('Control de faltantes agregado a ambos documentos; 19 meses y 255 días comprobados.')

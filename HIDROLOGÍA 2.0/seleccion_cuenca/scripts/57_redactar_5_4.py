"""Interpretación física e integración de los cinco puntos, PDF y HTML."""
from pathlib import Path
import json,html,re,shutil,base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
import pymupdf
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'la_vieja/documentos';OUT=DOCS/'apartado_5_4'
MONTHS=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
m=json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
clim=pd.read_csv(OUT/'climatologia_comun.csv');idx=pd.read_csv(OUT/'contraste_NOAA_Nino34.csv');reg=pd.read_csv(OUT/'regiones_coherentes.csv');dep=pd.read_csv(OUT/'dependencias_campos.csv');fourier=pd.read_csv(OUT/'sintesis_fourier.csv');lags=pd.read_csv(OUT/'lluvia_caudal_rezagos.csv')
robust=pd.read_csv(DOCS/'apartado_5_3/resumen_mensual.csv')
refs=[
 ('Poveda et al. (2001)','Poveda, G., Jaramillo, A., Gil, M. M., Quiceno, N. y Mantilla, R. I. Seasonality in ENSO-related precipitation, river discharges, soil moisture, and vegetation index in Colombia. Water Resources Research, 37, 2169-2178.','https://doi.org/10.1029/2000WR900395'),
 ('Poveda et al. (2011)','Poveda, G., Álvarez, D. M. y Rueda, O. A. Hydro-climatic variability over the Andes of Colombia associated with ENSO: a review of climatic processes and their impact on one of the Earth’s most important biodiversity hotspots. Climate Dynamics, 36, 2233-2249.','https://doi.org/10.1007/s00382-010-0931-y'),
 ('Poveda et al. (2014)','Poveda, G., Jaramillo, L. y Vallejo, L. F. Seasonal precipitation patterns along pathways of South American low-level jets and aerial rivers. Water Resources Research, 50, 98-118.','https://doi.org/10.1002/2013WR014087'),
 ('POMCA La Vieja, capítulo 3','CVC/CARDER/CRQ. Diagnóstico climático de la cuenca del río La Vieja, capítulo 3, documento oficial del POMCA. Se archivó el PDF consultado; ver POMCA_La_Vieja_clima_fuente.pdf.','https://www.cvc.gov.co/sites/default/files/Planes_y_Programas/Planes_de_Ordenacion_y_Manejo_de_Cuencas_Hidrografica/La%20Vieja%20-%20POMCA%20en%20Ajuste/Fase%20Diagnostico/3_CapituloI_Diagnostico_Clima.pdf'),
 ('NOAA PSL, Niño 3.4','NOAA Physical Sciences Laboratory. Serie mensual Niño 3.4 descargada: ERSST v6, anomalías de 1981-2010; región 5N-5S, 170W-120W; unidades °C. Archivo y huella en indice_NOAA_metadatos.json.','https://psl.noaa.gov/data/correlation/nina34.anom.data'),
]

noaa_q=idx.query('response == "Q" and month == 2').iloc[0]
noaa_i=idx.query('response == "IMERG" and month == 1').iloc[0]
noaa_c=idx.query('response == "CHIRPS" and month == 1').iloc[0]
qmap=robust.query('key == "Q_sst_l0" and month == 2').iloc[0]
coherent=reg.query('response == "Q" and field == "sst" and lag == 0 and month == 2 and region == "Pacifico_ecuatorial"').iloc[0]
texts=[
 ('Criterio de lectura y clasificación hidroclimática',
  f'La cuenca del río La Vieja hasta Cartago se caracteriza, a escala mensual, como una cuenca andina de régimen pluvial bimodal, con dos temporadas lluviosas y una respuesta de caudal modulada por el ciclo anual y la variabilidad interanual. Esta es una clasificación hidrológica funcional, no una clase Köppen homogénea para todo el relieve. La síntesis usa las mismas 285 fechas completas de 1998-2022: CHIRPS, IMERG poligonal, Q Cartago y temperatura ERA5-Land. El área de referencia es 2797,19 km². La temperatura media de estos meses es {m["T_mean_C"]:.2f} °C y el caudal medio {m["Q_mean_m3_s"]:.2f} m³/s. Los valores son medias mensuales de la muestra común, no una caracterización espacial de cada piso térmico.'),
 ('Ciclo anual: lluvia, almacenamiento y respuesta de cuenca',
  'CHIRPS e IMERG presentan temporadas lluviosas en abril-mayo y octubre-noviembre. En la muestra común, abril registra 245,04 y 276,15 mm/mes, y octubre 258,51 y 286,96 mm/mes, respectivamente. Q alcanza un máximo local en mayo (147,02 m³/s) y el máximo anual en noviembre (182,79 m³/s); su mínimo se observa en agosto (51,75 m³/s). Los meses relativamente secos no son meses sin lluvia: CHIRPS conserva 92,15 mm en julio e IMERG 151,88 mm en enero. El POMCA La Vieja (capítulo 3) describe un régimen bimodal de las estaciones y lo relaciona con el paso estacional de la ZCIT. La topografía y el transporte regional de humedad pueden modular esa respuesta; Poveda et al. (2014) documentan vías estacionales de los chorros de bajo nivel del Pacífico y el Caribe. Esos mecanismos dan contexto regional, sin demostrar el origen de cada lluvia de esta cuenca.'),
 ('La relación lluvia-caudal limita la interpretación del rezago',
  'Tras retirar la climatología mensual, la asociación contemporánea P-Q es r=0,542 para CHIRPS y 0,636 para IMERG (n=285). Al hacer que la lluvia anteceda a Q un mes, disminuye a 0,415 y 0,483 (n=274); a dos meses, a 0,303 y 0,379 (n=270). El desplazamiento se aplica sobre el calendario completo, sin concatenar huecos. El máximo climatológico de Q posterior al de lluvia es compatible con humedad antecedente, almacenamiento y tránsito por la red, pero no estima un tiempo de concentración. Tampoco prueba que un desfase de un mes sea el único mecanismo: el máximo contemporáneo de las anomalías y las diferencias entre productos deben conservarse en la explicación. No se midieron flujos subterráneos, humedad de suelo, extracciones o regulación para separar sus contribuciones.'),
 ('Regiones coherentes, signos y meses de mayor evidencia',
  f'Los patrones más extensos que reúnen el criterio BY y estabilidad del 5.3 corresponden a Q-SST en febrero, con ell=0 y ell=1; aparecen asociaciones adicionales en marzo. En febrero, Q-SST contemporáneo reúne {int(qmap.candidate_cells)} celdas ({qmap.area_candidate_pct:.2f}% del dominio oceánico válido ponderado), con un componente contiguo de {int(qmap.largest_connected_candidate_cells)} celdas. La región ecuatorial del Pacífico (-10 a 10°; 180 a 80°W) contiene {int(coherent.candidate_cells)} de esas celdas y muestra signo negativo: SST más alta coincide con Q más bajo. Estos son resultados condicionados a la inferencia AR(1) y al criterio declarado, no una teleconexión causal demostrada. Para precipitación, la evidencia espacial conjunta se concentra en junio frente a SLP en el Atlántico tropical oriental: 27 celdas para CHIRPS y 76 para IMERG, principalmente con signo negativo. La señal de precipitación no reproduce de forma uniforme la distribución de Q-SST. Los meses de mayor asociación climática tampoco equivalen a los de mayor promedio de lluvia o caudal.'),
 ('Estacionalidad y cambios de ubicación o signo',
  'En Niño 3.4, la media de los coeficientes Q-SST sin tendencia es negativa durante todos los meses, pero varía de -0,83 en febrero a -0,27 en mayo. La media regional se refiere a coeficientes por celda, no a la correlación de un índice. En el Caribe y el Atlántico tropical norte cambian magnitud y signo: Q-SST del Caribe pasa de aproximadamente -0,60 en febrero a +0,13 en julio; el Atlántico tropical norte pasa de -0,38 a +0,25. Esos cambios describen mapas, pero no superan BY en esas cajas para febrero o julio. No deben presentarse como un desplazamiento robusto del centro de acción. La región Niño 3.4 conserva el signo entre subperiodos en febrero, y 64,62% de su área válida reúne el criterio candidato. Las regiones remotas y los signos estacionales débiles orientan hipótesis, no efectos independientes comprobados.'),
 ('¿Los campos atmosféricos apoyan la explicación de SST?',
  'El apoyo es parcial. En el entorno amplio de Colombia (-5 a 15°N; 85 a 65°W), la media de Q-Z500 sin tendencia es negativa: -0,77 en enero, -0,73 en febrero y -0,75 en marzo; enero incluye 15 celdas candidatas. Una altura geopotencial mayor puede acompañar una columna tropical más cálida o un patrón de circulación, compatible con una señal compartida con SST. Z500 no es una medida directa de subsidencia ni transporte de vapor. En cambio, Q-SLP en esa caja tiene signo positivo en febrero (+0,43), sin celdas candidatas, y alterna de signo a lo largo del año. Esto no respalda una cadena uniforme “más presión local implica menos caudal”. Los gradientes de presión, viento, convergencia de humedad y movimientos verticales no se analizaron aquí. Por ello, SLP/Z500 ofrecen contexto de circulación, pero no bastan para demostrar un mecanismo de transporte sobre el relieve andino.'),
 ('Mecanismo físico propuesto y contraste con bibliografía regional',
  'La hipótesis físicamente plausible conecta calentamiento del Pacífico tropical con reorganización de la circulación, cambios de entrada y convergencia de humedad, anomalías de lluvia y una respuesta de Q modulada por el estado previo de la cuenca. Poveda et al. (2011) documentan en los Andes colombianos anomalías hidrológicas generalmente negativas durante El Niño y positivas durante La Niña, con efectos más intensos en diciembre-febrero. El signo negativo Q-SST y la concentración de evidencia en febrero son compatibles con ese marco. Poveda et al. (2001) muestran que la respuesta de caudal puede superar la de precipitación por procesos que también involucran humedad de suelo y evapotranspiración. En esta cuenca tales variables no se observaron: se proponen como mecanismo, no se cuantifica su papel. El contraste regional no autoriza trasladar magnitudes de otras cuencas ni atribuir un episodio individual a ENSO.'),
 ('Dependencia entre campos: la evidencia no se suma como efectos independientes',
  f'Los campos globales pueden responder al mismo forzamiento oceánico-atmosférico. Como diagnóstico, se compararon Niño 3.4 interno y medias de SLP/Z500 del entorno de Colombia, retirando tendencias por mes calendario. Las correlaciones entre pares de campos varían de {dep.r_detrended.min():+.2f} a {dep.r_detrended.max():+.2f} a lo largo de los doce meses. Ese acuerdo confirma que no es correcto sumar correlaciones separadas como tres influencias independientes. El diagnóstico no separa causalidad ni calcula contribuciones únicas; requiere un análisis multivariado con hipótesis, covariables y validación específicos para ello. Las cajas se declararon en el script y se conserva la tabla mensual de dependencia.'),
 ('Contraste complementario con un índice NOAA PSL documentado',
  f'Se descargó el índice mensual Niño 3.4 de NOAA PSL, cuyo archivo identifica ERSST v6 y anomalías respecto a 1981-2010. No es ONI, no se aplica una media móvil trimestral y no se clasifican eventos oficiales. Se reexpresa sobre los mismos meses de cuenca y se retira la tendencia en ambas series por mes. El contraste contemporáneo se fijó para las tres respuestas y doce meses: familia complementaria de 36 pruebas Pearson, p AR(1) aproximados y ajuste BY, separada de la familia de mapas. En febrero, Q tiene r={noaa_q.r_detrended:+.3f} y q_BY={noaa_q.q_BY_36:.2g} (n=24); IMERG supera BY en enero-febrero, mientras CHIRPS no lo supera en ningún mes. En enero, CHIRPS presenta r={noaa_c.r_detrended:+.3f}, pero q_BY={noaa_c.q_BY_36:.3f}. La distinción entre productos es material. El índice v6 contrasta con el campo v5 del 5.2-5.3 y comparte información de SST; no constituye una réplica completamente independiente ni altera las decisiones BY de los mapas.'),
 ('Un rezago no demuestra pronóstico',
  'El ell=1 del 5.2-5.3 conserva la convención de campo climático del mes anterior a la respuesta. La persistencia de una región Q-SST con ese rezago es compatible con evolución lenta del clima y memoria de la cuenca, pero también con autocorrelación del campo. No se eligió el rezago que maximiza r. Una asociación contemporánea usa información del mismo mes y no representa un predictor anticipado. Los modelos de lluvia-Q del punto 2 sí tienen una reserva temporal evaluada (68 meses, 2017-2022): NSE=0,605 para CHIRPS y 0,573 para IMERG, frente a 0,418 para climatología. Esa validación corresponde a esos modelos; no se transfiere al índice Niño 3.4 ni a un nuevo pronóstico climático. Este apartado no afirma capacidad predictiva ENSO-Q fuera de muestra.'),
 ('Síntesis de los puntos 4 y 5: escalas, procesos y límites',
  'En la ventana común continua 1998-01 a 2004-01 (73 meses), Fourier asigna 58,1% y 46,6% de la potencia normalizada de CHIRPS e IMERG originales a la banda semianual; al retirar el ciclo mensual descienden a 6,6% y 3,7%. Esto respalda la descripción de dos temporadas lluviosas. Q conserva variabilidad a escalas más largas: en anomalías, 65,3% de la potencia normalizada queda en periodos >=24 meses, frente a 25,7% para CHIRPS y 20,3% para IMERG. Sin embargo, el máximo interanual de esa ventana se sitúa en 73 meses: solo un ciclo observado. No demuestra una oscilación estable. La concentración espacial Q-SST y el contraste Niño 3.4 son compatibles con modulación climática interanual, pero compartir una banda de 2-10 años no identifica ENSO. No se calcularon coherencia espectral, fase ni significancia frente a ruido rojo. Los espectros de series con diferente duración tampoco deben compararse como si tuvieran idéntica resolución.'),
 ('Balance de las hipótesis de trabajo',
  'No se recuperó del informe local una formulación inicial formal de hipótesis; no se inventa un prerregistro ni se atribuye retrospectivamente al grupo. Como balance se revisan dos proposiciones operativas: un régimen pluvial bimodal, y una modulación interanual asociada al Pacífico tropical. La primera queda respaldada por climatología, Fourier y contexto del POMCA. La segunda se mantiene de forma condicionada para Q en regiones y meses concretos, pero debe modificarse cualquier expectativa de una respuesta ENSO igual para CHIRPS, IMERG y caudal o de tres campos independientes. No se comprueban la cadena completa de humedad/evapotranspiración, una tendencia común atribuible a cambio climático, ni la predicción de Q con índices globales. El esquema conceptual distingue esas evidencias de los mecanismos propuestos.'),
]

conclusions=[
 'La cuenca presenta un régimen pluvial bimodal en la muestra común 1998-2022, con lluvias altas en abril-mayo y octubre-noviembre y mayor caudal climatológico en noviembre. La clasificación es funcional y mensual; el relieve impide asignar una clase climática espacial uniforme a partir de una media de cuenca.',
 'CHIRPS e IMERG son productos espaciales distintos. La suma de las doce medias climatológicas es 2056,36 y 2604,56 mm, respectivamente; no es la media de totales de años completos. La diferencia limita un balance hídrico cuantitativo único. Zaragoza ofrece 14 meses completos y no permite validar una climatología interanual de lluvia en tierra.',
 'Las relaciones lluvia-Q conservan evidencia después de retirar el ciclo anual, y los modelos del punto 2 superan la climatología en su reserva de 68 meses. Sus errores y diferencias entre fuentes impiden generalizar esa capacidad a un pronóstico climático nuevo.',
 'Las pendientes del contraste común de 285 meses del punto 3 incluyen cero en sus intervalos HAC para CHIRPS, IMERG, Q y ERA5-Land. Los resultados de registros completos y fuentes auxiliares describen otras muestras. No se identifica aquí una tendencia secular común atribuible a una causa única.',
 'La banda semianual domina las precipitaciones originales en la ventana Fourier común; la variabilidad de mayor periodo en Q es descriptiva y la ventana corta no demuestra un ciclo ENSO estable. La potencia normalizada expresa reparto relativo, no magnitud física equivalente entre lluvia, caudal y temperatura.',
 'La evidencia climática más extensa y estable del análisis global se concentra en Q-SST de febrero. Precipitación muestra patrones y sensibilidad a la fuente distintos. SLP y Z500 ofrecen apoyo parcial y dependiente; la cadena de transporte, humedad del suelo y evapotranspiración sigue siendo una hipótesis. Las pruebas AR(1)/BY son aproximadas, la causalidad no se establece y la defensa requiere revisar esta interpretación con el grupo.'
]
evidence=[
 ['1. Exploración','Bimodalidad de P; Q máximo en noviembre','Climatología común: P abril/octubre; Q 182,79 m³/s en noviembre','Pluvial bimodal, con posible almacenamiento','POMCA La Vieja; datos comunes','Productos espaciales; lluvia local muy corta'],
 ['2. Modelos','Asociación P-Q y desempeño reservado','r anomalías 0,542/0,636; NSE reservado 0,605/0,573','Respuesta de escorrentía, información adicional al ciclo','Apartados 2.1-2.3','No valida ENSO como predictor; errores persistentes'],
 ['3. Tendencias','Sin una pendiente común inequívoca','IC HAC de las cuatro variables incluyen cero en 285 meses','Variabilidad natural y cambios locales son alternativas','Tabla común del apartado 3.6','No atribuir cambio climático desde una pendiente'],
 ['4. Fourier','Dominio estacional en P; bajas frecuencias en Q','Semianual 58,1/46,6%; interanual Q anomalías 65,3%','Dos temporadas; posible memoria e influencia climática','Punto 4, ventana continua N=73','Un ciclo en pico interanual; sin coherencia ni ruido rojo'],
 ['5. Clima global','Q-SST febrero; apoyo atmosférico parcial','244 celdas candidatas; NOAA Q-Feb r=-0,882','Modulación climática compatible con contexto ENSO','5.3; NOAA PSL; Poveda 2001/2011','Inferencia aproximada; campos dependientes; no causal']
]
(OUT/'tabla_evidencia_mecanismos.csv').write_text(pd.DataFrame(evidence,columns=['punto','resultado','evidencia','mecanismo_propuesto','fuente','limitacion']).to_csv(index=False),encoding='utf-8')
(OUT/'interpretacion.md').write_text('# 5.4. Interpretación física e integración\n\n'+'\n\n'.join('## '+t+'\n\n'+s for t,s in texts)+'\n\n## Cierre de los cinco puntos\n\n'+'\n\n'.join(conclusions)+'\n\n## Referencias\n\n'+'\n\n'.join(label+'. '+cite+' '+url for label,cite,url in refs),encoding='utf-8')

# New synthesis figures use quantitative tables already calculated.
fig,axes=plt.subplots(2,1,figsize=(9,6),sharex=True)
for col,label,color in [('P_CHIRPS_mm_mean','CHIRPS','#275d8a'),('P_IMERG_poligono_mm_mean','IMERG','#b5631e')]:axes[0].plot(np.arange(1,13),clim[col],'-o',label=label,color=color)
axes[0].set_ylabel('Precipitación (mm/mes)');axes[0].legend();axes[1].plot(np.arange(1,13),clim.Q_m3_s_mean,'-o',color='#326d50',label='Q Cartago');axes[1].set_ylabel('Caudal (m³/s)');axes[1].set_xticks(np.arange(1,13),MONTHS);axes[1].set_xlabel('Mes calendario')
for ax in axes:ax.grid(alpha=.2)
fig.suptitle('Ciclo anual común: 285 meses completos, 1998-2022');fig.tight_layout();fig.savefig(OUT/'ciclo_y_respuesta.pdf');fig.savefig(OUT/'ciclo_y_respuesta.png',dpi=160);plt.close(fig)

fig,ax=plt.subplots(figsize=(9,4.7))
for response,color in [('CHIRPS','#275d8a'),('IMERG','#b5631e'),('Q','#326d50')]:
 a=idx[idx.response==response];ax.plot(a.month,a.r_detrended,'-o',color=color,label=response);s=a[a.q_BY_36<=.05];ax.scatter(s.month,s.r_detrended,s=90,facecolors='none',edgecolors=color,linewidths=1.7)
ax.axhline(0,color='grey',lw=.8);ax.set(ylim=(-1,1),xticks=np.arange(1,13),xticklabels=MONTHS,ylabel='Pearson sin tendencia',title='Contraste Niño 3.4 NOAA PSL (ERSST v6), ell=0');ax.grid(alpha=.2);ax.legend();fig.text(.12,.015,'Círculo exterior: BY<=0,05 en familia complementaria de 36 pruebas. p AR(1) aproximados; no es ONI.',fontsize=8);fig.tight_layout(rect=(0,.055,1,1));fig.savefig(OUT/'indice_NOAA_contraste.pdf');fig.savefig(OUT/'indice_NOAA_contraste.png',dpi=160);plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(10,4.8),gridspec_kw={'width_ratios':[1.3,1]})
pairs=[('sst','slp'),('sst','z500'),('slp','z500')];a=np.array([dep[(dep.field1==x)&(dep.field2==y)].r_detrended.values for x,y in pairs]).T
im=axes[0].imshow(a,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto');axes[0].set(xticks=np.arange(3),xticklabels=['Niño-SLP','Niño-Z500','SLP-Z500'],yticks=np.arange(12),yticklabels=MONTHS,title='Dependencia entre medias regionales');fig.colorbar(im,ax=axes[0],label='r sin tendencia')
x=np.arange(4);variables=['CHIRPS','IMERG','Q','T'];original=[];anomaly=[]
for var in variables:
 r=fourier[fourier.variable==var];original.append(float(r.iloc[0].semiannual_pct));anomaly.append(float(r.iloc[1].semiannual_pct))
axes[1].bar(x-.17,original,width=.34,label='Original');axes[1].bar(x+.17,anomaly,width=.34,label='Anomalía');axes[1].set(xticks=x,xticklabels=variables,ylabel='Potencia en banda semianual (%)',title='Fourier: ventana común N=73');axes[1].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'dependencia_y_escalas.pdf');fig.savefig(OUT/'dependencia_y_escalas.png',dpi=160);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,5.8));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
nodes=[(.02,.68,'SST Pacífico tropical\nDato global + índice NOAA',True),(.36,.68,'Circulación de gran escala\nSLP y Z500 disponibles',True),(.70,.68,'Transporte y convergencia\nde humedad: no medidos',False),(.70,.32,'Precipitación de cuenca\nCHIRPS e IMERG',True),(.36,.32,'Suelo, almacenamiento y ET\nProcesos no medidos',False),(.02,.32,'Caudal Q en Cartago\nObservación CAMELS/IDEAM',True)]
for x,y,label,measured in nodes:
 ax.add_patch(FancyBboxPatch((x,y),.28,.18,boxstyle='round,pad=.01',facecolor='#e5eff5' if measured else '#fff2d7',edgecolor='#456371'));ax.text(x+.14,y+.09,label,ha='center',va='center',fontsize=10)
for a,b in [((.30,.77),(.36,.77)),((.64,.77),(.70,.77)),((.84,.68),(.84,.50)),((.70,.41),(.64,.41)),((.36,.41),(.30,.41))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='->',mutation_scale=14,ls='--',color='#8a652a',linewidth=1.5))
ax.text(.5,.97,'Hipótesis de proceso: no toda la cadena fue observada',ha='center',fontsize=14,weight='bold');ax.text(.5,.13,'Relaciones medidas: P-Q y Q-SST; su asociación no determina el sentido causal.\nAzul: variables disponibles. Beige y flechas discontinuas: mecanismos propuestos.\nRelieve y coberturas pueden modular la lluvia y el almacenamiento; no se estimaron efectos separados.',ha='center',va='center',fontsize=10);fig.tight_layout();fig.savefig(OUT/'esquema_conceptual.pdf');fig.savefig(OUT/'esquema_conceptual.png',dpi=160);plt.close(fig)

styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Body54',fontName='Helvetica',fontSize=10.2,leading=14.5,spaceAfter=10));styles.add(ParagraphStyle(name='Cell54',fontName='Helvetica',fontSize=8,leading=10))
styles['Heading2'].keepWithNext=True
def p(t,style='Body54'):return Paragraph(html.escape(t),styles[style])
def table(headers,rows,widths):
 t=Table([[p(str(c),'Cell54') for c in row] for row in [headers]+rows],colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deebf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f7f8')]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));return t
story=[p('5.4. Interpretación física e integración','Heading1')]
for title,text in texts:story +=[p(title,'Heading2'),p(text)]
story +=[p('Síntesis sustentada de los cinco puntos','Heading2'),p('La tabla conecta resultados, mecanismo propuesto, evidencia, fuente y limitación. Los mecanismos no medidos se identifican como hipótesis.'),table(['Punto','Resultado y evidencia','Mecanismo y fuente','Limitación'],[[a,b+'; '+c,d+'; '+e,f] for a,b,c,d,e,f in evidence],[64,149,156,114])]
story +=[p('Cierre de la caracterización hidroclimática','Heading2')]
for c in conclusions:story.append(p(c))
story +=[p('Referencias de la interpretación física','Heading2')]
for label,cite,url in refs:
 story +=[p(label+'. '+cite),Paragraph('<link href="'+url+'" color="#24577a">'+html.escape(url)+'</link>',styles['Cell54']),Spacer(1,9)]
story +=[p('Reproducción, alcance y verificación','Heading2'),p('El script 56 calcula tablas e índice, el 57 genera figuras y discusión, y el 58 integra los documentos. Se archivan los datos NOAA utilizados y sus metadatos, el diagnóstico del POMCA y el JSON de Fourier extraído del informe publicado. Las cifras de Fourier son una síntesis del punto 4, no una nueva prueba de significancia. Las tablas permiten revisar el cálculo; no hay interpolación o sustitución de observaciones. La interpretación y la declaración final de uso de IA deben ser revisadas por el grupo antes de la entrega y defensa.')]
SimpleDocTemplate(str(OUT/'texto_5_4.pdf'),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=60).build(story)
atlas=pymupdf.open(OUT/'texto_5_4.pdf');bookmarks=[]
figures=[('ciclo_y_respuesta','Ciclo anual y respuesta de cuenca'),('indice_NOAA_contraste','Contraste mensual con Niño 3.4 NOAA PSL'),('dependencia_y_escalas','Dependencia de campos y síntesis espectral'),('esquema_conceptual','Esquema conceptual de evidencias e hipótesis')]
for name,title in figures:
 f=pymupdf.open(OUT/(name+'.pdf'));bookmarks.append([1,title,len(atlas)+1]);atlas.insert_pdf(f);f.close()
atlas.set_toc(bookmarks);atlas.save(OUT/'punto_5_4.pdf',garbage=4,deflate=True);atlas.close()

body=''.join('<h4>'+html.escape(title)+'</h4><p>'+html.escape(text)+'</p>' for title,text in texts)
body+='<h4>Síntesis sustentada de los cinco puntos</h4>'+pd.DataFrame(evidence,columns=['Punto','Resultado','Evidencia','Mecanismo propuesto','Fuente','Limitación']).to_html(index=False,border=0)
body+='<h4>Cierre de la caracterización hidroclimática</h4>'+''.join('<p>'+html.escape(c)+'</p>' for c in conclusions)
for name,title in figures:
 if name!='esquema_conceptual':body+='<h4>'+html.escape(title)+'</h4><div id="'+name+'54" style="height:560px"></div>'
 else:
  data=base64.b64encode((OUT/(name+'.png')).read_bytes()).decode('ascii');body+='<figure><img style="max-width:100%;height:auto" src="data:image/png;base64,'+data+'" alt="'+title+'"><figcaption>'+html.escape(title)+'</figcaption></figure>'
graph_data={'months':MONTHS,'CHIRPS':clim.P_CHIRPS_mm_mean.tolist(),'IMERG':clim.P_IMERG_poligono_mm_mean.tolist(),'Q':clim.Q_m3_s_mean.tolist(),'n':clim.P_CHIRPS_mm_count.tolist(),'index':idx.to_dict('records'),'dependency':None,'semi_original':original,'semi_anomaly':anomaly}
# `a` was reused as a node endpoint in the conceptual figure; reconstruct dependency matrix explicitly.
graph_data['dependency']=np.array([dep[(dep.field1==x)&(dep.field2==y)].r_detrended.values for x,y in pairs]).T.tolist()
script=r'''<script id="script54">(function(){const D=__DATA__,colors={CHIRPS:'#275d8a',IMERG:'#b5631e',Q:'#326d50'};
function init(){if(!window.Plotly||!document.getElementById('ciclo_y_respuesta54'))return;
const config={responsive:true,displaylogo:false};
Plotly.newPlot('ciclo_y_respuesta54',[
...['CHIRPS','IMERG'].map(k=>({type:'scatter',mode:'lines+markers',x:D.months,y:D[k],name:k,line:{color:colors[k]},customdata:D.n,hovertemplate:'%{x}: %{y:.2f} mm/mes · n=%{customdata}<extra>'+k+'</extra>'})),
{type:'scatter',mode:'lines+markers',x:D.months,y:D.Q,name:'Q Cartago',xaxis:'x2',yaxis:'y2',line:{color:colors.Q},customdata:D.n,hovertemplate:'%{x}: %{y:.2f} m³/s · n=%{customdata}<extra>Q</extra>'}],
{title:'Ciclo anual común, 285 meses (1998-2022)',margin:{t:75,b:50,l:70,r:25},yaxis:{domain:[.58,1],title:'Precipitación (mm/mes)'},xaxis:{anchor:'y'},yaxis2:{domain:[0,.42],title:'Caudal (m³/s)'},xaxis2:{anchor:'y2'},legend:{orientation:'h'}},config);
let traces=[];['CHIRPS','IMERG','Q'].forEach(k=>{const a=D.index.filter(r=>r.response===k);traces.push({type:'scatter',mode:'lines+markers',name:k,x:a.map(r=>D.months[r.month-1]),y:a.map(r=>r.r_detrended),line:{color:colors[k]},customdata:a.map(r=>[r.n,r.q_BY_36]),hovertemplate:'%{x}: r=%{y:.3f}<br>n=%{customdata[0]} · q BY=%{customdata[1]:.5g}<extra>'+k+'</extra>'});const b=a.filter(r=>r.q_BY_36<=.05);traces.push({type:'scatter',mode:'markers',name:k+' BY 0,05',x:b.map(r=>D.months[r.month-1]),y:b.map(r=>r.r_detrended),marker:{symbol:'circle-open',size:14,color:colors[k],line:{width:2}},showlegend:false,hoverinfo:'skip'});});
Plotly.newPlot('indice_NOAA_contraste54',traces,{title:'Niño 3.4 NOAA PSL (ERSST v6), ell=0',yaxis:{range:[-1,1],title:'Pearson sin tendencia'},margin:{t:75,b:80,l:65,r:20},annotations:[{xref:'paper',yref:'paper',x:.5,y:-.16,text:'Círculo exterior: BY<=0,05; familia complementaria de 36 pruebas. No es ONI.',showarrow:false}]},config);
Plotly.newPlot('dependencia_y_escalas54',[{type:'heatmap',x:['Niño-SLP','Niño-Z500','SLP-Z500'],y:D.months,z:D.dependency,zmin:-1,zmax:1,colorscale:'RdBu',reversescale:true,colorbar:{x:.47,len:.85,thickness:10,title:'r'},hovertemplate:'%{y} · %{x}: r=%{z:.3f}<extra></extra>'},
{type:'bar',x:['CHIRPS','IMERG','Q','T'],y:D.semi_original,name:'Original',xaxis:'x2',yaxis:'y2'},
{type:'bar',x:['CHIRPS','IMERG','Q','T'],y:D.semi_anomaly,name:'Anomalía',xaxis:'x2',yaxis:'y2'}],
{title:'Dependencia regional y banda semianual de Fourier (N=73)',margin:{t:80,b:60,l:50,r:20},xaxis:{domain:[0,.38]},yaxis:{autorange:'reversed'},xaxis2:{domain:[.64,1],anchor:'y2'},yaxis2:{anchor:'x2',title:'Potencia semianual (%)'},barmode:'group',legend:{orientation:'h',y:-.17}},config);
}
if(document.readyState==='complete')init();else window.addEventListener('load',init);
})();</script>'''
body+=script.replace('__DATA__',json.dumps(graph_data,ensure_ascii=False,separators=(',',':')))
body+='<h4>Referencias</h4>'+''.join('<p>'+html.escape(label+'. '+cite)+' <a href="'+url+'">Fuente</a></p>' for label,cite,url in refs)
body+='<h4>Tablas del contraste NOAA (no ONI)</h4>'+idx.round(4).to_html(index=False,border=0)
body=body.replace('<table','<div style="overflow:auto"><table').replace('</table>','</table></div>')
(OUT/'contenido_5_4.html').write_text(body,encoding='utf-8')
hpath=DOCS/'informe_interactivo.html';h=hpath.read_text(encoding='utf-8');shutil.copy2(hpath,OUT/'respaldo_html_antes_5_4.html')
block='<!-- PUNTO_5_4_INICIO --><section class="panel" id="interpretacion-fisica-54">'+body+'</section><!-- PUNTO_5_4_FIN -->'
if '<!-- PUNTO_5_4_INICIO -->' in h:h=re.sub(r'<!-- PUNTO_5_4_INICIO -->.*?<!-- PUNTO_5_4_FIN -->',lambda _:block,h,flags=re.S)
else:h=h.replace('</main>',block+'</main>',1)
needle="else if(n===5&&i===2)mover(se,document.getElementById('robustez-patrones-53'));else pendiente"
new="else if(n===5&&i===2)mover(se,document.getElementById('robustez-patrones-53'));else if(n===5&&i===3)mover(se,document.getElementById('interpretacion-fisica-54'));else pendiente"
assert needle in h or "document.getElementById('interpretacion-fisica-54')" in h
h=h.replace(needle,new)
old="pendiente(grupo('guia-conclusiones','Conclusiones'),'Pendiente de síntesis final.');"
new="grupo('guia-conclusiones','Conclusiones').insertAdjacentHTML('beforeend',"+json.dumps(''.join('<p>'+html.escape(c)+'</p>' for c in conclusions),ensure_ascii=False)+");"
if old in h:h=h.replace(old,new)
hpath.write_text(h,encoding='utf-8');shutil.copy2(hpath,DOCS.parents[3]/'Informe_Hidrologia_interactivo.html')
(OUT/'conclusiones.json').write_text(json.dumps(conclusions,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'README.md').write_text('''# Punto 5.4

Reproducir con scripts 56_sintesis_fisica_5_4.py, 57_redactar_5_4.py y 58_integrar_5_4.py.
Índice complementario: NOAA PSL Niño 3.4 mensual ERSST v6, no ONI ni réplica independiente.
Familia separada de 36 pruebas contemporáneas: p AR(1) aproximados, BY.
Fourier se resume desde el JSON del informe publicado, sin recalcular ni afirmar significancia.
Datos, figuras, referencias y discusión están archivados en esta carpeta.
El esquema conceptual separa variables disponibles de mecanismos no medidos.
La revisión y defensa de la interpretación corresponde al grupo.
''',encoding='utf-8')
print('5.4: interpretación, cierre, figuras y HTML integrados.',flush=True)

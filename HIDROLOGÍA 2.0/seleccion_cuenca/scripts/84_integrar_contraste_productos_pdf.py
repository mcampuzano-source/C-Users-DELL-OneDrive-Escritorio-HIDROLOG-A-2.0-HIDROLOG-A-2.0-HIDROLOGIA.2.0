from pathlib import Path
import shutil,hashlib,json,io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import fitz
root=Path.cwd();base=next(root.glob('HIDROLOG*'))/'seleccion_cuenca';docs=base/'la_vieja/documentos';out=docs/'contraste_cambios_productos';out.mkdir(exist_ok=True)
current=root/'Informe_Hidrologia_actualizado_1_5.pdf';backup=out/'base_pdf_antes_contraste.pdf'
if not backup.exists():shutil.copy2(current,backup)
source=fitz.open(backup);assert len(source)==215,'La base debe ser el informe de 215 paginas.'
data=pd.read_csv(out/'datos_contraste.csv',parse_dates=['mes']).set_index('mes')
cases=[('2001-08-01','IMERG: cambio de \u00f3rbita de TRMM','lluvia','Agosto de 2001. NASA documenta un cambio orbital que puede afectar la continuidad de IMERG.','La diferencia ajustada frente a CHIRPS presenta una se\u00f1al d\u00e9bil: el cambio estimado es de 16,21 mm/mes con una ventana de dos a\u00f1os antes y despu\u00e9s (intervalo aproximado: -0,91 a 33,33), y de 17,81 con tres a\u00f1os (0,60 a 35,01). La conclusi\u00f3n depende de la ventana; no se confirma una causa t\u00e9cnica.'),('2014-06-01','IMERG: transici\u00f3n de TRMM a GPM','lluvia','Junio de 2014. Cambia el sat\u00e9lite de referencia de las estimaciones.','No se encontr\u00f3 un cambio persistente claro en la diferencia frente a CHIRPS. Los cambios estimados son 20,07 mm/mes (intervalo: -24,00 a 64,13) y 3,72 (-31,25 a 38,69), seg\u00fan la ventana de dos o tres a\u00f1os. Ambos intervalos incluyen cero; esto no demuestra ausencia de un efecto peque\u00f1o.'),('2020-01-01','ERA5-Land: cambio de interpolaci\u00f3n','temperatura','Enero de 2020. ECMWF incorpora el m\u00e9todo MIR para interpolar los datos atmosf\u00e9ricos de entrada.','La diferencia frente a la temperatura aproximada de CAMELS cambia -0,28 grados C (intervalo: -0,43 a -0,13) y -0,16 (-0,28 a -0,04), con ventanas de dos y tres a\u00f1os. Es una se\u00f1al exploratoria: la referencia es (Tmin + Tmax) / 2 y comparte origen ERA5. Tambi\u00e9n aparecen variaciones en otras fechas; no se demuestra causalidad.'),('2022-10-01','CHIRPS: disponibilidad de estaciones','lluvia','Septiembre-octubre de 2022. Cambian las estaciones disponibles para elaborar CHIRPS; no se confirm\u00f3 un cambio de versi\u00f3n o algoritmo.','La diferencia original IMERG - CHIRPS pasa de +29,00 mm en septiembre a -48,82 en octubre, +19,22 en noviembre y +17,44 en diciembre. Solo quedan tres meses desde octubre: no hay un per\u00edodo posterior suficiente para evaluar una ruptura persistente. La coincidencia temporal no identifica la causa del pico.')]
added=fitz.open()
for k,(date,title,kind,intro,conclusion) in enumerate(cases):
 cut=pd.Timestamp(date);start=cut-pd.DateOffset(months=36);end=min(cut+pd.DateOffset(months=36),pd.Timestamp('2022-12-01'));d=data.loc[start:end]
 fig,axs=plt.subplots(2,1,figsize=(8.4,5.1),sharex=True,layout='constrained')
 if kind=='lluvia':keys=['P_CHIRPS_mm','P_IMERG_poligono_mm'];labels=['CHIRPS','IMERG'];difference='diferencia_lluvia_mm_sin_ciclo';unit='mm/mes';axs[0].set_ylabel('Precipitacion (mm/mes)')
 else:keys=['Tmedia_ERA5_Land_C_sin_ciclo','Tmedia_estimada_sin_ciclo'];labels=['ERA5-Land','CAMELS: (Tmin + Tmax) / 2'];difference='diferencia_temperatura_C_sin_ciclo';unit='grados C';axs[0].set_ylabel('Temperatura sin ciclo\n(grados C)')
 for key,label,color in zip(keys,labels,['#1976a3','#c05a40']):axs[0].plot(d.index,d[key],label=label,color=color,lw=1.25)
 axs[1].plot(d.index,d[difference],color='#624399',lw=1.3);axs[1].axhline(0,color='#888',lw=.6)
 axs[1].set_ylabel(('IMERG - CHIRPS' if kind=='lluvia' else 'ERA5-Land - CAMELS')+'\nsin ciclo ('+unit+')');axs[1].set_xlabel('Mes');axs[0].legend(loc='upper left',fontsize=8)
 for ax in axs:ax.axvline(cut,color='#333',ls='--',lw=1.2);ax.grid(alpha=.18)
 fig.savefig(out/('caso_'+str(k+1)+'.pdf'));plt.close(fig)
 page=added.new_page(width=595.276,height=841.89)
 page.insert_text((48,52),'1.4. Calidad de las series: cambios documentados',fontname='tibo',fontsize=13)
 page.insert_text((48,82),title,fontname='tibo',fontsize=12)
 assert page.insert_textbox(fitz.Rect(48,99,548,170),intro,fontname='tiro',fontsize=11)>=0
 graph=fitz.open(out/('caso_'+str(k+1)+'.pdf'));page.show_pdf_page(fitz.Rect(40,166,555,508),graph,0);graph.close()
 caption='Contraste '+str(k+1)+'. La linea vertical marca '+cut.strftime('%Y-%m')+'. El panel inferior descuenta la diferencia habitual de cada mes calendario. Cero no significa igualdad entre fuentes. Se conservan los vacios.'
 assert page.insert_textbox(fitz.Rect(48,520,548,582),caption,fontname='tiro',fontsize=10)>=0
 assert page.insert_textbox(fitz.Rect(48,590,548,712),conclusion,fontname='tiro',fontsize=11)>=0
 note='Analisis exploratorio: mes calendario, tendencia y cambio de nivel; incertidumbre con dependencia temporal (HAC, 6 meses). No es una prueba causal ni evidencia de traslado de estacion. Las fuentes no son plenamente independientes.'
 assert page.insert_textbox(fitz.Rect(48,722,548,779),note,fontname='tiro',fontsize=9)>=0
 url='https://gpm.nasa.gov/resources/documents/imerg-v07-release-notes' if k<2 else ('https://confluence.ecmwf.int/pages/viewpage.action?pageId=501029136' if k==2 else 'https://data.chc.ucsb.edu/products/CHIRPS-2.0/diagnostics/list_of_stations_used/monthly/')
 page.insert_text((48,796),'Fuente tecnica: NASA' if k<2 else ('Fuente tecnica: ECMWF' if k==2 else 'Fuente tecnica: CHIRPS'),fontsize=9,fontname='tiro');page.insert_link({'kind':fitz.LINK_URI,'from':fitz.Rect(48,784,290,800),'uri':url})
added.save(out/'cuatro_casos_pdf.pdf')
result=fitz.open();result.insert_pdf(source,to_page=46);result.insert_pdf(added);result.insert_pdf(source,from_page=47)
# Conserva destinos y ajusta paginas de los marcadores del informe.
toc=source.get_toc()
for row in toc:
 if row[2]>=48:row[2]+=4
pos=next(i for i,row in enumerate(toc) if 'Climatolog' in row[1]);toc.insert(pos,[3,'Cambios documentados: contraste de productos',48]);result.set_toc(toc)
# Actualiza cifras del indice y numeracion impresa despues de la insercion.
index=result[1];changes=[]
for w in index.get_text('words'):
 if w[0]>520 and w[4].isdigit() and int(w[4])>=47:changes.append((fitz.Rect(w[:4]),str(int(w[4])+4)))
for rect,value in changes:index.add_redact_annot(rect,fill=(1,1,1))
index.apply_redactions(images=0,graphics=0)
for rect,value in changes:index.insert_textbox(fitz.Rect(rect.x0-1,rect.y0-1,rect.x1+6,rect.y1+5),value,fontname='tiro',fontsize=12,align=2)
for i in range(47,len(result)):
 page=result[i];rect=fitz.Rect(270,page.rect.height-40,330,page.rect.height-15);page.draw_rect(rect,color=None,fill=(1,1,1),overlay=True);page.insert_textbox(rect,str(i),fontsize=9,fontname='tiro',align=1)
final=out/'informe_con_contraste.pdf';result.save(final,garbage=1,deflate=False);result.close();added.close()
oldhash=hashlib.sha256(backup.read_bytes()).hexdigest();source.close()
targets=[current,root/'Informe_Hidrologia_actualizado.pdf',root/'Informe_Hidrologia_actualizado_5_4.pdf',root/'Informe_Hidrologia_integrado.pdf',root/'Informe_Hidrologia_continuo.pdf',docs/'informe_actualizado.pdf',docs/'informe_continuo.pdf',docs/'latex/informe_ordenado.pdf',docs/'apartado_3/informe_integrado.pdf']
updated=[]
for p in targets:
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==oldhash:shutil.copy2(final,p);updated.append(str(p.relative_to(root)))
check=fitz.open(current);assert len(check)==219;assert all(check[i].get_text().strip() for i in range(47,51));assert '1.5.' in check[51].get_text();check.close()
(out/'verificacion_pdf.json').write_text(json.dumps({'paginas_antes':215,'paginas_ahora':219,'insercion_fisica':[48,49,50,51],'archivos_actualizados':updated},indent=2),encoding='utf-8')
print('PDF actualizado: 219 paginas; cuatro casos en paginas fisicas 48-51.');print('Copias sincronizadas:',len(updated))



from pathlib import Path
import fitz,html,json,shutil,hashlib,tempfile,re
root=Path.cwd();base=next(root.glob('HIDROLOG*'))/'seleccion_cuenca';docs=base/'la_vieja/documentos';out=docs/'contraste_cambios_productos'
rows=[
['Meses incompletos de P y Q (19 meses)','Conteo de dias validos frente al calendario; retencion con 100 % de completitud.','Cobertura insuficiente para agregados mensuales completos.','Excluir agregados incompletos; sin imputacion.','Reduce la muestra y evita sumas parciales. Tratamiento aplicado.'],
['Extremos: noviembre 2010 y octubre 2022','Contraste cronologico de precipitaciones, Q y meses adyacentes.','Coherencia entre variables; episodios plausibles.','Retener observaciones.','Influyen en media, dispersion y modelos. La coherencia no certifica exactitud.'],
['Discrepancia CHIRPS: marzo 2015','Comparacion con IMERG, Q y meses vecinos.','Pico sin incremento comparable en las otras series.','Retener y marcar para revision.','Incertidumbre en extremos y comparacion de fuentes; causa pendiente.'],
['Q constante: 16-26 julio 2004','Deteccion de 11 dias consecutivos con 28,6 m3/s; busqueda de metadatos.','No se distingue entre estabilidad real, redondeo y procesamiento.','Retener, sin correccion numerica.','Limita la interpretacion diaria; contribuye al promedio mensual. Causa incierta.'],
['IMERG: agosto 2001','Metadatos del cambio orbital de TRMM; diferencia IMERG-CHIRPS ajustada por mes calendario, tendencia y cambio de nivel; ventanas de dos y tres anos.','Senal debil y dependiente de la ventana.','Retener y documentar el antecedente.','No se atribuye el salto al cambio orbital; homogeneidad temporal incierta.'],
['IMERG: junio 2014','Metadatos de la transicion TRMM-GPM y el mismo contraste temporal entre precipitaciones.','Sin cambio persistente claro en la diferencia entre fuentes.','Retener y documentar el antecedente.','No se confirma un efecto de la transicion; tampoco se descarta uno pequeno.'],
['ERA5-Land: enero 2020','Metadatos del cambio de interpolacion; contraste con temperatura aproximada CAMELS en ventanas de dos y tres anos.','Cambio estimado de la diferencia: -0,28 a -0,16 grados C. Referencia aproximada y de origen compartido.','Retener y senalar limitaciones.','Discrepancia exploratoria; no se demuestra que la interpolacion la cause.'],
['CHIRPS: septiembre-octubre 2022','Listas de estaciones disponibles y diferencias frente a IMERG.','Cambio en datos de entrada; diferencia temporal; solo tres meses de seguimiento desde octubre.','Retener y documentar; no clasificar como cambio de version.','Periodo insuficiente para evaluar una ruptura persistente; efecto no confirmado.']]
headers=['Hallazgo / periodo','Comprobacion realizada','Resultado','Decision','Efecto y estado']
(out/'registro_anomalias.json').write_text(json.dumps({'columnas':headers,'filas':rows},ensure_ascii=False,indent=2),encoding='utf-8')
def table(records):return '<table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in records)+'</tbody></table>'
start='<!-- REGISTRO_ANOMALIAS_1_4_INICIO -->';end='<!-- REGISTRO_ANOMALIAS_1_4_FIN -->'
block=start+'<section class="panel" id="registro-anomalias-1-4"><h3>1.4. Registro de anomal&iacute;as y decisiones</h3><p>Se registran cuatro antecedentes de cambios en productos o datos de entrada y cuatro hallazgos adicionales. Los casos inciertos se conservan: no se eliminan por ser at&iacute;picos.</p><div style="overflow-x:auto">'+table(rows)+'</div><p><b>Estado del control:</b> exclusi&oacute;n de meses incompletos aplicada; ninguna correcci&oacute;n num&eacute;rica por los dem&aacute;s hallazgos. Las causas no confirmadas permanecen registradas como incertidumbres.</p></section>'+end
backupdir=Path(tempfile.mkdtemp(prefix='hidrologia_antes_registro_'))
for i,p in enumerate([root/'Informe_Hidrologia_interactivo.html',docs/'informe_interactivo.html']):
 t=p.read_text(encoding='utf-8');(backupdir/(str(i)+p.name)).write_text(t,encoding='utf-8');clean=re.sub(re.escape(start)+'.*?'+re.escape(end),'',t,flags=re.S);anchor='<!-- CONTRASTE_CAMBIOS_PRODUCTOS_FIN -->';assert clean.count(anchor)==1
 new=clean.replace(anchor,anchor+block);assert new.replace(block,'',1)==clean;p.write_text(new,encoding='utf-8')
current=root/'Informe_Hidrologia_actualizado_1_5.pdf';backup=out/'base_pdf_antes_registro.pdf'
if not backup.exists():shutil.copy2(current,backup)
source=fitz.open(backup);assert len(source)==219
addition=fitz.open()
css='body{font-family:serif;font-size:10pt;line-height:1.24;color:#172738}h2{font-size:14pt}h3{font-size:12pt}table{border-collapse:collapse;width:100%;margin:12pt 0}th,td{border:0.5pt solid #9caab5;padding:7pt;vertical-align:top}th{background:#e8eff5}td{font-size:9.5pt}p{margin:10pt 0}'
for k in range(2):
 page=addition.new_page(width=595.276,height=841.89)
 lead='<h2>1.4. Registro de anomalias y decisiones</h2><h3>'+('Hallazgos de disponibilidad y comportamiento de las series' if k==0 else 'Cambios documentados en productos y datos de entrada')+'</h3>'
 text=lead+table(rows[k*4:k*4+4])+'<p><b>Estado:</b> se excluyen meses incompletos; no se corrigieron valores numericos por los demas casos. Las causas no confirmadas permanecen inciertas.</p>'
 scale=page.insert_htmlbox(fitz.Rect(40,40,555,790),text,css=css,scale_low=1);assert scale[0]>=0,'La tabla no cabe sin reducir la fuente.'
addition.save(out/'registro_anomalias_pdf.pdf')
result=fitz.open();result.insert_pdf(source,to_page=50);result.insert_pdf(addition);result.insert_pdf(source,from_page=51)
toc=source.get_toc()
for row in toc:
 if row[2]>=52:row[2]+=2
pos=next(i for i,row in enumerate(toc) if 'Climatolog' in row[1]);toc.insert(pos,[3,'Registro de anomalias y decisiones',52]);result.set_toc(toc)
index=result[1];changes=[]
for w in index.get_text('words'):
 if w[0]>520 and w[4].isdigit() and int(w[4])>=51:changes.append((fitz.Rect(w[:4]),str(int(w[4])+2)))
for rect,value in changes:index.add_redact_annot(rect,fill=(1,1,1))
index.apply_redactions(images=0,graphics=0)
for rect,value in changes:index.insert_textbox(fitz.Rect(rect.x0-1,rect.y0-1,rect.x1+6,rect.y1+5),value,fontname='tiro',fontsize=12,align=2)
for i in range(51,len(result)):
 page=result[i];rect=fitz.Rect(270,page.rect.height-40,330,page.rect.height-15);page.draw_rect(rect,color=None,fill=(1,1,1));page.insert_textbox(rect,str(i),fontname='tiro',fontsize=9,align=1)
final=out/'informe_con_registro.pdf';result.save(final,garbage=1,deflate=False);result.close();addition.close();source.close()
oldhash=hashlib.sha256(backup.read_bytes()).hexdigest();updated=[]
for p in [current,root/'Informe_Hidrologia_actualizado.pdf',root/'Informe_Hidrologia_actualizado_5_4.pdf',root/'Informe_Hidrologia_integrado.pdf',root/'Informe_Hidrologia_continuo.pdf',docs/'informe_actualizado.pdf',docs/'informe_continuo.pdf',docs/'latex/informe_ordenado.pdf',docs/'apartado_3/informe_integrado.pdf']:
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==oldhash:shutil.copy2(final,p);updated.append(p.name)
check=fitz.open(current);assert len(check)==221;assert '1.5.' in check[53].get_text();assert all(check[i].get_text().strip() for i in [51,52]);check[52].get_pixmap().save(Path(tempfile.gettempdir())/'registro_anomalias_pdf.png');check.close()
readme=root/'README_INFORMES.md';t=readme.read_text(encoding='utf-8').replace('Tiene 219','Tiene 221').replace('pagina 154','pagina 156').replace('p\u00e1gina 154','p\u00e1gina 156').replace('pagina 209','pagina 211').replace('p\u00e1gina 209','p\u00e1gina 211');t+='\nEl registro tecnico de ocho casos del punto 1.4 se presenta en las paginas fisicas 52-53. El script 85 reproduce esta incorporacion.\n';readme.write_text(t,encoding='utf-8')
(out/'verificacion_registro.json').write_text(json.dumps({'paginas':221,'filas':8,'paginas_fisicas_tabla':[52,53],'copias':updated},indent=2),encoding='utf-8')
print('HTML: ocho filas incorporadas. PDF: 221 paginas, tabla en 52-53. Copias:',len(updated))

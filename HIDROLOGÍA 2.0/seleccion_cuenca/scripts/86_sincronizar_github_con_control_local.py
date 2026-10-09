from pathlib import Path
import fitz,re,html,hashlib,shutil,json,tempfile
root=Path.cwd();base=next(root.glob('HIDROLOG*'))/'seleccion_cuenca';docs=base/'la_vieja/documentos';out=docs/'contraste_cambios_productos'
remote=root/'.git/lfs/objects/cb/bd/cbbdb7f2e7e9e7c7a9ddb9d32f30a7004df0b6d86f23d148907d30209bbc06fc'
assert hashlib.sha256(remote.read_bytes()).hexdigest()==remote.name
# Combina solo los dos bloques locales con el HTML actualizado.
local=(Path(tempfile.gettempdir())/'hidrologia_local_antes_sync_34d523e.html').read_text(encoding='utf-8')
blocks=[]
for name in ['CONTRASTE_CAMBIOS_PRODUCTOS','REGISTRO_ANOMALIAS_1_4']:
 pattern=r'<!-- '+name+r'_INICIO -->.*?<!-- '+name+r'_FIN -->'
 m=re.search(pattern,local,re.S);assert m;blocks.append(m.group(0))
current=docs/'informe_interactivo.html';remote_html=current.read_text(encoding='utf-8');assert remote_html.count('<!-- CONTROL_FALTANTES_FIN -->')==1
# Copia de seguridad de la version HTML de GitHub para reproducir esta integracion.
htmlbase=out/'base_html_github_34d523e.html'
if not htmlbase.exists():htmlbase.write_text(remote_html,encoding='utf-8')
merged=htmlbase.read_text(encoding='utf-8').replace('<!-- CONTROL_FALTANTES_FIN -->','<!-- CONTROL_FALTANTES_FIN -->'+''.join(blocks),1)
for p in [current,root/'Informe_Hidrologia_interactivo.html']:p.write_text(merged,encoding='utf-8')
source=fitz.open(remote);assert len(source)==480
before=next(i for i in range(4,len(source)) if '1.5. Climatolog' in source[i].get_text());assert before==47
addition=fitz.open()
for name in ['cuatro_casos_pdf.pdf','registro_anomalias_pdf.pdf']:
 d=fitz.open(out/name);addition.insert_pdf(d);d.close()
assert len(addition)==6
result=fitz.open();result.insert_pdf(source,to_page=before-1);result.insert_pdf(addition);result.insert_pdf(source,from_page=before)
toc=source.get_toc()
for item in toc:
 if item[2]>=before+1:item[2]+=6
pos=next(i for i,row in enumerate(toc) if 'Climatolog' in row[1]);toc[pos:pos]=[[3,'Cambios documentados: contraste de productos',48],[3,'Registro de anomalias y decisiones',52]];result.set_toc(toc)
idx=result[1];changes=[]
for w in idx.get_text('words'):
 if w[0]>520 and w[4].isdigit() and int(w[4])>=before:changes.append((fitz.Rect(w[:4]),str(int(w[4])+6)))
for rect,value in changes:idx.add_redact_annot(rect,fill=(1,1,1))
idx.apply_redactions(images=0,graphics=0)
for rect,value in changes:idx.insert_textbox(fitz.Rect(rect.x0-1,rect.y0-1,rect.x1+6,rect.y1+5),value,fontname='tiro',fontsize=12,align=2)
for i in range(before,len(result)):
 page=result[i];rect=fitz.Rect(270,page.rect.height-40,330,page.rect.height-15);page.draw_rect(rect,color=None,fill=(1,1,1));page.insert_textbox(rect,str(i),fontname='tiro',fontsize=9,align=1)
final=out/'informe_sincronizado_34d523e.pdf';result.save(final,garbage=1,deflate=False);result.close();addition.close()
check=fitz.open(final);assert len(check)==486
# Comprueba el texto cientifico de cada pagina original, ignorando los pies numericos.
def words(p):return [w[4] for w in p.get_text('words') if 35<w[1] and w[3]<p.rect.height-42]
for i in range(2,len(source)):
 target=i if i<before else i+6
 assert words(source[i])==words(check[target]),('Contenido alterado',i+1)
assert check[0].get_text()==source[0].get_text();check.close();source.close()
targets=[root/'Informe_Hidrologia_actualizado_1_5.pdf',root/'Informe_Hidrologia_actualizado.pdf',root/'Informe_Hidrologia_actualizado_5_4.pdf',root/'Informe_Hidrologia_integrado.pdf',docs/'informe_actualizado.pdf',docs/'informe_actualizado_1_5.pdf',docs/'latex/informe_ordenado.pdf']
for p in targets:shutil.copy2(final,p)
readme=root/'README_INFORMES.md';t=readme.read_text(encoding='utf-8');t=re.sub(r'Tiene \d+ p', 'Tiene 486 p',t,count=1)
t+='\nSincronizacion 34d523e: se descargaron los PDF completos mediante Git LFS (480 paginas) y se conservaron los seis folios locales del control 1.4. La version combinada tiene 486 paginas, incorpora las interpretaciones individuales recibidas y mantiene los cuatro contrastes y el registro de ocho casos. El script 86 reproduce esta integracion. Las versiones historicas se conservan.\n'
readme.write_text(t,encoding='utf-8')
(out/'verificacion_sincronizacion_34d523e.json').write_text(json.dumps({'commit':'34d523e','paginas_remotas':480,'paginas_combinadas':486,'paginas_originales_verificadas':478,'portada_preservada':True,'copias_pdf':len(targets)},indent=2),encoding='utf-8')
print('Sincronizacion verificada: 486 paginas; contenido de las paginas originales conservado; HTML remoto y dos bloques locales combinados.')

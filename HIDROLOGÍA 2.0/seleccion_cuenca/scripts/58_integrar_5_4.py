"""Integra interpretación y cierre en el informe con 5.3 verificado."""
from pathlib import Path
import pymupdf,shutil,json,hashlib
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'apartado_5_4'
backup=OUT/'base_antes_5_4.pdf'
if not backup.exists():shutil.copy2(ROOT/'Informe_Hidrologia_actualizado_5_3.pdf',backup)
base=pymupdf.open(backup);toc=base.get_toc();source=pymupdf.open(OUT/'punto_5_4.pdf');atlas=pymupdf.open()
for i,p in enumerate(source):
    if p.rect.width>p.rect.height:
        page=atlas.new_page(width=p.rect.width,height=p.rect.height+58);page.show_pdf_page(p.rect,source,i)
    else:atlas.insert_pdf(source,from_page=i,to_page=i)
atlas.set_toc(source.get_toc());source.close()
pos=next(row[2]-1 for row in toc if row[1]=='Interpretación física e integración')
p=base[pos];blocks=p.get_text('blocks');proc=next(b for b in blocks if b[4].startswith('Procedencia, alcance y reproducibilidad'))
out=pymupdf.open();out.insert_pdf(base,to_page=pos-1);out.insert_pdf(atlas)
# Move the remaining provenance to the top of its page; remove obsolete pending 5.4/conclusions.
clip=pymupdf.Rect(0,proc[1]-8,p.rect.width,p.rect.height-43)
page=out.new_page(width=p.rect.width,height=p.rect.height)
page.show_pdf_page(pymupdf.Rect(0,45,p.rect.width,45+clip.height),base,pos,clip=clip)
out.insert_pdf(base,from_page=pos+1)
for row in toc:
    if row[2]>pos and row[1]!='Interpretación física e integración':row[2]+=len(atlas)
toc += [[3,title,page+pos] for _,title,page in atlas.get_toc()]
out.set_toc(toc)
for i in range(pos,len(out)):
    p=out[i];y=p.rect.height;p.draw_rect(pymupdf.Rect(0,y-42,p.rect.width,y),color=None,fill=(1,1,1))
    p.insert_textbox(pymupdf.Rect(0,y-35,p.rect.width,y-15),str(i),fontsize=10,align=1)
index=out[1];index.add_redact_annot(pymupdf.Rect(35,35,index.rect.width-35,index.rect.height-43),fill=(1,1,1));index.apply_redactions()
for link in index.get_links():index.delete_link(link)
index.insert_text((56,66),'Índice',fontsize=18);y=98;section=0;sub=0
for level,title,page in toc:
    if level>2:continue
    if level==1:section+=1;sub=0;y+=7;prefix=f'{section}. '
    else:sub+=1;prefix=f'{section}.{sub}. '
    x=56 if level==1 else 68;index.insert_text((x,y),prefix+title,fontsize=10 if level==1 else 9)
    index.insert_text((534,y),str(page-1),fontsize=9);index.insert_link({'kind':pymupdf.LINK_GOTO,'from':pymupdf.Rect(x,y-11,553,y+4),'page':page-1});y+=19
meta=base.metadata;meta['subject']='Hidrología: puntos 1-5, interpretación física y síntesis';out.set_metadata(meta)
temp=OUT/'integrado_nuevo.pdf';out.save(temp,garbage=4,deflate=True);out.close();base.close();n_atlas=len(atlas);atlas.close()
target=ROOT/'Informe_Hidrologia_actualizado_5_4.pdf';shutil.copy2(temp,target)
for dest in [ROOT/'Informe_Hidrologia_actualizado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf',DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf']:
    try:shutil.copy2(target,dest)
    except PermissionError:print('Archivo abierto: consultar versión 5_4',dest)
check=pymupdf.open(target)
assert 'Integrantes' in check[0].get_text()
assert '5.4. Interpretación' in check[pos].get_text()
assert any('Cierre de la caracterización' in p.get_text() for p in check)
assert any('5.3. Robustez' in p.get_text() for p in check)
assert 'Pendiente de síntesis' not in check[-2].get_text()
for i in [0,1,*range(pos,pos+n_atlas),pos+n_atlas]:check[i].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(OUT/f'qa_integrado_{i+1}.png')
result={'pages':len(check),'start_5_4':pos+1,'pages_5_4':n_atlas,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'remaining_group_actions':['Revisar interpretación y defender resultados','Completar declaración final de IA y contribuciones personales','Revisar coherencia editorial global y referencias de versiones históricas']}
(OUT/'integracion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)

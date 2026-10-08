"""Conserva puntos 1-3 recientes y publica los puntos 4-5 completos."""
from pathlib import Path
import pymupdf as fitz
import shutil, json, hashlib
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
ROOT=DOCS.parents[3]
OUT=DOCS/'revision_publicacion'
OUT.mkdir(exist_ok=True)
published=DOCS/'latex/informe_ordenado.pdf'
backup=OUT/'base_latex_60_paginas.pdf'
if not backup.exists(): shutil.copy2(published,backup)
a=fitz.open(backup)
b=fitz.open(ROOT/'Informe_Hidrologia_actualizado_5_4.pdf')
ta,tb=a.get_toc(),b.get_toc()
cut_a=next(p-1 for l,t,p in ta if l==1 and 'Fourier' in t)
cut_b=next(p-1 for l,t,p in tb if l==1 and 'Fourier' in t)
out=fitz.open()
out.insert_pdf(a,to_page=cut_a-1)
out.insert_pdf(b,from_page=cut_b)
toc=[r for r in ta if r[2]<=cut_a]+[[l,t,p+cut_a-cut_b] for l,t,p in tb if p>cut_b]
out.set_toc(toc)
index=out[1]
index.add_redact_annot(fitz.Rect(35,35,index.rect.width-35,index.rect.height-43),fill=(1,1,1))
index.apply_redactions()
for link in index.get_links(): index.delete_link(link)
index.insert_text((56,66),'Índice',fontsize=18)
y=98; section=0; sub=0
for level,title,page in toc:
    if level>2: continue
    if level==1: section+=1; sub=0; y+=7; prefix=f'{section}. '
    else: sub+=1; prefix=f'{section}.{sub}. '
    x=56 if level==1 else 68
    index.insert_text((x,y),prefix+title,fontsize=10 if level==1 else 9)
    index.insert_text((534,y),str(page-1),fontsize=9)
    index.insert_link({'kind':fitz.LINK_GOTO,'from':fitz.Rect(x,y-11,553,y+4),'page':page-1})
    y+=19
for i in range(cut_a,len(out)):
    page=out[i]; h=page.rect.height
    page.draw_rect(fitz.Rect(0,h-42,page.rect.width,h),color=None,fill=(1,1,1))
    page.insert_textbox(fitz.Rect(0,h-35,page.rect.width,h-15),str(i),fontsize=10,align=1)
out.set_metadata(b.metadata)
temp=OUT/'informe_sincronizado.pdf'
out.save(temp,garbage=4,deflate=True)
out.close(); a.close(); b.close()
check=fitz.open(temp)
point5=next(i for i,r in enumerate(toc) if r[0]==1 and 'clima global' in r[1])
starts={f'5.{i+1}':r[2] for i,r in enumerate([r for r in toc[point5+1:] if r[0]==2])}
assert len(starts)==4
assert len(check)==151
assert 'Integrantes' in check[0].get_text()
check[1].get_pixmap().save(OUT/'indice.png')
for i in [25,27,starts['5.3']-1,starts['5.4']-1]: check[i].get_pixmap().save(OUT/f'pagina_{i+1}.png')
check.close()
for dest in [published,ROOT/'Informe_Hidrologia_actualizado_5_4.pdf',ROOT/'Informe_Hidrologia_actualizado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf',DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf']:
    shutil.copy2(temp,dest)
result={'pages':151,'starts':starts,'sha256':hashlib.sha256(temp.read_bytes()).hexdigest(),'retained_recent_points_1_3':True,'publication_path':str(published)}
(OUT/'verificacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))

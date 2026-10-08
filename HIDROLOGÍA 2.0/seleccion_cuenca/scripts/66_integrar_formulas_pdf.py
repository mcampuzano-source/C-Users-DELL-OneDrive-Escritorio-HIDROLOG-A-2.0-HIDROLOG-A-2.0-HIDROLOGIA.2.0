"""Integra matemática tipográfica y preserva visualmente cada página del punto 1."""
from pathlib import Path
import json,shutil,hashlib
import pymupdf as f
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_formulas'
base=f.open(OUT/'base_antes.pdf');native=f.open(DOCS/'latex/informe_ordenado.pdf');blocks=f.open(OUT/'bloques.pdf')
specs=json.loads((OUT/'reemplazos.json').read_text(encoding='utf-8'))
catalog=json.loads((OUT/'catalogo.json').read_text(encoding='utf-8'))
assert len(blocks)==len(specs)+len(catalog)
def ink(page):
    rects=[f.Rect(b[:4]) for b in page.get_text('blocks',flags=0)]
    r=rects[0]
    for v in rects[1:]:r|=v
    return f.Rect(0,max(0,r.y0-3),page.rect.width,r.y1+3)
for i,c in enumerate(catalog):
    p=blocks[len(specs)+i];r=ink(p)
    one=f.open();q=one.new_page(width=p.rect.width,height=r.height)
    q.show_pdf_page(q.rect,blocks,len(specs)+i,clip=r)
    svg=q.get_svg_image(text_as_path=True)
    (OUT/('ecuacion_'+c['number'].replace('.','_')+'.svg')).write_text(svg,encoding='utf-8')
    one.close()
btoc=base.get_toc();ntoc=native.get_toc()
b2=next(p-1 for l,t,p in btoc if l==1 and 'Relaciones entre series' in t)
b3=next(p-1 for l,t,p in btoc if l==1 and 'Tendencias hidroclim' in t)
n2=next(p-1 for l,t,p in ntoc if l==1 and 'Relaciones entre series' in t)
n3=next(p-1 for l,t,p in ntoc if l==1 and 'Tendencias hidroclim' in t)
out=f.open();out.insert_pdf(base,to_page=b2-1);out.insert_pdf(native,from_page=n2,to_page=n3-1)
mapping={i:i for i in range(b2)}
placements=[]
for bi in range(b3,len(base)):
    page=base[bi];items=[(j,s) for j,s in enumerate(specs) if s['page']==bi+1]
    mapping[bi]=len(out)
    if not items:out.insert_pdf(base,from_page=bi,to_page=bi);continue
    width,height=page.rect.width,page.rect.height;bottom=height-47
    target=out.new_page(width=width,height=height);y=0
    intervals=[(b[1],b[3]) for b in page.get_text('blocks',flags=0) if b[1]<bottom]
    atomic={45:[(664,770)],46:[(120,360),(510,658)],50:[(660,789)],56:[(150,325)],90:[(519,663),(672,778)]}.get(bi+1,[])
    intervals+=atomic
    def new():
        global target,y
        target=out.new_page(width=width,height=height);y=55
    def source_band(a,b):
        global y
        while b-a>0.05:
            available=bottom-y
            if available<20:new();continue
            end=min(b,a+available)
            if end<b-.1:
                candidates=[v[1]+2 for v in intervals if a+15<v[1]+2<=end and not any(lo<v[1]+2<hi for lo,hi in intervals)]
                if not candidates:new();continue
                end=max(candidates)
            clip=f.Rect(0,a,width,end)
            target.show_pdf_page(f.Rect(0,y,width,y+clip.height),base,bi,clip=clip)
            placements.append({'old_page':bi,'old_y0':a,'old_y1':end,'new_page':len(out)-1,'new_y':y})
            y+=clip.height;a=end
            if a<b-.1:new()
    previous=0
    for j,s in sorted(items,key=lambda t:t[1]['rect'][1]):
        r=f.Rect(s['rect']);start=max(previous,r.y0-1)
        source_band(previous,start)
        clip=ink(blocks[j]);need=clip.height+8
        if need>bottom-55:raise RuntimeError('Bloque matemático demasiado alto')
        if y+need>bottom:new()
        target.show_pdf_page(f.Rect(56,y,56+clip.width,y+clip.height),blocks,j,clip=clip)
        placements.append({'old_page':bi,'old_y0':r.y0,'old_y1':r.y1,'new_page':len(out)-1,'new_y':y})
        y+=need;previous=r.y1+1
    # No se añade espacio blanco al final de la última página de continuación.
    last_ink=max([v[1] for v in intervals if v[1]<bottom]+[previous])
    source_band(previous,min(bottom,last_ink+10))
# Marcadores: conserva los puntos 1 y 3-5; usa las posiciones nuevas de 2.
toc=[r for r in btoc if r[2]<=b2]
toc += [[l,t,p-n2+b2] for l,t,p in ntoc if n2<p<=n3]
def translated(oldpage,title):
    # Busca la línea del título para detectar si pasó a una continuación.
    lines=[b for b in base[oldpage].get_text('blocks',flags=0) if title in b[4].replace('\n',' ')]
    if lines:
        yy=lines[0][1]
        hit=next((v for v in placements if v['old_page']==oldpage and v['old_y0']<=yy<=v['old_y1']),None)
        if hit:return hit['new_page']+1
    return mapping[oldpage]+1
toc += [[l,t,translated(p-1,t)] for l,t,p in btoc if p>b3]
out.set_toc(toc)
for i in range(b2,len(out)):
    p=out[i];h=p.rect.height
    p.add_redact_annot(f.Rect(0,h-42,p.rect.width,h),fill=(1,1,1));p.apply_redactions(images=0,graphics=0)
    p.insert_textbox(f.Rect(0,h-35,p.rect.width,h-15),str(i),fontsize=10,align=1)
index=out[1]
index.add_redact_annot(f.Rect(35,35,index.rect.width-35,index.rect.height-43),fill=(1,1,1));index.apply_redactions(images=0,graphics=0)
for link in index.get_links():index.delete_link(link)
index.insert_text((56,66),'Índice',fontsize=18);yy=98;section=0;sub=0
for level,title,pn in toc:
    if level>2:continue
    if level==1:section+=1;sub=0;yy+=7;label=f'{section}. '
    else:sub+=1;label=f'{section}.{sub}. '
    xx=56 if level==1 else 68
    index.insert_text((xx,yy),label+title,fontsize=10 if level==1 else 9)
    index.insert_text((534,yy),str(pn-1),fontsize=9)
    index.insert_link({'kind':f.LINK_GOTO,'from':f.Rect(xx,yy-11,553,yy+4),'page':pn-1});yy+=19
out.set_metadata(base.metadata)
temp=OUT/'informe_formulas.pdf';out.save(temp,garbage=4,deflate=True);out.close()
check=f.open(temp)
# Comprobación píxel por píxel de portada y todas las páginas del punto 1.
protected=[0,*range(2,b2)]
for i in protected:
    a=base[i].get_pixmap();b=check[i].get_pixmap()
    assert a.samples==b.samples,('Punto 1 modificado',i+1)
qa=sorted(set([1,b2,*[v['new_page'] for v in placements],*[p-1 for l,t,p in toc if l<=2 and 'Modelos estad' in t]]))
for i in qa:check[i].get_pixmap().save(OUT/f'qa_{i+1}.png')
report={'pages':len(check),'equations':len(catalog),'protected_pages_identical':[i+1 for i in protected],'toc':toc,'sha256':hashlib.sha256(temp.read_bytes()).hexdigest(),'qa_pages':[i+1 for i in qa]}
(OUT/'verificacion_pdf.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
check.close();native.close();base.close();blocks.close()
for dest in [ROOT/'Informe_Hidrologia_actualizado_5_4.pdf',ROOT/'Informe_Hidrologia_actualizado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf',DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf',DOCS/'latex/informe_ordenado.pdf']:
    shutil.copy2(temp,dest)
print(json.dumps({k:v for k,v in report.items() if k not in ['toc']},ensure_ascii=True))

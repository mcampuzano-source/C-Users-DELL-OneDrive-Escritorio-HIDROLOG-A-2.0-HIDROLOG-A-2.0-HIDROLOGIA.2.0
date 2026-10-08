"""Unifica tablas y tipografía de 2-5 manteniendo páginas del punto 1 idénticas."""
from pathlib import Path
import json,re,html,shutil,hashlib
import numpy as np
import pymupdf as f
import matplotlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_tablas'
base=f.open(OUT/'base_antes.pdf');toc=base.get_toc();tables=json.loads((OUT/'tablas.json').read_text(encoding='utf-8'))
start=2
fontdir=OUT/'fuentes_originales'
for name,file in [('Hydro','lmroman10-regular.ttf'),('HydroBold','lmroman10-bold.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
items=[dict(t,kind='table') for t in tables]
atlas={p-1 for l,t,p in toc if l==3}
audit=[]
fontcache={};visibility=[];rastercache={}
cachepath=OUT/'visibilidad_cache.json';linecache=json.loads(cachepath.read_text()) if cachepath.exists() else {}
if not (OUT/'cache_fuentes_estandar_v2.ok').exists():
    for pi in range(start,len(base)):
        for block in base[pi].get_text('rawdict',flags=0)['blocks']:
            if 'lines' in block and any('Helvetica' in s['font'] or 'Times' in s['font'] for line in block['lines'] for s in line['spans']):
                linecache.pop(str(pi)+'|'+str(block['bbox']),None)
    (OUT/'cache_fuentes_estandar_v2.ok').write_text('Fuentes PDF estándar sin buffer usan fuente nativa de MuPDF.',encoding='utf-8')
def visible_lines(page,block):
    """Comprueba la tinta de los glifos para excluir texto oculto por recortes PDF."""
    cachekey=str(page.number)+'|'+str(block['bbox'])
    if cachekey in linecache:
        visibility.extend(1.0 if v else 0.0 for v in linecache[cachekey])
        return [line for line,accepted in zip(block['lines'],linecache[cachekey]) if accepted]
    probe=f.open();dest=probe.new_page(width=page.rect.width,height=page.rect.height);shape=dest.new_shape()
    resources={re.sub(r'[^a-z0-9]','',v[3].split('+')[-1].lower()):v[0] for v in page.get_fonts(full=True)}
    installed={};rendered=0
    for line in block['lines']:
        for span in line['spans']:
            name=span['font'];key=re.sub(r'[^a-z0-9]','',name.lower())
            if name not in installed:
                xref=resources.get(key)
                try:
                    alias='F'+str(len(installed))
                    if xref:
                        if xref not in fontcache:fontcache[xref]=base.extract_font(xref)[3]
                        if fontcache[xref]:dest.insert_font(fontname=alias,fontbuffer=fontcache[xref])
                        else:
                            family=name.lower()
                            if 'times' in family:alias='tibo' if 'bold' in family else 'tiro'
                            else:alias='hebo' if 'bold' in family else 'heit' if 'oblique' in family else 'helv'
                            dest.insert_font(fontname=alias)
                    else:
                        alias='hebo' if 'bold' in name.lower() else 'helv'
                        dest.insert_font(fontname=alias)
                    installed[name]=alias
                except Exception:installed[name]=None
            if installed[name] is None:continue
            for char in span['chars']:
                try:shape.insert_text(char['origin'],char['c'],fontname=installed[name],fontsize=span['size']);rendered+=1
                except Exception:pass
    shape.commit()
    if page.number not in rastercache:
        original=page.get_pixmap(matrix=f.Matrix(2,2),colorspace=f.csGRAY)
        rastercache[page.number]=np.frombuffer(original.samples,dtype=np.uint8).reshape(original.height,original.width)
    rectangle=f.Rect(block['bbox'])&page.rect
    expected=dest.get_pixmap(matrix=f.Matrix(2,2),clip=rectangle,colorspace=f.csGRAY)
    predicted=np.frombuffer(expected.samples,dtype=np.uint8).reshape(expected.height,expected.width)
    original=rastercache[page.number]
    result=[];decisions=[]
    for line in block['lines']:
        rect=f.Rect(line['bbox'])&page.rect
        if rect.is_empty:decisions.append(False);continue
        rr=rect*2;rr=rr.irect;x0,y0,x1,y1=rr
        aa=original[y0:y1,x0:x1].reshape(-1)
        bb=predicted[y0-expected.y:y1-expected.y,x0-expected.x:x1-expected.x].reshape(-1)
        if len(aa)!=len(bb):decisions.append(False);continue
        mask=bb<180
        score=float((aa[mask]<215).mean()) if mask.any() else 0
        visibility.append(score)
        decisions.append(score>=.55)
        if score>=.55:result.append(line)
    linecache[cachekey]=decisions;cachepath.write_text(json.dumps(linecache),encoding='utf-8')
    probe.close();return result
for pi in range(start,len(base)):
    page=base[pi]
    if pi in atlas or page.rect.width>page.rect.height:continue
    tagareas=[f.Rect(0,r.y0-18,page.rect.width,r.y1+18) for r in page.search_for('(') if False]
    text=page.get_text(flags=0)
    for number in re.findall(r'\([1-5]\.\d+\)',text):
        tagareas += [f.Rect(0,r.y0-23,page.rect.width,r.y1+23) for r in page.search_for(number)]
    reserved=[f.Rect(t['rect']) for t in tables if t['page']==pi+1]+tagareas
    for block in page.get_text('rawdict',flags=0)['blocks']:
        if 'lines' not in block:continue
        rect=f.Rect(block['bbox']);spans=[s for line in block['lines'] for s in line['spans']]
        for span in spans:span['text']=''.join(c['c'] for c in span['chars'])
        raw='\n'.join(''.join(s['text'] for s in line['spans']) for line in block['lines'])
        if rect.y0<35 or rect.y1>795 or rect.x0>85:continue
        center=(rect.y0+rect.y1)/2
        if any(r.y0-1<=center<=r.y1+1 for r in reserved):continue
        lines=visible_lines(page,block)
        if not lines:continue
        rect=f.Rect(lines[0]['bbox'])
        for line in lines[1:]:rect|=f.Rect(line['bbox'])
        spans=[s for line in lines for s in line['spans']]
        raw='\n'.join(''.join(s['text'] for s in line['spans']) for line in lines)
        if any(re.match(r'CM(?:MI|SY|EX)',s['font']) for s in spans):continue
        maximum=max(s['size'] for s in spans);bold=any('Bold' in s['font'] for s in spans)
        clean=raw.replace('ﬁ','fi').replace('ﬂ','fl').replace('ﬀ','ff')
        clean=re.sub(r'(\w)-\n(\w)',r'\1\2',clean);clean=' '.join(clean.split())
        if not clean or len(clean)<5:continue
        if re.match(r'^[1-5]\.\s',clean) and maximum>=13:kind='title';size=16;leading=20
        elif re.match(r'^[1-5]\.\d+\.',clean):kind='subtitle';size=13;leading=17
        elif bold and len(clean)<180 and rect.height<40:kind='heading';size=11.5;leading=15
        elif (rect.width>=260 or (rect.width>=100 and rect.height<30 and len(clean)>15)) and maximum>=5:kind='caption' if clean.startswith('Figura ') else 'body';size=9.5 if kind=='caption' else 10.5;leading=13.5
        else:continue
        style=ParagraphStyle(kind,fontName='HydroBold' if kind in ['title','subtitle','heading'] else 'Hydro',fontSize=size,leading=leading)
        obj=Paragraph(html.escape(clean),style);w,h=obj.wrap(483,2000)
        if h>700:raise RuntimeError(('Párrafo demasiado largo',pi+1))
        name=f'texto_{len(audit)+1}.pdf';c=canvas.Canvas(str(OUT/name),pagesize=(483,h+2));obj.drawOn(c,0,1);c.save()
        items.append({'page':pi+1,'rect':list(rect),'files':[name],'heights':[h+2],'kind':kind,'text':clean})
        audit.append({'page':pi+1,'kind':kind,'size':size,'font':style.fontName,'text':clean[:100]})
(OUT/'tipografia.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'elementos.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'visibilidad.json').write_text(json.dumps({'lines_checked':len(visibility),'hidden_lines_excluded':sum(v<.55 for v in visibility),'accepted_lines':sum(v>=.55 for v in visibility)},indent=2),encoding='utf-8')
out=f.open();out.insert_pdf(base,to_page=start-1);mapping={i:i for i in range(start)};placements=[]
assets={name:f.open(stream=(OUT/name).read_bytes(),filetype='pdf') for item in items for name in item['files']}
for pi in range(start,len(base)):
    page=base[pi];targets=sorted([i for i in items if i['page']==pi+1],key=lambda i:i['rect'][1]);mapping[pi]=len(out)
    if not targets:out.insert_pdf(base,from_page=pi,to_page=pi);continue
    width,height=page.rect.width,page.rect.height;bottom=height-47
    dest=out.new_page(width=width,height=height);y=0;old=0
    intervals=[(b[1],b[3]) for b in page.get_text('blocks',flags=0) if b[1]<bottom]
    for image in page.get_image_info():
        r=f.Rect(image['bbox'])
        if 0<=r.y0<r.y1<=bottom:intervals.append((r.y0-8,r.y1+18))
    def new():
        global dest,y
        dest=out.new_page(width=width,height=height);y=55
    def band(a,b):
        global y
        while b-a>.1:
            room=bottom-y;end=min(b,a+room)
            if end<b-.1:
                choices=[hi+1 for lo,hi in intervals if a+5<hi+1<=end and not any(lo2<hi+1<hi2 for lo2,hi2 in intervals)]
                if not choices:
                    if y==55 and a<55:a=55;continue
                    new();continue
                end=max(choices)
            if end<=a:new();continue
            rect=f.Rect(0,a,width,end);dest.show_pdf_page(f.Rect(0,y,width,y+rect.height),base,pi,clip=rect)
            placements.append({'old_page':pi,'old_y0':a,'old_y1':end,'new_page':len(out)-1,'new_y':y});y+=rect.height;a=end
            if a<b-.1:new()
    for k,item in enumerate(targets):
        r=f.Rect(item['rect']);a=max(old,r.y0-1)
        band(old,a)
        for part,name in enumerate(item['files']):
            doc=assets[name];need=doc[0].rect.height+7
            if item['kind'] in ['title','subtitle','heading'] and part==0:reserve=45
            else:reserve=0
            if y+need+reserve>bottom:new()
            dest.show_pdf_page(f.Rect(56,y,539,y+doc[0].rect.height),doc,0)
            placements.append({'old_page':pi,'old_y0':r.y0,'old_y1':r.y1,'new_page':len(out)-1,'new_y':y,'kind':item['kind']})
            y+=need
        old=max(old,r.y1+1)
    last=max([hi for lo,hi in intervals if hi<bottom]+[old]);band(old,min(bottom,last+6))
def translated(pn,title):
    oldpage=pn-1
    blocks=[b for b in base[oldpage].get_text('blocks',flags=0) if title in b[4].replace('\n',' ')]
    if blocks:
        yy=(blocks[0][1]+blocks[0][3])/2
        hit=next((p for p in placements if p['old_page']==oldpage and p['old_y0']<=yy<=p['old_y1']),None)
        if hit:return hit['new_page']+1
    return mapping[oldpage]+1
newtoc=[[l,t,translated(p,t)] for l,t,p in toc];out.set_toc(newtoc)
for i in range(start,len(out)):
    p=out[i];h=p.rect.height;p.add_redact_annot(f.Rect(0,h-42,p.rect.width,h),fill=(1,1,1));p.apply_redactions(images=0,graphics=0)
    p.insert_font(fontname='Hydro',fontfile=str(fontdir/'lmroman10-regular.ttf'))
    p.insert_textbox(f.Rect(0,h-35,p.rect.width,h-15),str(i),fontsize=9,fontname='Hydro',align=1)
idx=out[1];idx.add_redact_annot(f.Rect(35,35,idx.rect.width-35,idx.rect.height-43),fill=(1,1,1));idx.apply_redactions(images=0,graphics=0)
for link in idx.get_links():idx.delete_link(link)
idx.insert_font(fontname='Hydro',fontfile=str(fontdir/'lmroman10-regular.ttf'));idx.insert_font(fontname='HydroBold',fontfile=str(fontdir/'lmroman10-bold.ttf'))
idx.insert_text((56,66),'Índice',fontname='HydroBold',fontsize=16);yy=98;section=0;sub=0
for level,title,pn in newtoc:
    if level>2:continue
    if level==1:section+=1;sub=0;yy+=7;label=f'{section}. '
    else:sub+=1;label=f'{section}.{sub}. '
    xx=56 if level==1 else 68;idx.insert_text((xx,yy),label+title,fontname='HydroBold' if level==1 else 'Hydro',fontsize=9 if level==1 else 8)
    idx.insert_text((534,yy),str(pn-1),fontname='Hydro',fontsize=8);idx.insert_link({'kind':f.LINK_GOTO,'from':f.Rect(xx,yy-11,553,yy+4),'page':pn-1});yy+=19
out.set_metadata(base.metadata);temp=OUT/'informe_formato_unificado.pdf';out.save(temp,garbage=4,deflate=True);out.close()
check=f.open(temp)
for i in [0]:assert base[i].get_pixmap().samples==check[i].get_pixmap().samples,('Punto 1 cambiado',i+1)
qa=sorted(set([1,*[p['new_page'] for p in placements if p.get('kind')=='table']]))
for i in qa:check[i].get_pixmap().save(OUT/f'qa_{i+1}.png')
report={'pages':len(check),'tables':len(tables),'text_blocks':len(audit),'point1_format_updated':True,'cover_unchanged':True,'fonts':{'body':'Latin Modern Roman 10.5 pt','title':'Latin Modern Roman Bold 16 pt','subtitle':'Latin Modern Roman Bold 13 pt','heading':'Latin Modern Roman Bold 11.5 pt','table':'Latin Modern Roman 8.5 pt'},'toc':newtoc,'qa_pages':[i+1 for i in qa]}
(OUT/'verificacion_pdf.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');check.close();base.close()
for doc in assets.values():doc.close()
shutil.copy2(temp,ROOT/'Informe_Hidrologia_fuente_original.pdf')
for dest in [ROOT/'Informe_Hidrologia_actualizado_5_4.pdf',ROOT/'Informe_Hidrologia_actualizado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf',DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf',DOCS/'latex/informe_ordenado.pdf']:
    try:shutil.copy2(temp,dest)
    except PermissionError:print('Archivo abierto; consultar Informe_Hidrologia_formato_unificado.pdf:',dest,flush=True)
print(json.dumps({k:v for k,v in report.items() if k!='toc'},ensure_ascii=True),flush=True)

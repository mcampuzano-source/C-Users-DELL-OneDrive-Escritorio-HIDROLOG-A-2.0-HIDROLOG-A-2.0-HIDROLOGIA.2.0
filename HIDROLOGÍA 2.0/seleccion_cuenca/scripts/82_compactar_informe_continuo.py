"""Recompone las páginas con bandas de contenido visible, sin cambiar su escala."""
from pathlib import Path
import json,shutil,re
import numpy as np
import pymupdf as f
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';R=D.parents[3];O=D/'revision_continuidad';O.mkdir(exist_ok=True)
backup=O/'informe_antes_compactacion.pdf'
if not backup.exists():shutil.copy2(R/'Informe_Hidrologia_actualizado_1_5.pdf',backup)
base=f.open(backup);out=f.open();out.insert_pdf(base,to_page=1);placements=[];dest=None;y=48;removed=0
def newpage(width=595.276,height=841.89,top=48):
    global dest,y
    dest=out.new_page(width=width,height=height);y=top
for pi in range(2,len(base)):
    page=base[pi];w,h=page.rect.width,page.rect.height
    if w>h:
        out.insert_pdf(base,from_page=pi,to_page=pi);placements.append({'old_page':pi,'y0':0,'y1':h,'new_page':len(out)-1,'new_y':0});dest=None;continue
    pix=page.get_pixmap(colorspace=f.csGRAY);gray=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width)
    # Ignora pie de página y pequeñas marcas laterales; detecta únicamente tinta real.
    ink=(gray[:,:]<244);rows=ink[:,35:pix.width-35].sum(axis=1)>2;rows[:35]=False;rows[int(h-47):]=False
    indices=np.flatnonzero(rows)
    if not len(indices):removed+=1;continue
    groups=[];begin=int(indices[0]);last=begin
    for value in indices[1:]:
        value=int(value)
        if value-last>15:groups.append([begin-2,last+3]);begin=value
        last=value
    groups.append([begin-2,last+3])
    # Mantiene enteras las ilustraciones visibles aunque tengan vacíos internos.
    protected=[]
    for info in page.get_image_info():
        rect=f.Rect(info['bbox'])
        if rect.width>120 and 40<rect.height<730 and rect.y0>=30 and rect.y1<h-43:
            area=gray[max(35,int(rect.y0)):min(int(h-47),int(rect.y1)),max(35,int(rect.x0)):min(pix.width-35,int(rect.x1))]
            if area.size and (area<230).mean()>.005:protected.append((rect.y0-2,rect.y1+3))
    for drawing in page.get_drawings():
        rect=drawing['rect']
        if rect.width>150 and 90<rect.height<650 and rect.y0>35 and rect.y1<h-47 and drawing.get('color'):
            protected.append((rect.y0-2,rect.y1+3))
    for a,b in protected:
        hits=[k for k,(lo,hi) in enumerate(groups) if lo<b and hi>a]
        if len(hits)>1:
            left,right=hits[0],hits[-1];groups[left:right+1]=[[groups[left][0],groups[right][1]]]
    groups=[[max(35,a),min(h-47,b)] for a,b in groups]
    heading_areas=[]
    for block in page.get_text('dict',flags=0)['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                if span['bbox'][0]<85 and span['size']>=11.4 and 'Bold' in span['font']:heading_areas.append(f.Rect(span['bbox']))
    for k,(a,b) in enumerate(groups):
        height=b-a
        if height<=0:continue
        if dest is None:newpage(w,h)
        bottom=h-47
        reserve=0
        if height<45 and k+1<len(groups) and any(a<=r.y0<b for r in heading_areas):
            following=groups[k+1][1]-groups[k+1][0]+10
            reserve=following if height+following<bottom-35 else 35
        if y+height+reserve>bottom:newpage(w,h,top=35 if height>bottom-48 else 48)
        if height>bottom-y:raise RuntimeError(('Bloque demasiado alto',pi+1,a,b,height))
        dest.show_pdf_page(f.Rect(0,y,w,y+height),base,pi,clip=f.Rect(0,a,w,b))
        placements.append({'old_page':pi,'y0':a,'y1':b,'new_page':len(out)-1,'new_y':y})
        y+=height+10
def translated(pn,title):
    page=base[pn-1];candidates=[r for r in page.search_for(title) if 35<r.y0<page.rect.height-47]
    if not candidates:
        blocks=[b for b in page.get_text('blocks') if title in b[4].replace('\n',' ')]
        yy=(blocks[0][1]+blocks[0][3])/2 if blocks else 50
    else:yy=(candidates[0].y0+candidates[0].y1)/2
    hits=[p for p in placements if p['old_page']==pn-1]
    hit=next((p for p in hits if p['y0']<=yy<=p['y1']),hits[0] if hits else None)
    return hit['new_page']+1 if hit else pn
toc=[[l,t,translated(pn,t)] for l,t,pn in base.get_toc()];out.set_toc(toc)
F=D/'revision_tablas/fuentes_originales'
for pn in range(2,len(out)):
    p=out[pn];h=p.rect.height;p.add_redact_annot(f.Rect(0,h-42,p.rect.width,h),fill=(1,1,1));p.apply_redactions(images=0,graphics=0);p.insert_font(fontname='Hydro',fontfile=str(F/'lmroman10-regular.ttf'));p.insert_textbox(f.Rect(0,h-35,p.rect.width,h-15),str(pn),fontname='Hydro',fontsize=9,align=1)
idx=out[1];idx.add_redact_annot(f.Rect(35,35,idx.rect.width-35,idx.rect.height-43),fill=(1,1,1));idx.apply_redactions(images=0,graphics=0)
for link in idx.get_links():idx.delete_link(link)
idx.insert_font(fontname='Hydro',fontfile=str(F/'lmroman10-regular.ttf'));idx.insert_font(fontname='HydroBold',fontfile=str(F/'lmroman10-bold.ttf'));idx.insert_text((56,66),'Índice',fontname='HydroBold',fontsize=16);yy=98;sec=0;sub=0
for level,title,pn in toc:
    if level>2:continue
    if level==1:sec+=1;sub=0;yy+=7;label=f'{sec}. '
    else:sub+=1;label=f'{sec}.{sub}. '
    xx=56 if level==1 else 68;idx.insert_text((xx,yy),label+title,fontname='HydroBold' if level==1 else 'Hydro',fontsize=9 if level==1 else 8);idx.insert_text((534,yy),str(pn-1),fontname='Hydro',fontsize=8);idx.insert_link({'kind':f.LINK_GOTO,'from':f.Rect(xx,yy-11,553,yy+4),'page':pn-1});yy+=19
print(json.dumps({'layout_pages':len(out),'source_pages':len(base),'bands':len(placements)}),flush=True)
(O/'bandas.json').write_text(json.dumps(placements),encoding='utf-8')
out.set_metadata(base.metadata);final=O/'informe_continuo.pdf';out.save(final,garbage=1,deflate=True);out.close()
check=f.open(final);assert check[0].get_pixmap().samples==base[0].get_pixmap().samples
qa=sorted(set([2,3,*[pn-1 for level,title,pn in toc if level<=2],len(check)-1]))
for pn in qa:check[pn].get_pixmap().save(O/f'qa_{pn+1}.png')
report={'old_pages':len(base),'pages':len(check),'empty_pages_removed':removed,'font_and_scale_preserved':True,'cover_unchanged':True,'toc':toc,'qa_pages':[p+1 for p in qa]}
(O/'verificacion_continuidad.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');(O/'bandas.json').write_text(json.dumps(placements),encoding='utf-8');check.close();base.close()
for dest in [R/'Informe_Hidrologia_continuo.pdf',R/'Informe_Hidrologia_actualizado.pdf',R/'Informe_Hidrologia_integrado.pdf',D/'informe_continuo.pdf',D/'latex/informe_ordenado.pdf']:
    try:shutil.copy2(final,dest)
    except PermissionError:print('Copia abierta; usar Informe_Hidrologia_continuo.pdf')
# Fuente editable: elimina saltos forzados entre apartados y deja fluir figuras.
texpath=D/'latex/informe_ordenado.tex'
if not (O/'informe_antes_compactacion.tex').exists():shutil.copy2(texpath,O/'informe_antes_compactacion.tex')
tex=texpath.read_text(encoding='utf-8');cover_end=tex.find(r'\end{titlepage}')+len(r'\end{titlepage}');front=tex[:cover_end];body=tex[cover_end:]
body=re.sub(r'\\(?:clearpage|newpage)\b','',body);body=body.replace(r'\begin{figure}[p]',r'\begin{figure}[htbp]');texpath.write_text(front+body,encoding='utf-8')
# HTML: espaciado compacto entre puntos, párrafos, tablas y figuras.
path=D/'informe_interactivo.html'
if not (O/'informe_antes_compactacion.html').exists():shutil.copy2(path,O/'informe_antes_compactacion.html')
s=(O/'informe_antes_compactacion.html').read_text(encoding='utf-8')
css='''<style id="continuidad-informe">body [id^="guia-"]{margin-top:16px!important;margin-bottom:16px!important;padding-top:0!important;padding-bottom:0!important;min-height:0!important;break-before:auto!important;page-break-before:auto!important}body [id^="guia-"] p{margin-top:6px!important;margin-bottom:10px!important}body [id^="guia-"] h2,body [id^="guia-"] h3,body [id^="guia-"] h4{margin-top:18px!important;margin-bottom:10px!important}body [id^="guia-"] figure{margin:14px 0!important}body .tabla-contenedor{margin:8px 0 12px!important}body [id^="guia-"] .card{margin-top:10px!important;margin-bottom:10px!important;padding:16px!important}@media print{[id^="guia-"]{break-before:auto!important;page-break-before:auto!important}}</style>'''
s=s.replace('</body>',css+'\n</body>',1)
for dest in [path,R/'Informe_Hidrologia_interactivo.html']:dest.write_text(s,encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['toc','qa_pages']}),flush=True)

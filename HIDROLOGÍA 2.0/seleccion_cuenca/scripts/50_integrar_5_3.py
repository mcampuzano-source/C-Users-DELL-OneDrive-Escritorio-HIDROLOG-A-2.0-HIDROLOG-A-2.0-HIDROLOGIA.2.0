"""Integra 5.3 en la base con portada, Fourier y atlas 5.2."""
from pathlib import Path
import shutil,json,hashlib
import pymupdf

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
ROOT=DOCS.parents[3];OUT=DOCS/'apartado_5_3'
backup=OUT/'base_antes_5_3.pdf'
if not backup.exists():shutil.copy2(ROOT/'Informe_Hidrologia_actualizado.pdf',backup)
base=pymupdf.open(backup);toc=base.get_toc();source_atlas=pymupdf.open(OUT/'punto_5_3.pdf')
# Reserve a separate footer band: never cover the map legend or source note.
atlas=pymupdf.open()
basin=json.loads((DOCS.parent/'topografia/cuenca_la_vieja.geojson').read_text(encoding='utf-8'))
rings=[]
for feature in basin['features']:
    from shapely.geometry import shape,mapping
    # Cartographic simplification below one screen pixel at global scale.
    # The original polygon and the interactive outline retain every vertex.
    g=mapping(shape(feature['geometry']).simplify(.01,preserve_topology=True));polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    rings.extend(poly[0] for poly in polygons)
for i,p in enumerate(source_atlas):
    if p.rect.width>p.rect.height:
        width=p.rect.width;height=p.rect.height
        notes=[b[4].strip() for b in p.get_text('blocks') if b[4].startswith(('Negro:','Subperiodos:','Persistencia entre años','Gris:'))]
        # Separate source notes from the colorbar label before adding the footer.
        p.draw_rect(pymupdf.Rect(0,height-38,width,height),color=None,fill=(1,1,1))
        aw=.925/(3+2*.06);ah=.735/(4+3*.27)
        for row in range(4):
            for col in range(3):
                left=.05+col*aw*1.06;top=.895-row*ah*1.27
                for ring in rings:
                    points=[pymupdf.Point((left+aw*(lon+180)/360)*width,(1-top+ah*(90-lat)/180)*height) for lon,lat,*_ in ring]
                    p.draw_polyline(points,color=(0,0,0),width=.35,closePath=True)
        page=atlas.new_page(width=width,height=height+58);page.show_pdf_page(p.rect,source_atlas,i)
        label='Años efectivos (aproximación)' if 'Tamaño efectivo' in p.get_text() else 'Coeficiente adimensional (-1 a 1)'
        page.insert_textbox(pymupdf.Rect(width*.25,height-37,width*.75,height-23),label,fontsize=8,align=1)
        page.insert_textbox(pymupdf.Rect(45,height-10,width-45,height+13),'\n'.join(notes),fontsize=7)
    else:atlas.insert_pdf(source_atlas,from_page=i,to_page=i)
atlas.set_toc(source_atlas.get_toc());source_atlas.close()
pos=next(row[2]-1 for row in toc if row[1]=='Robustez y presentación de los patrones')
p=base[pos];blocks=p.get_text('blocks')
first=next(b for b in blocks if '5.3.' in b[4]);nextblock=next(b for b in blocks if '5.4.' in b[4])
p.add_redact_annot(pymupdf.Rect(35,first[1]-3,p.rect.width-35,nextblock[1]-4),fill=(1,1,1));p.apply_redactions()
out=pymupdf.open();out.insert_pdf(base,to_page=pos-1);out.insert_pdf(atlas);out.insert_pdf(base,from_page=pos)
for row in toc:
    if row[2]>pos and row[1]!='Robustez y presentación de los patrones':row[2]+=len(atlas)
insert=next(i for i,row in enumerate(toc) if row[1]=='Robustez y presentación de los patrones')+1
toc[insert:insert]=[[3,title,page+pos] for _,title,page in atlas.get_toc()]
out.set_toc(toc)
for i in range(pos,len(out)):
    p=out[i];y=p.rect.height
    p.draw_rect(pymupdf.Rect(0,y-42,p.rect.width,y),color=None,fill=(1,1,1))
    p.insert_textbox(pymupdf.Rect(0,y-35,p.rect.width,y-15),str(i),fontsize=10,align=1)
index=out[1];index.add_redact_annot(pymupdf.Rect(35,35,index.rect.width-35,index.rect.height-43),fill=(1,1,1));index.apply_redactions()
for link in index.get_links():index.delete_link(link)
index.insert_text((56,66),'Índice',fontsize=18);y=98;section=0;sub=0
for level,title,page in toc:
    if level>2:continue
    if level==1:section+=1;sub=0;y+=7;prefix=f'{section}. '
    else:sub+=1;prefix=f'{section}.{sub}. '
    x=56 if level==1 else 68
    index.insert_text((x,y),prefix+title,fontsize=10 if level==1 else 9)
    index.insert_text((534,y),str(page-1),fontsize=9)
    index.insert_link({'kind':pymupdf.LINK_GOTO,'from':pymupdf.Rect(x,y-11,553,y+4),'page':page-1});y+=19
meta=base.metadata;meta['subject']='Hidrología: puntos 1-4 y apartados 5.1, 5.2 y 5.3';out.set_metadata(meta)
target=ROOT/'Informe_Hidrologia_actualizado_5_3.pdf';tmp=OUT/'integrado_nuevo.pdf';out.save(tmp,garbage=4,deflate=True)
out.close();base.close();n_atlas=len(atlas);atlas.close();shutil.copy2(tmp,target)
for dest in [ROOT/'Informe_Hidrologia_actualizado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf',DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf']:
    try:shutil.copy2(target,dest)
    except PermissionError:print('Archivo abierto; usar versión 5_3:',dest)
check=pymupdf.open(target)
assert 'Integrantes' in check[0].get_text()
assert any('Fourier' in p.get_text() for p in check)
assert '5.3. Robustez' in check[pos].get_text()
assert any('5.4.' in p.get_text() and 'Pendiente' in p.get_text() for p in check)
for i in [0,1,pos,pos+1,pos+2,pos+3,pos+4,pos+n_atlas-1,pos+n_atlas]:
    check[i].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(OUT/f'qa_integrado_{i+1}.png')
validation={'pages':len(check),'start_5_3':pos+1,'pages_5_3':n_atlas,'pending':['5.4','Conclusiones finales','Declaración final de IA','Referencias consolidadas'],
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'base_sha256':hashlib.sha256(backup.read_bytes()).hexdigest()}
(OUT/'integracion.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False),flush=True)

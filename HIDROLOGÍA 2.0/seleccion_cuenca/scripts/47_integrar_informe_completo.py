"""Integra el atlas 5.2 conservando portada, puntos 1-4 y 5.1."""
from pathlib import Path
import hashlib
import json
import shutil
import pymupdf

DOCS = Path(__file__).resolve().parents[1] / 'la_vieja/documentos'
ROOT = DOCS.parents[3]
OUT = DOCS / 'integracion_final'
OUT.mkdir(exist_ok=True)
BACKUP = OUT / 'base_antes_5_2.pdf'
if not BACKUP.exists():
    shutil.copy2(DOCS / 'informe_actualizado.pdf', BACKUP)
base = pymupdf.open(BACKUP)
atlas = pymupdf.open(DOCS / 'apartado_5_2/punto_5_2.pdf')
for p in atlas:
    notes=[b for b in p.get_text('blocks') if b[4].startswith('Respuesta:')]
    for b in notes:
        p.add_redact_annot(pymupdf.Rect(b[:4]),fill=False)
    if notes:
        p.apply_redactions(images=0,graphics=0)
        from matplotlib import colormaps
        p.draw_rect(pymupdf.Rect(0,p.rect.height-120,p.rect.width,p.rect.height-57),color=None,fill=(1,1,1))
        x0=p.rect.width*.32; x1=p.rect.width*.68; y=p.rect.height-103
        for k in range(100):
            color=tuple(colormaps['RdBu_r'](k/99)[:3])
            p.draw_rect(pymupdf.Rect(x0+(x1-x0)*k/100,y,x0+(x1-x0)*(k+1)/100,y+8),color=None,fill=color)
        for k,label in enumerate(['-1','-0.5','0','0.5','1']):
            x=x0+(x1-x0)*k/4
            p.insert_textbox(pymupdf.Rect(x-16,y+10,x+16,y+22),label,fontsize=7,align=1)
        p.insert_textbox(pymupdf.Rect(x0-35,y+24,x1+35,y+36),'Coeficiente adimensional: misma escala en todos los paneles',fontsize=7,align=1)
        note=' '.join(b[4].replace('\n',' ') for b in notes)
        p.insert_textbox(pymupdf.Rect(40,p.rect.height-55,p.rect.width-40,p.rect.height-43),note,fontsize=7,align=1)
toc = base.get_toc()
pos = next(row[2]-1 for row in toc if row[1] == 'Definir y calcular los mapas mensuales')
page = base[pos]
blocks = page.get_text('blocks')
first = next(b for b in blocks if '5.2.' in b[4])
following = next(b for b in blocks if '5.3.' in b[4])
page.add_redact_annot(pymupdf.Rect(35,first[1]-3,page.rect.width-35,following[1]-4),fill=(1,1,1))
page.apply_redactions()
out = pymupdf.open()
out.insert_pdf(base,to_page=pos-1)
out.insert_pdf(atlas)
out.insert_pdf(base,from_page=pos)
updates=[
    ('IMERG está incorporado como promedio de caja',
     'IMERG Final V07B se incorpora como promedio ponderado sobre el polígono exacto de la cuenca: 300 meses válidos y 285 meses comunes completos. ERA5-Land aporta temperatura media a 2 m. Zaragoza aporta 14 meses completos de lluvia local; esa muestra no permite una climatología anual ni doce correlaciones interanuales. El inventario de estaciones no demuestra continuidad de sus series.'),
    ('Temperatura: el archivo contiene Tmin',
     'Temperatura: MSWX Tmin/Tmax se conserva como antecedente. Los análisis actualizados usan temperatura media a 2 m de ERA5-Land, un reanálisis, no una medición de estación.'),
]
for p in out:
    for needle,replacement in updates:
        blocks=[b for b in p.get_text('blocks') if needle in b[4]]
        for b in blocks:
            box=pymupdf.Rect(b[:4]);p.add_redact_annot(box,fill=(1,1,1));p.apply_redactions(images=0,graphics=0)
            for size in [9,8.5,8,7.5]:
                shape=p.new_shape()
                result=shape.insert_textbox(box,replacement,fontsize=size,fontname='helv')
                if result>=0:shape.commit();break
            else:raise RuntimeError('Texto actualizado no cabe en la página')
for row in toc:
    if row[2] > pos and row[1] != 'Definir y calcular los mapas mensuales':
        row[2] += len(atlas)
atlas_toc = [[3,title,page+pos] for _,title,page in atlas.get_toc()]
insert = next(i for i,row in enumerate(toc) if row[1]=='Definir y calcular los mapas mensuales')+1
toc[insert:insert] = atlas_toc
out.set_toc(toc)
for i in range(1,len(out)):
    p=out[i]; y=p.rect.height
    p.add_redact_annot(pymupdf.Rect(0,y-42,p.rect.width,y),fill=(1,1,1))
    p.apply_redactions()
    p.insert_textbox(pymupdf.Rect(0,y-35,p.rect.width,y-15),str(i),fontsize=10,align=1)
index=out[1]
index.add_redact_annot(pymupdf.Rect(35,35,index.rect.width-35,index.rect.height-43),fill=(1,1,1))
index.apply_redactions()
for link in index.get_links(): index.delete_link(link)
index.insert_text((56,66),'Índice',fontsize=18)
y=98; section=0; sub=0
for level,title,page in toc:
    if level>2: continue
    if level==1: section+=1;sub=0;y+=7;prefix=f'{section}. '
    else: sub+=1;prefix=f'{section}.{sub}. '
    x=56 if level==1 else 68
    index.insert_text((x,y),prefix+title,fontsize=10 if level==1 else 9)
    index.insert_text((534,y),str(page-1),fontsize=9)
    index.insert_link({'kind':pymupdf.LINK_GOTO,'from':pymupdf.Rect(x,y-11,553,y+4),'page':page-1})
    y+=19
out.set_metadata(base.metadata)
target=ROOT/'Informe_Hidrologia_actualizado.pdf'
if target.exists(): target.unlink()
out.save(target,garbage=4,deflate=True)
out.close();base.close();atlas.close()
for dest in [DOCS/'informe_actualizado.pdf',DOCS/'apartado_3/informe_integrado.pdf',ROOT/'Informe_Hidrologia_integrado.pdf']:
    try: shutil.copy2(target,dest)
    except PermissionError: print('Visor mantiene bloqueado:',dest)
import re
hpath=DOCS/'informe_interactivo.html'
h=hpath.read_text(encoding='utf-8')
for needle,replacement in updates:
    h=re.sub(r'<p[^>]*>\s*'+re.escape(needle)+r'.*?</p>',lambda _: '<p>'+replacement+'</p>',h,flags=re.S)
hpath.write_text(h,encoding='utf-8')
shutil.copy2(hpath,ROOT/'Informe_Hidrologia_interactivo.html')
check=pymupdf.open(target)
assert 'Integrantes' in check[0].get_text()
assert any('Fourier' in p.get_text() for p in check)
assert any('5.2. Correlaciones' in p.get_text() for p in check)
qa=[0,1,pos,pos+1,pos+2,pos+3,pos+len(pymupdf.open(DOCS/'apartado_5_2/punto_5_2.pdf'))-1]
for i in qa:check[i].get_pixmap(matrix=pymupdf.Matrix(1,1)).save(OUT/f'pagina_{i+1}.png')
(OUT/'verificacion.json').write_text(json.dumps({'pages':len(check),'start_5_2':pos+1,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pending':['5.3','5.4','Conclusiones finales'],'source_commit':'b68ea53c79d27ea6daf01db89cc54f3436211886'},indent=2),encoding='utf-8')
print('Informe integrado:',target,'paginas:',len(check),'5.2:',pos+1)

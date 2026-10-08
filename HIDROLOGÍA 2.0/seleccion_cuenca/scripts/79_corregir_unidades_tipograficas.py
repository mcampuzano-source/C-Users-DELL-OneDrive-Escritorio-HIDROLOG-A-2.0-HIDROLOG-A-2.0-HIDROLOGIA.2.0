"""Corrige dos escapes de unidades en el PDF ya compuesto; no altera cifras."""
from pathlib import Path
import pymupdf as f
import shutil,json
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';O=D/'revision_tablas';R=D.parents[3]
path=O/'informe_formato_unificado.pdf';d=f.open(path);fixed=[]
for pn in range(len(d)):
    p=d[pn];edits=[]
    for old,new in [('m^3/s','m³/s'),(r'^\circC','°C')]:
        for rect in p.search_for(old):
            edits.append((rect,new));p.add_redact_annot(rect,fill=None)
    if pn==24:
        for prefix,label in [('ERA5-Land Tmedia (','ERA5-Land Tmedia (°C)'),('Caudal Q (','Caudal Q (m³/s)')]:
            for rect in p.search_for(prefix):
                if rect.y0>650 and 55<rect.x0<85:
                    cell=f.Rect(rect.x0,rect.y0,245,rect.y1)
                    edits=[(r,t) for r,t in edits if not cell.intersects(r)]
                    edits.append((cell,label));p.add_redact_annot(cell,fill=None)
    if edits:
        p.apply_redactions(images=0,graphics=0)
        p.insert_font(fontname='HydroOriginal',fontfile=str(O/'fuentes_originales/lmroman10-regular.ttf'))
        for rect,text in edits:p.insert_text((rect.x0,rect.y1-2),text,fontname='HydroOriginal',fontsize=8.5)
        fixed.append(pn+1)
if fixed:
    tmp=O/'informe_fuente_original_corregido.pdf';d.save(tmp,garbage=3,deflate=True);d.close();shutil.copy2(tmp,path)
else:d.close()
for dest in [R/'Informe_Hidrologia_fuente_original.pdf',R/'Informe_Hidrologia_actualizado_5_4.pdf',R/'Informe_Hidrologia_actualizado.pdf',R/'Informe_Hidrologia_integrado.pdf',D/'informe_actualizado.pdf',D/'apartado_3/informe_integrado.pdf',D/'latex/informe_ordenado.pdf']:
    try:shutil.copy2(path,dest)
    except PermissionError:print('Copia abierta:',str(dest).encode('ascii','backslashreplace').decode())
d=f.open(path)
for pn in fixed:d[pn-1].get_pixmap().save(O/f'qa_{pn}.png')
(O/'verificacion_unidades.json').write_text(json.dumps({'pages_corrected':fixed,'values_changed':False}),encoding='utf-8')
print('Unidades corregidas:',fixed)

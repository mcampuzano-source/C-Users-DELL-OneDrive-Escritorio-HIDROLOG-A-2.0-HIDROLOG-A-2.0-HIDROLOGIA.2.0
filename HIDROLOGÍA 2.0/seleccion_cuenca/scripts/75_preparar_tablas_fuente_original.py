"""Prepara tablas homogéneas de 2-5; el punto 1 queda fuera del alcance."""
from pathlib import Path
import pymupdf as f
import re,json,shutil,html,csv
import numpy as np
from reportlab.platypus import Table,TableStyle,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import matplotlib
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_tablas';OUT.mkdir(exist_ok=True)
backup=OUT/'base_antes.pdf'
if not backup.exists():shutil.copy2(ROOT/'Informe_Hidrologia_actualizado_5_4.pdf',backup)
pdf=f.open(backup);toc=pdf.get_toc()
start=next(p-1 for l,t,p in toc if l==1)
end=next(p-1 for l,t,p in toc if l==3)
chapters=[(p-1,t) for l,t,p in toc if l==1]
def chapter(p):return next((i+1 for i,(a,t) in reversed(list(enumerate(chapters))) if a<=p),0)
def simplify(s):
    s=re.sub(r'\\hline|\\toprule|\\midrule|\\bottomrule|\\small|\\textbf|\\mathrm','',s).replace('$','').replace('{','').replace('}','')
    s=s.replace('\\%','%').replace('\\_','_').replace('^2','²').replace('--','–').replace('\\geq','≥').replace('\\leq','≤')
    return ' '.join(s.split())
tex=(DOCS/'latex/informe_ordenado.tex').read_text(encoding='utf-8')
section=tex[tex.index(r'\section{Relaciones entre series'):tex.index('% PUNTO_3_COMMIT')]
native=[]
for m in re.finditer(r'\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}',section,re.S):
    rows=[[simplify(v) for v in row.split('&')] for row in m.group(1).split('\\\\') if simplify(row)]
    native.append(rows)
specs=[];native_index=0
known=['variable','Estadístico','Fuente','Relación','Referencia','Variable','Representación','Mes','Variante','Método','Periodo','Modelo','Bloque','Muestra']
for pi in range(start,end):
    page=pdf[pi];ch=chapter(pi)
    if ch not in [1,2,3,4]:continue
    groups={}
    for drawing in page.get_drawings():
        for item in drawing['items']:
            if item[0]=='l':
                a,b=item[1:];x0,x1=sorted([a.x,b.x]);yy=(a.y+b.y)/2
                if abs(a.y-b.y)<.2 and x1-x0>70 and 45<yy<795:groups.setdefault((round(x0,1),round(x1,1)),[]).append(yy)
    if not any(len(set(v))>=3 for v in groups.values()):continue
    pix=page.get_pixmap(matrix=f.Matrix(2,2),colorspace=f.csGRAY)
    raster=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width)
    for (x0,x1),ys in groups.items():
        visible=[]
        for y in sorted(set(round(v,2) for v in ys)):
            area=raster[max(0,int(y*2)-2):int(y*2)+3,int((x0+2)*2):int((x1-2)*2)]
            if area.size and (area.min(axis=0)<210).mean()>.85:visible.append(y)
        for k in range(0,len(visible)-2,3):
            a,mid,b=visible[k:k+3]
            header=page.get_text(clip=f.Rect(x0,a,x1,mid),flags=0)
            if not any(v in header for v in known):continue
            specs.append({'page':pi+1,'chapter':ch,'rect':[x0,a-1,x1,b+1],'header_rect':[x0,a,x1,mid],'body_rect':[x0,mid,x1,b],'raw_header':header})
specs.sort(key=lambda s:(s['page'],s['rect'][1]))
for s in specs:
    if s['chapter']==2:
        s['rows']=native[native_index];native_index+=1
if native_index!=len(native):
    (OUT/'deteccion.json').write_text(json.dumps({'source':[r[0] for r in native],'detected':[{k:s[k] for k in ['page','rect','raw_header']} for s in specs if s['chapter']==2]},ensure_ascii=False,indent=2),encoding='utf-8')
    raise RuntimeError(f'Tablas detectadas: {native_index}/{len(native)}; revisar deteccion.json')
def matrix(s,n):
    page=pdf[s['page']-1];head=f.Rect(s['header_rect']);body=f.Rect(s['body_rect'])
    words=page.get_text('words',clip=head)
    first=min(w[1] for w in words);line=sorted([w for w in words if w[1]<first+4],key=lambda w:w[0])
    gaps=sorted([(line[i+1][0]-line[i][2],i) for i in range(len(line)-1)],reverse=True)
    divisions=sorted(i for _,i in gaps[:n-1])
    bounds=[head.x0]+[(line[i][2]+line[i+1][0])/2 for i in divisions]+[head.x1]
    if s['page']==47:bounds=[head.x0,187,272,356,448,head.x1]
    assert len(bounds)==n+1
    def celltext(ws):
        lines={}
        for w in ws:lines.setdefault(round(w[1]/3)*3,[]).append(w)
        return ' '.join(' '.join(w[4] for w in sorted(v,key=lambda q:q[0])) for _,v in sorted(lines.items()))
    header=[celltext([w for w in words if bounds[i]<=(w[0]+w[2])/2<bounds[i+1]]) for i in range(n)]
    ws=page.get_text('words',clip=body)
    last=[w for w in ws if bounds[-2]<=(w[0]+w[2])/2<bounds[-1] and re.search(r'\d',w[4])]
    if n==2 or not last:last=[w for w in ws if bounds[0]<=(w[0]+w[2])/2<bounds[1]]
    starts=sorted(set(round(w[1],1) for w in last))
    starts=[v for i,v in enumerate(starts) if i==0 or v-starts[i-1]>4]
    ys=[body.y0]+[(v-2) for v in starts[1:]]+[body.y1]
    rows=[header]
    for lo,hi in zip(ys,ys[1:]):
        rws=[w for w in ws if lo<=w[1]<hi]
        rows.append([celltext([w for w in rws if bounds[i]<=(w[0]+w[2])/2<bounds[i+1]]) for i in range(n)])
    return rows
schemas={12:[9,10,5,3,9],13:[10,5,3],15:[5,3,5,3],16:[4],20:[8,8],21:[8],25:[4,4],27:[5],28:[6],47:[5],48:[4],50:[3],51:[5],52:[9],53:[7],54:[7,11,2],55:[7],56:[6,4,4],57:[5],58:[6],59:[6],61:[7]}
page_indices={}
for s in specs:
    if s['chapter']==2:continue
    pi=s['page'];idx=page_indices.get(pi,0);page_indices[pi]=idx+1
    if pi not in schemas or idx>=len(schemas[pi]):raise RuntimeError(f'Schema required: {pi} {idx} {s["raw_header"]!r}')
    s['rows']=matrix(s,schemas[pi][idx])
    if pi==59:
        s['rows']=[['Variable y unidad','Cobertura disponible','Válidos','Tramo DFT seleccionado','N','Δf (ciclos/mes)'],
          ['Lluvia local Zaragoza-AUT (mm/mes)','2018-01–2019-11; 23 meses en el archivo','14 meses 100 % cubiertos','2018-08–2019-02','7','0,1429'],
          ['Precipitación de referencia CHIRPS (mm/mes)','1981-01–2022-12','485/504; 19 vacíos','1981-01–1990-01','109','0,00917'],
          ['IMERG Final V07B en el polígono (mm/mes)','1998-01–2022-12','300/300','1998-01–2022-12','300','0,00333'],
          ['Caudal Cartago (m³/s)','1981-01–2022-12','485/504; 19 vacíos','1981-01–1990-01','109','0,00917'],
          ['Temperatura ERA5-Land t2m (°C)','1981-01–2026-08','548/548','1981-01–2026-08','548','0,00182']]
    if pi==61:
        d=json.loads((DOCS/'apartado_5_4/d42_fuente_punto4.json').read_text(encoding='utf-8'))
        s['rows']=[['Variable','Muestra','Forma','Anual: periodo; ciclos; %','Semianual: periodo; ciclos; %','Interanual: periodo; ciclos; %','Δf']]
        for row in d['rows']:
            values=[f"{row[b]['period_months']:g} meses; {row[b]['cycles_observed']:.1f} ciclos; {row[b]['band_share_pct']:.1f} %" for b in ['annual','semiannual','interannual_2_10y']]
            s['rows'].append([row['variable'],row['period']+f" (N = {row['n']})",row['transformation'],*values,f"{row['df']:.5f}"])
# Las tablas de 5.3 y 5.4 tienen una celda por bloque: extracción directa conserva el texto.
for pn,needle,lastneedle,ncols in [(96,'Combinación','IMERG_z500_l0',7),(97,'Combinación','Fuentes metodológicas',5),(149,'Punto','Cierre de la caracterización',4)]:
    page=pdf[pn-1];bs=page.get_text('blocks',flags=0)
    first=next(i for i,b in enumerate(bs) if b[4].lstrip().startswith(needle+'\n'))
    if pn==96:last=next(i for i,b in enumerate(bs) if lastneedle in b[4])+1
    else:last=next(i for i,b in enumerate(bs[first+1:],first+1) if b[4].startswith(lastneedle))
    picked=bs[first:last]
    if pn in [96,97]:rows=[[v.strip() for v in b[4].splitlines()] for b in picked]
    else:
        with (DOCS/'apartado_5_4/tabla_evidencia_mecanismos.csv').open(encoding='utf-8',newline='') as file:evidence=list(csv.DictReader(file))
        rows=[['Punto','Resultado y evidencia','Mecanismo y fuente','Limitación']]+[[r['punto'],r['resultado']+'; '+r['evidencia'],r['mecanismo_propuesto']+'; '+r['fuente'],r['limitacion']] for r in evidence]
    assert all(len(r)==ncols for r in rows),(pn,rows)
    specs.append({'page':pn,'chapter':5,'rect':[62,picked[0][1]-5,545,picked[-1][3]+6],'rows':rows})

part1=tex[:tex.index(r'\section{Relaciones entre series')]
native1=[]
for m in re.finditer(r'\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}',part1,re.S):
    native1.append([[simplify(v) for v in row.split('&')] for row in m.group(1).split('\\\\') if simplify(row)])
lookup={12:{3:0},13:{2:1},15:{0:2,1:3,2:4,3:5},16:{0:6},20:{0:7},25:{0:8,1:9},27:{0:10},28:{0:11}}
counts={}
for spec in specs:
    if spec['chapter']!=1:continue
    pn=spec['page'];ordinal=counts.get(pn,0);counts[pn]=ordinal+1
    ix=lookup.get(pn,{}).get(ordinal)
    if ix is not None:spec['rows']=native1[ix]
    for row in spec['rows']:
        for k,value in enumerate(row):row[k]=value.replace('ﬁ','fi').replace('ﬂ','fl').replace('mş/s','m³/s').replace('řC','°C').replace(r'^\circC','°C').replace('^3','³')
        if len(row)>1 and row[1].startswith('Tmedia '):row[0]+=' Tmedia';row[1]=row[1][7:]
    spec['rows'][0]=[value.replace('_',' ') for value in spec['rows'][0]]
fontdir=OUT/'fuentes_originales'

pdfmetrics.registerFont(TTFont('HydroTable',str(fontdir/'lmroman10-regular.ttf')))
pdfmetrics.registerFont(TTFont('HydroTableBold',str(fontdir/'lmroman10-bold.ttf')))
style=ParagraphStyle('cell',fontName='HydroTable',fontSize=8.5,leading=11)
headerstyle=ParagraphStyle('head',fontName='HydroTableBold',fontSize=8.5,leading=11,textColor=colors.white)
for index,s in enumerate(specs):
    rows=s['rows'];n=len(rows[0]);assert all(len(row)==n for row in rows),(s['page'],rows)
    for row in rows:
        for i,value in enumerate(row):row[i]=re.sub(r'(?<=\d)\.(?=\d)',',',value)
    numeric=[all(re.fullmatch(r'[\d\s,.\[\];<>+−\-%/]+',r[i] or '') for r in rows[1:]) for i in range(n)]
    lengths=[max(len(r[i]) for r in rows) for i in range(n)]
    weights=[max(7,min(34,v)) for v in lengths]
    if n>=7:weights[0]=max(weights[0],20)
    minimum=[]
    for i in range(n):
        tokens=[v for r in rows for v in re.split(r'[\s;\[\]/]+',r[i]) if v]
        headtokens=[v for v in re.split(r'[\s;\[\]/]+',rows[0][i]) if v]
        minimum.append(max(25,max(pdfmetrics.stringWidth(v,'HydroTable',8.5) for v in tokens)+11,max(pdfmetrics.stringWidth(v,'HydroTableBold',8.5) for v in headtokens)+11))
    if sum(minimum)>483:minimum=[min(v,50) for v in minimum]
    remaining=483-sum(minimum)
    widths=[m+remaining*w/sum(weights) for m,w in zip(minimum,weights)]
    data=[]
    for ri,row in enumerate(rows):
        vals=[]
        for ci,v in enumerate(row):
            st=headerstyle if ri==0 else ParagraphStyle('value',parent=style,alignment=2 if numeric[ci] else 0)
            vals.append(Paragraph(html.escape(v.replace('/',' / ') if ri==0 else v),st))
        data.append(vals)
    table=Table(data,colWidths=widths,repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17485e')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f5f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd6dc'))]))
    queue=[table];parts=[]
    if n>9:
        queue=[]
        for begin in range(2,n,3):
            cols=[0,1,*range(begin,min(begin+3,n))]
            sub=Table([[row[k] for k in cols] for row in data],colWidths=[64,30,*([389/(len(cols)-2)]*(len(cols)-2))],repeatRows=1)
            sub.setStyle(table._cellStyles and TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17485e')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f5f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd6dc'))]))
            queue.append(sub)
    while queue:
        obj=queue.pop(0);w,h=obj.wrap(483,1500)
        if h>690:
            split=obj.split(483,690);assert len(split)>1
            queue=split+queue;continue
        parts.append((obj,h))
    s['files']=[];s['heights']=[]
    for j,(obj,h) in enumerate(parts):
        name=f'tabla_{index+1}_{j+1}.pdf';s['files'].append(name);s['heights'].append(h+2)
        c=canvas.Canvas(str(OUT/name),pagesize=(483,h+2));obj.drawOn(c,0,1);c.save()
(OUT/'tablas.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),encoding='utf-8')
print('Tablas:',len(specs),'Punto 1 incluido.',flush=True)

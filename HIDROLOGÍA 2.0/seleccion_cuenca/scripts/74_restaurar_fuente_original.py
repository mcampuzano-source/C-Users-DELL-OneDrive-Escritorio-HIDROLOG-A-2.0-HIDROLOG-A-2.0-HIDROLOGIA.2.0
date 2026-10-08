"""Extiende el formato al punto 1 y restaura Latin Modern Roman en ambos informes."""
from pathlib import Path
import urllib.request,json,re,subprocess,sys
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
S=Path(__file__).resolve().parent;D=S.parent/'la_vieja/documentos';O=D/'revision_tablas';F=O/'fuentes_originales';F.mkdir(exist_ok=True)
for weight in ['regular','bold']:
    otf=F/f'lmroman10-{weight}.otf';ttf=F/f'lmroman10-{weight}.ttf'
    if not otf.exists():
        urllib.request.urlretrieve('https://mirrors.ctan.org/fonts/lm/fonts/opentype/public/lm/'+otf.name,otf)
    if not ttf.exists():
        src=TTFont(otf);order=src.getGlyphOrder();gs=src.getGlyphSet();glyphs={}
        for name in order:
            pen=TTGlyphPen(gs);gs[name].draw(Cu2QuPen(pen,max_err=1.0,reverse_direction=True));glyphs[name]=pen.glyph()
        fb=FontBuilder(src['head'].unitsPerEm,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(src.getBestCmap());fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(src['hmtx'].metrics);fb.setupHorizontalHeader(ascent=src['hhea'].ascent,descent=src['hhea'].descent)
        fb.setupNameTable({'familyName':'Latin Modern Roman','styleName':weight.title(),'uniqueFontIdentifier':'Hydro-LMRoman10-'+weight,'fullName':'Latin Modern Roman '+weight.title(),'psName':'LMRoman10-'+weight.title()})
        fb.setupOS2(sTypoAscender=src['OS/2'].sTypoAscender,sTypoDescender=src['OS/2'].sTypoDescender,usWinAscent=src['OS/2'].usWinAscent,usWinDescent=src['OS/2'].usWinDescent);fb.setupPost();fb.setupMaxp();fb.save(ttf)
def fonts(t):
    t=t.replace("Path(matplotlib.get_data_path())/'fonts/ttf'","OUT/'fuentes_originales'")
    return t.replace('DejaVuSerif-Bold.ttf','lmroman10-bold.ttf').replace('DejaVuSerif.ttf','lmroman10-regular.ttf').replace('DejaVu Serif','Latin Modern Roman')
t=fonts((S/'71_preparar_formato_unificado.py').read_text(encoding='utf-8'))
t=t.replace("start=next(p-1 for l,t,p in toc if l==1 and 'Relaciones entre series' in t)","start=next(p-1 for l,t,p in toc if l==1)")
t=t.replace("r'\\\\hline|\\\\small|\\\\textbf|\\\\mathrm'","r'\\\\hline|\\\\toprule|\\\\midrule|\\\\bottomrule|\\\\small|\\\\textbf|\\\\mathrm'")
t=t.replace("known=['Fuente'","known=['variable','Estadístico','Fuente'").replace('ch not in [2,3,4]','ch not in [1,2,3,4]')
t=t.replace("schemas={47:","schemas={12:[9,10,5,3,9],13:[10,5,3],15:[5,3,5,3],16:[4],20:[8,8],21:[8],25:[4,4],27:[5],28:[6],47:")
t=t.replace("fontdir=OUT/'fuentes_originales'",r'''
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
''')
t=t.replace("Punto 1 excluido.","Punto 1 incluido.")
(S/'75_preparar_tablas_fuente_original.py').write_text(t,encoding='utf-8')
t=fonts((S/'72_unificar_tipografia_pdf.py').read_text(encoding='utf-8'))
t=t.replace("start=next(p-1 for l,t,p in toc if l==1 and 'Relaciones entre series' in t)","start=2")
t=t.replace("        maximum=max(s['size'] for s in spans);bold=", "        if any(re.match(r'CM(?:MI|SY|EX)',s['font']) for s in spans):continue\n        maximum=max(s['size'] for s in spans);bold=")
t=t.replace('[2-5]','[1-5]')
t=t.replace("for i in [0,*range(2,start)]:assert", "for i in [0]:assert")
t=t.replace("'point1_unchanged':True","'point1_format_updated':True,'cover_unchanged':True")
t=t.replace("f.open(OUT/name)","f.open(stream=(OUT/name).read_bytes(),filetype='pdf')")
t=t.replace("ROOT/'Informe_Hidrologia_formato_unificado.pdf'","ROOT/'Informe_Hidrologia_fuente_original.pdf'")
(S/'76_unificar_pdf_fuente_original.py').write_text(t,encoding='utf-8')
t=fonts((S/'73_unificar_formato_html.py').read_text(encoding='utf-8'))
t=t.replace("scope=':is(#guia-punto-2", "scope=':is(#guia-punto-1,#guia-punto-2")
t=t.replace("scope=':is(#guia-punto-1,#guia-punto-2,#guia-punto-3,#guia-punto-4,#guia-punto-5)'","scope='body'")
t=t.replace("'#guia-punto-2 table", "'#guia-punto-1 table,#guia-punto-2 table")
t=t.replace(" if(document.getElementById('guia-punto-1').innerHTML!==before)throw new Error('Se modificó el punto 1');",'')
t=t.replace('point1Unchanged:true','point1FormatUpdated:true').replace('punto 1 protegido','punto 1 incluido')
t=t.replace('s*d+(?:[.,]d+)?(?:s*%|s*[eE][+−-]?d+)?',r'\s*\d+(?:[.,]\d+)?(?:\s*%|\s*[eE][+−-]?\d+)?')
t=t.replace("snippet=", "css+='body h1,body label,body button,body figcaption{font-family:HydroDocumento,serif!important}'\nsnippet=")
(S/'77_unificar_html_fuente_original.py').write_text(t,encoding='utf-8')
for script in ['75_preparar_tablas_fuente_original.py','76_unificar_pdf_fuente_original.py','77_unificar_html_fuente_original.py']:
    if '--solo-preparar' not in sys.argv:subprocess.run([sys.executable,str(S/script)],check=True)

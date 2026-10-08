from pathlib import Path
import json
from playwright.sync_api import sync_playwright
import pymupdf as f
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';O=D/'revision_tablas'
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':1000});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((D/'informe_interactivo.html').as_uri())
    page.wait_for_function('window.verificacionFormato?.point1FormatUpdated === true')
    page.evaluate('document.fonts.ready')
    result=page.evaluate('''()=>({ ...window.verificacionFormato,
      point1Tables:document.querySelectorAll('#guia-punto-1 .tabla-hidro-unificada').length,
      styles:[1,2,3,4,5].map(n=>{let g=document.getElementById('guia-punto-'+n),p=g.querySelector('p'),h=g.querySelector('h3');return {point:n,font:getComputedStyle(p).fontFamily,body:getComputedStyle(p).fontSize,subtitle:getComputedStyle(h).fontSize}})
    })''')
    assert result['point1Tables']>0
    assert all(s['body']=='16px' and 'HydroDocumento' in s['font'] for s in result['styles'])
    assert not errors,errors
    for n in [1,2,5]:
        page.evaluate('(n)=>window.scrollTo(0,document.getElementById("guia-punto-"+n).getBoundingClientRect().top+window.scrollY)',n)
        page.screenshot(path=str(O/f'html_fuente_original_{n}.png'))
    page.locator('#guia-punto-1 table').first.screenshot(path=str(O/'html_tabla_punto1_fuente_original.png'))
    result['errors']=errors;(O/'verificacion_html_fuente_original.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    browser.close()
report=json.loads((O/'verificacion_pdf.json').read_text(encoding='utf-8'))
assert report['point1_format_updated'] and report['cover_unchanged']
assert report['tables']==64
d=f.open(O/'informe_formato_unificado.pdf')
for section in ['Series mensuales','Relaciones entre series','Análisis de frecuencias','Interpretación física e integración']:
    pn=next(p for l,t,p in d.get_toc() if section in t)
    d[pn-1].get_pixmap().save(O/f'fuente_original_{pn}.png')
pages=report['qa_pages']
for batch in range(0,len(pages),12):
    sheet=Image.new('RGB',(1200,4*440),'#cccccc');draw=ImageDraw.Draw(sheet)
    for pos,pn in enumerate(pages[batch:batch+12]):
        im=Image.open(O/f'qa_{pn}.png');im.thumbnail((390,410));x=(pos%3)*400;y=(pos//3)*440
        sheet.paste(im,(x,y+20));draw.text((x+5,y+2),f'PDF {pn}',fill='black')
    sheet.save(O/f'contacto_fuente_original_{batch//12+1}.png')
print(json.dumps({'pdf_pages':len(d),'pdf_tables':report['tables'],'html_tables':result['tables'],'point1_tables':result['point1Tables'],'html_errors':errors}))

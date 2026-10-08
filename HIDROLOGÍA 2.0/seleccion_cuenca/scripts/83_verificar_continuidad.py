from pathlib import Path
import json
import numpy as np
import pymupdf as f
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';O=D/'revision_continuidad'
report=json.loads((O/'verificacion_continuidad.json').read_text(encoding='utf-8'));bands=json.loads((O/'bandas.json').read_text());a=f.open(O/'informe_antes_compactacion.pdf');b=f.open(O/'informe_continuo.pdf');missing=[]
for pn in range(2,len(a)):
    p=a[pn]
    if p.rect.width>p.rect.height:continue
    pix=p.get_pixmap(colorspace=f.csGRAY);gray=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width);ink=(gray[:,35:pix.width-35]<244).sum(axis=1)>2;ink[:35]=False;ink[int(p.rect.height-47):]=False
    covered=np.zeros(pix.height,dtype=bool)
    for band in bands:
        if band['old_page']==pn:covered[max(0,int(band['y0'])):min(pix.height,int(np.ceil(band['y1'])))]=True
    if np.any(ink&~covered):missing.append(pn+1)
assert not missing,missing
report['all_visible_content_rows_preserved']=True
pages=report['qa_pages']
for batch in range(0,len(pages),6):
    sheet=Image.new('RGB',(1200,900),'#cccccc');draw=ImageDraw.Draw(sheet)
    for pos,pn in enumerate(pages[batch:batch+6]):
        im=Image.open(O/f'qa_{pn}.png');im.thumbnail((390,410));x=(pos%3)*400;y=(pos//3)*450;sheet.paste(im,(x,y+20));draw.text((x+5,y+2),f'PDF {pn}',fill='black')
    sheet.save(O/f'contacto_{batch//6+1}.png')
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1280,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((D/'informe_interactivo.html').as_uri());page.wait_for_function('window.verificacionClimatologia15?.tables === 5');page.evaluate('document.fonts.ready')
    styles=page.evaluate('''()=>[1,2,3,4,5].map(n=>{const g=document.getElementById('guia-punto-'+n),p=g.querySelector('p');return {point:n,margin:getComputedStyle(g).marginTop,body:getComputedStyle(p).fontSize,font:getComputedStyle(p).fontFamily}})''')
    assert all(s['margin']=='16px' and s['body']=='16px' and 'HydroDocumento' in s['font'] for s in styles) and not errors,(styles,errors)
    page.evaluate('window.scrollTo(0,document.getElementById("guia-punto-2").getBoundingClientRect().top+window.scrollY-220)');page.screenshot(path=str(O/'qa_html_continuidad.png'));browser.close()
    report['html_styles']=styles;report['html_errors']=errors
(O/'verificacion_continuidad_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'old_pages':len(a),'new_pages':len(b),'all_visible_content_rows_preserved':True,'html_errors':errors}))

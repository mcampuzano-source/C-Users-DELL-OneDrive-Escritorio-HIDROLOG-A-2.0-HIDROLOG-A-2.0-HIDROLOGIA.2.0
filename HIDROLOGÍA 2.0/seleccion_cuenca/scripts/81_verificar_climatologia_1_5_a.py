from pathlib import Path
import json
import pymupdf as f
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';O=D/'apartado_1_5'
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':1280,'height':1000});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)));page.goto((D/'informe_interactivo.html').as_uri());page.wait_for_function('window.verificacionClimatologia15?.tables === 5');page.evaluate('document.fonts.ready')
    result=page.evaluate('''()=>({...window.verificacionClimatologia15,text:document.getElementById('guia-1-5-a').innerText,oldPlaceholder:document.getElementById('guia-1-5').innerText.includes('esta reorganización'),imagesReady:Array.from(document.querySelectorAll('#guia-1-5-a img')).every(i=>i.complete&&i.naturalWidth>0),styles:{font:getComputedStyle(document.querySelector('#guia-1-5-a p')).fontFamily,body:getComputedStyle(document.querySelector('#guia-1-5-a p')).fontSize,table:getComputedStyle(document.querySelector('#guia-1-5-a td')).fontSize},otherSections:[2,3,4,5].map(n=>document.getElementById('guia-punto-'+n).innerText.length)})''')
    assert result['commonMonths']==285 and result['figures']==5 and result['imagesReady']
    assert result['styles']['body']=='16px' and result['styles']['table']=='14px'
    assert 'Pendiente' not in result['text'] and not result['oldPlaceholder']
    assert all(n>100 for n in result['otherSections']) and not errors
    page.evaluate('window.scrollTo(0,document.getElementById("guia-1-5").getBoundingClientRect().top+window.scrollY)');page.screenshot(path=str(O/'qa_html_1_5.png'))
    page.locator('#guia-1-5-a table').first.screenshot(path=str(O/'qa_html_tabla.png'));browser.close()
    result.pop('text');result['errors']=errors;(O/'verificacion_html.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
report=json.loads((O/'verificacion_integracion.json').read_text());d=f.open(O/'informe_actualizado_1_5.pdf');pages=list(range(report['section_start_pdf'],report['section_end_pdf']+1))
for pn in pages:
    text=d[pn-1].get_text();assert '\ufffd' not in text
for batch in range(0,len(pages),6):
    sheet=Image.new('RGB',(1200,900),'#cccccc');draw=ImageDraw.Draw(sheet)
    for pos,pn in enumerate(pages[batch:batch+6]):
        im=Image.open(O/f'qa_pdf_{pn}.png');im.thumbnail((390,410));x=(pos%3)*400;y=(pos//3)*450;sheet.paste(im,(x,y+20));draw.text((x+5,y+2),f'PDF {pn}',fill='black')
    sheet.save(O/f'qa_contacto_{batch//6+1}.png')
print(json.dumps({'pdf_pages':len(d),'section_pages':report['new_section_pages'],'html':result}))

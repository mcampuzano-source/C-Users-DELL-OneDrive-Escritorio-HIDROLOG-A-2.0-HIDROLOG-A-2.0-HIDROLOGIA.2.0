"""Renderiza la portada con los mismos HTML/CSS, sin cargar los análisis."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
OUT=DOCS/'revision_portada'
h=(DOCS/'informe_interactivo.html').read_text(encoding='utf-8')
preview=h[:h.index('<main>')]+'</body></html>'
results={}
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    for name,width,height in [('desktop',1280,1000),('movil',390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height})
        page.set_content(preview,wait_until='load')
        cover=page.locator('.portada-institucional')
        result=cover.evaluate('''el=>({textAlign:getComputedStyle(el).textAlign,
            width:el.getBoundingClientRect().width,overflow:el.scrollWidth>el.clientWidth,
            logoWidth:el.querySelector('.escudo').getBoundingClientRect().width,
            logoOverflow:getComputedStyle(el.querySelector('.escudo')).overflow,
            imageLoaded:el.querySelector('img').complete&&el.querySelector('img').naturalWidth>0})''')
        assert result['textAlign']=='center' and not result['overflow'] and result['imageLoaded']
        assert result['logoWidth']==148 and result['logoOverflow']=='hidden'
        cover.screenshot(path=str(OUT/('portada_'+name+'.png')))
        results[name]=result;page.close()
    browser.close()
(OUT/'verificacion_visual.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results),flush=True)

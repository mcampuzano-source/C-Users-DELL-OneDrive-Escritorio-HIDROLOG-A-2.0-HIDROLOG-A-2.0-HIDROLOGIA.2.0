"""Verifica fórmulas HTML, portada y protección de punto 1 en navegador real."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_formulas'
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':1000});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'Informe_Hidrologia_interactivo.html').as_uri(),wait_until='load',timeout=180000)
    try:page.wait_for_function('!!window.verificacionFormulas',timeout=15000)
    except Exception:print(json.dumps(errors,ensure_ascii=True));raise
    result=page.evaluate('window.verificacionFormulas')
    assert result['equations']==33
    assert result['point1Unchanged']
    assert page.locator('#guia-punto-1 .ecuacion-hidrologia').count()==0
    assert page.locator('.portada-institucional').evaluate('e=>getComputedStyle(e).textAlign')=='center'
    assert page.locator('#guia-5-4 #interpretacion-fisica-54').count()==1
    assert not errors,errors
    for n in ['2.5','2.8','3.4','4.1','5.3']:
        loc=page.locator('[data-ecuacion="'+n+'"]');loc.scroll_into_view_if_needed()
        assert loc.locator('img').evaluate('e=>e.complete&&e.naturalWidth>0')
        loc.screenshot(path=str(OUT/('html_'+n.replace('.','_')+'.png')))
    page.locator('#guia-2-2').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'html_2_2.png'))
    page.set_viewport_size({'width':390,'height':844})
    loc=page.locator('[data-ecuacion="2.8"]');loc.scroll_into_view_if_needed();loc.screenshot(path=str(OUT/'html_movil_2_8.png'))
    browser.close()
(OUT/'verificacion_html.json').write_text(json.dumps({'result':result,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))

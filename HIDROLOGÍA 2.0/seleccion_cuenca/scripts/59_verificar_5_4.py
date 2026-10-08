"""Verifica numerales, portada, gráficas y conclusiones en el HTML real."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'apartado_5_4'
errors=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':1000})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto((ROOT/'Informe_Hidrologia_interactivo.html').as_uri(),wait_until='load',timeout=180000)
    page.locator('#guia-5-4 #interpretacion-fisica-54').wait_for(timeout=30000)
    headings=page.locator('#guia-punto-5 > h2, #guia-punto-5 > div > h3').all_text_contents()
    assert headings[0].startswith('Punto 5.')
    assert all(headings[i].startswith(f'5.{i}.') for i in range(1,5))
    assert page.locator('.portada-institucional').evaluate("el=>getComputedStyle(el).textAlign")=='center'
    assert 'Pendiente de síntesis final' not in page.locator('#guia-conclusiones').inner_text()
    assert len(page.locator('#guia-conclusiones p').all_text_contents())==6
    plotinfo={}
    for id in ['ciclo_y_respuesta54','indice_NOAA_contraste54','dependencia_y_escalas54']:
        plot=page.locator('#'+id);plot.wait_for();page.wait_for_function('(id)=>!!document.getElementById(id).data',arg=id)
        plotinfo[id]=plot.evaluate('el=>({traces:el.data.length,width:el.getBoundingClientRect().width})')
        assert plotinfo[id]['traces']>=3
        plot.scroll_into_view_if_needed();plot.screenshot(path=str(OUT/(id+'_navegador.png')))
    page.locator('#guia-5-4 > h3').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'encabezado_5_4_navegador.png'))
    browser.close()
assert not errors,errors
result={'headings':headings,'portada_centered':True,'content_5_4_correctly_nested':True,'conclusions_present':True,'plots':plotinfo,'page_errors':errors}
(OUT/'verificacion_html.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)

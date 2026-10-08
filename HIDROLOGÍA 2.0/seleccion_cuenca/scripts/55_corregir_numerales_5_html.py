"""Restaura el número del punto 5 y verifica el agrupador real en Edge."""
from pathlib import Path
import re,json,shutil
import argparse

DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
ROOT=DOCS.parents[3];OUT=DOCS/'revision_numerales_5';OUT.mkdir(exist_ok=True)
p=DOCS/'informe_interactivo.html';h=p.read_text(encoding='utf-8')
backup=OUT/'antes_correccion.html'
if not backup.exists():shutil.copy2(p,backup)
bad="for(const [n,title,titles] of [[,'Mapas de correlación"
good="for(const [n,title,titles] of [[5,'Mapas de correlación"
if bad in h:
    assert h.count(bad)==1;h=h.replace(bad,good,1)
else:assert good in h
old='Punto 5</a></p>'
new='Punto 5</a></p><p><a href="#guia-5-1">5.1 Campos climáticos</a> · <a href="#guia-5-2">5.2 Mapas mensuales</a> · <a href="#guia-5-3">5.3 Robustez</a> · <a href="#guia-5-4">5.4 Interpretación física</a></p>'
if 'href="#guia-5-1"' not in h:
    assert old in h;h=h.replace(old,new,1)
assert "of [[,'Mapas" not in h
p.write_text(h,encoding='utf-8');shutil.copy2(p,ROOT/'Informe_Hidrologia_interactivo.html')
print('Número 5 y enlaces 5.1-5.4 restaurados.',flush=True)

if '--verify' in __import__('sys').argv:
    from playwright.sync_api import sync_playwright
    result={};errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((ROOT/'Informe_Hidrologia_interactivo.html').as_uri(),wait_until='load',timeout=180000)
        page.locator('#guia-punto-5').wait_for(timeout=30000)
        result['headings']=page.locator('#guia-punto-5 > h2, #guia-punto-5 > div > h3').all_text_contents()
        assert result['headings'][0].startswith('Punto 5.')
        assert all(result['headings'][i].startswith(f'5.{i}.') for i in range(1,5))
        for num,child in [(1,'seleccion-campos-51'),(2,'mapas-mensuales-52'),(3,'robustez-patrones-53')]:
            assert page.locator(f'#guia-5-{num} #{child}').count()==1
        assert page.locator('a[href="#guia-5-3"]').count()>=1
        assert 'Pendiente' in page.locator('#guia-5-4').inner_text()
        assert 'undefined.' not in page.locator('#guia-punto-5').inner_text()
        page.locator('#guia-punto-5 > h2').scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/'punto_5_navegador.png'))
        result['content_correctly_nested']=True;result['page_errors']=errors
        browser.close()
    (OUT/'verificacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

"""Comprueba apertura offline, datos, zoom y restablecimiento en Edge headless."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
errors=[]
network=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    context=browser.new_context(offline=True,viewport={'width':1400,'height':1100})
    page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('request',lambda request:network.append(request.url) if request.url.startswith(('http:','https:')) else None)
    page.goto((DOC/'informe_interactivo.html').as_uri())
    page.wait_for_function("document.getElementById('series-mensuales')._fullLayout !== undefined")
    counts=page.evaluate("""() => document.getElementById('series-mensuales').data.filter(t=>t.mode==='lines').map(t=>({n:t.y.length,nulls:t.y.filter(x=>x===null).length,connectgaps:t.connectgaps}))""")
    assert all(t['n']==504 and t['nulls']==19 and not t['connectgaps'] for t in counts),counts
    page.evaluate("""async()=>{await Plotly.relayout('series-mensuales',{'xaxis2.range':['2010-01-01','2012-01-01']});} """)
    ranges=page.evaluate("""()=>{let g=document.getElementById('series-mensuales');return [g._fullLayout.xaxis.range,g._fullLayout.xaxis2.range]}""")
    assert ranges[0]==ranges[1],ranges
    page.get_by_role('button',name='Ver todo el periodo').click()
    reset=page.evaluate("()=>document.getElementById('series-mensuales')._fullLayout.xaxis.range")
    assert reset[0].startswith('1981') and reset[1].startswith('2023'),reset
    if page.locator('#control-faltantes').count():
        page.wait_for_function("document.getElementById('control-faltantes')._fullLayout !== undefined")
        assert page.locator('#tabla-faltantes tbody tr').count()==19
        page.locator('#buscar-mes').fill('2011')
        assert page.locator('#tabla-faltantes tbody tr:visible').count()==4
        page.locator('#buscar-mes').fill('')
    page.screenshot(path=str(DOC/'verificacion_interactivo.png'),full_page=True)
    if page.locator('#cobertura-mensual-cronologica').count():
        page.wait_for_function("document.getElementById('cobertura-mensual-cronologica')._fullLayout !== undefined")
        coverage=page.evaluate("()=>document.getElementById('cobertura-mensual-cronologica').data[0].y")
        assert len(coverage)==504 and coverage.count(100)==485 and coverage.count(0)==6
        page.locator('#grafica-cobertura').screenshot(path=str(DOC/'verificacion_cobertura.png'))
    for graph_id in ['temperaturas-mensuales','dispersion-chirps-q','mapa-estaciones','mapa-relieve','histogramas-completos']:
        page.wait_for_function('(id) => document.getElementById(id)._fullLayout !== undefined',arg=graph_id)
    temperatures=page.evaluate("() => document.getElementById('temperaturas-mensuales').data.map(t => t.y.filter(v => v !== null).length)")
    assert temperatures==[485,485,485],temperatures
    histograms=page.evaluate("() => document.getElementById('histogramas-completos').data.map(t => ({n:t.customdata.reduce((a,b)=>a+b[2],0),percent:t.y.reduce((a,b)=>a+b,0)}))")
    assert len(histograms)==6 and all(h['n']==485 and abs(h['percent']-100)<1e-8 for h in histograms),histograms
    page.locator('#histogramas-completos').screenshot(path=str(DOC/'verificacion_histogramas.png'))
    assert not errors,errors
    assert not network,network
    (DOC/'verificacion_interactivo.json').write_text(json.dumps({'offline':True,'trazas':counts,'zoom_sincronizado':True,'restablecimiento':reset,'errores_js':errors,'peticiones_http':network},indent=2),encoding='utf-8')
    browser.close()
print('HTML verificado sin conexion: datos, 19 vacios, zoom sincronizado y restablecimiento.')

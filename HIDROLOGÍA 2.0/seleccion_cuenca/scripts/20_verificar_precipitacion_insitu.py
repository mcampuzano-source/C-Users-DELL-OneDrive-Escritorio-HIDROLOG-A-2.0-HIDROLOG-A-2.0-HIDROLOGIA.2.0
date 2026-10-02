"""Consulta pública IDEAM: existencia de registros, sin confundirlos con series diarias."""
from pathlib import Path
import urllib.request, urllib.parse, json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'la_vieja'/'estaciones_insitu'; OUT.mkdir(exist_ok=True)
inv=pd.read_csv(ROOT/'resultados'/'estaciones_dentro_cuencas.csv',dtype={'codigo':str})
inv=inv[(inv.cuenca_codigo==26127040)&inv.lluvia_por_categoria]
codes=sorted(set(inv.codigo))
where='codigoestacion in ('+','.join("'"+c+"'" for c in codes)+')'
params={'$where':where,'$select':'codigoestacion,nombreestacion,count(*) as n_registros,min(fechaobservacion) as inicio,max(fechaobservacion) as fin','$group':'codigoestacion,nombreestacion','$limit':1000}
url='https://www.datos.gov.co/resource/s54a-sgyg.json?'+urllib.parse.urlencode(params)
try:
    with urllib.request.urlopen(url,timeout=90) as response:
        data=json.load(response)
    (OUT/'inventario_registros_publicos.json').write_text(json.dumps({'url':url,'resultados':data,'alcance':'Conteo y fechas del portal; no verifica continuidad, unidades acumulativas, duplicados ni calidad'},indent=2,ensure_ascii=False),encoding='utf-8')
    pd.DataFrame(data).to_csv(OUT/'inventario_registros_publicos.csv',index=False,encoding='utf-8-sig')
    print(pd.DataFrame(data).to_string(index=False))
    if data:
        params={'$where':"codigoestacion='"+data[0]['codigoestacion']+"'",'$limit':20,'$order':'fechaobservacion DESC'}
        with urllib.request.urlopen('https://www.datos.gov.co/resource/s54a-sgyg.json?'+urllib.parse.urlencode(params),timeout=60) as response:
            sample=json.load(response)
        (OUT/'muestra_registros_originales.json').write_text(json.dumps(sample,indent=2,ensure_ascii=False),encoding='utf-8')
        print('Muestra original guardada: NO agregada a mensual; revisar definición temporal del sensor.')
except Exception as error:
    (OUT/'error_consulta.json').write_text(json.dumps({'url':url,'error':str(error)},indent=2),encoding='utf-8')
    raise

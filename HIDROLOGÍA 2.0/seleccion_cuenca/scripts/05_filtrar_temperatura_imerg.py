"""Filtro de ocho candidatas: temperatura real de CAMELS y cobertura catalogada IMERG.
No confundir cobertura de catalogo con precipitacion extraida y validada.
"""
from pathlib import Path
import io
import json
import math
import urllib.parse
import urllib.request
import zipfile
import pandas as pd
import shapefile
from pyproj import CRS, Transformer, Geod
from shapely.geometry import shape, mapping, box
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
D, R = ROOT/'datos', ROOT/'resultados'
tabla = pd.read_csv(R/'cuencas_recomendadas_estacion_insitu.csv')
candidatas = tabla[tabla['area'].between(100, 10000)].copy()
revision = pd.read_csv(R/'revision_todas_cuencas.csv')
periodo = revision[revision.periodo.eq('1998_2022')].set_index('gauge_id')
calendario = pd.date_range('1998-01-01','2022-12-31',freq='D')
geod = Geod(ellps='WGS84')
collection = 'C2723754851-GES_DISC'
features, results, weights = [], [], []

with zipfile.ZipFile(D/'03_CAMELS_COL_Basin_boundary.zip') as boundaries, zipfile.ZipFile(D/'04_CAMELS_COL_Hydrometeorological_data.zip') as series:
    base='03_CAMELS_COL_Basin_boundary/CAMELS_COL_catchments_boundaries'
    crs=CRS.from_wkt(boundaries.read(base+'.prj').decode())
    to_lonlat=Transformer.from_crs(crs,4326,always_xy=True)
    reader=shapefile.Reader(**{ext:io.BytesIO(boundaries.read(base+'.'+ext)) for ext in ['shp','shx','dbf']})
    polygons={int(s.record['IDEAM_CODE']):transform(to_lonlat.transform,shape(s.shape.__geo_interface__)) for s in reader.iterShapeRecords()}
    for _, candidate in candidatas.iterrows():
        code=int(candidate.gauge_id)
        info=periodo.loc[code]
        name=next(n for n in series.namelist() if str(code) in n)
        daily=pd.read_csv(io.BytesIO(series.read(name)),sep='\t')
        daily['Fecha']=pd.to_datetime(daily.Fecha,format='%d/%m/%Y')
        if daily.Fecha.duplicated().any():
            raise ValueError(f'Fechas duplicadas: {code}')
        daily=daily.set_index('Fecha').reindex(calendario)
        temperatures=daily[['Temperatura_minima','Temperatura_maxima']]
        temp_present=temperatures.notna().all(axis=1)
        temp_inverted=int((temperatures.Temperatura_minima>temperatures.Temperatura_maxima).sum())
        poly=polygons[code]
        if not poly.is_valid:
            raise ValueError(f'Geometria invalida {code}; revisar sin corregir silenciosamente')
        features.append({'type':'Feature','properties':{'gauge_id':code,'estacion':candidate.nombre},'geometry':mapping(poly)})
        west,south,east,north=poly.bounds
        params={'collection_concept_id':collection,'temporal':'1998-01-01T00:00:00Z,2022-12-31T23:59:59Z','bounding_box':f'{west},{south},{east},{north}','page_size':400,'sort_key':'start_date'}
        url='https://cmr.earthdata.nasa.gov/search/granules.json?'+urllib.parse.urlencode(params)
        with urllib.request.urlopen(url,timeout=60) as response:
            payload=json.load(response)
            hits=int(response.headers.get('CMR-Hits','0'))
        (D/f'imerg_catalogo_{code}.json').write_text(json.dumps({'url':url,'hits':hits,'response':payload},indent=2),encoding='utf-8')
        entries=payload['feed']['entry']
        months={e['time_start'][:7] for e in entries}
        expected=set(pd.period_range('1998-01','2022-12',freq='M').astype(str))
        total_area=0
        cell_list=[]
        # Malla nominal IMERG 0.1 grados: pesos geodesicos preliminares.
        # Se debe contrastar contra coordenadas reales del archivo al descargarlo.
        for ix in range(math.floor((west+180)*10),math.ceil((east+180)*10)):
            for iy in range(math.floor((south+90)*10),math.ceil((north+90)*10)):
                left,bottom=-180+ix/10,-90+iy/10
                part=poly.intersection(box(left,bottom,left+.1,bottom+.1))
                if part.is_empty or part.area<=0:
                    continue
                area=abs(geod.geometry_area_perimeter(part)[0])/1e6
                if area<=0:
                    continue
                cell_list.append({'gauge_id':code,'lon_centro':left+.05,'lat_centro':bottom+.05,'area_interseccion_km2':area})
                total_area+=area
        for cell in cell_list:
            cell['peso_area']=cell['area_interseccion_km2']/total_area
        weights.extend(cell_list)
        result={'codigo':code,'estacion':candidate.nombre,'area_camels_km2':candidate.area,'lat_estacion':info.latitud,'lon_estacion':info.longitud,'periodo':'1998-2022','faltantes_T_pct':100*(1-temp_present.mean()),'dias_Tmin_mayor_Tmax':temp_inverted,'temperatura':'Tmin/Tmax MSWX, promedio de cuenca; no Tmedia observada','meses_PQ_completos':int(info.meses_completos_PQ),'meses_IMERG_catalogados':len(months & expected),'cobertura_IMERG_catalogo_completa':expected.issubset(months),'celdas_nominales_intersectadas':len(cell_list),'area_geodesica_poligono_km2':total_area,'precipitacion_IMERG_extraida':False,'cumple_preseleccion':bool(expected.issubset(months) and temp_present.mean()>=.9 and temp_inverted==0 and info.cumple_filtro)}
        results.append(result)
        print(f'{code}: T faltante {result["faltantes_T_pct"]:.2f}%; IMERG {len(months & expected)}/300 meses catalogados; {len(cell_list)} celdas intersectadas.',flush=True)

summary=pd.DataFrame(results)
summary.to_csv(R/'filtro_8_temperatura_imerg.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(weights).to_csv(R/'pesos_preliminares_malla_imerg.csv',index=False)
(R/'ocho_cuencas_wgs84.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False),encoding='utf-8')
with pd.ExcelWriter(ROOT/'Filtro_8_cuencas_IMERG.xlsx',engine='openpyxl') as writer:
    summary.to_excel(writer,sheet_name='Filtro 8 cuencas',index=False)
    pd.DataFrame(weights).to_excel(writer,sheet_name='Pesos espaciales preliminares',index=False)
    pd.DataFrame({'Notas':[
        'IMERG proporciona precipitacion, no temperatura del aire. Temperatura disponible: Tmin/Tmax de MSWX en CAMELS.',
        'Periodo comun revisado: 1998-2022, 25 anos. Se cuentan los dias omitidos sin rellenar.',
        'IMERG: presencia mensual en catalogo espacial NASA CMR; no son valores descargados ni validacion de pixeles.',
        'Se dispone del poligono completo para calcular lluvia de cuenca; no sustituir por el pixel de estacion en el informe.',
        'Pesos preliminares: interseccion de poligonos con malla nominal 0.1 grados y areas geodesicas WGS84. Verificar malla con archivo real.',
        'La temperatura media mensual requiere fuente directa o justificar estimacion con Tmin/Tmax.',
        'Fuentes: https://doi.org/10.5281/zenodo.18794895 y https://cmr.earthdata.nasa.gov/',
    ]}).to_excel(writer,sheet_name='Leer primero',index=False)
    for sheet in writer.book:
        sheet.freeze_panes='A2'
        sheet.auto_filter.ref=sheet.dimensions
        for c in sheet[1]:
            sheet.column_dimensions[c.column_letter].width=25
print('Guardado:',ROOT/'Filtro_8_cuencas_IMERG.xlsx')

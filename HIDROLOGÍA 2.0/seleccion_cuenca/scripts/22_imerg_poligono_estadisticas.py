"""Extrae los 300 meses IMERG V07B y añade 1.2/1.3 sin sustituir antecedentes.

Ejecutar desde cualquier directorio. No modifica HDF5 ni tablas anteriores.
Después ejecutar 21_ordenar_informes.py para compilar el PDF y ordenar el HTML.
"""
from pathlib import Path
import calendar
import hashlib
import importlib.metadata
import json
import re

import h5py
import numpy as np
import pandas as pd
from pyproj import Geod
from shapely.geometry import shape, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
DOC = ROOT / 'la_vieja/documentos'
OUT = DOC / 'imerg_poligono'
FIG = DOC / 'latex/figuras'
GEOD = Geod(ellps='WGS84')
POLYGON_PATH = ROOT / 'la_vieja/topografia/cuenca_la_vieja.geojson'
LABELS = {'P_CHIRPS_mm': ('CHIRPS', 'mm/mes'), 'P_IMERG_poligono_mm': ('IMERG polígono', 'mm/mes'), 'Q_m3_s': ('Caudal Q', 'm³/s'), 'R_mm': ('Escorrentía R', 'mm/mes'), 'Tmedia_ERA5_Land_C': ('ERA5-Land Tmedia', '°C')}


def area(g):
    if g.is_empty:
        return 0.0
    if g.geom_type == 'Polygon':
        # Los límites de celda son paralelos/meridianos. Segmentizar evita
        # aproximar un borde de 0,1° por un único arco geodésico.
        return abs(GEOD.geometry_area_perimeter(orient(g.segmentize(0.001), sign=1))[0])
    return sum(area(part) for part in g.geoms)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def decode(v):
    return v.decode() if isinstance(v, bytes) else str(v)


def extract():
    paths = sorted(list((WORKSPACE / 'GPM_3IMERGM_07').glob('*.HDF5')) + list(WORKSPACE.glob('*.HDF5')))
    months = {}
    for p in paths:
        m = re.fullmatch(r'3B-MO\.MS\.MRG\.3IMERG\.(\d{6})01-S000000-E235959\.\d{2}\.V07B\.HDF5', p.name)
        if m:
            if m[1] in months:
                raise ValueError('Mes duplicado: ' + m[1])
            months[m[1]] = p
    expected = pd.date_range('1998-01-01', '2022-12-01', freq='MS')
    assert set(months) == set(expected.strftime('%Y%m')), 'Meses ausentes o adicionales'
    polygon = unary_union([shape(f['geometry']) for f in json.loads(POLYGON_PATH.read_text(encoding='utf-8'))['features']])
    assert polygon.is_valid
    with h5py.File(months['199801'], 'r') as f:
        lat = f['Grid/lat'][:]
        lon = f['Grid/lon'][:]
        lb = f['Grid/lat_bnds'][:]
        ob = f['Grid/lon_bnds'][:]
    # Los bounds float32 del original se solapan unos metros por redondeo.
    # Reconstruir límites contiguos de la malla nominal 0,1°, sin remuestrear P.
    lat_edges = np.linspace(round(float(lat[0]), 2) - .05, round(float(lat[-1]), 2) + .05, len(lat) + 1)
    lon_edges = np.linspace(round(float(lon[0]), 2) - .05, round(float(lon[-1]), 2) + .05, len(lon) + 1)
    spatial_lb = np.column_stack([lat_edges[:-1], lat_edges[1:]])
    spatial_ob = np.column_stack([lon_edges[:-1], lon_edges[1:]])
    assert np.allclose(lb, spatial_lb, atol=2e-5, rtol=0)
    assert np.allclose(ob, spatial_ob, atol=2e-5, rtol=0)
    assert np.allclose(lat, spatial_lb.mean(axis=1), atol=2e-5, rtol=0)
    assert np.allclose(lon, spatial_ob.mean(axis=1), atol=2e-5, rtol=0)
    west, south, east, north = polygon.bounds
    records, cells = [], []
    for i in np.flatnonzero((spatial_ob[:, 1] > west) & (spatial_ob[:, 0] < east)):
        for j in np.flatnonzero((spatial_lb[:, 1] > south) & (spatial_lb[:, 0] < north)):
            cell = box(float(spatial_ob[i, 0]), float(spatial_lb[j, 0]), float(spatial_ob[i, 1]), float(spatial_lb[j, 1]))
            intersection = polygon.intersection(cell)
            a = area(intersection)
            if a > 0:
                cells.append(cell)
                records.append({'lon_index': int(i), 'lat_index': int(j), 'lon': float(lon[i]), 'lat': float(lat[j]), 'west': cell.bounds[0], 'east': cell.bounds[2], 'south': cell.bounds[1], 'north': cell.bounds[3], 'west_original_float32': float(ob[i, 0]), 'east_original_float32': float(ob[i, 1]), 'south_original_float32': float(lb[j, 0]), 'north_original_float32': float(lb[j, 1]), 'interseccion_m2': a, 'fraccion_celda': a / area(cell)})
    weights = pd.DataFrame(records)
    weights['peso'] = weights.interseccion_m2 / weights.interseccion_m2.sum()
    uncovered = area(polygon.difference(unary_union(cells)))
    assert uncovered / area(polygon) < 1e-8, 'El recorte no cubre todo el polígono'
    assert np.isclose(weights.peso.sum(), 1)
    assert abs(weights.interseccion_m2.sum() / area(polygon) - 1) < 1e-6
    weights.to_csv(OUT / 'pesos_celdas.csv', index=False)
    rows, manifest, values = [], [], []
    imin, imax = weights.lon_index.min(), weights.lon_index.max()
    jmin, jmax = weights.lat_index.min(), weights.lat_index.max()
    for n, date in enumerate(expected):
        p = months[date.strftime('%Y%m')]
        with h5py.File(p, 'r') as f:
            header = decode(f.attrs['FileHeader'])
            assert 'ProductVersion=V07B;' in header and f'StartGranuleDateTime={date:%Y-%m}-01' in header
            assert np.array_equal(f['Grid/lat'][:], lat) and np.array_equal(f['Grid/lon'][:], lon)
            assert np.array_equal(f['Grid/lat_bnds'][:], lb) and np.array_equal(f['Grid/lon_bnds'][:], ob)
            ds = f['Grid/precipitation']
            assert ds.shape == (1, len(lon), len(lat))
            assert decode(ds.attrs['units']) == 'mm/hr'
            sub = ds[0, imin:imax + 1, jmin:jmax + 1]
            rain = np.array([sub[r.lon_index - imin, r.lat_index - jmin] for r in weights.itertuples()], dtype=float)
            valid = np.isfinite(rain) & (rain >= 0) & (rain != float(ds.attrs['_FillValue']))
            hours = calendar.monthrange(date.year, date.month)[1] * 24
            # No renormalización de pesos si alguna celda está ausente.
            mm = float(np.dot(rain, weights.peso) * hours) if valid.all() else np.nan
            assert np.isclose(mm, sum(float(v) * float(w) * hours for v, w in zip(rain, weights.peso))) if valid.all() else True
            values.append(rain)
            rows.append({'mes': date, 'P_IMERG_poligono_mm': mm, 'tasa_media_mm_h': mm / hours, 'horas_mes': hours, 'celdas_validas': int(valid.sum()), 'celdas_totales': len(weights), 'cobertura_area_pct': float(weights.loc[valid, 'peso'].sum() * 100)})
        manifest.append({'mes': date.strftime('%Y-%m'), 'archivo': str(p.relative_to(WORKSPACE)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
        if (n + 1) % 50 == 0:
            print(f'Verificados {n + 1}/300 meses', flush=True)
    series = pd.DataFrame(rows)
    series.to_csv(OUT / 'IMERG_mensual_poligono_1998_2022.csv', index=False)
    pd.DataFrame(manifest).to_csv(OUT / 'manifest_archivos.csv', index=False)
    np.savez_compressed(OUT / 'precipitacion_celdas_mm_h.npz', precipitation=np.array(values), lat=weights.lat.to_numpy(), lon=weights.lon.to_numpy(), weights=weights.peso.to_numpy(), dates=expected.strftime('%Y-%m').to_numpy(dtype=str))
    assert abs(weights.interseccion_m2.sum() / area(polygon) - 1) < 1e-6
    metadata = {'producto': 'GPM_3IMERGM', 'version': 'V07B', 'modalidad': 'Final Run', 'doi': '10.5067/GPM/IMERG/3B-MONTH/07', 'variable': 'Grid/precipitation', 'unidades_originales': 'mm/hr', 'conversion': 'tasa media mensual × 24 × días del mes calendario', 'periodo': '1998-01 a 2022-12', 'archivos': len(manifest), 'meses_validos': int(series.P_IMERG_poligono_mm.notna().sum()), 'resolucion_grados': 0.1, 'poligono': str(POLYGON_PATH.relative_to(WORKSPACE)), 'sha256_poligono': sha(POLYGON_PATH), 'area_poligono_geodesica_km2': area(polygon) / 1e6, 'suma_intersecciones_km2': float(weights.interseccion_m2.sum() / 1e6), 'celdas_intersectadas': len(weights), 'celdas_borde': int((weights.fraccion_celda < 0.999999).sum()), 'cobertura_espacial_pct': 100 * (1 - uncovered / area(polygon)), 'metodo': 'Intersección geométrica con límites de celda del HDF5; áreas geodésicas WGS84, bordes segmentizados a máximo 0,001°; peso = área de intersección / suma de áreas de intersección', 'faltantes': 'Mes excluido si alguna celda intersectada es inválida; no relleno ni renormalización', 'acceso': 'Archivos originales GES DISC mediante CMR y script download_files_GPM_3IMERGM_07.py; sesión Earthdata sin credenciales en los artefactos', 'alcance': 'No modifica el área CAMELS utilizada para R. Conserva el promedio Giovanni de caja como antecedente separado.', 'versiones': {'h5py': h5py.__version__, 'numpy': np.__version__, 'pandas': pd.__version__}}
    metadata['limites_celdas'] = 'Límites contiguos reconstruidos sobre malla nominal 0,1° para evitar solapes/huecos del redondeo float32 de lat_bnds/lon_bnds; desviación máxima permitida 0,00002°. Límites originales y reconstruidos conservados en pesos_celdas.csv. No se remuestrea ni modifica precipitación.'
    (OUT / 'metadatos.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return series, metadata


def statistics(frame, scope):
    rows = []
    for key, (label, unit) in LABELS.items():
        s = frame[key].dropna()
        q = s.quantile([.05, .1, .25, .5, .75, .9, .95], interpolation='linear')
        rows.append({'muestra': scope, 'variable': label, 'unidad': unit, 'inicio': s.index.min().strftime('%Y-%m'), 'fin': s.index.max().strftime('%Y-%m'), 'n': len(s), 'media': s.mean(), 'mediana': s.median(), 'sd': s.std(ddof=1), 'minimo': s.min(), 'maximo': s.max(), 'rango': s.max() - s.min(), 'Q1': q[.25], 'Q2': q[.5], 'Q3': q[.75], 'IQR': q[.75] - q[.25], 'P5': q[.05], 'P10': q[.1], 'P90': q[.9], 'P95': q[.95], 'ceros': int((s == 0).sum()), 'mes_minimo': s.idxmin().strftime('%Y-%m'), 'mes_maximo': s.idxmax().strftime('%Y-%m')})
    return pd.DataFrame(rows)


def report(series, meta):
    meta['limites_celdas'] = 'Límites contiguos reconstruidos sobre malla nominal 0,1° para evitar solapes/huecos del redondeo float32 de lat_bnds/lon_bnds; desviación máxima permitida 0,00002°. Límites originales y reconstruidos conservados en pesos_celdas.csv. No se remuestrea ni modifica precipitación.'
    meta['versiones'].update({name: importlib.metadata.version(name) for name in ['shapely', 'pyproj', 'matplotlib', 'plotly', 'openpyxl', 'Jinja2']})
    (OUT / 'metadatos.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'requirements.txt').write_text('\n'.join(name+'=='+version for name, version in meta['versiones'].items())+'\n', encoding='utf-8')
    source = pd.read_csv(DOC / 'datos_graficados.csv', parse_dates=['mes']).set_index('mes').rename(columns={'P_mm': 'P_CHIRPS_mm'})
    era = pd.read_csv(DOC / 'temperatura_media_ERA5_Land_mensual.csv', parse_dates=['mes']).set_index('mes')
    data = source.join(era[['Tmedia_ERA5_Land_C']]).join(series.set_index('mes')[['P_IMERG_poligono_mm']])
    common = data[list(LABELS)].dropna()
    assert len(common) == 285
    assert len(data) == 504
    data.to_csv(OUT / 'series_alineadas.csv')
    common.to_csv(OUT / 'meses_comunes_285.csv')
    fullstats, commonstats = statistics(data, 'Registro disponible por fuente'), statistics(common, 'Mismos 285 meses válidos')
    fullstats.to_csv(OUT / 'estadisticos_registros.csv', index=False)
    commonstats.to_csv(OUT / 'estadisticos_periodo_comun.csv', index=False)
    with pd.ExcelWriter(OUT / 'Punto_1_2_y_1_3.xlsx') as writer:
        data.to_excel(writer, sheet_name='Series alineadas')
        common.to_excel(writer, sheet_name='285 meses comunes')
        fullstats.to_excel(writer, sheet_name='Registros completos', index=False)
        commonstats.to_excel(writer, sheet_name='Estadisticos comunes', index=False)
        pd.read_csv(OUT / 'pesos_celdas.csv').to_excel(writer, sheet_name='Pesos espaciales', index=False)
    # Series: no se cambia ninguna figura histórica.
    period = data.loc['1998':'2022']
    fig, axes = plt.subplots(5, 1, figsize=(11, 11), sharex=True)
    pf = make_subplots(rows=5, cols=1, shared_xaxes=True, subplot_titles=[LABELS[k][0] for k in LABELS], vertical_spacing=.06)
    colors = ['#23769b', '#bf5b45', '#206c44', '#6b5291', '#a3344b']
    for n, (key, (label, unit)) in enumerate(LABELS.items()):
        v = period[key]
        axes[n].plot(v.index, v, color=colors[n], lw=.8)
        axes[n].set_ylabel(unit)
        axes[n].set_title(label, loc='left', fontsize=10)
        pf.add_trace(go.Scatter(x=v.index.strftime('%Y-%m-%d').tolist(), y=[float(x) if pd.notna(x) else None for x in v], name=label, mode='lines', connectgaps=False, line={'color': colors[n]}, hovertemplate='%{x|%Y-%m}<br>%{y:.2f} '+unit+'<extra></extra>'), row=n + 1, col=1)
        pf.update_yaxes(title_text=unit, row=n + 1, col=1)
    axes[-1].set_xlabel('Año');fig.tight_layout()
    fig.savefig(FIG / 'imerg_poligono_series.pdf');plt.close(fig)
    pf.update_layout(height=1050, showlegend=False, title='Fuentes separadas, 1998–2022; vacíos conservados')
    series_html = pf.to_html(full_html=False, include_plotlyjs=False, div_id='imerg-poligono-series', config={'responsive': True, 'displaylogo': False})
    rain_edges = np.histogram_bin_edges(np.concatenate([common.P_CHIRPS_mm, common.P_IMERG_poligono_mm]), bins='fd')
    histogram = make_subplots(rows=3, cols=2, subplot_titles=[v[0] for v in LABELS.values()])
    boxes = make_subplots(rows=3, cols=2, subplot_titles=[v[0] for v in LABELS.values()])
    fig_h, ah = plt.subplots(3, 2, figsize=(11, 10));fig_b, ab = plt.subplots(3, 2, figsize=(11, 10))
    edges_metadata = {}
    for n, (key, (label, unit)) in enumerate(LABELS.items()):
        s = common[key]
        edges = rain_edges if key.startswith('P_') else np.histogram_bin_edges(s, bins='fd')
        counts, _ = np.histogram(s, bins=edges)
        pct = counts / len(s) * 100
        assert counts.sum() == len(s) and np.isclose(pct.sum(), 100)
        edges_metadata[key] = {'bordes': edges.tolist(), 'conteos': counts.tolist(), 'n': len(s)}
        centers = (edges[:-1] + edges[1:]) / 2
        widths = np.diff(edges)
        row, col = n // 2 + 1, n % 2 + 1
        histogram.add_trace(go.Bar(x=centers.tolist(), y=pct.tolist(), width=widths.tolist(), marker_color=colors[n], name=label, customdata=counts.tolist(), hovertemplate='%{x:.2f}<br>%{y:.2f}%<br>Meses: %{customdata}<extra></extra>'), row=row, col=col)
        boxes.add_trace(go.Box(y=s.tolist(), name=label, quartilemethod='linear', boxmean=True, marker_color=colors[n], boxpoints='outliers'), row=row, col=col)
        histogram.update_xaxes(title_text=unit, row=row, col=col);histogram.update_yaxes(title_text='Meses (%)', row=row, col=col)
        boxes.update_yaxes(title_text=unit, row=row, col=col)
        ah.flat[n].bar(centers, pct, width=widths, color=colors[n], edgecolor='white');ah.flat[n].set(title=label, xlabel=unit, ylabel='Meses (%)')
        ab.flat[n].boxplot(s, whis=1.5, showmeans=True);ab.flat[n].set(title=label, ylabel=unit)
    ah.flat[-1].axis('off');ab.flat[-1].axis('off')
    for f, filename in [(fig_h, 'imerg_poligono_histogramas.pdf'), (fig_b, 'imerg_poligono_cajas.pdf')]:
        f.suptitle('Mismos 285 meses completos, 1998–2022');f.tight_layout();f.savefig(FIG / filename);plt.close(f)
    (OUT / 'clases_histogramas.json').write_text(json.dumps(edges_metadata, indent=2), encoding='utf-8')
    chart_html = ''
    for f, id in [(histogram, 'imerg-poligono-histogramas'), (boxes, 'imerg-poligono-cajas')]:
        f.update_layout(height=950, showlegend=False, title='Mismos 285 meses completos: fuentes identificadas')
        chart_html += f.to_html(full_html=False, include_plotlyjs=False, div_id=id, config={'responsive': True, 'displaylogo': False})
    weights = pd.read_csv(OUT / 'pesos_celdas.csv')
    proof = series.iloc[0]
    method = f'''Actualización del 4 de octubre de 2026. IMERG Final Run V07B (GPM_3IMERGM), variable Grid/precipitation, malla de 0,1°. Se verificaron 300 archivos mensuales de enero de 1998 a diciembre de 2022. El promedio se calcula sobre el polígono CAMELS de La Vieja con {len(weights)} celdas intersectadas, {meta['celdas_borde']} de borde, ponderadas por el área geodésica WGS84 de su intersección. Cobertura espacial {meta['cobertura_espacial_pct']:.6f}%. Área geodésica del polígono {meta['area_poligono_geodesica_km2']:.2f} km²; el área CAMELS de 2797,19 km² usada para R permanece sin cambios. Las tasas originales están en mm/h y se multiplican por las horas de cada mes, incluidos los bisiestos. No se rellenan celdas ni se renormalizan pesos cuando faltan valores. Hay {meta['meses_validos']}/300 meses válidos y 285 meses completos comunes con CHIRPS y Q. Enero de 1998: {proof.tasa_media_mm_h:.8f} mm/h × 744 h = {proof.P_IMERG_poligono_mm:.6f} mm/mes; se comprobó también la suma independiente celda por celda. El promedio Giovanni de caja y sus resultados previos se conservan como antecedentes y no se mezclan con esta nueva serie.'''
    method += ' Los bordes se segmentizan a máximo 0,001° para las áreas geodésicas. Se reconstruyen límites contiguos de la malla nominal 0,1° para evitar los solapes del redondeo float32 de los límites originales; ambos límites quedan registrados. No se modifica ni remuestrea la precipitación. La suma de intersecciones coincide con el área del polígono dentro de una tolerancia relativa de una parte por millón. La malla es de unos 11 km por lado en esta región: aporta representación espacial de la cuenca, pero no resuelve toda la variabilidad orográfica interna.'
    imerg_stats = commonstats.loc[commonstats.variable == 'IMERG polígono'].iloc[0]
    chirps_stats = commonstats.loc[commonstats.variable == 'CHIRPS'].iloc[0]
    qstats = commonstats.loc[commonstats.variable == 'Caudal Q'].iloc[0]
    discussion = f'''En los mismos 285 meses, IMERG de polígono tiene media {imerg_stats.media:.2f} y mediana {imerg_stats.mediana:.2f} mm/mes; CHIRPS tiene media {chirps_stats.media:.2f} y mediana {chirps_stats.mediana:.2f} mm/mes. La diferencia de medias es {imerg_stats.media-chirps_stats.media:+.2f} mm/mes. Es una diferencia entre productos, no un error frente a una verdad observada. Q tiene media {qstats.media:.2f} y mediana {qstats.mediana:.2f} m³/s; los meses de caudal alto elevan su promedio. Las cajas muestran mediana, P25–P75 y extremos fuera de 1,5 IQR: no se elimina ningún dato por ese criterio. Los ceros y las fechas de los mínimos/máximos se registran en las tablas. Las distribuciones reúnen todos los meses calendario y no sustituyen la climatología del 1.5. R se deriva de Q, y P−R no equivale automáticamente a evapotranspiración. Los extremos se deben contrastar con las cronologías; su plausibilidad no certifica la exactitud del dato.'''
    convention = 'Desviación estándar muestral (n−1); percentiles lineales tipo 7. Histogramas Freedman–Diaconis; CHIRPS e IMERG usan los mismos 285 meses y exactamente los mismos bordes. Barras en porcentaje de meses, cuya suma es 100%. Las estadísticas del registro disponible por fuente conservan sus distintas coberturas y se presentan separadas de la muestra común. ERA5-Land es temperatura a 2 m de reanálisis, no estación terrestre ni estimación MSWX.'
    def table_html(df):
        return '<div style="overflow:auto">' + df.to_html(index=False, classes='tabla-estadistica', float_format=lambda x: f'{x:.3f}') + '</div>'
    h12 = '<section class="panel" id="imerg-poligono-metodo"><h2>IMERG: promedio exacto de cuenca y validación (V07B)</h2><p>' + method + '</p><p>Acceso: archivos originales GES DISC, autenticación Earthdata y script de descarga conservado. Cálculo: scripts/22_imerg_poligono_estadisticas.py. Pesos, huellas SHA256, datos por celda y metadatos se guardan en documentos/imerg_poligono. DOI: <a href="https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07">10.5067/GPM/IMERG/3B-MONTH/07</a>.</p>' + series_html + '</section>'
    h13 = '<section class="panel" id="imerg-poligono-estadisticos"><h2>Distribuciones actualizadas: IMERG de cuenca y ERA5-Land</h2><p>'+convention+'</p><h3>Registros disponibles por fuente (no son la misma muestra)</h3>'+table_html(fullstats)+'<h3>Muestra común: 285 meses completos, 1998–2022</h3>'+table_html(commonstats)+chart_html+'<h3>Interpretación inicial</h3><p>'+discussion+'</p></section>'
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    text = re.sub(r'<!-- IMERG_POLIGONO_INICIO -->.*?<!-- IMERG_POLIGONO_FIN -->', '', text, flags=re.S)
    insertion = '<!-- IMERG_POLIGONO_INICIO -->'+h12+h13+'<!-- IMERG_POLIGONO_FIN -->'
    assert '<footer>' in text
    html.write_text(text.replace('<footer>', insertion+'<footer>', 1), encoding='utf-8')
    def textext(t):
        return t.replace('–', '--').replace('−', '-').replace('×', r'$\times$').replace('%', r'\%').replace('°', r'$^\circ$').replace('³', r'$^3$').replace('_', r'\_')
    def tex_table(df):
        chunks = []
        groups = [['n','media','mediana','sd','minimo','maximo','rango'], ['Q1','Q2','Q3','IQR','P5','P10','P90','P95'], ['ceros','mes_minimo','mes_maximo']]
        for fields in groups:
            cols = ['variable','unidad']+fields
            chunks.append('{\\scriptsize\n'+df[cols].to_latex(index=False, escape=True, float_format='%.2f', longtable=True)+'}\n')
        chunks.append('{\\scriptsize\n'+df[['variable','inicio','fin']].to_latex(index=False, escape=True)+'}\n')
        return ''.join(chunks)
    t12 = '\\subsubsection*{IMERG: promedio exacto de cuenca y validación (V07B)}\n'+textext(method)+'\n\nAcceso: GES DISC mediante el script de descarga conservado y sesión Earthdata. Reproducción: \\path{scripts/22_imerg_poligono_estadisticas.py}; huellas, pesos y metadatos en \\path{documentos/imerg_poligono}.\n\nDOI: \\url{https://doi.org/10.5067/GPM/IMERG/3B-MONTH/07}.\n\\begin{figure}[H]\\centering\\includegraphics[width=\\linewidth]{figuras/imerg_poligono_series.pdf}\\caption{Fuentes identificadas y alineadas, 1998--2022; los vacíos se conservan.}\\end{figure}\n'
    t13 = '\\subsubsection*{Distribuciones actualizadas: IMERG de cuenca y ERA5-Land}\n'+textext(convention)+'\n\\subsubsection*{Registros disponibles por fuente}\n'+tex_table(fullstats)+'\\subsubsection*{Mismos 285 meses completos}\n'+tex_table(commonstats)
    for filename, caption in [('imerg_poligono_histogramas.pdf', 'Histogramas sobre los mismos meses; las lluvias usan límites de clase compartidos.'), ('imerg_poligono_cajas.pdf', 'Cajas sobre los mismos 285 meses, con unidades propias de cada variable.')]:
        t13 += '\\begin{figure}[H]\\centering\\includegraphics[width=\\linewidth]{figuras/'+filename+'}\\caption{'+caption+'}\\end{figure}\n'
    t13 += '\\subsubsection*{Interpretación inicial}\n'+textext(discussion)+'\n'
    (OUT / 'apartado_1_2.tex').write_text(t12, encoding='utf-8')
    (OUT / 'apartado_1_3.tex').write_text(t13, encoding='utf-8')
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)
    print(commonstats[['variable','n','media','mediana','mes_minimo','mes_maximo']].to_string(index=False), flush=True)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    s, meta = extract()
    report(s, meta)

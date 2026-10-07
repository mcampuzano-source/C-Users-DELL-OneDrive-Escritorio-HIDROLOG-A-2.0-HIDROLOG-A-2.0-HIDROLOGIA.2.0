"""Audita campos reales y prepara el apartado 5.1 en PDF/HTML y NetCDF.

No calcula correlaciones: deja sus entradas y criterios documentados para 5.2.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import re
import shutil
import tempfile
import base64
import html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'la_vieja/documentos'
OUT = DOCS / 'apartado_5_1'
OUT.mkdir(exist_ok=True)
RAW = ROOT / 'datos/clima_global_5_1'
spec = importlib.util.spec_from_file_location('download51', Path(__file__).with_name('41_descargar_campos_globales.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SOURCES = {
    'sst': ('SST', 'NOAA ERSSTv5', 'degC', '2°', 'https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html'),
    'slp': ('Presión al nivel del mar', 'NCEP/NCAR Reanalysis 1', 'hPa', '2,5°', 'https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html'),
    'z500': ('Altura geopotencial a 500 hPa', 'NCEP/NCAR Reanalysis 1', 'm', '2,5°', 'https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html'),
    'psfc': ('Presión de superficie (auxiliar)', 'NCEP/NCAR Reanalysis 1', 'hPa', '2,5°', 'https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.html'),
}
hydro_path = DOCS / 'imerg_poligono/series_alineadas.csv'
hydro = pd.read_csv(hydro_path, parse_dates=['mes']).set_index('mes')
cols = ['P_CHIRPS_mm', 'P_IMERG_poligono_mm', 'Q_m3_s']
sim = hydro.loc['1998-01-01':'2022-12-01', cols].dropna()
assert len(hydro) == 504 and len(sim) == 285
hydro.loc[:, cols].to_csv(OUT / 'series_cuenca_1981_2022.csv', index_label='mes')
sim.to_csv(OUT / 'series_cuenca_comunes_1998_2022.csv', index_label='mes')
counts = sim.groupby(sim.index.month).size()
counts.rename('pares_disponibles').to_csv(OUT / 'muestra_por_mes_calendario.csv', index_label='mes_calendario')

datasets = {}
inventory = []
for key in SOURCES:
    path = RAW / f'{key}_1981_2022.nc'
    assert path.exists(), f'Falta el campo {key}; ejecutar 41_descargar_campos_globales.py'
    ds = mod.load(path)
    var = mod.FIELDS[key][1]
    da = ds[var].squeeze(drop=True).reset_coords(drop=True).astype('float64')
    assert da.sizes['time'] == 504
    units = str(da.attrs.get('units', ''))
    if key in ('slp', 'psfc'):
        if units.lower() in ('pa', 'pascal', 'pascals'):
            da = da / 100
        else:
            assert units.lower() in ('millibars', 'millibar', 'mb', 'hpa'), units
        da.attrs['units'] = 'hPa'
    if key == 'z500':
        assert units == 'm', units
        if 'level' in ds:
            assert float(ds.level.values.reshape(-1)[0]) == 500
    # Regular longitude convention without duplicated seam; no spatial interpolation.
    da = da.assign_coords(lon=((da.lon + 180) % 360) - 180).sortby('lon').sortby('lat')
    assert len(np.unique(da.lon)) == da.sizes['lon']
    assert np.allclose(np.diff(da.lat), np.diff(da.lat)[0])
    assert np.allclose(np.diff(da.lon), np.diff(da.lon)[0])
    assert da.lat.min() <= -88 and da.lat.max() >= 88
    datasets[key] = da
    a = da.values
    inventory.append(dict(field=key, name=SOURCES[key][0], product=SOURCES[key][1],
                          units=SOURCES[key][2], native_units=units,
                          resolution_deg=float(np.diff(da.lon)[0]),
                          months=504, first_month='1981-01', last_month='2022-12',
                          latitudes=da.sizes['lat'], longitudes=da.sizes['lon'],
                          finite_values=int(np.isfinite(a).sum()),
                          total_values=int(a.size), min=float(np.nanmin(a)), max=float(np.nanmax(a)),
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          source_url=SOURCES[key][4], attributes={k:str(v) for k,v in ds.attrs.items()}))

assert datasets['z500'].lat.equals(datasets['psfc'].lat)
assert datasets['z500'].lon.equals(datasets['psfc'].lon)
assert datasets['z500'].time.equals(datasets['psfc'].time)
monthly_above = datasets['psfc'] >= 500
below_count = int((~monthly_above).values.sum())
datasets['z500'] = datasets['z500'].where(monthly_above)

prepared = {}
for key in ('sst', 'slp', 'z500'):
    da = datasets[key].sel(time=sim.index)
    clim = da.groupby('time.month').mean('time', skipna=True)
    anomalies = da.groupby('time.month') - clim
    n = da.groupby('time.month').count('time')
    sd = da.groupby('time.month').std('time', ddof=1)
    # Pairwise season-specific maps require enough data and nonzero variance.
    mask = (n >= 20) & (sd > 1e-8)
    if key == 'sst':
        # Preserve land missingness from ERSST; do not fill or invent coast pixels.
        mask &= np.isfinite(clim)
    out = anomalies.rename(key + '_anomaly').to_dataset()
    out[key + '_anomaly'].attrs.update(units=SOURCES[key][2], reference='1998-2022, mismos 285 meses completos de cuenca')
    out['climatology'] = clim
    out['sample_count'] = n
    out['mask_valid'] = mask.astype('int8')
    out.attrs.update(product=SOURCES[key][1], native_resolution=SOURCES[key][3],
                     method='Anomalías por mes calendario; sin relleno, interpolación ni eliminación de tendencia.',
                     source_sha256=next(x['sha256'] for x in inventory if x['field']==key))
    with tempfile.TemporaryDirectory(prefix='hydro_ready_') as tmp:
        temp = Path(tmp) / 'prepared.nc'
        out.to_netcdf(temp, engine='netcdf4', encoding={key+'_anomaly':{'zlib':True,'complevel':4}})
        shutil.copyfile(temp, OUT / f'{key}_anomalias_285_meses.nc')
    # Group means should be zero where the monthly climatology is defined.
    residual = anomalies.groupby('time.month').mean('time', skipna=True).values
    assert np.nanmax(np.abs(residual)) < 1e-3, key
    prepared[key] = dict(valid_grid_months=int(mask.values.sum()),
                         total_grid_months=int(mask.size),
                         zero_mean_error=float(np.nanmax(np.abs(residual))))

pd.DataFrame([{k:v for k,v in x.items() if k!='attributes'} for x in inventory]).to_csv(OUT / 'inventario_campos.csv', index=False)
summary = dict(coverage='1981-01 a 2022-12', complete_months_global=504,
               common_period='1998-01 a 2022-12', common_months=285,
               missing_months_common=15, monthly_sample_counts=counts.to_dict(),
               inventory=inventory, prepared=prepared,
               z500_masked_cell_months=below_count,
               hydro_input_sha256=hashlib.sha256(hydro_path.read_bytes()).hexdigest(),
               status='5.1 preparado; 5.2-5.4 pendientes; no se han calculado correlaciones',
               era5='Catálogos CDS explorados; no descargado ni mezclado con NCEP. Requiere acceso autenticado.')
(OUT / 'resultados.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

# Coastlines are cartographic context, not a computational mask.
coast = OUT / 'ne_110m_coastline.geojson'
if not coast.exists():
    try:
        import requests
        r = requests.get('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson', timeout=(10,30))
        r.raise_for_status();coast.write_bytes(r.content)
    except requests.RequestException:
        pass
def outlines(ax):
    if coast.exists():
        for f in json.loads(coast.read_text())['features']:
            coords=f['geometry']['coordinates']
            if f['geometry']['type']=='LineString':coords=[coords]
            for line in coords:
                a=np.asarray(line);cut=np.abs(np.diff(a[:,0],prepend=a[0,0]))>180
                a=a.astype(float);a[cut]=np.nan
                ax.plot(a[:,0],a[:,1],color='#333333',lw=.35)
    ax.plot(-75.7,4.45,'*',color='#b52824',ms=7)
    ax.set(xlim=(-180,180),ylim=(-90,90),xlabel='Longitud (°)',ylabel='Latitud (°)')
    ax.set_xticks([-180,-120,-60,0,60,120,180]);ax.set_yticks([-90,-45,0,45,90])
    ax.grid(alpha=.18)
fig,axs=plt.subplots(2,2,figsize=(12.5,7.2),layout='constrained')
for key,ax,cmap in zip(['sst','slp','z500'],axs.flat,['turbo','viridis','viridis']):
    da=datasets[key].sel(time=slice('1998-01','2022-12')).mean('time')
    im=ax.pcolormesh(da.lon,da.lat,da.values,shading='auto',cmap=cmap)
    ax.set_title(SOURCES[key][0]+' · '+SOURCES[key][3],fontsize=10)
    fig.colorbar(im,ax=ax,label=SOURCES[key][2],shrink=.75);outlines(ax)
freq=(~monthly_above).mean('time')*100
ax=axs.flat[3];im=ax.pcolormesh(freq.lon,freq.lat,freq.values,shading='auto',cmap='magma_r',vmin=0,vmax=100)
ax.set_title('500 hPa bajo superficie según presión mensual',fontsize=10)
fig.colorbar(im,ax=ax,label='% de meses 1981-2022',shrink=.75);outlines(ax)
fig.suptitle('Campos globales y control vertical · selección 5.1\nMedias 1998-2022; estrella: cuenca La Vieja. No son mapas de correlación.',fontsize=13)
fig.savefig(OUT/'campos_globales_control.png',dpi=170)
fig.savefig(OUT/'campos_globales_control.pdf');plt.close(fig)

selected = [
    ('SST (ERSSTv5)', '2° · °C · superficie marina', 'Estado térmico de Pacífico y Atlántico; permite explorar ENSO y patrones oceánicos sin reducirlos a un único índice.'),
    ('SLP (NCEP/NCAR R1)', '2,5° · hPa · nivel del mar', 'Gradientes de presión y circulación tropical de gran escala, compatibles con contrastes Pacífico-Atlántico y circulación de Walker.'),
    ('Z500 (NCEP/NCAR R1)', '2,5° · m · 500 hPa', 'Estructura de la troposfera media y patrones remotos de circulación; complementa SLP sin medir directamente el transporte de humedad.'),
    ('Presión superficial', '2,5° · hPa · superficie', 'Variable auxiliar para excluir Z500 cuando 500 hPa queda bajo la superficie del modelo.'),
]
sections = [
    ('Selección y justificación física', 'Se obtuvo una base pública de campos globales mensuales: SST NOAA ERSSTv5, presión al nivel del mar (SLP) y altura geopotencial a 500 hPa (Z500) de NCEP/NCAR Reanalysis 1. Se añade presión de superficie como control vertical. La malla nativa de 2°/2,5° resuelve patrones de gran escala y evita interpolar a una resolución aparente mayor. No resuelve el relieve ni los procesos de lluvia de una cuenca andina. La selección se fijó antes de calcular mapas de correlación.'),
    ('Mecanismos relevantes y alcance', 'Para el occidente y los Andes colombianos, la literatura describe conexiones de la lluvia con SST del Pacífico y Atlántico, ENSO y circulación asociada a los chorros de Chocó y del Caribe (Poveda y Mesa, 1997; Poveda et al., 2014). Es una justificación regional, no una atribución demostrada para La Vieja. SLP y Z500 describen el estado de circulación; para evaluar directamente advección de humedad se necesitarían vientos y humedad, no inferirla solo de estos dos campos.'),
    ('Productos atmosféricos y alternativas', 'Se consideraron los productos mensuales ERA5 en superficie y en niveles de presión, distribuidos por el CDS en una malla atmosférica regular de 0,25°. En este análisis se adopta NCEP/NCAR Reanalysis 1, de acceso público y resolución de 2,5°, como base inicial para identificar patrones de gran escala. ERA5 constituye una alternativa para evaluar la sensibilidad de los resultados al reanálisis y a la resolución espacial; esa comparación requeriría una agregación consistente por área y debe conservar ambos productos separados. La temperatura ERA5-Land utilizada en el estudio de cuenca no reemplaza los campos atmosféricos globales.'),
    ('Periodo, cobertura y correspondencia con la cuenca', f'Cada campo descargado contiene 504 meses consecutivos entre enero de 1981 y diciembre de 2022. CHIRPS y Q tienen 485 meses completos; IMERG tiene 300 desde 1998. La comparación principal conserva los mismos 285 meses completos de CHIRPS, IMERG y Q en 1998-2022, con 15 huecos sin relleno. El análisis secundario CHIRPS-Q podrá usar 1981-2022 por separado. La muestra principal aporta entre {int(counts.min())} y {int(counts.max())} pares por mes calendario; los mapas informarán el tamaño efectivo en cada píxel.'),
    ('Unidades, máscaras y transformaciones', 'Las medias mensuales no se suman. SLP y presión superficial vienen en las unidades declaradas en el NetCDF: se dividen por 100 solo si están en Pa; millibars equivale a hPa. NCEP hgt ya es altura geopotencial en metros: no se vuelve a dividir por g. En ERA5, geopotential es Φ en m²/s² y se convertiría a Z=Φ/9,80665 m. Se conservan los faltantes oceánicos/terrestres de ERSST sin interpolarlos. Las longitudes se normalizan a [-180°,180°) sin duplicar la costura; cada campo mantiene su malla nativa.'),
    ('Control vertical y máscara para los mapas', f'Se comparó cada celda y mes de presión superficial con 500 hPa: se enmascaran {below_count:,} valores celda-mes de Z500 donde la presión superficial mensual es menor de 500 hPa. Es un control sobre medias, no garantiza que el nivel esté sobre el terreno durante cada instante del mes. Los mapas por mes calendario deberán conservar solo píxeles con al menos 20 pares y variación no nula. SLP es una reducción al nivel del mar y puede ser menos fiable sobre terreno elevado; se contrastarán sus patrones sobre océanos y tierras altas en 5.3. Los valores de SST próximos a congelación y el hielo marino requieren cautela; el interés físico principal es tropical.'),
    ('Anomalías y muestra de análisis', 'Las anomalías de cada campo se definen como la diferencia entre el valor mensual y la media de su mes calendario. La climatología de referencia se estima con las mismas 285 fechas completas de la cuenca durante 1998-2022, de modo que las comparaciones no dependan de calendarios distintos. Los campos conservan su malla nativa, sus unidades y sus faltantes; no se elimina la tendencia. La verificación de una media de anomalías próxima a cero en cada mes confirma esta transformación. Los índices Niño 3.4 u ONI podrán complementar la interpretación, sin sustituir los campos espaciales. La asociación con lluvia y caudal, sus rezagos y su robustez se evaluarán en los apartados siguientes.'),
    ('Procedencia y alcance de los productos', 'La base global combina ERSSTv5 y NCEP/NCAR Reanalysis 1, distribuidos por NOAA PSL. ERSSTv5 es una reconstrucción de SST basada en observaciones oceánicas, mientras que los campos atmosféricos proceden de un reanálisis; por ello, sus valores no se interpretan como mediciones locales directas. Se fijaron las versiones, el periodo y los niveles verticales antes de construir los mapas. Los metadatos de soporte conservan las solicitudes de acceso, fechas, coordenadas, unidades y huellas SHA-256 de los archivos, junto con los conteos y las máscaras. La lluvia de Zaragoza no se utiliza como respuesta principal: sus 14 meses completos resultan insuficientes para estimar asociaciones por mes calendario.'),
]
refs = [
    ('NOAA PSL: catálogo de SST', 'https://psl.noaa.gov/data/gridded/tables/sst.html'),
    ('NOAA PSL: ERSSTv5', SOURCES['sst'][4]),
    ('NOAA PSL: NCEP/NCAR Reanalysis 1', SOURCES['slp'][4]),
    ('CDS: ERA5 mensual en superficie', 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means'),
    ('CDS: ERA5 mensual en niveles de presión', 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5-pressure-levels-monthly-means'),
    ('Poveda y Mesa (1997), Journal of Climate', 'https://doi.org/10.1175/1520-0442(1997)010<2690:FBHPIT>2.0.CO;2'),
    ('Poveda et al. (2014), Water Resources Research', 'https://doi.org/10.1002/2013WR014087'),
]

# A short appendix-style section retains equations and provenance for later work.
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body51',parent=styles['BodyText'],fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='Cell51',parent=styles['BodyText'],fontName='Helvetica',fontSize=8,leading=11))
styles['Heading1'].textColor=colors.HexColor('#193646');styles['Heading2'].textColor=colors.HexColor('#193646')
def para(s,style='Body51'):return Paragraph(html.escape(s),styles[style])
story=[para('5. Mapas de correlación con el clima global','Heading1'),para('5.1. Seleccionar los campos climáticos','Heading2')]
story += [para(sections[0][0],'Heading2'),para(sections[0][1])]
table=[[para('Campo','Cell51'),para('Resolución, unidad y nivel','Cell51'),para('Justificación','Cell51')]]+[[para(x,'Cell51') for x in row] for row in selected]
t=Table(table,colWidths=[112,128,243]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf4f7')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbd9df')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story +=[t,Spacer(1,12)]
for title,text in sections[1:]:story +=[para(title,'Heading2'),para(text)]
story +=[PageBreak(),para('Inspección de los campos obtenidos','Heading2'),Image(str(OUT/'campos_globales_control.png'),width=483,height=278)]
story +=[para('Las figuras muestran campos medios y el control vertical; no corresponden a correlaciones. Se mantienen las rejillas originales. Costas: Natural Earth (contexto cartográfico).')]
story +=[para('Inventario verificado','Heading2')]
for row in inventory:story +=[para(f"{row['name']}: {row['latitudes']} × {row['longitudes']} centros de rejilla, {row['months']} meses; unidad fuente {row['native_units']}. Rango global temporal: {row['min']:.2f} a {row['max']:.2f} {row['units']}.")]
story +=[para('Fuentes','Heading2')]
for label,url in refs:story +=[Paragraph(f'<a href="{html.escape(url,quote=True)}">{html.escape(label)}</a>',styles['Body51'])]
SimpleDocTemplate(str(OUT/'punto_5_1.pdf'),pagesize=A4,rightMargin=56,leftMargin=56,topMargin=48,bottomMargin=55,title='Apartado 5.1 - Selección de campos climáticos',author='Grupo de Hidrología').build(story)

rows=''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in selected)
body='<h4>Base global preparada</h4><p><strong>Base obtenida: 504 meses globales por campo; comparación principal: 285 meses simultáneos de cuenca.</strong></p>'
for i,(title,text) in enumerate(sections):
    body+='<h4>'+html.escape(title)+'</h4><p>'+html.escape(text)+'</p>'
    if i==0:body+='<div style="overflow:auto"><table><thead><tr><th>Campo</th><th>Resolución, unidad y nivel</th><th>Justificación</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
img=base64.b64encode((OUT/'campos_globales_control.png').read_bytes()).decode()
body+='<h4>Inspección de campos y control vertical</h4><img style="width:100%;height:auto" src="data:image/png;base64,'+img+'" alt="Campos globales mensuales obtenidos y máscara de superficie para 500 hPa"><p>Medias 1998-2022 y frecuencia del control vertical. Estos gráficos no son mapas de correlación.</p>'
body+='<h4>Muestra disponible por mes calendario</h4><p>'+', '.join(f'{m:02d}: {n}' for m,n in counts.items())+' pares; muestra principal 1998-2022.</p><h4>Fuentes</h4><ul>'+''.join('<li><a href="'+html.escape(url,quote=True)+'">'+html.escape(label)+'</a></li>' for label,url in refs)+'</ul>'
(OUT/'contenido_5_1.html').write_text(body,encoding='utf-8')
hpath=DOCS/'informe_interactivo.html';h=hpath.read_text(encoding='utf-8')
block='<!-- PUNTO_5_1_INICIO --><section class="panel" id="seleccion-campos-51">'+body+'</section><!-- PUNTO_5_1_FIN -->'
if '<!-- PUNTO_5_1_INICIO -->' in h:h=re.sub(r'<!-- PUNTO_5_1_INICIO -->.*?<!-- PUNTO_5_1_FIN -->',lambda _:block,h,flags=re.S)
else:h=h.replace('</main>',block+'</main>',1)
needle="pendiente(sub(el,'guia-'+n+'-'+(i+1),n+'.'+(i+1)+'. '+t),'Pendiente de desarrollar.')"
replacement="(()=>{const se=sub(el,'guia-'+n+'-'+(i+1),n+'.'+(i+1)+'. '+t);if(n===5&&i===0)mover(se,document.getElementById('seleccion-campos-51'));else pendiente(se,'Pendiente de desarrollar.');})()"
if needle in h:h=h.replace(needle,replacement)
else:assert "seleccion-campos-51'" in h,'No se encontró el organizador del punto 5'
hpath.write_text(h,encoding='utf-8')
tex=DOCS/'latex/informe_ordenado.tex';s=tex.read_text(encoding='utf-8')
start=s.index(r'\subsection{Seleccionar los campos climáticos}')
end=s.index(r'\subsection{Definir y calcular los mapas mensuales}',start)
fragment=r'\subsection{Seleccionar los campos climáticos}'+'\n'
for title,text in sections:
    escape=lambda x:x.replace('%',r'\%').replace('_',r'\_').replace('&',r'\&').replace('°',r'$^\circ$').replace('≥',r'$\geq$').replace('²',r'$^2$').replace('Φ',r'$\Phi$')
    fragment+=r'\subsubsection*{'+escape(title)+'}\n'+escape(text)+'\n\n'
fragment+=r'\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../apartado_5_1/campos_globales_control.pdf}\caption{Campos obtenidos y control vertical; no son mapas de correlación.}\end{figure}'+'\n'
(OUT/'seccion_5_1.tex').write_text(fragment,encoding='utf-8');s=s[:start]+fragment+s[end:];tex.write_text(s,encoding='utf-8')
print('5.1 preparado en PDF, HTML y NetCDF. Correlaciones pendientes de 5.2.',flush=True)

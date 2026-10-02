"""Cribado reproducible; no rellena faltantes ni certifica calidad hidrologica."""
from pathlib import Path
import io
import json
import re
import zipfile
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D, O = ROOT / 'datos', ROOT / 'resultados'
O.mkdir(exist_ok=True)
info = pd.read_csv(D/'02_CAMELS_COL_Catchment_information.csv', sep=';', encoding='cp1252')
phys = pd.read_csv(D/'10_CAMELS_COL_Physiograpic_characteristics.csv', sep=';')
catalog = pd.DataFrame(json.loads((D/'catalogo_ideam.json').read_text(encoding='utf-8')))
catalog['gauge_id'] = pd.to_numeric(catalog.codigo)
attrs = info.merge(phys, on='gauge_id').merge(catalog[['gauge_id','nombre','municipio','latitud','longitud','subzona_hidrografica']], on='gauge_id', how='left')
rows, availability = [], []
with zipfile.ZipFile(D/'04_CAMELS_COL_Hydrometeorological_data.zip') as z:
    for name in z.namelist():
        if not name.endswith('.txt'):
            continue
        code = int(re.search(r'(\d{8})', name).group(1))
        a = attrs[attrs.gauge_id == code]
        if a.empty:
            continue
        raw = pd.read_csv(io.BytesIO(z.read(name)), sep='\t')
        dates = pd.to_datetime(raw.pop('Fecha'), format='%d/%m/%Y', errors='raise')
        duplicates = int(dates.duplicated().sum())
        if duplicates:
            raise ValueError(f'Duplicados en {code}: {duplicates}')
        raw.index = dates
        raw = raw.apply(pd.to_numeric, errors='raise').sort_index()
        negative = int((raw[['Precipitacion','Caudal']] < 0).sum().sum())
        raw[['Precipitacion','Caudal']] = raw[['Precipitacion','Caudal']].where(raw[['Precipitacion','Caudal']] >= 0)
        raw = raw.replace([np.inf, -np.inf], np.nan)
        # Periodo fijo completo y ventana reciente de 25 anos, sin buscar por resultados climaticos.
        for label, start, end in [('1981_2022','1981-01-01','2022-12-31'), ('1998_2022','1998-01-01','2022-12-31')]:
            x = raw.reindex(pd.date_range(start,end,freq='D'))
            counts = x.resample('MS').count()
            complete = counts.eq(counts.index.days_in_month, axis=0)
            row = a.iloc[0].to_dict()
            row.update(periodo=label, inicio=start, fin=end, dias_esperados=len(x), filas_originales=len(raw), duplicados=duplicates, negativos_P_Q=negative)
            for col, short in [('Precipitacion','P'), ('Caudal','Q'), ('Temperatura_minima','Tmin'), ('Temperatura_maxima','Tmax')]:
                row[f'faltantes_{short}_pct'] = 100*x[col].isna().mean()
                row[f'meses_completos_{short}'] = int(complete[col].sum())
            row['meses_completos_PQ'] = int(complete[['Precipitacion','Caudal']].all(axis=1).sum())
            row['cumple_filtro'] = bool(100 <= row['area'] <= 10000 and row['faltantes_P_pct'] <= 10 and row['faltantes_Q_pct'] <= 10)
            rows.append(row)
        if code in [12027050,22027020,26127040,23057140,21017020]:
            x = raw.reindex(pd.date_range('1981-01-01','2022-12-31'))
            counts=x.resample('MS').count()
            counts.insert(0,'gauge_id',code)
            counts.insert(1,'dias_esperados',counts.index.days_in_month)
            availability.append(counts.reset_index(names='mes'))
            raw.to_csv(O/f'diario_{code}.csv', index_label='fecha')
            monthly = pd.DataFrame({'P_mm':x.Precipitacion.resample('MS').sum(min_count=1),'Q_m3_s':x.Caudal.resample('MS').mean()})
            monthly.loc[counts.Precipitacion < counts.dias_esperados,'P_mm']=np.nan
            monthly.loc[counts.Caudal < counts.dias_esperados,'Q_m3_s']=np.nan
            monthly.to_csv(O/f'mensual_preliminar_{code}.csv', index_label='mes')
result=pd.DataFrame(rows)
result.to_csv(O/'revision_todas_cuencas.csv',index=False,encoding='utf-8-sig')
pd.concat(availability).to_csv(O/'disponibilidad_mensual_candidatas.csv',index=False)
valid=result[(result.periodo=='1981_2022') & result.cumple_filtro].sort_values('faltantes_Q_pct')
valid.to_csv(O/'candidatas_42_anos.csv',index=False,encoding='utf-8-sig')
print('Cuencas evaluadas:',result.gauge_id.nunique(), 'Cumplen en 1981-2022:',len(valid))
print(result[(result.periodo=='1981_2022') & result.gauge_id.isin([12027050,22027020,26127040,23057140,21017020])][['gauge_id','nombre','area','faltantes_P_pct','faltantes_Q_pct','meses_completos_PQ','negativos_P_Q']].to_string(index=False))

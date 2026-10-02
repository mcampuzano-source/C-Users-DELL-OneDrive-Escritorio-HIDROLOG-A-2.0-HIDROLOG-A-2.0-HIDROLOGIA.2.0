"""Punto 1, primera exploracion P/Q: originales, auditoria, agregacion y figuras.
Ejecutar desde cualquier carpeta. Sin rellenos, sin eliminacion por ser extremo.
"""
from pathlib import Path
import io, json, math, zipfile, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from openpyxl.styles import Font, PatternFill

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'la_vieja'/'punto_1'
OUT.mkdir(parents=True,exist_ok=True)
FIG=OUT/'figuras'
FIG.mkdir(exist_ok=True)
AREA=2797.19
CODE=26127040
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':110})
LABELS={'P_mm':'Precipitación CHIRPS (mm/mes)','Q_m3_s':'Caudal observado (m³/s)','R_mm':'Escorrentía (mm/mes)'}
COLORS={'P_mm':'#257da4','Q_m3_s':'#a35720','R_mm':'#368269'}
NAMES=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

# 1. Lectura directa del original y auditoria de fechas y valores.
archive=ROOT/'datos'/'04_CAMELS_COL_Hydrometeorological_data.zip'
with zipfile.ZipFile(archive) as z:
    member=next(n for n in z.namelist() if str(CODE) in n)
    data=z.read(member)
raw=pd.read_csv(io.BytesIO(data),sep='\t')
dates=pd.to_datetime(raw.pop('Fecha'),format='%d/%m/%Y',errors='raise')
duplicates=int(dates.duplicated().sum())
if duplicates:
    raise ValueError('Fechas duplicadas; resolver antes de agregar')
ordered=bool(dates.is_monotonic_increasing)
raw.index=pd.DatetimeIndex(dates,name='fecha')
raw=raw.apply(pd.to_numeric,errors='raise').sort_index()
calendar=pd.date_range('1981-01-01','2022-12-31',freq='D',name='fecha')
if not raw.index.isin(calendar).all():
    raise ValueError('Fechas fuera del periodo declarado')
daily=raw.reindex(calendar)
issues=[]
for col in raw:
    finite=np.isfinite(daily[col])
    invalid=(daily[col].notna() & ~finite)
    if col in ['Precipitacion','Caudal']:
        invalid |= daily[col].lt(0)
    for date,value in daily.loc[invalid,col].items():
        issues.append({'fecha':date,'variable':col,'valor':value,'decision':'No valido; se conserva en original y se excluye de la agregacion'})
    daily.loc[invalid,col]=np.nan
inverted=int((daily.Temperatura_minima>daily.Temperatura_maxima).sum())
pd.DataFrame(issues,columns=['fecha','variable','valor','decision']).to_csv(OUT/'valores_invalidos.csv',index=False)
daily.to_csv(OUT/'diario_calendario_completo.csv',index_label='fecha')

def intervals(mask):
    """Intervalos consecutivos en calendario real; no concatenar dias ausentes."""
    groups=mask.ne(mask.shift()).cumsum()
    return [{'inicio':x.index[0], 'fin':x.index[-1], 'dias':len(x)} for _,x in mask[mask].groupby(groups[mask])]

gap_rows=[]
for col in ['Precipitacion','Caudal']:
    gap_rows.extend(dict(variable=col,**v) for v in intervals(daily[col].isna()))
gaps=pd.DataFrame(gap_rows)
gaps.to_csv(OUT/'intervalos_faltantes.csv',index=False)

# 2. Agregacion mensual estricta, con 100 % de dias validos por variable.
counts=daily.resample('MS').count()
expected=pd.Series(counts.index.days_in_month,index=counts.index,name='dias_esperados')
complete=counts.eq(expected,axis=0)
monthly=pd.DataFrame(index=counts.index)
monthly['P_mm']=daily.Precipitacion.resample('MS').sum(min_count=1).where(complete.Precipitacion)
monthly['Q_m3_s']=daily.Caudal.resample('MS').mean().where(complete.Caudal)
monthly['R_mm']=(86.4/AREA*daily.Caudal.resample('MS').sum(min_count=1)).where(complete.Caudal)
monthly['Tmin_media_C']=daily.Temperatura_minima.resample('MS').mean().where(complete.Temperatura_minima)
monthly['Tmax_media_C']=daily.Temperatura_maxima.resample('MS').mean().where(complete.Temperatura_maxima)
monthly.index.name='mes'
availability=pd.DataFrame({'dias_esperados':expected})
for col,short in [('Precipitacion','P'),('Caudal','Q'),('Temperatura_minima','Tmin'),('Temperatura_maxima','Tmax')]:
    availability[f'dias_validos_{short}']=counts[col]
    availability[f'dias_faltantes_{short}']=expected-counts[col]
    availability[f'mes_retenido_{short}']=complete[col]
availability['P_Q_pareados']=monthly[['P_mm','Q_m3_s']].notna().all(axis=1)
monthly.to_csv(OUT/'series_mensuales.csv')
availability.to_csv(OUT/'disponibilidad_mensual.csv',index_label='mes')
availability[~availability.P_Q_pareados].to_csv(OUT/'meses_excluidos.csv',index_label='mes')
yearly=availability.groupby(availability.index.year).sum()
yearly.to_csv(OUT/'disponibilidad_anual.csv',index_label='ano')

# 3. Comprobacion independiente con sumas de Python (incluye febrero bisiesto).
checks=[]
for period in ['1981-01','1992-02']:
    block=daily.loc[period]
    if block[['Precipitacion','Caudal']].isna().any().any():
        raise ValueError(f'Mes de comprobacion incompleto: {period}')
    p=math.fsum(block.Precipitacion.tolist())
    qsum=math.fsum(block.Caudal.tolist())
    q=qsum/len(block)
    volume=qsum*86400
    r=volume/(AREA*1e6)*1000
    measured=monthly.loc[pd.Timestamp(period+'-01')]
    for variable,a,b in [('P',p,measured.P_mm),('Q',q,measured.Q_m3_s),('R',r,measured.R_mm)]:
        assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10),(period,variable,a,b)
    checks.append({'mes':period,'dias':len(block),'suma_P_diaria_mm':p,'suma_Q_diaria':qsum,'Q_media_m3_s':q,'volumen_m3':volume,'area_km2':AREA,'R_mm':r,'coincide':True})
manual=pd.DataFrame(checks)
manual.to_csv(OUT/'comprobacion_manual.csv',index=False)
assert np.allclose(monthly.R_mm,monthly.Q_m3_s*expected*86.4/AREA,equal_nan=True)

# 4. Estadistica descriptiva. Percentiles lineales, desviacion muestral ddof=1.
stats=[]
extremes=[]
box_flags=[]
for var in LABELS:
    s=monthly[var].dropna()
    quant=s.quantile([.05,.10,.25,.5,.75,.90,.95],interpolation='linear')
    q1,q3=quant.loc[.25],quant.loc[.75]
    iqr=q3-q1
    stats.append({'variable':var,'unidad':LABELS[var].split('(')[-1].rstrip(')'), 'meses_validos':len(s),'media':s.mean(),'mediana':s.median(),'desviacion_estandar':s.std(ddof=1),'minimo':s.min(),'maximo':s.max(),'rango':s.max()-s.min(),'q25':q1,'q75':q3,'IQR':iqr,'p05':quant.loc[.05],'p10':quant.loc[.10],'p90':quant.loc[.90],'p95':quant.loc[.95],'asimetria':s.skew(),'meses_cero':int(s.eq(0).sum()),'min_fecha':str(s.idxmin().date()),'max_fecha':str(s.idxmax().date())})
    for direction,values in [('minimo',s.nsmallest(5)),('maximo',s.nlargest(5))]:
        for date,value in values.items():
            extremes.append({'variable':var,'tipo':direction,'mes':date,'valor':value,'P_mm':monthly.loc[date,'P_mm'],'Q_m3_s':monthly.loc[date,'Q_m3_s'],'R_mm':monthly.loc[date,'R_mm']})
    for date,value in s[(s<q1-1.5*iqr)|(s>q3+1.5*iqr)].items():
        box_flags.append({'variable':var,'mes':date,'valor':value,'criterio':'Fuera de Q1-1.5 IQR o Q3+1.5 IQR global','decision':'Conservar; alerta exploratoria, no error demostrado'})
statistics=pd.DataFrame(stats).set_index('variable')
statistics.to_csv(OUT/'estadistica_descriptiva.csv')
extremes=pd.DataFrame(extremes)
extremes.to_csv(OUT/'meses_extremos.csv',index=False)
box_flags=pd.DataFrame(box_flags)
box_flags.to_csv(OUT/'alertas_diagramas_caja.csv',index=False)

# Secuencias constantes de al menos 7 dias: ceros de lluvia se separan de alertas.
runs=[]
for col in ['Precipitacion','Caudal']:
    s=daily[col]
    group=(s.ne(s.shift())|s.isna()).cumsum()
    for _,x in s.dropna().groupby(group[s.notna()]):
        if len(x)>=7:
            runs.append({'variable':col,'inicio':x.index[0],'fin':x.index[-1],'dias':len(x),'valor':x.iloc[0],'tipo':'Racha seca, no error por si sola' if col=='Precipitacion' and x.iloc[0]==0 else 'Constancia para revisar con metadatos'})
run_table=pd.DataFrame(runs,columns=['variable','inicio','fin','dias','valor','tipo'])
run_table.to_csv(OUT/'secuencias_constantes.csv',index=False)

# Cambios bruscos: solo pares consecutivos, cociente >=5 o <=1/5; no prueba de ruptura.
jumps=[]
for var in ['P_mm','Q_m3_s']:
    ratio=monthly[var]/monthly[var].shift(1)
    for date,value in ratio[(ratio>=5)|(ratio<=.2)].items():
        jumps.append({'variable':var,'mes':date,'valor':monthly.loc[date,var],'cociente_mes_previo':value,'decision':'Conservar; contrastar con estacionalidad y metadatos'})
jump_table=pd.DataFrame(jumps,columns=['variable','mes','valor','cociente_mes_previo','decision'])
jump_table.to_csv(OUT/'alertas_cambios_bruscos.csv',index=False)

# Sensibilidad de Q a retener meses con >=90 % de dias; no modificar serie principal.
q90=daily.Caudal.resample('MS').mean().where(counts.Caudal/expected>=.9)
sensitivity=pd.DataFrame({'Q_estricto':monthly.Q_m3_s,'Q_90pct_exploratorio':q90,'dias_validos':counts.Caudal,'dias_esperados':expected})
sensitivity.to_csv(OUT/'sensibilidad_completitud_Q.csv')

# 5. Ciclo anual exploratorio, con los mismos meses validos para P y Q.
paired=monthly.loc[availability.P_Q_pareados,list(LABELS)]
clim=[]
for var in LABELS:
    for month,s in paired[var].groupby(paired.index.month):
        clim.append({'variable':var,'mes_calendario':month,'n_anos':len(s),'media':s.mean(),'mediana':s.median(),'sd':s.std(),'p10':s.quantile(.1),'q25':s.quantile(.25),'q75':s.quantile(.75),'p90':s.quantile(.9)})
climatology=pd.DataFrame(clim)
climatology.to_csv(OUT/'climatologia_exploratoria.csv',index=False)

# 6. Graficas exportables PNG y PDF.
def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)

fig,axes=plt.subplots(3,1,figsize=(15,9),sharex=True,layout='constrained')
for ax,var in zip(axes,LABELS):
    ax.plot(monthly.index,monthly[var],color=COLORS[var],lw=.8,marker='.',ms=2)
    for month in monthly.index[monthly[var].isna()]:
        ax.axvspan(month,month+pd.offsets.MonthBegin(1),color='#d9d9d9',alpha=.75,lw=0)
    ax.set_ylabel(LABELS[var]); ax.set_ylim(bottom=0); ax.grid(alpha=.2)
axes[-1].xaxis.set_major_locator(mdates.YearLocator(5))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
axes[-1].set_xlabel('Fecha')
fig.suptitle('La Vieja–Cartago · 26127040 · 1981–2022\nMeses completos; gris = mes excluido por días faltantes. Sin relleno.')
save(fig,'01_series_cronologicas')

fig,ax=plt.subplots(figsize=(15,4),layout='constrained')
matrix=(counts.Caudal/expected*100).to_frame('pct')
matrix['ano']=matrix.index.year; matrix['mes']=matrix.index.month
im=ax.imshow(matrix.pivot(index='mes',columns='ano',values='pct'),origin='lower',aspect='auto',vmin=0,vmax=100,cmap='YlGn',extent=[1980.5,2022.5,.5,12.5])
ax.set_yticks(range(1,13),NAMES); ax.set_xlabel('Año')
ax.set_title('Porcentaje de días válidos por mes · P y Q tienen la misma disponibilidad')
fig.colorbar(im,ax=ax,label='Días válidos (%)')
save(fig,'02_disponibilidad')

fig,axes=plt.subplots(2,3,figsize=(14,7),layout='constrained')
bins_info=[]
for j,var in enumerate(LABELS):
    values=monthly[var].dropna().to_numpy()
    edges=np.histogram_bin_edges(values,bins='fd')
    bins_info.append({'variable':var,'metodo':'Freedman–Diaconis','n_clases':len(edges)-1,'bordes':edges.tolist()})
    axes[0,j].hist(values,bins=edges,weights=np.ones(len(values))/len(values)*100,color=COLORS[var],edgecolor='white')
    axes[0,j].axvline(values.mean(),color='#333',ls='--',label='Media')
    axes[0,j].axvline(np.median(values),color='#b32945',ls=':',label='Mediana')
    axes[0,j].set_xlabel(LABELS[var]); axes[0,j].set_ylabel('Meses (%)'); axes[0,j].legend(fontsize=8)
    axes[1,j].boxplot(values,orientation='horizontal',whis=1.5,showfliers=True)
    axes[1,j].set_xlabel(LABELS[var]); axes[1,j].set_yticks([])
fig.suptitle('Distribución de meses de todas las estaciones del año · 1981–2022\nPuntos fuera de bigotes se conservan: no son errores demostrados')
save(fig,'03_distribuciones')
(OUT/'criterio_histogramas.json').write_text(json.dumps(bins_info,indent=2),encoding='utf-8')

fig,axes=plt.subplots(2,1,figsize=(11,8),sharex=True,layout='constrained')
for ax,var in zip(axes,['P_mm','Q_m3_s']):
    c=climatology[climatology.variable==var]
    ax.fill_between(c.mes_calendario,c.p10,c.p90,color=COLORS[var],alpha=.12,label='Percentiles 10–90')
    ax.fill_between(c.mes_calendario,c.q25,c.q75,color=COLORS[var],alpha=.25,label='Cuartiles 25–75')
    ax.plot(c.mes_calendario,c.media,'o-',color=COLORS[var],label='Media')
    ax.plot(c.mes_calendario,c.mediana,'--',color=COLORS[var],label='Mediana')
    ax.set_ylabel(LABELS[var]); ax.legend(ncol=2,fontsize=8); ax.grid(alpha=.2)
axes[-1].set_xticks(range(1,13),NAMES)
fig.suptitle('Ciclo anual exploratorio · meses válidos pareados 1981–2022\nBandas = dispersión entre años, no intervalos de confianza')
save(fig,'04_ciclo_anual_exploratorio')

fig,axes=plt.subplots(2,1,figsize=(15,7),sharex=True,layout='constrained')
for ax,var in zip(axes,['P_mm','Q_m3_s']):
    frame=monthly[[var]].copy(); frame['ano']=frame.index.year; frame['mes']=frame.index.month
    mat=frame.pivot(index='mes',columns='ano',values=var)
    cmap=plt.get_cmap('Blues' if var=='P_mm' else 'YlOrBr').copy(); cmap.set_bad('#bbbbbb')
    im=ax.imshow(mat,origin='lower',aspect='auto',cmap=cmap,extent=[1980.5,2022.5,.5,12.5])
    ax.set_yticks([1,3,6,9,12],[NAMES[i-1] for i in [1,3,6,9,12]])
    fig.colorbar(im,ax=ax,label=LABELS[var])
axes[-1].set_xlabel('Año'); fig.suptitle('Meses individuales: variabilidad y vacíos (gris)')
save(fig,'05_mapa_ano_mes')

# Ventanas alrededor de los extremos mensuales de P y Q, con fechas reales.
targets=sorted(set([monthly.P_mm.idxmax(),monthly.P_mm.idxmin(),monthly.Q_m3_s.idxmax(),monthly.Q_m3_s.idxmin()]))
fig,axes=plt.subplots(len(targets),2,figsize=(14,3*len(targets)),layout='constrained',squeeze=False)
for i,target in enumerate(targets):
    begin=target-pd.DateOffset(months=6); end=target+pd.DateOffset(months=7)
    for j,var in enumerate(['P_mm','Q_m3_s']):
        part=monthly.loc[begin:end,var]
        axes[i,j].plot(part.index,part,'o-',color=COLORS[var],ms=3)
        axes[i,j].axvspan(target,target+pd.offsets.MonthBegin(1),color='#ebbe74',alpha=.25)
        axes[i,j].set_title(f'Entorno de {target:%Y-%m}'); axes[i,j].set_ylabel(LABELS[var])
        axes[i,j].xaxis.set_major_locator(mdates.MonthLocator(interval=3)); axes[i,j].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
save(fig,'06_revision_extremos')

# 7. Resumen verificable; el informe interpretativo se redacta despues de leerlo.
summary={'estacion':CODE,'area_km2':AREA,'fuente':'https://doi.org/10.5281/zenodo.18794895','archivo_interno':member,'sha256_serie_original':hashlib.sha256(data).hexdigest(),'inicio':str(calendar[0].date()),'fin':str(calendar[-1].date()),'dias_esperados':len(calendar),'filas_originales':len(raw),'fechas_omitidas':len(calendar.difference(raw.index)),'duplicados':duplicates,'orden_original_correcto':ordered,'valores_invalidos_PQ_no_finitos':len(issues),'Tmin_mayor_Tmax':inverted,'dias_faltantes_P':int(daily.Precipitacion.isna().sum()),'dias_faltantes_Q':int(daily.Caudal.isna().sum()),'meses_esperados':len(monthly),'meses_pareados_completos':len(paired),'meses_excluidos':int((~availability.P_Q_pareados).sum()),'max_hueco_dias':int(gaps.dias.max()),'meses_R_mayor_P':int((paired.R_mm>paired.P_mm).sum()),'R_sobre_P_acumulados_meses_pareados':float(paired.R_mm.sum()/paired.P_mm.sum()),'meses_Q_90pct':int(q90.notna().sum()),'media_Q_100pct':float(monthly.Q_m3_s.mean()),'media_Q_90pct':float(q90.mean()),'IMERG':'Pendiente de descarga; ninguna serie IMERG sintetica o sustitutiva','temperatura':'Tmin y Tmax de MSWX; no se calcula Tmedia sin justificar','metodo':'100% dias validos por mes; sin relleno; percentiles lineales; sd ddof=1'}
(OUT/'resumen_control.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
notes=pd.DataFrame([
    ('Datos','P CHIRPS v2 en mm/día; Q observado CAMELS en m³/s; 1981–2022.'),
    ('Completitud','Mes válido solo si tiene 100 % de días válidos. Sin relleno. Los ceros se conservan.'),
    ('Agregación','P=sum(Pd); Q=mean(Qd); R=86.4/2797.19*sum(Qd). R y P en mm/mes.'),
    ('Estadística','Desviación muestral ddof=1; percentiles interpolación lineal. Histogramas Freedman–Diaconis, frecuencia relativa.'),
    ('Alertas','Bigotes 1.5 IQR, cambios factor 5 y constancia >=7 días son exploratorios; no motivan eliminaciones automáticas.'),
    ('Incertidumbre','Dispersión entre meses/años no equivale a incertidumbre de medición ni a intervalo de confianza.'),
    ('Ciclo anual','Exploratorio; no se completa aún el punto 1.5 ni se demuestra una tendencia.'),
    ('Pendientes','IMERG, temperatura media, antecedentes de estación, regulación/extracciones y validación de delimitación.'),
],columns=['Tema','Criterio'])
with pd.ExcelWriter(OUT/'Exploracion_mensual_La_Vieja.xlsx',engine='openpyxl') as writer:
    tables={'Leer primero':notes,'Series mensuales':monthly.reset_index(),'Estadística':statistics.reset_index(),'Disponibilidad mensual':availability.reset_index(),'Disponibilidad anual':yearly.reset_index(),'Meses excluidos':availability[~availability.P_Q_pareados].reset_index(),'Huecos diarios':gaps,'Extremos':extremes,'Alertas caja':box_flags,'Constancias':run_table,'Cambios bruscos':jump_table,'Comprobación manual':manual,'Ciclo anual exploratorio':climatology,'Sensibilidad Q':sensitivity.reset_index()}
    for name,frame in tables.items():
        frame.to_excel(writer,sheet_name=name,index=False)
    for ws in writer.book:
        ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:
            cell.font=Font(bold=True,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='176B87')
            ws.column_dimensions[cell.column_letter].width=min(45,max(18,len(str(cell.value))+2))
print(json.dumps(summary,indent=2,ensure_ascii=False))
print(statistics.to_string())
print('Climatologia:'); print(climatology[climatology.variable.isin(['P_mm','Q_m3_s'])].to_string(index=False))

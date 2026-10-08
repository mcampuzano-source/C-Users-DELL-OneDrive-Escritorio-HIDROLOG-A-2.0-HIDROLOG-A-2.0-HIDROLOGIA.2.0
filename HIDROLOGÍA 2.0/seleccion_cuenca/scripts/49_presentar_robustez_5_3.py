"""Informe PDF e interfaz Plotly autocontenida de robustez 5.3."""
from pathlib import Path
import json, html, re, shutil, base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import pymupdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import importlib.util

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'la_vieja/documentos';OUT=DOCS/'apartado_5_3'
spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('41_descargar_campos_globales.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
MONTHS=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
NAMES={'CHIRPS':'Precipitación CHIRPS','IMERG':'Precipitación IMERG','Q':'Caudal Cartago','sst':'SST ERSSTv5','slp':'SLP NCEP/NCAR R1','z500':'Z500 NCEP/NCAR R1'}
metadata=json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
summary=pd.read_csv(OUT/'resumen_mensual.csv');regions=pd.read_csv(OUT/'regiones_sst.csv');sens=pd.read_csv(OUT/'sensibilidad_fuentes.csv')
group=summary.groupby('key',sort=False).agg(delta=('mean_abs_detrend_delta','mean'),neff=('neff_median','median'),by=('area_by_pct','mean'),stable=('area_candidate_pct','mean'),loo=('mean_loo_max_delta','mean'),split=('pattern_subperiods','mean')).reset_index()
top=summary.sort_values(['area_candidate_pct','largest_connected_candidate_cells'],ascending=False).head(8)
refs=[
 ('Bretherton et al. (1999). The Effective Number of Spatial Degrees of Freedom of a Time-Varying Field. Journal of Climate, 12, 1990-2009. Apéndice A: tamaño efectivo para correlaciones.', 'https://journals.ametsoc.org/abstract/journals/clim/12/7/1520-0442_1999_012_1990_tenosd_2.0.co_2.xml'),
 ('Benjamini y Yekutieli (2001). The control of the false discovery rate in multiple testing under dependency. Annals of Statistics, 29, 1165-1188.', 'https://www.math.tau.ac.il/~ybenja/depApr27.pdf'),
 ('Wilks (2016). The Stippling Shows Statistically Significant Grid Points: How Research Results are Routinely Overstated and Overinterpreted, and What to Do about It. BAMS, 97, 2263-2273.', 'https://doi.org/10.1175/BAMS-D-15-00267.1'),
 ('SciPy. false_discovery_control: implementaciones BH y BY.', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html')]

minne=summary.neff_min.min();maxne=summary.neff_median.max()
texts=[
 ('Presentación, calendario y máscaras',
  'Se conservan las doce combinaciones del 5.2: CHIRPS, IMERG y Q frente a SST, SLP y Z500 con rezago cero, y Q frente a los tres campos con rezago de un mes. No se busca un rezago óptimo. El campo antecede a la respuesta cuando ell=1. La muestra común contiene 285 meses completos de 1998-2022, con 22-25 pares de años por mes. Se exige n>=20 y varianza no nula para correlaciones completas; SST conserva su máscara terrestre y Z500 la máscara de presión superficial. Gris significa sin estimación válida, no correlación cero. Todos los mapas de correlación y sus diferencias usan escala divergente fija de -1 a 1; los mapas de n y n efectivo tienen escala secuencial y unidades de años. La estrella ubica aproximadamente La Vieja; la delimitación exacta se conserva en la cartografía de contexto del informe. Los mapas se calculan por celda, no entre celdas.'),
 ('Retiro de tendencias en ambas variables',
  'Para cada mes calendario y celda se ajustan dos regresiones OLS, una para la respuesta de cuenca y otra para el campo global, contra el año real centrado, usando exactamente los mismos pares válidos. Se correlacionan sus residuos. Los huecos permanecen en sus años originales. Esto equivale a una correlación parcial lineal que controla el año, no a probar causalidad. Se comparan r de anomalías y r sin tendencia, sus diferencias espaciales y la correlación ponderada entre mapas. El ciclo mensual ya fue retirado por la climatología fija del 5.2. En subperiodos y exclusiones se reajustan las dos tendencias para evitar usar la tendencia de años retirados.'),
 ('Persistencia interanual e inferencia aproximada',
  'La dependencia relevante se estima entre años consecutivos del mismo mes. No se trata enero y febrero como observaciones consecutivas ni se conectan artificialmente años separados por huecos. Por celda, rhoX y rhoY son las autocorrelaciones anuales de orden uno de los mismos pares; se requieren al menos diez pares anuales adyacentes. Se adopta la aproximación AR(1) n_eff = n(1-rhoX*rhoY)/(1+rhoX*rhoY), limitada a [3,n], basada en el tamaño efectivo para correlaciones de Bretherton et al. (1999). El límite superior evita aumentar la información por autocorrelación estimada negativa. La prueba bilateral usa t=|r| sqrt(df/(1-r²)), con df=n_eff-2 para anomalías y df=n_eff-3 al controlar el año. Con df<=1 no se emite p. Los p son aproximados: n corto, no normalidad, incertidumbre de rho y memoria de orden superior pueden afectar su calibración; no son una garantía exacta de cobertura o significancia.'),
 ('Una familia de pruebas y control FDR',
  f'La familia se fija antes de interpretar máximos: todas las celdas con p admisible, doce meses, doce combinaciones y ambas representaciones Pearson. Contiene {metadata["family_size"]:,} pruebas. No se reinicia el ajuste por mapa, mes o región ni se escoge ell por el mayor coeficiente. Se aplica Benjamini-Yekutieli (BY) con nivel 0,05, válido frente a dependencia arbitraria si los p individuales son válidos (Benjamini y Yekutieli, 2001). Benjamini-Hochberg (BH) se reporta solo como sensibilidad bajo independencia o dependencia positiva apropiada. El contraste p<0,05 sin corrección ilustra la diferencia entre significancia puntual y evidencia tras la búsqueda espacial; Wilks (2016) explica por qué los puntos aislados se sobreinterpretan. Spearman sin tendencia se conserva como contraste descriptivo y no amplía la familia inferencial. BY no repara p mal calibrados ni convierte una asociación en mecanismo causal.'),
 ('Subperiodos, años extremos y regiones coherentes',
  'Los subperiodos se fijan en 1998-2009 y 2010-2022, sin elegir el corte por los resultados. Exigen al menos diez años por celda y usan tendencias propias; sus coeficientes se presentan como estabilidad descriptiva, sin pruebas FDR independientes. Al excluir cada año se reajusta OLS y se guarda el rango de r y el mayor cambio absoluto. También se retiran conjuntamente los dos años con mayor anomalía absoluta de la respuesta de cada mes, usando los mismos años para todo el campo; no se borran observaciones del archivo original. Esta comprobación detecta influencia, no demuestra que los extremos sean errores. Se contrasta CHIRPS con IMERG sobre iguales fechas y rejillas. Zaragoza tiene 14 meses completos, insuficientes para este contraste interanual.'),
 ('Criterio descriptivo de estabilidad',
  'Se denomina estable una celda con |r sin tendencia|>=0,30, igual signo en ambos subperiodos y en todas las exclusiones individuales, y cambio máximo leave-one-year-out <=0,20. Los umbrales se declaran como reglas descriptivas, no como una segunda prueba o un intervalo de confianza. Una celda candidata requiere además q_BY<=0,05. Las áreas se ponderan por coseno de latitud sobre celdas con correlación completa válida. Se reporta el mayor componente contiguo de cuatro vecinos, con continuidad de longitud en la costura global, para evitar interpretar píxeles aislados. Las tres regiones SST (Niño 3.4, Atlántico tropical norte y Caribe) estaban definidas en el 5.2; aquí sus medias de coeficientes son diagnósticos de extensión regional y no la correlación de un índice espacial.'),
]
candidate=summary[summary.candidate_cells>0]
if len(candidate):
    lead=candidate.sort_values('area_candidate_pct',ascending=False).iloc[0]
    interpretation=(f'El criterio conjunto deja celdas candidatas en {len(candidate)} de los 144 mapas sin tendencia. La mayor fracción se encuentra en {lead.key}, {MONTHS[int(lead.month)-1]}: {lead.area_candidate_pct:.2f}% del dominio válido ponderado y {int(lead.candidate_cells)} celdas; su mayor componente contiguo contiene {int(lead.largest_connected_candidate_cells)} celdas. Estos máximos describen toda la búsqueda ya corregida, no una selección de rezago. La tabla y el atlas permiten verificar extensión, signo y continuidad; la explicación física se desarrollará en 5.4.')
else:
    interpretation='Ninguna celda reúne simultáneamente BY y todos los criterios de estabilidad. No corresponde declarar una teleconexión robusta con esta muestra y esta familia. Los patrones descriptivos pueden orientar hipótesis para 5.4, manteniendo la diferencia entre falta de evidencia y prueba de ausencia de relación.'
texts += [
 ('Resultados de la muestra y alcance',
  f'La mediana espacial de n efectivo por mapa varía entre {summary.neff_median.min():.1f} y {maxne:.1f} años; el mínimo de una celda admisible es {minne:.1f}. El cambio espacial medio |r sin tendencia-r original| varía de {summary.mean_abs_detrend_delta.min():.3f} a {summary.mean_abs_detrend_delta.max():.3f}. Los campos no deben tratarse como {metadata["family_size"]:,} observaciones independientes. '+interpretation),
 ('Sensibilidad a la fuente y límites de interpretación',
  f'La correlación espacial ponderada entre los mapas CHIRPS e IMERG sin tendencia varía de {sens.pattern_detrended_CHIRPS_IMERG.min():.2f} a {sens.pattern_detrended_CHIRPS_IMERG.max():.2f}; sus diferencias absolutas medias van de {sens.mean_abs_delta.min():.3f} a {sens.mean_abs_delta.max():.3f}. Es un acuerdo de patrones de dos productos espaciales; no valida ninguno contra una verdad independiente ni sustituye la lluvia local. El caudal integra almacenamiento, regulación y respuesta de cuenca: una región climática asociada no identifica por sí sola un proceso. Las comparaciones entre subperiodos tienen 10-13 años, tendencias estimadas y baja potencia. Sin una validación adicional de memoria de orden superior, la inferencia se presenta como aproximada y condicionada al modelo AR(1). La conclusión física no se extrae de unos pocos coeficientes altos.'),
 ('Reproducibilidad y controles',
  'El script 48 reproduce los cálculos y el 49 las figuras y documentos. Se conservan NetCDF con n, n efectivo, autocorrelaciones, p, q BH/BY, coeficientes y sensibilidad por celda; tablas CSV y Excel; metadatos, versiones y huellas SHA-256. Se comprueba OLS con años reales y faltantes contra mínimos cuadrados independientes, autocorrelación sin conectar huecos, continuidad de componentes en longitud y reproducción de los 144 mapas Pearson del 5.2 a precisión numérica. El visor usa rejillas nativas y redondea coeficientes a 0,001; no redondea datos para los cálculos. No se descargaron ni rellenaron nuevas observaciones. La IA apoyó programación y redacción; el grupo debe verificar decisiones y explicar los resultados en la defensa.'),
]

styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyHydro',fontName='Helvetica',fontSize=9.5,leading=13,spaceAfter=9));styles.add(ParagraphStyle(name='CellHydro',fontName='Helvetica',fontSize=7.4,leading=9))
def p(t,style='BodyHydro'):return Paragraph(html.escape(t),styles[style])
def table(headers,rows,widths):
    t=Table([[p(str(c),'CellHydro') for c in row] for row in [headers]+rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deebf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#6c8796')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
story=[p('5.3. Robustez y presentación de los patrones','Heading1')]
for title,text in texts[:6]:story += [p(title,'Heading2'),p(text)]
story += [p('Diagnóstico agregado por combinación','Heading2'),p('Promedio de los doce diagnósticos mensuales. Las fracciones son áreas del dominio válido ponderadas por coseno de latitud; no porcentajes de años ni una prueba global de campo.')]
rows=[[r.key,f'{r.delta:.3f}',f'{r.neff:.1f}',f'{r.by:.2f}',f'{r.stable:.2f}',f'{r.loo:.3f}',f'{r.split:.2f}'] for r in group.itertuples()]
story +=[table(['Combinación','Delta r','n eff','BY %','Candidata %','LOO delta','Patrón subperiodos'],rows,[130,49,42,50,61,57,94])]
for title,text in texts[6:]:story +=[p(title,'Heading2'),p(text)]
story +=[p('Regiones candidatas de mayor extensión','Heading2')]
if len(candidate):
    rows=[[r.key,MONTHS[int(r.month)-1],f'{r.area_candidate_pct:.2f}',str(int(r.candidate_cells)),str(int(r.largest_connected_candidate_cells))] for r in top.itertuples() if r.candidate_cells>0]
    story +=[table(['Combinación','Mes','Área %','Celdas','Mayor región contigua'],rows,[170,48,65,75,125])]
else:story +=[p('No hay regiones que superen el criterio conjunto. El atlas mantiene todos los coeficientes descriptivos y las máscaras para que se examine el patrón completo.')]
story +=[p('Fuentes metodológicas','Heading2')]
for title,url in refs:story +=[p(title),Paragraph('<link href="'+url+'" color="#24577a">'+html.escape(url)+'</link>',styles['CellHydro']),Spacer(1,8)]
story +=[p('Lectura del atlas','Heading2'),p('Por combinación se muestran cuatro láminas: correlación sin tendencia (puntos negros: BY; círculos verdes: BY y estabilidad), subperiodo inicial, subperiodo final y n efectivo anual. Todas incluyen doce meses. Las láminas de subperiodos no contienen inferencia; sus mínimos n se indican en cada panel. El visor añade anomalías originales, diferencia, n real, influencia de exclusiones y q BY.')]
SimpleDocTemplate(str(OUT/'texto_5_3.pdf'),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=55).build(story)

coast=json.loads((DOCS/'apartado_5_1/ne_110m_coastline.geojson').read_bytes());lines=[];cx=[];cy=[]
for f in coast['features']:
    parts=f['geometry']['coordinates'];parts=[parts] if f['geometry']['type']=='LineString' else parts
    for part in parts:
        a=np.asarray(part,float);a[np.abs(np.diff(a[:,0],prepend=a[0,0]))>180]=np.nan;lines.append(a)
        cx.extend([None if not np.isfinite(x) else float(x) for x in a[:,0]]+[None]);cy.extend([None if not np.isfinite(y) else float(y) for y in a[:,1]]+[None])

atlas=pymupdf.open(OUT/'texto_5_3.pdf');bookmarks=[]
browser_data=json.loads((OUT/'mapas_binarios.json').read_text(encoding='utf-8'))
layers=[('r_detrended','Pearson sin tendencia','n_pairs'),('r_1998_2009','Pearson 1998-2009 sin tendencia','n_1998_2009'),('r_2010_2022','Pearson 2010-2022 sin tendencia','n_2010_2022'),('neff_detrended','Tamaño efectivo anual AR(1)','n_pairs')]
for key in group.key:
    ds=reader.load(OUT/(key+'.nc'))
    for name in ['n_1998_2009','n_2010_2022','by_significant']:
        v=(ds.q_by_detrended.values<=.05).astype(float) if name=='by_significant' else ds[name].values
        v=np.where(np.isfinite(ds.r_detrended.values),v,np.nan)
        a=np.where(np.isfinite(v),v,-32768).astype('<i2')
        browser_data[key]['layers'][name]={'scale':1,'data':base64.b64encode(a.tobytes()).decode('ascii')}
    for layer,label,nlayer in layers:
        fig,axes=plt.subplots(4,3,figsize=(12.8,9),sharex=True,sharey=True)
        fig.subplots_adjust(left=.05,right=.975,top=.895,bottom=.16,wspace=.06,hspace=.27)
        for m,ax in enumerate(axes.flat,1):
            a=ds[layer].sel(month=m).values;counts=ds[nlayer].sel(month=m).values;ok=np.isfinite(a)
            im=ax.pcolormesh(ds.lon,ds.lat,a,shading='auto',cmap='viridis' if layer.startswith('neff') else 'RdBu_r',vmin=3 if layer.startswith('neff') else -1,vmax=25 if layer.startswith('neff') else 1,rasterized=True)
            ax.set_facecolor('#ededed');ax.add_collection(LineCollection(lines,linewidths=.32,colors='#444'));ax.plot(-75.7,4.45,'*',color='black',ms=4)
            if layer=='r_detrended':
                sig=ds.q_by_detrended.sel(month=m).values<=.05;stable=ds.candidate_by_stable.sel(month=m).values>0
                # All discoveries are shown; no selection of the strongest cell or lag.
                iy,ix=np.where(sig);ax.scatter(ds.lon.values[ix],ds.lat.values[iy],s=1,c='black',alpha=.4,rasterized=True)
                iy,ix=np.where(stable);ax.scatter(ds.lon.values[ix],ds.lat.values[iy],s=4,facecolors='none',edgecolors='#188038',linewidths=.3,rasterized=True)
            ns=counts[ok];count='sin estimación' if not len(ns) else f'n={int(ns.min())}-{int(ns.max())}'
            if layer.startswith('neff') and ok.any():count+=f'; eff {a[ok].min():.1f}-{a[ok].max():.1f}'
            ax.set_title(f'{MONTHS[m-1]}: {count}',fontsize=8,pad=3)
            ax.set(xlim=(-180,180),ylim=(-90,90),xticks=[-180,-90,0,90,180],yticks=[-90,-45,0,45,90]);ax.tick_params(labelsize=6,length=2)
            if m>9:ax.set_xlabel('Longitud (°)',fontsize=7)
            if (m-1)%3==0:ax.set_ylabel('Latitud (°)',fontsize=7)
        response=ds.attrs['response'];field=ds.attrs['field'];lag=int(ds.attrs['lag_months'])
        fig.suptitle(f'{NAMES[response]} frente a {NAMES[field]}\n{label}; respuesta 1998-2022; ell={lag} mes(es)',fontsize=12,y=.98)
        cb=fig.colorbar(im,cax=fig.add_axes([.32,.082,.36,.013]),orientation='horizontal');cb.ax.tick_params(labelsize=7)
        cb.set_label('Años efectivos (aproximación)' if layer.startswith('neff') else 'Coeficiente adimensional (-1 a 1)',fontsize=8)
        note='Negro: q BY<=0,05; verde: BY y estabilidad descriptiva. Familia global: ambas representaciones, celdas, meses y rezagos.' if layer=='r_detrended' else 'Subperiodos: diagnóstico descriptivo; mínimo 10 años; tendencias reajustadas.' if layer.startswith('r_') else 'Persistencia entre años consecutivos del mismo mes; no se conectan huecos. Escala secuencial de 3 a 25 años.'
        fig.text(.05,.025,note+'\nGris: sin estimación válida. SST enmascara tierra. Estrella: La Vieja (aproximada).',fontsize=7,linespacing=1.5)
        name=key+'_'+layer;fig.savefig(OUT/(name+'.pdf'));fig.savefig(OUT/(name+'.png'),dpi=120);plt.close(fig)
        f=pymupdf.open(OUT/(name+'.pdf'));bookmarks.append([1,key+' '+label,len(atlas)+1]);atlas.insert_pdf(f);f.close()
    print('Atlas',key,flush=True)
atlas.set_toc(bookmarks);atlas.save(OUT/'punto_5_3.pdf',garbage=4,deflate=True);atlas.close()

body=''.join('<h4>'+html.escape(title)+'</h4><p>'+html.escape(text)+'</p>' for title,text in texts)
body+='<h4>Diagnóstico por combinación</h4>'+group.rename(columns={'key':'Combinación','delta':'Delta r medio','neff':'n efectivo','by':'Área BY (%)','stable':'Área candidata (%)','loo':'Máximo LOO medio','split':'Patrón subperiodos'}).round(3).to_html(index=False,border=0)
body+='<h4>Fuentes metodológicas</h4>'+''.join('<p>'+html.escape(t)+' <a href="'+u+'">Fuente</a></p>' for t,u in refs)
payload=json.dumps(browser_data,separators=(',',':'))
body+='''<div class="controles53"><label>Combinación <select id="combo53"></select></label> <label>Capa <select id="capa53">
<option value="r_detrended">Pearson sin tendencia</option><option value="r_original">Pearson anomalías originales</option><option value="delta">Diferencia sin tendencia - original</option><option value="r_1998_2009">1998-2009 sin tendencia</option><option value="r_2010_2022">2010-2022 sin tendencia</option><option value="n_pairs">Años válidos</option><option value="neff_detrended">Años efectivos</option><option value="loo_max_delta">Influencia máxima de un año</option><option value="q_by_detrended">q BY global</option><option value="candidate_by_stable">BY y estabilidad</option></select></label> <label>Mes <select id="mes53"><option value="0">Doce meses</option>'''+''.join(f'<option value="{i+1}">{m}</option>' for i,m in enumerate(MONTHS))+'''</select></label> <button id="csv53">Exportar mes CSV</button></div><p id="nota53"></p><div id="mapas53" style="height:1100px"></div>'''
script=r'''<script id="script53">(function(){
const DATA=__DATA__,COAST=__COAST__,MONTHS=__MONTHS__;
const names=__NAMES__,E=id=>document.getElementById(id),cache={};
function layer(d,key){const id=E('combo53').value+':'+key;if(cache[id])return cache[id];const o=d.layers[key],raw=atob(o.data),buf=new ArrayBuffer(raw.length),bytes=new Uint8Array(buf);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);const view=new DataView(buf),out=[];for(let i=0;i<raw.length;i+=2){const v=view.getInt16(i,true);out.push(v===-32768?null:v/o.scale);}cache[id]=out;return out;}
function z(d,key,m){if(key==='delta'){const a=z(d,'r_detrended',m),b=z(d,'r_original',m);return a.map((r,i)=>r.map((v,j)=>v===null||b[i][j]===null?null:v-b[i][j]));}const a=layer(d,key),valid=layer(d,'r_detrended'),w=d.lon.length,h=d.lat.length,start=m*w*h;return Array.from({length:h},(_,i)=>a.slice(start+i*w,start+(i+1)*w).map((v,j)=>valid[start+i*w+j]===null?null:v));}
function draw(){const d=DATA[E('combo53').value],mode=E('capa53').value,selected=Number(E('mes53').value),months=selected?[selected-1]:Array.from({length:12},(_,i)=>i),traces=[];
const diverging=mode.startsWith('r_')||mode==='delta',seqN=mode==='n_pairs'||mode==='neff_detrended';const layout={title:{text:names[d.response]+' frente a '+names[d.field]+' · '+E('capa53').selectedOptions[0].text+' · ell='+d.lag},margin:{l:45,r:30,t:100,b:90},annotations:[],showlegend:false,paper_bgcolor:'#fff',plot_bgcolor:'#eee'};
months.forEach((m,k)=>{const cols=selected?1:3,rows=selected?1:4,row=Math.floor(k/cols),col=k%cols,suffix=k?' '+(k+1):'',s=k?String(k+1):'',xa='x'+s,ya='y'+s,xd=[col/cols+.015,(col+1)/cols-.015],yd=[1-(row+1)/rows+.045,1-row/rows-.035];
layout['xaxis'+s]={domain:xd,anchor:ya,range:[-180,180],tickvals:[-180,-90,0,90,180],title:row===rows-1?'Longitud (°)':''};layout['yaxis'+s]={domain:yd,anchor:xa,range:[-90,90],tickvals:[-90,-45,0,45,90],title:col===0?'Latitud (°)':''};
const zz=z(d,mode,m),nn=z(d,mode==='r_1998_2009'?'n_1998_2009':mode==='r_2010_2022'?'n_2010_2022':'n_pairs',m),ne=z(d,'neff_detrended',m),q=z(d,'q_by_detrended',m),flags=z(d,'candidate_by_stable',m),sig=z(d,'by_significant',m);let ns=[];zz.forEach((r,i)=>r.forEach((v,j)=>{if(v!==null&&nn[i][j]!==null)ns.push(nn[i][j]);}));
layout.annotations.push({text:MONTHS[m]+' · n='+Math.min(...ns)+'-'+Math.max(...ns),x:(xd[0]+xd[1])/2,y:yd[1]+.015,xref:'paper',yref:'paper',showarrow:false,font:{size:11}});
const custom=nn.map((r,i)=>r.map((v,j)=>[v,ne[i][j],q[i][j],flags[i][j]]));
traces.push({type:'heatmap',x:d.lon,y:d.lat,z:zz,customdata:custom,xaxis:xa,yaxis:ya,zmin:diverging?-1:seqN?0:0,zmax:diverging?1:seqN?25:1,colorscale:diverging?'RdBu':'Viridis',reversescale:diverging,hoverongaps:false,showscale:k===0,colorbar:{orientation:'h',x:.5,y:-.1,len:.5,thickness:12,title:diverging?'Coeficiente adimensional':seqN?'Años':'Diagnóstico'},hovertemplate:'Lon %{x} · Lat %{y}<br>Valor %{z:.3f}<br>n=%{customdata[0]} · n eff=%{customdata[1]:.2f}<br>q BY=%{customdata[2]:.3f} · candidata=%{customdata[3]}<extra></extra>'});
traces.push({type:'scatter',mode:'lines',x:COAST.x,y:COAST.y,xaxis:xa,yaxis:ya,line:{color:'#444',width:.5},hoverinfo:'skip'});
if(mode==='r_detrended'){let sx=[],sy=[],cx=[],cy=[];sig.forEach((r,i)=>r.forEach((v,j)=>{if(v===1){sx.push(d.lon[j]);sy.push(d.lat[i]);}if(flags[i][j]===1){cx.push(d.lon[j]);cy.push(d.lat[i]);}}));traces.push({type:'scatter',mode:'markers',x:sx,y:sy,xaxis:xa,yaxis:ya,marker:{size:2,color:'black'},hoverinfo:'skip'},{type:'scatter',mode:'markers',x:cx,y:cy,xaxis:xa,yaxis:ya,marker:{size:4,symbol:'circle-open',color:'#188038'},hoverinfo:'skip'});}
traces.push({type:'scatter',mode:'markers',x:[-75.7],y:[4.45],xaxis:xa,yaxis:ya,marker:{symbol:'star',size:7,color:'black'},hovertemplate:'La Vieja (ubicación aproximada)<extra></extra>'});});
E('mapas53').style.height=selected?'650px':'1100px';E('nota53').textContent='Respuesta 1998-2022; ell='+d.lag+' (campo antecedente si ell=1). Negro: BY global; verde: BY y estabilidad. Gris: sin estimación. n corresponde al periodo de la capa. n efectivo y q corresponden a la muestra completa sin tendencia. q se muestra redondeado a 0,001; las máscaras de decisión usan precisión completa.';
Plotly.react('mapas53',traces,layout,{responsive:true,displaylogo:false});E('csv53').disabled=!selected;
}
function init(){if(!E('combo53')||!window.Plotly)return;Object.keys(DATA).forEach(k=>{const o=document.createElement('option');o.value=k;o.textContent=k;E('combo53').appendChild(o);});['combo53','capa53','mes53'].forEach(id=>E(id).addEventListener('change',draw));E('csv53').addEventListener('click',()=>{const d=DATA[E('combo53').value],m=Number(E('mes53').value)-1,mode=E('capa53').value,a=z(d,mode,m),n=z(d,'n_pairs',m),ne=z(d,'neff_detrended',m),q=z(d,'q_by_detrended',m);let lines=['combinacion,mes,latitud,longitud,capa,valor,n_total,n_efectivo,q_BY_redondeado'];a.forEach((r,i)=>r.forEach((v,j)=>{if(v!==null)lines.push([E('combo53').value,m+1,d.lat[i],d.lon[j],mode,v,n[i][j],ne[i][j],q[i][j]].join(','));}));const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'})),ael=document.createElement('a');ael.href=url;ael.download='robustez_'+E('combo53').value+'_mes'+(m+1)+'.csv';ael.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});draw();}
if(document.readyState==='complete')init();else window.addEventListener('load',init);
})();</script>'''
script=script.replace('__DATA__',payload).replace('__COAST__',json.dumps({'x':cx,'y':cy})).replace('__MONTHS__',json.dumps(MONTHS)).replace('__NAMES__',json.dumps(NAMES))
basin=json.loads((DOCS.parent/'topografia/cuenca_la_vieja.geojson').read_text(encoding='utf-8'))
bx=[];by=[]
for feature in basin['features']:
    g=feature['geometry'];polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    for poly in polygons:
        bx.extend([c[0] for c in poly[0]]+[None]);by.extend([c[1] for c in poly[0]]+[None])
script=script.replace('function layer(d,key)',"const BASIN="+json.dumps({'x':bx,'y':by})+";\nfunction layer(d,key)")
script=script.replace("traces.push({type:'scatter',mode:'markers',x:[-75.7]", "traces.push({type:'scatter',mode:'lines',x:BASIN.x,y:BASIN.y,xaxis:xa,yaxis:ya,line:{color:'black',width:1.2},hoverinfo:'skip'});\ntraces.push({type:'scatter',mode:'markers',x:[-75.7]")
body+=script;(OUT/'contenido_5_3.html').write_text(body,encoding='utf-8')
hpath=DOCS/'informe_interactivo.html';h=hpath.read_text(encoding='utf-8');shutil.copy2(hpath,OUT/'respaldo_html_antes_5_3.html')
block='<!-- PUNTO_5_3_INICIO --><section class="panel" id="robustez-patrones-53">'+body+'</section><!-- PUNTO_5_3_FIN -->'
if '<!-- PUNTO_5_3_INICIO -->' in h:h=re.sub(r'<!-- PUNTO_5_3_INICIO -->.*?<!-- PUNTO_5_3_FIN -->',lambda _:block,h,flags=re.S)
else:h=h.replace('</main>',block+'</main>',1)
needle="else if(n===5&&i===1)mover(se,document.getElementById('mapas-mensuales-52'));else pendiente"
new="else if(n===5&&i===1)mover(se,document.getElementById('mapas-mensuales-52'));else if(n===5&&i===2)mover(se,document.getElementById('robustez-patrones-53'));else pendiente"
if needle in h:h=h.replace(needle,new)
else:assert "document.getElementById('robustez-patrones-53')" in h
# Historical 5.2 statements point explicitly to the now completed robustness.
h=h.replace('autocorrelación, pruebas múltiples y sensibilidad temporal se evaluarán en 5.3.','autocorrelación, pruebas múltiples y sensibilidad temporal se evalúan en el apartado 5.3.')
hpath.write_text(h,encoding='utf-8');shutil.copy2(hpath,DOCS.parents[3]/'Informe_Hidrologia_interactivo.html')
(OUT/'metodologia.md').write_text('# 5.3. Robustez\n\n'+'\n\n'.join('## '+title+'\n\n'+text for title,text in texts)+'\n\n## Referencias\n\n'+'\n\n'.join(t+' '+u for t,u in refs),encoding='utf-8')
(OUT/'README.md').write_text('''# Robustez 5.3

Reproducción: scripts 48_calcular_robustez_5_3.py, 49_presentar_robustez_5_3.py y 50_integrar_5_3.py.
Excel: ejecutar 51_excel_robustez.mjs con @oai/artifact-tool (exportación estática de las tablas).
Verificación del visor sin navegador: 52_verificar_html_5_3.mjs.
La inferencia es Pearson bilateral con n efectivo AR(1) anual y FDR BY global.
BH es sensibilidad; Spearman y los subperiodos son descriptivos.
Se conserva precisión completa en los NetCDF; el visor redondea a 0,001.
Excel es una exportación de diagnósticos calculados en Python, no un motor de inferencia.
Datos originales: imerg_poligono/series_alineadas.csv y datos/clima_global_5_1.
Ver metodologia.md, resultados.json y verificacion_reproduccion_5_2.csv.
No ejecutar el script 47 como último paso: genera la versión histórica sin 5.3.
''',encoding='utf-8')
print('5.3 presentado con atlas y visor autocontenido.',flush=True)

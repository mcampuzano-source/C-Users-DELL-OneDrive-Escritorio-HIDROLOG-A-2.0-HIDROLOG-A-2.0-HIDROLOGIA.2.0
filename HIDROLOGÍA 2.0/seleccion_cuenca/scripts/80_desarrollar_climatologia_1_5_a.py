"""Climatologías comparables, dispersión interanual y mapas año-mes para 1.5.a."""
from pathlib import Path
import pandas as pd,numpy as np,json,html,base64,shutil,re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import pymupdf as fitz
D=Path(__file__).resolve().parents[1]/'la_vieja/documentos';B=D.parent;R=D.parents[3];O=D/'apartado_1_5';O.mkdir(exist_ok=True)
F=D/'revision_tablas/fuentes_originales'
for name,file in [('Hydro','lmroman10-regular.ttf'),('HydroBold','lmroman10-bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(F/file)));fontManager.addfont(str(F/file))
plt.rcParams.update({'font.family':'Latin Modern Roman','font.size':10,'axes.titlesize':12,'axes.labelsize':10,'legend.fontsize':9,'pdf.fonttype':42})
def read(path):return pd.read_csv(path,parse_dates=['mes']).set_index('mes')
a=read(B/'punto_1/series_mensuales.csv');i=read(D/'imerg_poligono/IMERG_mensual_poligono_1998_2022.csv');t=read(D/'temperatura_media_ERA5_Land_mensual.csv')
x=a[['P_mm','Q_m3_s','R_mm']].join(i[['P_IMERG_poligono_mm']]).join(t[['Tmedia_ERA5_Land_C']]).loc['1998':'2022'].dropna()
variables=[('P_mm','P_L: precipitación de referencia CHIRPS','mm/mes'),('P_IMERG_poligono_mm','P_I: precipitación IMERG de cuenca','mm/mes'),('Q_m3_s','Q: caudal en Cartago','m³/s'),('R_mm','R: escorrentía equivalente','mm/mes'),('Tmedia_ERA5_Land_C','Temperatura media ERA5-Land','°C')]
months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
assert len(x)==285 and x.index.is_unique
records=[]
for v,label,unit in variables:
    for month,s in x[v].groupby(x.index.month):
        qs=s.quantile([.1,.25,.5,.75,.9],interpolation='linear')
        records.append({'variable':v,'mes':int(month),'n_anios':len(s),'media':s.mean(),'mediana':qs.loc[.5],'desviacion_estandar':s.std(ddof=1),'Q25':qs.loc[.25],'Q75':qs.loc[.75],'P10':qs.loc[.1],'P90':qs.loc[.9]})
c=pd.DataFrame(records);c.to_csv(O/'climatologia_12_meses_comun.csv',index=False);x.to_csv(O/'series_comunes_1998_2022.csv',index_label='mes')
reference=pd.read_csv(D/'apartado_5_4/climatologia_comun.csv')
for v,_,_ in variables:
    old={'P_mm':'P_CHIRPS_mm','P_IMERG_poligono_mm':'P_IMERG_poligono_mm','Q_m3_s':'Q_m3_s','R_mm':'R_mm','Tmedia_ERA5_Land_C':'Tmedia_ERA5_Land_C'}[v]
    assert np.allclose(c[c.variable==v].media,reference[old+'_mean'])
verification={'n_meses_comunes':len(x),'periodo':'1998-01 a 2022-12','n_por_mes':{str(k):int(v) for k,v in x.groupby(x.index.month).size().items()},'cuantiles':'Interpolación lineal, Hyndman-Fan tipo 7','desviacion_estandar':'Muestral, ddof=1','medias_coinciden_con_5_4':True,'fuentes':[str(B/'punto_1/series_mensuales.csv'),str(D/'imerg_poligono/IMERG_mensual_poligono_1998_2022.csv'),str(D/'temperatura_media_ERA5_Land_mensual.csv')]}
(O/'verificacion_calculos.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
figures=[]
for batch in [[0,1],[2,3,4]]:
    fig,axs=plt.subplots(len(batch),1,figsize=(9,3.0*len(batch)),layout='constrained',squeeze=False)
    for ax,k in zip(axs[:,0],batch):
        v,label,unit=variables[k];z=c[c.variable==v];m=z.mes.to_numpy()
        ax.fill_between(m,z.P10,z.P90,color='#cbdce5',label='P10–P90 entre años');ax.fill_between(m,z.Q25,z.Q75,color='#83acbb',label='Q25–Q75 entre años')
        ax.plot(m,z.media,'o-',color='#17485e',label='Media');ax.plot(m,z.mediana,'s--',color='#b36937',label='Mediana')
        ax.set(title=label,ylabel=unit,xticks=range(1,13),xticklabels=months,xlim=(.7,12.3));ax.grid(alpha=.2);ax.legend(ncol=2,loc='best')
    name='ciclos_precipitacion' if batch[0]==0 else 'ciclos_caudal_escorrentia_temperatura';fig.savefig(O/(name+'.png'),dpi=160);fig.savefig(O/(name+'.pdf'));plt.close(fig);figures.append((name,'Las bandas representan la dispersión de los valores de cada mes entre años; no son intervalos de confianza de la media.'))
for batch in [[0,1],[2,3],[4]]:
    fig,axs=plt.subplots(1,len(batch),figsize=(4.8*len(batch),8),layout='constrained',squeeze=False)
    for ax,k in zip(axs[0],batch):
        v,label,unit=variables[k];matrix=x.assign(anio=x.index.year,mes_cal=x.index.month).pivot(index='anio',columns='mes_cal',values=v).reindex(index=range(1998,2023),columns=range(1,13))
        matrix.to_csv(O/(v+'_ano_mes.csv'),index_label='anio')
        cmap=plt.get_cmap('YlGnBu' if k<4 else 'YlOrRd').copy();cmap.set_bad('#dddddd')
        limits=(float(x[['P_mm','P_IMERG_poligono_mm']].min().min()),float(x[['P_mm','P_IMERG_poligono_mm']].max().max())) if k<2 else (float(x[v].min()),float(x[v].max()))
        im=ax.imshow(matrix.to_numpy(),aspect='auto',cmap=cmap,vmin=limits[0],vmax=limits[1]);ax.set(title=label,xticks=range(12),xticklabels=months,yticks=range(25),yticklabels=range(1998,2023));ax.tick_params(axis='x',labelrotation=90);fig.colorbar(im,ax=ax,label=unit,shrink=.7)
    name='ano_mes_'+str(batch[0]);fig.savefig(O/(name+'.png'),dpi=150);fig.savefig(O/(name+'.pdf'));plt.close(fig);figures.append((name,'Cada celda conserva un año y un mes. El gris identifica fechas excluidas de la muestra común; no se interpolan los vacíos. CHIRPS e IMERG comparten la escala de color para facilitar su comparación.' if batch[0]==0 else 'Cada celda conserva un año y un mes. El gris identifica fechas excluidas de la muestra común; no se interpolan los vacíos. Las unidades y escalas de cada variable se indican en sus barras.'))
intro='Para separar el ciclo que se repite durante el año de las diferencias entre años, agrupamos las observaciones por mes calendario. La climatología resume, por ejemplo, todos los eneros comparables, mientras que los mapas año–mes conservan los valores individuales. Así podremos reconocer la época húmeda y seca, observar cuánto cambia de un año a otro y comparar la respuesta del caudal con las dos estimaciones de precipitación.'
method='Utilizamos las mismas 285 fechas mensuales completas de enero de 1998 a diciembre de 2022 para CHIRPS, IMERG, caudal Q, escorrentía R y temperatura media de ERA5-Land. CHIRPS representa aquí la precipitación de referencia P_L sobre la cuenca; no es una medición puntual de pluviómetro. P_I corresponde a IMERG de cuenca. La temperatura procede del promedio espacial de la caja de cuenca usado en el apartado 3.1. Los registros locales de Zaragoza no permiten construir un ciclo de doce meses con varios años y quedan fuera de esta comparación.'
stats='Para cada mes reportamos el número de años válidos, media, mediana, desviación estándar muestral, cuartiles Q25 y Q75 y percentiles P10 y P90. Los cuantiles usan interpolación lineal (tipo 7). Cada observación mensual aporta una vez; no se rellenan faltantes ni se ponderan los años por días del mes. La muestra contiene entre 22 y 25 años por mes, por lo que las bandas describen variabilidad interanual y no incertidumbre de la media.'
closing='Las tablas y las figuras describen una muestra común, no necesariamente el registro completo de cada fuente. La selección facilita la comparación entre productos y variables, pero excluye de todas ellas los meses sin caudal completo. La diferencia entre media y mediana y la amplitud de las bandas permiten identificar meses sensibles a valores altos; los mapas año–mes muestran si esos valores corresponden a episodios particulares.'
style=ParagraphStyle('body',fontName='Hydro',fontSize=10.5,leading=13.5,spaceAfter=9)
heading=ParagraphStyle('heading',fontName='HydroBold',fontSize=11.5,leading=15,spaceBefore=12,spaceAfter=9)
subtitle=ParagraphStyle('subtitle',fontName='HydroBold',fontSize=13,leading=17,spaceAfter=12)
cell=ParagraphStyle('cell',fontName='Hydro',fontSize=8.5,leading=11);head=ParagraphStyle('head',parent=cell,fontName='HydroBold',textColor=colors.white)
def p(s,st=style):return Paragraph(html.escape(s),st)
def table(k):
    v,label,unit=variables[k];z=c[c.variable==v];rows=[['Mes','n','Media','Mediana','Desv. est.','Q25','Q75','P10','P90']]
    for row in z.itertuples(index=False):rows.append([months[row.mes-1],str(row.n_anios),*[f'{getattr(row,key):.2f}'.replace('.',',') for key in ['media','mediana','desviacion_estandar','Q25','Q75','P10','P90']]])
    content=[[p(value,head if ri==0 else ParagraphStyle('num',parent=cell,alignment=0 if ci==0 else 2)) for ci,value in enumerate(row)] for ri,row in enumerate(rows)]
    tb=Table(content,colWidths=[39,24,*([60]*7)],repeatRows=1);tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17485e')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f5f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd6dc'))]))
    return [p(label+' ('+unit+')',heading),tb,Spacer(1,10)]
story=[p('1.5. Climatología, variabilidad y explicación física',subtitle),p(intro),p('1.5.a. Construir la climatología de doce meses',heading),p(method),p(stats),*table(0),PageBreak(),*table(1),*table(2),PageBreak(),*table(3),*table(4),p(closing)]
for name,caption in figures:
    story.append(PageBreak());story.append(p('Ciclos mensuales y dispersión entre años' if name.startswith('ciclos') else 'Variabilidad año–mes',heading))
    image=Image(str(O/(name+'.png')));ratio=min(483/image.imageWidth,620/image.imageHeight);image.drawWidth=image.imageWidth*ratio;image.drawHeight=image.imageHeight*ratio
    story.extend([image,Spacer(1,10),p(caption)])
story.extend([PageBreak(),p('1.5.b. Describir y contrastar el ciclo anual',heading),p('Pendiente de desarrollar.'),p('1.5.c. Explicar los procesos regionales y de la cuenca',heading),p('Pendiente de desarrollar.')])
SimpleDocTemplate(str(O/'apartado_1_5_a.pdf'),pagesize=A4,leftMargin=56,rightMargin=56,topMargin=50,bottomMargin=47).build(story)
# Guarda el contenido en LaTeX sin reconstruir otros apartados.
texpath=D/'latex/informe_ordenado.tex';tex=texpath.read_text(encoding='utf-8');a0=tex.index(r'\subsection{Climatología, variabilidad y explicación física}');b0=tex.index(r'\section{Relaciones entre series',a0)
if not (O/'informe_antes_1_5.tex').exists():shutil.copy2(texpath,O/'informe_antes_1_5.tex')
def escape(s):return s.replace('%',r'\%').replace('_',r'\_').replace('–','--').replace('³',r'$^3$')
new=r'\subsection{Climatología, variabilidad y explicación física}'+'\n'+escape(intro)+'\n'+r'\subsubsection*{1.5.a. Construir la climatología de doce meses}'+'\n'+escape(method)+'\n\n'+escape(stats)+'\n'
for v,label,unit in variables:
    new+='\n'+r'\subsubsection*{'+escape(label+' ('+unit+')')+'}\n'+r'\begin{center}\small\begin{tabular}{lrrrrrrrr}\hline'+'\nMes & n & Media & Mediana & Desv. est. & Q25 & Q75 & P10 & P90 '+r'\\\hline'+'\n'
    for row in c[c.variable==v].itertuples(index=False):new+=' & '.join([months[row.mes-1],str(row.n_anios),*[f'{getattr(row,k):.2f}'.replace('.',',') for k in ['media','mediana','desviacion_estandar','Q25','Q75','P10','P90']]])+r'\\'+'\n'
    new+=r'\hline\end{tabular}\end{center}'+'\n'
new+='\n'+escape(closing)+'\n'
for name,caption in figures:new+=r'\begin{figure}[p]\centering\includegraphics[width=0.94\textwidth,height=0.78\textheight,keepaspectratio]{../apartado_1_5/'+name+r'.pdf}\caption{'+escape(caption)+r'}\end{figure}'+'\n'
new+=r'\clearpage\subsubsection*{1.5.b. Describir y contrastar el ciclo anual}'+'\nPendiente de desarrollar.\n'+r'\subsubsection*{1.5.c. Explicar los procesos regionales y de la cuenca}'+'\nPendiente de desarrollar.\n'+r'\clearpage'+'\n'
texpath.write_text(tex[:a0]+new+tex[b0:],encoding='utf-8')
# Sustituye únicamente las páginas del antiguo 1.5 e incorpora la nueva paginación.
backup=O/'informe_antes_1_5.pdf'
if not backup.exists():shutil.copy2(R/'Informe_Hidrologia_fuente_original.pdf',backup)
base=fitz.open(backup);section=fitz.open(O/'apartado_1_5_a.pdf');toc=base.get_toc();start=next(pn-1 for level,title,pn in toc if level==2 and title.startswith('Climatología'));end=next(pn-1 for level,title,pn in toc if level==1 and title.startswith('Relaciones'))
out=fitz.open();out.insert_pdf(base,to_page=start-1);out.insert_pdf(section);out.insert_pdf(base,from_page=end);delta=len(section)-(end-start)
newtoc=[[l,title,pn if pn<=start else pn+delta if pn>end else start+1] for l,title,pn in toc];out.set_toc(newtoc)
for pn in range(start,len(out)):
    page=out[pn];h=page.rect.height;page.add_redact_annot(fitz.Rect(0,h-42,page.rect.width,h),fill=(1,1,1));page.apply_redactions(images=0,graphics=0);page.insert_font(fontname='Hydro',fontfile=str(F/'lmroman10-regular.ttf'));page.insert_textbox(fitz.Rect(0,h-35,page.rect.width,h-15),str(pn),fontname='Hydro',fontsize=9,align=1)
idx=out[1];idx.add_redact_annot(fitz.Rect(35,35,idx.rect.width-35,idx.rect.height-43),fill=(1,1,1));idx.apply_redactions(images=0,graphics=0)
for link in idx.get_links():idx.delete_link(link)
idx.insert_font(fontname='Hydro',fontfile=str(F/'lmroman10-regular.ttf'));idx.insert_font(fontname='HydroBold',fontfile=str(F/'lmroman10-bold.ttf'));idx.insert_text((56,66),'Índice',fontname='HydroBold',fontsize=16);yy=98;sec=0;sub=0
for level,title,pn in newtoc:
    if level>2:continue
    if level==1:sec+=1;sub=0;yy+=7;label=f'{sec}. '
    else:sub+=1;label=f'{sec}.{sub}. '
    xx=56 if level==1 else 68;idx.insert_text((xx,yy),label+title,fontname='HydroBold' if level==1 else 'Hydro',fontsize=9 if level==1 else 8);idx.insert_text((534,yy),str(pn-1),fontname='Hydro',fontsize=8);idx.insert_link({'kind':fitz.LINK_GOTO,'from':fitz.Rect(xx,yy-11,553,yy+4),'page':pn-1});yy+=19
out.set_metadata(base.metadata);final=O/'informe_actualizado_1_5.pdf';out.save(final,garbage=3,deflate=True);out.close()
check=fitz.open(final)
for pn in [0,*range(2,start)]:assert check[pn].get_pixmap().samples==base[pn].get_pixmap().samples
for pn in range(start,start+len(section)):check[pn].get_pixmap().save(O/f'qa_pdf_{pn+1}.png')
(O/'verificacion_integracion.json').write_text(json.dumps({'pages':len(check),'new_section_pages':len(section),'section_start_pdf':start+1,'section_end_pdf':start+len(section),'prior_content_unchanged':True,'point_2_start_pdf':end+delta+1},indent=2),encoding='utf-8');check.close();base.close();section.close()
for dest in [R/'Informe_Hidrologia_actualizado_1_5.pdf',R/'Informe_Hidrologia_actualizado.pdf',D/'informe_actualizado_1_5.pdf',D/'latex/informe_ordenado.pdf']:
    try:shutil.copy2(final,dest)
    except PermissionError:print('Copia abierta; usar Informe_Hidrologia_actualizado_1_5.pdf')
# HTML: integración posterior al organizador y al formato global.
path=D/'informe_interactivo.html'
if not (O/'informe_antes_1_5.html').exists():shutil.copy2(path,O/'informe_antes_1_5.html')
s=(O/'informe_antes_1_5.html').read_text(encoding='utf-8')
content='<p>'+html.escape(method)+'</p><p>'+html.escape(stats)+'</p>'
for v,label,unit in variables:
    z=c[c.variable==v].copy();z['Mes']=[months[m-1] for m in z.mes];z=z[['Mes','n_anios','media','mediana','desviacion_estandar','Q25','Q75','P10','P90']];z.columns=['Mes','n','Media','Mediana','Desv. est.','Q25','Q75','P10','P90'];tab=z.to_html(index=False,border=0,classes='tabla-hidro-unificada',float_format=lambda value:f'{value:.2f}'.replace('.',','))
    content+='<h4>'+html.escape(label+' ('+unit+')')+'</h4><div class="tabla-contenedor">'+tab+'</div>'
content+='<p>'+html.escape(closing)+'</p>'
for name,caption in figures:
    content+='<figure><img style="display:block;max-width:100%;max-height:850px;object-fit:contain;margin:auto" src="data:image/png;base64,'+base64.b64encode((O/(name+'.png')).read_bytes()).decode()+'" alt="'+html.escape(name)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'
script='''(function integrarClimatologia(){if(!window.verificacionFormato){setTimeout(integrarClimatologia,100);return;}const s=document.getElementById('guia-1-5');const a=document.getElementById('guia-1-5-a');for(const node of Array.from(s.children)){if(node===a)break;if(node.tagName==='P'||node.tagName==='DIV'&&!node.id)node.remove();}const p=document.createElement('p');p.textContent=INTRO;s.querySelector('h3').after(p);const h=a.querySelector('h4,h3');a.innerHTML='';if(h)a.appendChild(h);a.insertAdjacentHTML('beforeend',CONTENT);for(const cell of a.querySelectorAll('tbody td'))if(/^[+-]?\\d+(?:[.,]\\d+)?$/.test(cell.textContent.trim()))cell.classList.add('numero');window.verificacionClimatologia15={months:12,variables:5,commonMonths:285,tables:a.querySelectorAll('table').length,figures:a.querySelectorAll('img').length};})();'''.replace('INTRO',json.dumps(intro,ensure_ascii=False)).replace('CONTENT',json.dumps(content,ensure_ascii=False))
s=s.replace('</body>','<script id="climatologia-1-5-a">'+script+'</script>\n</body>',1)
for dest in [path,R/'Informe_Hidrologia_interactivo.html']:dest.write_text(s,encoding='utf-8')
print(json.dumps({'common_months':len(x),'section_start_pdf':start+1,'new_section_pages':json.loads((O/'verificacion_integracion.json').read_text())['new_section_pages'],'climatology_rows':len(c),'tables':5,'figures':len(figures)},ensure_ascii=True))

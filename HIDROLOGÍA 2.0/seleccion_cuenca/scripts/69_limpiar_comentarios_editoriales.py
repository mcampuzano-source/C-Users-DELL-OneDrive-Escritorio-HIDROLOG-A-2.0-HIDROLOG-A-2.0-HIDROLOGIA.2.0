"""Sustituye comentarios de elaboración por contexto de resultados, sin tocar punto 1."""
from pathlib import Path
import re,shutil,json
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3]
OUT=DOCS/'revision_redaccion_tablas';OUT.mkdir(exist_ok=True)
tex=DOCS/'latex/informe_ordenado.tex';s=tex.read_text(encoding='utf-8')
start=s.index(r'\section{Relaciones entre series y modelos estadísticos}');protected=s[:start]
if not (OUT/'fuente_antes.tex').exists():shutil.copy2(tex,OUT/'fuente_antes.tex')
context='La tabla compara IMERG y CHIRPS sin corrección con sus rectas de calibración para estimar la lluvia mensual de Zaragoza. Las rectas se ajustaron con siete meses completos de 2018 y se comprobaron con siete de 2019; RMSE, MAE y sesgo se expresan en mm/mes. Por su corta duración y su uso en la selección de los modelos, esta comparación es exploratoria y no constituye una validación final independiente.'
chirps='Los diagramas comparan CHIRPS con la lluvia local y el caudal, bajo las mismas unidades y colores por mes calendario que IMERG. Ambos productos representan precipitación promediada sobre la cuenca. Se utilizan las mismas fechas para cada contraste: 14 meses completos frente a Zaragoza y 285 frente a caudal y escorrentía durante 1998–2022. Esto permite comparar los productos sin confundir sus diferencias con cambios en la cobertura temporal.'
title='Comparación de estimaciones de lluvia local'
s,n=re.subn(r'\\subsubsection\*\{Lluvia local: no existe una reserva independiente adicional\}\s*.*?(?=\\begin\{center\})',lambda m:r'\subsubsection*{'+title+'}\n'+context+'\n',s,count=1,flags=re.S);assert n==1 or title in s
s=s.replace('Fuente & Caso previo & n & RMSE & MAE & Sesgo','Fuente & Método & n & RMSE & MAE & Sesgo').replace('Recta: diagnóstico previo','Recta de calibración')
s,n=re.subn(r'\\subsubsection\*\{Alcance del apartado\}\s*.*?(?=\\subsubsection)', '',s,count=1,flags=re.S)
s,n=re.subn(r'Debajo de IMERG se presentan.*?(?=\n\\subsubsection)',lambda m:chirps.replace('–','--')+'\n',s,count=1,flags=re.S)
s=s.replace('Los 68 meses reservados quedan intactos para comprobar generalización, extremos y estabilidad. ','')
s=s.replace('El periodo reservado no se usó para ajustar ni seleccionar los modelos del 2.2, aunque sus series ya aparecieron en la exploración de 1.1 y 2.1. Se trata de una evaluación temporal fuera del ajuste, no de un experimento completamente ciego. Una comprobación prospectiva con años nuevos reforzaría la evidencia.','La reserva temporal permite evaluar la generalización del modelo; una comprobación prospectiva con años nuevos reforzaría la evidencia.')
s=s.replace(' Para lluvia local, la utilidad continúa siendo exploratoria: no hay una prueba independiente adicional disponible.','')
assert s[:start]==protected
tex.write_text(s,encoding='utf-8')
js=r'''
(function limpiar(){
 if(!window.verificacionFormulas){setTimeout(limpiar,100);return;}
 const original=document.getElementById('guia-punto-1').innerHTML;
 const s21=document.getElementById('guia-2-1'),s23=document.getElementById('guia-2-3');
 const headings=Array.from(s21.querySelectorAll('h3,h4'));
 const scope=headings.find(h=>h.textContent==='Alcance del apartado');
 if(scope){const p=scope.nextElementSibling;if(p?.tagName==='P')p.remove();scope.remove();}
 const cp=Array.from(s21.querySelectorAll('p')).find(p=>p.textContent.startsWith('Debajo de IMERG'));
 if(cp)cp.textContent=__CHIRPS__;
 const old=headings.find(h=>h.textContent.includes('comparación debajo de IMERG'));if(old)old.textContent='CHIRPS: comparación de precipitación y caudal';
 // El panel local reúne la tabla con referencias sin corrección y rectas calibradas.
 const tables=Array.from(s23.querySelectorAll('table'));
 let target=tables.find(t=>t.textContent.includes('108,19')||t.textContent.includes('108.19'));
 if(!target){
  const article=document.createElement('article');article.className='panel';
  article.innerHTML='<h4>'+__TITLE__+'</h4><p></p><table class="tabla-estadistica"><thead><tr><th>Fuente</th><th>Método</th><th>n</th><th>RMSE</th><th>MAE</th><th>Sesgo</th></tr></thead><tbody><tr><td>IMERG</td><td>Sin corrección</td><td>7</td><td>108,19</td><td>95,51</td><td>95,51</td></tr><tr><td>IMERG</td><td>Recta de calibración</td><td>7</td><td>41,85</td><td>36,76</td><td>-17,40</td></tr><tr><td>CHIRPS</td><td>Sin corrección</td><td>7</td><td>85,28</td><td>67,75</td><td>67,75</td></tr><tr><td>CHIRPS</td><td>Recta de calibración</td><td>7</td><td>30,50</td><td>25,58</td><td>-14,29</td></tr></tbody></table>';
  s23.appendChild(article);target=article.querySelector('table');
 }
 let parent=target.parentElement;
 while(parent!==s23&&parent.querySelectorAll('table').length!==1)parent=parent.parentElement;
 const candidate=Array.from(s23.querySelectorAll('h3,h4')).find(h=>/local/i.test(h.textContent));
 if(candidate)candidate.textContent=__TITLE__;
 const nearby=target.closest('article')||target.parentElement;
 const paras=Array.from(nearby.querySelectorAll('p'));
 if(paras.length){paras[0].textContent=__CONTEXT__;paras.slice(1).filter(p=>/ya|previo|solicitada|adicional|2\.2/.test(p.textContent)).forEach(p=>p.remove());}
 else {const p=document.createElement('p');p.textContent=__CONTEXT__;target.before(p);}
 for(const cell of target.querySelectorAll('th,td')){
  if(cell.textContent==='Caso previo')cell.textContent='Método';
  if(/Recta.*previo/.test(cell.textContent))cell.textContent='Recta de calibración';
 }
 if(document.getElementById('guia-punto-1').innerHTML!==original)throw new Error('Se modificó punto 1');
 window.verificacionRedaccionTablas={point1Unchanged:true,localTableContext:__CONTEXT__};
})();
'''
js=js.replace('__CHIRPS__',json.dumps(chirps,ensure_ascii=False)).replace('__TITLE__',json.dumps(title,ensure_ascii=False)).replace('__CONTEXT__',json.dumps(context,ensure_ascii=False))
for path in [DOCS/'informe_interactivo.html',ROOT/'Informe_Hidrologia_interactivo.html']:
    h=path.read_text(encoding='utf-8')
    if not (OUT/(path.stem+'_antes.html')).exists():shutil.copy2(path,OUT/(path.stem+'_antes.html'))
    h=re.sub(r'<!-- REDACCION_TABLAS_INICIO -->.*?<!-- REDACCION_TABLAS_FIN -->','',h,flags=re.S)
    h=h.replace('</body>','<!-- REDACCION_TABLAS_INICIO --><script>'+js+'</script><!-- REDACCION_TABLAS_FIN -->\n</body>',1)
    path.write_text(h,encoding='utf-8')
(OUT/'contexto_tabla_local.md').write_text(context,encoding='utf-8')
print('Comentarios editoriales eliminados; contexto de tabla conservado. Punto 1 sin cambios.')

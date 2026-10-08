"""Muestra las mismas ecuaciones vectoriales en HTML, limitadas a puntos 2-5."""
from pathlib import Path
import json,base64,re,shutil
import pymupdf as fitz
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_formulas'
catalog=json.loads((OUT/'catalogo.json').read_text(encoding='utf-8'))
blocks=fitz.open(OUT/'bloques.pdf');offset=len(json.loads((OUT/'reemplazos.json').read_text(encoding='utf-8')))
assets={}
for i,c in enumerate(catalog):
    page=blocks[offset+i];tag=page.search_for('('+c['number']+')')[0]
    words=[w for w in page.get_text('words') if w[0]<tag.x0-2]
    clip=fitz.Rect(min(w[0] for w in words)-4,min(w[1] for w in words)-4,max(w[2] for w in words)+4,max(w[3] for w in words)+4)
    one=fitz.open();p=one.new_page(width=clip.width,height=clip.height);p.show_pdf_page(p.rect,blocks,offset+i,clip=clip)
    svg=p.get_svg_image(text_as_path=True);one.close()
    assets[c['number']]={'math':c['math'],'width':round(clip.width*4/3,2),'url':'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()}
blocks.close()
js=r'''
(function(){
function aplicar(){
 if(!document.getElementById('guia-5-4')){setTimeout(aplicar,100);return;}
 const protectedHTML=document.getElementById('guia-punto-1').innerHTML;
 const assets=__ASSETS__;
 const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
 const eq=n=>'<div class="ecuacion-hidrologia" data-ecuacion="'+n+'" style="overflow-x:auto;padding:14px 0"><div style="position:relative;width:100%;min-width:'+(assets[n].width+90)+'px"><img style="display:block;margin:0 auto;width:'+assets[n].width+'px;max-width:none;height:auto" alt="Ecuación ('+n+'): '+esc(assets[n].math)+'" src="'+assets[n].url+'"><span style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-family:serif">('+n+')</span></div></div>';
 const updated=[];
 function paragraph(p,content){
   const links=Array.from(p.querySelectorAll('a')).map(a=>[esc(a.textContent),a.outerHTML]);
   for(const [label,link] of links)content=content.replace(label,link);
   const box=document.createElement('div');box.className='parrafo-con-ecuaciones';box.innerHTML=content;p.replaceWith(box);
 }
 function replace(scope,needle,search,value){
   const p=Array.from(document.querySelectorAll(scope+' p')).find(e=>e.textContent.includes(needle));
   if(!p)throw new Error('No se encontró el párrafo: '+needle);
   const text=p.textContent;const at=text.indexOf(search);
   if(at<0)throw new Error('No se encontró la fórmula: '+search);
   paragraph(p,'<p>'+esc(text.slice(0,at))+'</p>'+value+'<p>'+esc(text.slice(at+search.length))+'</p>');updated.push(needle);
 }
 replace('#guia-2-1','error e =','Con lluvia local como referencia y error e = IMERG − local,','<p>Con lluvia local como referencia, el error mensual se define mediante</p>'+eq('2.1'));
 replace('#guia-2-1','Se define k','Se define k≥0 como correlación entre P del mes t−k y Q del mes t; k=1 significa lluvia del mes anterior.','<p>Se relaciona la lluvia antecedente con el caudal mediante</p>'+eq('2.2')+'<p>Un rezago de un mes utiliza la lluvia del mes anterior.</p>');
 replace('#guia-2-1','La comparación en láminas usa','R = 86,4 × días del mes × Q / 2797,19, en mm/mes.',eq('2.3')+'<p>El número de días del mes se representa por d y el caudal medio mensual por Q.</p>');
 replace('#guia-2-1','Se define X′','Se define X′(t)=X(t)−promedio de X para el mes calendario de t.','<p>La anomalía mensual se define como</p>'+eq('2.4'));
 replace('#guia-2-2','La nube positiva','Se comparan media constante, climatología mensual, Q=a+bP(t), Q=a+bP(t−1), Q=a+bP(t)+cP(t−1) y Q=a+b√P(t).','<p>Se comparan la media constante y la climatología mensual con cuatro relaciones que incorporan precipitación:</p>'+['2.5','2.6','2.7','2.8'].map(eq).join(''));
 const pres=Array.from(document.querySelectorAll('#guia-2-2 pre'));
 if(pres.length!==5)throw new Error('Cantidad inesperada de ecuaciones de ajuste');
 pres.forEach((p,i)=>{if(i===3)p.previousElementSibling.innerHTML='<b>Lluvia local · CHIRPS</b>';p.outerHTML=eq(['2.9','2.10','2.11','2.12','2.13'][i]);});
 replace('#guia-2-2','R_est=','R_est=86,4×días_del_mes×Q_est/2797,19,',eq('2.14'));
 const s23=document.getElementById('guia-2-3');
 s23.querySelector('h3').insertAdjacentHTML('afterend','<p>Se mantienen las ecuaciones ajustadas en el periodo de desarrollo:</p>'+eq('2.15')+eq('2.16')+'<p>La eficiencia de Nash–Sutcliffe compara el error del modelo con el de la media del periodo evaluado:</p>'+eq('2.17'));
 replace('#guia-3-1','La unidad es K','T[°C] = T[K] - 273,15.',eq('3.1'));
 const cards=Array.from(document.querySelectorAll('#guia-3-1 article'));
 cards.find(e=>e.querySelector('h4')?.textContent.includes('Descarga y promedio temporal')).insertAdjacentHTML('beforeend','<p>Si se parte de datos diarios completos, la media mensual se calcula utilizando todos los días del mes:</p>'+eq('3.2'));
 cards.find(e=>e.querySelector('h4')?.textContent.includes('Promedio espacial')).insertAdjacentHTML('beforeend','<p>El promedio de cuenca y sus pesos por área se expresan como</p>'+eq('3.3'));
 for(const [id,n,text] of [['guia-3-2','3.4','Las anomalías y su estandarización se definen respecto al mes calendario de referencia:'],['guia-3-3','3.5','El modelo de tendencia con control del ciclo anual tiene la siguiente expresión:'],['guia-3-4','3.6','La regresión lineal simple utilizada como contraste se escribe como']]){
   const section=document.getElementById(id);section.querySelector('h3').insertAdjacentHTML('afterend','<p>'+text+'</p>'+eq(n));
 }
 const method=Array.from(document.querySelectorAll('#guia-4-1 p')).find(p=>p.textContent.includes('Muestreo regular'));
 paragraph(method,'<p>El muestreo es mensual y regular. En cada tramo continuo se calcula la transformada discreta:</p>'+eq('4.1')+'<p>Las frecuencias, los periodos equivalentes y el espaciamiento espectral son</p>'+eq('4.2')+'<p>Con ventana rectangular y sin taper, la potencia de base se normaliza como</p>'+eq('4.3')+'<p>Se duplican las frecuencias positivas salvo Nyquist; la suma reproduce la varianza de la serie centrada. Las unidades son el cuadrado de la variable. La frecuencia cero representa la media y se excluye de los periodos.</p>');
 const walker=document.createTreeWalker(document.getElementById('guia-4-2'),NodeFilter.SHOW_TEXT);let node,found=null;
 while(node=walker.nextNode())if(node.textContent.includes('densidad S(f)=')){found=node;break;}
 const box=document.createElement('div');box.innerHTML='<p>La densidad espectral de base del periodograma unilateral es</p>'+eq('4.4')+'<p>Se duplican las frecuencias positivas salvo Nyquist. La potencia por bin y su porcentaje normalizado se calculan mediante</p>'+eq('4.5')+'<p>La densidad tiene unidades de variable al cuadrado por mes y la potencia por bin conserva unidades de variable al cuadrado.</p>';
 if(found)found.replaceWith(box);else document.querySelector('#guia-4-2 > h3').after(box);
 replace('#guia-5-1','Las medias mensuales','Z=Φ/9,80665 m.',eq('5.1')+'<p>La altura resultante se expresa en metros.</p>');
 replace('#guia-5-2','La referencia comprende','r_j(lon,lat;ell) = corr[a_X(t),a_Y(lon,lat,t-ell)] para mes(t)=j,',eq('5.2'));
 replace('#guia-5-3','La dependencia relevante','n_eff = n(1-rhoX*rhoY)/(1+rhoX*rhoY), limitada a [3,n],',eq('5.3')+'<p>El tamaño efectivo se limita al intervalo indicado.</p>');
 replace('#guia-5-3','La prueba bilateral usa','t=|r| sqrt(df/(1-r²)), con df=n_eff-2 para anomalías y df=n_eff-3 al controlar el año.',eq('5.4')+'<p>Los grados de libertad se definen como</p>'+eq('5.5'));
 if(document.getElementById('guia-punto-1').innerHTML!==protectedHTML)throw new Error('Se modificó el punto 1');
 window.verificacionFormulas={equations:document.querySelectorAll('.ecuacion-hidrologia').length,point1Unchanged:true,updated};
}
if(document.readyState==='complete')aplicar();else window.addEventListener('load',aplicar);
})();
'''
s=(OUT/'base_antes.html').read_text(encoding='utf-8')
snippet='<!-- FORMULAS_2_5_INICIO --><script>'+js.replace('__ASSETS__',json.dumps(assets,ensure_ascii=False))+'</script><!-- FORMULAS_2_5_FIN -->'
s=s.replace('</body>',snippet+'\n</body>',1)
for dest in [DOCS/'informe_interactivo.html',ROOT/'Informe_Hidrologia_interactivo.html']:dest.write_text(s,encoding='utf-8')
print('HTML actualizado con ecuaciones SVG autocontenidas y alcance limitado a puntos 2-5.')

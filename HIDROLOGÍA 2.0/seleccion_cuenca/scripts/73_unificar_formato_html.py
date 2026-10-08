"""Fuente, jerarquía y tablas comunes en HTML; alcance estricto 2-5."""
from pathlib import Path
import base64,shutil,re,json
import matplotlib
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';ROOT=DOCS.parents[3];OUT=DOCS/'revision_tablas'
path=DOCS/'informe_interactivo.html'
if not (OUT/'base_antes.html').exists():shutil.copy2(path,OUT/'base_antes.html')
s=(OUT/'base_antes.html').read_text(encoding='utf-8')
fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
scope=':is(#guia-punto-2,#guia-punto-3,#guia-punto-4,#guia-punto-5)'
css=''
for weight,file in [('400','DejaVuSerif.ttf'),('700','DejaVuSerif-Bold.ttf')]:
    css+='@font-face{font-family:HydroDocumento;font-style:normal;font-weight:'+weight+';src:url(data:font/ttf;base64,'+base64.b64encode((fonts/file).read_bytes()).decode()+') format("truetype");}'
css+=f'''{scope}{{font-family:HydroDocumento,serif!important;font-size:16px!important;line-height:1.5;color:#18252d}}
{scope} p,{scope} li{{font-family:HydroDocumento,serif!important;font-size:16px!important;line-height:1.5!important}}
{scope} h2{{font-family:HydroDocumento,serif!important;font-size:24px!important;font-weight:700;line-height:1.25;margin:28px 0 16px}}
{scope} h3{{font-family:HydroDocumento,serif!important;font-size:20px!important;font-weight:700;line-height:1.3;margin:24px 0 12px}}
{scope} h4,{scope} h5{{font-family:HydroDocumento,serif!important;font-size:17px!important;font-weight:700;line-height:1.35;margin:20px 0 10px}}
{scope} table.tabla-hidro-unificada{{width:100%!important;max-width:none!important;border-collapse:collapse!important;border-spacing:0!important;margin:14px 0!important;border:0!important;font-family:HydroDocumento,serif!important;font-size:14px!important;background:white!important}}
{scope} .tabla-hidro-unificada th,{scope} .tabla-hidro-unificada td{{font-family:HydroDocumento,serif!important;font-size:14px!important;padding:9px 10px!important;border:0!important;border-bottom:1px solid #ccd6dc!important;vertical-align:top!important;line-height:1.4!important;text-align:left}}
{scope} .tabla-hidro-unificada thead th{{background:#17485e!important;color:white!important;font-weight:700!important}}
{scope} .tabla-hidro-unificada tbody tr:nth-child(odd) td{{background:white!important}}
{scope} .tabla-hidro-unificada tbody tr:nth-child(even) td{{background:#f2f5f7!important}}
{scope} .tabla-hidro-unificada td.numero{{text-align:right!important;font-variant-numeric:tabular-nums;white-space:nowrap}}
{scope} .tabla-contenedor{{width:100%;overflow-x:auto;margin:10px 0 20px}}
'''
js=r'''
(function aplicarFormato(){
 if(!window.verificacionRedaccionTablas){setTimeout(aplicarFormato,100);return;}
 const before=document.getElementById('guia-punto-1').innerHTML;
 const tables=Array.from(document.querySelectorAll('#guia-punto-2 table,#guia-punto-3 table,#guia-punto-4 table,#guia-punto-5 table'));
 for(const table of tables){
  table.classList.add('tabla-hidro-unificada');
  if(!table.tHead&&table.rows.length){const head=table.createTHead();head.appendChild(table.rows[0]);}
  if(table.tHead){for(const row of table.tHead.rows)for(const cell of Array.from(row.cells))if(cell.tagName!=='TH'){const th=document.createElement('th');th.innerHTML=cell.innerHTML;cell.replaceWith(th);}}
  for(const body of table.tBodies)for(const row of body.rows)for(const cell of row.cells){if(/^[<>≤≥+−-]?s*d+(?:[.,]d+)?(?:s*%|s*[eE][+−-]?d+)?$/.test(cell.textContent.trim()))cell.classList.add('numero');}
  const box=document.createElement('div');box.className='tabla-contenedor';table.before(box);box.appendChild(table);
 }
 if(document.getElementById('guia-punto-1').innerHTML!==before)throw new Error('Se modificó el punto 1');
 window.verificacionFormato={tables:tables.length,point1Unchanged:true,font:'HydroDocumento',title:24,subtitle:20,heading:17,body:16,table:14};
})();
'''
snippet='<!-- FORMATO_UNIFICADO_INICIO --><style>'+css+'</style><script>'+js+'</script><!-- FORMATO_UNIFICADO_FIN -->'
s=s.replace('</body>',snippet+'\n</body>',1)
for dest in [path,ROOT/'Informe_Hidrologia_interactivo.html']:dest.write_text(s,encoding='utf-8')
print('HTML: tipografía y tablas unificadas, fuentes incluidas, punto 1 protegido.')

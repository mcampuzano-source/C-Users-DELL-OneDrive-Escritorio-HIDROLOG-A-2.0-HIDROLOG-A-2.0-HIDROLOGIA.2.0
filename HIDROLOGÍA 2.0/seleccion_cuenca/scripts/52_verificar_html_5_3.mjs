import fs from 'node:fs/promises';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const docs=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../la_vieja/documentos');
const h=await fs.readFile(path.join(docs,'informe_interactivo.html'),'utf8');
const scripts=[...h.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)];
for(const m of scripts)new vm.Script(m[1]);
const s=h.match(/<script id="script53">([\s\S]*?)<\/script>/)[1];
const table=JSON.parse(await fs.readFile(path.join(docs,'apartado_5_3/resumen_mensual.table.json'),'utf8'));
const col=Object.fromEntries(table.columns.map((v,i)=>[v,i]));
const elements={};let traces,exported;
function element(id){return elements[id]??=( {value:id==='capa53'?'r_detrended':id==='mes53'?'0':'',style:{},selectedOptions:[{text:'Prueba'}],options:[],events:{},addEventListener(event,cb){this.events[event]=cb;},appendChild(o){this.options.push(o);if(!this.value)this.value=o.value;},click(){}} );}
const context={document:{readyState:'complete',getElementById:element,createElement:()=>({click(){}})},window:{Plotly:true},Plotly:{react(id,t){traces=t;}},atob:v=>Buffer.from(v,'base64').toString('binary'),ArrayBuffer,Uint8Array,DataView,Blob,URL:{createObjectURL(b){exported=b;return 'test';},revokeObjectURL(){}},setTimeout(){}};
vm.runInNewContext(s,context,{timeout:120000});
if(traces.filter(t=>t.type==='heatmap').length!==12)throw Error('No se mostraron doce mapas');
element('mes53').value='2';
for(const option of element('combo53').options){
 element('combo53').value=option.value;element('combo53').events.change();
 const expected=table.data.find(r=>r[col.key]===option.value&&r[col.month]===2)[col.by_cells];
 const observed=traces.filter(t=>t.type==='scatter'&&t.mode==='markers')[0].x.length;
 if(expected!==observed)throw Error('Máscara BY no coincide con precisión completa: '+option.value);
 const map=traces.find(t=>t.type==='heatmap');if(map.zmin!==-1||map.zmax!==1)throw Error('Escala divergente incorrecta');
}
element('combo53').value='Q_sst_l0';element('capa53').value='r_1998_2009';element('capa53').events.change();
if(traces.find(t=>t.type==='heatmap').customdata.flat().some(a=>a[0]>12))throw Error('n del subperiodo incorrecto');
element('capa53').value='r_detrended';element('capa53').events.change();element('csv53').events.click();
const csv=await exported.text();if(!csv.includes('\n')||csv.includes('\\n'))throw Error('CSV no contiene saltos de línea reales');
const result={all_script_syntax:'passed',twelve_months:'passed',exact_BY_masks_all_combinations:'passed',common_diverging_scale:'passed',subperiod_n:'passed',csv_export:'passed',browser_visual_test:'not performed'};
await fs.writeFile(path.join(docs,'apartado_5_3/verificacion_html.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));

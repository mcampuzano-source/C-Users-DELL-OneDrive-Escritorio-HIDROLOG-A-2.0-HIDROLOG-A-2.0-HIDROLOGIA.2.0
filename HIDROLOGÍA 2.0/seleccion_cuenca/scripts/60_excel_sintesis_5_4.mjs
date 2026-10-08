import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../la_vieja/documentos/apartado_5_4');
const wb=Workbook.create();
const specs=[['Índice NOAA','contraste_NOAA_Nino34'],['Regiones','regiones_coherentes'],['Campos dependientes','dependencias_campos'],['Evidencia y límites','tabla_evidencia_mecanismos'],['Fourier','sintesis_fourier'],['Climatología','climatologia_comun']];
const letters=n=>{let s='';for(let a=n;a>0;a=Math.floor((a-1)/26))s=String.fromCharCode(65+(a-1)%26)+s;return s;};
for(const [name,file] of specs){
 const d=JSON.parse(await fs.readFile(path.join(root,file+'.table.json'),'utf8'));
 const sh=wb.worksheets.add(name);sh.showGridLines=false;
 sh.getRange('A1').values=[[name+' - interpretación 5.4']];
 sh.getRange('A2').values=[['Exportación de '+file+'.csv. Cálculos y definiciones: scripts 56-58.']];
 sh.getRange('A3').values=[['NOAA: ERSST v6 mensual, no ONI; mapas: v5. Inferencia AR(1)/BY aproximada; no causal.']];
 sh.getRangeByIndexes(4,0,1,d.columns.length).values=[d.columns];
 sh.getRangeByIndexes(5,0,d.data.length,d.columns.length).values=d.data;
 const range=sh.getRangeByIndexes(4,0,d.data.length+1,d.columns.length);
 range.format.font.name='Arial';range.format.font.size=10;range.format.columnWidth=20;range.format.rowHeight=22;range.format.verticalAlignment='center';
 sh.getRangeByIndexes(4,0,1,d.columns.length).format={fill:'#224f65',font:{name:'Arial',bold:true,color:'#FFFFFF',size:10},wrapText:true,rowHeight:48};
 sh.getRange('A1').format.font={name:'Arial',bold:true,size:14,color:'#224f65'};
 for(let j=0;j<d.columns.length;j++)if(d.data.every(r=>r[j]===null||typeof r[j]==='number'))sh.getRangeByIndexes(5,j,d.data.length,1).setNumberFormat(/cells|^n$|^month$|^lag$|^mes_calendario$|cycles/.test(d.columns[j])?'0':'0.000');
 sh.getRangeByIndexes(4,0,d.data.length+1,1).format.columnWidth=24;
 if(name==='Evidencia y límites'){
  sh.getRangeByIndexes(5,0,d.data.length,d.columns.length).format.wrapText=true;
  sh.getRangeByIndexes(5,0,d.data.length,d.columns.length).format.rowHeight=96;
  sh.getRangeByIndexes(4,1,d.data.length+1,d.columns.length-1).format.columnWidth=38;
 }
 sh.freezePanes.freezeRows(5);sh.freezePanes.freezeColumns(1);
 sh.tables.add('A5:'+letters(d.columns.length)+(d.data.length+5),true,'Sintesis'+file.replaceAll('_',''));
}
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:"'Índice NOAA'!A5:H9",include:'values',maxChars:1400})).ndjson);
for(const [name,file] of specs){const preview=await wb.render({sheetName:name,range:name==='Evidencia y límites'?'A1:D7':'A1:F10',scale:1,format:'png'});await fs.writeFile(path.join(root,file+'_excel.png'),new Uint8Array(await preview.arrayBuffer()));}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(root,'Sintesis_fisica_5_4.xlsx'));
console.log('Excel de síntesis exportado.');

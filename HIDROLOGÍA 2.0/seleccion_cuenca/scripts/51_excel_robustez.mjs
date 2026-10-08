import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../la_vieja/documentos/apartado_5_3');
const wb=Workbook.create();
const specs=[['Resumen mensual','resumen_mensual'],['Regiones SST','regiones_sst'],['CHIRPS IMERG','sensibilidad_fuentes']];
for(const [name,file] of specs){
 const d=JSON.parse(await fs.readFile(path.join(root,file+'.table.json'),'utf8'));
 const sh=wb.worksheets.add(name);sh.showGridLines=false;
 sh.getRange('A1').values=[[name+' - robustez 5.3, 1998-2022']];
 sh.getRange('A2').values=[['Diagnósticos calculados en Python; los CSV y NetCDF conservan precisión completa.']];
 sh.getRange('A3').values=[['Fuente: '+file+'.csv; scripts 48 y 49. BY global 0,05; p aproximados AR(1) anual.']];
 sh.getRangeByIndexes(4,0,1,d.columns.length).values=[d.columns];
 sh.getRangeByIndexes(5,0,d.data.length,d.columns.length).values=d.data;
 const range=sh.getRangeByIndexes(4,0,d.data.length+1,d.columns.length);
 range.format.font.name='Arial';range.format.font.size=10;
 range.format.columnWidth=19;range.format.rowHeight=21;range.format.verticalAlignment='center';
 sh.getRangeByIndexes(4,0,1,d.columns.length).format={fill:'#224f65',font:{name:'Arial',bold:true,color:'#FFFFFF',size:10},wrapText:true,rowHeight:56};
 sh.getRange('A1').format.font={name:'Arial',bold:true,size:14,color:'#224f65'};
 for(let j=0;j<d.columns.length;j++){
  if(d.data.every(r=>r[j]===null||typeof r[j]==='number'))sh.getRangeByIndexes(5,j,d.data.length,1).setNumberFormat(/cells|^n_|^month$|^lag$/.test(d.columns[j])?'0':'0.000');
 }
 sh.getRange('A5:A'+(d.data.length+5)).format.columnWidth=23;
 sh.freezePanes.freezeRows(5);sh.freezePanes.freezeColumns(name==='Resumen mensual'?5:2);
 const letters=n=>{let s='';for(let a=n;a>0;a=Math.floor((a-1)/26))s=String.fromCharCode(65+(a-1)%26)+s;return s;};
 sh.tables.add('A5:'+letters(d.columns.length)+(d.data.length+5),true,'Robustez'+file.replaceAll('_',''));
}
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:"'Resumen mensual'!A5:F9",include:'values',maxChars:1500})).ndjson);
for(const [name,file] of specs){
 const preview=await wb.render({sheetName:name,range:'A1:F10',scale:1.5,format:'png'});
 await fs.writeFile(path.join(root,file+'_excel.png'),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(root,'Robustez_5_3.xlsx'));
console.log('Excel exportado con tres tablas de diagnóstico.');

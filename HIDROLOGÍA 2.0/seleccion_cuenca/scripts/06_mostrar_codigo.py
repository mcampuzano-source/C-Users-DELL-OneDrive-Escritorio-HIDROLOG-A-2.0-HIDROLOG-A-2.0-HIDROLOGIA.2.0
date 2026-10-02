"""Crea una vista local de todo el codigo, desde la descarga inicial."""
from pathlib import Path
from html import escape
import json
import pandas as pd

root=Path(__file__).resolve().parents[1]
files=[('01','Descarga inicial de CAMELS','descargar_camels.py'),
       ('02','Revision diaria y seleccion inicial','revisar_series.py'),
       ('03','Disponibilidad mensual','graficar_disponibilidad.py'),
       ('04','Primer archivo Excel','crear_excel.py'),
       ('05','Filtro de temperatura y cobertura IMERG','05_filtrar_temperatura_imerg.py'),
       ('06','Vista del codigo desde el inicio','06_mostrar_codigo.py'),
       ('07','Conteo espacial de estaciones IDEAM y prioridad','07_contar_estaciones_ideam.py'),
       ('08','Exploracion mensual de La Vieja','08_exploracion_mensual_la_vieja.py'),
       ('09','Informe visual de exploracion','09_informe_exploracion.py'),
       ('10','Documentos Matplotlib-LaTeX y Plotly autocontenido','10_documentos_series_mensuales.py'),
       ('11','Verificacion del HTML sin conexion','11_verificar_documento_interactivo.py'),
       ('12','Compilacion del documento LaTeX','12_compilar_latex.py'),
       ('13','Control de faltantes en ambos documentos','13_control_faltantes_documentos.py'),
       ('14','Estadistica descriptiva global y por año','14_estadisticas_por_ano.py'),
       ('15','Cobertura mensual: porcentaje válido vs años','15_grafica_cobertura_mensual.py'),
       ('16','Procedencia y alcance de los documentos','16_procedencia_alcance.py'),
       ('17','Descarga y recorte topográfico Copernicus','17_topografia_la_vieja.py'),
       ('18','Temperatura, dispersiones y mapas','18_temperatura_dispersion_mapas.py'),
       ('19','Histogramas y estadísticos completos','19_histogramas_estadisticas.py'),
       ('20','Consulta pública de precipitación in situ','20_verificar_precipitacion_insitu.py')]
summary=pd.read_csv(root/'resultados/filtro_8_temperatura_imerg.csv')
sections=[]
for number,title,file in files:
    code=(root/'scripts'/file).read_text(encoding='utf-8')
    sections.append(f'<section id="paso{number}"><h2>{number}. {escape(title)}</h2><p>{escape(file)}</p><pre><code>{escape(code)}</code></pre></section>')
html='''<!doctype html><html lang="es"><meta charset="utf-8"><title>CAMELS — código desde el inicio</title>
<style>body{font:16px system-ui;max-width:1250px;margin:32px auto;padding:0 24px;color:#163342;background:#f5f8fa}nav{display:flex;gap:18px;flex-wrap:wrap}a{color:#006c88}pre{background:#122632;color:#edf5fa;padding:24px;overflow:auto;font:14px/1.6 Consolas,monospace;border-radius:8px}section{margin:40px 0}table{border-collapse:collapse;background:white;font-size:13px;display:block;overflow:auto}th,td{padding:10px;border:1px solid #d5e0e6;text-align:left}.nota{padding:18px;background:#fff2d8;border-left:4px solid #cb8a12}</style>
<h1>Selección de cuenca: código desde el inicio</h1>
<p>Scripts reales utilizados en esta revisión. El orden conserva la descarga, auditoría y generación de resultados. Los catálogos IDEAM y NASA guardados en datos/ son entradas adicionales documentadas en README.md.</p>
<nav>'''+''.join(f'<a href="#paso{n}">{n}. {escape(t)}</a>' for n,t,_ in files)+'''</nav>
<h2>Resultado del filtro</h2><p>Las ocho candidatas pasan la preselección por área, temperatura Tmin/Tmax y cobertura mensual catalogada de IMERG para 1998–2022.</p>
<p class="nota">IMERG es precipitación, no temperatura del aire. Tmin/Tmax provienen de MSWX mediante CAMELS. Hay 300 meses catalogados por cuenca; todavía no se han extraído valores IMERG. La prueba de descarga directa respondió HTTP 401: requiere autenticación de Earthdata. Los pesos espaciales son preliminares, pendientes de comprobar con la malla del archivo descargado.</p>'''+summary.to_html(index=False,border=0)+''.join(sections)+'</html>'
(root/'Codigo_desde_el_inicio.html').write_text(html,encoding='utf-8')
print(root/'Codigo_desde_el_inicio.html')

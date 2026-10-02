"""Vista HTML local de figuras, estadisticas y codigo; sin dependencias de red."""
from pathlib import Path
from html import escape
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'la_vieja'/'punto_1'
s=json.loads((OUT/'resumen_control.json').read_text(encoding='utf-8'))
stats=pd.read_csv(OUT/'estadistica_descriptiva.csv')
figs=[('01_series_cronologicas','1. Series cronológicas','Las franjas grises son meses excluidos; no se unen los valores a través de vacíos.'),('02_disponibilidad','2. Disponibilidad','Los faltantes diarios se concentran en 19 meses; el hueco continuo más largo es de 62 días.'),('03_distribuciones','3. Distribuciones y extremos','Q tiene una cola superior marcada. Los puntos fuera de los bigotes se conservan.'),('04_ciclo_anual_exploratorio','4. Ciclo anual exploratorio','P tiene máximos locales en abril y octubre; Q en mayo y noviembre. Las bandas muestran variabilidad entre años, no incertidumbre de la media.'),('05_mapa_ano_mes','5. Variabilidad entre años','Esta figura conserva los años individuales; la climatología por sí sola los ocultaría.'),('06_revision_extremos','6. Inspección de extremos','Ventanas temporales de los mínimos y máximos de P y Q. Las franjas naranjas señalan el mes extremo.')]
sections=''.join(f'<section><h2>{title}</h2><p>{desc}</p><a href="figuras/{name}.png"><img src="figuras/{name}.png" alt="{title}"></a><p><a href="figuras/{name}.pdf">Descargar figura en PDF</a></p></section>' for name,title,desc in figs)
code=(ROOT/'scripts'/'08_exploracion_mensual_la_vieja.py').read_text(encoding='utf-8')
text=(OUT/'Interpretacion_inicial.md').read_text(encoding='utf-8')
# Vista del texto fiel al Markdown original; conservar el archivo editable y sus enlaces.
interpretation='<pre class="texto">'+escape(text)+'</pre>'
html='''<!doctype html><html lang="es"><meta charset="utf-8"><title>La Vieja — exploración mensual</title><style>
body{font:17px/1.6 system-ui;max-width:1250px;margin:32px auto;padding:0 24px;color:#19384a;background:#f7f9fa}h1,h2{line-height:1.2}img{width:100%;background:white;border:1px solid #dbe4e8}a{color:#096d87}section{margin:45px 0}.tarjetas{display:flex;gap:18px;flex-wrap:wrap}.tarjetas p{background:#e1eff1;padding:18px;border-radius:8px}.nota{background:#fff0d6;padding:20px;border-left:4px solid #c28826}table{display:block;overflow:auto;border-collapse:collapse;font-size:14px}td,th{padding:9px;border:1px solid #d2dfe4;white-space:nowrap}pre{overflow:auto;background:#142b38;color:#e8f1f4;padding:20px;font:13px/1.55 Consolas,monospace}.texto{white-space:pre-wrap;background:white;color:#19384a;font:16px/1.6 system-ui}nav{display:flex;gap:24px;flex-wrap:wrap}</style>
<h1>La Vieja–Cartago: primera exploración mensual</h1><p>Estación 26127040 · 1981–2022 · Precipitación CHIRPS y caudal observado reportado por CAMELS</p>
<nav><a href="Exploracion_mensual_La_Vieja.xlsx">Excel de resultados</a><a href="Interpretacion_inicial.md">Interpretación editable</a><a href="#codigo">Código de este paso</a><a href="../../Codigo_desde_el_inicio.html">Código desde el inicio</a></nav>
<div class="tarjetas"><p><b>485 / 504</b><br>meses completos</p><p><b>255 días</b><br>ausentes (1,66 %)</p><p><b>19 meses</b><br>excluidos, sin relleno</p></div>
<p class="nota">Exploración inicial: IMERG y temperatura media siguen pendientes. Las estaciones de lluvia del catálogo no se han usado como registros observados en estas figuras. Los extremos y secuencias constantes son alertas que se conservan hasta comprobarlas.</p>
<h2>Primeros resultados</h2><p>La lluvia media mensual es 168,20 mm y el caudal medio de los meses válidos, 98,70 m³/s. Los dos máximos del ciclo de lluvia anteceden un mes a los máximos del caudal. Es una hipótesis inicial de régimen bimodal con respuesta retardada, no una atribución causal.</p>
<p>Se verificaron de manera independiente enero de 1981 y febrero bisiesto de 1992. Se encontraron ocho secuencias de caudal constante de al menos siete días; permanecen en el análisis y requieren metadatos.</p>'''+sections+'<h2>Tabla descriptiva completa</h2>'+stats.to_html(index=False,float_format=lambda x:f'{x:.3f}',border=0)+'<h2>Interpretación, decisiones y limitaciones</h2>'+interpretation+'<details id="codigo"><summary>Ver código completo de esta exploración</summary><pre><code>'+escape(code)+'</code></pre></details></html>'
(OUT/'Informe_exploracion.html').write_text(html,encoding='utf-8')
print(OUT/'Informe_exploracion.html')

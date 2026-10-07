"""Incorpora la portada institucional sin modificar los análisis."""
from pathlib import Path
import base64
import shutil
import re

DOCS = Path(__file__).resolve().parents[1] / 'la_vieja' / 'documentos'
LOGO = DOCS / 'latex' / 'figuras' / 'escudos_unal_oficial.jpg'
if not LOGO.exists():
    shutil.copyfile(Path.home() / 'AppData/Local/Temp/escudos_unal.jpg', LOGO)
tex = DOCS / 'latex' / 'informe_ordenado.tex'
s = tex.read_text(encoding='utf-8')
cover = r'''% PORTADA_INSTITUCIONAL_INICIO
\begin{titlepage}
\centering
\vspace*{0.5cm}
\vspace{0.8cm}
{\huge\bfseries Cuenca del río La Vieja\par}
\vspace{0.4cm}
{\Large Exploración hidroclimática mensual\par}
\vspace{0.5cm}
{\large Curso: Hidrología\par}
\vspace{0.6cm}
{\large\bfseries Profesor\par}
{\large Carlos David Hoyos Ortiz\par}
\vspace{0.9cm}
{\large\bfseries Integrantes\par}
\vspace{0.4cm}
{\large Marcos Correal Suarez\par
Andrea Carolina Vergara Tenorio\par
Mariana Campuzano Tobón\par}
\vspace{0.3cm}
{\large Ingeniería Civil\par}
\vspace{0.9cm}
\includegraphics[width=3.7cm,trim=850bp 230bp 820bp 150bp,clip]{figuras/escudos_unal_oficial.jpg}\par
\vspace{0.5cm}
{\Large\bfseries Universidad Nacional de Colombia\par}
\vspace{0.2cm}
{\large Sede Medellín\par Facultad de Minas\par}
\vfill
{\large Medellín, Colombia\par 2026\par}
\vspace*{0.6cm}
\end{titlepage}
% PORTADA_INSTITUCIONAL_FIN
'''
if '% PORTADA_INSTITUCIONAL_INICIO' in s:
    s = re.sub(r'% PORTADA_INSTITUCIONAL_INICIO.*?% PORTADA_INSTITUCIONAL_FIN\n', lambda _: cover, s, flags=re.S)
else:
    start = s.index(r'\begin{center}', s.index(r'\begin{document}'))
    end = s.index(r'\end{center}', start) + len(r'\end{center}')
    s = s[:start] + cover + s[end:]
tex.write_text(s, encoding='utf-8')
html = DOCS / 'informe_interactivo.html'
s = html.read_text(encoding='utf-8')
s = s[s.index('<!doctype'):]
img = base64.b64encode(LOGO.read_bytes()).decode()
cover_html = f'''<!-- PORTADA_INSTITUCIONAL_INICIO -->
<style>.portada-institucional{{max-width:1100px;margin:28px auto;padding:46px 24px;background:white;border:1px solid #dce5e9;border-top:5px solid #94b43b;border-radius:10px;text-align:center;box-sizing:border-box}}.portada-institucional .escudo{{width:148px;height:212px;overflow:hidden;position:relative;margin:0 auto 22px}}.portada-institucional .escudo img{{position:absolute;width:897.88px;max-width:none;height:auto;left:-381.42px;top:-67.32px}}.portada-institucional h1{{margin:34px 0 14px;font-size:clamp(28px,4vw,42px)}}.portada-institucional .autores{{margin:32px 0;line-height:1.9}}.portada-institucional .institucion{{font-size:23px;font-weight:700}}@media print{{.portada-institucional{{break-after:page;box-shadow:none;border:0}}}}</style>
<header class="portada-institucional" aria-label="Portada del informe">

<h1>Cuenca del río La Vieja</h1>
<p>Exploración hidroclimática mensual<br>Curso: Hidrología</p>
<p><strong>Profesor</strong><br>Carlos David Hoyos Ortiz</p>
<div class="autores"><strong>Integrantes</strong><br>Marcos Correal Suarez<br>Andrea Carolina Vergara Tenorio<br>Mariana Campuzano Tobón<br><em>Ingeniería Civil</em></div>
<div class="escudo"><img src="data:image/jpeg;base64,{img}" alt="Escudo oficial de la Universidad Nacional de Colombia"></div>
<div class="institucion">Universidad Nacional de Colombia</div>
<div>Sede Medellín · Facultad de Minas</div>
<p>Medellín, Colombia · 2026</p>
</header><!-- PORTADA_INSTITUCIONAL_FIN -->'''
if '<!-- PORTADA_INSTITUCIONAL_INICIO -->' in s:
    s = re.sub(r'<!-- PORTADA_INSTITUCIONAL_INICIO -->.*?<!-- PORTADA_INSTITUCIONAL_FIN -->', lambda _: cover_html, s, flags=re.S)
else:
    s = s.replace('<body>', '<body>' + cover_html, 1)
html.write_text(s, encoding='utf-8')
print('Portada incorporada al LaTeX y al informe interactivo.')

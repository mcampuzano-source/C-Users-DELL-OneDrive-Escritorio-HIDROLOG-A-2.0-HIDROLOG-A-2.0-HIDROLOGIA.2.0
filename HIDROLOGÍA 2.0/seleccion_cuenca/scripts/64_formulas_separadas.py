"""Prepara fórmulas tipográficas; no modifica el punto 1."""
from pathlib import Path
import re, json, shutil
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'; ROOT=DOCS.parents[3]
OUT=DOCS/'revision_formulas'; OUT.mkdir(exist_ok=True)
for source,name in [(ROOT/'Informe_Hidrologia_actualizado_5_4.pdf','base_antes.pdf'),(DOCS/'latex/informe_ordenado.tex','base_antes.tex'),(DOCS/'informe_interactivo.html','base_antes.html')]:
    if not (OUT/name).exists(): shutil.copy2(source,OUT/name)
tex=(OUT/'base_antes.tex').read_text(encoding='utf-8')
begin=tex.index(r'\section{Relaciones entre series y modelos estadísticos}')
end=tex.index('% PUNTO_3_COMMIT',begin)
prefix=tex[:begin]; body=tex[begin:end]; suffix=tex[end:]
catalog=[]
def eq(math):
    catalog.append({'chapter':2,'number':f'2.{len(catalog)+1}','math':math})
    return '\n\\begin{equation}\n'+math+'\n\\end{equation}\n'
def replace(old,new):
    global body
    assert old in body,old
    body=body.replace(old,new,1)
replace('Con lluvia local como referencia y error e = IMERG - local, el sesgo medio',
        'Con lluvia local como referencia, el error mensual se define mediante'+eq(r'e_t=P_{\mathrm{IMERG},t}-L_t')+'El sesgo medio')
replace('Se define k$\\geq$0 como correlación entre P del mes t-k y Q del mes t; k=1 significa lluvia del mes anterior.',
        'Se relaciona la lluvia antecedente con el caudal mediante'+eq(r'\rho(k)=\operatorname{corr}\!\left[P(t-k),Q(t)\right],\qquad k\geq 0')+'Un rezago de un mes significa que se utiliza la lluvia del mes anterior.')
replace('R = 86,4 $\\times$ días del mes $\\times$ Q / 2797,19, en mm/mes.',
        'la conversión a escorrentía mensual'+eq(r'R_m=\frac{86{,}4\,d_m\,Q_m}{2797{,}19}\quad[\mathrm{mm/mes}]')+'Aquí, $d_m$ es el número de días del mes y $Q_m$ el caudal medio mensual en m$^3$/s.')
replace("Se define X'(t)=X(t)-promedio de X para el mes calendario de t.",
        'La anomalía mensual se define como'+eq(r"X'(t)=X(t)-\overline{X}_{j(t)}")+'La media de referencia corresponde al mes calendario $j(t)$.')
replace(r'Se comparan media constante, climatología mensual, Q=a+bP(t), Q=a+bP(t-1), Q=a+bP(t)+cP(t-1) y Q=a+b$\sqrt{\vphantom{P}}$P(t).',
        'Se comparan la media constante y la climatología mensual con cuatro relaciones que incorporan precipitación:'+
        eq(r'Q_t=a+bP_t')+eq(r'Q_t=a+bP_{t-1}')+eq(r'Q_t=a+bP_t+cP_{t-1}')+eq(r'Q_t=a+b\sqrt{P_t}'))
# Las ecuaciones de ajuste ya estaban separadas; ahora se numeran también.
body=re.sub(r'\\\[(.*?)\\\]',lambda m:eq(m.group(1)),body,flags=re.S)
replace(r'R\_est=86,4$\times$días\_del\_mes$\times$Q\_est/2797,19, pero la regresión no conserva masa:',
        'la siguiente expresión:'+eq(r'\widehat{R}_m=\frac{86{,}4\,d_m\,\widehat{Q}_m}{2797{,}19}')+'Sin embargo, la regresión no conserva masa:')
replace('con salida max(0, expresión): IMERG, -87,269198 + 0,465439 P(t) + 0,433065 P(t-1); CHIRPS, -35,852625 + 0,422155 P(t) + 0,434939 P(t-1).',
        'con el mismo truncamiento de los valores negativos:'+
        eq(r'\widehat{Q}_{\mathrm{IMERG},t}=\max\!\left(0,-87{,}269198+0{,}465439P_t+0{,}433065P_{t-1}\right)')+
        eq(r'\widehat{Q}_{\mathrm{CHIRPS},t}=\max\!\left(0,-35{,}852625+0{,}422155P_t+0{,}434939P_{t-1}\right)'))
replace('NSE=1-SSE/SST compara el error con la media del periodo evaluado;',
        'La eficiencia de Nash–Sutcliffe se calcula mediante'+eq(r'\mathrm{NSE}=1-\frac{\mathrm{SSE}}{\mathrm{SST}}')+'Este indicador compara el error con la media del periodo evaluado;')
body=body.replace(r'$\sqrt{\vphantom{P}}$P',r'$\sqrt{P}$').replace(r'$\sqrt{\vphantom{P}}$(mm/mes)',r'$\sqrt{\mathrm{mm/mes}}$')
# Numera en el orden final del texto, incluso las ecuaciones de ajuste existentes.
maths=re.findall(r'\\begin\{equation\}\s*(.*?)\s*\\end\{equation\}',body,re.S)
catalog=[{'chapter':2,'number':f'2.{i+1}','math':m} for i,m in enumerate(maths)]
body=body.replace(r'\subsubsection*{Relaciones candidatas y criterio de selección}',r'\begin{samepage}\subsubsection*{Relaciones candidatas y criterio de selección}')
body=body.replace('Q_t=a+b\\sqrt{P_t}\n\\end{equation}', 'Q_t=a+b\\sqrt{P_t}\n\\end{equation}\n\\end{samepage}')
body=re.sub(r'(\\begin\{equation\}\s*\\widehat\{L\}_t=.*?\\end\{equation\}\s*\\begin\{equation\}\s*\\widehat\{L\}_t=.*?\\end\{equation\})',lambda m:'\\begin{samepage}\n'+m.group(1)+'\n\\end{samepage}',body,flags=re.S)
body=body.replace(r'\section{Relaciones entre series y modelos estadísticos}',r'\section{Relaciones entre series y modelos estadísticos}'+'\n'+r'\setcounter{equation}{0}\renewcommand{\theequation}{2.\arabic{equation}}')
result=prefix+body+suffix
assert result[:begin]==prefix
(DOCS/'latex/informe_ordenado.tex').write_text(result,encoding='utf-8')
(OUT/'catalogo_2.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
print('Punto 2:',len(catalog),'ecuaciones; fuente del punto 1 intacta.')

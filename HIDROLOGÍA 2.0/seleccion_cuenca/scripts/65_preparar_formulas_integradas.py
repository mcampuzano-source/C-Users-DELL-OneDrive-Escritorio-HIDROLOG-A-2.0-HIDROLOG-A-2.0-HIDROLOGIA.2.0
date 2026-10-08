"""Prepara reemplazos tipográficos para las páginas integradas de 3, 4 y 5."""
from pathlib import Path
import re,json,subprocess
import pymupdf as fitz
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos';OUT=DOCS/'revision_formulas'
source=fitz.open(OUT/'base_antes.pdf')
specs=[];catalog=json.loads((OUT/'catalogo_2.json').read_text(encoding='utf-8'))
counts={3:0,4:0,5:0}
def clean(s):
    s=s.replace('ﬁ','fi').replace('ﬂ','fl').replace('ﬀ','ff')
    s=re.sub(r'(\w)-\n(\w)',r'\1\2',s)
    return ' '.join(s.split())
def esc(s):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#'),('$',r'\$')]:s=s.replace(a,b)
    for a,b in [('–','--'),('−','-'),('’',"'"),('◦',r'$^\circ$'),('°',r'$^\circ$'),('³',r'$^3$'),('²',r'$^2$'),('α',r'$\alpha$'),('β',r'$\beta$'),('ϵ',r'$\epsilon$'),('≥',r'$\geq$'),('∆',r'$\Delta$'),('µ',r'$\mu$'),('Φ',r'$\Phi$')]:s=s.replace(a,b)
    return s
def eq(ch,math):
    counts[ch]+=1;num=f'{ch}.{counts[ch]}'
    catalog.append({'chapter':ch,'number':num,'math':math})
    return '\n\\begin{equation}\n'+math+r'\tag{'+num+'}\n\\end{equation}\n'
def block(pn,needle):
    return next(b for b in source[pn-1].get_text('blocks',flags=0) if needle in clean(b[4]))
def add(pn,rect,body):specs.append({'page':pn,'rect':list(rect),'body':body})
def replace(pn,needle,old,new):
    b=block(pn,needle);s=clean(b[4]);assert old in s,(pn,old,s)
    before,after=s.split(old,1);add(pn,b[:4],esc(before)+new+esc(after))
replace(45,'La variable original','T[◦C] = T[K] −273, 15.',eq(3,r'T[{}^\circ\mathrm{C}]=T[\mathrm{K}]-273{,}15'))
add(45,[56.5,313,541,379],esc('El archivo ya contiene medias mensuales de medias diarias: no se suman ni se vuelve a calcular una media temporal. Si se parte de datos diarios completos, la media mensual se calcula como')+
    eq(3,r'T_m=\frac{1}{N_m}\sum_{d=1}^{N_m}T_d')+esc('Se utilizan todos los 28, 29, 30 o 31 días del mes. Los 548 meses de la serie de cuenca están válidos. Para representar la cuenca se ponderan 36 celdas según el área de intersección con el polígono:')+
    eq(3,r'T_m^B=\sum_i w_iT_{i,m},\qquad w_i=\frac{A(B\cap C_i)}{\sum_i A(B\cap C_i)}')+esc('Las celdas cubren el 100 % del polígono de cuenca.'))
replace(46,'Para cada mes calendario','at = Xt −µj(t) y zt = at/sj(t).',eq(3,r'a_t=X_t-\mu_{j(t)},\qquad z_t=\frac{a_t}{s_{j(t)}}'))
replace(48,'Secuencia cronológica completa','Yt = αj(t) + βt + ϵt.',eq(3,r'Y_t=\alpha_{j(t)}+\beta t+\epsilon_t'))
replace(50,'1. Tendencia lineal por OLS','Yt = β0 + β1t + ϵt',eq(3,r'Y_t=\beta_0+\beta_1t+\epsilon_t'))
add(56,[56.2,540.5,540,585.5],esc('Transformada, ventana y normalización. En cada tramo continuo de N meses se calcula la transformada discreta:')+
    eq(4,r'X_k=\sum_{t=0}^{N-1}x_t\exp\!\left(-\frac{2\pi\mathrm{i}kt}{N}\right)')+
    esc('Se reportan las frecuencias positivas, los periodos equivalentes y el espaciamiento entre frecuencias:')+
    eq(4,r'f_k=\frac{k}{N\Delta t},\qquad T_k=\frac{1}{f_k},\qquad\Delta f=\frac{1}{N\Delta t}')+
    esc('Se usa el periodograma unilateral con ventana rectangular (sin taper), cuya potencia de base se normaliza como')+
    eq(4,r'\mathcal{P}_k=\frac{|X_k|^2}{N^2}')+
    esc('Esta potencia se duplica en las frecuencias positivas, excepto en Nyquist cuando N es par. La suma de potencias reproduce la varianza poblacional de la señal centrada y las unidades son el cuadrado de la variable. No se rellena con ceros ni se interpreta la frecuencia cero como un periodo finito.'))
add(56,[56.2,697.5,540,738.5],esc('Convención y lectura. Se presentan periodogramas unilaterales de densidad espectral. Para una frecuencia de muestreo de una muestra por mes, la densidad de base se expresa como')+
    eq(4,r'S(f_k)=\frac{|X_k|^2}{f_s\sum_t w_t^2},\qquad f_s=1\ \mathrm{muestra/mes}')+
    esc('Se duplican los bins positivos, salvo Nyquist. La densidad tiene unidades de variable al cuadrado por mes. La potencia integrada por bin y su normalización porcentual son')+
    eq(4,r'\mathcal{P}_k=S(f_k)\Delta f,\qquad p_k=100\,\frac{\mathcal{P}_k}{\sum_{j>0}\mathcal{P}_j}')+
    esc('La potencia por bin tiene unidades de variable al cuadrado. Las curvas normalizadas permiten comparar formas, no variabilidad absoluta entre variables. La varianza original y su unidad se conservan en los archivos de resultados.'))
replace(61,'Las medias mensuales','Z=Φ/9,80665 m.',eq(5,r'Z=\frac{\Phi}{g},\qquad g=9{,}80665\ \mathrm{m/s^2}')+esc('La altura resultante se expresa en metros. '))
replace(63,'La referencia comprende','r_j(lon,lat;ell) = corr[a_X(t),a_Y(lon,lat,t-ell)] para mes(t)=j,',eq(5,r'r_j(\lambda,\varphi;\ell)=\operatorname{corr}\!\left[a_X(t),a_Y(\lambda,\varphi,t-\ell)\right],\qquad j(t)=j'))
b=block(90,'La dependencia relevante');s=clean(b[4])
old='n_eff = n(1-rhoX*rhoY)/(1+rhoX*rhoY), limitada a [3,n],'
assert old in s
a,z=s.split(old,1)
before,after=z.split('t=|r| sqrt(df/(1-r²)), con df=n_eff-2 para anomalías y df=n_eff-3 al controlar el año.',1)
add(90,b[:4],esc(a)+eq(5,r'n_{\mathrm{ef}}=n\,\frac{1-\rho_X\rho_Y}{1+\rho_X\rho_Y},\qquad 3\leq n_{\mathrm{ef}}\leq n')+esc('Limitada al intervalo indicado y ')+esc(before)+eq(5,r't=|r|\sqrt{\frac{\nu}{1-r^2}}')+esc('Los grados de libertad utilizados son')+eq(5,r'\nu=\begin{cases}n_{\mathrm{ef}}-2,&\text{para anomalías},\\n_{\mathrm{ef}}-3,&\text{al controlar el año}.\end{cases}')+esc(after.replace('Con df<=1','Con un grado de libertad o menos')))
(OUT/'reemplazos.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'catalogo.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
header=r'''\documentclass[10pt]{article}
\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot]{babel}\usepackage{amsmath}
\usepackage[paperwidth=485pt,paperheight=1800pt,margin=1pt]{geometry}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}\pagestyle{empty}
\begin{document}
'''
bodies=[s['body'] for s in specs]+['\\begin{equation}\n'+c['math']+r'\tag{'+c['number']+'}\n\\end{equation}' for c in catalog]
(OUT/'bloques.tex').write_text(header+'\n\\newpage\n'.join(bodies)+'\n\\end{document}',encoding='utf-8')
print(len(specs),'bloques integrados;',len(catalog),'ecuaciones tipográficas.')

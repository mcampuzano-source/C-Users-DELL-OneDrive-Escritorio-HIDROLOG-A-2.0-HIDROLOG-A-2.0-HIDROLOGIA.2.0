"""Añade una justificación breve sin regenerar datos ni gráficos."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
JUSTIFICATION = ('Se utilizan frecuencias relativas para expresar qué porcentaje de meses cae en cada intervalo y facilitar la comparación de las distribuciones. '
                 'En CHIRPS e IMERG se mantienen los mismos 285 meses y límites de clase, por lo que las diferencias entre barras corresponden a la distribución de los productos y no a distintos tamaños de muestra.')


def main():
    script = ROOT / 'scripts' / '22_imerg_poligono_estadisticas.py'
    text = script.read_text(encoding='utf-8')
    anchor = 'Barras en porcentaje de meses, cuya suma es 100%.'
    if JUSTIFICATION not in text:
        assert text.count(anchor) == 1
        script.write_text(text.replace(anchor, anchor+' '+JUSTIFICATION), encoding='utf-8')
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    if JUSTIFICATION not in text:
        assert text.count(anchor) == 1
        html.write_text(text.replace(anchor, anchor+' '+JUSTIFICATION), encoding='utf-8')
    tex = DOC / 'imerg_poligono' / 'apartado_1_3.tex'
    text = tex.read_text(encoding='utf-8')
    anchor_tex = anchor.replace('%', r'\%')
    if JUSTIFICATION not in text:
        assert text.count(anchor_tex) == 1
        tex.write_text(text.replace(anchor_tex, anchor_tex+' '+JUSTIFICATION), encoding='utf-8')


if __name__ == '__main__':
    main()

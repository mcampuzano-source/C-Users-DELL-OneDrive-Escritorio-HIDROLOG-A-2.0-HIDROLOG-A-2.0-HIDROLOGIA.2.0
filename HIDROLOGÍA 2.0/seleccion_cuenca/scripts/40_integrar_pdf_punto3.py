"""Integra las páginas publicadas del punto 3 y actualiza índice y paginación.

El commit de origen contiene PDF/HTML, sin fuentes LaTeX del nuevo análisis.
Conservamos sus páginas vectoriales y la base revisada con portada y punto 2.
"""
from pathlib import Path
import pymupdf

DOCS = Path(__file__).resolve().parents[1] / 'la_vieja/documentos'
base = pymupdf.open(DOCS / 'apartado_3/base_portada_punto2.pdf')
p3 = pymupdf.open(DOCS / 'apartado_3/punto_3_commit_2d27402.pdf')
toc = base.get_toc()
start = next(row[2] - 1 for row in toc if row[0] == 1 and row[1].startswith('Tendencias hidroclim'))
end = next(row[2] - 1 for row in toc if row[0] == 1 and row[1].startswith('Análisis de frecuencias'))
out = pymupdf.open()
out.insert_pdf(base, from_page=0, to_page=start - 1)
out.insert_pdf(p3)
out.insert_pdf(base, from_page=end)
offset = len(p3) - (end - start)
new_toc = []
sub_offsets = iter([0, 1, 3, 5, 8, 9])
for level, title, page in toc:
    if start + 1 <= page <= end:
        page = start + 1 + (next(sub_offsets) if level == 2 else 0)
    elif page > end:
        page += offset
    new_toc.append([level, title, page])
# Incorporar el 5.1 cuando sus datos y sección hayan sido generados.
p51_path = DOCS / 'apartado_5_1/punto_5_1.pdf'
if p51_path.exists():
    p51 = pymupdf.open(p51_path)
    pos = next(row[2] - 1 for row in new_toc if row[0] == 1 and row[1].startswith('Mapas de correlación'))
    # Quitar únicamente el encabezado y el marcador pendiente de 5.1.
    # Los apartados 5.2-5.4, conclusiones y procedencia se conservan.
    old_page = out[pos]
    old_page.add_redact_annot(pymupdf.Rect(35, 40, old_page.rect.width - 35, 131), fill=(1, 1, 1))
    old_page.apply_redactions()
    out.insert_pdf(p51, start_at=pos)
    for row in new_toc:
        if row[2] > pos:
            if row[1] not in ('Mapas de correlación con el clima global', 'Seleccionar los campos climáticos'):
                row[2] += len(p51)
    p51.close()
p52_path = DOCS / 'apartado_5_2/punto_5_2.pdf'
if p52_path.exists():
    p52 = pymupdf.open(p52_path)
    pos = next(row[2] - 1 for row in new_toc if row[1] == 'Definir y calcular los mapas mensuales')
    old_page = out[pos]
    old_page.add_redact_annot(pymupdf.Rect(35, 135, old_page.rect.width - 35, 183), fill=(1, 1, 1))
    old_page.apply_redactions()
    out.insert_pdf(p52, start_at=pos)
    for row in new_toc:
        if row[2] > pos and row[1] != 'Definir y calcular los mapas mensuales':
            row[2] += len(p52)
    p52.close()
out.set_toc(new_toc)
# Portada sin número; el índice comienza en la página numerada 1.
for i in range(1, len(out)):
    page = out[i]
    y = page.rect.height
    page.draw_rect(pymupdf.Rect(0, y - 42, page.rect.width, y), color=None, fill=(1, 1, 1))
    page.insert_textbox(pymupdf.Rect(0, y - 35, page.rect.width, y - 15), str(i), fontsize=10, align=1)
# Rehacer el índice para que páginas y enlaces correspondan al informe integrado.
index = out[1]
index.add_redact_annot(pymupdf.Rect(35, 35, index.rect.width - 35, index.rect.height - 43), fill=(1, 1, 1))
index.apply_redactions()
index.insert_text((56, 66), 'Índice', fontsize=18)
y = 98
section = 0
sub = 0
for level, title, page in new_toc:
    if level == 1:
        section += 1
        sub = 0
        prefix = f'{section}. '
        y += 7
    else:
        sub += 1
        prefix = f'{section}.{sub}. '
    x = 56 if level == 1 else 68
    index.insert_text((x, y), prefix + title, fontsize=10 if level == 1 else 9)
    index.insert_text((534, y), str(page - 1), fontsize=9)
    index.insert_link({'kind': pymupdf.LINK_GOTO, 'from': pymupdf.Rect(x, y - 11, 553, y + 4), 'page': page - 1})
    y += 19
out.set_metadata({'title': 'Cuenca del río La Vieja - Informe integrado', 'author': 'Marcos Correal Suarez; Andrea Carolina Vergara Tenorio; Mariana Campuzano Tobón', 'subject': 'Hidrología - Carlos David Hoyos Ortiz - Ingeniería Civil'})
target = DOCS / 'apartado_3/informe_integrado.pdf'
out.save(target, garbage=4, deflate=True)
out.close()
base.close()
p3.close()
import shutil
for dest in [DOCS / 'informe_actualizado.pdf', DOCS / 'latex/informe_ordenado.pdf']:
    try:
        shutil.copyfile(target, dest)
        print('Actualizado:', dest.name)
    except PermissionError:
        print('Bloqueado:', dest)

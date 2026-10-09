"""Reconstruye la edición publicada completa desde fuentes verificadas.

No recalcula observaciones, modelos ni interpretaciones: los scripts históricos
documentan esos análisis. Este módulo reproduce su edición final integrada.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import shutil
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
SOURCES = PROJECT / "fuentes_informes"
DOCUMENTS = PROJECT / "la_vieja" / "documentos"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_sources():
    manifest = json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        path = SOURCES / name
        if not path.is_file():
            raise FileNotFoundError(f"Falta la fuente {path}")
        if digest(path) != expected["sha256"]:
            raise ValueError(f"Fuente incompleta o distinta: {path}. Si usa Git LFS, ejecute git lfs pull.")
    return manifest


def build_html(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    base = (SOURCES / "informe_base.html").read_text(encoding="utf-8")
    anchor = "<!-- CONTROL_FALTANTES_FIN -->"
    if base.count(anchor) != 1:
        raise ValueError("La fuente HTML no contiene una única ubicación para el control 1.4.")
    blocks = [(SOURCES / name).read_text(encoding="utf-8")
              for name in ("contraste_1_4.html", "registro_1_4.html")]
    result = base.replace(anchor, anchor + "".join(blocks), 1)
    if result.replace("".join(blocks), "", 1) != base:
        raise ValueError("La integración cambió el contenido de la fuente original.")
    for marker in ("CONTRASTE_CAMBIOS_PRODUCTOS", "REGISTRO_ANOMALIAS_1_4"):
        if result.count(f"<!-- {marker}_INICIO -->") != 1:
            raise ValueError(f"Bloque duplicado: {marker}")
    match = re.search(r'srcdoc="(.*?)"', blocks[0], re.S)
    viewer = html.unescape(match.group(1)) if match else ""
    if viewer.count('"method":"update"') != 4:
        raise ValueError("El visor no contiene los cuatro casos seleccionables.")
    path = output / "Informe_Hidrologia_interactivo.html"
    path.write_text(result, encoding="utf-8")
    return {"file": str(path), "sha256": digest(path), "cases": 4,
            "original_content_preserved": True}


def scientific_words(page):
    return [w[4] for w in page.get_text("words")
            if 35 < w[1] and w[3] < page.rect.height - 42]


def build_pdf(output, manifest):
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("Instale las dependencias: python -m pip install -r requirements_informes.txt") from error
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    before = manifest["insert_before_page"] - 1
    with fitz.open(SOURCES / "informe_base.pdf") as source:
        if len(source) != manifest["base_pdf_pages"]:
            raise ValueError("La fuente PDF no tiene la paginación esperada.")
        with fitz.open() as added, fitz.open() as result:
            for name in ("cuatro_casos_pdf.pdf", "registro_anomalias_pdf.pdf"):
                with fitz.open(SOURCES / name) as document:
                    added.insert_pdf(document)
            shift = len(added)
            if shift != 6:
                raise ValueError("Los anexos deben contener cuatro casos y dos tablas.")
            result.insert_pdf(source, to_page=before - 1)
            result.insert_pdf(added)
            result.insert_pdf(source, from_page=before)
            toc = source.get_toc()
            for row in toc:
                if row[2] >= before + 1:
                    row[2] += shift
            position = next(i for i, row in enumerate(toc) if "Climatolog" in row[1])
            toc[position:position] = [
                [3, "Cambios documentados: contraste de productos", before + 1],
                [3, "Registro de anomalias y decisiones", before + 5]]
            result.set_toc(toc)
            index = result[1]
            changes = [(fitz.Rect(w[:4]), str(int(w[4]) + shift))
                       for w in index.get_text("words")
                       if w[0] > 520 and w[4].isdigit() and int(w[4]) >= before]
            for rect, value in changes:
                index.add_redact_annot(rect, fill=(1, 1, 1))
            index.apply_redactions(images=0, graphics=0)
            for rect, value in changes:
                index.insert_textbox(fitz.Rect(rect.x0 - 1, rect.y0 - 1, rect.x1 + 6, rect.y1 + 5),
                                     value, fontname="tiro", fontsize=12, align=2)
            for i in range(before, len(result)):
                page = result[i]
                rect = fitz.Rect(270, page.rect.height - 40, 330, page.rect.height - 15)
                page.draw_rect(rect, color=None, fill=(1, 1, 1))
                page.insert_textbox(rect, str(i), fontname="tiro", fontsize=9, align=1)
            path = output / "Informe_Hidrologia_actualizado_1_5.pdf"
            # Escribe primero a un archivo nuevo para admitir ejecuciones repetidas.
            with tempfile.NamedTemporaryFile(dir=output, suffix=".pdf", delete=False) as temporary:
                temporary_path = Path(temporary.name)
            try:
                result.save(temporary_path, garbage=1, deflate=False)
                with fitz.open(temporary_path) as check:
                    if len(check) != manifest["published_pdf_pages"]:
                        raise ValueError("Paginación final incorrecta.")
                    for i in range(2, len(source)):
                        destination = i if i < before else i + shift
                        if scientific_words(source[i]) != scientific_words(check[destination]):
                            raise ValueError(f"Cambió el contenido científico de la página {i + 1}.")
                    if source[0].get_text() != check[0].get_text():
                        raise ValueError("Cambió la portada.")
                temporary_path.replace(path)
            finally:
                temporary_path.unlink(missing_ok=True)
    return {"file": str(path), "pages": manifest["published_pdf_pages"],
            "original_pages_verified": manifest["base_pdf_pages"] - 2,
            "sha256": digest(path), "original_content_preserved": True}


def publish(results):
    """Actualiza las copias visibles; preserva versiones previas fuera del repositorio."""
    backup = Path(tempfile.mkdtemp(prefix="hidrologia_antes_publicacion_"))
    for kind, info in results.items():
        if kind == "html":
            targets = [REPOSITORY / "Informe_Hidrologia_interactivo.html",
                       DOCUMENTS / "informe_interactivo.html"]
        else:
            targets = [REPOSITORY / name for name in (
                "Informe_Hidrologia_actualizado_1_5.pdf", "Informe_Hidrologia_actualizado.pdf",
                "Informe_Hidrologia_actualizado_5_4.pdf", "Informe_Hidrologia_integrado.pdf")]
            targets += [DOCUMENTS / "informe_actualizado.pdf", DOCUMENTS / "informe_actualizado_1_5.pdf",
                        DOCUMENTS / "latex" / "informe_ordenado.pdf"]
        for index, target in enumerate(targets):
            if target.exists():
                shutil.copy2(target, backup / f"{kind}_{index}_{target.name}")
            shutil.copy2(info["file"], target)
    return str(backup)


def main(default="ambos"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tipo", choices=("html", "pdf", "ambos"), default=default)
    parser.add_argument("--salida", type=Path, default=PROJECT / "salida_informes")
    parser.add_argument("--publicar", action="store_true", help="Actualizar también las copias principales.")
    args = parser.parse_args()
    manifest = validate_sources()
    results = {}
    if args.tipo in ("html", "ambos"):
        results["html"] = build_html(args.salida)
    if args.tipo in ("pdf", "ambos"):
        results["pdf"] = build_pdf(args.salida, manifest)
    if args.publicar:
        backup = publish(results)
        print(f"Copias principales actualizadas. Respaldo: {backup}")
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "verificacion_generacion.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

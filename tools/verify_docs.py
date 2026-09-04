"""
Verificación de integridad de la documentación web SDEP.
"""
import json
from pathlib import Path

def main():
    docs_data_path = Path("docs/docs_data.js")
    if not docs_data_path.exists():
        raise FileNotFoundError("docs/docs_data.js no existe.")

    content = docs_data_path.read_text(encoding="utf-8")
    marker = "window.SDEP_DOCS_DATA = "
    if marker not in content:
        raise ValueError("No se encontró el marcador de asignación en docs_data.js")

    json_str = content.split(marker)[1].strip().rstrip(";")
    data = json.loads(json_str)

    print(f"Total documentos indexados: {len(data)}")
    assert len(data) == 17, f"Se esperaban 17 documentos, pero se obtuvieron {len(data)}"

    total_words = 0
    categories = set()

    for d in data:
        assert d.get("id"), "Falta 'id'"
        assert d.get("title"), f"Falta 'title' en {d.get('id')}"
        assert d.get("category"), f"Falta 'category' en {d.get('id')}"
        assert d.get("content"), f"Falta 'content' en {d.get('id')}"
        assert d.get("readingTime", 0) > 0, f"readingTime invalido en {d.get('id')}"
        total_words += d.get("wordCount", 0)
        categories.add(d.get("category"))
        print(f"  [OK] {d.get('badge') or 'DOC':<12} | {d.get('id'):<25} | {d.get('wordCount'):>6} palabras | ~{d.get('readingTime'):>2} min")

    print(f"\nCategorias encontradas: {categories}")
    print(f"Total palabras en todo el corpus: {total_words:,}")

    # Verificar que los archivos HTML, CSS, JS y vendors existan
    required_files = [
        "docs/index.html",
        "docs/styles.css",
        "docs/script.js",
        "docs/README.md",
        "docs/vendor/marked.min.js",
        "docs/vendor/prism.min.js",
        "docs/vendor/prism-python.min.js",
        "docs/vendor/prism-bash.min.js",
        "docs/vendor/prism-sql.min.js",
        "docs/vendor/prism-json.min.js",
        "docs/vendor/prism-markdown.min.js"
    ]

    print("\nVerificando archivos requeridos de la web...")
    for rf in required_files:
        p = Path(rf)
        if not p.exists():
            raise FileNotFoundError(f"Archivo requerido no encontrado: {rf}")
        size_kb = p.stat().st_size / 1024
        print(f"  [OK] {rf:<35} ({size_kb:.1f} KB)")

    print("\n[EXITO] Todos los chequeos de integracion pasaron satisfactoriamente!")

if __name__ == "__main__":
    main()

"""
Generador del catálogo centralizado de documentación (docs_data.js).
Empaqueta todos los documentos Markdown de TESIS/ y de la raíz del proyecto
en un archivo JavaScript estructurado para permitir lectura instantánea offline
y en cualquier navegador (sin problemas de CORS en file://).
"""

import os
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "docs_data.js"
GITHUB_REPO_URL = "https://github.com/LiebeBlack/SDEP_CPP5"

DOCUMENTS_MANIFEST = [
    # --- Tesis Académica ---
    {
        "id": "tesis-indice-general",
        "file": "TESIS/INDICE_GENERAL.md",
        "title": "Índice General y Resumen Ejecutivo",
        "subtitle": "Estructura global de la investigación, resumen ejecutivo y abstract en inglés.",
        "category": "Tesis Académica",
        "order": 1,
        "badge": "Índice",
        "icon": "📑"
    },
    {
        "id": "tesis-proyecto-social",
        "file": "TESIS/PROYECTO_SOCIAL_TECNOLOGICO.md",
        "title": "Proyecto Social Tecnológico",
        "subtitle": "Justificación social, tecnológica, económica y cronograma del proyecto aplicado.",
        "category": "Tesis Académica",
        "order": 2,
        "badge": "PST",
        "icon": "🏛️"
    },
    {
        "id": "tesis-anteproyecto",
        "file": "TESIS/ANTEPROYECTO_TESIS.md",
        "title": "Anteproyecto de Tesis",
        "subtitle": "Planteamiento preliminar, objetivos, hipótesis, variables y presupuesto.",
        "category": "Tesis Académica",
        "order": 3,
        "badge": "Anteproyecto",
        "icon": "📐"
    },
    {
        "id": "tesis-capitulo-1",
        "file": "TESIS/CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md",
        "title": "Capítulo I: Planteamiento del Problema",
        "subtitle": "Diagnóstico de la situación actual, formulación y justificación académica.",
        "category": "Tesis Académica",
        "order": 4,
        "badge": "Capítulo 01",
        "icon": "🎯"
    },
    {
        "id": "tesis-capitulo-2",
        "file": "TESIS/CAPITULO_II_MARCO_TEORICO.md",
        "title": "Capítulo II: Marco Teórico",
        "subtitle": "Antecedentes nacionales e internacionales, bases teóricas y fundamentación legal.",
        "category": "Tesis Académica",
        "order": 5,
        "badge": "Capítulo 02",
        "icon": "📚"
    },
    {
        "id": "tesis-capitulo-3",
        "file": "TESIS/CAPITULO_III_METODOLOGIA.md",
        "title": "Capítulo III: Metodología",
        "subtitle": "Enfoque metodológico, diseño de investigación, población, técnicas e instrumentos.",
        "category": "Tesis Académica",
        "order": 6,
        "badge": "Capítulo 03",
        "icon": "🔬"
    },
    {
        "id": "tesis-capitulo-4",
        "file": "TESIS/CAPITULO_IV_RESULTADOS.md",
        "title": "Capítulo IV: Resultados y Software",
        "subtitle": "Descripción del sistema, módulos, arquitectura de software y validación experimental.",
        "category": "Tesis Académica",
        "order": 7,
        "badge": "Capítulo 04",
        "icon": "📊"
    },
    {
        "id": "tesis-capitulo-5",
        "file": "TESIS/CAPITULO_V_CONCLUSIONES.md",
        "title": "Capítulo V: Conclusiones y Recomendaciones",
        "subtitle": "Evaluación del cumplimiento de objetivos, aportes y líneas futuras de trabajo.",
        "category": "Tesis Académica",
        "order": 8,
        "badge": "Capítulo 05",
        "icon": "🎓"
    },
    {
        "id": "tesis-bibliografia-anexos",
        "file": "TESIS/BIBLIOGRAFIA_ANEXOS.md",
        "title": "Bibliografía y 10 Anexos",
        "subtitle": "Referencias completas (normas APA) y los 10 anexos técnicos de la investigación.",
        "category": "Tesis Académica",
        "order": 9,
        "badge": "Anexos",
        "icon": "📎"
    },
    {
        "id": "tesis-completado",
        "file": "TESIS/COMPLETADO.md",
        "title": "Estado Final y Validación del Proyecto",
        "subtitle": "Certificación de cumplimiento del software (281 tests, arquitectura y cobertura).",
        "category": "Tesis Académica",
        "order": 10,
        "badge": "Validación",
        "icon": "✅"
    },

    # --- Documentación Técnica & Guías ---
    {
        "id": "readme",
        "file": "README.md",
        "title": "README - Visión General del Sistema",
        "subtitle": "Presentación del software, características funcionales, requisitos y primeros pasos.",
        "category": "Documentación Técnica",
        "order": 11,
        "badge": "General",
        "icon": "📖"
    },
    {
        "id": "doc-tecnica",
        "file": "DOCUMENTACION_TECNICA.md",
        "title": "Documentación Técnica y Arquitectura",
        "subtitle": "Arquitectura en capas, modelos relacionales SQLAlchemy, servicios y patrones aplicados.",
        "category": "Documentación Técnica",
        "order": 12,
        "badge": "Arquitectura",
        "icon": "🛠️"
    },
    {
        "id": "guia-usuario",
        "file": "GUIA_USUARIO.md",
        "title": "Guía de Usuario y Manual Operativo",
        "subtitle": "Manual paso a paso para empleados, documentos, incidencias, nóminas y reportes.",
        "category": "Documentación Técnica",
        "order": 13,
        "badge": "Manual",
        "icon": "👤"
    },
    {
        "id": "estructura-proyecto",
        "file": "ESTRUCTURA_PROYECTO_COMPLETO.md",
        "title": "Estructura Completa del Proyecto",
        "subtitle": "Árbol íntegro de directorios, módulos fuente, pruebas unitarias y ficheros auxiliares.",
        "category": "Documentación Técnica",
        "order": 14,
        "badge": "Estructura",
        "icon": "🗂️"
    },
    {
        "id": "notas-desarrollo",
        "file": "NOTAS_DESARROLLO.md",
        "title": "Notas y Decisiones de Desarrollo",
        "subtitle": "Bitácora de desarrollo, decisiones de diseño, optimizaciones y lecciones aprendidas.",
        "category": "Documentación Técnica",
        "order": 15,
        "badge": "Bitácora",
        "icon": "📝"
    },
    {
        "id": "contributing",
        "file": "CONTRIBUTING.md",
        "title": "Guía de Contribución y Estándares",
        "subtitle": "Flujo de trabajo Git, guía de estilo PEP 8, pruebas automatizadas y estándares de calidad.",
        "category": "Documentación Técnica",
        "order": 16,
        "badge": "Contribución",
        "icon": "🤝"
    },
    {
        "id": "quickstart-cicd",
        "file": "QUICKSTART_CICD.md",
        "title": "Quickstart CI/CD y Automatización",
        "subtitle": "Instrucciones de configuración rápida de integración continua con GitHub Actions.",
        "category": "Documentación Técnica",
        "order": 17,
        "badge": "CI/CD",
        "icon": "⚡"
    }
]


def calculate_reading_time(text: str) -> int:
    """Calcula el tiempo estimado de lectura en minutos (aprox. 200 palabras por minuto)."""
    words = len(re.findall(r"\w+", text))
    return max(1, round(words / 200))


def count_words(text: str) -> int:
    """Cuenta el número de palabras en el texto."""
    return len(re.findall(r"\w+", text))


def build_bundle():
    print(f"Empaquetando documentos desde {REPO_ROOT}...")
    documents = []

    for item in DOCUMENTS_MANIFEST:
        file_path = REPO_ROOT / item["file"]
        if not file_path.exists():
            print(f"⚠️ Advertencia: No se encontró el archivo {file_path}")
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")

        word_count = count_words(content)
        read_time = calculate_reading_time(content)
        github_url = f"{GITHUB_REPO_URL}/blob/main/{item['file']}"

        documents.append({
            "id": item["id"],
            "title": item["title"],
            "subtitle": item["subtitle"],
            "category": item["category"],
            "order": item["order"],
            "badge": item["badge"],
            "icon": item["icon"],
            "filename": item["file"],
            "githubUrl": github_url,
            "wordCount": word_count,
            "readingTime": read_time,
            "content": content
        })
        print(f"[OK] Procesado: [{item['id']}] {item['title']} ({word_count:,} palabras, ~{read_time} min)")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_DIR = DOCS_DIR / "content"
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    (CONTENT_DIR / "TESIS").mkdir(parents=True, exist_ok=True)

    # Sync raw markdown files into docs/content/ for GitHub Pages same-origin access
    for item in DOCUMENTS_MANIFEST:
        src_path = REPO_ROOT / item["file"]
        if src_path.exists():
            dest_path = CONTENT_DIR / item["file"]
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(src_path.read_bytes())

    js_content = "/**\n"
    js_content += " * Catálogo Centralizado de Documentos SDEP_CPP5\n"
    js_content += " * Generado automáticamente por tools/generate_docs_bundle.py\n"
    js_content += f" * Total documentos indexados: {len(documents)}\n"
    js_content += " */\n\n"
    js_content += "window.SDEP_DOCS_DATA = " + json.dumps(documents, ensure_ascii=False, indent=2) + ";\n"

    OUTPUT_FILE.write_text(js_content, encoding="utf-8")
    file_size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"Catalogo generado exitosamente en {OUTPUT_FILE} ({file_size_kb:.1f} KB)")
    print(f"Archivos sincronizados en {CONTENT_DIR}")


if __name__ == "__main__":
    build_bundle()

# Plataforma de Documentación Web SDEP

Plataforma web moderna, seria, elegante y ultra-minimalista para el **Sistema de Gestión de Personal y Nómina (SDEP)**. Incorpora un visor interactivo de Markdown integrado directamente en el navegador, catálogo centralizado de 17 documentos técnicos y académicos, buscador instantáneo (`Ctrl+K`) y soporte 100% offline.

---

## 🎨 Características Principales

- **Lector Integrado de Markdown en Web**: Renderiza en tiempo real los 10 documentos de la tesis y los 7 documentos técnicos con tipografía editorial de alta precisión, sin redirigir a archivos planos ni requerir herramientas externas.
- **Formato Markdown Avanzado**:
  - Resaltado de sintaxis con Prism (Python, Bash, SQL, JSON, Markdown).
  - Botón de copia de bloques de código con confirmación visual.
  - Alertas estilo GitHub (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`).
  - Tablas estilizadas, listas de verificación interactivas y citas.
  - Encabezados con anclas y enlaces directos compartibles.
- **Tabla de Contenidos Dinámica (TOC)**: Extracción automática de encabezados (`H2`, `H3`) con *Scrollspy* para indicar visualmente la sección activa.
- **Métricas de Lectura**: Cálculo automático de tiempo estimado de lectura (WPM) y conteo de palabras por documento.
- **Buscador Instantáneo & Paleta de Comandos (`Ctrl+K` / `⌘K`)**: Búsqueda en tiempo real sobre títulos, resúmenes y cuerpo completo de los 17 documentos con fragmentos destacados.
- **Diseño Ultra-Minimalista**:
  - Tema claro y tema oscuro profundo (*Slate/Zinc*) con persistencia en `localStorage`.
  - Tipografía cuidada basada en *Inter* y *JetBrains Mono*.
  - Cabecera flotante con *backdrop-filter* (efecto cristal translúcido).
  - Totalmente adaptable a dispositivos móviles, tablets y monitores ultrawide.
  - Soporte de impresión y exportación a PDF limpia (`@media print`).
- **Funcionamiento 100% Autónomo y Offline**:
  - No depende de servidores locales ni presenta bloqueos de CORS al abrirse directamente mediante el protocolo `file://`.
  - Bibliotecas de terceros empaquetadas localmente en `docs/vendor/`.

---

## 🚀 Cómo Usar

### 1. Apertura Directa en el Navegador

Puedes abrir el portal haciendo doble clic en `docs/index.html` o desde la terminal:

```bash
# Windows
start docs/index.html

# macOS
open docs/index.html

# Linux
xdg-open docs/index.html
```

### 2. Ejecutar mediante Servidor Local (Opcional)

Si prefieres servirlo mediante HTTP:

```bash
# Python 3
python -m http.server 8000 --directory docs

# Abrir en el navegador:
# http://localhost:8000
```

### 3. Enlaces Directos a Documentos (Deep Linking)

El visor soporta enrutamiento por hash. Puedes compartir o acceder directamente a cualquier documento:

- `index.html#doc=readme` — README General del sistema
- `index.html#doc=guia-usuario` — Guía de Usuario y manual operativo
- `index.html#doc=doc-tecnica` — Documentación Técnica y arquitectura
- `index.html#doc=tesis-capitulo-1` — Capítulo I: Planteamiento del Problema
- `index.html#doc=tesis-capitulo-4` — Capítulo IV: Resultados y Software
- `index.html#doc=tesis-bibliografia-anexos` — Bibliografía y los 10 Anexos

---

## 📁 Estructura de la Web

```
docs/
├── index.html              # Estructura HTML de la plataforma y del visor web
├── styles.css              # Sistema de diseño, temas claro/oscuro y estilos Markdown
├── script.js               # Motor de renderizado Markdown, TOC, scrollspy y buscador
├── docs_data.js            # Corpus centralizado con los 17 documentos precompilados
├── README.md               # Esta documentación
└── vendor/                 # Dependencias JavaScript locales (100% offline)
    ├── marked.min.js       # Parser de Markdown de alto rendimiento
    ├── prism.min.js        # Motor de resaltado de código
    ├── prism-python.min.js # Soporte de sintaxis Python
    ├── prism-bash.min.js   # Soporte de sintaxis Bash/Shell
    ├── prism-sql.min.js    # Soporte de sintaxis SQL
    ├── prism-json.min.js   # Soporte de sintaxis JSON
    └── prism-markdown.min.js # Soporte de sintaxis Markdown
```

---

## 🔄 Actualización del Catálogo de Documentos

Cuando edites o agregues contenido en los archivos Markdown de `TESIS/` o de la raíz del proyecto, regenera el catálogo ejecutando:

```bash
python tools/generate_docs_bundle.py
```

Este script:
1. Lee los 17 archivos `.md` en codificación UTF-8.
2. Extrae títulos, resúmenes, categorías y badges.
3. Calcula el conteo de palabras y minutos de lectura estimados.
4. Genera el bundle optimizado `docs/docs_data.js`.

---

## ⌨️ Atajos de Teclado

| Atajo | Acción |
| :--- | :--- |
| `Ctrl + K` / `⌘ + K` | Abrir / cerrar la paleta de búsqueda global |
| `↑` / `↓` | Navegar por los resultados de búsqueda |
| `Enter` | Abrir el documento seleccionado en el visor |
| `Escape` | Cerrar la paleta de búsqueda o salir del lector al portal |

---

## 📄 Licencia

Este proyecto forma parte de **SDEP** y está publicado bajo la [Licencia MIT](https://github.com/LiebeBlack/SDEP_CPP5/blob/main/LICENSE).
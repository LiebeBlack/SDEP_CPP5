# Portal de Documentación SDEP

Portal estático del **Sistema de Gestión de Personal y Nómina (SDEP)**. Reúne el corpus de la tesis, la documentación técnica y los informes académicos en una sola página, con lector de Markdown integrado, catálogo filtrable y búsqueda instantánea (`Ctrl+K`). No necesita servidor, conexión ni compilación: se abre desde el sistema de archivos.

## Contenido publicado

| Bloque | Documentos | Cómo se consulta |
| :--- | ---: | :--- |
| Tesis académica | 14 | Lector integrado, texto completo en `docs_data.js` |
| Documentación técnica | 7 | Lector integrado, texto completo en `docs_data.js` |
| Informes académicos | 4 | Enlace al Markdown del repositorio |

Los 21 documentos del lector viven en `docs_data.js`, que genera `tools/generate_docs_bundle.py`. Los cuatro informes de `informes_academicos/` son entregables independientes de la carrera de Informática; se enlazan a su archivo porque su texto no forma parte del bundle. Para leerlos dentro de la página habría que añadirlos al manifiesto del generador y regenerar el bundle.

---

## 🎨 Características Principales

- **Lector Integrado de Markdown en Web**: Renderiza en tiempo real los 14 documentos de la tesis y los 7 documentos técnicos con tipografía editorial de alta precisión, sin redirigir a archivos planos ni requerir herramientas externas.
- **Formato Markdown Avanzado**:
  - Resaltado de sintaxis con Prism (Python, Bash, SQL, JSON, Markdown).
  - Botón de copia de bloques de código con confirmación visual.
  - Alertas estilo GitHub (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`).
  - Tablas estilizadas, listas de verificación interactivas y citas.
  - Encabezados con anclas y enlaces directos compartibles.
- **Tabla de Contenidos Dinámica (TOC)**: Extracción automática de encabezados (`H2`, `H3`) con *Scrollspy* para indicar visualmente la sección activa.
- **Métricas de Lectura**: Cálculo automático de tiempo estimado de lectura (WPM) y conteo de palabras por documento.
- **Buscador Instantáneo & Paleta de Comandos (`Ctrl+K` / `⌘K`)**: Búsqueda en tiempo real sobre títulos, resúmenes y cuerpo completo de los 21 documentos, sin distinguir mayúsculas ni acentos.
- **Diseño Ultra-Minimalista**:
  - Tema claro y tema oscuro profundo (*Slate/Zinc*) con persistencia en `localStorage`.
  - Tipografía del sistema, sin fuentes externas ni peticiones a terceros.
  - Cabecera flotante con *backdrop-filter* (efecto cristal translúcido).
  - Totalmente adaptable a dispositivos móviles, tablets y monitores ultrawide.
  - Soporte de impresión y exportación a PDF limpia (`@media print`).
- **Funcionamiento 100% Autónomo y Offline**:
  - No depende de servidores locales ni presenta bloqueos de CORS al abrirse mediante el protocolo `file://`.
  - Bibliotecas de terceros empaquetadas localmente en `docs/vendor/`; la tipografía es la del sistema.
  - Al abrir un documento no se consulta la red: el Markdown se renderiza desde `docs_data.js`.

---

## 🧭 Estructura de la Página

La portada se organiza en seis bloques: **Inicio** (presentación y métricas), **Software** (nueve módulos), **Arquitectura** (cinco capas), **Documentos** (catálogo con pestañas y buscador), **Informes** (cuatro informes académicos) e **Inicio Rápido**.

Las pestañas del catálogo y sus recuentos se calculan desde `docs_data.js`; el contador de documentos de la portada también. Ninguna cifra de documentos está escrita a mano, de modo que el portal no se queda desfasado al regenerar el bundle.

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
- `index.html#doc=tesis-documento-01` — Documento 01: Introducción y Planteamiento del Problema
- `index.html#doc=tesis-capitulo-4` — Capítulo IV: Resultados y Software
- `index.html#doc=tesis-bibliografia-anexos` — Bibliografía y los 10 Anexos

---

## 📁 Estructura de la Web

```
docs/
├── index.html              # Portada, catálogo, sección de informes y lector
├── styles.css              # Sistema de diseño, temas claro/oscuro y estilos Markdown
├── script.js               # Tema, catálogo, lector, TOC, scrollspy, búsqueda y enrutado
├── docs_data.js            # Corpus centralizado con los 21 documentos (generado)
├── manifest.json           # Metadatos de instalación como aplicación web
├── robots.txt              # Indexación
├── sitemap.xml             # Mapa del sitio
├── content/                # Copias Markdown de referencia del corpus
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
1. Lee los 21 archivos `.md` declarados en su manifiesto, en codificación UTF-8.
2. Extrae títulos, resúmenes, categorías y badges.
3. Calcula el conteo de palabras y minutos de lectura estimados.
4. Genera el bundle optimizado `docs/docs_data.js`.

Cada documento del catálogo se mantiene duplicado en `docs/content/` como copia de
referencia. El lector no consulta la red al abrir un documento: renderiza el texto
incluido en el bundle, de modo que la página funciona igual con `file://` y sin conexión.
Para comprobar que el catálogo y sus copias están íntegros y sincronizados:

```bash
python tools/verify_docs.py
```

---

## 🗂️ Informes Académicos

Los cuatro informes de `informes_academicos/` (contabilidad, socio crítico, proyecto y
redes de computadoras) no forman parte del bundle del lector: se enlazan a su Markdown en
el repositorio y aparecen tanto en la sección **Informes** de la portada como en el pie de
página. Su texto completo se consulta en GitHub o en el propio archivo del repositorio.

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
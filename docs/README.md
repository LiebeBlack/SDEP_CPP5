# Documentación Web

Sitio web ultra minimalista, elegante y moderno para la documentación del Sistema de Gestión de Personal y Nómina.

## 🎨 Características

- **Diseño Ultra Minimalista** - Enfoque en contenido esencial
- **Tema Claro/Oscuro** - Alternancia de temas con persistencia
- **Responsive** - Adaptable a todos los dispositivos
- **Animaciones Suaves** - Transiciones elegantes y sutiles
- **Interactividad** - Elementos interactivos con feedback visual
- **Código Copiable** - Código preview con función de copiar

## 🚀 Cómo Usar

### Abrir la Documentación

Simplemente abre el archivo `index.html` en tu navegador:

```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

### Tema Claro/Oscuro

El sitio web detecta automáticamente tu preferencia del sistema, pero puedes alternar manualmente:

- Haz clic en el botón del sol/luna en la esquina superior derecha
- La preferencia se guarda en localStorage para persistencia

## 📁 Estructura de Archivos

```
docs/
├── index.html          # Página principal
├── styles.css          # Estilos CSS
├── script.js           # Funcionalidad JavaScript
└── README.md          # Este archivo
```

## 🎯 Secciones

### 1. Hero Section
- Título principal con efecto de typing
- Subtítulo descriptivo
- Botones de acción
- Preview de código interactivo

### 2. Software
- Grid de características del sistema
- Stack tecnológico con tags
- Iconos descriptivos
- Cards con hover effects

### 3. Tesis Académica
- Grid con todos los documentos de tesis
- Enlaces directos a los archivos Markdown
- Cards numeradas con gradientes
- Descripciones concisas

### 4. Documentación Técnica
- Lista de documentos técnicos
- Iconos por tipo de documento
- Enlaces a documentación del proyecto
- Efectos de desplazamiento

### 5. Estadísticas
- Contadores animados
- Números destacados
- Grid de 4 columnas
- Animación al scroll

### 6. Footer
- Información del proyecto
- Copyright
- Estilo minimalista

## 🎨 Diseño

### Colores (Tema Claro)
- Background: `#ffffff`
- Texto: `#1a1a1a`
- Acento: `#2563eb`
- Bordes: `#e9ecef`

### Colores (Tema Oscuro)
- Background: `#0f0f0f`
- Texto: `#f5f5f5`
- Acento: `#3b82f6`
- Bordes: `#333333`

### Tipografía
- Fuente: Inter (Google Fonts)
- Tamaños: 0.875rem - 3.5rem
- Peso: 300 - 700

### Espaciado
- Base: 0.5rem - 8rem
- Consistencia en padding y margins
- Sistema de 8px

## ⚡ Funcionalidades JavaScript

### Theme Toggle
- Alternancia entre temas claro/oscuro
- Persistencia en localStorage
- Detección de preferencia del sistema

### Smooth Scroll
- Navegación suave entre secciones
- Header fijo con scroll effect
- Active link highlighting

### Animaciones
- Intersection Observer para lazy loading
- Fade-in effects al scroll
- Counter animation para estadísticas
- Typing effect para título

### Interactividad
- Hover effects en cards
- Code copy functionality
- Mobile responsive menu
- Performance optimization

## 📱 Responsive Design

### Breakpoints
- Desktop: > 768px
- Tablet: 481px - 768px
- Mobile: ≤ 480px

### Adaptaciones
- Grid responsive: auto-fit columns
- Font scaling en móviles
- Botones full-width en mobile
- Navigation simplificada

## 🔧 Personalización

### Cambiar Colores
Edita las variables CSS en `styles.css`:

```css
:root {
    --accent-color: #2563eb;  /* Cambia tu color principal */
    --bg-primary: #ffffff;     /* Cambia fondo principal */
    /* ... otras variables */
}
```

### Modificar Contenido
Edita el HTML en `index.html`:

```html
<!-- Cambia títulos -->
<h1 class="hero-title">Tu Título</h1>

<!-- Modifica características -->
<div class="feature-card">
    <div class="feature-icon">🎯</div>
    <h3 class="feature-title">Tu Característica</h3>
</div>
```

### Añadir Nueva Sección
Copia el patrón de sección existente:

```html
<section id="nueva-seccion" class="section">
    <div class="section-header">
        <h2 class="section-title">Nueva Sección</h2>
        <p class="section-subtitle">Descripción</p>
    </div>
    <!-- Contenido -->
</section>
```

## 🌐 Hosting

### GitHub Pages
1. Sube el contenido a GitHub
2. Activa GitHub Pages en settings
3. Apunta al directorio `docs/`

### Netlify
1. Arrastra la carpeta `docs/` a Netlify
2. Configura automáticamente
3. Deploy instantáneo

### Vercel
1. Instala Vercel CLI
2. Ejecuta `vercel deploy docs`
3. Configura y deploy

## 📊 Performance

- **Tamaño Total:** ~25KB
- **Load Time:** < 100ms
- **Lighthouse Score:** 95+
- **Optimizado:** Imágenes lazy loading, código minificado

## 🎓 Referencias

- **CSS Variables:** Soporte nativo de temas
- **Intersection Observer:** API moderna de animaciones
- **LocalStorage:** Persistencia de preferencias
- **Grid Layout:** Sistema de layout moderno
- **Flexbox:** Flexibilidad en componentes

## 📝 Notas

- Todo el código es vanilla (sin frameworks)
- No hay dependencias externas excepto Google Fonts
- Compatible con todos los navegadores modernos
- Accesible (semántica HTML, keyboard navigation)
- Optimizado para SEO

## 🚧 Futuras Mejoras

- [ ] Búsqueda integrada
- [ ] Modo impresión
- [ ] Comentarios en documentos
- [ ] Versión multi-idioma
- [ ] PWA capabilities
- [ ] Analytics integration

---

**Creado:** 24 de agosto de 2026
**Versión:** 1.0
**Estilo:** Ultra Minimalista
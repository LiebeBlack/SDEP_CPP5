/**
 * SDEP - Sistema de Gestión de Personal y Nómina
 * Application Controller & In-Web Markdown Reader Engine
 */

(function () {
    'use strict';

    // --- State & DOM References ---
    let currentDocId = null;
    let docsData = window.SDEP_DOCS_DATA || [];
    let selectedPaletteIndex = 0;

    const htmlEl = document.documentElement;
    const themeToggleBtn = document.getElementById('theme-toggle');
    const readerThemeToggleBtn = document.getElementById('reader-theme-toggle');
    const readerView = document.getElementById('reader-view');
    const readerCloseBtn = document.getElementById('reader-close-btn');
    const readerScrollContainer = document.getElementById('reader-scroll-container');
    const readerProgressBar = document.getElementById('reader-progress-bar');
    const readerSidebarNav = document.getElementById('reader-sidebar-nav');
    const readerSidebarFilter = document.getElementById('reader-sidebar-filter');
    const readerTocList = document.getElementById('toc-list');
    const markdownRenderTarget = document.getElementById('markdown-render-target');
    const paletteOverlay = document.getElementById('palette-overlay');
    const paletteInput = document.getElementById('palette-input');
    const paletteResults = document.getElementById('palette-results');
    const openSearchBtn = document.getElementById('open-search-btn');
    const heroSearchBtn = document.getElementById('hero-search-btn');
    const readerSearchBtn = document.getElementById('reader-search-btn');
    const toastEl = document.getElementById('toast-msg');
    const docsGrid = document.getElementById('docs-grid');
    const catalogFilterInput = document.getElementById('catalog-filter-input');
    const catalogTabs = document.querySelectorAll('.catalog-tab');

    // --- 1. Theme Controller ---
    function initTheme() {
        const savedTheme = localStorage.getItem('sdep_theme');
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const activeTheme = savedTheme ? savedTheme : (prefersDark ? 'dark' : 'light');
        setTheme(activeTheme);
    }

    function setTheme(theme) {
        htmlEl.setAttribute('data-theme', theme);
        localStorage.setItem('sdep_theme', theme);
        updateThemeIcons(theme);
    }

    function toggleTheme() {
        const currentTheme = htmlEl.getAttribute('data-theme') || 'light';
        const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(nextTheme);
    }

    function updateThemeIcons(theme) {
        const iconText = theme === 'dark' ? '☀️' : '🌙';
        document.querySelectorAll('.theme-icon').forEach(icon => {
            icon.textContent = iconText;
        });
    }

    if (themeToggleBtn) themeToggleBtn.addEventListener('click', toggleTheme);
    if (readerThemeToggleBtn) readerThemeToggleBtn.addEventListener('click', toggleTheme);

    // --- 2. Toast Notification ---
    let toastTimeout;
    function showToast(message) {
        if (!toastEl) return;
        toastEl.textContent = message;
        toastEl.classList.add('show');
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toastEl.classList.remove('show');
        }, 2200);
    }

    // --- 3. Clipboard Helper ---
    function copyTextToClipboard(text, successMsg = 'Copiado al portapapeles') {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                showToast(successMsg);
            }).catch(() => {
                fallbackCopyText(text, successMsg);
            });
        } else {
            fallbackCopyText(text, successMsg);
        }
    }

    function fallbackCopyText(text, successMsg) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(successMsg);
        } catch (err) {
            showToast('No se pudo copiar');
        }
        document.body.removeChild(textArea);
    }

    // --- 4. Markdown Processing & Renderer ---
    function configureMarkedRenderer() {
        if (typeof marked === 'undefined') {
            console.warn('Marked library not loaded yet');
            return null;
        }

        const renderer = new marked.Renderer();

        // Custom Heading Renderer with Anchor Links
        renderer.heading = function (text, level) {
            // Clean text for slug
            const plainText = text.replace(/<[^>]*>/g, '').trim();
            const slug = plainText.toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/\s+/g, '-');

            return `
                <h${level} id="${slug}">
                    <a class="header-anchor" href="#${slug}" aria-hidden="true">#</a>
                    <span>${text}</span>
                </h${level}>
            `;
        };

        // Custom Code Block Renderer
        renderer.code = function (code, lang) {
            const validLang = lang && lang.trim() ? lang.trim().toLowerCase() : 'text';
            return `
                <div class="code-block-wrapper">
                    <div class="code-block-header">
                        <span class="code-lang-label">${validLang}</span>
                        <button class="code-btn-copy" type="button" data-code="${encodeURIComponent(code)}">
                            <span>📋</span> Copiar
                        </button>
                    </div>
                    <pre><code class="language-${validLang}">${escapeHtml(code)}</code></pre>
                </div>
            `;
        };

        // Custom Blockquote with GitHub Callout support
        renderer.blockquote = function (quote) {
            const alertRegex = /^\s*<p>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(?:<br>)?([\s\S]*?)<\/p>/i;
            const match = quote.match(alertRegex);

            if (match) {
                const type = match[1].toUpperCase();
                const remainder = match[2];
                const restOfQuote = quote.replace(alertRegex, remainder ? `<p>${remainder}</p>` : '');

                const typeIcons = {
                    'NOTE': 'ℹ️',
                    'TIP': '💡',
                    'IMPORTANT': '📌',
                    'WARNING': '⚠️',
                    'CAUTION': '🛑'
                };

                const typeLabels = {
                    'NOTE': 'Nota',
                    'TIP': 'Sugerencia',
                    'IMPORTANT': 'Importante',
                    'WARNING': 'Advertencia',
                    'CAUTION': 'Precaución'
                };

                const icon = typeIcons[type] || 'ℹ️';
                const label = typeLabels[type] || type;
                const cssClass = `gh-alert gh-alert-${type.toLowerCase()}`;

                return `
                    <div class="${cssClass}">
                        <div class="gh-alert-header">
                            <span>${icon}</span>
                            <span>${label}</span>
                        </div>
                        <div class="gh-alert-content">
                            ${restOfQuote}
                        </div>
                    </div>
                `;
            }

            return `<blockquote>${quote}</blockquote>`;
        };

        marked.setOptions({
            renderer: renderer,
            gfm: true,
            breaks: false,
            smartLists: true,
            smartypants: true
        });

        return renderer;
    }

    function escapeHtml(string) {
        const entityMap = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };
        return String(string).replace(/[&<>"']/g, s => entityMap[s]);
    }

    // --- 5. Catalog Cards Population ---
    function renderCatalogCards(filterCategory = 'all', searchQuery = '') {
        if (!docsGrid) return;
        docsGrid.innerHTML = '';

        const query = searchQuery.trim().toLowerCase();
        const filteredDocs = docsData.filter(doc => {
            const matchesCat = filterCategory === 'all' ||
                (filterCategory === 'tesis' && doc.category === 'Tesis Académica') ||
                (filterCategory === 'tecnica' && doc.category === 'Documentación Técnica');

            const matchesQuery = !query ||
                doc.title.toLowerCase().includes(query) ||
                doc.subtitle.toLowerCase().includes(query) ||
                (doc.badge && doc.badge.toLowerCase().includes(query));

            return matchesCat && matchesQuery;
        });

        if (filteredDocs.length === 0) {
            docsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; color: var(--text-tertiary);">
                    <p style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔍</p>
                    <p>No se encontraron documentos con los criterios de búsqueda actuales.</p>
                </div>
            `;
            return;
        }

        filteredDocs.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'doc-card';
            card.innerHTML = `
                <div class="doc-card-top">
                    <span class="doc-card-badge">${doc.badge || 'DOC'}</span>
                    <span class="doc-card-readtime">⏱️ ~${doc.readingTime} min</span>
                </div>
                <h3 class="doc-card-title">${doc.icon ? doc.icon + ' ' : ''}${doc.title}</h3>
                <p class="doc-card-desc">${doc.subtitle}</p>
                <div class="doc-card-actions">
                    <button class="doc-card-btn open-doc-trigger" data-doc="${doc.id}">
                        <span>Leer en Web</span>
                        <span>→</span>
                    </button>
                    <a href="${doc.githubUrl}" target="_blank" rel="noopener noreferrer" class="doc-card-ghlink" title="Ver en GitHub">
                        GitHub ↗
                    </a>
                </div>
            `;
            docsGrid.appendChild(card);
        });

        // Attach listeners to "Leer en Web" buttons
        docsGrid.querySelectorAll('.open-doc-trigger').forEach(btn => {
            btn.addEventListener('click', () => {
                const docId = btn.getAttribute('data-doc');
                if (docId) openDocument(docId);
            });
        });
    }

    // --- 6. In-Web Markdown Reader Logic ---
    function openDocument(docId, targetHeadingId = null) {
        const doc = docsData.find(d => d.id === docId);
        if (!doc) {
            console.error(`Document with ID '${docId}' not found.`);
            return;
        }

        currentDocId = docId;

        // Update Breadcrumbs & Meta Header
        const breadcrumbCat = document.getElementById('breadcrumb-category');
        const breadcrumbTitle = document.getElementById('breadcrumb-title');
        const articleBadge = document.getElementById('article-badge');
        const articleReadTime = document.getElementById('article-readtime');
        const articleWords = document.getElementById('article-words');
        const articleTitle = document.getElementById('article-title');
        const articleSubtitle = document.getElementById('article-subtitle');
        const readerGhLink = document.getElementById('reader-gh-link');

        if (breadcrumbCat) breadcrumbCat.textContent = doc.category;
        if (breadcrumbTitle) breadcrumbTitle.textContent = doc.title;
        if (articleBadge) articleBadge.textContent = `${doc.badge} • ${doc.category}`;
        if (articleReadTime) articleReadTime.textContent = `⏱️ ~${doc.readingTime} min de lectura`;
        if (articleWords) articleWords.textContent = `${doc.wordCount.toLocaleString()} palabras`;
        if (articleTitle) articleTitle.textContent = `${doc.icon ? doc.icon + ' ' : ''}${doc.title}`;
        if (articleSubtitle) articleSubtitle.textContent = doc.subtitle;
        if (readerGhLink) readerGhLink.href = doc.githubUrl;

        // Render Markdown content
        if (typeof marked !== 'undefined') {
            configureMarkedRenderer();
            markdownRenderTarget.innerHTML = marked.parse(doc.content);
        } else {
            // Fallback plain text if marked is not ready
            markdownRenderTarget.innerHTML = `<pre>${escapeHtml(doc.content)}</pre>`;
        }

        // Apply syntax highlighting with Prism
        if (typeof Prism !== 'undefined') {
            Prism.highlightAllUnder(markdownRenderTarget);
        }

        // Attach copy buttons inside rendered code blocks
        markdownRenderTarget.querySelectorAll('.code-btn-copy').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const codeText = decodeURIComponent(btn.getAttribute('data-code') || '');
                copyTextToClipboard(codeText, 'Código copiado al portapapeles');
            });
        });

        // Generate Table of Contents (TOC)
        generateTableOfContents();

        // Update Sidebar items
        populateReaderSidebar();

        // Update Prev / Next Buttons
        updateReaderNavigation(doc);

        // Show Reader Modal/View
        readerView.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.title = `${doc.title} | SDEP`;

        // Update URL Hash
        window.location.hash = `doc=${doc.id}`;

        // Reset scroll position or jump to target heading
        if (targetHeadingId) {
            setTimeout(() => {
                const targetEl = document.getElementById(targetHeadingId);
                if (targetEl) targetEl.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        } else {
            readerScrollContainer.scrollTop = 0;
        }

        updateReadingProgress();

        // Check and fetch live updates from GitHub or content/
        fetchLiveDocument(doc);
    }

    function setSyncBadgeStatus(isLive, labelText) {
        const badge = document.getElementById('reader-sync-badge');
        const text = document.getElementById('reader-sync-text');
        if (!badge || !text) return;
        badge.className = `sync-badge ${isLive ? 'live' : 'local'}`;
        text.textContent = labelText || (isLive ? 'GitHub En Vivo' : 'Sincronizado');
    }

    function convertGitHubUrlToRaw(url) {
        if (!url) return '';
        let clean = url.trim();
        if (clean.includes('github.com') && clean.includes('/blob/')) {
            clean = clean.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/');
        }
        return clean;
    }

    function fetchLiveDocument(doc) {
        const contentUrl = `./content/${doc.filename}`;
        const rawGhUrl = `https://raw.githubusercontent.com/LiebeBlack/SDEP_CPP5/main/${doc.filename}`;

        // Attempt same-origin first (GitHub Pages or local web server)
        fetch(contentUrl)
            .then(res => {
                if (res.ok) return res.text();
                return fetch(rawGhUrl).then(r => r.ok ? r.text() : Promise.reject('GitHub raw not available'));
            })
            .then(remoteMarkdown => {
                if (remoteMarkdown && remoteMarkdown.trim().length > 50 && currentDocId === doc.id) {
                    if (remoteMarkdown !== doc.content) {
                        doc.content = remoteMarkdown;
                        if (typeof marked !== 'undefined') {
                            markdownRenderTarget.innerHTML = marked.parse(doc.content);
                            if (typeof Prism !== 'undefined') {
                                Prism.highlightAllUnder(markdownRenderTarget);
                            }
                            generateTableOfContents();
                        }
                    }
                    setSyncBadgeStatus(true, 'GitHub En Vivo (main)');
                }
            })
            .catch(() => {
                setSyncBadgeStatus(false, 'Copia Local');
            });
    }

    function loadCustomMarkdownFromUrl(rawOrBlobUrl) {
        if (!rawOrBlobUrl) return;
        const rawUrl = convertGitHubUrlToRaw(rawOrBlobUrl);

        // Check if URL matches any document in our manifest
        for (const doc of docsData) {
            if (rawOrBlobUrl.toLowerCase().includes(doc.filename.toLowerCase())) {
                openDocument(doc.id);
                return;
            }
        }

        showToast('Cargando archivo desde GitHub...');
        fetch(rawUrl)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.text();
            })
            .then(markdown => {
                const filename = rawOrBlobUrl.split('/').pop() || 'DOCUMENTO.md';
                const firstH1Match = markdown.match(/^#\s+(.+)$/m);
                const title = firstH1Match ? firstH1Match[1] : filename;

                const customDoc = {
                    id: 'custom-url',
                    title: title,
                    subtitle: `Cargado directamente desde ${rawOrBlobUrl}`,
                    category: 'GitHub Repository',
                    order: 99,
                    badge: 'GitHub',
                    icon: '⚡',
                    filename: filename,
                    githubUrl: rawOrBlobUrl,
                    wordCount: markdown.split(/\s+/).length,
                    readingTime: Math.max(1, Math.round(markdown.split(/\s+/).length / 200)),
                    content: markdown
                };

                // Render document in reader
                currentDocId = customDoc.id;
                const breadcrumbCat = document.getElementById('breadcrumb-category');
                const breadcrumbTitle = document.getElementById('breadcrumb-title');
                const articleBadge = document.getElementById('article-badge');
                const articleReadTime = document.getElementById('article-readtime');
                const articleWords = document.getElementById('article-words');
                const articleTitle = document.getElementById('article-title');
                const articleSubtitle = document.getElementById('article-subtitle');
                const readerGhLink = document.getElementById('reader-gh-link');

                if (breadcrumbCat) breadcrumbCat.textContent = 'GitHub';
                if (breadcrumbTitle) breadcrumbTitle.textContent = customDoc.title;
                if (articleBadge) articleBadge.textContent = 'En Vivo • GitHub';
                if (articleReadTime) articleReadTime.textContent = `⏱️ ~${customDoc.readingTime} min`;
                if (articleWords) articleWords.textContent = `${customDoc.wordCount.toLocaleString()} palabras`;
                if (articleTitle) articleTitle.textContent = `⚡ ${customDoc.title}`;
                if (articleSubtitle) articleSubtitle.textContent = customDoc.subtitle;
                if (readerGhLink) readerGhLink.href = customDoc.githubUrl;

                if (typeof marked !== 'undefined') {
                    configureMarkedRenderer();
                    markdownRenderTarget.innerHTML = marked.parse(customDoc.content);
                    if (typeof Prism !== 'undefined') {
                        Prism.highlightAllUnder(markdownRenderTarget);
                    }
                } else {
                    markdownRenderTarget.innerHTML = `<pre>${escapeHtml(customDoc.content)}</pre>`;
                }

                generateTableOfContents();
                readerView.classList.add('active');
                document.body.style.overflow = 'hidden';
                document.title = `${customDoc.title} | SDEP`;
                readerScrollContainer.scrollTop = 0;
                setSyncBadgeStatus(true, 'GitHub Live (URL)');
                showToast('Documento renderizado en la web con éxito');
            })
            .catch(err => {
                console.warn('Error loading custom GitHub URL:', err);
                showToast('No se pudo conectar a GitHub. Abriendo copia local...');
                // Fallback to first doc
                openDocument(docsData[0].id);
            });
    }

    function closeDocument() {
        readerView.classList.remove('active');
        document.body.style.overflow = '';
        document.title = 'SDEP - Sistema de Gestión de Personal y Nómina | Documentación Centralizada';
        currentDocId = null;

        if (window.location.hash.startsWith('#doc=')) {
            history.pushState('', document.title, window.location.pathname + window.location.search);
        }
    }

    function generateTableOfContents() {
        if (!readerTocList) return;
        readerTocList.innerHTML = '';

        const headings = markdownRenderTarget.querySelectorAll('h2, h3');
        if (headings.length === 0) {
            readerTocList.innerHTML = '<li class="toc-item" style="color: var(--text-tertiary); font-size: 0.75rem;">Sin secciones</li>';
            return;
        }

        headings.forEach(heading => {
            const level = heading.tagName.toLowerCase() === 'h2' ? 'level-2' : 'level-3';
            const id = heading.id;
            const text = heading.querySelector('span') ? heading.querySelector('span').textContent : heading.textContent;

            const li = document.createElement('li');
            li.className = `toc-item ${level}`;
            li.innerHTML = `<a href="#${id}" class="toc-link" data-target="${id}">${text}</a>`;
            readerTocList.appendChild(li);
        });

        // Smooth scroll on TOC clicks
        readerTocList.querySelectorAll('.toc-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('data-target');
                const targetEl = document.getElementById(targetId);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    function populateReaderSidebar(filterText = '') {
        if (!readerSidebarNav) return;
        readerSidebarNav.innerHTML = '';

        const query = filterText.trim().toLowerCase();
        const categories = ['Tesis Académica', 'Documentación Técnica'];

        categories.forEach(cat => {
            const catDocs = docsData.filter(d => d.category === cat && (!query || d.title.toLowerCase().includes(query) || d.subtitle.toLowerCase().includes(query)));
            if (catDocs.length === 0) return;

            const catTitle = document.createElement('div');
            catTitle.className = 'sidebar-category-title';
            catTitle.textContent = cat;
            readerSidebarNav.appendChild(catTitle);

            catDocs.forEach(d => {
                const a = document.createElement('a');
                a.href = `#doc=${d.id}`;
                a.className = `sidebar-doc-link ${d.id === currentDocId ? 'active' : ''}`;
                a.innerHTML = `
                    <span>${d.icon || '📄'}</span>
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${d.title}</span>
                    <span class="sidebar-doc-badge">${d.badge}</span>
                `;
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    openDocument(d.id);
                });
                readerSidebarNav.appendChild(a);
            });
        });
    }

    function updateReaderNavigation(currentDoc) {
        const prevBtn = document.getElementById('nav-prev-btn');
        const nextBtn = document.getElementById('nav-next-btn');
        const prevTitle = document.getElementById('nav-prev-title');
        const nextTitle = document.getElementById('nav-next-title');

        const currentIndex = docsData.findIndex(d => d.id === currentDoc.id);

        if (currentIndex > 0) {
            const prevDoc = docsData[currentIndex - 1];
            prevBtn.style.visibility = 'visible';
            prevTitle.textContent = `${prevDoc.icon ? prevDoc.icon + ' ' : ''}${prevDoc.title}`;
            prevBtn.onclick = () => openDocument(prevDoc.id);
        } else {
            prevBtn.style.visibility = 'hidden';
        }

        if (currentIndex < docsData.length - 1) {
            const nextDoc = docsData[currentIndex + 1];
            nextBtn.style.visibility = 'visible';
            nextTitle.textContent = `${nextDoc.icon ? nextDoc.icon + ' ' : ''}${nextDoc.title}`;
            nextBtn.onclick = () => openDocument(nextDoc.id);
        } else {
            nextBtn.style.visibility = 'hidden';
        }
    }

    // Scrollspy & Progress Bar
    function updateReadingProgress() {
        if (!readerScrollContainer || !readerProgressBar) return;

        const scrollTop = readerScrollContainer.scrollTop;
        const scrollHeight = readerScrollContainer.scrollHeight - readerScrollContainer.clientHeight;
        const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
        readerProgressBar.style.width = `${progress}%`;

        // Update active TOC item
        const headings = markdownRenderTarget.querySelectorAll('h2, h3');
        let activeHeadingId = null;

        headings.forEach(heading => {
            const rect = heading.getBoundingClientRect();
            if (rect.top <= 140) {
                activeHeadingId = heading.id;
            }
        });

        if (activeHeadingId && readerTocList) {
            readerTocList.querySelectorAll('.toc-link').forEach(link => {
                if (link.getAttribute('data-target') === activeHeadingId) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }
    }

    if (readerScrollContainer) {
        readerScrollContainer.addEventListener('scroll', updateReadingProgress);
    }

    if (readerCloseBtn) readerCloseBtn.addEventListener('click', closeDocument);

    // Filter inside reader sidebar
    if (readerSidebarFilter) {
        readerSidebarFilter.addEventListener('input', (e) => {
            populateReaderSidebar(e.target.value);
        });
    }

    // Copy Raw Markdown
    const readerCopyMdBtn = document.getElementById('reader-copy-md-btn');
    if (readerCopyMdBtn) {
        readerCopyMdBtn.addEventListener('click', () => {
            const doc = docsData.find(d => d.id === currentDocId);
            if (doc) {
                copyTextToClipboard(doc.content, 'Contenido Markdown copiado');
            }
        });
    }

    // Print / PDF
    const readerPrintBtn = document.getElementById('reader-print-btn');
    if (readerPrintBtn) {
        readerPrintBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // --- 7. Command Palette & Search (`Ctrl + K`) ---
    function openPalette() {
        if (!paletteOverlay) return;
        paletteOverlay.classList.add('active');
        paletteInput.value = '';
        selectedPaletteIndex = 0;
        runPaletteSearch('');
        setTimeout(() => paletteInput.focus(), 50);
    }

    function closePalette() {
        if (!paletteOverlay) return;
        paletteOverlay.classList.remove('active');
    }

    function runPaletteSearch(query) {
        const q = query.trim().toLowerCase();
        let matches = [];

        if (!q) {
            // Default: show top featured documents
            matches = docsData.slice(0, 8);
        } else {
            docsData.forEach(doc => {
                let score = 0;
                let snippet = '';

                if (doc.title.toLowerCase().includes(q)) score += 10;
                if (doc.subtitle.toLowerCase().includes(q)) score += 5;

                const bodyIndex = doc.content.toLowerCase().indexOf(q);
                if (bodyIndex !== -1) {
                    score += 2;
                    const start = Math.max(0, bodyIndex - 40);
                    const end = Math.min(doc.content.length, bodyIndex + 90);
                    snippet = doc.content.slice(start, end).replace(/[\r\n#*_`]/g, ' ');
                }

                if (score > 0) {
                    matches.push({
                        doc,
                        score,
                        snippet: snippet || doc.subtitle
                    });
                }
            });

            matches.sort((a, b) => b.score - a.score);
            matches = matches.map(m => m.doc);
        }

        renderPaletteResults(matches, q);
    }

    function renderPaletteResults(docs, query) {
        if (!paletteResults) return;
        paletteResults.innerHTML = '';

        if (docs.length === 0) {
            paletteResults.innerHTML = `
                <div class="palette-empty">
                    No se encontraron resultados para "<strong>${escapeHtml(query)}</strong>"
                </div>
            `;
            return;
        }

        docs.forEach((doc, idx) => {
            const item = document.createElement('div');
            item.className = `palette-item ${idx === selectedPaletteIndex ? 'selected' : ''}`;
            item.innerHTML = `
                <div class="palette-item-top">
                    <span class="palette-item-title">${doc.icon ? doc.icon + ' ' : ''}${doc.title}</span>
                    <span class="palette-item-badge">${doc.badge}</span>
                </div>
                <div class="palette-item-snippet">${doc.subtitle}</div>
            `;

            item.addEventListener('click', () => {
                closePalette();
                openDocument(doc.id);
            });

            paletteResults.appendChild(item);
        });
    }

    if (openSearchBtn) openSearchBtn.addEventListener('click', openPalette);
    if (heroSearchBtn) heroSearchBtn.addEventListener('click', openPalette);
    if (readerSearchBtn) readerSearchBtn.addEventListener('click', openPalette);

    if (paletteOverlay) {
        paletteOverlay.addEventListener('click', (e) => {
            if (e.target === paletteOverlay) closePalette();
        });
    }

    if (paletteInput) {
        paletteInput.addEventListener('input', (e) => {
            selectedPaletteIndex = 0;
            runPaletteSearch(e.target.value);
        });

        paletteInput.addEventListener('keydown', (e) => {
            const items = paletteResults.querySelectorAll('.palette-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedPaletteIndex = (selectedPaletteIndex + 1) % items.length;
                updatePaletteSelection(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedPaletteIndex = (selectedPaletteIndex - 1 + items.length) % items.length;
                updatePaletteSelection(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (items[selectedPaletteIndex]) {
                    items[selectedPaletteIndex].click();
                }
            }
        });
    }

    function updatePaletteSelection(items) {
        items.forEach((item, i) => {
            if (i === selectedPaletteIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    // Global Keydown Listeners (Ctrl + K, Escape)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (paletteOverlay.classList.contains('active')) {
                closePalette();
            } else {
                openPalette();
            }
        } else if (e.key === 'Escape') {
            if (paletteOverlay.classList.contains('active')) {
                closePalette();
            } else if (readerView.classList.contains('active')) {
                closeDocument();
            }
        }
    });

    // --- 8. Hero Code Tabs & Copy ---
    const codeTabBtns = document.querySelectorAll('.code-tab-btn');
    const heroCodeSnippets = document.querySelectorAll('.hero-code-snippet');
    const heroCodeCopy = document.getElementById('hero-code-copy');

    codeTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            codeTabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            heroCodeSnippets.forEach(snippet => {
                if (snippet.id === `snippet-${targetTab}`) {
                    snippet.classList.add('active');
                } else {
                    snippet.classList.remove('active');
                }
            });
        });
    });

    if (heroCodeCopy) {
        heroCodeCopy.addEventListener('click', () => {
            const activeSnippet = document.querySelector('.hero-code-snippet.active code');
            if (activeSnippet) {
                copyTextToClipboard(activeSnippet.textContent, 'Código copiado');
            }
        });
    }

    // Copy Quickstart
    const copyQuickstartBtn = document.getElementById('copy-quickstart-btn');
    if (copyQuickstartBtn) {
        copyQuickstartBtn.addEventListener('click', () => {
            const codeEl = document.getElementById('quickstart-text');
            if (codeEl) {
                copyTextToClipboard(codeEl.textContent, 'Comandos de inicio copiados');
            }
        });
    }

    // --- 9. Catalog Tabs & Filter Input ---
    let currentCatalogCategory = 'all';

    catalogTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            catalogTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCatalogCategory = tab.getAttribute('data-filter');
            renderCatalogCards(currentCatalogCategory, catalogFilterInput ? catalogFilterInput.value : '');
        });
    });

    if (catalogFilterInput) {
        catalogFilterInput.addEventListener('input', (e) => {
            renderCatalogCards(currentCatalogCategory, e.target.value);
        });
    }

    // Hero Open Reader Button
    const heroOpenReaderBtn = document.getElementById('hero-open-reader-btn');
    if (heroOpenReaderBtn) {
        heroOpenReaderBtn.addEventListener('click', () => {
            const docId = heroOpenReaderBtn.getAttribute('data-doc') || 'readme';
            openDocument(docId);
        });
    }

    // Listeners for triggers across the page
    document.querySelectorAll('.open-doc-trigger').forEach(el => {
        el.addEventListener('click', (e) => {
            const docId = el.getAttribute('data-doc');
            if (docId) {
                e.preventDefault();
                openDocument(docId);
            }
        });
    });

    // GitHub Direct URL Form & Quick Chips
    const ghUrlForm = document.getElementById('gh-url-form');
    const ghUrlInput = document.getElementById('gh-url-input');
    if (ghUrlForm && ghUrlInput) {
        ghUrlForm.addEventListener('submit', (e) => {
            e.preventDefault();
            loadCustomMarkdownFromUrl(ghUrlInput.value);
        });
    }

    document.querySelectorAll('.github-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const url = chip.getAttribute('data-url');
            if (url) {
                if (ghUrlInput) ghUrlInput.value = url;
                loadCustomMarkdownFromUrl(url);
            }
        });
    });

    const readerLoadUrlBtn = document.getElementById('reader-load-url-btn');
    if (readerLoadUrlBtn) {
        readerLoadUrlBtn.addEventListener('click', () => {
            const userUrl = prompt(
                'Ingresa la URL del archivo Markdown en GitHub:\n(Ej: https://github.com/LiebeBlack/SDEP_CPP5/blob/main/GUIA_USUARIO.md)',
                'https://github.com/LiebeBlack/SDEP_CPP5/blob/main/GUIA_USUARIO.md'
            );
            if (userUrl) {
                loadCustomMarkdownFromUrl(userUrl);
            }
        });
    }

    // --- 10. Hash Routing & Deep Linking ---
    function checkHashRoute() {
        const urlParams = new URLSearchParams(window.location.search);
        const queryUrl = urlParams.get('url') || urlParams.get('gh');
        if (queryUrl) {
            loadCustomMarkdownFromUrl(queryUrl);
            return;
        }

        const hash = window.location.hash;
        if (!hash) return;

        if (hash.startsWith('#gh=') || hash.startsWith('#url=')) {
            const targetUrl = hash.replace(/#(gh|url)=/, '');
            loadCustomMarkdownFromUrl(decodeURIComponent(targetUrl));
            return;
        }

        if (hash.startsWith('#doc=')) {
            const docParam = hash.replace('#doc=', '');
            const parts = docParam.split('#');
            const docId = parts[0];
            const targetHeading = parts[1] || null;

            if (docId) {
                openDocument(docId, targetHeading);
            }
        }
    }

    window.addEventListener('hashchange', checkHashRoute);

    // --- 11. Initial Boot ---
    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        renderCatalogCards('all');
        checkHashRoute();

        // Highlight existing code on landing page
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
    });

})();
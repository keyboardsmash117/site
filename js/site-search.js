/* Scythe — site-wide page search */
(function () {
    'use strict';

    const INDEX_URL = 'search-index.json';
    const MAX_RESULTS = 8;

    const wrapper = document.querySelector('.navbar-search');
    if (!wrapper) return;

    const input = wrapper.querySelector('input');
    const resultsEl = wrapper.querySelector('.search-results');
    if (!input || !resultsEl) return;

    let index = null;
    let indexPromise = null;
    let activeIndex = -1;
    let currentHits = [];

    function loadIndex() {
        if (index) return Promise.resolve(index);
        if (indexPromise) return indexPromise;
        indexPromise = fetch(INDEX_URL, { cache: 'default' })
            .then((r) => (r.ok ? r.json() : []))
            .then((data) => {
                index = Array.isArray(data) ? data : [];
                return index;
            })
            .catch(() => {
                index = [];
                return index;
            });
        return indexPromise;
    }

    function tokenize(q) {
        return q
            .toLowerCase()
            .split(/[^a-z0-9']+/)
            .filter((t) => t.length >= 2);
    }

    function scoreEntry(entry, tokens) {
        const title = (entry.title || '').toLowerCase();
        const subtitle = (entry.subtitle || '').toLowerCase();
        const headings = (entry.headings || []).map((h) => h.toLowerCase());
        const content = (entry.content || '').toLowerCase();

        let score = 0;
        let matchedHeading = null;

        for (const tok of tokens) {
            if (title === tok) score += 100;
            if (title.startsWith(tok)) score += 40;
            if (title.includes(tok)) score += 25;
            if (subtitle.includes(tok)) score += 10;

            for (const h of headings) {
                if (h.includes(tok)) {
                    score += 12;
                    if (!matchedHeading) matchedHeading = h;
                }
            }

            if (content.includes(tok)) score += 4;
        }

        return { score, matchedHeading };
    }

    function search(query) {
        const tokens = tokenize(query);
        if (tokens.length === 0) return [];

        const hits = [];
        for (const entry of index) {
            const { score, matchedHeading } = scoreEntry(entry, tokens);
            if (score > 0) {
                hits.push({ entry, score, matchedHeading, tokens });
            }
        }
        hits.sort((a, b) => b.score - a.score);
        return hits.slice(0, MAX_RESULTS);
    }

    function highlight(text, tokens) {
        if (!text) return '';
        let safe = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        for (const tok of tokens) {
            if (!tok) continue;
            const re = new RegExp('(' + tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
            safe = safe.replace(re, '<mark>$1</mark>');
        }
        return safe;
    }

    function excerptAround(content, tokens) {
        if (!content) return '';
        const lower = content.toLowerCase();
        let pos = -1;
        for (const tok of tokens) {
            const p = lower.indexOf(tok);
            if (p !== -1 && (pos === -1 || p < pos)) pos = p;
        }
        if (pos === -1) return content.slice(0, 160);
        const start = Math.max(0, pos - 60);
        const end = Math.min(content.length, pos + 140);
        let snippet = content.slice(start, end);
        if (start > 0) snippet = '… ' + snippet;
        if (end < content.length) snippet = snippet + ' …';
        return snippet;
    }

    function render(hits) {
        currentHits = hits;
        activeIndex = -1;

        if (!hits.length) {
            resultsEl.innerHTML = '<div class="search-empty">No matches</div>';
            resultsEl.classList.add('open');
            wrapper.classList.add('has-results');
            return;
        }

        const parts = hits.map((h, i) => {
            const title = highlight(h.entry.title || h.entry.url, h.tokens);
            const matchLine = h.matchedHeading
                ? '<div class="search-result-match">' + highlight(h.matchedHeading, h.tokens) + '</div>'
                : '';
            const excerpt = highlight(excerptAround(h.entry.content || h.entry.subtitle || '', h.tokens), h.tokens);
            return (
                '<a class="search-result" href="' + h.entry.url + '" data-idx="' + i + '">' +
                '<div class="search-result-title">' + title + '</div>' +
                matchLine +
                '<div class="search-result-excerpt">' + excerpt + '</div>' +
                '</a>'
            );
        });

        resultsEl.innerHTML = parts.join('');
        resultsEl.classList.add('open');
        wrapper.classList.add('has-results');
    }

    function close() {
        resultsEl.classList.remove('open');
        wrapper.classList.remove('has-results');
        activeIndex = -1;
    }

    function setActive(i) {
        const items = resultsEl.querySelectorAll('.search-result');
        if (!items.length) return;
        activeIndex = ((i % items.length) + items.length) % items.length;
        items.forEach((el, idx) => {
            el.classList.toggle('active', idx === activeIndex);
            if (idx === activeIndex) el.scrollIntoView({ block: 'nearest' });
        });
    }

    let debounceTimer = null;
    function onInput() {
        const q = input.value.trim();
        clearTimeout(debounceTimer);
        if (!q) {
            close();
            resultsEl.innerHTML = '';
            return;
        }
        debounceTimer = setTimeout(() => {
            loadIndex().then(() => {
                render(search(q));
            });
        }, 80);
    }

    function onKey(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!resultsEl.classList.contains('open')) return;
            setActive(activeIndex + 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (!resultsEl.classList.contains('open')) return;
            setActive(activeIndex - 1);
        } else if (e.key === 'Enter') {
            const items = resultsEl.querySelectorAll('.search-result');
            if (activeIndex >= 0 && items[activeIndex]) {
                e.preventDefault();
                window.location.href = items[activeIndex].getAttribute('href');
            } else if (currentHits.length > 0) {
                e.preventDefault();
                window.location.href = currentHits[0].entry.url;
            }
        } else if (e.key === 'Escape') {
            close();
            input.blur();
        }
    }

    input.addEventListener('input', onInput);
    input.addEventListener('keydown', onKey);
    input.addEventListener('focus', () => {
        loadIndex();
        if (input.value.trim()) onInput();
    });

    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) close();
    });

    // Global keyboard shortcut: "/" focuses the search box
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== input && !e.ctrlKey && !e.metaKey) {
            const tag = (document.activeElement && document.activeElement.tagName) || '';
            if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
                e.preventDefault();
                input.focus();
                input.select();
            }
        }
    });
})();

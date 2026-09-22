const elements = {
    total: document.querySelector('#total'),
    critical: document.querySelector('#critical'),
    warning: document.querySelector('#warning'),
    info: document.querySelector('#info'),
    events: document.querySelector('#events'),
    themeToggle: document.querySelector('#theme-toggle'),
};

const savedTheme = localStorage.getItem('sentineldesk-theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
setTheme(savedTheme || (prefersDark ? 'dark' : 'light'));

async function request(path, options = {}) {
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

function renderMetrics(metrics) {
    for (const key of ['total', 'critical', 'warning', 'info']) elements[key].textContent = metrics[key];
}

function renderEvents(events) {
    if (!events.length) {
        elements.events.innerHTML = '<p class="empty">Aucun evenement. Lance la demonstration pour commencer.</p>';
        return;
    }
    elements.events.innerHTML = events.map((event, index) => `
        <article class="event">
            <i class="event-dot ${event.severity}"></i>
            <div><p class="event-message">${escapeHtml(event.message)}</p><p class="event-meta">${escapeHtml(event.source)} · ${formatDate(event.created_at)}</p></div>
            <span class="badge ${event.severity}">${event.severity}</span>
        </article>
    `).join('');
    elements.events.querySelectorAll('.event').forEach((eventElement, index) => {
        eventElement.style.animationDelay = `${Math.min(index * 55, 330)}ms`;
    });
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character]));
}

function formatDate(value) {
    return new Date(value).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });
}

function setTheme(theme) {
    const isDark = theme === 'dark';
    document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
    elements.themeToggle?.setAttribute('aria-pressed', String(isDark));
    elements.themeToggle?.setAttribute('aria-label', isDark ? 'Activer le mode jour' : 'Activer le mode nuit');
}

async function refresh() {
    const [metrics, eventPayload] = await Promise.all([request('/api/metrics'), request('/api/events?limit=20')]);
    renderMetrics(metrics);
    renderEvents(eventPayload.events);
}

document.querySelector('#refresh-button').addEventListener('click', refresh);
elements.themeToggle.addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('sentineldesk-theme', nextTheme);
});
document.querySelector('#demo-button').addEventListener('click', async (event) => {
    event.target.disabled = true;
    event.target.textContent = 'Analyse en cours...';
    try { await request('/api/demo', { method: 'POST' }); await refresh(); }
    finally { event.target.disabled = false; event.target.textContent = 'Generer une demonstration'; }
});

refresh().catch(() => { elements.events.innerHTML = '<p class="empty">API indisponible. Lance api.py puis recharge la page.</p>'; });

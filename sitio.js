const API_BASE_URL = window.PELICATOS_API_URL || 'http://127.0.0.1:8000';
const userId = new URLSearchParams(window.location.search).get('usuario');

function escapeHtml(value) {
    return String(value || '').replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[character]);
}

async function loadPublicSite() {
    if (!userId) throw new Error('Falta el usuario');
    const response = await fetch(`${API_BASE_URL}/public/site/${encodeURIComponent(userId)}`);
    if (!response.ok) throw new Error('Sitio no encontrado');
    const site = await response.json();
    document.title = `${site.nombre_mostrar} | Pelicatos TV`;
    document.querySelector('#public-brand').textContent = site.nombre_mostrar;
    document.querySelector('#public-eyebrow').textContent = site.hero_eyebrow || 'Mi sitio personal';
    document.querySelector('#public-title').textContent = site.nombre_mostrar;
    document.querySelector('#public-title').textContent = site.hero_titulo || site.nombre_mostrar;
    document.querySelector('#public-description').textContent = site.hero_descripcion || site.descripcion || 'Historias, fotos y experiencias compartidas.';
    if (site.logo) {
        document.querySelector('#public-logo').src = `${API_BASE_URL}${site.logo}`;
        document.querySelector('#public-nav-logo').src = `${API_BASE_URL}${site.logo}`;
        document.querySelector('#public-footer-logo').src = `${API_BASE_URL}${site.logo}`;
    }
    if (site.fondo_url) document.querySelector('.public-hero').style.backgroundImage = `linear-gradient(135deg, rgba(10, 22, 37, .75), rgba(10, 22, 37, .35)), url("${API_BASE_URL}${site.fondo_url}")`;
    if (site.hero_image_url) document.querySelector('.public-hero').style.backgroundImage = `linear-gradient(135deg, rgba(10, 22, 37, .72), rgba(10, 22, 37, .35)), url("${API_BASE_URL}${site.hero_image_url}")`;
    document.querySelector('#public-adventures').innerHTML = site.aventuras.length ? site.aventuras.map((adventure) => `<article class="destination-card"><div class="image-wrap ${adventure.imagen_url ? '' : 'adventure-placeholder'}">${adventure.imagen_url ? `<img src="${API_BASE_URL}${adventure.imagen_url}" alt="${escapeHtml(adventure.titulo)}">` : ''}</div><div class="card-body"><span class="tag">${escapeHtml(adventure.ubicacion || 'Mi ruta')}</span><h3>${escapeHtml(adventure.titulo)}</h3><p>${escapeHtml(adventure.contenido)}</p></div></article>`).join('') : '<p class="empty-note">Todavía no hay aventuras publicadas.</p>';
    document.querySelector('#public-media').innerHTML = site.media.length ? site.media.map((item) => `<article class="social-post">${item.tipo === 'video' ? `<video controls src="${API_BASE_URL}${item.url}"></video>` : `<img src="${API_BASE_URL}${item.url}" alt="${escapeHtml(item.titulo)}">`}<div class="post-copy"><h3>${escapeHtml(item.titulo)}</h3><p>${escapeHtml(item.descripcion)}</p></div></article>`).join('') : '<p class="empty-note">Todavía no hay experiencias publicadas.</p>';
    document.querySelector('#public-photos').innerHTML = site.fotos.length ? site.fotos.map((photo) => `<img src="${API_BASE_URL}${photo.url}" alt="${escapeHtml(photo.nombre_archivo)}" loading="lazy">`).join('') : '<p class="empty-note">Todavía no hay fotos publicadas.</p>';
    document.querySelector('#public-footer-brand').textContent = site.nombre_mostrar;
    document.querySelector('#public-footer-description').textContent = site.footer_descripcion || site.descripcion || 'Viviendo viajes y compartiendo recuerdos.';
    document.querySelector('#public-copyright').textContent = site.copyright_texto || `© ${new Date().getFullYear()} ${site.nombre_mostrar}`;
    const socials = [['Facebook', site.facebook_url], ['Instagram', site.instagram_url], ['TikTok', site.tiktok_url], ['YouTube', site.youtube_url]].filter(([, url]) => url);
    document.querySelector('#public-socials').innerHTML = socials.map(([name, url]) => `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" aria-label="${name}">${name}</a>`).join('');
    document.querySelector('#public-site').hidden = false;
}

loadPublicSite().catch(() => { document.querySelector('#public-error').hidden = false; });

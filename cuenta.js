// Esta es la direccion base de FastAPI. Puede cambiarse desde el HTML antes de
// cargar este archivo definiendo window.PELICATOS_API_URL.
const API_BASE_URL = window.PELICATOS_API_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'pelicatos_access_token';

const authView = document.querySelector('#auth-view');
const dashboardView = document.querySelector('#dashboard-view');
const authMessage = document.querySelector('#auth-message');
const loginForm = document.querySelector('#login-form');
const registerForm = document.querySelector('#register-form');

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function showMessage(element, message, isError = true) {
    element.textContent = message;
    element.classList.toggle('is-error', isError);
    element.classList.toggle('is-success', !isError);
}

async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('Accept', 'application/json');
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    if (getToken()) headers.set('Authorization', `Bearer ${getToken()}`);

    // Todas las llamadas al backend pasan por aqui: agrega JSON y el token.
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    } catch (error) {
        throw new Error(`No se pudo conectar con el backend en ${API_BASE_URL}. Inicia FastAPI y vuelve a intentarlo.`);
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        if (response.status === 401) logout(false);
        throw new Error(data.detail || `Error ${response.status}`);
    }
    return data;
}

function setAuthTab(tab) {
    const isLogin = tab === 'login';
    document.querySelectorAll('[data-auth-tab]').forEach((button) => button.classList.toggle('active', button.dataset.authTab === tab));
    loginForm.hidden = !isLogin;
    registerForm.hidden = isLogin;
    document.querySelector('#auth-kicker').textContent = isLogin ? 'Tu espacio personal' : 'Empieza tu ruta';
    document.querySelector('#auth-title').textContent = isLogin ? 'Qué bueno verte.' : 'Crea tu cuenta.';
    document.querySelector('#auth-description').textContent = isLogin ? 'Ingresa para continuar con tus historias.' : 'Tus aventuras merecen un lugar propio.';
    authMessage.textContent = '';
}

document.querySelectorAll('[data-auth-tab]').forEach((button) => button.addEventListener('click', () => setAuthTab(button.dataset.authTab)));

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(loginForm));
    try {
        // FastAPI valida este JSON con LoginRequest y devuelve el token JWT.
        const data = await request('/auth/login', { method: 'POST', body: JSON.stringify(body) });
        localStorage.setItem(TOKEN_KEY, data.access_token);
        await showDashboard('¡Inicio de sesión exitoso! Bienvenido a tu espacio personal.');
    } catch (error) {
        showMessage(authMessage, error.message);
    }
});

registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(registerForm));
    try {
        await request('/auth/register', { method: 'POST', body: JSON.stringify(body) });
        setAuthTab('login');
        document.querySelector('#login-email').value = body.email;
        showMessage(authMessage, 'Cuenta creada. Ahora inicia sesión.', false);
    } catch (error) {
        showMessage(authMessage, error.message);
    }
});

async function showDashboard(successMessage = '') {
    authView.hidden = true;
    dashboardView.hidden = false;
    if (successMessage) showMessage(document.querySelector('#dashboard-message'), successMessage, false);
    try {
        await Promise.all([loadProfile(), loadSite(), loadCategories(), loadAdventures(), loadPhotos(), loadMedia()]);
    } catch (error) {
        showMessage(document.querySelector('#dashboard-message'), `La sesión inició, pero no se pudo cargar tu espacio: ${error.message}`);
    }
}

function logout(showAuth = true) {
    localStorage.removeItem(TOKEN_KEY);
    if (showAuth) {
        dashboardView.hidden = true;
        authView.hidden = false;
        setAuthTab('login');
        showMessage(authMessage, 'Has cerrado sesión correctamente.', false);
    }
}

document.querySelector('#logout-button')?.addEventListener('click', () => logout());

document.querySelector('#media-input').addEventListener('change', (event) => {
    const file = event.target.files[0];
    document.querySelector('#media-file-name').textContent = file ? file.name : 'Selecciona una imagen o video';
});

document.querySelector('#media-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    try {
        await request('/me/media', { method: 'POST', body: form });
        event.currentTarget.reset();
        document.querySelector('#media-file-name').textContent = 'Selecciona una imagen o video';
        showMessage(document.querySelector('#media-message'), 'Publicación agregada a tu perfil.', false);
        await loadMedia();
    } catch (error) {
        showMessage(document.querySelector('#media-message'), error.message);
    } finally {
        button.disabled = false;
    }
});

async function loadProfile() {
    const profile = await request('/me/profile');
    document.querySelector('#welcome-title').textContent = `Hola, ${profile.nombre}`;
    document.querySelector('#profile-name').textContent = profile.nombre;
    document.querySelector('#profile-email').textContent = profile.email;
    document.querySelector('#profile-name-input').value = profile.nombre;
    document.querySelector('#profile-bio-input').value = profile.biografia || '';
    document.querySelector('#profile-avatar').textContent = profile.nombre.charAt(0).toUpperCase();
}

async function loadSite() {
    const site = await request('/me/site');
    const form = document.querySelector('#site-settings-form');
    Object.entries(site).forEach(([field, value]) => {
        const input = form.elements.namedItem(field);
        if (input) input.value = value || '';
    });
    applySite(site);
}

function applySite(site) {
    document.querySelector('#welcome-title').textContent = site.hero_titulo || site.nombre_mostrar || 'Tus aventuras empiezan aqui.';
    document.querySelector('.account-hero .eyebrow').textContent = site.hero_eyebrow || 'Mi ruta personal';
    document.querySelector('#dashboard-message').textContent = site.hero_descripcion || site.descripcion || 'Escribe tus historias, comparte tus imagenes y guarda tus videos en un solo lugar.';
    const hero = document.querySelector('.account-hero');
    if (site.fondo_url) hero.style.backgroundImage = `linear-gradient(135deg, rgba(10, 22, 37, .75), rgba(10, 22, 37, .35)), url("${API_BASE_URL}${site.fondo_url}")`;
    const logo = document.querySelector('#site-logo-preview');
    if (logo && site.logo) logo.src = `${API_BASE_URL}${site.logo}`;
    const publicLink = document.querySelector('#public-site-link');
    if (publicLink && site.id_usuario) {
        publicLink.href = `sitio.html?usuario=${site.id_usuario}`;
        publicLink.hidden = false;
    }
}

document.querySelector('#site-settings-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        const site = await request('/me/site', { method: 'PUT', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
        applySite(site);
        showMessage(document.querySelector('#site-settings-message'), 'Presentación guardada.', false);
    } catch (error) {
        showMessage(document.querySelector('#site-settings-message'), error.message);
    }
});

async function uploadSiteAsset(formId, inputId, endpoint, nameId, successMessage) {
    const form = document.querySelector(formId);
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = document.querySelector(inputId).files[0];
        if (!file) return;
        try {
            const site = await request(endpoint, { method: 'POST', body: imageForm(file) });
            applySite(site);
            document.querySelector(nameId).textContent = successMessage;
        } catch (error) {
            showMessage(document.querySelector('#site-settings-message'), error.message);
        }
    });
}

uploadSiteAsset('#site-logo-form', '#site-logo-input', '/me/site/logo', '#site-logo-name', 'Logo guardado');
uploadSiteAsset('#site-background-form', '#site-background-input', '/me/site/background', '#site-background-name', 'Fondo guardado');
uploadSiteAsset('#site-hero-image-form', '#site-hero-image-input', '/me/site/hero-image', '#site-hero-image-name', 'Imagen principal guardada');

document.querySelector('#profile-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
        await request('/me/profile', { method: 'PUT', body: JSON.stringify(Object.fromEntries(form)) });
        await loadProfile();
        showMessage(document.querySelector('#adventure-message'), 'Perfil actualizado.', false);
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

async function loadCategories() {
    const categories = await request('/me/categories');
    const select = document.querySelector('#category-select');
    const list = document.querySelector('#category-list');
    select.innerHTML = '<option value="">Sin categoría</option>';
    list.innerHTML = '';
    categories.forEach((category) => {
        select.insertAdjacentHTML('beforeend', `<option value="${category.id_categoria}">${escapeHtml(category.nombre)}</option>`);
        list.insertAdjacentHTML('beforeend', `<span class="category-chip">${escapeHtml(category.nombre)}</span>`);
    });
    if (!categories.length) list.innerHTML = '<span class="empty-note">Crea tu primera categoría para ordenar tus historias.</span>';
}

document.querySelector('#category-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
        await request('/me/categories', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
        event.currentTarget.reset();
        await loadCategories();
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

document.querySelector('#adventure-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const adventure = Object.fromEntries(['titulo', 'ubicacion', 'contenido', 'id_categoria'].map((field) => [field, formData.get(field) || null]));
    if (adventure.id_categoria) adventure.id_categoria = Number(adventure.id_categoria);
    try {
        const created = await request('/me/adventures', { method: 'POST', body: JSON.stringify(adventure) });
        const image = formData.get('imagen');
        if (image && image.size) await request(`/me/adventures/${created.id_aventura}/image`, { method: 'POST', body: imageForm(image) });
        event.currentTarget.reset();
        await loadAdventures();
        showMessage(document.querySelector('#adventure-message'), 'Aventura publicada en tu diario.', false);
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

async function loadAdventures() {
    const adventures = await request('/me/adventures');
    const cardList = document.querySelector('#adventure-list');
    const archiveList = document.querySelector('#adventure-archive-list');
    const cards = adventures.map((adventure) => `<article class="destination-card account-adventure-card reveal"><div class="image-wrap ${adventure.imagen_url ? '' : 'adventure-placeholder'}">${adventure.imagen_url ? `<img src="${API_BASE_URL}${adventure.imagen_url}" alt="${escapeHtml(adventure.titulo)}" loading="lazy">` : `<span>${escapeHtml((adventure.ubicacion || 'Mi ruta').charAt(0).toUpperCase())}</span>`}</div><div class="card-body"><div class="meta-row"><span class="tag">${escapeHtml(adventure.ubicacion || 'Mi diario')}</span><span class="rating">Mi aventura</span></div><h3>${escapeHtml(adventure.titulo)}</h3><p>${escapeHtml(adventure.contenido)}</p><div class="card-actions"><button class="text-button" type="button" data-edit-adventure="${adventure.id_aventura}">Editar informacion</button><label class="text-button" for="adventure-image-${adventure.id_aventura}">Cambiar foto<input class="replace-adventure-image" id="adventure-image-${adventure.id_aventura}" data-adventure-id="${adventure.id_aventura}" type="file" accept="image/jpeg,image/png,image/webp,image/gif"></label></div></div></article>`).join('');
    cardList.innerHTML = cards || '<div class="empty-state"><p class="empty-note">Todavia no has escrito una aventura.</p><a class="btn btn-primary rounded-pill" href="#adventure-form">Agregar mi primera aventura</a></div>';
    archiveList.innerHTML = adventures.length ? adventures.map((adventure) => `<article class="adventure-item"><div><span class="item-location">${escapeHtml(adventure.ubicacion || 'Mi diario')}</span><h3>${escapeHtml(adventure.titulo)}</h3><p>${escapeHtml(adventure.contenido)}</p></div></article>`).join('') : '<p class="empty-note">Tu archivo aparecera aqui.</p>';
}

function imageForm(file) {
    const form = new FormData();
    form.append('file', file);
    return form;
}

document.querySelector('#adventure-list').addEventListener('change', async (event) => {
    if (!event.target.classList.contains('replace-adventure-image') || !event.target.files[0]) return;
    try {
        await request(`/me/adventures/${event.target.dataset.adventureId}/image`, { method: 'POST', body: imageForm(event.target.files[0]) });
        await loadAdventures();
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

document.querySelector('#adventure-list').addEventListener('click', async (event) => {
    const button = event.target.closest('[data-edit-adventure]');
    if (!button) return;
    const adventure = (await request('/me/adventures')).find((item) => item.id_aventura === Number(button.dataset.editAdventure));
    if (!adventure) return;
    const titulo = prompt('Titulo de la aventura', adventure.titulo);
    if (titulo === null) return;
    const contenido = prompt('Informacion de la aventura', adventure.contenido);
    if (contenido === null) return;
    try {
        await request(`/me/adventures/${adventure.id_aventura}`, { method: 'PUT', body: JSON.stringify({ titulo, contenido, ubicacion: adventure.ubicacion, id_categoria: adventure.id_categoria }) });
        await loadAdventures();
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

document.querySelector('#photo-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button');
    button.disabled = true;
    try {
        await request('/me/photos', { method: 'POST', body: new FormData(event.currentTarget) });
        event.currentTarget.reset();
        await loadPhotos();
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    } finally {
        button.disabled = false;
    }
});

async function loadPhotos() {
    const photos = await request('/me/photos');
    const grid = document.querySelector('#photo-grid');
    grid.innerHTML = photos.length ? photos.map((photo) => `<img src="${API_BASE_URL}${photo.url}" alt="${escapeHtml(photo.nombre_archivo)}" loading="lazy">`).join('') : '<div class="empty-state"><p class="empty-note">Todavía no tienes fotos.</p><a class="btn btn-dark rounded-pill" href="#photo-form">Agregar mi primera foto</a></div>';
}

async function loadMedia() {
    const media = await request('/me/media');
    const feed = document.querySelector('#media-feed');
    feed.innerHTML = media.length ? media.map((item) => {
        const source = `${API_BASE_URL}${item.url}`;
        const visual = item.tipo === 'video'
            ? `<video controls preload="metadata" src="${source}"></video>`
            : `<img src="${source}" alt="${escapeHtml(item.titulo)}" loading="lazy">`;
        return `<article class="social-post">${visual}<div class="post-copy"><span class="item-location">${item.tipo}</span><h3>${escapeHtml(item.titulo)}</h3><p>${escapeHtml(item.descripcion || '')}</p></div></article>`;
    }).join('') : '<div class="empty-state"><p class="empty-note">Todavía no tienes publicaciones.</p><a class="btn btn-primary rounded-pill" href="#media-form">Subir mi primera imagen o video</a></div>';
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[character]);
}

if (getToken()) showDashboard();

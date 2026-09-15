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

    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
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
        await Promise.all([loadProfile(), loadCategories(), loadAdventures(), loadPhotos(), loadMedia()]);
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

document.querySelector('#logout-button').addEventListener('click', () => logout());

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
    try {
        await request('/me/adventures', { method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
        event.currentTarget.reset();
        await loadAdventures();
        showMessage(document.querySelector('#adventure-message'), 'Aventura publicada en tu diario.', false);
    } catch (error) {
        showMessage(document.querySelector('#adventure-message'), error.message);
    }
});

async function loadAdventures() {
    const adventures = await request('/me/adventures');
    const list = document.querySelector('#adventure-list');
    list.innerHTML = adventures.length ? adventures.map((adventure) => `<article class="adventure-item"><div><span class="item-location">${escapeHtml(adventure.ubicacion || 'Mi diario')}</span><h3>${escapeHtml(adventure.titulo)}</h3><p>${escapeHtml(adventure.contenido)}</p></div></article>`).join('') : '<p class="empty-note">Todavía no has escrito una aventura.</p>';
}

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
    grid.innerHTML = photos.length ? photos.map((photo) => `<img src="${API_BASE_URL}${photo.url}" alt="${escapeHtml(photo.nombre_archivo)}" loading="lazy">`).join('') : '<p class="empty-note">Tus fotos aparecerán aquí.</p>';
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
    }).join('') : '<p class="empty-note">Todavía no tienes publicaciones. Comparte tu primera imagen o video.</p>';
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' })[character]);
}

if (getToken()) showDashboard();

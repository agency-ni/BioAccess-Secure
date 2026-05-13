// api.js - Gestion centralisée des appels API

// ── Détection file:// — redirige automatiquement vers Flask ─────────────────
(function () {
    if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
        const page = window.location.pathname.split('/').pop() || 'login.html';
        window.location.replace('http://localhost:5000/' + page);
    }
})();
// ────────────────────────────────────────────────────────────────────────────

const API = {
    baseURL: window.API_URL || window.CONFIG?.API_URL || (
        // Servi par Flask (port 5000) → URL relative, sinon Live Server → absolu
        (typeof window !== 'undefined' && window.location.port === '5000')
            ? '/api/v1'
            : 'http://localhost:5000/api/v1'
    ),
    _csrfToken: null,

    requireAuth() {
        if (!sessionStorage.getItem('token')) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    },

    headers() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${sessionStorage.getItem('token')}`
        };
    },

    // ── Status badge (bottom-right corner) ──────────────────────────
    _status: {
        _el: null,
        _timer: null,
        _init() {
            if (this._el || typeof document === 'undefined') return;
            const el = document.createElement('div');
            el.id = '_apiStatusBadge';
            el.style.cssText = [
                'position:fixed', 'bottom:18px', 'right:18px', 'z-index:99999',
                'font-size:12px', 'font-family:inherit',
                'padding:7px 14px', 'border-radius:20px',
                'transition:opacity 0.4s', 'display:flex', 'align-items:center',
                'gap:7px', 'box-shadow:0 2px 10px rgba(0,0,0,0.15)',
                'pointer-events:none', 'opacity:0'
            ].join(';');
            document.body.appendChild(el);
            this._el = el;
        },
        ok(msg) {
            if (typeof document === 'undefined') return;
            this._init();
            clearTimeout(this._timer);
            this._el.style.cssText = this._el.style.cssText
                .replace(/background:[^;]+;?/, '')
                .replace(/color:[^;]+;?/, '');
            this._el.style.background = '#d1fae5';
            this._el.style.color = '#065f46';
            this._el.style.opacity = '1';
            this._el.innerHTML =
                '<span style="width:8px;height:8px;background:#10b981;border-radius:50%;display:inline-block;flex-shrink:0"></span>' +
                (msg || 'Backend connecté');
            this._timer = setTimeout(() => { if (this._el) this._el.style.opacity = '0'; }, 4000);
        },
        error(msg) {
            if (typeof document === 'undefined') return;
            this._init();
            clearTimeout(this._timer);
            this._el.style.background = '#fee2e2';
            this._el.style.color = '#991b1b';
            this._el.style.opacity = '1';
            this._el.innerHTML =
                '<span style="width:8px;height:8px;background:#ef4444;border-radius:50%;display:inline-block;flex-shrink:0"></span>' +
                msg;
        }
    },

    // ── Internal fetch wrapper – catches network errors ───────────────
    async _fetchSafe(url, options) {
        try {
            return await fetch(url, options);
        } catch (e) {
            // TypeError = backend unreachable (refused / no network)
            const host = this.baseURL.replace('/api/v1', '');
            API._status.error('Backend inaccessible');
            throw new Error(
                `Impossible de joindre le backend (${host}) — assurez-vous que le serveur Flask est démarré.`
            );
        }
    },

    // CSRF désactivé (JWT Bearer) — retourne toujours une chaîne vide
    async _ensureCsrf() {
        return '';
    },

    async _mutatingHeaders() {
        const csrf = await this._ensureCsrf();
        const h = this.headers();
        if (csrf) h['X-CSRFToken'] = csrf;
        return h;
    },

    async get(endpoint) {
        const response = await this._fetchSafe(`${this.baseURL}${endpoint}`, {
            method: 'GET',
            headers: this.headers(),
            credentials: 'include'
        });
        const newCsrf = response.headers.get('X-CSRFToken');
        if (newCsrf) this._csrfToken = newCsrf;
        return this.handleResponse(response);
    },

    async post(endpoint, data) {
        const response = await this._fetchSafe(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: await this._mutatingHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },

    async put(endpoint, data) {
        const response = await this._fetchSafe(`${this.baseURL}${endpoint}`, {
            method: 'PUT',
            headers: await this._mutatingHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },

    async delete(endpoint) {
        const response = await this._fetchSafe(`${this.baseURL}${endpoint}`, {
            method: 'DELETE',
            headers: await this._mutatingHeaders(),
            credentials: 'include'
        });
        return this.handleResponse(response);
    },

    async upload(endpoint, formData) {
        const csrf = await this._ensureCsrf();
        const headers = { 'Authorization': `Bearer ${sessionStorage.getItem('token')}` };
        if (csrf) headers['X-CSRFToken'] = csrf;
        const response = await this._fetchSafe(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers,
            credentials: 'include',
            body: formData
        });
        return this.handleResponse(response);
    },

    async handleResponse(response) {
        let data;
        try { data = await response.json(); } catch (_) { data = {}; }

        if (!response.ok) {
            const token = sessionStorage.getItem('token');

            if (response.status === 401) {
                // Demo token detected — all API calls will fail with this token
                if (token && token.startsWith('demo-token')) {
                    API._status.error('Token de démo — reconnectez-vous');
                    throw new Error(
                        'Session de démonstration invalide — le backend est maintenant actif, reconnectez-vous.'
                    );
                }
                // Real token expired / invalid
                if (token) {
                    API._status.error('Session expirée');
                    sessionStorage.removeItem('token');
                    sessionStorage.removeItem('user');
                    window.location.href = 'login.html';
                }
                throw new Error(data.message || data.error || 'Non authentifié (401)');
            }

            if (response.status === 403) {
                API._status.error('Accès refusé (403)');
                throw new Error(data.message || data.error || 'Accès refusé — droits insuffisants');
            }

            if (response.status >= 500) {
                API._status.error(`Erreur serveur (${response.status})`);
                throw new Error(data.message || data.error || `Erreur interne du serveur (${response.status})`);
            }

            API._status.error(`Erreur ${response.status}`);
            throw new Error(data.message || data.error || `Erreur HTTP ${response.status}`);
        }

        API._status.ok('Données chargées');
        return this.normalizeResponse(data);
    },

    // Normalise les réponses vers un format unifié { status, data, meta }
    normalizeResponse(data) {
        if (data.status && (data.status === 'success' || data.status === 'error')) {
            return data;
        }
        return {
            status: data.success !== false ? 'success' : 'error',
            code: data.code || 200,
            timestamp: data.timestamp || new Date().toISOString(),
            message: data.message || (data.success ? 'Succès' : 'Erreur'),
            data: data.data !== undefined ? data.data : data,
            error_code: data.error_code || null
        };
    },

    // ── Health check (public endpoint, no auth) ──────────────────────
    async checkHealth() {
        const host = this.baseURL.replace('/api/v1', '');
        try {
            const r = await fetch(`${host}/health`, { method: 'GET' });
            return r.ok;
        } catch (_) {
            return false;
        }
    },

    // ── Dashboard ────────────────────────────────────────────────
    dashboard: {
        async getKpis() {
            return API.get('/dashboard/kpis');
        },
        async getActivity(days = 7) {
            return API.get(`/dashboard/activity?days=${days}`);
        },
        async getRecentLogins() {
            return API.get('/dashboard/recent-logins');
        },
        async getTopFailures() {
            return API.get('/dashboard/top-failures');
        }
    },

    // ── Utilisateurs ─────────────────────────────────────────────
    users: {
        async getAll(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return API.get('/users' + (qs ? '?' + qs : ''));
        },
        async getById(id) {
            return API.get(`/users/${id}`);
        },
        async create(data) {
            return API.post('/users', data);
        },
        async update(id, data) {
            return API.put(`/users/${id}`, data);
        },
        async delete(id) {
            return API.delete(`/users/${id}`);
        }
    },

    // ── Logs ─────────────────────────────────────────────────────
    logs: {
        async getAll(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return API.get('/logs' + (qs ? '?' + qs : ''));
        }
    },

    // ── Alertes ──────────────────────────────────────────────────
    alerts: {
        async getAll(params = {}) {
            const qs = new URLSearchParams(params).toString();
            return API.get('/alerts' + (qs ? '?' + qs : ''));
        },
        async resolve(id) {
            return API.post(`/alerts/${id}/resolve`, {});
        }
    },

    // ── Auth ─────────────────────────────────────────────────────
    auth: {
        async login(email, password) {
            return API.post('/auth/login', { email, password });
        },
        logout() {
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = 'login.html';
        }
    },

    // ── Enrôlement biométrique (admin) ────────────────────────
    enrollment: {
        async faceEnroll(userId, imageB64, livenessConfirmed = true, earMin = null) {
            return API.post('/admin/biometric/enroll/face', {
                user_id: userId,
                image_b64: imageB64,
                liveness_confirmed: livenessConfirmed,
                ear_min: earMin
            });
        },
        async voiceEnroll(userId, audioB64) {
            return API.post('/admin/biometric/enroll/voice', { user_id: userId, audio_b64: audioB64 });
        },
        async voiceChallenge() {
            const r = await fetch(`${API.baseURL}/auth/voice/challenge`, { credentials: 'include' });
            return r.json();
        }
    }
};

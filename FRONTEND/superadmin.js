// superadmin.js — Système de protection des actions sensibles
// Le mode Super Admin est requis pour toute écriture (création, modification, suppression, résolution).
// Les logs sont en lecture seule pour tout le monde, côté frontend et backend.

const SuperAdmin = {
    STORAGE_KEY: 'bioAccess_superAdminActive',

    get active() {
        return sessionStorage.getItem(this.STORAGE_KEY) === 'true';
    },

    _setActive(val) {
        sessionStorage.setItem(this.STORAGE_KEY, val ? 'true' : 'false');
    },

    init() {
        // Inject CSS guard
        const style = document.createElement('style');
        style.textContent = `
            body.sa-locked [data-sa="write"] {
                opacity: 0.38 !important;
                filter: grayscale(0.4);
            }
            #superAdminToggle { outline: none; border: none; }
            #superAdminToggle:focus-visible { box-shadow: 0 0 0 2px #4f46e5; }
            .sa-toast {
                position: fixed; bottom: 24px; left: 50%;
                transform: translateX(-50%) translateY(0);
                padding: 10px 22px; border-radius: 10px;
                font-size: 13px; font-weight: 500; z-index: 99999;
                pointer-events: none; white-space: nowrap;
                box-shadow: 0 4px 16px rgba(0,0,0,0.18);
                transition: opacity 0.35s ease, transform 0.35s ease;
            }
        `;
        document.head.appendChild(style);

        // Apply initial visual state
        this._applyBodyClass();
        const btn = document.getElementById('superAdminToggle');
        if (btn) {
            this._applyToggleUI(btn, this.active);
            btn.addEventListener('click', () => this.toggle());
        }

        // Global capture interceptor — fires before any element's own handlers
        document.addEventListener('click', (e) => this._interceptClick(e), true);
    },

    toggle() {
        // TODO: quand le système biométrique est prêt, appeler ici l'auth admin
        // avant d'activer. Pour l'instant: toggle direct.
        const next = !this.active;
        this._setActive(next);
        this._applyBodyClass();
        const btn = document.getElementById('superAdminToggle');
        if (btn) this._applyToggleUI(btn, next);
        this._showToast(next
            ? '🔓 Mode Super Admin activé — modifications autorisées'
            : '🔒 Mode Protégé — lecture seule uniquement',
            next ? '#4f46e5' : '#6b7280'
        );
    },

    // Appel explicite depuis du code JS : retourne true si autorisé
    require() {
        if (!this.active) {
            this._showToast('🔒 Activez le Mode Super Admin pour cette action', '#ef4444');
            return false;
        }
        return true;
    },

    _interceptClick(e) {
        const target = e.target.closest('[data-sa="write"]');
        if (target && !this.active) {
            e.preventDefault();
            e.stopImmediatePropagation();
            this._showToast('🔒 Mode Super Admin requis pour cette action', '#ef4444');
        }
    },

    _applyBodyClass() {
        document.body.classList.toggle('sa-locked', !this.active);
    },

    _applyToggleUI(btn, active) {
        const dot = btn.querySelector('span');
        if (active) {
            btn.style.backgroundColor = '#4f46e5';
            if (dot) dot.style.transform = 'translateX(20px)';
        } else {
            btn.style.backgroundColor = '#d1d5db';
            if (dot) dot.style.transform = 'translateX(0px)';
        }

        const icon = document.getElementById('saIcon');
        const label = document.getElementById('saLabel');
        if (icon) {
            icon.style.color = active ? '#4f46e5' : '#9ca3af';
        }
        if (label) {
            label.textContent = active ? 'Super Admin ON' : 'Mode Protégé';
            label.style.color = active ? '#4f46e5' : '#6b7280';
            label.style.fontWeight = active ? '600' : '500';
        }
    },

    _showToast(msg, color) {
        // Remove any existing toast
        document.querySelectorAll('.sa-toast').forEach(t => t.remove());
        const t = document.createElement('div');
        t.className = 'sa-toast';
        t.style.background = color;
        t.style.color = '#fff';
        t.textContent = msg;
        document.body.appendChild(t);
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translateX(-50%) translateY(10px)';
        }, 2400);
        setTimeout(() => t.remove(), 2850);
    }
};

document.addEventListener('DOMContentLoaded', () => SuperAdmin.init());

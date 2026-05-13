const PROFILE_FIELDS = {
    lastName: 'nom',
    firstName: 'prenom',
    email: 'email',
    phone: 'tel',
    department: 'departement',
    role: 'role',
};

function showProfileMessage(message, success = true) {
    const statusEl = document.getElementById('profileSaveStatus');
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.className = success ? 'text-sm text-green-600 mt-3' : 'text-sm text-red-600 mt-3';
}

function normalizeText(value) {
    return (value || '').toString().trim().toLowerCase().replace(/[\W_]+/g, ' ').replace(/\s+/g, ' ').trim();
}

async function loadProfile() {
    const token = sessionStorage.getItem('token');
    if (!token) { window.location.replace('login.html'); return; }
    try {
        const res = await fetch('/api/v1/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.status === 401) { window.location.replace('login.html'); return; }
        if (!res.ok) throw new Error('Échec chargement profil');
        const u = await res.json();
        if (!u) throw new Error('Aucune donnée utilisateur');

        const initials = `${(u.prenom || '').charAt(0) || ''}${(u.nom || '').charAt(0) || ''}`.toUpperCase() || 'AD';
        document.querySelectorAll('#userInitials').forEach(el => el.textContent = initials);
        const adminNameEl = document.getElementById('adminName');
        if (adminNameEl) adminNameEl.textContent = `${u.prenom || ''} ${u.nom || ''}`.trim() || 'Admin';
        const adminRoleEl = document.getElementById('adminRole');
        if (adminRoleEl) adminRoleEl.textContent = u.role === 'admin' ? 'Administrateur' : u.role || 'Utilisateur';
        const avatarEl = document.querySelector('.w-32.h-32');
        if (avatarEl) avatarEl.textContent = initials;
        const nameH2 = document.querySelector('.w-32.h-32 ~ h2');
        if (nameH2) nameH2.textContent = `${u.prenom || ''} ${u.nom || ''}`.trim();
        const roleP = document.querySelector('.w-32.h-32 ~ h2 + p');
        if (roleP) roleP.textContent = u.role === 'admin' ? 'Super Admin' : u.role || '';

        Object.entries(PROFILE_FIELDS).forEach(([elementId, key]) => {
            const input = document.getElementById(elementId);
            if (!input) return;
            if (u[key] !== undefined && u[key] !== null) {
                input.value = u[key];
            }
        });

        const twoFaToggle = document.getElementById('twoFaToggle');
        if (twoFaToggle && typeof u.twofa_enabled !== 'undefined') {
            twoFaToggle.checked = Boolean(u.twofa_enabled);
        }
        setup2faToggle();
        loadRecentActions(token);
    } catch (e) {
        console.warn('[Profil] Erreur chargement:', e);
        showProfileMessage('Impossible de charger le profil.', false);
    }
}

async function loadRecentActions(token) {
    try {
        const res = await fetch('/api/v1/auth/my-actions', {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Échec chargement actions');
        const json = await res.json();
        const actions = json.actions || json.data || json.history || [];
        const tbody = document.getElementById('recentActionsBody');
        if (!tbody) return;
        if (!actions.length) {
            tbody.innerHTML = '<tr class="border-t"><td class="py-2" colspan="3">Aucune action récente.</td></tr>';
            return;
        }
        tbody.innerHTML = actions.map(action => {
            const date = action.date || action.timestamp || action.created_at || action.time || '—';
            const dateStr = date ? new Date(date).toLocaleString('fr-FR', {
                day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
            }) : '—';
            const label = action.action || action.type || action.description || '—';
            const ip = action.ip || action.adresse_ip || action.client_ip || '—';
            return `<tr class="border-t"><td class="py-2">${dateStr}</td><td>${label}</td><td>${ip}</td></tr>`;
        }).join('');
    } catch (e) {
        console.warn('[Profil] Erreur chargement actions:', e);
    }
}

function setup2faToggle() {
    const toggle = document.getElementById('twoFaToggle');
    if (!toggle) return;
    toggle.addEventListener('change', async () => {
        const token = sessionStorage.getItem('token');
        if (!token) { window.location.replace('login.html'); return; }
        try {
            const res = await fetch('/api/v1/auth/twofa/toggle', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            const json = await res.json();
            if (!res.ok || !json.success) {
                toggle.checked = !toggle.checked;
                throw new Error(json.error || 'Impossible de changer 2FA');
            }
            toggle.checked = Boolean(json.enabled ?? json.twofa_enabled ?? toggle.checked);
            showProfileMessage(`2FA ${toggle.checked ? 'activée' : 'désactivée'}.`);
        } catch (e) {
            toggle.checked = !toggle.checked;
            showProfileMessage(e.message || 'Erreur activation 2FA.', false);
        }
    });
}

async function saveProfile() {
    const token = sessionStorage.getItem('token');
    if (!token) { window.location.replace('login.html'); return; }
    const email = document.getElementById('email')?.value.trim();
    const phone = document.getElementById('phone')?.value.trim();
    try {
        const res = await fetch('/api/v1/auth/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ email, telephone: phone, tel: phone }),
        });
        const json = await res.json();
        if (!res.ok || !json.success) {
            throw new Error(json.error || 'Mise à jour impossible');
        }
        showProfileMessage('Profil mis à jour.', true);
    } catch (e) {
        showProfileMessage(e.message || 'Erreur enregistrement profil.', false);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const saveBtn = document.getElementById('saveProfileBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveProfile);
    }
    loadProfile();
});

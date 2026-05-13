const FIELD_MAP = {
    facialThreshold:  { key: 'facial_threshold',  type: 'float' },
    voiceThreshold:   { key: 'voice_threshold',   type: 'float' },
    maxAttempts:      { key: 'max_attempts',      type: 'integer' },
    blockDuration:    { key: 'lockout_duration',  type: 'integer' },
    liveDetection:    { key: 'liveness_required', type: 'boolean' },
    lockDelay:        { key: 'lock_delay',        type: 'integer' },
    doorOpenTime:     { key: 'door_open_time',    type: 'integer' },
    antiTailgating:   { key: 'anti_tailgating',   type: 'boolean' },
    accessAlarm:      { key: 'access_alarm',      type: 'boolean' },
    logLevel:         { key: 'log_level',         type: 'string' },
    logRetention:     { key: 'log_retention',     type: 'integer' },
    autoArchive:      { key: 'auto_archive',      type: 'boolean' },
    secureBackup:     { key: 'secure_backup',     type: 'boolean' },
    emailAlerts:      { key: 'email_alerts',      type: 'boolean' },
    smsAlerts:        { key: 'sms_alerts',        type: 'boolean' },
    systemAlerts:     { key: 'system_alerts',     type: 'boolean' },
    alertLevel:       { key: 'alert_level',       type: 'string' },
    apiEnabled:       { key: 'api_enabled',       type: 'boolean' },
    apiRateLimit:     { key: 'api_rate_limit',    type: 'integer' },
    apiVersion:       { key: 'api_version',       type: 'string' },
    oauth2:           { key: 'oauth2',            type: 'boolean' },
    tlsEncryption:    { key: 'tls_encryption',    type: 'boolean' },
    customHeaders:    { key: 'custom_headers',    type: 'boolean' },
};

const API_KEY_TO_FIELD = Object.fromEntries(
    Object.entries(FIELD_MAP).map(([fieldId, meta]) => [meta.key, fieldId])
);

function _getFieldValue(elId, type) {
    const el = document.getElementById(elId);
    if (!el) return undefined;
    if (type === 'boolean') return el.checked;
    if (type === 'integer') return parseInt(el.value, 10);
    if (type === 'float') return parseFloat(el.value);
    return el.value;
}

function _setFieldValue(elId, value) {
    const el = document.getElementById(elId);
    if (!el) return;
    if (el.type === 'checkbox') {
        el.checked = Boolean(value);
        return;
    }
    el.value = value !== null && value !== undefined ? value : '';
    if (elId === 'facialThreshold') {
        const lbl = document.getElementById('facialThresholdValue');
        if (lbl) lbl.textContent = parseFloat(el.value).toFixed(2);
    }
    if (elId === 'voiceThreshold') {
        const lbl = document.getElementById('voiceThresholdValue');
        if (lbl) lbl.textContent = parseFloat(el.value).toFixed(2);
    }
}

async function updateConfigValue(apiKey, value) {
    const token = sessionStorage.getItem('token');
    if (!token) {
        alert('Session expirée — reconnectez-vous.');
        return false;
    }

    try {
        const res = await fetch(`/api/v1/config/${encodeURIComponent(apiKey)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ value }),
        });
        const json = await res.json();
        if (!res.ok || !json.success) {
            console.warn('[Config] Erreur mise à jour immédiate', json);
            alert(`Erreur mise à jour ${apiKey} : ${json.error || 'Échec'}`);
            return false;
        }
        return true;
    } catch (e) {
        console.error('[Config] updateConfigValue', e);
        alert(`Erreur réseau — mise à jour de ${apiKey} impossible.`);
        return false;
    }
}

async function attachToggleEvents() {
    Object.entries(FIELD_MAP).forEach(([fieldId, meta]) => {
        if (meta.type !== 'boolean') return;
        const input = document.getElementById(fieldId);
        if (!input) return;
        input.addEventListener('change', async () => {
            await updateConfigValue(meta.key, _getFieldValue(fieldId, meta.type));
            await saveConfigHistory();
        });
    });
}

async function loadConfig() {
    await Promise.all([loadConfigFromAPI(), saveConfigHistory()]);
    attachToggleEvents();
}

async function loadConfigFromAPI() {
    const token = sessionStorage.getItem('token');
    if (!token) return;
    try {
        const res = await fetch('/api/v1/config', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) return;
        const json = await res.json();
        if (!json.success || !json.config) return;
        const cfg = json.config;
        Object.entries(cfg).forEach(([apiKey, value]) => {
            const fieldId = API_KEY_TO_FIELD[apiKey];
            if (fieldId) _setFieldValue(fieldId, value);
        });
    } catch (e) {
        console.warn('[Config] Échec chargement config', e);
    }
}

async function saveConfigHistory() {
    const token = sessionStorage.getItem('token');
    if (!token) return;
    try {
        const res = await fetch('/api/v1/config/history', {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) return;
        const json = await res.json();
        const history = json.history || json.data || [];
        const tbody = document.getElementById('configHistoryBody');
        if (!tbody) return;
        tbody.innerHTML = history.length
            ? history.map(entry => {
                const date = entry.date || entry.timestamp || entry.created_at || '—';
                const niceDate = new Date(date).toLocaleString('fr-FR', {
                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                });
                return `
                    <tr class="border-t">
                        <td class="py-2">${niceDate}</td>
                        <td>${entry.admin || entry.user || entry.author || '—'}</td>
                        <td>${entry.key || entry.parametre || entry.setting || '—'}</td>
                        <td>${entry.before ?? entry.avant ?? '—'}</td>
                        <td>${entry.after ?? entry.apres ?? '—'}</td>
                    </tr>`;
            }).join('')
            : '<tr class="border-t"><td class="py-2" colspan="5">Aucune modification enregistrée.</td></tr>';
    } catch (e) {
        console.warn('[Config] Échec historique', e);
    }
}

async function restoreDefaults() {
    const token = sessionStorage.getItem('token');
    if (!token) {
        alert('Session expirée — reconnectez-vous.');
        return;
    }
    try {
        const res = await fetch('/api/v1/config/defaults', {
            headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Requête échouée');
        const json = await res.json();
        const defaults = json.defaults || json.data || json.config;
        if (!defaults) throw new Error('Aucun jeu de défauts reçu');
        const updates = {};
        Object.entries(defaults).forEach(([apiKey, value]) => {
            const fieldId = API_KEY_TO_FIELD[apiKey];
            if (fieldId) {
                _setFieldValue(fieldId, value);
                updates[apiKey] = value;
            }
        });
        const batchRes = await fetch('/api/v1/config/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ updates }),
        });
        const batchJson = await batchRes.json();
        if (!batchRes.ok || !batchJson.success) {
            throw new Error(batchJson.error || 'Échec restauration défauts');
        }
        await saveConfigHistory();
        alert('Réinitialisation aux valeurs par défaut effectuée.');
    } catch (e) {
        console.error('[Config] restoreDefaults', e);
        alert(`Impossible de restaurer les valeurs par défaut : ${e.message}`);
    }
}

async function saveConfigChanges() {
    const token = sessionStorage.getItem('token');
    if (!token) { alert('Session expirée — reconnectez-vous.'); return; }
    const updates = {};
    Object.entries(FIELD_MAP).forEach(([elId, meta]) => {
        const value = _getFieldValue(elId, meta.type);
        if (value !== undefined) updates[meta.key] = value;
    });
    try {
        const res = await fetch('/api/v1/config/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ updates }),
        });
        const json = await res.json();
        if (json.success) {
            alert(`Configuration enregistrée — ${json.message || 'OK'}`);
            await saveConfigHistory();
        } else {
            alert(`Erreur : ${json.error || 'Sauvegarde échouée'}`);
        }
    } catch (e) {
        console.error('Erreur saveConfigChanges:', e);
        alert('Erreur réseau — configuration non sauvegardée.');
    }
}

window.addEventListener('load', loadConfig);

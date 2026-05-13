/**
 * Admin Biometric Dashboard - JavaScript Logic
 * Gère l'interface d'administration pour authentification biométrique
 * Support: Enregistrement users, Desktop users, Logs, Erreurs, Analytics
 */

const API_BASE = '/api/v1';
const TOKEN = sessionStorage.getItem('token') || localStorage.getItem('token');

let currentPage = 0;
let selectedFaceImage = null;
let enrollmentMode = 'upload'; // 'upload' ou 'live'
let stream = null;
let canvas = null;
let liveMode = 'enroll'; // 'enroll' ou 'modal'

// ============================================
// INITIALIZATION
// ============================================

// ============================================
// HELPER FUNCTIONS
// ============================================

// Normalise les réponses au nouveau format APIResponse
function normalizeResponse(data) {
    // Si déjà au nouveau format, retourner tel quel
    if (data.status && (data.status === 'success' || data.status === 'error')) {
        return data;
    }
    
    // Sinon, convertir ancien format vers nouveau format pour backward compatibility
    // Ancien format: { success, ... }
    return {
        status: data.success !== false ? 'success' : 'error',
        code: data.code || 200,
        message: data.message || (data.success ? 'Succès' : 'Erreur'),
        data: data.data || data  // Le reste des données
    };
}

document.addEventListener('DOMContentLoaded', async () => {
    loadAdminDashboard();
    setupTabNavigation();
    setupEnrollmentForm();
    setupDesktopUsers();
    setupLogs();
    setupErrorsMonitoring();
    setupAnalytics();
});

async function loadAdminDashboard() {
    try {
        const response = await axios.get(`${API_BASE}/admin/biometric/dashboard`, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            const stats = data.stats || data;
            document.getElementById('stat-users').textContent = stats.total_users || '--';
            document.getElementById('stat-auth').textContent = stats.auth_24h || '--';
            document.getElementById('stat-errors').textContent = stats.errors_24h || '--';
            document.getElementById('stat-rate').textContent = 
                (stats.success_rate || 0).toFixed(1) + '%';
            
            document.getElementById('adminName').textContent = data.admin_name || 'Admin';
        }
    } catch (error) {
        console.error('Erreur chargement dashboard:', error);
    }
}

// ============================================
// TAB NAVIGATION
// ============================================

function setupTabNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Hide all tabs
            document.getElementById('enrollmentTab').classList.add('hidden');
            document.getElementById('desktopUsersTab').classList.add('hidden');
            document.getElementById('logsTab').classList.add('hidden');
            document.getElementById('errorsTab').classList.add('hidden');
            document.getElementById('analyticsTab').classList.add('hidden');

            // Show selected tab
            const tabId = btn.dataset.tab;
            switch(tabId) {
                case 'enrollment':
                    document.getElementById('enrollmentTab').classList.remove('hidden');
                    break;
                case 'desktop-users':
                    document.getElementById('desktopUsersTab').classList.remove('hidden');
                    loadDesktopUsers();
                    break;
                case 'logs':
                    document.getElementById('logsTab').classList.remove('hidden');
                    loadAuthLogs();
                    break;
                case 'errors':
                    document.getElementById('errorsTab').classList.remove('hidden');
                    loadErrorAlerts();
                    break;
                case 'analytics':
                    document.getElementById('analyticsTab').classList.remove('hidden');
                    loadAnalytics();
                    break;
            }
        });
    });
}

// ============================================
// ENROLLMENT FORM
// ============================================

function setupEnrollmentForm() {
    // Mode buttons
    document.getElementById('modeUploadBtn').addEventListener('click', () => switchEnrollmentMode('upload'));
    document.getElementById('modeLiveBtn').addEventListener('click', () => switchEnrollmentMode('live'));

    // Upload handling
    const uploadArea = document.getElementById('uploadArea');
    const faceUpload = document.getElementById('faceUpload');

    uploadArea.addEventListener('click', () => faceUpload.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('bg-indigo-50');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('bg-indigo-50');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('bg-indigo-50');
        handleUploadedFile(e.dataTransfer.files[0]);
    });

    faceUpload.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleUploadedFile(e.target.files[0]);
        }
    });

    // Clear upload
    document.getElementById('clearUploadBtn').addEventListener('click', clearUploadPreview);

    // Live capture buttons
    document.getElementById('captureLiveBtn').addEventListener('click', captureLivePhoto);
    document.getElementById('stopLiveBtn').addEventListener('click', stopLiveCapture);
    document.getElementById('clearLiveBtn').addEventListener('click', clearLivePreview);

    // Enrollment submit
    document.getElementById('submitEnrollBtn').addEventListener('click', submitEnrollment);

    // Auto-update submit button
    setupEnrollmentValidation();
}

function switchEnrollmentMode(mode) {
    enrollmentMode = mode;
    
    document.getElementById('modeUploadBtn').classList.toggle('bg-indigo-600', mode === 'upload');
    document.getElementById('modeUploadBtn').classList.toggle('text-white', mode === 'upload');
    document.getElementById('modeUploadBtn').classList.toggle('border-2', mode !== 'upload');
    document.getElementById('modeUploadBtn').classList.toggle('border-gray-300', mode !== 'upload');
    document.getElementById('modeUploadBtn').classList.toggle('text-gray-700', mode !== 'upload');

    document.getElementById('modeLiveBtn').classList.toggle('bg-indigo-600', mode === 'live');
    document.getElementById('modeLiveBtn').classList.toggle('text-white', mode === 'live');
    document.getElementById('modeLiveBtn').classList.toggle('border-2', mode !== 'live');
    document.getElementById('modeLiveBtn').classList.toggle('border-gray-300', mode !== 'live');
    document.getElementById('modeLiveBtn').classList.toggle('text-gray-700', mode !== 'live');

    document.getElementById('uploadSection').classList.toggle('hidden', mode !== 'upload');
    document.getElementById('liveSection').classList.toggle('hidden', mode !== 'live');

    if (mode === 'live' && !stream) {
        startLiveCapture();
    } else if (mode !== 'live' && stream) {
        stopLiveCapture();
    }
}

function handleUploadedFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        showMessage('enrollmentResult', 'Veuillez sélectionner une image valide (JPG/PNG)', 'error');
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showMessage('enrollmentResult', 'L\'image doit faire moins de 5MB', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        selectedFaceImage = e.target.result;
        document.getElementById('uploadPreviewImg').src = selectedFaceImage;
        document.getElementById('uploadPreview').classList.remove('hidden');
        document.getElementById('uploadArea').classList.add('hidden');
        
        analyzeImageQuality(selectedFaceImage);
        setupEnrollmentValidation();
    };
    reader.readAsDataURL(file);
}

function clearUploadPreview() {
    selectedFaceImage = null;
    document.getElementById('uploadPreview').classList.add('hidden');
    document.getElementById('uploadArea').classList.remove('hidden');
    document.getElementById('qualityStatus').classList.add('hidden');
    setupEnrollmentValidation();
}

async function startLiveCapture() {
    try {
        const video = document.getElementById('enrollVideo');
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: 640, height: 480 }
        });
        video.srcObject = stream;

        canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 480;

        document.getElementById('livePreview').classList.add('hidden');
        startQualityDetection();
    } catch (error) {
        let msg = 'Impossible d\'accéder à la caméra.';
        if (error.name === 'NotAllowedError') msg = 'Permission caméra refusée — autorisez la caméra dans les paramètres du navigateur (icône 🔒).';
        else if (error.name === 'NotFoundError') msg = 'Aucune caméra détectée — utilisez l\'import de photo.';
        else if (error.name === 'NotReadableError') msg = 'Caméra utilisée par une autre application — fermez-la et réessayez.';
        showMessage('enrollmentResult', msg, 'error');
    }
}

function stopLiveCapture() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

async function captureLivePhoto() {
    if (!stream) return;

    try {
        document.getElementById('liveCaptureLoading').classList.remove('hidden');
        const video = document.getElementById('enrollVideo');
        
        canvas.getContext('2d').drawImage(video, 0, 0);
        selectedFaceImage = canvas.toDataURL('image/jpeg');
        
        document.getElementById('livePreviewImg').src = selectedFaceImage;
        document.getElementById('livePreview').classList.remove('hidden');
        document.getElementById('liveContainer').classList.add('hidden');

        analyzeImageQuality(selectedFaceImage);
        setupEnrollmentValidation();

        document.getElementById('liveCaptureLoading').classList.add('hidden');
    } catch (error) {
        showMessage('enrollmentResult', 'Erreur lors de la capture', 'error');
    }
}

function clearLivePreview() {
    document.getElementById('livePreview').classList.add('hidden');
    document.getElementById('liveContainer').classList.remove('hidden');
    selectedFaceImage = null;
    setupEnrollmentValidation();
}

async function analyzeImageQuality(imageBase64) {
    try {
        // Appel API backend pour analyser la qualité
        const response = await axios.post(`${API_BASE}/biometric/analyze-quality`, {
            image_base64: imageBase64
        }, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            const quality = Math.round(data.quality_score * 100);
            document.getElementById('qualityPercent').textContent = quality + '%';
            document.getElementById('qualityBar').style.width = quality + '%';
            document.getElementById('qualityStatus').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Erreur analyse qualité:', error);
    }
}

function startQualityDetection() {
    // Simulation détection qualité vidéo (en temps réel)
    const interval = setInterval(() => {
        if (!stream) {
            clearInterval(interval);
            return;
        }

        const quality = Math.random() * 100;
        if (quality > 30) {
            document.getElementById('qualityPercent').textContent = Math.round(quality) + '%';
            document.getElementById('qualityBar').style.width = quality + '%';
            document.getElementById('qualityStatus').classList.remove('hidden');
        }
    }, 500);
}

function setupEnrollmentValidation() {
    const email = document.getElementById('enrollEmail').value.trim();
    const role = document.getElementById('enrollRole').value.trim();
    const hasFace = selectedFaceImage !== null;

    const isValid = email && role && hasFace;
    document.getElementById('submitEnrollBtn').disabled = !isValid;
}

document.getElementById('enrollEmail').addEventListener('input', setupEnrollmentValidation);
document.getElementById('enrollRole').addEventListener('change', setupEnrollmentValidation);

async function submitEnrollment() {
    if (typeof SuperAdmin !== 'undefined' && !SuperAdmin.require()) return;
    const email = document.getElementById('enrollEmail').value.trim();
    const firstName = document.getElementById('enrollFirstName').value.trim();
    const lastName = document.getElementById('enrollLastName').value.trim();
    const role = document.getElementById('enrollRole').value;
    const requireBiometric = document.getElementById('requireBiometric').checked;

    if (!email || !role || !selectedFaceImage) {
        showMessage('enrollmentResult', 'Veuillez remplir tous les champs', 'error');
        return;
    }

    try {
        document.getElementById('submitEnrollBtn').disabled = true;

        // Enregistrer l'utilisateur + biométrie
        const response = await axios.post(`${API_BASE}/admin/biometric/enroll-user`, {
            email,
            first_name: firstName,
            last_name: lastName,
            role,
            require_biometric: requireBiometric,
            face_image_base64: selectedFaceImage,
            enrollment_mode: enrollmentMode
        }, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            showMessage('enrollmentResult', 
                `Utilisateur "${email}" enregistré avec succès!`, 'success');
            
            // Reset form
            setTimeout(() => {
                document.getElementById('enrollEmail').value = '';
                document.getElementById('enrollFirstName').value = '';
                document.getElementById('enrollLastName').value = '';
                document.getElementById('enrollRole').value = '';
                selectedFaceImage = null;
                clearUploadPreview();
                clearLivePreview();
                setupEnrollmentValidation();
                loadDesktopUsers(); // Refresh users list
            }, 2000);
        } else {
            showMessage('enrollmentResult', normalizedData.message || 'Erreur lors de l\'enregistrement', 'error');
        }
    } catch (error) {
        const message = error.response?.data?.message || 'Erreur serveur';
        showMessage('enrollmentResult', message, 'error');
    }

    document.getElementById('submitEnrollBtn').disabled = false;
}

// ============================================
// DESKTOP USERS
// ============================================

function setupDesktopUsers() {
    document.getElementById('refreshDesktopBtn').addEventListener('click', loadDesktopUsers);
    document.getElementById('desktopSearchInput').addEventListener('input', filterDesktopUsers);
}

async function loadDesktopUsers() {
    try {
        const response = await axios.get(`${API_BASE}/admin/biometric/desktop-users`, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            renderDesktopUsersTable(data.users || []);
        }
    } catch (error) {
        console.error('Erreur chargement desktop users:', error);
        document.getElementById('desktopUsersTableBody').innerHTML = 
            '<tr><td colspan="6" class="px-6 py-4 text-center text-red-600">Erreur lors du chargement</td></tr>';
    }
}

function renderDesktopUsersTable(users) {
    const tbody = document.getElementById('desktopUsersTableBody');
    
    if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-8 text-center text-gray-500">Aucun utilisateur desktop</td></tr>';
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4">
                <div class="font-medium text-gray-900">${user.full_name || user.email}</div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">${user.email}</td>
            <td class="px-6 py-4 text-sm">
                <span class="badge-info">
                    <i class="fas fa-image"></i>
                    ${user.template_count || 0} templates
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
                ${user.last_auth ? new Date(user.last_auth).toLocaleString('fr-FR') : 'Jamais'}
            </td>
            <td class="px-6 py-4 text-sm">
                <span class="badge-${user.is_active ? 'success' : 'error'}">
                    <span class="status-dot ${user.is_active ? 'active' : 'error'}"></span>
                    ${user.is_active ? 'Actif' : 'Inactif'}
                </span>
            </td>
            <td class="px-6 py-4 text-sm">
                <button onclick="viewUserDetail('${user.id}')" class="text-indigo-600 hover:text-indigo-900 mr-3">
                    <i class="fas fa-eye"></i>
                </button>
                <button onclick="removeUserBiometric('${user.id}')" class="text-red-600 hover:text-red-900">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function filterDesktopUsers() {
    const searchTerm = document.getElementById('desktopSearchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#desktopUsersTableBody tr');
    
    rows.forEach(row => {
        const email = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
        const name = row.querySelector('td:nth-child(1)')?.textContent.toLowerCase() || '';
        
        const match = email.includes(searchTerm) || name.includes(searchTerm);
        row.style.display = match ? '' : 'none';
    });
}

async function viewUserDetail(userId) {
    // Implémenter modal de détails utilisateur
    alert('Détails utilisateur: ' + userId);
}

async function removeUserBiometric(userId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer les données biométriques?')) return;

    try {
        const response = await axios.delete(`${API_BASE}/admin/biometric/${userId}/templates`, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);

        if (normalizedData.status === 'success') {
            alert('Données biométriques supprimées');
            loadDesktopUsers();
        } else {
            alert(normalizedData.message || 'Erreur lors de la suppression');
        }
    } catch (error) {
        alert('Erreur lors de la suppression');
    }
}

// ============================================
// AUTHENTICATION LOGS
// ============================================

let currentLogsPage = 0;

function setupLogs() {
    document.getElementById('filterEmail').addEventListener('input', () => {
        currentLogsPage = 0;
        loadAuthLogs();
    });
    
    document.getElementById('filterResult').addEventListener('change', () => {
        currentLogsPage = 0;
        loadAuthLogs();
    });

    document.getElementById('filterType').addEventListener('change', () => {
        currentLogsPage = 0;
        loadAuthLogs();
    });

    document.getElementById('applyFilterBtn').addEventListener('click', () => {
        currentLogsPage = 0;
        loadAuthLogs();
    });

    document.getElementById('prevPageBtn').addEventListener('click', () => {
        currentLogsPage--;
        loadAuthLogs();
    });

    document.getElementById('nextPageBtn').addEventListener('click', () => {
        currentLogsPage++;
        loadAuthLogs();
    });
}

async function loadAuthLogs() {
    try {
        const filters = {
            email: document.getElementById('filterEmail').value,
            result: document.getElementById('filterResult').value,
            auth_type: document.getElementById('filterType').value,
            page: currentLogsPage,
            per_page: 25
        };

        const response = await axios.get(`${API_BASE}/admin/biometric/auth-logs`, {
            params: filters,
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            renderLogsTable(data.logs || []);
            
            // Update pagination
            document.getElementById('prevPageBtn').disabled = currentLogsPage === 0;
            document.getElementById('nextPageBtn').disabled = !data.has_next;
            document.getElementById('paginationInfo').textContent = 
                `Page ${currentLogsPage + 1} / ${data.total_pages || 1}`;
        }
    } catch (error) {
        console.error('Erreur chargement logs:', error);
        document.getElementById('logsTableBody').innerHTML = 
            '<tr><td colspan="7" class="px-6 py-4 text-center text-red-600">Erreur lors du chargement</td></tr>';
    }
}

function renderLogsTable(logs) {
    const tbody = document.getElementById('logsTableBody');
    
    if (!logs.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">Aucun log</td></tr>';
        return;
    }

    tbody.innerHTML = logs.map(log => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm text-gray-900">
                ${new Date(log.timestamp).toLocaleString('fr-FR')}
            </td>
            <td class="px-6 py-4 text-sm text-gray-900">${log.user_email}</td>
            <td class="px-6 py-4 text-sm">
                <span class="badge-${log.success ? 'success' : 'error'}">
                    <i class="fas fa-${log.success ? 'check' : 'times'}-circle"></i>
                    ${log.success ? 'Succès' : 'Échec'}
                </span>
            </td>
            <td class="px-6 py-4 text-sm">
                ${log.similarity_score ? (log.similarity_score * 100).toFixed(1) + '%' : '-'}
            </td>
            <td class="px-6 py-4 text-sm">
                <span class="badge-info">${log.auth_type}</span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">${log.client_ip}</td>
            <td class="px-6 py-4 text-sm">
                <button onclick="showLogDetails('${log.id}')" class="text-indigo-600 hover:text-indigo-900">
                    <i class="fas fa-info-circle"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function showLogDetails(logId) {
    // Implémenter modal de détails du log
    alert('Détails du log: ' + logId);
}

// ============================================
// ERROR ALERTS (Client Desktop)
// ============================================

function setupErrorsMonitoring() {
    // Auto-refresh errors every 30 seconds
    setInterval(loadErrorAlerts, 30000);
}

async function loadErrorAlerts() {
    try {
        const response = await axios.get(`${API_BASE}/admin/biometric/error-alerts`, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            renderErrorAlerts(data.critical_errors || [], data.recent_errors || []);
        }
    } catch (error) {
        console.error('Erreur chargement alertes:', error);
    }
}

function renderErrorAlerts(criticalErrors, recentErrors) {
    // Critical Errors
    const criticalList = document.getElementById('criticalErrorsList');
    if (!criticalErrors.length) {
        criticalList.innerHTML = '<div class="p-6 text-center text-green-600"><i class="fas fa-check-circle mr-2"></i>Aucune erreur critique</div>';
    } else {
        criticalList.innerHTML = criticalErrors.map(error => `
            <div class="alert-error p-4">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-semibold text-red-900">${error.error_type}</h4>
                        <p class="text-sm text-red-800 mt-1">${error.message}</p>
                        <p class="text-xs text-red-700 mt-2">
                            <strong>${error.occurrence_count}</strong> occurrences - 
                            Dernier: ${new Date(error.last_timestamp).toLocaleString('fr-FR')}
                        </p>
                    </div>
                    <span class="badge-error">${error.severity}</span>
                </div>
            </div>
        `).join('');
    }

    // Recent Errors
    const tbody = document.getElementById('errorsTableBody');
    if (!recentErrors.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-8 text-center text-gray-500">Aucune erreur récente</td></tr>';
    } else {
        tbody.innerHTML = recentErrors.map(error => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm text-gray-900">
                    ${new Date(error.timestamp).toLocaleString('fr-FR')}
                </td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">${error.user_email}</td>
                <td class="px-6 py-4 text-sm">
                    <span class="badge-error">${error.error_type}</span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                    ${error.error_message.substring(0, 50)}...
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                    <div class="text-xs">
                        <p>${error.client_info?.os || 'N/A'}</p>
                        <p>${error.client_info?.app_version || 'N/A'}</p>
                    </div>
                </td>
                <td class="px-6 py-4 text-sm">
                    <button onclick="alertUserError('${error.id}')" class="text-blue-600 hover:text-blue-900 mr-3" title="Alerter l'utilisateur">
                        <i class="fas fa-bell"></i>
                    </button>
                    <button onclick="resolveError('${error.id}')" class="text-green-600 hover:text-green-900" title="Marquer résolu">
                        <i class="fas fa-check"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

async function alertUserError(errorId) {
    try {
        const response = await axios.post(`${API_BASE}/admin/biometric/alert-error`, { error_id: errorId }, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });
        const normalizedData = normalizeResponse(response.data);
        if (normalizedData.status === 'success') {
            alert('Alerte envoyée à l\'utilisateur');
        } else {
            alert(normalizedData.message || 'Erreur lors de l\'envoi de l\'alerte');
        }
    } catch (error) {
        alert('Erreur lors de l\'envoi de l\'alerte');
    }
}

async function resolveError(errorId) {
    try {
        const response = await axios.post(`${API_BASE}/admin/biometric/resolve-error`, { error_id: errorId }, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });
        const normalizedData = normalizeResponse(response.data);
        if (normalizedData.status === 'success') {
            loadErrorAlerts();
        } else {
            alert(normalizedData.message || 'Erreur lors de la résolution');
        }
    } catch (error) {
        alert('Erreur lors de la résolution');
    }
}

// ============================================
// ANALYTICS
// ============================================

let authTrendChart = null;
let resultDistributionChart = null;

function setupAnalytics() {
    // Charts will be initialized in loadAnalytics
}

async function loadAnalytics() {
    try {
        const response = await axios.get(`${API_BASE}/admin/biometric/analytics`, {
            headers: { Authorization: `Bearer ${TOKEN}` }
        });

        const normalizedData = normalizeResponse(response.data);
        const data = normalizedData.status === 'success' ? 
            (normalizedData.data || normalizedData) : 
            normalizedData;

        if (normalizedData.status === 'success') {
            renderAnalytics(data);
        }
    } catch (error) {
        console.error('Erreur chargement analytics:', error);
    }
}

function renderAnalytics(data) {
    // Trend Chart
    const trendCtx = document.getElementById('authTrendChart');
    if (authTrendChart) authTrendChart.destroy();
    
    authTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: data.trend_labels || [],
            datasets: [
                {
                    label: 'Authentifications réussies',
                    data: data.trend_success || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Authentifications échouées',
                    data: data.trend_failed || [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });

    // Distribution Chart
    const distCtx = document.getElementById('resultDistributionChart');
    if (resultDistributionChart) resultDistributionChart.destroy();
    
    resultDistributionChart = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: ['Succès', 'Échovés'],
            datasets: [{
                data: [data.success_count || 0, data.failed_count || 0],
                backgroundColor: ['#10b981', '#ef4444'],
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });

    // Error Analysis
    const errorAnalysis = document.getElementById('errorAnalysisList');
    if (data.error_analysis && data.error_analysis.length) {
        errorAnalysis.innerHTML = data.error_analysis.map(err => `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                    <p class="font-medium text-gray-900">${err.error_type}</p>
                    <p class="text-sm text-gray-600">${err.count} occurrences</p>
                </div>
                <span class="text-lg font-bold text-red-600">${((err.count / (data.success_count + data.failed_count)) * 100).toFixed(1)}%</span>
            </div>
        `).join('');
    } else {
        errorAnalysis.innerHTML = '<p class="text-gray-500">Aucune erreur à afficher</p>';
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    const className = {
        'success': 'alert-success',
        'error': 'alert-error',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const icon = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';

    element.innerHTML = `
        <div class="${className}">
            <div class="flex items-start gap-3">
                <i class="fas ${icon} mt-0.5"></i>
                <div>
                    <p class="font-medium">${message}</p>
                </div>
            </div>
        </div>
    `;
    element.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => element.classList.add('hidden'), 4000);
    }
}

// Auto-load dashboard stats every minute
setInterval(loadAdminDashboard, 60000);

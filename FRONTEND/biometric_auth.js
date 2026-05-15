/**
 * Biometric Authentication - User Interface
 * Support: Live capture, Email verification, Desktop Client redirect
 */

const API_BASE = '/api/v1';
let stream = null;
let canvas = null;
let detectionActive = false;
let isDesktopClient = () => navigator.userAgent.includes('BioAccessClient');

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkAuthStatus();
});

function checkAuthStatus() {
    const token = sessionStorage.getItem('token');
    if (token) {
        window.location.href = '/dashboard.html';
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

function setupEventListeners() {
    // Mode selection
    document.getElementById('liveAuthBtn').addEventListener('click', switchToLiveAuth);
    document.getElementById('emailAuthBtn').addEventListener('click', switchToEmailAuth);

    // Navigation
    document.getElementById('backFromLiveBtn').addEventListener('click', backToModeSelection);
    document.getElementById('backFromEmailBtn').addEventListener('click', backToModeSelection);
    document.getElementById('backToEmailBtn').addEventListener('click', () => {
        document.getElementById('codeSection').classList.add('hidden');
        document.getElementById('emailInput').value = '';
        document.getElementById('emailInput').focus();
    });

    // Live capture
    document.getElementById('captureBtn').addEventListener('click', captureLivePhoto);
    document.getElementById('cancelLiveBtn').addEventListener('click', stopLiveAuthView);

    // Email verification
    document.getElementById('sendCodeBtn').addEventListener('click', sendVerificationCode);
    document.getElementById('verifyCodeBtn').addEventListener('click', verifyCode);
    
    // Auto-submit code when 6 digits entered
    document.getElementById('codeInput').addEventListener('input', (e) => {
        if (e.target.value.length === 6) {
            verifyCode();
        }
    });

    // Error handling
    document.getElementById('errorRetryBtn').addEventListener('click', backToModeSelection);
}

// ============================================
// MODE NAVIGATION
// ============================================

function switchToLiveAuth() {
    document.getElementById('modeSelection').classList.add('hidden');
    document.getElementById('liveAuthSection').classList.remove('hidden');
    startLiveCapture();
}

function switchToEmailAuth() {
    document.getElementById('modeSelection').classList.add('hidden');
    document.getElementById('emailAuthSection').classList.remove('hidden');
    document.getElementById('emailInput').focus();
}

function backToModeSelection() {
    document.getElementById('modeSelection').classList.remove('hidden');
    document.getElementById('liveAuthSection').classList.add('hidden');
    document.getElementById('emailAuthSection').classList.add('hidden');
    document.getElementById('successMessage').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
    stopLiveCapture();
}

// ============================================
// LIVE CAPTURE
// ============================================

async function startLiveCapture() {
    try {
        const video = document.getElementById('authVideo');
        stream = await navigator.mediaDevices.getUserMedia({
            video: { 
                facingMode: 'user',
                width: { ideal: 640 },
                height: { ideal: 480 }
            },
            audio: false
        });

        video.srcObject = stream;
        
        // Setup detection canvas
        setupDetectionCanvas();
        
        // Start quality detection
        startQualityDetection();
        
        document.getElementById('cameraStatus').textContent = '🟢 Caméra active';
        
    } catch (error) {
        showError('Impossible d\'accéder à la caméra. Vérifiez les permissions.');
        console.error('Camera error:', error);
    }
}

function setupDetectionCanvas() {
    const video = document.getElementById('authVideo');
    const canvas = document.getElementById('detectionCanvas');
    
    video.addEventListener('loadedmetadata', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
    });
}

function startQualityDetection() {
    detectionActive = true;
    const video = document.getElementById('authVideo');
    let frameCount = 0;

    const detectFrame = () => {
        if (!detectionActive || !stream) return;

        frameCount++;
        
        // Simulate quality detection (in production, use face detection library)
        const quality = Math.random() * 100;
        
        // Simulate better quality when conditions are good
        if (frameCount % 10 === 0) {
            const randomQuality = 40 + Math.random() * 60; // 40-100%
            updateQualityBar(randomQuality);
        }

        setTimeout(detectFrame, 100);
    };

    detectFrame();
}

function updateQualityBar(quality) {
    const qualityPercent = Math.min(100, Math.max(0, quality));
    document.getElementById('qualityValue').textContent = Math.round(qualityPercent) + '%';
    document.getElementById('qualityBar').style.width = qualityPercent + '%';

    // Update hint
    let hint = '';
    if (qualityPercent < 30) {
        hint = '❌ Qualité insuffisante - Meilleure lumière nécessaire';
    } else if (qualityPercent < 60) {
        hint = '⚠️ Qualité moyenne - Repositionnez votre visage';
    } else if (qualityPercent < 80) {
        hint = '✓ Qualité acceptable - Prêt à capturer';
    } else {
        hint = '✓✓ Excellente qualité - Vous êtes prêt!';
    }
    
    document.getElementById('qualityHint').textContent = hint;
}

function stopLiveCapture() {
    detectionActive = false;
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
}

async function captureLivePhoto() {
    if (!stream) {
        showError('Erreur: Caméra non disponible');
        return;
    }

    try {
        const video = document.getElementById('authVideo');
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = video.videoWidth;
        tempCanvas.height = video.videoHeight;
        
        const ctx = tempCanvas.getContext('2d');
        // Mirror the image (undo the video flipping)
        ctx.scale(-1, 1);
        ctx.drawImage(video, -tempCanvas.width, 0);
        
        const imageBase64 = tempCanvas.toDataURL('image/jpeg', 0.85);

        // Show loading
        document.getElementById('captureLoading').classList.remove('hidden');
        document.getElementById('captureBtn').disabled = true;

        // Send to backend for authentication
        await authenticateWithFace(imageBase64, 'live');

    } catch (error) {
        showError('Erreur lors de la capture');
        console.error('Capture error:', error);
        document.getElementById('captureBtn').disabled = false;
        document.getElementById('captureLoading').classList.add('hidden');
    }
}

function stopLiveAuthView() {
    backToModeSelection();
}

// ============================================
// FACE AUTHENTICATION
// ============================================

async function authenticateWithFace(imageBase64, mode = 'live') {
    try {
        const isAdmin = sessionStorage.getItem('isAdmin') === 'true';
        
        // Determine auth type based on client
        const authType = isDesktopClient() ? 'desktop' : (isAdmin ? 'admin' : 'web');

        const response = await axios.post(`${API_BASE}/auth/biometric/authenticate`, {
            image_base64: imageBase64,
            auth_type: authType,
            is_admin: isAdmin
        }, {
            timeout: 30000
        });

        // Normaliser la réponse au nouveau format APIResponse
        let authData = response.data;
        
        // Nouveau format: { status: 'success', data: { access_token, user_id, user_email, user_name } }
        if (authData.status === 'success' && authData.data) {
            authData = authData.data;
        }
        // Ancien format: { success: true, token, user_id, user_email, user_name }
        else if (!authData.success && authData.data) {
            authData = authData.data;
        }
        
        if (authData.success !== false && (authData.token || authData.access_token)) {
            // Store auth data (sessionStorage = same storage as api.js)
            const token = authData.access_token || authData.token;
            sessionStorage.setItem('token', token);
            sessionStorage.setItem('user_id', authData.user_id);
            sessionStorage.setItem('user_email', authData.user_email);
            sessionStorage.setItem('user_name', authData.user_name);

            // Show success
            showSuccess();

            // Redirect based on user type
            setTimeout(() => {
                const redirectUrl = isAdmin ? '/admin_biometric.html' : '/dashboard.html';
                window.location.href = redirectUrl;
            }, 2000);

        } else {
            // Authentication failed - log error for admin
            await logAuthenticationError({
                error_type: 'FACE_NOT_RECOGNIZED',
                message: authData.message || 'Visage non reconnu',
                auth_type: authType,
                image_base64: imageBase64.substring(0, 50) // Just header for size
            });

            showError(authData.message || 'Visage non reconnu. Réessayez.');
        }

    } catch (error) {
        // Network or server error - log for admin
        const errorMessage = error.response?.data?.message || 
                            (error.message === 'timeout of 30000ms exceeded' ? 
                             'Délai d\'attente dépassé' : 
                             'Erreur serveur');

        await logAuthenticationError({
            error_type: 'AUTH_ERROR',
            message: errorMessage,
            auth_type: isDesktopClient() ? 'desktop' : 'web',
            error_details: error.message
        });

        showError(errorMessage);
    } finally {
        document.getElementById('captureLoading').classList.add('hidden');
        document.getElementById('captureBtn').disabled = false;
    }
}

// ============================================
// EMAIL VERIFICATION
// ============================================

async function sendVerificationCode() {
    const email = document.getElementById('emailInput').value.trim();

    if (!email || !email.includes('@')) {
        showError('Veuillez entrer une adresse email valide');
        return;
    }

    try {
        document.getElementById('sendCodeBtn').disabled = true;
        document.getElementById('sendCodeBtn').innerHTML = 
            '<i class="fas fa-spinner fa-spin mr-2"></i>Envoi en cours...';

        const response = await axios.post(`${API_BASE}/auth/send-verification-code`, {
            email: email,
            auth_type: isDesktopClient() ? 'desktop' : 'web'
        });

        // Normaliser la réponse au nouveau format APIResponse
        let responseData = response.data;
        if (response.data.status === 'success' && response.data.data) {
            responseData = response.data.data;
        }

        if (responseData.success !== false || response.status === 200) {
            // Show code input section
            document.getElementById('codeSection').classList.remove('hidden');
            document.getElementById('codeInput').focus();
            
            // Log this attempt
            logAuthAttempt('email_code_sent', email, 'success');
        } else {
            showError(responseData.message || 'Erreur lors de l\'envoi du code');
        }

    } catch (error) {
        const message = error.response?.data?.message || 'Erreur lors de l\'envoi du code';
        showError(message);
        logAuthAttempt('email_code_send_failed', document.getElementById('emailInput').value, 'failed', message);
    } finally {
        document.getElementById('sendCodeBtn').disabled = false;
        document.getElementById('sendCodeBtn').innerHTML = 
            '<i class="fas fa-send mr-2"></i>Envoyer un code de vérification';
    }
}

async function verifyCode() {
    const email = document.getElementById('emailInput').value.trim();
    const code = document.getElementById('codeInput').value.trim();

    if (!code || code.length !== 6) {
        showError('Veuillez entrer un code à 6 chiffres');
        return;
    }

    try {
        document.getElementById('verifyCodeBtn').disabled = true;
        document.getElementById('verifyCodeBtn').innerHTML = 
            '<i class="fas fa-spinner fa-spin mr-2"></i>Vérification...';

        const response = await axios.post(`${API_BASE}/auth/verify-code`, {
            email: email,
            code: code,
            auth_type: isDesktopClient() ? 'desktop' : 'web'
        });

        // Normaliser la réponse au nouveau format APIResponse
        let responseData = response.data;
        if (response.data.status === 'success' && response.data.data) {
            responseData = response.data.data;
        }

        if (responseData.success !== false || response.status === 200) {
            const token = responseData.access_token || responseData.token;
            sessionStorage.setItem('token', token);
            sessionStorage.setItem('user_id', responseData.user_id);
            sessionStorage.setItem('user_email', responseData.user_email);

            logAuthAttempt('email_verification', email, 'success');
            showSuccess();

            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 2000);

        } else {
            showError(response.data.message || 'Code invalide');
            logAuthAttempt('email_verification_failed', email, 'failed', response.data.message);
        }

    } catch (error) {
        const message = error.response?.data?.message || 'Erreur lors de la vérification';
        showError(message);
        logAuthAttempt('email_verification_error', email, 'failed', message);
    } finally {
        document.getElementById('verifyCodeBtn').disabled = false;
        document.getElementById('verifyCodeBtn').innerHTML = 
            '<i class="fas fa-check mr-2"></i>Vérifier';
    }
}

// ============================================
// ERROR LOGGING FOR ADMIN
// ============================================

async function logAuthenticationError(errorData) {
    try {
        const clientInfo = {
            user_agent: navigator.userAgent,
            platform: navigator.platform,
            screen_resolution: window.screen.width + 'x' + window.screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timestamp: new Date().toISOString()
        };

        if (isDesktopClient()) {
            clientInfo.app_type = 'desktop_client';
            clientInfo.version = localStorage.getItem('app_version') || 'unknown';
        }

        // Post error log to admin dashboard
        await axios.post(`${API_BASE}/admin/biometric/log-client-error`, {
            error_type: errorData.error_type,
            error_message: errorData.message,
            auth_type: errorData.auth_type,
            client_info: clientInfo,
            additional_details: errorData.error_details
        }).catch(err => {
            // Silent fail - don't affect user experience
            console.error('Error logging failed:', err);
        });

    } catch (error) {
        console.error('Failed to log error:', error);
    }
}

async function logAuthAttempt(attemptType, email, status, details = null) {
    try {
        await axios.post(`${API_BASE}/admin/biometric/log-auth-attempt`, {
            attempt_type: attemptType,
            email: email,
            status: status,
            auth_type: isDesktopClient() ? 'desktop' : 'web',
            details: details,
            timestamp: new Date().toISOString()
        }).catch(err => console.error('Attempt logging failed:', err));
    } catch (error) {
        console.error('Failed to log attempt:', error);
    }
}

// ============================================
// UI HELPERS
// ============================================

function showSuccess() {
    document.getElementById('modeSelection').classList.add('hidden');
    document.getElementById('liveAuthSection').classList.add('hidden');
    document.getElementById('emailAuthSection').classList.add('hidden');
    document.getElementById('errorMessage').classList.add('hidden');
    document.getElementById('successMessage').classList.remove('hidden');
    
    stopLiveCapture();
}

function showError(message) {
    document.getElementById('errorText').textContent = message;
    document.getElementById('errorMessage').classList.remove('hidden');
    document.getElementById('successMessage').classList.add('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (document.getElementById('errorMessage').classList.contains('hidden') === false) {
            backToModeSelection();
        }
    }, 5000);
}

// ============================================
// RESPONSIVE DESIGN
// ============================================

// Handle orientation change for mobile
window.addEventListener('orientationchange', () => {
    if (stream) {
        // Restart camera on orientation change
        stopLiveCapture();
        setTimeout(startLiveCapture, 500);
    }
});

// Handle visibility change
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopLiveCapture();
    } else if (detectionActive) {
        startLiveCapture();
    }
});

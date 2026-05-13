/**
 * Configuration Frontend - BioAccess Secure
 * Ce fichier doit être chargé AVANT login.html et autres pages
 * 
 * IMPORTANT: Remplacez les valeurs par vos vraies configurations
 */

// Configuration globale
window.CONFIG = {
    // ========================================
    // API Configuration
    // ========================================
    API_URL: 'http://localhost:5000/api/v1',
    
    // ========================================
    // Google OAuth Configuration
    // ========================================
    // Obtenez votre Client ID depuis https://console.cloud.google.com/
    // 1. Créer un projet
    // 2. Activer Google+ API
    // 3. Créer une "OAuth 2.0 Web Application"
    // 4. Ajouter les URIs:
    //    - Origines JavaScript: http://localhost:5000
    //    - URIs de redirection: http://localhost:5000/api/v1/auth/google
    // 5. Copier le Client ID (avant le .apps.googleusercontent.com)
    //
    GOOGLE_CLIENT_ID: 'YOUR_CLIENT_ID_HERE.apps.googleusercontent.com',
    
    // ========================================
    // Autres configurations
    // ========================================
    APP_NAME: 'BioAccess Secure',
    APP_VERSION: '2.0.0',
    ENVIRONMENT: 'development', // 'development', 'staging', 'production'
    
    // Timeouts
    DEFAULT_TIMEOUT: 10000, // 10 secondes
    API_TIMEOUT: 30000,     // 30 secondes
    
    // Logging
    DEBUG_MODE: true,
    LOG_LEVEL: 'info' // 'debug', 'info', 'warn', 'error'
};

// Validation des configurations critiques
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier le Client ID Google
    if (window.CONFIG.GOOGLE_CLIENT_ID === 'YOUR_CLIENT_ID_HERE.apps.googleusercontent.com') {
        console.warn('⚠️  WARNING: GOOGLE_CLIENT_ID n\'est pas configuré!');
        console.warn('Veuillez:');
        console.warn('1. Créer un projet sur https://console.cloud.google.com/');
        console.warn('2. Activer Google+ API');
        console.warn('3. Créer une application OAuth 2.0 Web');
        console.warn('4. Remplacer YOUR_CLIENT_ID_HERE dans config.js');
    }
    
    // Vérifier l'API URL
    if (window.CONFIG.API_URL.includes('localhost') && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        console.warn('⚠️  WARNING: API_URL pointe vers localhost mais le frontend est sur', window.location.hostname);
    }
});

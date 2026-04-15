// api.js - Gestion centralisée des appels API

const API = {
    baseURL: window.API_URL || window.CONFIG?.API_URL || 'http://localhost:5000/api',
    
    // Headers par défaut
    headers() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        };
    },
    
    // GET request
    async get(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'GET',
            headers: this.headers()
        });
        return this.handleResponse(response);
    },
    
    // POST request
    async post(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: this.headers(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    // PUT request
    async put(endpoint, data) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'PUT',
            headers: this.headers(),
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    // DELETE request
    async delete(endpoint) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'DELETE',
            headers: this.headers()
        });
        return this.handleResponse(response);
    },
    
    // Gestion des réponses - Normalise le nouveau format APIResponse
    async handleResponse(response) {
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token expiré
                localStorage.removeItem('token');
                window.location.href = 'login.html';
            }
            // Nouveau format APIResponse
            const errorMessage = data.message || data.error || 'Erreur serveur';
            throw new Error(errorMessage);
        }
        
        // Normaliser la réponse au nouveau format APIResponse
        // Format attendu: { status, code, timestamp, message, data, error_code }
        return this.normalizeResponse(data);
    },
    
    // Normalise les réponses au format APIResponse
    normalizeResponse(data) {
        // Si déjà au nouveau format, retourner tel quel
        if (data.status && (data.status === 'success' || data.status === 'error')) {
            return data;
        }
        
        // Sinon, convertir ancien format vers nouveau format pour backward compatibility
        // Ancien format: { access_token, user, ... } ou { success, token, ... }
        return {
            status: data.success !== false ? 'success' : 'error',
            code: data.code || 200,
            timestamp: data.timestamp || new Date().toISOString(),
            message: data.message || (data.success ? 'Succès' : 'Erreur'),
            data: data.data || data,  // Le reste des données
            error_code: data.error_code || null
        };
    },
    
    // Upload de fichiers (pour enrôlement)
    async upload(endpoint, formData) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });
        return this.handleResponse(response);
    }
};

// Exemple d'utilisation:
// const users = await API.get('/users');
// await API.post('/users', { nom: 'Dupont', ... });
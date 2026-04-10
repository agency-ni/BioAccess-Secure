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
    
    // Gestion des réponses
    async handleResponse(response) {
        if (!response.ok) {
            if (response.status === 401) {
                // Token expiré
                localStorage.removeItem('token');
                window.location.href = 'login.html';
            }
            const error = await response.json();
            throw new Error(error.message || 'Erreur serveur');
        }
        return response.json();
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
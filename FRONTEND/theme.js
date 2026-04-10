/**
 * Theme Manager - Gestion du mode sombre/clair
 * Gère le stockage et l'application des thèmes
 */

class ThemeManager {
    constructor() {
        this.STORAGE_KEY = 'bioAccess-theme';
        this.DARK_CLASS = 'dark-mode';
        this.init();
    }

    init() {
        // Charger le thème sauvegardé ou utiliser la préférence système
        const savedTheme = localStorage.getItem(this.STORAGE_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        const isDark = savedTheme ? savedTheme === 'dark' : prefersDark;
        
        if (isDark) {
            this.enableDarkMode();
        } else {
            this.enableLightMode();
        }
        
        // Écoute les changements de préférence système
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(this.STORAGE_KEY)) {
                e.matches ? this.enableDarkMode() : this.enableLightMode();
            }
        });
    }

    enableDarkMode() {
        document.documentElement.classList.add(this.DARK_CLASS);
        document.body.classList.add('bg-gray-900', 'text-white');
        localStorage.setItem(this.STORAGE_KEY, 'dark');
        this.updateThemeButton('dark');
        this.applyDarkTheme();
    }

    enableLightMode() {
        document.documentElement.classList.remove(this.DARK_CLASS);
        document.body.classList.remove('bg-gray-900', 'text-white');
        localStorage.setItem(this.STORAGE_KEY, 'light');
        this.updateThemeButton('light');
        this.applyLightTheme();
    }

    toggle() {
        const isDark = document.documentElement.classList.contains(this.DARK_CLASS);
        isDark ? this.enableLightMode() : this.enableDarkMode();
    }

    updateThemeButton(theme) {
        const button = document.getElementById('themeToggleBtn');
        if (!button) return;
        
        if (theme === 'dark') {
            button.innerHTML = '<i class="fas fa-sun"></i>';
            button.title = 'Mode clair';
        } else {
            button.innerHTML = '<i class="fas fa-moon"></i>';
            button.title = 'Mode sombre';
        }
    }

    applyDarkTheme() {
        // Ajouter les styles dynamiques pour le mode sombre
        let style = document.getElementById('darkThemeStyles');
        if (!style) {
            style = document.createElement('style');
            style.id = 'darkThemeStyles';
            document.head.appendChild(style);
        }

        style.textContent = `
            :root.dark-mode {
                --color-bg-primary: #111827;
                --color-bg-secondary: #1f2937;
                --color-text-primary: #f3f4f6;
                --color-text-secondary: #d1d5db;
                --color-border: #374151;
            }

            :root.dark-mode body {
                background-color: #111827 !important;
                color: #f3f4f6 !important;
            }

            :root.dark-mode .bg-white {
                background-color: #1f2937 !important;
                color: #f3f4f6 !important;
            }

            :root.dark-mode .bg-gray-50 {
                background-color: #1f2937 !important;
            }

            :root.dark-mode .bg-gray-100 {
                background-color: #374151 !important;
            }

            :root.dark-mode .bg-gray-200 {
                background-color: #4b5563 !important;
            }

            :root.dark-mode .border {
                border-color: #374151 !important;
            }

            :root.dark-mode .border-b {
                border-bottom-color: #374151 !important;
            }

            :root.dark-mode .border-r {
                border-right-color: #374151 !important;
            }

            :root.dark-mode .border-t {
                border-top-color: #374151 !important;
            }

            :root.dark-mode .text-gray-800 {
                color: #f3f4f6 !important;
            }

            :root.dark-mode .text-gray-700 {
                color: #e5e7eb !important;
            }

            :root.dark-mode .text-gray-600 {
                color: #d1d5db !important;
            }

            :root.dark-mode .text-gray-500 {
                color: #a6adb8 !important;
            }

            :root.dark-mode .text-gray-400 {
                color: #9ca3af !important;
            }

            :root.dark-mode .text-gray-900 {
                color: #f3f4f6 !important;
            }

            :root.dark-mode .placeholder-gray-400::placeholder {
                color: #9ca3af !important;
            }

            :root.dark-mode input,
            :root.dark-mode textarea,
            :root.dark-mode select {
                background-color: #374151 !important;
                color: #f3f4f6 !important;
                border-color: #4b5563 !important;
            }

            :root.dark-mode input::placeholder,
            :root.dark-mode textarea::placeholder {
                color: #9ca3af !important;
            }

            :root.dark-mode .shadow-sm {
                box-shadow: 0 1px 2px 0 rgba(0,0,0,0.5) !important;
            }

            :root.dark-mode .shadow {
                box-shadow: 0 1px 3px 0 rgba(0,0,0,0.6) !important;
            }

            :root.dark-mode .shadow-lg {
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.7) !important;
            }

            :root.dark-mode .shadow-2xl {
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8) !important;
            }

            :root.dark-mode .hover\\:bg-gray-50:hover {
                background-color: #374151 !important;
            }

            :root.dark-mode .hover\\:bg-gray-100:hover {
                background-color: #4b5563 !important;
            }

            :root.dark-mode .divide-gray-200 > * + * {
                border-color: #374151 !important;
            }

            :root.dark-mode .ring-gray-300 {
                --tw-ring-color: #374151 !important;
            }

            :root.dark-mode .focus\\:ring-offset-gray-100:focus {
                --tw-ring-offset-color: #374151 !important;
            }

            :root.dark-mode .from-gray-100 {
                --tw-gradient-from: #374151 !important;
                --tw-gradient-to: rgb(55 65 81 / 0) !important;
                --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to) !important;
            }

            :root.dark-mode .to-gray-100 {
                --tw-gradient-to: #374151 !important;
            }

            :root.dark-mode .bg-gradient-to-r {
                background-image: linear-gradient(to right, var(--tw-gradient-stops)) !important;
            }

            :root.dark-mode .navbar {
                background-color: #1f2937 !important;
                border-bottom-color: #374151 !important;
            }

            :root.dark-mode .sidebar {
                background-color: #1f2937 !important;
                box-shadow: 2px 0 10px rgba(0,0,0,0.5) !important;
            }

            :root.dark-mode .sidebar-item {
                color: #d1d5db !important;
            }

            :root.dark-mode .sidebar-item:hover:not(.active) {
                background-color: #374151 !important;
                border-left-color: #6b7280 !important;
            }

            :root.dark-mode .card,
            :root.dark-mode .bg-blue-50,
            :root.dark-mode .bg-green-50,
            :root.dark-mode .bg-red-50,
            :root.dark-mode .bg-yellow-50 {
                background-color: #1f2937 !important;
            }

            :root.dark-mode .text-red-600 {
                color: #f87171 !important;
            }

            :root.dark-mode .text-green-600 {
                color: #4ade80 !important;
            }

            :root.dark-mode .text-blue-600 {
                color: #60a5fa !important;
            }

            :root.dark-mode .text-yellow-600 {
                color: #facc15 !important;
            }

            :root.dark-mode table {
                color: #f3f4f6 !important;
            }

            :root.dark-mode thead {
                background-color: #374151 !important;
            }

            :root.dark-mode tbody tr:hover {
                background-color: #374151 !important;
            }

            :root.dark-mode .modal,
            :root.dark-mode .dropdown {
                background-color: #1f2937 !important;
            }

            :root.dark-mode video {
                background-color: #000 !important;
            }

            :root.dark-mode .bg-indigo-600 {
                background-color: #4f46e5 !important;
            }

            :root.dark-mode .hover\\:bg-indigo-700:hover {
                background-color: #4338ca !important;
            }

            :root.dark-mode .text-indigo-600 {
                color: #818cf8 !important;
            }

            :root.dark-mode .text-white {
                color: #f3f4f6 !important;
            }

            :root.dark-mode .bg-red-500,
            :root.dark-mode .bg-red-600 {
                background-color: #dc2626 !important;
            }

            :root.dark-mode .bg-green-100,
            :root.dark-mode .bg-green-600 {
                background-color: #15803d !important;
            }

            :root.dark-mode .text-red-700,
            :root.dark-mode .text-red-800,
            :root.dark-mode .text-red-900 {
                color: #fca5a5 !important;
            }

            :root.dark-mode .text-green-700,
            :root.dark-mode .text-green-800 {
                color: #86efac !important;
            }

            :root.dark-mode .text-blue-700,
            :root.dark-mode .text-blue-800 {
                color: #93c5fd !important;
            }

            :root.dark-mode .bg-yellow-50 {
                background-color: #7c2d12 !important;
            }

            :root.dark-mode .text-yellow-700,
            :root.dark-mode .text-yellow-800 {
                color: #fef08a !important;
            }

            :root.dark-mode .focus\\:ring-indigo-500:focus {
                --tw-ring-color: #6366f1 !important;
            }

            :root.dark-mode .focus\\:border-indigo-500:focus {
                border-color: #6366f1 !important;
            }

            :root.dark-mode hr {
                border-color: #374151 !important;
            }

            :root.dark-mode .space-y-2 > * + * {
                margin-top: 0.5rem !important;
            }

            :root.dark-mode code,
            :root.dark-mode pre {
                background-color: #1f2937 !important;
                color: #f3f4f6 !important;
            }

            :root.dark-mode .spinner {
                border-color: #374151 !important;
                border-right-color: #6366f1 !important;
            }

            :root.dark-mode .badge,
            :root.dark-mode .tag {
                background-color: #374151 !important;
                color: #f3f4f6 !important;
            }

            :root.dark-mode .alert {
                background-color: #1f2937 !important;
                border-color: #374151 !important;
                color: #f3f4f6 !important;
            }

            :root.dark-mode .btn,
            :root.dark-mode button {
                transition: all 0.3s ease !important;
            }

            :root.dark-mode .disabled,
            :root.dark-mode :disabled {
                opacity: 0.5 !important;
            }

            :root.dark-mode .scrollbar-gray-400::-webkit-scrollbar {
                background-color: #1f2937 !important;
            }

            :root.dark-mode .scrollbar-gray-400::-webkit-scrollbar-track {
                background-color: #111827 !important;
            }

            :root.dark-mode .scrollbar-gray-400::-webkit-scrollbar-thumb {
                background-color: #4b5563 !important;
            }

            :root.dark-mode .glass-effect {
                background: rgba(31, 41, 55, 0.8) !important;
                backdrop-filter: blur(10px) !important;
            }

            :root.dark-mode .text-center {
                color: #f3f4f6 !important;
            }

            :root.dark-mode .font-medium {
                color: #e5e7eb !important;
            }

            :root.dark-mode .font-bold {
                color: #f3f4f6 !important;
            }

            /* BADGES - Contraste fort avec couleurs complémentaires */
            :root.dark-mode .bg-red-100 {
                background-color: #7f1d1d !important;
            }

            :root.dark-mode .text-red-700,
            :root.dark-mode .text-red-800 {
                color: #fca5a5 !important;
            }

            :root.dark-mode .bg-yellow-100 {
                background-color: #78350f !important;
            }

            :root.dark-mode .text-yellow-700,
            :root.dark-mode .text-yellow-800 {
                color: #fcd34d !important;
            }

            :root.dark-mode .bg-green-100 {
                background-color: #065f46 !important;
            }

            :root.dark-mode .text-green-700,
            :root.dark-mode .text-green-800 {
                color: #86efac !important;
            }

            :root.dark-mode .bg-blue-100 {
                background-color: #1e3a8a !important;
            }

            :root.dark-mode .text-blue-700,
            :root.dark-mode .text-blue-800 {
                color: #93c5fd !important;
            }

            :root.dark-mode .bg-indigo-100 {
                background-color: #312e81 !important;
            }

            :root.dark-mode .text-indigo-600,
            :root.dark-mode .text-indigo-700 {
                color: #a5b4fc !important;
            }

            :root.dark-mode .bg-purple-100 {
                background-color: #3b1f47 !important;
            }

            :root.dark-mode .text-purple-600,
            :root.dark-mode .text-purple-700 {
                color: #d9a5ff !important;
            }

            :root.dark-mode .badge-success {
                background-color: #065f46 !important;
                color: #86efac !important;
            }

            :root.dark-mode .badge-error {
                background-color: #7f1d1d !important;
                color: #fca5a5 !important;
            }

            :root.dark-mode .badge-pending {
                background-color: #78350f !important;
                color: #fcd34d !important;
            }

            :root.dark-mode .badge-info {
                background-color: #1e3a8a !important;
                color: #93c5fd !important;
            }
        `;
    }

    applyLightTheme() {
        const style = document.getElementById('darkThemeStyles');
        if (style) {
            style.textContent = '';
        }
    }

    isDarkMode() {
        return document.documentElement.classList.contains(this.DARK_CLASS);
    }

    getCurrentTheme() {
        return this.isDarkMode() ? 'dark' : 'light';
    }
}

// Initialiser le gestionnaire de thème au chargement du DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}

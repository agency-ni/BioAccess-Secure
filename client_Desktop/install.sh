#!/bin/bash

# Script d'installation pour Linux/Mac
# BioAccess Secure Client Desktop

clear
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║     🔐 BioAccess Secure - Installation Wizard          ║"
echo "║     Client Desktop v1.0                                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Vérifier Python
echo "🔍 Vérification de Python..."
python_version=$(python3 --version 2>&1)

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    echo ""
    echo "Installation:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  macOS: brew install python3"
    exit 1
fi

echo "✅ $python_version trouvé"
echo ""

# Créer venv
echo "📦 Création de l'environnement virtuel..."

if [ -d "venv" ]; then
    echo "   ⚠️  Environnement existant détecté"
    read -p "   Réinitialiser? (y/n) [n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi

echo "✅ Environnement virtuel créé"
echo ""

# Activer venv
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
echo "✅ Environnement activé"
echo ""

# Mettre à jour pip
echo "Mise à jour de pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ Pip mis à jour"
echo ""

# Installer requirements
echo "📚 Installation des dépendances..."
echo "   (cela peut prendre 2-3 minutes...)"
echo ""

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

echo ""
echo "✅ Dépendances installées"
echo ""

# Créer .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Fichier .env créé"
    fi
fi
echo ""

# Créer répertoires
mkdir -p logs
mkdir -p temp
echo "✅ Répertoires créés"
echo ""

# Rendre les scripts exécutables
chmod +x main.py test_api.py install.py 2>/dev/null
echo "✅ Scripts exécutables"
echo ""

echo "╔════════════════════════════════════════════════════════╗"
echo "║              ✅ Installation réussie!                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Prochaines étapes:"
echo ""
echo "1️⃣  Éditer la configuration:"
echo "    nano .env"
echo "    # Vérifier API_BASE_URL et autres paramètres"
echo ""
echo "2️⃣  Démarrer le serveur backend (terminal séparé):"
echo "    cd BACKEND"
echo "    python3 run.py"
echo ""
echo "3️⃣  Lancer l'application:"
echo "    python main.py"
echo ""
echo "💡 Commandes utiles:"
echo ""
echo "    • Tester l'API:"
echo "      python test_api.py"
echo ""
echo "    • Voir les logs:"
echo "      tail -f logs/app.log"
echo ""
echo "📖 Documentation:"
echo "    • README.md - Documentation complète"
echo "    • QUICKSTART.md - Guide rapide"
echo ""
echo "🚀 C'est prêt! Bon test!"
echo ""

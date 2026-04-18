#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════╗
# ║  BioAccess Secure - Installation du Client Desktop             ║
# ║  Linux / macOS - Installation Automatique                       ║
# ╚══════════════════════════════════════════════════════════════════╝

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║         BioAccess Secure - Installation du Client Desktop       ║"
echo "║                   Installation Automatique                       ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier Python
echo "📋 Étape 1: Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "❌ ERREUR: Python 3 n'est pas installé"
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Sur macOS, installez Python avec:"
        echo "  brew install python3"
    else
        echo "Sur Linux, installez Python avec:"
        echo "  sudo apt-get install python3 python3-pip"
    fi
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python trouvé: $PYTHON_VERSION"
echo ""

# Créer dossiers nécessaires
echo "📋 Étape 2: Préparation des dossiers..."
mkdir -p logs
echo "✅ Dossiers prêts"
echo ""

# Installer dépendances
echo "📋 Étape 3: Installation des dépendances (cela peut prendre 2-3 minutes)..."
echo ""

python3 -m pip install --upgrade pip > /dev/null 2>&1
python3 -m pip install opencv-python requests pyaudio sounddevice soundfile scipy pillow cryptography -q

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    echo "Contactez l'administrateur: support@bioaccess.secure"
    exit 1
fi

echo "✅ Dépendances installées avec succès"
echo ""

# Vérifier configuration
echo "📋 Étape 4: Configuration de base..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
API_SERVER=http://localhost:5000
API_PREFIX=/api/v1
DEBUG=false
EOF
    echo "✅ Fichier de configuration créé"
else
    echo "✅ Configuration trouvée"
fi
echo ""

# Rendre exécutable les scripts (si nécessaire)
chmod +x biometric/*.py 2>/dev/null
chmod +x *.py 2>/dev/null

# Résumé
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║  ✅ INSTALLATION RÉUSSIE                                        ║"
echo "║                                                                  ║"
echo "║  Prochaines étapes:                                             ║"
echo "║  1. Lancez le client:                                           ║"
echo "║     python3 -m biometric.examples_quickstart                    ║"
echo "║                                                                  ║"
echo "║  OU                                                              ║"
echo "║                                                                  ║"
echo "║  1. Double-cliquez sur l'icône BioAccess (si disponible)        ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

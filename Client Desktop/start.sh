#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════╗
# ║  BioAccess Secure - Démarrage du Client Desktop               ║
# ║  Linux / macOS                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

clear
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║         BioAccess Secure - Démarrage du Client Desktop          ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier Python
echo "🔍 Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python n'est pas installé!"
    echo ""
    echo "Solution:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  1. Installez Homebrew depuis https://brew.sh"
        echo "  2. Exécutez: brew install python3"
    else
        echo "  1. Exécutez: sudo apt-get install python3 python3-pip"
    fi
    echo "  2. Redémarrez votre ordinateur"
    echo "  3. Relancez ce script"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python trouvé: $PYTHON_VERSION"
echo ""

# Vérifier dossiers
echo "🔍 Vérification de la configuration..."
mkdir -p logs

if [ ! -f ".env" ]; then
    echo "⚠️  Configuration non trouvée, création..."
    cat > .env << 'EOF'
API_SERVER=http://localhost:5000
API_PREFIX=/api/v1
DEBUG=false
EOF
    echo "✅ Configuration créée"
else
    echo "✅ Configuration trouvée"
fi
echo ""

# Vérifier dépendances
echo "🔍 Vérification des dépendances..."
python3 -c "import cv2; import sounddevice; import soundfile; import scipy" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "⚠️  Certaines dépendances manquent!"
    echo ""
    echo "Installation automatique des dépendances..."
    python3 -m pip install --upgrade pip > /dev/null 2>&1
    python3 -m pip install opencv-python requests pyaudio sounddevice soundfile scipy pillow cryptography -q
    
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de l'installation des dépendances"
        exit 1
    fi
    echo "✅ Dépendances installées"
else
    echo "✅ Toutes les dépendances sont présentes"
fi
echo ""

# Démarrage
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ Tout est prêt! Démarrage du client...                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

python3 -m biometric.examples_quickstart

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erreur lors du démarrage de l'application"
    echo "Contactez le support: support@bioaccess.secure"
    exit 1
fi

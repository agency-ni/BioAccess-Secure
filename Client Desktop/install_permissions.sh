#!/bin/bash

################################################################################
# Script d'installation pour BioAccess Secure - Linux
# Configuration automatique des déperphériques biométriques
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================================"
echo "  Installation - BioAccess Secure (Linux)"
echo "  Configuration des périphériques biométriques"
echo "========================================================"
echo -e "${NC}"

# Déterminer le gestionnaire de paquets
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    echo -e "${GREEN}✅ Gestionnaire: apt${NC}"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo -e "${GREEN}✅ Gestionnaire: dnf${NC}"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    echo -e "${GREEN}✅ Gestionnaire: pacman${NC}"
else
    echo -e "${RED}❌ Gestionnaire de paquets non supporté${NC}"
    exit 1
fi

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python n'est pas installé${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python détecté:$(python3 --version)${NC}"

# Créer le dossier logs
mkdir -p logs
echo -e "${GREEN}✅ Dossier logs créé${NC}"

echo -e "\n${BLUE}📦 Installation des dépendances système...${NC}"

case $PKG_MANAGER in
    apt-get)
        echo "Mise à jour de apt..."
        sudo apt-get update
        echo "Installation des paquets..."
        sudo apt-get install -y \
            python3-pip \
            python3-dev \
            libopencv-dev \
            python3-opencv \
            libasound2-dev \
            portaudio19-dev
        ;;
    dnf)
        echo "Installation des paquets..."
        sudo dnf install -y \
            python3-pip \
            python3-devel \
            opencv-devel \
            opencv-python \
            alsa-lib-devel \
            portaudio-devel
        ;;
    pacman)
        echo "Installation des paquets..."
        sudo pacman -Sy --noconfirm \
            python-pip \
            opencv \
            portaudio \
            alsa-lib
        ;;
esac

echo -e "\n${BLUE}📦 Installation des modules Python...${NC}"

python3 -m pip install --upgrade pip

echo "📷 Installation OpenCV..."
python3 -m pip install opencv-python

echo "🎤 Installation sounddevice, soundfile et scipy..."
python3 -m pip install sounddevice soundfile scipy numpy

echo -e "\n${BLUE}🔐 Configuration des groupes système...${NC}"

CURRENT_USER=$(whoami)
echo -e "Utilisateur courant: ${YELLOW}$CURRENT_USER${NC}"

# Ajouter aux groupes vidéo et audio
echo "Ajout aux groupes video et audio..."
sudo usermod -a -G video "$CURRENT_USER"
sudo usermod -a -G audio "$CURRENT_USER"

echo -e "\n${YELLOW}⚠️  IMPORTANT:${NC}"
echo "Pour que les changements de groupe prennent effet, vous devez:"
echo ""
echo "Option 1: Se reconnecter à la session"
echo "Option 2: Exécuter cette commande maintenant:"
echo -e "${BLUE}newgrp video && newgrp audio${NC}"
echo ""

read -p "Voulez-vous continuer? (oui/non): " continue_response
if [ "$continue_response" != "oui" ] && [ "$continue_response" != "o" ]; then
    echo "Reconnectez-vous d'abord!"
    exit 0
fi

echo -e "\n${BLUE}========================================================"
echo "  ✅ Installation terminée!"
echo "========================================================${NC}"
echo ""
echo "Prochaines étapes:"
echo ""
echo "1. Lancez le diagnostic:"
echo -e "   ${BLUE}python3 device_diagnostic.py${NC}"
echo ""
echo "2. Puis configurez les permissions:"
echo -e "   ${BLUE}python3 device_setup.py${NC}"
echo ""
echo "3. Suivez les instructions à l'écran"
echo ""

#!/bin/bash

################################################################################
# Lanceur d'installation - Setup universel
# BioAccess Secure - Linux/macOS
# Donnez les permissions: chmod +x SETUP_LINUX_MAC.sh
# Puis exécutez: ./SETUP_LINUX_MAC.sh
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "========================================"
echo "  Installation - BioAccess Secure"
echo "  Setup universel - Linux/macOS"
echo "========================================"
echo -e "${NC}"

# Vérifier Python
echo -e "${BLUE}1️⃣  Vérification de Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python n'est pas installé${NC}"
    echo ""
    echo "Installation:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# Créer le dossier logs
echo -e "\n${BLUE}2️⃣  Création du dossier logs...${NC}"
mkdir -p logs
echo -e "${GREEN}✅ Dossier logs créé${NC}"

# Lancer le setup
echo -e "\n${BLUE}3️⃣  Lancement de l'installation...${NC}"
echo ""

python3 setup.py

echo -e "\n${GREEN}✅ Installation terminée${NC}"

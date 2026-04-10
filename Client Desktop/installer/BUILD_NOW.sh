#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clear screen
clear

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║  🏗️  BIOACCESS SECURE - CONSTRUCTION EN COURS                         ║"
echo "║  Construction + Packaging automatique                                 ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo -e "${BLUE}1️⃣  Vérification de l'environnement...${NC}"

if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ ERREUR: Python n'est pas installé${NC}"
        echo ""
        echo "Solution:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "  macOS:"
            echo "    brew install python3"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "  Linux (Ubuntu/Debian):"
            echo "    sudo apt-get install python3 python3-pip"
            echo "  Linux (Fedora/RHEL):"
            echo "    sudo dnf install python3 python3-pip"
        fi
        echo ""
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}   ✅ ${PYTHON_VERSION}${NC}"

# Check required files
echo ""
echo -e "${BLUE}2️⃣  Vérification des fichiers...${NC}"

for file in "quickstart_build.py" "../device_diagnostic.py" "../device_setup.py" "../../setup.py"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}   ❌ Fichier manquant: $file${NC}"
        echo ""
        exit 1
    fi
    filename=$(basename "$file")
    echo -e "${GREEN}   ✅ $filename trouvé${NC}"
done

# Check PyInstaller
echo ""
echo -e "${BLUE}3️⃣  Vérification de PyInstaller...${NC}"

if ! $PYTHON_CMD -m pip show pyinstaller > /dev/null 2>&1; then
    echo -e "${YELLOW}   ⚠️  PyInstaller non installé${NC}"
    echo -e "${YELLOW}   📥 Installation en cours...${NC}"
    
    if ! $PYTHON_CMD -m pip install pyinstaller -q; then
        echo -e "${RED}❌ Impossible d'installer PyInstaller${NC}"
        echo ""
        exit 1
    fi
    echo -e "${GREEN}   ✅ PyInstaller installé${NC}"
else
    echo -e "${GREEN}   ✅ PyInstaller disponible${NC}"
fi

# Start build
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo -e "${BLUE} 🚀 DÉMARRAGE DE LA CONSTRUCTION${NC}"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Cela peut prendre 15-25 minutes selon votre système..."
echo "Veuillez patienter, traitement en cours..."
echo ""

# Run quickstart_build.py
$PYTHON_CMD quickstart_build.py
BUILD_STATUS=$?

echo ""
echo "════════════════════════════════════════════════════════════════════════"

if [ $BUILD_STATUS -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║  ✅ SUCCÈS! APPLICATION CONSTRUITE ET EMBALLÉE                        ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}📁 FICHIERS CRÉÉS:${NC}"
    echo ""
    echo "   Exécutables:"
    if [ -f "../../dist/BioAccessSetup" ]; then
        echo -e "   ${GREEN}✓${NC} dist/BioAccessSetup"
    fi
    if [ -f "../../dist/BioAccessDiagnostic" ]; then
        echo -e "   ${GREEN}✓${NC} dist/BioAccessDiagnostic"
    fi
    if [ -f "../../dist/BioAccessConfig" ]; then
        echo -e "   ${GREEN}✓${NC} dist/BioAccessConfig"
    fi
    echo ""
    echo "   Paquets Distribution:"
    if [ -d "../../release" ]; then
        ls -1 "../../release" 2>/dev/null | grep -E "\.(zip|7z)$" | while read file; do
            echo -e "   ${GREEN}✓${NC} $file"
        done
    fi
    echo ""
    echo "════════════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "${BLUE}🚀 PROCHAINES ÉTAPES:${NC}"
    echo ""
    echo "   1. Ouvrir le dossier: release/"
    echo "   2. Télécharger l'archive ZIP ou 7Z"
    echo "   3. Partager avec les utilisateurs"
    echo "   4. Les utilisateurs lancent: BioAccessSetup"
    echo ""
    echo -e "${BLUE}💡 CONSEIL:${NC}"
    echo "   • Utilisez le fichier .tar.gz (plus compact)"
    echo "   • Ou le fichier .zip (plus compatible)"
    echo ""
    
    # Try to open release folder
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "../../release" 2>/dev/null
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "../../release" 2>/dev/null || nautilus "../../release" 2>/dev/null || dolphin "../../release" 2>/dev/null
    fi
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║  ❌ ERREUR LORS DE LA CONSTRUCTION                                    ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}📋 DÉPANNAGE:${NC}"
    echo ""
    echo "   1. Vérifiez que Python3 est correctement installé"
    echo "   2. Tentez manuelle:"
    echo "      python3 quickstart_build.py"
    echo "   3. Si erreur persiste, essayez:"
    echo "      python3 build_executables_advanced.py --verbose"
    echo ""
fi

echo ""
exit $BUILD_STATUS

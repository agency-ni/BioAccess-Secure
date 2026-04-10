"""
Gestionnaire des permissions d'accès aux périphériques biométriques
Support: Windows, Linux, macOS
"""

import platform
import subprocess
import os
import json
import logging
import webbrowser
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class PermissionsManager:
    """Gère les permissions d'accès aux caméras et microphones"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.username = os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
        self.permissions_file = Path('logs/permissions_config.json')
    
    def check_all_permissions(self) -> Dict[str, bool]:
        """Vérifie toutes les permissions"""
        permissions = {}
        
        if self.os_type == 'Windows':
            permissions = self._check_windows_permissions()
        elif self.os_type == 'Linux':
            permissions = self._check_linux_permissions()
        elif self.os_type == 'Darwin':
            permissions = self._check_macos_permissions()
        
        return permissions
    
    def _check_windows_permissions(self) -> Dict[str, bool]:
        """Vérifie les permissions Windows"""
        permissions = {
            'camera_enabled': True,  # À vérifier manuellement
            'microphone_enabled': True,  # À vérifier manuellement
            'requires_manual_setup': True,
            'os': 'Windows'
        }
        
        return permissions
    
    def _check_linux_permissions(self) -> Dict[str, bool]:
        """Vérifie les permissions Linux"""
        permissions = {
            'video_group': self._check_group_membership('video'),
            'audio_group': self._check_group_membership('audio'),
            'os': 'Linux'
        }
        
        return permissions
    
    def _check_macos_permissions(self) -> Dict[str, bool]:
        """Vérifie les permissions macOS"""
        permissions = {
            'camera_granted': self._check_tcc_permission('kTCCServiceCamera'),
            'microphone_granted': self._check_tcc_permission('kTCCServiceMicrophone'),
            'os': 'macOS'
        }
        
        return permissions
    
    def _check_group_membership(self, group: str) -> bool:
        """Vérifie si l'utilisateur fait partie d'un groupe"""
        try:
            result = subprocess.run(
                ['groups'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return group in result.stdout
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification du groupe {group}: {e}")
            return False
    
    def _check_tcc_permission(self, service: str) -> bool:
        """Vérifie une permission TCC macOS"""
        try:
            result = subprocess.run(
                ['tccutil', 'status', service],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'granted' in result.stdout
        except:
            return False
    
    def setup_windows_permissions(self):
        """Guide pour configurer les permissions Windows"""
        print("\n" + "="*60)
        print("🔐 CONFIGURATION DES PERMISSIONS - WINDOWS")
        print("="*60)
        
        instructions = [
            "\n📋 Étapes pour permettre l'accès à la caméra:",
            "1. Ouvrir Paramètres (Win + I)",
            "2. Aller à: Confidentialité et sécurité > Caméra",
            "3. S'assurer que 'L'accès à la caméra' est activé",
            "4. Vérifier que l'application BioAccessSecure est autorisée",
            "",
            "📋 Étapes pour permettre l'accès au microphone:",
            "1. Ouvrir Paramètres (Win + I)",
            "2. Aller à: Confidentialité et sécurité > Microphone",
            "3. S'assurer que 'L'accès au microphone' est activé",
            "4. Vérifier que l'application BioAccessSecure est autorisée",
            "",
            "⚠️  IMPORTANT: Vous devrez peut-être redémarrer l'application",
            "               après avoir modifié les permissions.",
        ]
        
        for instruction in instructions:
            print(instruction)
        
        response = input("\n✅ Avez-vous configuré les permissions? (oui/non): ").lower()
        return response in ['oui', 'yes', 'o', 'y']
    
    def setup_linux_permissions(self):
        """Guide pour configurer les permissions Linux"""
        print("\n" + "="*60)
        print("🔐 CONFIGURATION DES PERMISSIONS - LINUX")
        print("="*60)
        
        print(f"\n👤 Utilisateur courant: {self.username}")
        
        # Vérifier les groupes actuels
        video_group = self._check_group_membership('video')
        audio_group = self._check_group_membership('audio')
        
        print(f"   Groupe video: {'✅' if video_group else '❌'}")
        print(f"   Groupe audio: {'✅' if audio_group else '❌'}")
        
        if video_group and audio_group:
            print("\n✅ L'utilisateur possède déjà tous les groupes nécessaires!")
            return True
        
        print("\n📋 Commandes à exécuter pour ajouter les groupes:")
        
        if not video_group:
            print(f"   sudo usermod -a -G video {self.username}")
        if not audio_group:
            print(f"   sudo usermod -a -G audio {self.username}")
        
        print("\n⚠️  APRÈS avoir exécuté les commandes:")
        print("   1. Se reconnecter à la session")
        print("   OU")
        print("   2. Exécuter dans le terminal:")
        print("      newgrp video && newgrp audio")
        
        response = input("\n✅ Avez-vous exécuté les commandes? (oui/non): ").lower()
        
        if response in ['oui', 'yes', 'o', 'y']:
            return True
        
        return False
    
    def setup_macos_permissions(self):
        """Guide pour configurer les permissions macOS"""
        print("\n" + "="*60)
        print("🔐 CONFIGURATION DES PERMISSIONS - MACOS")
        print("="*60)
        
        camera_granted = self._check_tcc_permission('kTCCServiceCamera')
        microphone_granted = self._check_tcc_permission('kTCCServiceMicrophone')
        
        print(f"\n   Caméra: {'✅' if camera_granted else '❌'}")
        print(f"   Microphone: {'✅' if microphone_granted else '❌'}")
        
        if camera_granted and microphone_granted:
            print("\n✅ Toutes les permissions sont accordées!")
            return True
        
        print("\n📋 Instructions manuelles:")
        print("1. Ouvrir Préférences Système")
        print("2. Aller à Sécurité et Confidentialité")
        print("3. Accorder les permissions pour Caméra et Microphone")
        
        if not camera_granted:
            print("\n💡 Pour la caméra, vous verrez une demande de permission")
            print("   lors de la première utilisation.")
        
        if not microphone_granted:
            print("\n💡 Pour le microphone, vous verrez une demande de permission")
            print("   lors de la première utilisation.")
        
        response = input("\n✅ Avez-vous accordé les permissions? (oui/non): ").lower()
        return response in ['oui', 'yes', 'o', 'y']
    
    def run_setup(self) -> bool:
        """Exécute la configuration des permissions"""
        print("\n🔐 ASSISTANT DE CONFIGURATION DES PERMISSIONS")
        print(f"   Système: {self.os_type}")
        
        if self.os_type == 'Windows':
            return self.setup_windows_permissions()
        elif self.os_type == 'Linux':
            return self.setup_linux_permissions()
        elif self.os_type == 'Darwin':
            return self.setup_macos_permissions()
        
        return False
    
    def get_instructions_url(self) -> str:
        """Retourne l'URL des instructions pour l'OS courant"""
        urls = {
            'Windows': 'https://support.microsoft.com/en-us/windows/manage-app-permissions-in-windows-10-77738314',
            'Linux': 'https://wiki.archlinux.org/title/PulseAudio',
            'Darwin': 'https://support.apple.com/en-us/HT210602'
        }
        return urls.get(self.os_type, '')
    
    def open_instructions_in_browser(self):
        """Ouvre les instructions dans le navigateur"""
        url = self.get_instructions_url()
        if url:
            try:
                webbrowser.open(url)
                print(f"\n✅ Instructions ouvertes dans le navigateur")
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du navigateur: {e}")
    
    def save_permissions_config(self, config: Dict) -> bool:
        """Sauvegarde la configuration des permissions"""
        try:
            config_dir = self.permissions_file.parent
            config_dir.mkdir(exist_ok=True)
            
            with open(self.permissions_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Configuration sauvegardée: {self.permissions_file}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def load_permissions_config(self) -> Dict:
        """Charge la configuration des permissions"""
        try:
            if self.permissions_file.exists():
                with open(self.permissions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
        
        return {}
    
    def get_permission_summary(self) -> str:
        """Retourne un résumé des permissions"""
        perms = self.check_all_permissions()
        
        summary = f"\n🔐 RÉSUMÉ DES PERMISSIONS ({self.os_type})\n"
        
        if self.os_type == 'Windows':
            summary += "   Caméra: À vérifier dans Paramètres\n"
            summary += "   Microphone: À vérifier dans Paramètres\n"
        elif self.os_type == 'Linux':
            summary += f"   Groupe video: {'✅' if perms.get('video_group') else '❌'}\n"
            summary += f"   Groupe audio: {'✅' if perms.get('audio_group') else '❌'}\n"
        elif self.os_type == 'Darwin':
            summary += f"   Caméra: {'✅' if perms.get('camera_granted') else '❌'}\n"
            summary += f"   Microphone: {'✅' if perms.get('microphone_granted') else '❌'}\n"
        
        return summary


if __name__ == '__main__':
    manager = PermissionsManager()
    print(manager.get_permission_summary())
    manager.run_setup()

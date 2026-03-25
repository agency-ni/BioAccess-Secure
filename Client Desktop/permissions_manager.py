"""
Gestionnaire des permissions pour caméra et microphone
Gère les permissions Windows et les configurations système
"""

import os
import platform
import subprocess
import logging
from typing import Dict, Tuple, Optional
import sys

logger = logging.getLogger(__name__)


class PermissionsManager:
    """Gestionnaire des permissions pour les périphériques"""

    def __init__(self):
        self.os_type = platform.system()
        self.permission_status = {
            'camera': False,
            'microphone': False,
            'errors': []
        }

    def check_all_permissions(self) -> Dict[str, bool]:
        """Vérifier toutes les permissions"""
        logger.info("Vérification des permissions...")
        
        if self.os_type == 'Windows':
            self._check_windows_permissions()
        elif self.os_type == 'Darwin':  # macOS
            self._check_macos_permissions()
        elif self.os_type == 'Linux':
            self._check_linux_permissions()
        
        return self.permission_status

    def _check_windows_permissions(self):
        """Vérifier les permissions Windows"""
        logger.info("Vérification des permissions Windows...")
        
        try:
            import winreg
            
            # Vérifier caméra
            camera_permission = self._check_registry_permission(
                r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
            )
            self.permission_status['camera'] = camera_permission
            
            # Vérifier microphone
            mic_permission = self._check_registry_permission(
                r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone"
            )
            self.permission_status['microphone'] = mic_permission
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification Windows: {e}")
            self.permission_status['errors'].append(str(e))

    def _check_registry_permission(self, registry_path: str) -> bool:
        """Vérifier une permission dans le registre Windows"""
        try:
            import winreg
            
            hkey = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                registry_path
            )
            
            try:
                value, _ = winreg.QueryValueEx(hkey, "Value")
                result = value == "Allow"
                logger.debug(f"Permission '{registry_path}': {value}")
                return result
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(hkey)
                
        except Exception as e:
            logger.debug(f"Impossible de vérifier '{registry_path}': {e}")
            return False

    def _check_macos_permissions(self):
        """Vérifier les permissions macOS"""
        logger.info("Vérification des permissions macOS...")
        
        try:
            # Vérifier caméra
            result = subprocess.run(
                ['security', 'dump-trust-settings', '-d'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.permission_status['camera'] = result.returncode == 0
            
            # Vérifier microphone
            result = subprocess.run(
                ['security', 'dump-trust-settings', '-d'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.permission_status['microphone'] = result.returncode == 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification macOS: {e}")
            self.permission_status['errors'].append(str(e))

    def _check_linux_permissions(self):
        """Vérifier les permissions Linux"""
        logger.info("Vérification des permissions Linux...")
        
        try:
            username = os.getenv('USER', 'unknown')
            
            # Vérifier groupe video (caméra)
            result = subprocess.run(
                ['groups', username],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                groups = result.stdout.lower()
                self.permission_status['camera'] = 'video' in groups
                self.permission_status['microphone'] = 'audio' in groups
                
                if not self.permission_status['camera']:
                    logger.warning(f"Utilisateur '{username}' n'est pas dans le groupe 'video'")
                if not self.permission_status['microphone']:
                    logger.warning(f"Utilisateur '{username}' n'est pas dans le groupe 'audio'")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification Linux: {e}")
            self.permission_status['errors'].append(str(e))

    def request_permissions_windows(self) -> Dict[str, str]:
        """Demander les permissions sous Windows"""
        logger.info("Demande des permissions Windows...")
        
        results = {}
        
        # Ouvrir les paramètres de confidentialité
        try:
            # Caméra
            logger.info("Ouverture des paramètres de confidentialité pour la caméra...")
            subprocess.Popen(
                'start ms-settings:privacy-webcam',
                shell=True
            )
            results['camera'] = 'Permission dialog opened - user interaction required'
            
            # Microphone
            logger.info("Ouverture des paramètres de confidentialité pour le microphone...")
            subprocess.Popen(
                'start ms-settings:privacy-microphone',
                shell=True
            )
            results['microphone'] = 'Permission dialog opened - user interaction required'
            
        except Exception as e:
            logger.error(f"Erreur lors de la demande de permissions: {e}")
            results['error'] = str(e)
        
        return results

    def enable_permissions_linux(self) -> Dict[str, str]:
        """Activer les permissions sous Linux"""
        logger.info("Instructions pour activer les permissions Linux...")
        
        results = {}
        username = os.getenv('USER', 'unknown')
        
        try:
            # Vérifier si l'utilisateur est déjà dans les groupes
            result = subprocess.run(
                ['groups', username],
                capture_output=True,
                text=True
            )
            
            groups_str = result.stdout.lower()
            camera_ok = 'video' in groups_str
            mic_ok = 'audio' in groups_str
            
            if not camera_ok:
                logger.warning(f"À exécuter: sudo usermod -a -G video {username}")
                results['camera'] = f"Run: sudo usermod -a -G video {username}"
            else:
                results['camera'] = "User is in video group"
            
            if not mic_ok:
                logger.warning(f"À exécuter: sudo usermod -a -G audio {username}")
                results['microphone'] = f"Run: sudo usermod -a -G audio {username}"
            else:
                results['microphone'] = "User is in audio group"
            
        except Exception as e:
            logger.error(f"Erreur: {e}")
            results['error'] = str(e)
        
        return results

    def show_permission_instructions(self) -> str:
        """Afficher les instructions pour les permissions"""
        instructions = """
╔════════════════════════════════════════════════════════════════╗
║           INSTRUCTIONS DE PERMISSION                          ║
╚════════════════════════════════════════════════════════════════╝

"""
        
        if self.os_type == 'Windows':
            instructions += """
WINDOWS 10/11:

1. CAMÉRA:
   - Aller à Paramètres > Confidentialité et sécurité > Caméra
   - Activer "Accès à la caméra"
   - Activer "Autoriser les applications à accéder à votre caméra"
   - S'assurer que BioAccess Secure est dans la liste des app autorisées

2. MICROPHONE:
   - Aller à Paramètres > Confidentialité et sécurité > Microphone
   - Activer "Accès au microphone"
   - Activer "Autoriser les applications à accéder à votre microphone"
   - S'assurer que BioAccess Secure est dans la liste des app autorisées

3. VÉRIFIER LES PILOTES:
   - Vérifier que les pilotes de la caméra sont installés
   - Vérifier que les pilotes audio sont à jour
   - Redémarrer l'application après chaque changement
"""
        
        elif self.os_type == 'Darwin':  # macOS
            instructions += """
MAC OS:

1. CAMÉRA:
   - Aller à Paramètres Système > Confidentialité et sécurité > Caméra
   - Ajouter BioAccess Secure à la liste des applications autorisées

2. MICROPHONE:
   - Aller à Paramètres Système > Confidentialité et sécurité > Microphone
   - Ajouter BioAccess Secure à la liste des applications autorisées

3. TERMINAL (si nécessaire):
   chmod +x /Applications/BioAccessSecure.app/Contents/MacOS/BioAccessSecure
"""
        
        elif self.os_type == 'Linux':
            username = os.getenv('USER', 'your_username')
            instructions += f"""
LINUX:

1. AJOUTER VOTRE UTILISATEUR AUX GROUPES REQUIS:

   - Groupe vidéo (pour caméra):
     sudo usermod -a -G video {username}
   
   - Groupe audio (pour microphone):
     sudo usermod -a -G audio {username}

2. APPLIQUER LES CHANGEMENTS:
   - Déconnexion puis reconnexion (ou redémarrage)
   - Ou: newgrp video && newgrp audio

3. VÉRIFIER LES PERMISSIONS:
   groups
   
4. PULSEAUDIO/PIPEWIRE (si nécessaire):
   - Vérifier que pulseaudio/pipewire est en cours d'exécution
   - Consulter la documentation de votre distributeur
"""
        
        instructions += """
╔════════════════════════════════════════════════════════════════╗
║                    DÉPANNAGE                                  ║
╚════════════════════════════════════════════════════════════════╝

✗ Caméra / Microphone pas détectés:
  → Redémarrer l'application
  → Redémarrer l'ordinateur
  → Vérifier que le matériel est connecté
  → Exécuter le diagnostic: python device_diagnostic.py

✗ Permission refusée:
  → Vérifier les paramètres de confidentialité
  → Ajouter l'application à la liste blanche
  → Redémarrer le système

✗ Volumes faibles / Qualité mauvaise:
  → Vérifier les niveaux d'entrée dans les paramètres audio
  → Régler les niveaux de la caméra/microphone
  → Tester avec d'autres applications (ex: Skype)
"""
        
        return instructions

    def diagnose_and_fix(self) -> Tuple[bool, str]:
        """Diagnostiquer et essayer de corriger les problèmes"""
        logger.info("Diagnostic et correction des permissions...")
        
        status_ok = True
        message = ""
        
        # Vérifier les permissions actuelles
        permissions = self.check_all_permissions()
        
        if not permissions['camera']:
            status_ok = False
            message += "⚠ Problème de caméra détecté\n"
            
            if self.os_type == 'Windows':
                message += "→ Ouverture des paramètres Windows...\n"
                self.request_permissions_windows()
        
        if not permissions['microphone']:
            status_ok = False
            message += "⚠ Problème de microphone détecté\n"
            
            if self.os_type == 'Windows':
                message += "→ Ouverture des paramètres Windows...\n"
                self.request_permissions_windows()
            elif self.os_type == 'Linux':
                linux_results = self.enable_permissions_linux()
                for key, value in linux_results.items():
                    if key != 'error':
                        message += f"→ {value}\n"
        
        if permissions['errors']:
            message += "\nErreurs détectées:\n"
            for error in permissions['errors']:
                message += f"  - {error}\n"
        
        if status_ok:
            message = "✓ Toutes les permissions sont correctement configurées"
        
        return status_ok, message


def show_menu():
    """Afficher le menu interactif"""
    print("\n" + "=" * 60)
    print("GESTIONNAIRE DE PERMISSIONS - BIOACCESS SECURE")
    print("=" * 60)
    print("\n1. Vérifier les permissions")
    print("2. Demander les permissions")
    print("3. Afficher les instructions détaillées")
    print("4. Lancer le diagnostic complet")
    print("5. Quitter\n")


def main():
    """Fonction principale"""
    manager = PermissionsManager()
    
    while True:
        show_menu()
        choice = input("Sélectionner une option (1-5): ").strip()
        
        if choice == '1':
            print("\n" + "=" * 60)
            print("VÉRIFICATION DES PERMISSIONS")
            print("=" * 60)
            
            permissions = manager.check_all_permissions()
            
            print(f"\n🎥 Caméra: {'✓ OK' if permissions['camera'] else '✗ Problème'}")
            print(f"🎤 Microphone: {'✓ OK' if permissions['microphone'] else '✗ Problème'}")
            
            if permissions['errors']:
                print("\n⚠ Erreurs:")
                for error in permissions['errors']:
                    print(f"  - {error}")
            
            if not permissions['camera'] or not permissions['microphone']:
                status_ok, message = manager.diagnose_and_fix()
                print(f"\n{message}")
        
        elif choice == '2':
            print("\n" + "=" * 60)
            print("DEMANDE DE PERMISSIONS")
            print("=" * 60)
            
            if manager.os_type == 'Windows':
                print("\nOuverture des paramètres Windows...")
                manager.request_permissions_windows()
                print("✓ Paramètres ouverts - veuillez activer les permissions")
            elif manager.os_type == 'Linux':
                print("\nCommandes à exécuter:")
                results = manager.enable_permissions_linux()
                for key, value in results.items():
                    if key != 'error' and value.startswith('Run:'):
                        print(f"  {value}")
                    elif key != 'error':
                        print(f"  {value}")
            else:
                print("Veuillez vérifier les paramètres de votre système")
        
        elif choice == '3':
            print(manager.show_permission_instructions())
        
        elif choice == '4':
            print("\nLancement du diagnostic complet...")
            os.system(f"{sys.executable} device_diagnostic.py")
        
        elif choice == '5':
            print("\nAu revoir!")
            break
        
        else:
            print("Option invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    main()

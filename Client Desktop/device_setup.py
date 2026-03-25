"""
Script de configuration et test des périphériques
Intégration avec diagnostic et gestionnaire de permissions
"""

import sys
import os
import platform
import logging
from typing import Dict, Tuple
from datetime import datetime

# Importer les modules
try:
    from biometric.face import FaceRecognizer, CameraAccessError
    from biometric.voice import VoiceRecorder, MicrophoneAccessError
    from permissions_manager import PermissionsManager
    from device_diagnostic import DeviceDiagnostic
except ImportError as e:
    print(f"Erreur d'import: {e}")
    sys.exit(1)

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/device_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeviceSetup:
    """Gestionnaire de configuration des périphériques"""

    def __init__(self):
        self.permissions_manager = PermissionsManager()
        self.diagnostic = DeviceDiagnostic()
        self.face_recognizer = None
        self.voice_recorder = None
        self.setup_log = []

    def print_header(self, title: str):
        """Afficher un en-tête"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def print_section(self, title: str):
        """Afficher une section"""
        print("\n" + "-" * 70)
        print(f"  {title}")
        print("-" * 70 + "\n")

    def run_full_setup(self):
        """Exécuter la configuration complète"""
        self.print_header("CONFIGURATION DES PÉRIPHÉRIQUES BIOMÉTRIQUES")
        
        logger.info("Démarrage de la configuration complète")
        
        # 1. Diagnostic système
        self.print_section("1. DIAGNOSTIC SYSTÈME")
        if not self._run_diagnostic():
            return False
        
        # 2. Vérifier les permissions
        self.print_section("2. VÉRIFICATION DES PERMISSIONS")
        if not self._check_permissions():
            logger.warning("Permissions incomplètes - tentative de correction")
            self._request_permissions()
        
        # 3. Tester la caméra
        self.print_section("3. TEST DE LA CAMÉRA")
        camera_ok = self._test_camera()
        
        # 4. Tester le microphone
        self.print_section("4. TEST DU MICROPHONE")
        microphone_ok = self._test_microphone()
        
        # 5. Résumé final
        self.print_section("RÉSUMÉ FINAL")
        self._print_summary(camera_ok, microphone_ok)
        
        logger.info("Configuration terminée")
        return camera_ok and microphone_ok

    def _run_diagnostic(self) -> bool:
        """Exécuter le diagnostic"""
        try:
            print("Exécution du diagnostic...")
            results = self.diagnostic.run_full_diagnostic()
            
            # Afficher le résumé
            print(f"\n✓ Diagnostic terminé")
            print(f"  Caméra: {results['camera'].get('status', 'UNKNOWN')}")
            print(f"  Microphone: {results['microphone'].get('status', 'UNKNOWN')}")
            
            self.setup_log.append({
                'step': 'Diagnostic',
                'status': 'OK',
                'results': results
            })
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors du diagnostic: {e}")
            print(f"✗ Erreur: {e}")
            return False

    def _check_permissions(self) -> bool:
        """Vérifier les permissions"""
        try:
            print("Vérification des permissions...")
            permissions = self.permissions_manager.check_all_permissions()
            
            camera_ok = permissions.get('camera', False)
            microphone_ok = permissions.get('microphone', False)
            
            print(f"  🎥 Caméra: {'✓ OK' if camera_ok else '✗ PROBLÈME'}")
            print(f"  🎤 Microphone: {'✓ OK' if microphone_ok else '✗ PROBLÈME'}")
            
            self.setup_log.append({
                'step': 'Vérification permissions',
                'camera': camera_ok,
                'microphone': microphone_ok
            })
            
            return camera_ok and microphone_ok
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            print(f"✗ Erreur: {e}")
            return False

    def _request_permissions(self):
        """Demander les permissions"""
        try:
            print("\nDemande des permissions...")
            
            if platform.system() == 'Windows':
                print("  Ouverture des paramètres Windows...")
                results = self.permissions_manager.request_permissions_windows()
                for key, value in results.items():
                    print(f"    {key}: {value}")
            elif platform.system() == 'Linux':
                print("  Commandes à exécuter:")
                results = self.permissions_manager.enable_permissions_linux()
                for key, value in results.items():
                    if key != 'error':
                        print(f"    {value}")
            
            print("\n  Appuyez sur Entrée après avoir mis à jour les permissions...")
            input()
        except Exception as e:
            logger.warning(f"Erreur lors de la demande: {e}")

    def _test_camera(self) -> bool:
        """Tester la caméra"""
        try:
            print("Test de la caméra...")
            
            # Créer le FaceRecognizer
            self.face_recognizer = FaceRecognizer()
            
            if not self.face_recognizer.is_available():
                print("✗ Cascade classifier non disponible")
                return False
            
            # Essayer de démarrer la caméra
            try:
                cap = self.face_recognizer.start_camera()
                if cap:
                    print("✓ Caméra démarrée avec succès")
                    cap.release()
                    
                    self.setup_log.append({
                        'step': 'Test caméra',
                        'status': 'OK'
                    })
                    return True
                else:
                    print("✗ Impossible de démarrer la caméra")
                    return False
            
            except CameraAccessError as e:
                print(f"✗ Erreur d'accès caméra: {e}")
                
                # Essayer une caméra alternative
                print("  Tentative d'accès à une caméra alternative...")
                cap = self.face_recognizer.try_alternative_cameras()
                if cap:
                    print("✓ Caméra alternative trouvée")
                    cap.release()
                    self.setup_log.append({
                        'step': 'Test caméra',
                        'status': 'OK_ALTERNATIVE'
                    })
                    return True
                else:
                    print("✗ Aucune caméra alternative trouvée")
                    return False
        
        except Exception as e:
            logger.error(f"Erreur lors du test caméra: {e}")
            print(f"✗ Erreur: {e}")
            return False

    def _test_microphone(self) -> bool:
        """Tester le microphone"""
        try:
            print("Test du microphone...")
            
            # Créer le VoiceRecorder
            try:
                self.voice_recorder = VoiceRecorder()
            except MicrophoneAccessError as e:
                print(f"✗ Erreur d'initialisation: {e}")
                return False
            
            if not self.voice_recorder.is_available():
                print("✗ Aucun périphérique d'entrée audio détecté")
                return False
            
            # Lister les périphériques
            devices = self.voice_recorder.get_input_devices()
            print(f"\n  Périphériques détectés: {len(devices)}")
            for device in devices:
                print(f"    {device['id']}: {device['name']}")
            
            # Essayer d'enregistrer
            print("\n  Enregistrement de test (2 secondes)...")
            try:
                audio = self.voice_recorder.record_audio(duration=2)
                if audio is not None and len(audio) > 0:
                    level = __import__('numpy').sqrt(__import__('numpy').mean(audio**2))
                    print(f"✓ Enregistrement réussi (niveau: {level:.4f})")
                    
                    self.setup_log.append({
                        'step': 'Test microphone',
                        'status': 'OK',
                        'level': float(level)
                    })
                    return True
                else:
                    print("✗ Enregistrement vide")
                    return False
            
            except MicrophoneAccessError as e:
                print(f"✗ Erreur d'enregistrement: {e}")
                
                # Essayer un microphone alternatif
                print("  Tentative avec un microphone alternatif...")
                audio = self.voice_recorder.try_alternative_devices()
                if audio is not None and len(audio) > 0:
                    print("✓ Microphone alternatif trouvé")
                    self.setup_log.append({
                        'step': 'Test microphone',
                        'status': 'OK_ALTERNATIVE'
                    })
                    return True
                else:
                    print("✗ Aucun microphone alternatif trouvé")
                    return False
        
        except Exception as e:
            logger.error(f"Erreur lors du test microphone: {e}")
            print(f"✗ Erreur: {e}")
            return False

    def _print_summary(self, camera_ok: bool, microphone_ok: bool):
        """Afficher le résumé final"""
        print(f"\n{'✓' if camera_ok else '✗'} Caméra: {'OK' if camera_ok else 'PROBLÈME'}")
        print(f"{'✓' if microphone_ok else '✗'} Microphone: {'OK' if microphone_ok else 'PROBLÈME'}")
        
        if camera_ok and microphone_ok:
            print("\n✓ TOUS LES PÉRIPHÉRIQUES SONT CONFIGURÉS CORRECTEMENT")
            print("  L'application est prête à fonctionner!")
        else:
            print("\n⚠ DES PROBLÈMES DÉTECTÉS")
            print("  Conseils:")
            if not camera_ok:
                print("    - Caméra: Vérifier la connexion et les permissions Windows")
                print("      Allez à: Paramètres > Confidentialité > Caméra")
            if not microphone_ok:
                print("    - Microphone: Vérifier la connexion et les permissions Windows")
                print("      Allez à: Paramètres > Confidentialité > Microphone")
        
        # Sauvegarder le log
        self._save_setup_log()

    def _save_setup_log(self):
        """Sauvegarder le log de configuration"""
        import json
        import os
        
        os.makedirs('logs', exist_ok=True)
        
        log_file = f"logs/setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'os': platform.system(),
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                    'steps': self.setup_log
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n✓ Log sauvegardé: {log_file}")
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder le log: {e}")


def show_main_menu():
    """Afficher le menu principal"""
    print("\n" + "=" * 70)
    print("  CONFIGURATION - BIOACCESS SECURE")
    print("=" * 70)
    print("\n1. Configuration complète (recommandé)")
    print("2. Diagnostic uniquement")
    print("3. Gestionnaire de permissions")
    print("4. Re-tester les périphériques")
    print("5. Afficher les instructions")
    print("6. Quitter\n")


def main():
    """Fonction principale"""
    
    os.makedirs('logs', exist_ok=True)
    
    while True:
        show_main_menu()
        choice = input("Sélectionner une option (1-6): ").strip()
        
        if choice == '1':
            setup = DeviceSetup()
            setup.run_full_setup()
        
        elif choice == '2':
            diagnostic = DeviceDiagnostic()
            diagnostic.run_full_diagnostic()
            diagnostic.print_summary()
        
        elif choice == '3':
            os.system(f"{sys.executable} permissions_manager.py")
        
        elif choice == '4':
            setup = DeviceSetup()
            setup.print_section("RE-TEST DES PÉRIPHÉRIQUES")
            
            camera_ok = setup._test_camera()
            microphone_ok = setup._test_microphone()
            
            setup.print_section("RÉSUMÉ")
            setup._print_summary(camera_ok, microphone_ok)
        
        elif choice == '5':
            manager = PermissionsManager()
            print(manager.show_permission_instructions())
        
        elif choice == '6':
            print("\nAu revoir!")
            break
        
        else:
            print("Option invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur: {e}", exc_info=True)
        print(f"\nErreur: {e}")
        sys.exit(1)

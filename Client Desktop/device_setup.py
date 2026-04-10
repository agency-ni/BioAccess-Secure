"""
Interface interactive de configuration des périphériques biométriques
Fait fonctionner automatiquement la caméra et le microphone
"""

import sys
import json
import logging
from pathlib import Path
from device_diagnostic import DeviceDiagnostic
from permissions_manager import PermissionsManager

# Configure le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/device_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeviceSetup:
    """Interface interactive pour configurer les périphériques biométriques"""
    
    def __init__(self):
        self.diagnostic = DeviceDiagnostic()
        self.permissions = PermissionsManager()
        self.setup_complete = False
    
    def run_full_setup(self):
        """Exécute la configuration complète"""
        self.show_header()
        
        # Menu principal
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.setup_full_configuration()
            elif choice == '2':
                self.run_diagnostic_only()
            elif choice == '3':
                self.manage_permissions()
            elif choice == '4':
                self.test_devices()
            elif choice == '5':
                self.show_help()
            elif choice == '0':
                print("\n✅ Configuration terminée!")
                break
            else:
                print("\n❌ Option invalide. Essayez à nouveau.")
    
    def show_header(self):
        """Affiche l'en-tête"""
        print("\n" + "="*70)
        print("  🔐 ASSISTANT DE CONFIGURATION - BioAccess Secure")
        print("="*70)
        print("  Bienvenue! Cet assistant vous aidera à configurer")
        print("  votre caméra et microphone pour la biométrie.")
        print("="*70 + "\n")
    
    def show_menu(self) -> str:
        """Affiche le menu principal"""
        print("\n📋 MENU PRINCIPAL")
        print("-" * 50)
        print("1. ✅ Configuration complète (recommandé)")
        print("2. 🔍 Diagnostic uniquement")
        print("3. 🔐 Gestionnaire de permissions")
        print("4. 🧪 Test des périphériques")
        print("5. 📖 Afficher les instructions")
        print("0. ❌ Quitter")
        print("-" * 50)
        
        return input("Choisissez une option (0-5): ").strip()
    
    def setup_full_configuration(self):
        """Configuration complète"""
        print("\n" + "="*70)
        print("  ⚙️  CONFIGURATION COMPLÈTE")
        print("="*70)
        
        steps_completed = 0
        total_steps = 3
        
        # Étape 1: Diagnostic
        print(f"\n[Étape 1/{total_steps}] 🔍 Diagnostic des périphériques...")
        self._run_diagnostic()
        steps_completed += 1
        
        # Étape 2: Permissions
        print(f"\n[Étape 2/{total_steps}] 🔐 Configuration des permissions...")
        if self.permissions.run_setup():
            print("✅ Permissions configurées")
            steps_completed += 1
        else:
            print("⚠️  Permissions non validées - Vous pouvez continuer")
        
        # Étape 3: Test
        print(f"\n[Étape 3/{total_steps}] 🧪 Test des périphériques...")
        self._test_devices_interactive()
        steps_completed += 1
        
        # Résumé
        self._show_completion_summary(steps_completed, total_steps)
    
    def run_diagnostic_only(self):
        """Exécute le diagnostic uniquement"""
        print("\n" + "="*70)
        print("  🔍 DIAGNOSTIC DES PÉRIPHÉRIQUES")
        print("="*70)
        
        self._run_diagnostic()
    
    def _run_diagnostic(self):
        """Exécute le diagnostic"""
        try:
            results = self.diagnostic.run_full_diagnostic()
            
            # Analyser les résultats
            cameras = results.get('cameras', [])
            microphones = results.get('microphones', [])
            recommendations = results.get('recommendations', [])
            
            # Sauvegarder les résultats
            self._save_diagnostic_results(results)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors du diagnostic: {e}")
            print(f"\n❌ Erreur lors du diagnostic: {e}")
            return False
    
    def manage_permissions(self):
        """Gère les permissions"""
        print("\n" + "="*70)
        print("  🔐 GESTIONNAIRE DE PERMISSIONS")
        print("="*70)
        
        print(self.permissions.get_permission_summary())
        
        print("\n📋 OPTIONS")
        print("-" * 50)
        print("1. 📖 Afficher les instructions")
        print("2. 🔄 Réexécuter la configuration")
        print("0. ❌ Retour au menu")
        print("-" * 50)
        
        choice = input("Choisissez une option: ").strip()
        
        if choice == '1':
            self.permissions.open_instructions_in_browser()
        elif choice == '2':
            self.permissions.run_setup()
        
    def test_devices(self):
        """Teste les périphériques"""
        print("\n" + "="*70)
        print("  🧪 TEST DES PÉRIPHÉRIQUES")
        print("="*70)
        
        self._test_devices_interactive()
    
    def _test_devices_interactive(self):
        """Test interactif des périphériques"""
        print("\n📷 Test de la caméra...")
        camera_ok = self._test_camera()
        
        print("\n🎤 Test du microphone...")
        mic_ok = self._test_microphone()
        
        # Résumé des tests
        print("\n" + "-"*50)
        print("📊 RÉSUMÉ DES TESTS")
        print("-"*50)
        print(f"Caméra: {'✅ OK' if camera_ok else '❌ Échouée'}")
        print(f"Microphone: {'✅ OK' if mic_ok else '❌ Échoué'}")
        
        if camera_ok and mic_ok:
            print("\n🎉 Tous les tests sont réussis!")
        else:
            print("\n⚠️  Certains tests ont échoué")
            print("💡 Vérifiez les permissions et les connexions matérielles")
    
    def _test_camera(self) -> bool:
        """Teste la caméra"""
        try:
            import cv2
            
            camera_idx = self.diagnostic.get_primary_camera()
            if camera_idx < 0:
                print("❌ Aucune caméra trouvée")
                return False
            
            cap = cv2.VideoCapture(camera_idx)
            if not cap.isOpened():
                print("❌ Impossible d'ouvrir la caméra")
                return False
            
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                print("✅ Caméra fonctionnelle")
                return True
            else:
                print("❌ Captures échouées")
                return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def _test_microphone(self) -> bool:
        """Teste le microphone"""
        try:
            import sounddevice as sd
            import soundfile as sf
            import numpy as np
            
            mic_idx = self.diagnostic.get_primary_microphone()
            if mic_idx < 0:
                print("❌ Aucun microphone trouvé")
                return False
            
            print("🎤 Enregistrement 2 secondes...")
            duration = 2
            fs = 44100
            
            # Enregister
            recording = sd.rec(
                int(duration * fs),
                samplerate=fs,
                channels=1,
                device=mic_idx
            )
            sd.wait()
            
            # Vérifier
            if len(recording) > 0 and np.max(np.abs(recording)) > 0.01:
                print("✅ Microphone fonctionnel")
                
                # Sauvegarder l'enregistrement de test
                try:
                    test_file = Path('logs/test_audio.wav')
                    test_file.parent.mkdir(exist_ok=True)
                    sf.write(test_file, recording, fs)
                except:
                    pass
                
                return True
            else:
                print("⚠️  Microphone détecté mais volume très faible")
                return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            logger.error(f"Erreur lors du test du micro: {e}")
            return False
    
    def show_help(self):
        """Affiche les instructions détaillées"""
        print("\n" + "="*70)
        print("  📖 INSTRUCTIONS DÉTAILLÉES")
        print("="*70)
        
        help_text = """
🔍 DIAGNOSTIC
Scanne tous les périphériques connectés et teste leur fonctionnement.
Génère un rapport JSON dans logs/

🔐 PERMISSIONS
Configure les droits d'accès pour chaque système:
  • Windows: Via Paramètres > Confidentialité
  • Linux: Ajouter à groupes video/audio
  • macOS: Via Sécurité & Confidentialité

🧪 TEST DES PÉRIPHÉRIQUES
Teste effectivement la caméra (capture) et le microphone (enregistrement).

📊 RÉSUMÉ
Affiche l'état de tous les périphériques et les recommandations.

💡 TROUBLESHOOTING
  ❌ Aucune caméra détectée
    → Vérifier les connexions USB
    → Essayer un autre port USB
    → Redémarrer l'ordinateur
  
  ❌ Nombre de caméras inférieur à la détection système
    → Certains pilotes sont peut-être actifs
    → Essayer de redémarrer l'application
  
  ❌ Microphone non détecté
    → Vérifier les connexions
    → Tester avec l'application Volume du système
    → Vérifier les permissions de groupe (Linux)
  
  ❌ Permissions refusées (Linux)
    → Exécuter: sudo usermod -a -G video $USER
    → Exécuter: sudo usermod -a -G audio $USER
    → Se reconnecter à la session

🌐 RESSOURCES
  Windows: https://support.microsoft.com/windows/manage-app-permissions
  Linux: https://wiki.archlinux.org/title/PulseAudio
  macOS: https://support.apple.com/HT210602
        """
        
        print(help_text)
    
    def _save_diagnostic_results(self, results: dict):
        """Sauvegarde les résultats du diagnostic"""
        try:
            config = {
                'diagnostic': results,
                'setup_complete': True,
                'primary_camera': self.diagnostic.get_primary_camera(),
                'primary_microphone': self.diagnostic.get_primary_microphone()
            }
            
            self.permissions.save_permissions_config(config)
            
            # Afficher un résumé
            config_file = Path('logs/device_config.json')
            print(f"\n✅ Configuration sauvegardée: {config_file}")
        except Exception as e:
            logger.error(f"Erreur: {e}")
    
    def _show_completion_summary(self, completed: int, total: int):
        """Affiche le résumé de completion"""
        percentage = int((completed / total) * 100)
        
        print("\n" + "="*70)
        print("  ✅ RÉSUMÉ DE CONFIGURATION")
        print("="*70)
        print(f"\nÉtapes complétées: {completed}/{total} ({percentage}%)")
        
        if percentage == 100:
            print("\n🎉 Configuration complète!")
            print("   Votre système est prêt pour la biométrie.")
            self.setup_complete = True
        else:
            print(f"\n⚠️  {total - completed} étape(s) restante(s)")
        
        input("\nAppuyez sur Entrée pour continuer...")


def main():
    """Point d'entrée principal"""
    try:
        # Créer le dossier logs s'il n'existe pas
        Path('logs').mkdir(exist_ok=True)
        
        # Lancer l'assistant
        setup = DeviceSetup()
        setup.run_full_setup()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

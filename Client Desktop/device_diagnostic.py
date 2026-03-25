"""
Script de diagnostic des périphériques (caméra et microphone)
Vérifie l'accès et les permissions sur Windows
"""

import cv2
import sounddevice as sd
import numpy as np
import platform
import subprocess
import sys
import logging
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeviceDiagnostic:
    """Diagnostic des périphériques audio et vidéo"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'os': platform.system(),
            'camera': {},
            'microphone': {},
            'issues': [],
            'recommendations': []
        }

    def run_full_diagnostic(self) -> Dict:
        """Exécuter le diagnostic complet"""
        logger.info("=" * 60)
        logger.info("DIAGNOSTIC DES PÉRIPHÉRIQUES BIOMÉTRIQUES")
        logger.info("=" * 60)
        
        self._diagnose_system()
        self._diagnose_camera()
        self._diagnose_microphone()
        self._check_permissions()
        self._generate_recommendations()
        
        return self.results

    def _diagnose_system(self):
        """Diagnostiquer le système"""
        logger.info("\n[SYSTÈME]")
        self.results['system_info'] = {
            'platform': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        logger.info(f"  OS: {self.results['system_info']['platform']} "
                   f"{self.results['system_info']['release']}")
        logger.info(f"  Python: {self.results['system_info']['python_version']}")

    def _diagnose_camera(self):
        """Diagnostiquer la caméra"""
        logger.info("\n[CAMÉRA]")
        
        # Tester différents index de caméra
        cameras_found = []
        for camera_id in range(5):  # Tester les 5 premiers index
            try:
                cap = cv2.VideoCapture(camera_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cameras_found.append(camera_id)
                        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        logger.info(f"  ✓ Caméra trouvée (ID: {camera_id})")
                        logger.info(f"    - Résolution: {width}x{height}")
                        logger.info(f"    - FPS: {fps}")
                    cap.release()
            except Exception as e:
                logger.debug(f"  ✗ Caméra {camera_id}: {e}")
        
        if cameras_found:
            self.results['camera']['status'] = 'OK'
            self.results['camera']['cameras_found'] = cameras_found
            self.results['camera']['default_id'] = cameras_found[0]
        else:
            self.results['camera']['status'] = 'ERROR'
            self.results['camera']['cameras_found'] = []
            self.results['issues'].append("Aucune caméra détectée")
            logger.error("  ✗ Aucune caméra trouvée")

    def _diagnose_microphone(self):
        """Diagnostiquer le microphone"""
        logger.info("\n[MICROPHONE]")
        
        try:
            devices = sd.query_devices()
            input_devices = []
            
            logger.info(f"  Périphériques audio détectés: {len(devices)}")
            
            # Chercher les périphériques d'entrée
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
                    logger.info(f"  ✓ Entrée audio: {device['name']}")
                    logger.info(f"    - Canaux: {device['max_input_channels']}")
                    logger.info(f"    - Fréquence: {device['default_samplerate']} Hz")
            
            if input_devices:
                self.results['microphone']['status'] = 'OK'
                self.results['microphone']['devices'] = input_devices
                self.results['microphone']['default_device'] = sd.default.device[0]
                
                # Tester l'enregistrement
                self._test_microphone_recording()
            else:
                self.results['microphone']['status'] = 'ERROR'
                self.results['microphone']['devices'] = []
                self.results['issues'].append("Aucun périphérique d'entrée audio détecté")
                logger.error("  ✗ Aucun microphone trouvé")
                
        except Exception as e:
            self.results['microphone']['status'] = 'ERROR'
            self.results['microphone']['error'] = str(e)
            self.results['issues'].append(f"Erreur lors du diagnostic du microphone: {e}")
            logger.error(f"  ✗ Erreur: {e}")

    def _test_microphone_recording(self):
        """Tester l'enregistrement du microphone"""
        logger.info("\n[TEST D'ENREGISTREMENT]")
        
        try:
            logger.info("  Test d'enregistrement 1 seconde...")
            duration = 1  # 1 seconde
            fs = 44100  # Fréquence d'échantillonnage
            
            # Enregistrer 1 seconde
            audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.float32)
            sd.wait()
            
            # Vérifier si audio a été enregistré
            if audio is not None and len(audio) > 0:
                # Calculer le niveau sonore
                level = np.sqrt(np.mean(audio**2))
                
                if level > 0.01:
                    self.results['microphone']['recording_test'] = 'OK'
                    logger.info("  ✓ Enregistrement réussi")
                    logger.info(f"    - Niveau sonore: {level:.4f}")
                else:
                    self.results['microphone']['recording_test'] = 'WARNING'
                    logger.warning("  ⚠ Enregistrement silencieux (vérifier le micro)")
                    self.results['issues'].append("Microphone silencieux - vérifier la configuration")
            else:
                self.results['microphone']['recording_test'] = 'ERROR'
                logger.error("  ✗ Échec de l'enregistrement")
                self.results['issues'].append("impossible d'enregistrer du son")
                
        except Exception as e:
            self.results['microphone']['recording_test'] = 'ERROR'
            logger.error(f"  ✗ Erreur lors du test: {e}")
            self.results['issues'].append(f"Erreur test enregistrement: {e}")

    def _check_permissions(self):
        """Vérifier les permissions Windows"""
        logger.info("\n[PERMISSIONS]")
        
        if platform.system() == 'Windows':
            logger.info("  Système: Windows")
            
            # Vérifier les permissions de registre
            try:
                # Vérifier si l'app a accès aux paramètres de confidentialité
                self._check_windows_privacy_settings()
            except Exception as e:
                logger.warning(f"  ⚠ Impossible de vérifier les paramètres Windows: {e}")

    def _check_windows_privacy_settings(self):
        """Vérifier les paramètres de confidentialité Windows"""
        try:
            # Clés de registre pour les permissions
            import winreg
            
            # Vérifier caméra
            try:
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam")
                value, _ = winreg.QueryValueEx(hkey, "Value")
                camera_enabled = value == "Allow"
                logger.info(f"  - Caméra: {'Activée' if camera_enabled else 'Désactivée'}")
                if not camera_enabled:
                    self.results['issues'].append("Caméra désactivée dans les paramètres Windows")
                winreg.CloseKey(hkey)
            except:
                logger.info("  - Caméra: État indéterminé")
            
            # Vérifier microphone
            try:
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone")
                value, _ = winreg.QueryValueEx(hkey, "Value")
                mic_enabled = value == "Allow"
                logger.info(f"  - Microphone: {'Activé' if mic_enabled else 'Désactivé'}")
                if not mic_enabled:
                    self.results['issues'].append("Microphone désactivé dans les paramètres Windows")
                winreg.CloseKey(hkey)
            except:
                logger.info("  - Microphone: État indéterminé")
                
        except ImportError:
            logger.warning("  Module winreg non disponible")

    def _generate_recommendations(self):
        """Générer des recommandations basées sur le diagnostic"""
        logger.info("\n[RECOMMANDATIONS]")
        
        if not self.results['issues']:
            logger.info("  ✓ Aucun problème détecté")
            self.results['recommendations'].append("Le système est correctement configuré")
            return
        
        logger.warning(f"  {len(self.results['issues'])} problème(s) détecté(s)")
        
        recommendations = []
        
        if "Aucune caméra détectée" in self.results['issues']:
            recommendations.append("1. Vérifier que la caméra est connectée et reconnue par Windows")
            recommendations.append("2. Redémarrer l'application")
            recommendations.append("3. Réinstaller les pilotes de la caméra")
            recommendations.append("4. Vérifier en Paramètres > Confidentialité > Caméra")
        
        if "Microphone" in str(self.results['issues']):
            recommendations.append("1. Vérifier que le microphone est connecté et sélectionné")
            recommendations.append("2. Régler le niveau du microphone dans les paramètres audio Windows")
            recommendations.append("3. Vérifier en Paramètres > Confidentialité > Microphone")
            recommendations.append("4. Tester avec l'enregistreur de bruit Windows")
        
        if "désactivée" in str(self.results['issues']).lower():
            recommendations.append("→ Activer en Paramètres > Confidentialité > Caméra/Microphone")
            recommendations.append("→ Autoriser cette application à accéder au périphérique")
        
        for rec in recommendations:
            logger.info(f"  {rec}")
            self.results['recommendations'].append(rec)

    def print_summary(self):
        """Afficher un résumé du diagnostic"""
        logger.info("\n" + "=" * 60)
        logger.info("RÉSUMÉ")
        logger.info("=" * 60)
        
        camera_status = self.results['camera'].get('status', 'UNKNOWN')
        mic_status = self.results['microphone'].get('status', 'UNKNOWN')
        
        logger.info(f"Caméra: {camera_status}")
        logger.info(f"Microphone: {mic_status}")
        
        if self.results['issues']:
            logger.error(f"\n⚠ {len(self.results['issues'])} problème(s):")
            for issue in self.results['issues']:
                logger.error(f"  - {issue}")
        else:
            logger.info("\n✓ Tous les périphériques fonctionnent correctement")


def main():
    """Fonction principale"""
    diagnostic = DeviceDiagnostic()
    results = diagnostic.run_full_diagnostic()
    diagnostic.print_summary()
    
    # Sauvegarder les résultats
    import json
    import os
    
    results_file = os.path.join('logs', 'device_diagnostic_results.json')
    os.makedirs('logs', exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Résultats sauvegardés dans: {results_file}")
    
    # Retourner le code d'erreur approprié
    if results['camera']['status'] != 'OK' or results['microphone']['status'] != 'OK':
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""
Diagnostic complet des périphériques biométriques (caméra et microphone)
Détecte et teste les périphériques disponibles sur le système
"""

import cv2
import json
import platform
import subprocess
import os
import sys
import logging
import numpy as np
from datetime import datetime
from pathlib import Path

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    sd = None
    sf = None

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/device_diagnostic.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeviceDiagnostic:
    """Diagnostique les périphériques biométriques du système"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.python_version = platform.python_version()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'os': self.os_type,
            'python_version': self.python_version,
            'cameras': [],
            'microphones': [],
            'permissions': {},
            'recommendations': []
        }
        
    def run_full_diagnostic(self) -> dict:
        """Exécute le diagnostic complet"""
        logger.info("Démarrage du diagnostic complet des périphériques")
        
        print("\n" + "="*60)
        print("🔍 DIAGNOSTIC DES PÉRIPHÉRIQUES BIOMÉTRIQUES")
        print("="*60)
        
        # Infos système
        self._print_system_info()
        
        # Diagnostic des caméras
        print("\n📷 Diagnostic des caméras...")
        self._diagnose_cameras()
        
        # Diagnostic des microphones
        print("\n🎤 Diagnostic des microphones...")
        self._diagnose_microphones()
        
        # Vérification des permissions
        print("\n🔐 Vérification des permissions...")
        self._check_permissions()
        
        # Générer les recommandations
        self._generate_recommendations()
        
        # Afficher le résumé
        self._print_summary()
        
        # Sauvegarder le rapport
        self._save_report()
        
        return self.results
    
    def _print_system_info(self):
        """Affiche les infos système"""
        print(f"\n🖥️  Système d'exploitation: {self.os_type}")
        print(f"   Version Python: {self.python_version}")
        print(f"   OpenCV version: {cv2.__version__}")
        if sd:
            print(f"   sounddevice version: {sd.__version__}")
        else:
            print("   ⚠️  sounddevice non installé")
    
    def _diagnose_cameras(self):
        """Détecte et teste les caméras"""
        cameras_found = []
        
        # Essayer les différents index de caméra
        for i in range(10):  # Tester jusqu'à 10 caméras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Obtenir les propriétés
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                camera_info = {
                    'index': i,
                    'resolution': f'{width}x{height}',
                    'fps': fps if fps > 0 else 'N/A',
                    'accessible': True,
                    'status': '✅ Accessible'
                }
                
                # Test de capture
                try:
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        camera_info['capture_test'] = 'Réussi'
                        print(f"\n  ✅ Caméra {i} détectée")
                        print(f"     Résolution: {camera_info['resolution']}")
                        print(f"     FPS: {camera_info['fps']}")
                    else:
                        camera_info['capture_test'] = 'Échoué'
                        camera_info['status'] = '⚠️  Détectée mais capture échouée'
                        print(f"\n  ⚠️  Caméra {i} détectée (capture échouée)")
                except Exception as e:
                    camera_info['capture_test'] = f'Erreur: {str(e)}'
                    logger.warning(f"Erreur lors du test de caméra {i}: {e}")
                
                cap.release()
                cameras_found.append(camera_info)
            else:
                cap.release()
        
        if not cameras_found:
            print("\n  ❌ Aucune caméra détectée")
            self.results['recommendations'].append(
                "❌ Aucune caméra détectée - Vérifiez les connexions matérielles"
            )
        
        self.results['cameras'] = cameras_found
    
    def _diagnose_microphones(self):
        """Détecte et teste les microphones"""
        if not sd:
            print("\n  ❌ sounddevice non installé")
            print("     Installez: pip install sounddevice soundfile scipy")
            self.results['microphones'] = []
            return
        
        try:
            devices = sd.query_devices()
            mics = []
            
            if isinstance(devices, dict):
                devices = [devices]
            
            for i, device in enumerate(devices):
                # Vérifier si c'est un périphérique d'entrée
                if device.get('max_input_channels', 0) > 0:
                    mic_info = {
                        'index': i,
                        'name': device.get('name', f'Microphone {i}'),
                        'channels': device.get('max_input_channels', 1),
                        'sample_rate': device.get('default_samplerate', 44100),
                        'accessible': True,
                        'status': '✅ Accessible'
                    }
                    mics.append(mic_info)
                    print(f"\n  ✅ Micro {i}: {mic_info['name']}")
                    print(f"     Canaux: {mic_info['channels']}")
                    print(f"     Taux d'échantillonnage: {mic_info['sample_rate']} Hz")
            
            if not mics:
                print("\n  ❌ Aucun microphone détecté")
                self.results['recommendations'].append(
                    "❌ Aucun microphone détecté - Vérifiez les connexions matérielles"
                )
            
            self.results['microphones'] = mics
            
        except Exception as e:
            logger.error(f"Erreur lors du diagnostic des microphones: {e}")
            print(f"\n  ❌ Erreur: {str(e)}")
    
    def _check_permissions(self):
        """Vérifie les permissions d'accès aux périphériques"""
        permissions = {}
        
        if self.os_type == 'Windows':
            permissions = self._check_windows_permissions()
        elif self.os_type == 'Linux':
            permissions = self._check_linux_permissions()
        elif self.os_type == 'Darwin':
            permissions = self._check_macos_permissions()
        
        self.results['permissions'] = permissions
    
    def _check_windows_permissions(self) -> dict:
        """Vérifie les permissions Windows"""
        permissions = {
            'os': 'Windows',
            'camera': 'À vérifier dans Paramètres > Confidentialité > Caméra',
            'microphone': 'À vérifier dans Paramètres > Confidentialité > Microphone',
            'instructions': [
                '1. Ouvrir Paramètres Windows',
                '2. Aller à Confidentialité et sécurité',
                '3. Vérifier que l\'application a accès à la caméra',
                '4. Vérifier que l\'application a accès au microphone'
            ]
        }
        
        print("\n  📋 Instructions Windows:")
        for instruction in permissions['instructions']:
            print(f"     {instruction}")
        
        return permissions
    
    def _check_linux_permissions(self) -> dict:
        """Vérifie les permissions Linux"""
        permissions = {
            'os': 'Linux',
            'video_group': self._check_user_group('video'),
            'audio_group': self._check_user_group('audio'),
            'instructions': [
                'Ajouter l\'utilisateur aux groupes vidéo et audio:',
                'sudo usermod -a -G video $USER',
                'sudo usermod -a -G audio $USER',
                'Puis se reconnecter ou utiliser: newgrp video && newgrp audio'
            ]
        }
        
        print("\n  📋 Status des groupes:")
        print(f"     Groupe vidéo: {'✅ OK' if permissions['video_group'] else '❌ Non'}")
        print(f"     Groupe audio: {'✅ OK' if permissions['audio_group'] else '❌ Non'}")
        
        return permissions
    
    def _check_macos_permissions(self) -> dict:
        """Vérifie les permissions macOS"""
        try:
            # Vérifier avec tccutil (nécessite sudo)
            result = subprocess.run(
                ['tccutil', 'status', 'kTCCServiceCamera'],
                capture_output=True,
                text=True,
                timeout=5
            )
            camera_status = 'granted' in result.stdout
        except:
            camera_status = None
        
        try:
            result = subprocess.run(
                ['tccutil', 'status', 'kTCCServiceMicrophone'],
                capture_output=True,
                text=True,
                timeout=5
            )
            mic_status = 'granted' in result.stdout
        except:
            mic_status = None
        
        permissions = {
            'os': 'macOS',
            'camera': 'Granted' if camera_status else 'Unknown',
            'microphone': 'Granted' if mic_status else 'Unknown',
            'instructions': [
                'Autorisation automatique via la boîte de dialogue système',
                'Ou: Système > Sécurité & Confidentialité > Caméra/Microphone'
            ]
        }
        
        return permissions
    
    def _check_user_group(self, group_name: str) -> bool:
        """Vérifie si l'utilisateur fait partie d'un groupe"""
        try:
            result = subprocess.run(
                ['groups'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return group_name in result.stdout
        except:
            return False
    
    def _generate_recommendations(self):
        """Génère des recommandations basées sur le diagnostic"""
        recommendations = self.results['recommendations'].copy()
        
        # Vérifier les caméras
        if not self.results['cameras']:
            recommendations.append("❌ Aucune caméra détectée")
        elif not any(c.get('capture_test') == 'Réussi' for c in self.results['cameras']):
            recommendations.append("⚠️  Les caméras sont détectées mais les tests de capture échouent")
        
        # Vérifier les microphones
        if not self.results['microphones']:
            recommendations.append("❌ Aucun microphone détecté")
        
        # Recommandations spécifiques à l'OS
        if self.os_type == 'Linux':
            perms = self.results['permissions']
            if not perms.get('video_group'):
                recommendations.append("⚠️  Ajoutez votre utilisateur au groupe 'video'")
            if not perms.get('audio_group'):
                recommendations.append("⚠️  Ajoutez votre utilisateur au groupe 'audio'")
        
        self.results['recommendations'] = recommendations
    
    def _print_summary(self):
        """Affiche le résumé du diagnostic"""
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DU DIAGNOSTIC")
        print("="*60)
        
        print(f"\n📷 Caméras: {len(self.results['cameras'])}")
        for cam in self.results['cameras']:
            status = "✅" if cam.get('capture_test') == 'Réussi' else "⚠️"
            print(f"   {status} Caméra {cam['index']}: {cam['resolution']} @ {cam['fps']} FPS")
        
        print(f"\n🎤 Microphones: {len(self.results['microphones'])}")
        for mic in self.results['microphones']:
            print(f"   ✅ {mic['name']} ({mic['channels']} ch)")
        
        if self.results['recommendations']:
            print("\n💡 Recommandations:")
            for rec in self.results['recommendations']:
                print(f"   {rec}")
        else:
            print("\n✅ Aucun problème détecté!")
        
        print("\n" + "="*60)
    
    def _save_report(self):
        """Sauvegarde le rapport en JSON"""
        report_dir = Path('logs')
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"device_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Rapport sauvegardé: {report_file}")
            logger.info(f"Diagnostic sauvegardé: {report_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
    
    def get_primary_camera(self) -> int:
        """Retourne l'index de la caméra primaire"""
        if self.results['cameras']:
            return self.results['cameras'][0]['index']
        return -1
    
    def get_primary_microphone(self) -> int:
        """Retourne l'index du microphone primaire"""
        if self.results['microphones']:
            return self.results['microphones'][0]['index']
        return -1


if __name__ == '__main__':
    diagnostic = DeviceDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    # Retourner le code de succès/échec
    if diagnostic.results['cameras'] and diagnostic.results['microphones']:
        sys.exit(0)
    else:
        sys.exit(1)

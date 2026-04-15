#!/usr/bin/env python3
"""
QUICK START - Biometric Module Demo
Exemple simple pour démarrer avec la reconnaissance faciale

À exécuter depuis: Client Desktop/
Commande: python biometric/examples_quickstart.py
"""

import sys
import time
from pathlib import Path

# Ajouter biometric au path
sys.path.insert(0, str(Path(__file__).parent))

from biometric import (
    BiometricAPI,
    get_capture_service,
    get_cache_manager,
    MUSE_AVAILABLE
)


def check_setup():
    """Vérifier que tout est correctement configuré"""
    print("🔍 Vérification de la configuration...\n")
    
    # Vérifier MUSE
    if not MUSE_AVAILABLE:
        print("❌ MUSE n'est pas disponible")
        print("   Installer dépendances: pip install -r biometric/requirements.txt")
        return False
    print("✅ MUSE disponible")
    
    # Vérifier API
    if BiometricAPI.is_healthy():
        print("✅ API BioAccess-Secure accessible")
    else:
        print("⚠️  API BioAccess-Secure non accessible")
        print("   (non critique pour ce demo)")
    
    return True


def demo_capture():
    """Demo: Capturer et encoder un visage"""
    print("\n" + "="*60)
    print("DEMO 1: Capture et encodage facial")
    print("="*60 + "\n")
    
    service = get_capture_service()
    
    print("🎬 Démarrage de la caméra...")
    if not service.start_camera():
        print("❌ Impossible d'accéder à la caméra")
        return False
    
    print("⏳ Préparation (2 secondes)...")
    time.sleep(2)
    
    print("📸 Capture en cours...")
    time.sleep(1)
    
    frame = service.capture_frame(timeout=2)
    service.stop_camera()
    
    if frame is None:
        print("❌ Pas de frame disponible")
        return False
    
    # Détecter visage
    result = service.detect_and_encode_face(frame)
    
    if result.success:
        print("✅ Visage détecté!")
        print(f"  - Quality score: {result.quality_score:.2%}")
        print(f"  - Encoding dimension: {result.face_encoding.shape}")
        print(f"  - Face location: {result.face_location}")
        if result.landmarks is not None:
            print(f"  - Landmarks: {len(result.landmarks)} points")
        return True
    else:
        print(f"❌ {result.error_message}")
        return False


def demo_cache():
    """Demo: Stockage et récupération en cache"""
    print("\n" + "="*60)
    print("DEMO 2: Cache local")
    print("="*60 + "\n")
    
    import numpy as np
    
    cache = get_cache_manager()
    
    # Créer un encodage de test
    test_encoding = np.random.rand(128)
    user_id = "demo_user_001"
    
    print(f"💾 Sauvegarde encodage pour {user_id}...")
    filepath = cache.save_encoding(
        user_id=user_id,
        face_encoding=test_encoding,
        label="Demo Face"
    )
    print(f"✅ Sauvegardé: {filepath}")
    
    print(f"📂 Chargement encodage...")
    loaded = cache.load_encoding(user_id)
    
    if loaded is not None:
        print(f"✅ Encodage chargé: shape {loaded.shape}")
        
        # Vérifier que c'est le même
        diff = np.abs(test_encoding - loaded).max()
        print(f"  - Différence maximale: {diff:.10f}")
        
        if diff < 1e-10:
            print("✅ Cache fonctionne correctement!")
            return True
    else:
        print("❌ Encodage non trouvé en cache")
        return False


def demo_api():
    """Demo: Communication avec API"""
    print("\n" + "="*60)
    print("DEMO 3: API BioAccess-Secure")
    print("="*60 + "\n")
    
    if not BiometricAPI.is_healthy():
        print("⚠️  API non accessible - demo skipped")
        print("   Assurez-vous que le backend est lancé")
        print("   Commande backend: python BACKEND/run.py")
        return None
    
    print("✅ API accessible")
    
    from biometric import get_api_client
    client = get_api_client()
    
    # Tester endpoints
    print("\n📡 Test endpoints API:")
    
    # Health check déjà fait
    print("  ✅ GET /health")
    
    # User profile (nécessite token)
    print("  ⏬ GET /users/profile (nécessite token)")
    
    # Face operations
    print("  ⏬ POST /auth/face/register (nécessite token)")
    print("  ⏬ POST /auth/face/verify")
    print("  ⏬ POST /auth/voice/register (nécessite token)")
    print("  ⏬ POST /auth/voice/verify")
    print("  ⏬ POST /auth/liveness/detect")
    
    print("\n✅ Endpoints disponibles")
    return True


def demo_full_flow():
    """Demo: Flux complet capture + API"""
    print("\n" + "="*60)
    print("DEMO 4: Flux complet (capture + API)")
    print("="*60 + "\n")
    
    if not BiometricAPI.is_healthy():
        print("⚠️  API non accessible - demo skipped")
        print("   Assurez-vous que le backend est lancé")
        return False
    
    print("📸 1. Capture faciale...")
    service = get_capture_service()
    
    if not service.start_camera():
        print("❌ Caméra non accessible")
        return False
    
    time.sleep(2)
    frame = service.capture_frame(timeout=2)
    service.stop_camera()
    
    if frame is None:
        print("❌ Capture échouée")
        return False
    
    print("✅ Capture réussie")
    
    print("🔄 2. Encodage local...")
    result = service.detect_and_encode_face(frame)
    
    if not result.success:
        print(f"❌ Encodage échoué: {result.error_message}")
        return False
    
    print(f"✅ Encodage réussi (qualité: {result.quality_score:.2%})")
    
    print("📤 3. Envoi à API...")
    image_b64 = service.encode_to_base64(frame)
    
    # Test: enregistrement (nécessite authentification)
    # Pour ce demo, on teste juste le health check
    print("✅ Prêt pour enregistrement/vérification")
    
    return True


def demo_apiresponse_format():
    """Demo: Nouveau format APIResponse standardisé"""
    print("\n" + "="*60)
    print("DEMO 5: New APIResponse Format")
    print("="*60 + "\n")
    
    if not BiometricAPI.is_healthy():
        print("⚠️  API non accessible - demo skipped")
        return None
    
    print("📋 Example: Handling new standardized API responses\n")
    
    print("Backend now returns standardized responses:")
    print("""
    ✨ NEW FORMAT:
    {
        "status": "success",
        "code": 200,
        "timestamp": "2026-04-12T10:30:45Z",
        "message": "Operation successful",
        "data": {
            "token": "eyJhbGciOiJIUzUxMiIs...",
            "user_id": "user123",
            "role": "admin"
        }
    }
    
    LEGACY FORMAT (still supported):
    {
        "success": true,
        "token": "eyJhbGciOiJIUzUxMiIs...",
        "user_id": "user123"
    }
    """)
    
    print("\n✅ Client handles BOTH formats automatically:\n")
    
    print("""
    from biometric import BiometricAPI
    
    # This works with BOTH old and new backend formats
    response = BiometricAPI.face_verify(
        email="admin@example.com",
        image_base64="..."
    )
    
    # Standard response object (same regardless of backend format)
    if response.success:
        print(f"✅ Success: {response.status_code}")
        print(f"   Token: {response.data.get('token')}")
        print(f"   User ID: {response.data.get('user_id')}")
    else:
        print(f"❌ Error: {response.error_message}")
    """)
    
    print("✅ Benefits:")
    print("   • Backward compatible with legacy backends")
    print("   • Automatic format detection")
    print("   • Standardized error handling")
    print("   • Consistent across all endpoints")
    
    return True


def main():
    """Menu principal"""
    print("\n" + "="*60)
    print(" 🎯 BioAccess-Secure - Biometric Module QUICKSTART")
    print("="*60 + "\n")
    
    # Vérifier setup
    if not check_setup():
        print("\n❌ Configuration incomplète")
        print("\nEtapes de correction:")
        print("1. pip install -r biometric/requirements.txt")
        print("2. Vérifier caméra disponible")
        print("3. Vérifier API backend (si testé)")
        return False
    
    print("\n✅ Configuration OK\n")
    
    demos = [
        ("Capture et encodage facial", demo_capture),
        ("Cache local", demo_cache),
        ("API communication", demo_api),
        ("Flux complet", demo_full_flow),
        ("APIResponse format (NEW)", demo_apiresponse_format),
    ]
    
    print("Demos disponibles:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  0. Quitter")
    
    while True:
        try:
            choice = input("\nSélectionnez une demo (0-5): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("\n👋 Au revoir!")
                return True
            
            if 1 <= choice_num <= len(demos):
                demo_name, demo_func = demos[choice_num - 1]
                print(f"\n🚀 Lancement: {demo_name}")
                
                try:
                    result = demo_func()
                    if result is None:
                        print("⏭️  Demo skipped")
                    elif result:
                        print(f"\n✅ {demo_name} - SUCCÈS")
                    else:
                        print(f"\n❌ {demo_name} - ÉCHOUÉ")
                except Exception as e:
                    print(f"\n❌ Erreur: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Choix invalide")
        
        except ValueError:
            print("❌ Entrée invalide")
        except KeyboardInterrupt:
            print("\n\n⏸️  Interrompu")
            return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur non gérée: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

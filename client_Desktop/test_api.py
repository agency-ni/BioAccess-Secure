#!/usr/bin/env python3
"""
Script de test de l'API BioAccess Secure
Vérifie la connectivité et la disponibilité des endpoints
"""

import requests
import json
from config import API_BASE_URL, API_TIMEOUT, API_KEY

def test_health():
    """Tester la disponibilité de l'API"""
    print("\n🔍 Test de santé de l'API...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=API_TIMEOUT)
        if response.status_code == 200:
            print("✅ API ACCESSIBLE")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API répondu avec {response.status_code}")
            return False
    except requests.ConnectionError:
        print(f"❌ Impossible de se connecter à {API_BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_endpoints():
    """Tester les endpoints disponibles"""
    endpoints = [
        ('GET', '/health'),
        ('GET', '/auth/me'),
    ]
    
    print("\n📋 Test des endpoints...")
    
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    for method, endpoint in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        print(f"\n   {method:6} {endpoint:30}", end=" ")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=API_TIMEOUT)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json={}, timeout=API_TIMEOUT)
            
            if response.status_code < 400:
                print(f"✅ {response.status_code}")
            else:
                print(f"⚠️  {response.status_code}")
        
        except Exception as e:
            print(f"❌ {str(e)[:50]}")

def display_config():
    """Afficher la configuration actuelle"""
    print("\n⚙️  Configuration actuelle:")
    print(f"   API_BASE_URL:    {API_BASE_URL}")
    print(f"   API_TIMEOUT:     {API_TIMEOUT}s")
    print(f"   API_KEY:         {API_KEY[:20]}..." if len(API_KEY) > 20 else f"   API_KEY:         {API_KEY}")

def main():
    """Fonction principale"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     🔐 BioAccess Secure - API Test Tool               ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    display_config()
    
    # Tests
    health_ok = test_health()
    
    if health_ok:
        test_endpoints()
        print("\n✅ L'API est prête à l'emploi!")
        return 0
    else:
        print("\n❌ L'API n'est pas accessible")
        print("   Assurez-vous que le serveur Flask est en cours d'exécution:")
        print(f"   cd BACKEND && python run.py")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())

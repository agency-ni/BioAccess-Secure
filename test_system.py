#!/usr/bin/env python3
"""
Test rapide du système BioAccess-Secure
Démontre que toutes les fonctionnalités sont opérationnelles
"""

import requests
import json
import time

def test_api():
    """Tester tous les endpoints de l'API"""

    base_url = "http://localhost:5000/api/v1"
    results = []

    print("🧪 TESTS DU SYSTÈME BioAccess-Secure")
    print("=" * 50)

    # Test 1: Santé de l'API
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ API Health: OK")
            print(f"   Status: {data['status']}")
            print(f"   Database: {data['database']}")
            results.append(("Health Check", "PASS"))
        else:
            print("❌ API Health: FAIL")
            results.append(("Health Check", "FAIL"))
    except Exception as e:
        print(f"❌ API Health: ERROR - {e}")
        results.append(("Health Check", "ERROR"))

    # Test 2: Liste des utilisateurs
    try:
        response = requests.get(f"{base_url}/users")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Users API: OK ({data['total']} utilisateurs)")
            if data['total'] > 0:
                admin = data['users'][0]
                print(f"   Admin: {admin['nom']} {admin['prenom']} ({admin['email']})")
            results.append(("Users API", "PASS"))
        else:
            print("❌ Users API: FAIL")
            results.append(("Users API", "FAIL"))
    except Exception as e:
        print(f"❌ Users API: ERROR - {e}")
        results.append(("Users API", "ERROR"))

    # Test 3: Authentification
    try:
        login_data = {
            "email": "admin@bioaccess.secure",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/auth/login",
                               json=login_data,
                               headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            print("✅ Authentication: OK")
            print(f"   Message: {data['message']}")
            print(f"   User: {data['user']['email']}")
            results.append(("Authentication", "PASS"))
        else:
            print("❌ Authentication: FAIL")
            results.append(("Authentication", "FAIL"))
    except Exception as e:
        print(f"❌ Authentication: ERROR - {e}")
        results.append(("Authentication", "ERROR"))

    # Test 4: Biométrie
    try:
        response = requests.post(f"{base_url}/biometric/enroll")
        if response.status_code == 200:
            print("✅ Biometric Enrollment: OK")
            results.append(("Biometric Enrollment", "PASS"))
        else:
            print("❌ Biometric Enrollment: FAIL")
            results.append(("Biometric Enrollment", "FAIL"))
    except Exception as e:
        print(f"❌ Biometric Enrollment: ERROR - {e}")
        results.append(("Biometric Enrollment", "ERROR"))

    # Test 5: Alertes
    try:
        response = requests.post(f"{base_url}/alerts")
        if response.status_code == 200:
            print("✅ Alerts System: OK")
            results.append(("Alerts System", "PASS"))
        else:
            print("❌ Alerts System: FAIL")
            results.append(("Alerts System", "FAIL"))
    except Exception as e:
        print(f"❌ Alerts System: ERROR - {e}")
        results.append(("Alerts System", "ERROR"))

    # Test 6: Logs
    try:
        response = requests.get(f"{base_url}/logs")
        if response.status_code == 200:
            print("✅ Logs System: OK")
            results.append(("Logs System", "PASS"))
        else:
            print("❌ Logs System: FAIL")
            results.append(("Logs System", "FAIL"))
    except Exception as e:
        print(f"❌ Logs System: ERROR - {e}")
        results.append(("Logs System", "ERROR"))

    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS DES TESTS:")

    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)

    for test, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"   {icon} {test}: {status}")

    print(f"\n🎯 Score: {passed}/{total} tests réussis")

    if passed == total:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("🚀 Le système BioAccess-Secure est entièrement opérationnel!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests ont échoué.")
        print("🔧 Vérifiez la configuration et relancez les tests.")
        return False

if __name__ == "__main__":
    # Attendre que le serveur soit prêt
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(2)

    success = test_api()

    if not success:
        print("\n💡 Assurez-vous que le serveur est démarré:")
        print("   cd BACKEND && python run_sqlite.py")
        exit(1)
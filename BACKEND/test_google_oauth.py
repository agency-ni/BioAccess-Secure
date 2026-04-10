#!/usr/bin/env python
"""
Test endpoint Google OAuth
Run: python test_google_oauth.py
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("TEST Endpoint Google OAuth")
print("=" * 60)

# Test 1: Endpoint existe?
print("\n1. Vérification si l'endpoint existe...")
try:
    response = requests.options(f"{BASE_URL}/api/v1/auth/google", timeout=5)
    print(f"   ✓ Endpoint accessible (Status: {response.status_code})")
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    print("   → Vérifiez que le backend est lancé sur http://localhost:5000")

# Test 2: Test avec credential invalide
print("\n2. Test avec credential invalide...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/google",
        json={"credential": "test-invalid-token"},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Réponse: {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

# Test 3: Test sans credential
print("\n3. Test sans credential...")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/google",
        json={},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    print(f"   Réponse: {response.text}")
except Exception as e:
    print(f"   ✗ Erreur: {e}")

print("\n" + "=" * 60)
print("Tests terminés")
print("=" * 60)

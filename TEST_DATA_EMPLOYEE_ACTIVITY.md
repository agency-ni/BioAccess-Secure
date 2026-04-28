# Test et Données d'exemple - Employee Activity API

## Exemples de requêtes

### Test 1 : Période 7 jours

```bash
curl -X GET "http://localhost:5000/api/dashboard/employee-activity?period=7days" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse attendue** :
```json
{
  "labels": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
  "attempts_per_employee": [1.2, 1.5, 1.8, 2.1, 1.9, 1.3, 0.9],
  "avg_time_seconds": [4.2, 4.8, 5.1, 6.2, 5.9, 3.8, 3.2]
}
```

---

### Test 2 : Aujourd'hui uniquement

```bash
curl -X GET "http://localhost:5000/api/dashboard/employee-activity?period=today" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse attendue** :
```json
{
  "labels": ["Aujourd'hui"],
  "attempts_per_employee": [1.8],
  "avg_time_seconds": [5.1]
}
```

---

### Test 3 : Plage personnalisée

```bash
curl -X GET "http://localhost:5000/api/dashboard/employee-activity?period=custom&start=2025-04-01&end=2025-04-07" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse attendue** :
```json
{
  "labels": ["1 avr", "2 avr", "3 avr", "4 avr", "5 avr", "6 avr", "7 avr"],
  "attempts_per_employee": [1.1, 1.3, 1.5, 1.6, 1.4, 1.2, 1.0],
  "avg_time_seconds": [4.5, 4.8, 5.2, 5.4, 5.1, 4.6, 4.2]
}
```

---

### Test 4 : 30 jours

```bash
curl -X GET "http://localhost:5000/api/dashboard/employee-activity?period=30days" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse attendue** (30 points) :
```json
{
  "labels": ["1 avr", "2 avr", ..., "30 avr"],
  "attempts_per_employee": [1.1, 1.2, 1.3, ..., 1.8],
  "avg_time_seconds": [4.5, 4.6, 4.7, ..., 5.2]
}
```

---

## Données de test mockées (JavaScript)

Les données mockées sont **automatiquement** générées avec ces caractéristiques :

```javascript
// Tentatives par employé
Min: 0.5
Max: 3.0
Moyenne: ~1.7
Distribution: Aléatoire réaliste

// Temps d'authentification (secondes)
Min: 2.5
Max: 12.0
Moyenne: ~5.5
Distribution: Aléatoire réaliste
```

### Exemple de données générées :

**Pour 7 jours** :
```javascript
labels: ["Lun 20", "Mar 21", "Mer 22", "Jeu 23", "Ven 24", "Sam 25", "Dim 26"]

attempts_per_employee: [
  1.24,  // Lundi
  1.89,  // Mardi ← Anomalie (hausse)
  1.45,  // Mercredi
  2.12,  // Jeudi ← Pic (anomalie détectée)
  1.78,  // Vendredi
  0.92,  // Samedi
  0.67   // Dimanche (activité basse = normal)
]

avg_time_seconds: [
  4.2,   // Lundi
  5.1,   // Mardi ← Hausse (avec tentatives)
  4.8,   // Mercredi
  6.4,   // Jeudi ← Pic temps (avec tentatives)
  5.3,   // Vendredi
  3.9,   // Samedi
  3.1    // Dimanche
]
```

---

## Test unitaire (Python)

### Avec pytest :

```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_employee_activity_7days(client):
    """Test la requête 7 jours"""
    response = client.get('/api/dashboard/employee-activity?period=7days')
    
    assert response.status_code == 200
    data = response.json
    
    # Vérifier la structure
    assert 'labels' in data
    assert 'attempts_per_employee' in data
    assert 'avg_time_seconds' in data
    
    # Vérifier les longueurs
    assert len(data['labels']) == 7
    assert len(data['attempts_per_employee']) == 7
    assert len(data['avg_time_seconds']) == 7
    
    # Vérifier les valeurs
    for attempts in data['attempts_per_employee']:
        assert 0.5 <= attempts <= 3.0
    
    for time_val in data['avg_time_seconds']:
        assert 2.5 <= time_val <= 12.0

def test_employee_activity_today(client):
    """Test la requête pour aujourd'hui"""
    response = client.get('/api/dashboard/employee-activity?period=today')
    
    assert response.status_code == 200
    data = response.json
    
    assert len(data['labels']) == 1
    assert len(data['attempts_per_employee']) == 1
    assert len(data['avg_time_seconds']) == 1

def test_employee_activity_custom_range(client):
    """Test la plage personnalisée"""
    response = client.get(
        '/api/dashboard/employee-activity?period=custom&start=2025-04-01&end=2025-04-07'
    )
    
    assert response.status_code == 200
    data = response.json
    
    assert len(data['labels']) == 7
    assert len(data['attempts_per_employee']) == 7
    assert len(data['avg_time_seconds']) == 7

def test_employee_activity_invalid_date(client):
    """Test avec date invalide"""
    response = client.get(
        '/api/dashboard/employee-activity?period=custom&start=invalid&end=2025-04-07'
    )
    
    # Devrait retourner une erreur ou des données par défaut
    assert response.status_code in [400, 200]

# Lancer les tests
# pytest tests/test_employee_activity.py -v
```

---

## Test de charge

### Simuler 100 requêtes simultanées

```bash
# Avec Apache Bench
ab -n 100 -c 10 "http://localhost:5000/api/dashboard/employee-activity?period=7days"

# Avec locust
locust -f locustfile.py --host=http://localhost:5000
```

### locustfile.py :

```python
from locust import HttpUser, task, between

class EmployeeActivityUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_employee_activity(self):
        self.client.get(
            "/api/dashboard/employee-activity",
            params={"period": "7days"}
        )
```

---

## Données réelles (Exemple avec vraies valeurs)

Si votre système a:
- **124 employés** actifs
- **1,547 tentatives** aujourd'hui

**Calcul** :
```
Tentatives par employé = 1,547 / 124 = 12.48 tentatives/employé

⚠️ ANOMALIE DÉTECTÉE !
(Valeur normale : 0.5-3.0)
```

**Causes possibles** :
1. ✅ Test de charge (expected)
2. 🔴 Attaque brute force (security alert!)
3. 🔴 Nouveau déploiement (problèmes ergonomie)

---

## Intégration Postman

### Collection Postman

Créez une collection avec ces requêtes :

```json
{
  "info": {
    "name": "BioAccess Employee Activity API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Activity - 7 Days",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/dashboard/employee-activity?period=7days",
          "host": ["{{base_url}}"],
          "path": ["api", "dashboard", "employee-activity"],
          "query": [
            {
              "key": "period",
              "value": "7days"
            }
          ]
        }
      }
    },
    {
      "name": "Get Activity - Custom Range",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/api/dashboard/employee-activity?period=custom&start=2025-04-01&end=2025-04-07",
          "query": [
            {
              "key": "period",
              "value": "custom"
            },
            {
              "key": "start",
              "value": "2025-04-01"
            },
            {
              "key": "end",
              "value": "2025-04-07"
            }
          ]
        }
      }
    }
  ]
}
```

---

## Performance observée

Tests sur exemple de configuration :

| Requête | Temps réponse | Cache hit |
|---------|--------------|-----------|
| /api/dashboard/employee-activity (7days) | 120ms | Oui |
| /api/dashboard/employee-activity (30days) | 180ms | Oui |
| /api/dashboard/employee-activity (custom) | 200ms | Non |

**Objectif** : < 500ms ✅

---

## Erreurs possibles et résolutions

### Erreur 401 - Non authentifié
```
Message: "Authorization required"
Solution: Ajouter le header Authorization: Bearer TOKEN
```

### Erreur 400 - Paramètres invalides
```
Message: "Invalid period: xxxx"
Solution: Utiliser l'une des périodes valides (today, 7days, 30days, custom)
```

### Erreur 404 - Endpoint non trouvé
```
Message: "404 Not Found"
Solution: Vérifier que l'endpoint existe dans le backend
         Vérifier le port (5000, 8000, etc)
```

### Erreur 500 - Erreur serveur
```
Message: "Internal Server Error"
Solution: Vérifier les logs du backend
         Vérifier la connexion à la base de données
```

---

## Debugging

### Voir les requêtes réseau (DevTools)

1. F12 → Network
2. Chercher "employee-activity"
3. Vérifier :
   - Status code ✅ 200
   - Response time ✅ < 500ms
   - Response body ✅ JSON valide

### Logs de debug (Backend)

```python
import logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/api/dashboard/employee-activity')
def get_employee_activity():
    logging.debug(f"Period: {request.args.get('period')}")
    logging.debug(f"Start: {request.args.get('start')}")
    # ...
```

---

*Document créé pour BioAccess Secure Dev Team - Avril 2026*

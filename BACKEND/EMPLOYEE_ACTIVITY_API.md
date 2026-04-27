# Exemple d'implémentation Backend - API Employee Activity

Ce fichier montre comment implémenter l'endpoint `/api/dashboard/employee-activity` dans le backend Flask/FastAPI.

## Option 1 : Flask (Recommandé)

```python
from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func

@app.route('/api/dashboard/employee-activity', methods=['GET'])
def get_employee_activity():
    """
    Retourne les statistiques d'activité des employés
    
    Paramètres:
    - period: 'today', 'yesterday', '7days', '30days', 'month', 'custom'
    - start: date format YYYY-MM-DD (si custom)
    - end: date format YYYY-MM-DD (si custom)
    """
    
    # Récupérer les paramètres
    period = request.args.get('period', '7days')
    start_date_str = request.args.get('start')
    end_date_str = request.args.get('end')
    
    # Déterminer la plage de dates
    today = datetime.now().date()
    
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday
    elif period == '7days':
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == '30days':
        start_date = today - timedelta(days=29)
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=6)
        end_date = today
    
    # Générer les labels de jours
    labels = []
    current = start_date
    while current <= end_date:
        if (end_date - start_date).days <= 30:
            label = current.strftime('%a').capitalize()  # Lun, Mar, etc
            if (end_date - start_date).days > 7:
                label += f" {current.day}"  # Lun 15
        else:
            label = current.strftime('%d %b')  # 15 Apr
        
        labels.append(label)
        current += timedelta(days=1)
    
    # Récupérer les données depuis la base de données
    attempts_per_employee = []
    avg_time_seconds = []
    
    current = start_date
    while current <= end_date:
        # ===== A ADAPTER SELON VOTRE SCHEMA DE BASE DE DONNÉES =====
        
        # 1. Compter le nombre d'employés actifs ce jour-là
        # (employés ayant fait au moins une tentative)
        active_employees = db.session.query(
            func.count(func.distinct(Log.employee_id))
        ).filter(
            func.date(Log.timestamp) == current,
            Log.status.in_(['success', 'failed'])  # Adaptez selon votre schema
        ).scalar() or 1
        
        # 2. Compter le total des tentatives ce jour-là
        total_attempts = db.session.query(func.count(Log.id)).filter(
            func.date(Log.timestamp) == current,
            Log.status.in_(['success', 'failed'])
        ).scalar() or 0
        
        # 3. Calculer le temps moyen d'authentification
        # (si vous avez un champ duration dans Log)
        total_auth_time = db.session.query(
            func.sum(Log.duration)  # duration en secondes
        ).filter(
            func.date(Log.timestamp) == current,
            Log.status == 'success'
        ).scalar() or 0
        
        successful_attempts = db.session.query(func.count(Log.id)).filter(
            func.date(Log.timestamp) == current,
            Log.status == 'success'
        ).scalar() or 1
        
        # Calculer les moyennes
        attempts_avg = round(total_attempts / active_employees, 2) if active_employees > 0 else 0
        time_avg = round(total_auth_time / successful_attempts, 1) if successful_attempts > 0 else 0
        
        attempts_per_employee.append(attempts_avg)
        avg_time_seconds.append(time_avg)
        
        current += timedelta(days=1)
    
    return jsonify({
        'labels': labels,
        'attempts_per_employee': attempts_per_employee,
        'avg_time_seconds': avg_time_seconds
    }), 200
```

## Option 2 : FastAPI

```python
from fastapi import FastAPI, Query
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func

@app.get("/api/dashboard/employee-activity")
async def get_employee_activity(
    period: str = Query("7days", regex="^(today|yesterday|7days|30days|month|custom)$"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None)
):
    """
    Retourne les statistiques d'activité des employés
    """
    
    today = datetime.now().date()
    
    # Déterminer la plage de dates (même logique que Flask)
    period_map = {
        'today': (today, today),
        'yesterday': (today - timedelta(days=1), today - timedelta(days=1)),
        '7days': (today - timedelta(days=6), today),
        '30days': (today - timedelta(days=29), today),
        'month': (today.replace(day=1), today),
    }
    
    if period == 'custom' and start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
    else:
        start_date, end_date = period_map.get(period, (today - timedelta(days=6), today))
    
    # Générer labels et requêtes (voir Option 1 pour la logique)
    # ...
    
    return {
        'labels': labels,
        'attempts_per_employee': attempts_per_employee,
        'avg_time_seconds': avg_time_seconds
    }
```

## Points clés

### 1. **Adaptez le schéma**
- `Log.timestamp` : colonne timestamp des tentatives
- `Log.employee_id` : clé étrangère vers l'employé
- `Log.status` : 'success' ou 'failed'
- `Log.duration` : durée en secondes (peut être calculée si absent)

### 2. **Performances**
```python
# Utilisez des index pour optimiser
db.create_index('idx_log_timestamp_employee', Log.timestamp, Log.employee_id)
```

### 3. **Gestion des erreurs**
```python
try:
    # Votre logique...
except Exception as e:
    return {'error': str(e)}, 500
```

### 4. **Cache recommandé** (30 secondes)
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/dashboard/employee-activity')
@cache.cached(timeout=30)  # Cache 30 secondes
def get_employee_activity():
    # ...
```

### 5. **Tests unitaires**
```python
def test_employee_activity_today():
    response = client.get('/api/dashboard/employee-activity?period=today')
    assert response.status_code == 200
    data = response.json()
    assert 'labels' in data
    assert 'attempts_per_employee' in data
    assert 'avg_time_seconds' in data
    assert len(data['labels']) == len(data['attempts_per_employee'])
    assert len(data['labels']) == len(data['avg_time_seconds'])

def test_employee_activity_custom_range():
    response = client.get(
        '/api/dashboard/employee-activity?period=custom&start=2025-04-01&end=2025-04-07'
    )
    assert response.status_code == 200
```

---

## Checklist d'implémentation

- [ ] Endpoint GET `/api/dashboard/employee-activity` créé
- [ ] Support des paramètres `period` et `start/end`
- [ ] Calcul correct de `attempts_per_employee`
- [ ] Calcul correct de `avg_time_seconds`
- [ ] Format de réponse JSON matching
- [ ] Gestion des erreurs/edge cases
- [ ] Tests unitaires passants
- [ ] Cache activé (30 secondes)
- [ ] Performance < 500ms

---

## Intégration continue

Quand l'endpoint est prêt, le dashboard passera automatiquement des **données mockées** aux **données réelles**.

Pas besoin de modifier le frontend !

# Graphique Activité Employés - Documentation

## Vue d'ensemble

Le graphique **Activité des employés** est une nouvelle section du dashboard BioAccess Secure qui affiche deux métriques comparatives essentielles pour la détection d'anomalies.

---

## Métriques affichées

### 1. **Moyenne de tentatives par employé**
- **Unité** : Nombre (tentatives)
- **Axe** : Gauche (Y)
- **Couleur** : Indigo (#4f46e5)
- **Interprétation** : 
  - Hausse → Plus d'authentifications par employé
  - Baisse → Moins d'authentifications

### 2. **Temps moyen d'authentification**
- **Unité** : Secondes
- **Axe** : Droite (Y)
- **Couleur** : Ambre (#f59e0b)
- **Interprétation** :
  - Hausse → Authentifications plus lentes
  - Baisse → Authentifications plus rapides

---

## Détection d'anomalies

Le système détecte automatiquement les anomalies basées sur l'écart-type :

```
Anomalies = Points dont la valeur s'écarte de plus de 1.5× l'écart-type de la moyenne
```

**Cas d'usage RSSI** :
- ⚠️ **Hausse tentatives + Hausse temps** → Problème d'ergonomie (mauvais placement caméra)
- ⚠️ **Hausse tentatives + Temps stable** → Tentative de brute force
- ⚠️ **Baisse temps + Hausse échecs** → Possible fraude (photo plutôt que visage)

---

## Sélecteur de période

### Périodes pré-définies
- **Aujourd'hui** : Les données du jour actuel
- **Hier** : Les données du jour précédent
- **7 jours** : Les 7 derniers jours (par défaut)
- **30 jours** : Les 30 derniers jours
- **Ce mois** : Depuis le 1er du mois courant
- **Personnalisé** : Plage de dates personnalisée

### Mode personnalisé
Si "Personnalisé" est sélectionné :
1. Deux datepickers apparaissent (début et fin)
2. L'utilisateur sélectionne les dates
3. Un bouton "Appliquer" charge les données

---

## Actualisation automatique

### Comportement
- **Période actuelle** (incluant aujourd'hui) : Rafraîchissement automatique toutes les **30 secondes**
- **Période historique** : Pas de rafraîchissement automatique
- **Manuel** : Bouton "Rafraîchir" toujours disponible

### Bouton Rafraîchissement
- Animation de rotation lors du chargement
- État désactivé pendant le chargement
- Fonctionne pour toutes les périodes

---

## Données

### Mode Mockées (Développement)
Données cohérentes intégrées directement en JavaScript :

```javascript
// Tentatives par employé : 0.5 à 3
attemptsPerEmployee = [0.8, 1.2, 1.5, 2.1, 1.9, 1.3, 0.9]

// Temps d'auth : 2 à 12 secondes
avgTimeSeconds = [4.2, 4.8, 5.1, 6.2, 5.9, 3.8, 3.2]
```

### Mode API (Production)

**Endpoint** : `GET /api/dashboard/employee-activity`

**Paramètres** :
- `period=7days` (ou any period)
- OU `start=YYYY-MM-DD&end=YYYY-MM-DD` (pour personnalisé)

**Réponse attendue** (JSON) :
```json
{
  "labels": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
  "attempts_per_employee": [1.2, 1.5, 1.8, 2.1, 1.9, 1.3, 0.9],
  "avg_time_seconds": [4.2, 4.8, 5.1, 6.2, 5.9, 3.8, 3.2]
}
```

---

## Statistiques affichées

### Bas du graphique
| Section | Affichage | Données |
|---------|-----------|---------|
| Moy. tentatives/employé | Chiffre + Tendance % | Moyenne + Variation |
| Temps moyen (sec) | Chiffre + Tendance % | Moyenne + Variation |
| Anomalies détectées | Nombre | Count des anomalies |

---

## Légende et couleurs

- **Bleu Indigo** : Tentatives par employé
- **Ambre/Orange** : Temps d'authentification

Points du graphique :
- Rayon normal : 5px
- Au survol : 7px
- Bordure blanche : 2px

---

## Intégration Chart.js

### Configuration
- **Type** : Line Chart
- **Interpolation** : Tension 0.4 (courbe lissée)
- **Mode interaction** : Index (affichage de deux valeurs)
- **Responsive** : Oui
- **Axes Y distincts** : Oui (échelles différentes)

### Tooltip personnalisé
Affiche :
- Label du jour/date
- "Tentatives par employé: X.XX tent."
- "Temps moyen: Y.Y sec"

---

## Mode sombre

Le graphique s'adapte automatiquement au mode sombre :
- Grilles visibles sur l'axe Y gauche
- Grille masquée sur l'axe Y droite
- Couleurs des axes adaptées
- Fond transparent

---

## Cas d'erreur et fallback

Si l'API n'est pas disponible :
1. Log dans la console : "API non disponible, utilisation des données mockées"
2. Affichage des données mockées
3. Le graphique fonctionne normalement

---

## Implémentation backend requise

Pour activer les données réelles, implémentez :

**Pseudo-code** :
```python
@app.get("/api/dashboard/employee-activity")
def get_employee_activity(period: str = "7days", start: str = None, end: str = None):
    # Récupérer la plage de dates selon period ou start/end
    
    # Calculer :
    # 1. Nombre d'employés actifs par jour
    # 2. Total tentatives d'authentification par jour
    # 3. Temps total d'authentification par jour
    
    # Retourner :
    attempts_per_employee = [total_attempts / active_employees for each day]
    avg_time_seconds = [total_auth_time / total_attempts for each day]
    
    return {
        "labels": ["Lun", "Mar", ...],
        "attempts_per_employee": [...],
        "avg_time_seconds": [...]
    }
```

---

## FAQ

### Q: Pourquoi deux axes Y ?
**R** : Les deux métriques n'ont pas la même échelle (tentatives : 0-3, temps : 0-12). Deux axes permettent une visualisation claire des deux courbes.

### Q: Le graphique ne se rafraîchit pas automatiquement ?
**R** : Vérifiez que la période sélectionnée inclut aujourd'hui (Aujourd'hui, 7 jours, 30 jours, Ce mois). Les périodes historiques n'ont pas de rafraîchissement auto.

### Q: Comment tester les données mockées ?
**R** : Dès que vous ouvrez le dashboard, les données mockées s'affichent. Pas besoin de backend.

---

## Version
- **Créé** : Avril 2026
- **Dernière mise à jour** : Avril 2026
- **Statut** : Production-ready avec mockées, prêt pour API réelle

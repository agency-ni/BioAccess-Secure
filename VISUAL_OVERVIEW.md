# Vue d'ensemble visuelle - Graphique Activité Employés

## 🖼️ Layout du dashboard

```
┌─────────────────────────────────────────────────────────────────────────┐
│ BioAccess Secure - Dashboard                          🔔 🌙             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│ Bonjour, Admin Système                                                  │
│ Précédente connexion : 25 avr 2026                   [Plage horaire]    │
│                                                                           │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│ │ 124 employés│ │ 1547 tent.  │ │ 94% succès  │ │ 3 alertes   │        │
│ │ actifs      │ │ aujourd'hui  │ │ (obj: 95%)  │ │ en attente  │        │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │
│                                                                           │
│ ╔══════════════════════════════════════════════════════════════════════╗ │
│ ║ 📊 ACTIVITÉ DES EMPLOYÉS                       [7 jours ▼] [⟳ Ref] ║ │
│ ║─────────────────────────────────────────────────────────────────────║ │
│ ║                    GRAPHIQUE À DEUX AXES Y                         ║ │
│ ║                                                                     ║ │
│ ║  3.0 │     ●    ●                            12 sec              ║ │
│ ║      │   ●   ●   ●──●                                           ║ │
│ ║  2.0 │  ●         ●  ●───                  8 sec ●─●──          ║ │
│ ║      │                  ●──●                     ●    ●  ●─     ║ │
│ ║  1.0 │─────────────────────                 4 sec─────────●──   ║ │
│ ║      │Axe Y Gauche    Axe Y Droite                                ║ │
│ ║      │Tentatives     Temps (sec)                                  ║ │
│ ║      ├───────────────────────────────────────────────────────    ║ │
│ ║      │ Lun  Mar  Mer  Jeu  Ven  Sam  Dim                         ║ │
│ ║      │                                                             ║ │
│ ║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║ │
│ ║  ◯ Moy. tentatives: 1.62 tent.  ▲ +5.2%                        ║ │
│ ║  ◯ Temps moyen:      4.8 sec    ▼ -2.1%                        ║ │
│ ║  ◯ Anomalies:        2          À investiguer                   ║ │
│ ╚══════════════════════════════════════════════════════════════════════╝ │
│                                                                           │
│ ┌─────────────────────────────────────┐ ┌──────────────────────────────┐ │
│ │ 📈 Activité                         │ │ 🥧 Répartition               │ │
│ │ (courbe tentatives + succès)        │ │ (succès 94% / échecs 6%)     │ │
│ │                                     │ │                              │ │
│ └─────────────────────────────────────┘ └──────────────────────────────┘ │
│                                                                           │
│ ┌─────────────────────────────────────┐ ┌──────────────────────────────┐ │
│ │ 🚨 Alertes récentes                 │ │ ⚠️ Top 5 échecs              │ │
│ │                                     │ │                              │ │
│ └─────────────────────────────────────┘ └──────────────────────────────┘ │
│                                                                           │
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ 📋 Historique des connexions admin                                   │ │
│ │                                                                        │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Contrôles détaillés

### Sélecteur de période

```
┌─ 📅 7 jours ▼
├─ Aujourd'hui
├─ Hier
├─ 7 derniers jours ✓ (défaut)
├─ 30 derniers jours
├─ Ce mois
└─ Personnalisé...
   ├─ [Date début] — [Date fin] [Appliquer]
```

### Bouton Rafraîchir

```
┌──────────────────────────────┐
│ [⟳ Rafraîchir]  ← Clique    │
│  ↻ (animation lors du chargement) │
└──────────────────────────────┘
```

---

## 📊 Deux courbes superposées

### Axe Y Gauche (Bleu Indigo)

```
Tentatives par employé
Range: 0 à 3

Calcul: Total tentatives du jour / Nombre employés actifs

Exemple:
- 1000 tentatives / 100 employés = 10 tent/employé
- Mais normalized entre 0.5 et 3 en conditions normales
```

### Axe Y Droite (Ambre)

```
Temps moyen d'authentification (secondes)
Range: 0 à 12 sec

Calcul: Temps total authentifications / Nombre authentifications

Exemple:
- 500 sec de temps total / 100 auth = 5 sec/auth
- Normal: 2-6 secondes
- Alerte si > 8 sec = problème ergonomique
```

---

## 🔍 Détection d'anomalies

### Algorithme

```
Pour chaque métrique (tentatives, temps):
  1. Calculer moyenne des 7 jours
  2. Calculer écart-type
  3. Identifier points où: |valeur - moyenne| > 1.5 × écart-type
  4. Ces points = ANOMALIES

Exemple sur 7 jours:
  Tentatives: [1.0, 1.2, 1.1, 2.8, 1.3, 1.0, 1.1]
  Moyenne = 1.36
  Écart-type = 0.74
  Seuil = 1.36 + 1.5×0.74 = 2.47
  
  2.8 > 2.47 → ANOMALIE DÉTECTÉE ⚠️
```

---

## 📈 Tendances

### Calcul

```
Tendance = (Valeur dernière - Valeur première) / Valeur première × 100%

Exemple:
  Jour 1: 1.0 tentative/employé
  Jour 7: 1.2 tentatives/employé
  
  Tendance = (1.2 - 1.0) / 1.0 × 100 = +20%
  
Affichage: ▲ +20% (en ROUGE = mauvais)
ou
           ▼ -5% (en VERT = bon)
```

---

## 💾 Données mockées

### Structure JavaScript

```javascript
const mockData = {
  labels: ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
  
  attempts_per_employee: [
    1.2,  // Lundi
    1.5,  // Mardi
    1.8,  // Mercredi
    2.1,  // Jeudi
    1.9,  // Vendredi
    1.3,  // Samedi
    0.9   // Dimanche
  ],
  
  avg_time_seconds: [
    4.2,  // Lundi
    4.8,  // Mardi
    5.1,  // Mercredi
    6.2,  // Jeudi
    5.9,  // Vendredi
    3.8,  // Samedi
    3.2   // Dimanche
  ]
};
```

### Plage de valeurs

```
Tentatives/employé:
  Min: 0.5    (très peu d'activité)
  Max: 3.0    (pic d'activité)
  Normal: 1.0-2.0

Temps auth (sec):
  Min: 2.5    (très rapide, suspect?)
  Max: 12.0   (très lent, problème?)
  Normal: 4-6 secondes
```

---

## 🎨 Couleurs et styles

### Palette

```css
/* Courbe Tentatives */
Border: #4f46e5 (Indigo)
Background: rgba(79, 70, 229, 0.05)
Point: #4f46e5

/* Courbe Temps */
Border: #f59e0b (Ambre)
Background: rgba(245, 158, 11, 0.05)
Point: #f59e0b

/* Anomalies */
Text: #EAB308 (Jaune/Ambre)

/* Tendances */
Hausse: #EF4444 (Rouge)
Baisse: #10B981 (Vert)
```

### Mode sombre

```
Background: #111827 (Dark gray)
Text: #f3f4f6 (Light gray)
Grille: rgba(79, 70, 229, 0.1)
Legendes: Adaptées au thème
```

---

## 🔄 Cycle de rafraîchissement

### Timeline

```
T=0:00 Chargement initial
       ↓ (données mockées)
       Graphique affiche 7 jours par défaut

T=0:30 Rafraîchissement auto #1 (si période = "7 jours")
       ↓ (nouvelles données mockées)
       Graphique se redraw

T=1:00 Rafraîchissement auto #2
       ↓
       ...

T=Anytime Clic sur "Rafraîchir" manuel
          ↓ (animation ⟳)
          Rechargement immédiat
```

### Règles

```
Auto-refresh = OUI si:
  ✓ Période = "Aujourd'hui"
  ✓ Période = "7 jours"
  ✓ Période = "30 jours"
  ✓ Période = "Ce mois"

Auto-refresh = NON si:
  ✗ Période = "Hier"
  ✗ Période = "Personnalisé" (historique)

Intervalle: 30 secondes (configurable)
```

---

## 📞 Interaction utilisateur

### Scénario typique RSSI

```
1. Ouvre le dashboard
   → Voit graphique 7 jours par défaut

2. Remarque anomalie: 2 points détectés
   → Lit: "Anomalies détectées: 2"

3. Clique "Aujourd'hui"
   → Graphique se redraw avec 1 point

4. Voit: ▲ +25% en tentatives, ▼ -3% en temps
   → Diagnostic: Possible brute force

5. Clique "⟳ Rafraîchir"
   → Animation de rotation
   → Données actualisées

6. Note les employés (via autre vue)
   → Contacte IT pour investigation
```

---

## 🧪 Points de test

### Test 1: Changement de période
```
Action: Cliquer "30 jours"
Attente: 
  - Menu se ferme
  - Graphique affiche 30 points (1 par jour)
  - Labels changent
  - Anomalies recalculées
```

### Test 2: Rafraîchissement auto
```
Action: Sélectionner "7 jours"
        Attendre 30 secondes
Attente:
  - Sans interaction
  - Graphique se met à jour
  - Nouvelles données affichées
```

### Test 3: Mode sombre
```
Action: Cliquer 🌙
Attente:
  - Graphique reste lisible
  - Couleurs contrastées
  - Pas de texte blanc sur fond blanc
```

### Test 4: Personnalisé
```
Action: Cliquer "Personnalisé"
        Sélectionner dates (01/04 au 07/04)
        Cliquer "Appliquer"
Attenta:
  - Datepickers apparaissent
  - Labels deviennent "1 avr", "2 avr", etc
  - Graphique affiche 7 jours selectionnés
```

---

## 🚀 Prochains développements

### Quand l'API sera prête

```
Maintenant (Mockées):
  GET /api/dashboard/employee-activity?period=7days
  → Retourne données JavaScript locales

Plus tard (Réelle):
  GET /api/dashboard/employee-activity?period=7days
  → Appelle backend
  → Récupère vraies données DB
  → Code JavaScript = IDENTIQUE
```

### Aucun changement nécessaire au frontend !

---

## 📋 Checklist visuelle

Pour vérifier que le graphique fonctionne correctement :

- [ ] **Graphique s'affiche** avec courbes bleue et orange
- [ ] **Labels** (Lun Mar Mer...) sont lisibles
- [ ] **Légende** au-dessus affiche les deux métriques
- [ ] **Axes Y** sont distincts (gauche vs droite)
- [ ] **Tooltip** affiche valeurs précises au survol
- [ ] **Statistiques** en bas = chiffres corrects
- [ ] **Anomalies** = nombre > 0 (données mockées)
- [ ] **Bouton "Rafraîchir"** tourne lors du clic
- [ ] **Sélecteur période** ferme après choix
- [ ] **Mode sombre** maintient la lisibilité
- [ ] **Mobile** : Graphique responsive
- [ ] **Auto-refresh** : Données changent après 30 sec

---

*Créé : Avril 2026 - BioAccess Secure Team*

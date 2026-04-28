# Guide RSSI - Interprétation du graphique Activité Employés

## Objectif
Le graphique **Activité des employés** aide le RSSI à détecter rapidement les anomalies de sécurité biométrique en comparant deux métriques clés.

---

## Les deux métriques

```
┌─────────────────────────────────────────────────────────────┐
│ GRAPHIQUE ACTIVITÉ EMPLOYÉS (7 jours par défaut)            │
│                                                              │
│ Axe Y Gauche (Bleu)    │ Axe Y Droite (Orange)             │
│ Tentatives par employé │ Temps d'authentification (sec)     │
│                                                              │
│ 3.0 ─────────                 12s                          │
│ 2.5 ────●───●──●─────        10s  ────●────●──           │
│ 2.0 ───   ●   ●  ●────────   8s ──●    ●    ●  ●─       │
│ 1.5 ──●      ●    ●────      6s   ●──●              ●─   │
│ 1.0 ─────────────────────    4s      ────────●──●──    ── │
│ 0.5 ─────────────────────    2s                          │
└─────────────────────────────────────────────────────────────┘
  Lun  Mar  Mer  Jeu  Ven  Sam  Dim
```

---

## Cas d'usage : Détection d'anomalies

### Cas 1️⃣ : Problème d'ergonomie 🔴 HAUTE PRIORITÉ

**Symptôme** :
- ⬆️ Hausse des tentatives/employé
- ⬆️ Hausse du temps d'authentification

**Diagnostic possible** :
- Mauvais placement de la caméra
- Éclairage insuffisant
- Surface de capture sale/réfléchissante
- Logiciel obsolète

**Action RSSI** :
1. Vérifier la caméra/capteur biométrique
2. Nettoyer la surface de capture
3. Vérifier l'éclairage
4. Tester sur différents angles
5. Si toujours problématique → Remplacer le matériel

**Exemple graphique** :
```
Mardi: 2.8 tentatives, 8.2 sec  ← Anomalie détectée !
Mercredi: 2.9 tentatives, 8.5 sec  ← Anomalie détectée !
```

---

### Cas 2️⃣ : Tentative de brute force 🔴 HAUTE PRIORITÉ - SÉCURITÉ

**Symptôme** :
- ⬆️ Hausse forte des tentatives/employé
- ➡️ Temps d'authentification STABLE (pas de hausse)

**Diagnostic possible** :
- Attaque par dictionnaire/reconnaissance faciale
- Robot testant plusieurs identités
- Usurpation d'identité systématique

**Action RSSI** :
1. **Immédiatement** : Consulter les logs d'accès
   ```
   SELECT * FROM logs WHERE date = TODAY AND status = 'failed' 
   ORDER BY failure_count DESC LIMIT 10
   ```
2. Identifier l'employé/la borne concernée
3. Alerter le service de sécurité
4. Bloquer temporairement la borne si nécessaire
5. Augmenter les délais entre tentatives (rate limiting)

**Exemple graphique** :
```
Jeudi: 3.2 tentatives, 4.1 sec  ← Tentative brute force !
(3.2 tentatives mais temps COURT = pas d'ajustement humain)
```

---

### Cas 3️⃣ : Possible fraude 🟠 PRIORITÉ MOYENNE-HAUTE

**Symptôme** :
- ➡️ Temps d'authentification en BAISSE
- ⬆️ Taux d'échecs augmente (à vérifier dans autre graphique)

**Diagnostic possible** :
- Utilisation de photos au lieu du visage réel
- Deep fake tentant d'exploiter un pattern
- Tentative rapide avec leurre

**Action RSSI** :
1. Revérifier avec les logs : taux d'échecs constaté ?
2. Consulter les enregistrements vidéo (si disponibles)
3. Vérifier les heures des tentatives (hors horaires ?)
4. Contacter l'employé concerné
5. Tester la biométrie en présence physique

**Exemple graphique** :
```
Samedi: 0.7 tentatives, 2.1 sec  ← Temps TRÈS court !
(+ taux d'échec = 85%)
```

---

### Cas 4️⃣ : Amélioration normale 🟢 À SURVEILLER

**Symptôme** :
- ⬇️ Baisse progressive des tentatives/employé
- ⬇️ Baisse progressive du temps d'authentification

**Diagnostic** :
- Les employés maîtrisent mieux le système
- Apprentissage des modèles biométriques
- Habituation au processus

**Action RSSI** :
- ✅ Normal, rien à faire
- 📊 Excellente tendance

**Exemple graphique** :
```
Semaine 1: 2.0 tentatives, 5.5 sec
Semaine 2: 1.8 tentatives, 5.2 sec
Semaine 3: 1.5 tentatives, 4.8 sec  ← Bonne évolution !
```

---

### Cas 5️⃣ : Pic ponctuel 🟡 INVESTIGATION

**Symptôme** :
- 🔺 Un pic isolé sur UNE SEULE journée
- Pas de récurrence

**Diagnostic possible** :
- Problème technique temporaire
- Jour de formation d'un grand nombre d'employés
- Évenement spécial (nombreux visiteurs)

**Action RSSI** :
1. Vérifier les notes/calendrier
2. Consulter les logs de ce jour
3. Si problème technique → vérifier les alertes système
4. Sinon → À surveiller pour voir si récurrence

---

## Dashboard : Où voir les infos ?

### En bas du graphique :

```
┌─────────────────────────────────────────────────────────┐
│ Moy. tentatives/employé: 1.62 tent.  ▲ +5.2%           │
│ Temps moyen:              4.8 sec     ▼ -2.1%           │
│ Anomalies détectées:      2           À investiguer     │
└─────────────────────────────────────────────────────────┘
```

| Métrique | Signification | Action si ⬆️ | Action si ⬇️ |
|----------|---------------|-----------|-----------|
| **Moy. tentatives/employé** | Moyen. tentatives par employé | ⚠️ Investiguer | ✅ Bon signe |
| **Temps moyen (sec)** | Durée moyenne auth | ⚠️ Investiguer | ✅ Bon signe |
| **Anomalies détectées** | Nombre de points aberrants | ⚠️ Investiguer | ✅ Normal |

---

## Tutoriel rapide RSSI

### Étape 1 : Ouvrir le dashboard
- 🔗 Accès : Administration > Dashboard
- 📊 Scroll jusqu'au graphique "Activité des employés"

### Étape 2 : Choisir la période
- Par défaut : **7 jours**
- Pour incident : **Aujourd'hui** ou **Hier**
- Pour tendance : **30 jours**

### Étape 3 : Repérer les anomalies
1. Regarder le nombre en bas : "Anomalies détectées: X"
2. Visualiser sur le graphique (pic isolé)
3. Vérifier les tendances (▲▼)

### Étape 4 : Associer les deux courbes

| Courbe Bleu | Courbe Orange | Interprétation |
|-----------|---------------|-----------------|
| ⬆️ | ⬆️ | Problème ergonomique |
| ⬆️ | ➡️ | Brute force |
| ⬇️ | ⬇️ | Bon |
| ⬆️ | ⬇️ | Possible fraude |

### Étape 5 : Agir

```
Anomalie détectée ?
        ↓
   [Rafraîchir] (bouton)
        ↓
Réanalyser la période
        ↓
Si conforme → OK
Si persiste → Investiguer
```

---

## Interprétation rapide : Les 4 patterns

### Pattern A : V-Shape ✅ NORMAL

```
3 |     •
2 |   •   •
1 | •       •
  |_________
```

**Sens** : Légère récupération, normal

---

### Pattern B : Montée continue 🔴 ALERTE

```
3 |         •
2 |     •
1 | • •
  |_________
```

**Sens** : Problème croissant, investiguer immédiatement

---

### Pattern C : Plateau élevé 🟡 MONITORER

```
3 | • • •
2 | •   •
1 |
  |_________
```

**Sens** : Problème persistant, action requise

---

### Pattern D : Divergence 🔴 ANOMALIE

```
3 | •─────────    (tentatives ⬆️)
2 |      
1 | ─────•──────  (temps ⬇️)
  |_________
```

**Sens** : Les deux courbes se séparent = fraude possible

---

## Checklist d'investigation

Si anomalie détectée :

```
☐ 1. Identifier la date/période exakte
☐ 2. Consulter les logs : 
     SELECT * FROM logs WHERE DATE = ? ORDER BY timestamp
☐ 3. Vérifier les taux d'échec :
     SELECT COUNT(*) WHERE status = 'failed'
☐ 4. Identifier les employés concernés (top failures)
☐ 5. Vérifier l'état des caméras/capteurs
☐ 6. Consulter les alertes système
☐ 7. Analyser les patterns (même heure ? même lieu ?)
☐ 8. Contacter l'équipe support biométrique si nécessaire
☐ 9. Documenter l'incident
☐ 10. Résoudre et suivre la tendance
```

---

## Hotkeys & Raccourcis

| Raccourci | Action |
|-----------|--------|
| **Clic** sur "Rafraîchir" | Charger les données actuelles |
| **Choix période** | Actualise le graphique |
| **Survol courbe** | Affiche détails (tooltip) |

---

## Contactez le support

- 📧 **Email** : support-biometric@company.com
- 🔧 **Incident critique** : +33 X XX XX XX XX
- 🐛 **Bug graphique** : GitHub Issues (repo)

---

*Document créé pour BioAccess Secure RSSI - Avril 2026*

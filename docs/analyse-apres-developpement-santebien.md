# SanteBien - Analyse après développement centrée sur le modèle IA

Date : 16 juin 2026  
Projet : application web communautaire de santé  
Objectif : analyser le modèle IA selon la démarche du cours : baseline FP32, optimisation INT8, calculs avant/après, perte, green gates et CI/CD vert.

## 1. Périmètre du modèle

Le modèle ajouté à SanteBien sert à classer une question santé dans une catégorie.

Catégories :

- prévention ;
- nutrition ;
- mental ;
- dermatologie ;
- respiratoire ;
- orientation.

Point de sécurité : le modèle ne fournit aucun diagnostic médical. Il aide seulement à organiser les questions.

## 2. Mesure avant optimisation : FP32

| Indicateur | Valeur FP32 |
|---|---:|
| Taille modèle | 600 bytes |
| Accuracy échantillon | 100 % |
| Latence moyenne | 0,0195 ms |
| CO₂ par inférence | 9,8583e-12 kg CO₂eq |
| Inférences mesurées | 1500 |

Interprétation : c'est la baseline avant optimisation. Elle sert de référence pour mesurer les gains.

## 3. Optimisation appliquée : INT8

| Indicateur | Valeur INT8 |
|---|---:|
| Taille modèle | 154 bytes |
| Accuracy échantillon | 100 % |
| Accord FP32/INT8 | 100 % |
| Latence moyenne | 0,0253 ms |
| CO₂ par inférence | 1,2791e-11 kg CO₂eq |
| Inférences mesurées | 1500 |

Interprétation : la quantification INT8 réduit la taille numérique des poids du modèle.

## 4. Calculs avant/après

| Mesure | Avant FP32 | Après INT8 | Gain / perte |
|---|---:|---:|---:|
| Taille | 600 bytes | 154 bytes | -74,33 % |
| Accuracy | 100 % | 100 % | 0 point perdu |
| Accord des prédictions | - | 100 % | aucune divergence |
| Latence moyenne | 0,0195 ms | 0,0253 ms | +29,74 % |
| CO₂ par inférence | 9,8583e-12 kg | 1,2791e-11 kg | +29,74 % |

Conclusion : l'optimisation principale est la réduction de taille du modèle, avec une qualité stable sur l'échantillon. La latence augmente légèrement dans cette implémentation Python, mais reste largement sous le seuil fixé.

## 5. Analyse de la perte

La perte à surveiller après quantification est la perte de qualité.

Résultat :

- perte d'accuracy : 0 point ;
- divergence FP32/INT8 : 0 cas observé ;
- accuracy INT8 : 100 % ;
- accord FP32/INT8 : 100 %.

Limites :

- l'échantillon contient 6 exemples ;
- il faut ajouter davantage de questions réelles ;
- le modèle ne valide pas médicalement les contenus ;
- il sert uniquement à l'orientation.

## 6. Green gates modèle

| Gate | Résultat | Seuil | Statut |
|---|---:|---:|---|
| Compression INT8 | 74,33 % | ≥ 70 % | OK |
| Accord FP32/INT8 | 100 % | ≥ 95 % | OK |
| Accuracy INT8 | 100 % | ≥ 95 % | OK |
| Taille INT8 | 154 bytes | ≤ 200 bytes | OK |
| Latence INT8 | 0,0253 ms | ≤ 0,1 ms | OK |
| CO₂ INT8 | 1,2791e-11 kg | ≤ 1e-10 kg | OK |

Sortie vérifiée :

```text
GREEN GATES OK
- Compression modele INT8: 74.33% >= 70.0%
- Accord FP32/INT8: 100.0% >= 95.0%
- Accuracy INT8: 100.0% >= 95.0%
- Taille INT8: 154 bytes <= 200.0 bytes
- Latence INT8: 0.0253 ms <= 0.1 ms
- CO2/inference INT8: 1.279e-11 kg <= 1e-10 kg
```

## 7. CI/CD vert

Workflow : `.github/workflows/green-ci.yml`

Étapes appliquées :

- installation avec cache pip ;
- compilation Python ;
- scan sécurité Bandit ;
- tests automatisés ;
- mesure modèle FP32/INT8 ;
- mesure API en contexte ;
- green gates modèle ;
- build Docker ;
- gate de taille d'image Docker.

Décision importante : la CI est maintenant centrée sur le modèle. Les mesures API/cache restent utiles, mais elles ne sont plus le cœur de l'analyse du cours.

## 8. Contexte API secondaire

| Indicateur API | Résultat |
|---|---:|
| P95 API | 0,288 ms |
| Cache hit rate | 98,02 % |
| Gain cache | -91,44 % |
| CO₂ par requête API | 6,34e-10 kg |

Interprétation : l'application autour du modèle reste légère et cohérente avec l'éco-conception.

## 9. Résultat fonctionnel

| Élément | État |
|---|---:|
| Application full-stack | OK |
| Authentification | OK |
| Questions / réponses | OK |
| Validation médecin | OK |
| Articles médecins | OK |
| Endpoint IA | OK |
| Bouton IA dans le front | OK |
| Tests automatisés | 7/7 |

## 10. Conclusion

Le livrable répond à l'objectif du cours :

- baseline FP32 mesurée ;
- optimisation INT8 appliquée ;
- gain de taille calculé ;
- perte de qualité vérifiée ;
- CO₂ estimé ;
- green gates automatisées ;
- CI/CD vert configuré.

Résultat final :

```text
Modèle INT8 = -74,33 % de taille, 100 % d'accord FP32/INT8, 0 point d'accuracy perdu.
```

# Synthèse complète - IA frugale et DevOps Vert appliqués au modèle SanteBien

Date : 16 juin 2026  
Projet : SanteBien  
Objectif : présenter une analyse centrée sur le modèle IA, avec baseline FP32, optimisation INT8, mesures avant/après, pertes, green gates et CI/CD vert.

## 1. Résumé du projet

SanteBien est une application web communautaire de santé inspirée de Stack Overflow.

Fonctionnalités principales :

- inscription et connexion ;
- publication de questions santé ;
- réponses et commentaires ;
- demande de profil médecin vérifié ;
- validation par administrateur ;
- articles publiés par médecins vérifiés ;
- mini-modèle IA d'orientation des questions ;
- API FastAPI, PostgreSQL, cache Redis/mémoire, Docker.

## 2. Rôle du modèle IA

Le modèle ne fait pas de diagnostic médical.

Il classe une question dans une catégorie :

- prévention ;
- nutrition ;
- mental ;
- dermatologie ;
- respiratoire ;
- orientation.

Pourquoi ce choix est frugal :

- modèle très petit ;
- explicable ;
- pas besoin de GPU ;
- pas de gros modèle externe ;
- quantifiable en INT8 ;
- mesurable dans la CI.

## 3. Concepts du cours appliqués

| Concept du cours | Application dans SanteBien |
|---|---|
| Mesurer avant optimisation | Baseline modèle FP32 mesurée |
| Optimiser | Quantification INT8 |
| Comparer avant/après | Tableau FP32 vs INT8 |
| Mesurer la perte | Accuracy et accord FP32/INT8 |
| Mesurer l'énergie | CO₂ estimé par inférence |
| Green gates | Seuils bloquants sur compression, accuracy, latence, CO₂ |
| CI/CD vert | Workflow GitHub Actions avec jobs ciblés |
| Monitoring frugal | `/metrics`, `/api/monitoring/summary`, contrôle CI |
| Sécurité frugale | Bandit, secrets hors code, modèle non diagnostique |
| Déploiement sobre | Docker multi-stage, image contrôlée |

## 4. Baseline avant optimisation : FP32

| Indicateur | Résultat FP32 |
|---|---:|
| Taille modèle | 600 bytes |
| Accuracy échantillon | 100 % |
| Latence moyenne | 0,0195 ms |
| CO₂ par inférence | 9,8583e-12 kg CO₂eq |
| Inférences mesurées | 1500 |

Interprétation : le modèle est déjà très petit, mais le cours demande de comparer une version de référence avec une version optimisée.

## 5. Optimisation : quantification INT8

| Indicateur | Résultat INT8 |
|---|---:|
| Taille modèle | 154 bytes |
| Accuracy échantillon | 100 % |
| Accord FP32/INT8 | 100 % |
| Latence moyenne | 0,0253 ms |
| CO₂ par inférence | 1,2791e-11 kg CO₂eq |

Interprétation : INT8 réduit fortement la taille du modèle et conserve les mêmes prédictions sur l'échantillon.

## 6. Comparaison avant/après

| Mesure | FP32 avant | INT8 après | Gain / perte |
|---|---:|---:|---:|
| Taille | 600 bytes | 154 bytes | -74,33 % |
| Accuracy | 100 % | 100 % | 0 point perdu |
| Accord prédictions | - | 100 % | aucune divergence |
| Latence moyenne | 0,0195 ms | 0,0253 ms | +29,74 % |
| CO₂ par inférence | 9,8583e-12 kg | 1,2791e-11 kg | +29,74 % |

Résultat principal :

```text
INT8 = -74,33 % de taille avec 0 perte d'accuracy observée.
Perte acceptée : latence Python +29,74 %, mais toujours sous le seuil de 0,1 ms.
```

## 7. Analyse de la perte

Dans ce cours, la perte à surveiller après quantification est surtout une perte de qualité.

Résultat :

- accuracy FP32 : 100 % ;
- accuracy INT8 : 100 % ;
- accord FP32/INT8 : 100 % ;
- perte d'accuracy observée : 0 point.

Limites :

- échantillon encore petit ;
- modèle volontairement simple ;
- pas de validation médicale automatique ;
- besoin de tester plus de questions réelles.

## 8. Green gates modèle

Les green gates bloquent une régression si le modèle devient plus lourd, moins fiable, plus lent ou plus coûteux.

| Gate | Résultat | Seuil | Statut |
|---|---:|---:|---|
| Compression INT8 | 74,33 % | ≥ 70 % | OK |
| Accord FP32/INT8 | 100 % | ≥ 95 % | OK |
| Accuracy INT8 | 100 % | ≥ 95 % | OK |
| Taille INT8 | 154 bytes | ≤ 200 bytes | OK |
| Latence INT8 | 0,0253 ms | ≤ 0,1 ms | OK |
| CO₂ INT8 | 1,2791e-11 kg | ≤ 1e-10 kg | OK |

Sortie actuelle :

```text
GREEN GATES OK
- Compression modele INT8: 74.33% >= 70.0%
- Accord FP32/INT8: 100.0% >= 95.0%
- Accuracy INT8: 100.0% >= 95.0%
- Taille INT8: 154 bytes <= 200.0 bytes
- Latence INT8: 0.0253 ms <= 0.1 ms
- CO2/inference INT8: 1.279e-11 kg <= 1e-10 kg
```

## 9. CI/CD vert

Le workflow `.github/workflows/green-ci.yml` applique les normes du cours :

- déclenchement limité aux fichiers utiles ;
- annulation des runs obsolètes ;
- cache pip ;
- compilation ;
- tests automatisés ;
- scan sécurité Bandit ;
- mesure FP32/INT8 avec `scripts.measure_ai_model` ;
- vérification monitoring avec `scripts.check_monitoring` ;
- green gates modèle avec `scripts.green_gates` ;
- build Docker ;
- contrôle de taille d'image.

La CI est maintenant centrée sur le modèle : l'API/cache reste mesuré comme contexte, mais les gates principales sont FP32/INT8.

## 10. Monitoring frugal

Le monitoring est volontairement léger.

| Élément | Rôle |
|---|---|
| `/metrics` | Export Prometheus texte |
| `/api/monitoring/summary` | Résumé JSON lisible |
| `santebien_requests_total` | Nombre de requêtes observées |
| `santebien_request_latency_average_ms` | Latence moyenne |
| `santebien_co2_total_kg` | CO₂ estimé cumulé |
| `santebien_model_size_bytes` | Taille FP32 et INT8 |
| `santebien_model_size_reduction_percent` | Gain de taille du modèle |

Pourquoi c'est frugal :

- peu de métriques ;
- faible cardinalité ;
- pas de dashboard obligatoire ;
- compatible Prometheus/Grafana si le projet grandit ;
- vérifié automatiquement en CI.

## 11. Contexte API secondaire

Ces mesures montrent que l'application autour du modèle reste légère.

| Indicateur API | Résultat |
|---|---:|
| P95 API | 0,288 ms |
| Cache hit rate | 98,02 % |
| Gain cache | -91,44 % |
| CO₂ par requête API | 6,34e-10 kg |

À dire clairement : l'optimisation API est utile, mais le livrable principal du cours est l'analyse du modèle.

## 12. Phrase orale courte

> Nous avons appliqué la démarche IA frugale sur le modèle de SanteBien. La baseline FP32 pèse 600 bytes. Après quantification INT8, le modèle pèse 154 bytes, soit -74,33 %. L'accuracy reste à 100 % sur l'échantillon et l'accord FP32/INT8 est de 100 %. La latence INT8 est légèrement plus haute en Python, mais elle reste sous le seuil de 0,1 ms. Ces résultats sont protégés par des green gates dans la CI/CD verte et surveillés par un monitoring Prometheus léger.

## 13. Prochaines étapes

- augmenter l'échantillon de validation ;
- ajouter des questions réelles anonymisées ;
- suivre l'accuracy par catégorie ;
- mesurer après déploiement ;
- comparer éventuellement avec un modèle entraîné plus riche ;
- refuser un modèle plus lourd si le gain métier ne justifie pas le coût.

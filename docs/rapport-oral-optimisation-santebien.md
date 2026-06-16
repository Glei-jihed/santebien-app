# Rapport oral - Analyse modèle IA frugal SanteBien

## Message principal

L'objectif du cours est appliqué sur le modèle IA : mesurer une baseline FP32, optimiser en INT8, comparer avant/après, puis bloquer les régressions avec des green gates.

Résultat clé :

```text
Le modèle INT8 réduit la taille de 74,33 % sans perte d'accuracy observée.
```

## 1. Projet et rôle du modèle

Ce que je peux dire :

> SanteBien est une application santé communautaire. Le modèle IA ajouté ne donne aucun diagnostic médical. Il sert uniquement à classer une question dans une catégorie : prévention, nutrition, santé mentale, dermatologie, respiratoire ou orientation.

Pourquoi c'est prudent :

- le modèle aide à organiser les questions ;
- il ne remplace pas un médecin ;
- il affiche un message de sécurité ;
- il reste petit, explicable et mesurable.

## 2. Baseline avant optimisation : FP32

Ce que je peux dire :

> Nous avons d'abord mesuré le modèle en FP32, qui représente notre version avant optimisation.

| Indicateur | FP32 avant |
|---|---:|
| Taille modèle | 600 bytes |
| Accuracy échantillon | 100 % |
| Latence moyenne | 0,0195 ms |
| CO₂ par inférence | 9,8583e-12 kg CO₂eq |
| Inférences mesurées | 1500 |

## 3. Optimisation appliquée : INT8

Ce que je peux dire :

> Nous avons ensuite quantifié le modèle en INT8. Le principe est de stocker les poids avec moins de précision numérique pour réduire la taille et le coût d'exécution.

| Indicateur | INT8 après |
|---|---:|
| Taille modèle | 154 bytes |
| Accuracy échantillon | 100 % |
| Accord FP32/INT8 | 100 % |
| Latence moyenne | 0,0253 ms |
| CO₂ par inférence | 1,2791e-11 kg CO₂eq |

## 4. Comparaison avant/après

| Mesure | FP32 | INT8 | Gain / perte |
|---|---:|---:|---:|
| Taille | 600 bytes | 154 bytes | -74,33 % |
| Accuracy | 100 % | 100 % | 0 point perdu |
| Accord prédictions | - | 100 % | aucune divergence |
| Latence moyenne | 0,0195 ms | 0,0253 ms | +29,74 % |
| CO₂ par inférence | 9,8583e-12 kg | 1,2791e-11 kg | +29,74 % |

Phrase simple :

> On gagne surtout sur la taille du modèle : -74,33 %. La qualité reste stable. La latence INT8 est légèrement plus haute en Python, mais elle reste très faible et sous le seuil.

## 5. Analyse de la perte

Ce que je peux dire :

> La perte importante à surveiller après quantification est la perte de qualité. Ici, nous n'observons aucune perte sur l'échantillon : l'accuracy INT8 reste à 100 % et l'accord FP32/INT8 est aussi à 100 %.

Pertes restantes :

- l'échantillon de validation est petit ;
- le modèle est volontairement simple ;
- il faudra tester plus de questions réelles ;
- le modèle ne juge pas la validité médicale des réponses.

## 6. Green gates modèle

Ce que je peux dire :

> Les green gates empêchent de livrer une version moins frugale ou moins fiable.

| Gate | Résultat | Seuil | Statut |
|---|---:|---:|---|
| Compression INT8 | 74,33 % | ≥ 70 % | OK |
| Accord FP32/INT8 | 100 % | ≥ 95 % | OK |
| Accuracy INT8 | 100 % | ≥ 95 % | OK |
| Taille INT8 | 154 bytes | ≤ 200 bytes | OK |
| Latence INT8 | 0,0253 ms | ≤ 0,1 ms | OK |
| CO₂ INT8 | 1,2791e-11 kg | ≤ 1e-10 kg | OK |

## 7. CI/CD vert

Ce que je peux dire :

> Le workflow GitHub Actions exécute les tests, mesure le modèle FP32/INT8, puis lance les green gates. Si la compression, l'accuracy, l'accord, la taille, la latence ou le CO₂ régressent, le pipeline échoue.

Éléments appliqués :

- déclenchement limité aux fichiers utiles ;
- cache pip ;
- tests automatisés ;
- scan sécurité Bandit ;
- mesure modèle avec `scripts.measure_ai_model` ;
- green gates avec `scripts.green_gates` ;
- build Docker et contrôle de taille d'image.

## 8. Contexte API secondaire

Le cache API reste utile, mais ce n'est plus l'analyse principale.

| Indicateur API | Résultat |
|---|---:|
| P95 API | 0,288 ms |
| Cache hit rate | 98,02 % |
| Gain cache | -91,44 % |
| CO₂ par requête API | 6,34e-10 kg |

Phrase à dire :

> L'API est aussi légère, mais le livrable principal du cours est maintenant bien centré sur le modèle.

## 9. Conclusion orale

Version courte :

> Nous avons appliqué la démarche IA frugale sur un modèle réel de SanteBien. Nous avons mesuré le modèle FP32, puis nous l'avons quantifié en INT8. La taille passe de 600 bytes à 154 bytes, soit -74,33 %. L'accuracy reste à 100 % sur l'échantillon et l'accord FP32/INT8 est de 100 %, donc nous n'observons pas de perte de qualité. La latence INT8 est légèrement plus haute en Python, mais reste très faible et sous le seuil de 0,1 ms. Enfin, la CI/CD verte bloque toute régression avec des green gates centrées sur le modèle.

Version très courte :

> Notre optimisation principale est la quantification INT8 du modèle : -74,33 % de taille, 100 % d'accord FP32/INT8, et des green gates automatisées.

## 10. Questions possibles

### Est-ce que le modèle donne un diagnostic ?

Non. Il classe seulement les questions par catégorie. Il ne remplace jamais un médecin.

### Quelle est la perte après INT8 ?

Sur notre échantillon, aucune perte d'accuracy observée : FP32 = 100 %, INT8 = 100 %, accord = 100 %.

### Pourquoi ne pas utiliser un gros modèle ?

Parce que l'objectif est la frugalité. Un mini-modèle suffit pour classer les questions, coûte moins cher et reste explicable.

### Quel est le prochain travail ?

Augmenter l'échantillon de validation avec plus de questions réelles, puis recalculer accuracy, accord FP32/INT8, latence et CO₂.

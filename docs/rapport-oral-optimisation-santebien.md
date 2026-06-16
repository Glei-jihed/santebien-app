# Rapport oral simple - Optimisation SanteBien

## Message principal à retenir

Notre objectif de cours était de mesurer avant d'optimiser, appliquer une optimisation ciblée, puis prouver le gain avec des chiffres.

Sur SanteBien, nous avons optimisé le parcours le plus fréquent : la lecture répétée des questions et des articles. L'optimisation principale est le cache.

Résultat clé :

```text
Le cache réduit la latence moyenne de 92,30 %.
```

## 1. Présentation du projet

Ce que je peux dire :

> Notre projet s'appelle SanteBien. C'est une application web communautaire de santé, un peu comme Stack Overflow, mais pour poser des questions de santé, répondre, commenter et publier des articles. Les médecins peuvent demander un profil vérifié, et les administrateurs valident les justificatifs.

Stack technique :

- Backend : FastAPI.
- Base de données : PostgreSQL.
- Cache : Redis ou mémoire en local.
- Frontend : HTML, CSS, JavaScript.
- Déploiement : Docker, Fly.io, base Render PostgreSQL.

## 2. Objectif du cours appliqué au projet

Ce que je peux dire :

> L'objectif n'était pas seulement de développer l'application. L'objectif était surtout d'appliquer une démarche d'éco-conception : mesurer, identifier les pertes, optimiser, puis comparer les résultats avant/après.

Concepts utilisés :

- Profiling CPU avec `cProfile`.
- Mesure de latence.
- Mesure du cache hit rate.
- Estimation CO₂ avec CodeCarbon et headers applicatifs.
- Analyse de perte : cache miss, latence restante, CO₂ restant.
- Règle 80/20.
- Quick Win d'optimisation.

## 3. Problème identifié

Ce que je peux dire :

> Dans une application communautaire, les mêmes questions et articles peuvent être lus plusieurs fois. Si chaque lecture interroge la base de données, on consomme plus de CPU, plus d'I/O, plus de temps et donc plus d'énergie.

Problème technique :

- lecture répétée des mêmes questions ;
- risque de requêtes base inutiles ;
- latence plus élevée ;
- consommation plus forte.

## 4. Optimisation appliquée

Ce que je peux dire :

> Nous avons ajouté un cache sur les listes de questions, les détails des questions et les articles. Quand une question est lue une première fois, la réponse est stockée. Les lectures suivantes sont servies depuis le cache. Si quelqu'un ajoute un commentaire, vote ou publie un article, le cache concerné est invalidé.

Optimisations concrètes :

- cache liste des questions ;
- cache détail d'une question ;
- cache articles ;
- invalidation après création, commentaire, vote ou article ;
- validation Pydantic pour rejeter tôt les données invalides ;
- limite de résultats pour éviter de charger trop de données.

## 5. Résultats avant/après

Ce que je peux dire :

> Nous avons comparé deux scénarios : une lecture froide sans bénéfice du cache, puis une lecture chaude avec cache optimisé.

Résultats principaux :

| Mesure | Sans cache utile | Avec cache | Gain |
|---|---:|---:|---:|
| Latence moyenne | 2,7821 ms | 0,2143 ms | -92,30 % |
| P95 | 3,159 ms | 0,301 ms | -90,47 % |
| Latence maximale | 18,893 ms | 0,431 ms | -97,72 % |
| CO₂ estimé | 1,40647e-07 kg | 1,08370e-08 kg | -92,29 % |

Phrase simple à dire :

> Grâce au cache, on divise environ par 13 le coût moyen d'une lecture répétée.

## 6. Profiling CPU

Ce que je peux dire :

> Le profiling montre que le coût principal ne vient pas encore de notre code métier, mais plutôt du framework, de HTTPX, de Starlette et du banc de test. Donc il ne faut pas optimiser au hasard. Le bon Quick Win est bien le cache, car il réduit directement les lectures répétées.

Fonctions dominantes :

| Zone | Temps cumulé | Interprétation |
|---|---:|---|
| `exercise_api` | 0,768 s | scénario complet |
| `httpx.AsyncClient.get` | 0,686 s | client HTTP du test |
| `httpx.AsyncClient.request` | 0,684 s | orchestration requête |
| `starlette.routing` | 0,444 s | routage framework |
| `asgi.handle_async_request` | 0,253 s | transport ASGI |

Conclusion profiling :

> La règle 80/20 ne révèle pas encore un gros hotspot métier. Donc on évite l'optimisation prématurée et on garde l'optimisation qui a un vrai impact mesuré : le cache.

## 7. Analyse des pertes restantes

Ce que je peux dire :

> Après optimisation, il reste quand même des pertes. Une application n'est jamais à zéro coût. On mesure donc les pertes restantes.

Pertes restantes :

- cache miss global : 1,98 % ;
- P95 restant : 0,331 ms ;
- CO₂ pour 100 lectures : 7,96e-08 kg CO₂eq ;
- équivalent voiture : environ 0,398 mm ;
- perte réseau future possible entre Fly.io et Render PostgreSQL.

Phrase simple :

> La perte restante est faible en local, mais il faudra refaire la mesure en production car la latence réseau peut changer les résultats.

## 8. Quick Win choisi

Ce que je peux dire :

> Le Quick Win prioritaire est le cache de lecture. Il est simple, peu risqué et très efficace pour notre cas d'usage.

Pourquoi c'est le bon Quick Win :

- effort faible ;
- impact élevé ;
- gain mesuré supérieur à 90 % ;
- cohérent avec une application où beaucoup de contenus sont lus plusieurs fois ;
- compatible avec l'éco-conception.

## 9. Conclusion à dire à la fin

Version courte :

> Nous avons respecté la démarche du cours : mesurer, profiler, optimiser et valider. L'optimisation par cache réduit la latence moyenne de 92,30 %, le P95 de 90,47 % et l'impact CO₂ estimé de 92,29 %. Les pertes restantes sont faibles en local, mais devront être mesurées après le déploiement réel.

Version très courte :

> Notre optimisation principale est le cache. Elle réduit le coût d'une lecture répétée d'environ 92 %. C'est notre Quick Win d'éco-conception.

## 10. Questions possibles du professeur

### Pourquoi le cache ?

Parce que les questions et articles sont lus plusieurs fois. Cacher ces lectures évite de recalculer et de réinterroger la base.

### Est-ce que vous avez optimisé au hasard ?

Non. Nous avons mesuré avec `cProfile`, puis comparé lecture froide et lecture chaude.

### Quelle est la perte ?

La perte restante est le cache miss, la latence restante, le CPU consommé par le framework et le CO₂ estimé restant.

### Est-ce que les résultats sont définitifs ?

Non. Les mesures sont locales. Il faudra refaire les mesures en production pour intégrer la latence réseau réelle.

### Quel est le prochain axe d'optimisation ?

Activer Redis externe en production, mesurer la latence Fly.io vers PostgreSQL Render, puis ajouter des index PostgreSQL si la recherche devient coûteuse.

# SanteBien - Analyse après développement

Date : 16 juin 2026  
Projet : application web communautaire de santé, inspirée de Stack Overflow  
Stack : FastAPI, SQLAlchemy async, PostgreSQL, Redis/mémoire, Docker, Fly.io, Render PostgreSQL

## Objectif d'optimisation

Cette analyse mesure le résultat obtenu après développement avec un objectif principal : identifier les optimisations réalisées, mesurer leurs gains et préciser les pertes restantes.

L'optimisation prioritaire de cette itération est la réduction du coût des lectures répétées grâce au cache. Dans SanteBien, les pages les plus consultées sont les questions, les réponses et les articles. Sans optimisation, chaque lecture peut solliciter la base de données. Avec cache, une lecture déjà calculée est servie directement, ce qui réduit la latence, le CPU, les entrées/sorties et donc l'impact CO₂ estimé.

SanteBien n'est pas un modèle d'IA prédictif. Il n'y a donc pas de `loss`, `accuracy`, `precision` ou `recall` au sens machine learning. Ici :

- la précision signifie : conformité fonctionnelle avec le besoin demandé ;
- la perte signifie : coût résiduel en latence, cache miss, CPU, énergie et CO₂.

## Optimisations appliquées

| Optimisation | Objectif | Effet attendu |
|---|---|---|
| Cache sur la liste des questions | Éviter de recalculer les listes consultées souvent | Moins de requêtes base |
| Cache sur le détail d'une question | Accélérer les lectures répétées | Latence et CO₂ réduits |
| Cache sur articles santé | Réduire le coût des contenus pédagogiques souvent lus | Moins d'I/O |
| Invalidation ciblée du cache | Garder les données cohérentes après commentaire/vote/article | Éviter les données obsolètes |
| Validation Pydantic | Rejeter tôt les entrées invalides | Moins de traitement inutile |
| Pagination/limite de résultats | Éviter de charger trop de données | Moins de mémoire et CPU |
| Docker slim | Réduire l'image et faciliter le déploiement | Déploiement plus sobre |
| PostgreSQL externe | Éviter SQLite volatile en prod | Données persistantes |

## Mesure avant/après optimisation cache

Le scénario suivant compare 100 lectures froides, où le cache est invalidé avant chaque requête, avec 100 lectures chaudes, où la réponse est servie depuis le cache.

| Indicateur | Sans bénéfice cache | Avec cache optimisé | Gain |
|---|---:|---:|---:|
| Latence moyenne | 2,7821 ms | 0,2143 ms | -92,30 % |
| Latence P95 | 3,159 ms | 0,301 ms | -90,47 % |
| Latence maximale | 18,893 ms | 0,431 ms | -97,72 % |
| CO₂ estimé pour 100 lectures | 1,40647e-07 kg | 1,08370e-08 kg | -92,29 % |
| Cache hit rate | 0 % | 100 % | +100 points |

Conclusion : l'optimisation cache est le gain principal de cette itération. Elle divise environ par 13 le coût moyen d'une lecture répétée.

## Résultat fonctionnel

| Fonctionnalité | État |
|---|---:|
| Inscription et connexion | OK |
| Publication de questions santé | OK |
| Commentaires/réponses | OK |
| Tags, recherche, tri, votes | OK |
| Demande de profil médecin | OK |
| Approbation admin des médecins | OK |
| Articles publiés par médecins vérifiés | OK |
| Docker/Fly.io | OK |
| PostgreSQL externe Render | OK |

Tests automatisés :

| Indicateur | Résultat |
|---|---:|
| Tests réussis | 6/6 |
| Taux de réussite fonctionnelle testé | 100 % |
| Erreurs bloquantes | 0 |

## Précision fonctionnelle

La précision fonctionnelle est estimée à 100 % sur le périmètre développé et testé.

| Besoin | Implémenté | Précision |
|---|---:|---:|
| Créer un compte | Oui | 100 % |
| Se connecter | Oui | 100 % |
| Poser une question | Oui | 100 % |
| Répondre/commenter | Oui | 100 % |
| Demander un rôle médecin | Oui | 100 % |
| Valider un médecin | Oui | 100 % |
| Publier un article médecin | Oui | 100 % |

Limite : l'application ne garantit pas la précision médicale des contenus. Elle encadre le risque avec le badge médecin vérifié, la validation admin et l'avertissement indiquant que SanteBien ne remplace pas une consultation.

## Mesures après développement

Campagne locale : 100 lectures répétées d'une question avec cache actif.

| Indicateur | Résultat |
|---|---:|
| Requêtes mesurées | 100 |
| Latence minimale | 0,198 ms |
| Latence moyenne | 0,2863 ms |
| Latence P95 | 0,331 ms |
| Latence maximale | 5,161 ms |
| Cache hits questions | 99 |
| Cache misses questions | 2 |
| Hit rate cache questions | 98,02 % |
| CO₂ campagne CodeCarbon | 0,000000079606 kg CO₂eq |
| CO₂ par requête | 0,000000000796 kg CO₂eq |
| Équivalent voiture | environ 0,398 mm |

## Analyse des pertes restantes après optimisation

### Perte cache

| Indicateur | Valeur |
|---|---:|
| Cache hit rate | 98,02 % |
| Cache miss rate | 1,98 % |

La perte cache est faible : seulement 1,98 % des lectures de la campagne globale ne sont pas servies depuis le cache. Dans le scénario optimisé pur, le cache atteint 100 % de hits après préchauffage.

### Perte performance restante

Comparaison avec la précédente mesure de Phase 2 :

| Métrique | Avant | Après | Perte |
|---|---:|---:|---:|
| Latence moyenne | 0,2475 ms | 0,2863 ms | +15,68 % |
| P95 | 0,282 ms | 0,331 ms | +17,38 % |
| CO₂ campagne | 6,72e-08 kg | 7,96e-08 kg | +18,41 % |

Interprétation : cette table compare deux états après développement, pas le scénario avant/après cache. La perte relative existe, mais la valeur absolue reste très faible. L'augmentation vient surtout de la variabilité locale et des couches ajoutées pour préparer la production : configuration PostgreSQL externe, SSL Render, admin initial et tests supplémentaires.

La vraie optimisation mesurée est celle du cache : -92,30 % de latence moyenne entre lecture froide et lecture chaude.

### Perte énergétique

| Indicateur | Valeur |
|---|---:|
| CO₂ total pour 100 lectures | 0,000000079606 kg CO₂eq |
| CO₂ par requête | 0,000000000796 kg CO₂eq |
| Équivalent voiture | 0,398 mm |

La perte énergétique mesurée localement est très faible. En production, la vraie perte dépendra surtout de la latence réseau entre Fly.io et Render PostgreSQL.

## Profiling CPU

Campagne `cProfile` : 1 000 lectures répétées.

| Zone | ncalls | cumtime | Analyse |
|---|---:|---:|---|
| `exercise_api` | 4052 | 0,768 s | scénario complet |
| `httpx.AsyncClient.get` | 5005 | 0,686 s | coût client HTTP du benchmark |
| `httpx.AsyncClient.request` | 5005 | 0,684 s | orchestration requête |
| `httpx.AsyncClient.send` | 5005 | 0,484 s | transport ASGI local |
| `starlette.routing` | 5050 | 0,444 s | routage framework |
| `asgi.handle_async_request` | 5005 | 0,253 s | transport de test |

Le code métier SanteBien n'est pas le hotspot principal. Les coûts dominants viennent du framework, du client HTTPX et du banc de test.

## Règle 80/20

La règle 80/20 ne montre pas encore une fonction métier critique. Les zones les plus coûteuses sont génériques : asyncio, HTTPX, Starlette et ASGI.

Conclusion : il n'est pas pertinent d'optimiser prématurément les endpoints métier. Le meilleur Quick Win reste le cache sur les lectures fréquentes.

## Quick Win prioritaire

Quick Win : maintenir et améliorer le cache des questions/articles.

Justification :

- 98,02 % de cache hit ;
- seulement 1,98 % de perte cache ;
- -92,30 % de latence moyenne sur les lectures chaudes ;
- -90,47 % de P95 ;
- -92,29 % de CO₂ estimé sur le scénario optimisé ;
- P95 de 0,331 ms ;
- empreinte CO₂ très faible sur le scénario mesuré.

Effort : faible.  
Impact : élevé sur les lectures répétées.  
Risque : faible, car l'invalidation existe déjà après création, commentaire, vote ou article.

## Limites

- Mesures locales sans latence réseau réelle.
- Cache mesuré en mémoire, pas Redis externe.
- PostgreSQL Render externe peut ajouter de la latence.
- Render Free expire le 16 juillet 2026.
- L'application ne produit pas de diagnostic médical automatique.

## Prochaines optimisations recommandées

| Priorité | Optimisation | Impact attendu | Effort |
|---|---|---|---|
| 1 | Activer Redis externe en production | Cache partagé entre machines | Moyen |
| 2 | Mesurer la latence Fly.io vers Render PostgreSQL | Identifier la perte réseau réelle | Faible |
| 3 | Ajouter des index PostgreSQL sur tags, dates et auteurs | Accélérer recherche/tri | Moyen |
| 4 | Compresser les assets front | Réduire transfert réseau | Faible |
| 5 | Ajouter pagination stricte côté API | Réduire mémoire et I/O | Faible |
| 6 | Journaliser les endpoints les plus coûteux | Optimisation pilotée par données | Moyen |

Décision : ne pas optimiser prématurément les fonctions métier tant que le profiling montre que les hotspots principaux viennent surtout du framework et du banc de test.

## Conclusion

Après développement, SanteBien est fonctionnel, testable, déployable et déjà optimisé sur son parcours de lecture principal.

La précision fonctionnelle est forte sur le périmètre demandé : 6 tests sur 6 réussissent.

La perte mesurée est faible :

- 1,98 % de cache miss ;
- P95 de 0,331 ms ;
- 7,96e-08 kg CO₂eq pour 100 lectures ;
- environ 0,398 mm en équivalent voiture.

Le gain d'optimisation principal est net :

- -92,30 % de latence moyenne grâce au cache ;
- -90,47 % sur le P95 ;
- -92,29 % de CO₂ estimé sur 100 lectures répétées.

La prochaine analyse devra être faite après déploiement réel, pour mesurer la latence entre Fly.io et Render PostgreSQL et décider si Redis externe ou une base plus proche de l'application est nécessaire.

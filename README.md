# SanteBien

SanteBien est une application communautaire de sante inspiree de Stack Overflow.
Les membres posent des questions et partagent leurs experiences. Les medecins
verifies peuvent repondre avec un badge visible et publier des articles. Les
administrateurs valident les justificatifs medicaux.

## Fonctionnalites

- inscription, connexion, deconnexion et profil ;
- roles membre, medecin verifie et administrateur ;
- questions, recherche, tags, tri, votes et commentaires ;
- articles publies uniquement par les medecins verifies ;
- demande de validation medecin et espace d'approbation admin ;
- PostgreSQL avec SQLAlchemy async ;
- cache Redis avec fallback memoire ;
- mini-modele IA frugal de classification non diagnostique ;
- headers de mesure `X-Process-Time-Ms` et `X-CO2-Kg` ;
- front SPA HTML/CSS/JavaScript servi par FastAPI.

## Lancement Docker recommande

Docker Desktop doit etre demarre.

```bash
docker compose up --build
```

Puis ouvrir `http://localhost:8000`.

## Deploiement sobre generique

L'application est preparee pour un deploiement conteneurise sans dependance a un
fournisseur cloud precis. Le `Dockerfile` expose le port `8000` et lit la
configuration depuis des variables d'environnement.

Variables minimales en production :

```bash
DATABASE_URL="postgresql://user:password@host:5432/santebien?sslmode=require"
REDIS_URL="redis://host:6379/0"
SEED_DEMO_DATA="false"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="mot-de-passe-long-et-secret"
ADMIN_DISPLAY_NAME="Administrateur SanteBien"
```

Sans `REDIS_URL`, l'application fonctionne avec un cache memoire de secours.
Pour une base PostgreSQL externe, ajouter `?sslmode=require` si le service
demande une connexion chiffree.

## CI/CD vert

Le pipeline GitHub Actions applique les pratiques du cours DevOps Vert :

- declenchement limite aux fichiers applicatifs utiles ;
- cache `pip` pour eviter les installations inutiles ;
- compilation, tests automatises et scan securite leger ;
- mesure FP32/INT8 du mini-modele IA ;
- green gates modele sur compression, accuracy, accord, taille, latence et CO2 ;
- mesure API/cache gardee comme contexte d'eco-conception ;
- build Docker et controle de taille d'image.

Commandes locales equivalentes :

```bash
.venv/bin/python -m scripts.measure_phase2
.venv/bin/python -m scripts.compare_cache_optimization
.venv/bin/python -m scripts.measure_ai_model
.venv/bin/python -m scripts.green_gates
```

## Lancement local leger

Sans PostgreSQL ni Redis, l'application utilise SQLite et un cache memoire :

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

## Comptes de demonstration

| Role | Email | Mot de passe |
|---|---|---|
| Membre | `user@santebien.fr` | `User123!` |
| Medecin verifie | `medecin@santebien.fr` | `Doctor123!` |
| Administrateur | `admin@santebien.fr` | `Admin123!` |
| Candidat medecin | `candidat@santebien.fr` | `Doctor123!` |

## Verification

```bash
.venv/bin/pytest -q
.venv/bin/python -m scripts.measure_phase2
.venv/bin/python -m scripts.profile_phase2
.venv/bin/python -m scripts.reset_demo
```

Documentation API : `http://localhost:8000/docs`

Mesures cache : `http://localhost:8000/api/metrics/cache`

Analyse IA non diagnostique : `POST /api/ai/analyze-question`

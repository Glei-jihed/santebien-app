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
- headers de mesure `X-Process-Time-Ms` et `X-CO2-Kg` ;
- front SPA HTML/CSS/JavaScript servi par FastAPI.

## Lancement Docker recommande

Docker Desktop doit etre demarre.

```bash
docker compose up --build
```

Puis ouvrir `http://localhost:8000`.

## Deploiement Fly.io

L'application contient deja un `Dockerfile` et un `fly.toml`. Fly construit
l'image Docker pendant `fly deploy` et expose le port interne `8000`.

```bash
fly auth login
fly launch --no-deploy
fly postgres create
fly postgres attach <nom-du-cluster-postgres>
fly secrets set ADMIN_EMAIL="admin@example.com"
fly secrets set ADMIN_PASSWORD="mot-de-passe-long-et-secret"
fly secrets set ADMIN_DISPLAY_NAME="Administrateur SanteBien"
fly deploy
```

Si le nom `santebien-edgar-jihed` est deja pris, modifier la ligne `app = "..."`
dans `fly.toml`, ou utiliser `fly apps create <nom-unique>`.

Pour Redis en production, configurer un service Redis compatible et ajouter :

```bash
fly secrets set REDIS_URL="redis://..."
```

En production, `SEED_DEMO_DATA=false` evite de publier les comptes de demo.
Le premier administrateur est cree automatiquement avec `ADMIN_EMAIL` et
`ADMIN_PASSWORD` si ces secrets sont presents.

Une base PostgreSQL externe gratuite comme Neon ou Supabase peut aussi etre
utilisee. Copier l'URL Postgres fournie par le service puis la definir comme
secret :

```bash
fly secrets set DATABASE_URL="postgresql://..."
```

Sans `REDIS_URL`, l'application fonctionne avec un cache memoire de secours.

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

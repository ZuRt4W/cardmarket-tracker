# 📈 Cardmarket TCG Price Tracker

Suivi historique des prix des produits Pokémon scellés (Booster Boxes & Elite Trainer Boxes) sur [Cardmarket](https://www.cardmarket.com), avec visualisation sous forme de graphiques interactifs.

> **Projet personnel** — Les données collectées sont strictement agrégées (min/max/moyenne) et aucune offre brute n'est redistribuée. Ce projet est développé dans le respect des CGU de l'API Cardmarket.

---

## 🏗️ Architecture

```
cardmarket-tracker/
├── collector/          # Appels API Cardmarket (OAuth 1.0a)
├── processor/          # Agrégation et transformation des données
├── database/           # Modèles SQLAlchemy + migrations
├── scheduler/          # Planification des collectes (APScheduler)
├── api/                # API REST interne (FastAPI)
├── tests/              # Tests unitaires et d'intégration
└── scripts/            # Utilitaires (init DB, seed...)
```

## ⚙️ Stack technique

| Couche | Technologie |
|--------|-------------|
| Collecte API | `httpx` + `authlib` (OAuth 1.0a) |
| Base de données | PostgreSQL + TimescaleDB |
| ORM | SQLAlchemy 2.0 |
| Planification | APScheduler |
| API interne | FastAPI |
| Visualisation | React + ApexCharts |

## 🚀 Installation

```bash
# 1. Cloner le repo
git clone https://github.com/ZuRt4W/cardmarket-tracker.git
cd cardmarket-tracker

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Renseigner vos clés API Cardmarket dans .env

# 5. Initialiser la base de données
python scripts/init_db.py
```

## 🔑 Configuration `.env`

```env
CM_APP_TOKEN=your_app_token
CM_APP_SECRET=your_app_secret
CM_ACCESS_TOKEN=your_access_token
CM_ACCESS_TOKEN_SECRET=your_access_token_secret

DATABASE_URL=postgresql://user:password@localhost:5432/cardmarket_tracker
```

## 📦 Utilisation

```bash
# Lancer une collecte manuelle
python -m scheduler.manual_run

# Démarrer l'API
uvicorn api.main:app --reload

# Lancer les tests
pytest tests/
```

## 📊 Données collectées

Par extension Pokémon, pour les Booster Boxes et Elite Trainer Boxes :
- Prix minimum, maximum, moyenne — par langue
- Historique quotidien conservé indéfiniment

## 📄 Licence

Usage personnel uniquement. Voir [LICENSE](LICENSE).

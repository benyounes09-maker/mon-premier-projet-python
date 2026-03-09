# OptiGest Pro v3.0
### Application de gestion wholesale de verres optiques — Next Generation

---

## 🚀 Lancement

```bash
cd optigest_v3
pip install customtkinter matplotlib reportlab
python main.py
```

## 🔑 Identifiants

| Identifiant | Mot de passe | Rôle           |
|-------------|--------------|----------------|
| admin       | admin123     | Administrateur |
| manager     | manager123   | Manager        |
| vendeur     | vendeur123   | Vendeur        |

---

## ✨ Ce qui distingue v3.0 de la concurrence

### Interface
- **Dark mode premium** — palette #0f1117 / #6c63ff design pro
- **CustomTkinter** — widgets modernes, arrondis, hover effects natifs
- **Toggle Dark/Light** en live depuis l'écran de login
- **Sidebar animée** avec état actif violet glow

### Dashboard
- **Graphique CA 12 mois** avec matplotlib embedded — barres + courbe overlay
- **Donut chart** répartition des ventes par catégorie
- **6 KPI cards** avec delta mensuel et indicateurs colorés
- **Alertes stock** en temps réel avec compteur
- **Tableau ventes récentes** avec scroll fluide

### Modules
- 📊 **Dashboard** — graphiques matplotlib natifs
- 💳 **Caisse POS** — catalogue en grille de cards tactiles, panier live, popup confirmation
- 📦 **Inventaire** — CRUD complet, recherche instantanée, filtre catégorie
- 👥 **Clients** — fiche complète avec historique
- 🏭 **Fournisseurs** — CRUD
- 📈 **Rapports** — filtre période, export, synthèse KPI
- 👤 **Utilisateurs** — gestion rôles + passwords
- ⚙ **Paramètres** — config société + **journal d'audit** complet

### Architecture
- **Stack** : CustomTkinter + matplotlib + SQLite — 0 dépendance lourde
- **~1 200 lignes** — 3× plus maintenable que la concurrence
- Seed 50 produits + 10 clients + 12 mois d'historique au premier lancement
- Log erreurs automatique dans `optigest_v3.log`

---

## 📁 Structure

```
optigest_v3/
├── main.py              # Login + MainApp
├── config.py            # Thèmes DARK/LIGHT + config
├── database/
│   └── models.py        # Toute la logique DB + seed
├── ui/
│   └── widgets.py       # KPICard + helpers CTk
└── modules/
    ├── dashboard.py     # Dashboard + matplotlib
    ├── pos.py           # Caisse POS
    ├── inventory.py     # Inventaire
    └── other_modules.py # Clients, Fournisseurs, Rapports, Users, Settings
```

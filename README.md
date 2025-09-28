# Traducteur FR → EN (DeepL)

Application Streamlit pour traduire des fichiers PowerPoint (.pptx/.ppt) et Jupyter Notebooks (.ipynb) du français vers l'anglais en utilisant l'API DeepL, tout en préservant la mise en forme.

## 🌟 Fonctionnalités

### PowerPoint
- Traduction des fichiers .pptx et .ppt (conversion automatique via LibreOffice)
- Préservation de la mise en forme (polices, tailles, couleurs, gras, etc.)
- Traduction des tableaux et notes des diapositives
- Optimisation des appels API DeepL par lots

### Jupyter Notebook
- Traduction des cellules markdown
- Traduction des commentaires dans le code Python
- Préservation du code intact (seuls les commentaires sont traduits)
- Optimisation des appels API DeepL par lots

## ⚙️ Prérequis

- Python 3.9+
- Clé API DeepL via la variable d'environnement `DEEPL_API_KEY`
- (Optionnel pour .ppt) LibreOffice installé avec la commande `soffice` disponible dans le PATH

## 🚀 Installation

1. Cloner le repository :
```bash
git clone <repository-url>
cd translate_ppt
```

2. Créer un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installer les dépendances :
```bash
pip install streamlit python-pptx requests nbformat python-dotenv
```

4. Configurer la clé API DeepL :

**Option A : Fichier .env (recommandé)**
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer le fichier .env et ajouter votre clé API
DEEPL_API_KEY=votre_clef_deepl
```

**Option B : Variable d'environnement**
```bash
export DEEPL_API_KEY="votre_clef_deepl"
```

## ▶️ Utilisation

Lancer l'application :
```bash
streamlit run translate_ppt_deepl_app.py
```

L'application s'ouvrira dans votre navigateur avec deux onglets :
- **PowerPoint** : Pour traduire des fichiers .pptx/.ppt
- **Jupyter Notebook** : Pour traduire des fichiers .ipynb

## 📝 Notes

### PowerPoint
- La traduction se fait run par run (éléments de texte formatés) pour préserver la mise en forme
- Les graphiques/SmartArt/objets intégrés ne sont pas modifiables via python-pptx et ne seront pas traduits
- Les fichiers .ppt (ancien format) sont automatiquement convertis en .pptx via LibreOffice si disponible

### Jupyter Notebook
- Seuls les cellules markdown et les commentaires dans le code sont traduits
- Le code Python reste intact
- Les commentaires de ligne (#) sont extraits et traduits individuellement

## 🔧 Configuration

### Paramètres avancés
- **Variante d'anglais** : EN-US ou EN-GB
- **Notes des diapositives** : Option pour inclure/exclure la traduction des notes (PowerPoint uniquement)

### API DeepL
- Les clés Free (contenant "-free") utilisent automatiquement l'endpoint gratuit
- Les clés payantes utilisent l'endpoint premium
- Taille de lot optimisée : 45 textes par requête (limite de sécurité < 50)

## 📦 Dépendances

- `streamlit` : Interface web
- `python-pptx` : Manipulation des fichiers PowerPoint
- `requests` : Appels API DeepL
- `nbformat` : Manipulation des fichiers Jupyter Notebook
- `python-dotenv` : Chargement des variables d'environnement depuis .env

## 🐳 Docker

Un Dockerfile et docker-compose.yml sont fournis pour un déploiement en conteneur.

## 📄 Licence

Ce projet est sous licence MIT.

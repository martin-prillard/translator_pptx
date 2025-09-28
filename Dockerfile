FROM python:3.10-slim

# Installer dépendances système utiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Installer hatch et uv
RUN pip install --no-cache-dir hatch uv

WORKDIR /app

# Copier la spec des dépendances
COPY pyproject.toml ./

# Générer le lockfile et installer les dépendances dans le container
RUN uv lock && uv sync

# Copier ton code (webapp Streamlit)
COPY translate_ppt_deepl_app.py .

EXPOSE 8501

# Lancer Streamlit via hatch
#CMD ["hatch", "run", "streamlit", "run", "translate_ppt_deepl_app.py", "--server.address=0.0.0.0"]
CMD ["uv", "run", "streamlit", "run", "translate_ppt_deepl_app.py", "--server.address=0.0.0.0"]
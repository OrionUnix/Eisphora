#!/bin/bash
echo "Activation de l'environnement virtuel..."

# Activer l'environnement virtuel
source venv/bin/activate

# Aller dans le dossier backend
cd backend

# Lancer le serveur Django
echo "Lancement du serveur..."
python manage.py runserver

@echo off
ECHO Activation de l'environnement virtuel...

:: Activer l'environnement virtuel
call venv\Scripts\activate

:: Aller dans le dossier backend
cd backend

:: Lancer le serveur Django
ECHO Lancement du serveur...
python manage.py runserver

pause
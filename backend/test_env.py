import os
import environ

# Initialiser l'objet environnement
env = environ.Env()

# Déterminer le chemin du fichier .env en remontant d'un niveau
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
environ.Env.read_env(env_path)

# Afficher les variables d'environnement
print("SECRET_KEY:", env("SECRET_KEY"))
print("DB_NAME:", env("DB_NAME"))
print("DB_USER:", env("DB_USER"))
print("DB_PASSWORD:", env("DB_PASSWORD"))
print("DB_HOST:", env("DB_HOST"))
print("DB_PORT:", env("DB_PORT"))

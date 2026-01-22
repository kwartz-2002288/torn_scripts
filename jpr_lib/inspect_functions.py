import inspect
import utilities  # le fichier utilities.py doit être dans le même dossier
# permet d'afficher les fonctions d'une "librairy"
functions = inspect.getmembers(utilities, inspect.isfunction)
for name, func in functions:
    print(name)

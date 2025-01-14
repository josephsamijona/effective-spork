import os
import django
import pycountry
from tqdm import tqdm

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import Language

def populate_languages():
    # Obtenir toutes les langues de pycountry
    languages = []
    for lang in pycountry.languages:
        # Vérifier si la langue a un nom et un code alpha_2
        if hasattr(lang, 'name') and hasattr(lang, 'alpha_2'):
            languages.append({
                'name': lang.name,
                'code': lang.alpha_2
            })

    # Trier les langues par nom
    languages.sort(key=lambda x: x['name'])

    # Créer les entrées dans la base de données avec une barre de progression
    print("Création des langues dans la base de données...")
    created_count = 0
    for lang_data in tqdm(languages):
        try:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={
                    'name': lang_data['name'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
        except Exception as e:
            print(f"Erreur lors de la création de {lang_data['name']}: {str(e)}")

    print(f"\nTerminé! {created_count} nouvelles langues ont été ajoutées à la base de données.")
    print(f"Total des langues dans la base de données: {Language.objects.count()}")

if __name__ == '__main__':
    # Confirmation avant de procéder
    print("Ce script va peupler la table des langues.")
    print("Les langues existantes ne seront pas dupliquées.")
    response = input("Voulez-vous continuer? (o/n): ")
    
    if response.lower() == 'o':
        populate_languages()
    else:
        print("Opération annulée.")
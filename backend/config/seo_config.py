# backend/config/seo_config.py

seo_config = {
    'site_name': 'Eisphora',
    'site_url': 'http://127.0.0.1:8000/',
    'site_logo': '/static/images/logo.png',
    'google_analytics_id': '',  # tu peux lire depuis env si besoin

    # Réseaux sociaux
    'social_links': {
        'github': 'https://github.com/OrionUnix/Eisphora',
        'twitter': 'https://x.com/OrionDeimos',
        'discord': 'https://x.com/OrionDeimos',
        'instagram': 'https://x.com/OrionDeimos',
        'facebook': 'https://x.com/OrionDeimos',
        'dribbble': 'https://x.com/OrionDeimos',
    },

    # Metadata par locale
    'metadata_by_locale': {
        'en-US': {
            'title': 'Eisphora – Open-Source Tax Platform',
            'description': 'Multilingual, secure tax reporting. From crypto to global compliance.',
        },
        'fr-FR': {
            'title': 'Eisphora – Plateforme fiscale open source',
            'description': 'Simplifiez vos impôts avec une application multilingue, sécurisée et transparente.',
        },
    },

    # Valeurs par défaut
    'default_language': 'en-us',
    'default_locale': 'en-US',

    # Hreflang
    'hreflang': {
        'en-US': 'https://eisphora.org/en',
        'fr-FR': 'https://eisphora.org/fr',
    },
}

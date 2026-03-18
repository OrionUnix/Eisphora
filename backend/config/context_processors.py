
from django.conf import settings
from config.seo_config import seo_config

def seo(request):
    # Récupérer la locale active (ex: "fr-fr", "en-us")
    current_language = getattr(request, 'LANGUAGE_CODE', seo_config['default_locale']).lower()
    
    # Normaliser les clés de metadata_by_locale en minuscules pour la recherche
    metadata_lower = {k.lower(): v for k, v in seo_config['metadata_by_locale'].items()}
    
    # Chercher la metadata correspondante (exacte ou par racine de langue)
    current_meta = metadata_lower.get(current_language)
    
    if not current_meta:
        # Essayer de chercher par code court (ex: 'fr' si on a 'fr-fr')
        lang_short = current_language.split('-')[0]
        for key, value in metadata_lower.items():
            if key.startswith(lang_short):
                current_meta = value
                break
    
    # Fallback final sur la locale par défaut
    if not current_meta:
        default_key = seo_config['default_locale'].lower()
        current_meta = metadata_lower.get(default_key, list(seo_config['metadata_by_locale'].values())[0])

    return {
        'seo': {
            'site_name': seo_config['site_name'],
            'site_url': seo_config['site_url'],
            'site_logo': seo_config['site_logo'],
            'site_favicon': seo_config['site_favicon'],
            'google_analytics_id': seo_config.get('google_analytics_id'),
            'social_links': seo_config['social_links'],
            'current_meta': current_meta,
            'default_locale': seo_config['default_locale'],
            'hreflang': seo_config['hreflang'],
        }
    }

def language_flag_mapping(request):
    return {
        "LANGUAGE_FLAG_MAP": {
            "fr-fr": "fr-Fr.png",
            "en-us": "en-US.png",
            "it": "it.png",
            "nl": "nl.png",
            "uk": "uk.png",
        }
    }
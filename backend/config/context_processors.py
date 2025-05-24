
from django.conf import settings
from config.seo_config import seo_config

def seo(request):
    # Récupérer la locale active (ex: "fr-FR") ; on laisse tomber les risques d’incohérence
    current_locale = getattr(request, 'LANGUAGE_CODE', seo_config['default_locale'])
    # Chercher la metadata correspondante, ou fallback
    current_meta = seo_config['metadata_by_locale'].get(
        current_locale,
        seo_config['metadata_by_locale'][seo_config['default_locale']]
        
    )
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

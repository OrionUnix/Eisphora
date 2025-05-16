# backend/config/context_processors.py
from .seo_config import seo_config

def seo(request):
    """
    Injecte la configuration SEO dans tous les templates.
    """
    # On peut, ici, adapter la locale en fonction de request.LANGUAGE_CODE
    locale = getattr(request, 'LANGUAGE_CODE', seo_config['default_language'])
    meta = seo_config['metadata_by_locale'].get(locale, {})
    return {
        'SEO_SITE_NAME': seo_config['site_name'],
        'SEO_SITE_URL': seo_config['site_url'],
        'SEO_SITE_LOGO': seo_config['site_logo'],
        'SEO_GA_ID': seo_config['google_analytics_id'],
        'SEO_TITLE': meta.get('title', seo_config['site_name']),
        'SEO_DESCRIPTION': meta.get('description', ''),
        'SEO_HREFLANG': seo_config['hreflang'],
        'SEO_SOCIAL_LINKS': seo_config['social_links'],
    }

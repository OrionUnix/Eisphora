# backend/config/seo_config.py
from django.utils.translation import gettext_lazy as _

seo_config = {
    'site_name': 'Eisphora',
    'site_url': 'http://127.0.0.1:8000/',
    'site_logo': '*/static/images/logo/logo.svg',
    'site_favicon': '/static/images/logo/favicon.png',
    'google_analytics_id': '', 

    # Réseaux sociaux
    'social_links': {
        'github': 'https://github.com/OrionUnix/Eisphora',
        'twitter': 'https://x.com/OrionDeimos',
        'discord': 'https://x.com/OrionDeimos',
        'instagram': 'https://x.com/OrionDeimos',
        'facebook': 'https://x.com/OrionDeimos',
        'dribbble': 'https://x.com/OrionDeimos',
    },

    #Boost SEO IA
    'structured_data': {
    'en-US': {
        'organization': {
            '@type': 'Organization',
            'name': 'Eisphora',
            'url': 'http://127.0.0.1:8000/',
            'sameAs': [
                'https://github.com/OrionUnix/Eisphora',
                'https://x.com/OrionDeimos',
            ]
        }
    }
},

    # Metadata par locale
'metadata_by_locale': {
        'en-US': {
            'title': _('Eisphora - Open-Source Tax Platform'),
            'description': _('File your crypto taxes in seconds. Eisphora is a secure, open-source and multilingual app built for global tax compliance'),
            '4_words':_('Easy. Secure. Open-source. Global.'),
            '3_words':_('Clarity. Simplicity. Peace of mind.'),
            'og':_('No stress, no lock-in. An open-source app to simplify your crypto taxes.'),
            'make_love':_('Make with love ❤, Say goodbye to tax headaches. Eisphora is free, open, and designed to make crypto tax compliance finally make sense. '),  
        },

        'fr-FR': {
            'title': _('Eisphora - Plateforme fiscale open source'),
            'description': _('Calculez et déclarez vos impôts crypto en quelques clics. Eisphora est open source, multilingue et pensée pour la conformité fiscale.'),
            '4_words':_(' Facile. Sécurisé. Open-source. Mondial.'),
            '3_words':_('Transparence. Simplicité. Sérénité.'),
            'og':_('Open source. Multilingue. Pour simplifier vos impôts crypto.'),
            'make_love':_('Créée avec amour ❤, construite pour vous simplifier la vie : Eisphora vous aide à reprendre le contrôle de vos obligations fiscales '),  
        },

         'it-IT': {
            'title': _('Eisphora - Piattaforma fiscale open source'),
            'description': _(
                'Dichiara le tue tasse crypto in pochi secondi. Eisphora è gratuita, sicura, open source e progettata per la conformità globale.'
            ),
            '4_words': _('Semplice. Sicura. Open-source. Globale.'),
            '3_words': _('Chiarezza. Semplicità. Tranquillità.'),
            'og': _(
                'Stop allo stress fiscale. Eisphora semplifica la dichiarazione delle tue criptovalute.'
            ),
            'make_love': _(
                'Creata con amore ❤, pensata per aiutarti a gestire le tasse crypto senza stress.'
            ),
        },

        'es-ES': {
            'title': _('Eisphora - Plataforma fiscal open source'),
            'description': _(
                'Declara tus impuestos cripto en segundos. Eisphora es segura, gratuita, multilingüe y diseñada para una fiscalidad clara.'
            ),
            '4_words': _('Simple. Segura. Open-source. Global.'),
            '3_words': _('Claridad. Simplicidad. Tranquilidad.'),
            'og': _(
                'Sin estrés fiscal. Eisphora te ayuda a declarar tus criptomonedas sin complicaciones.'
            ),
            'make_love': _(
                'Hecha con amor ❤, construida para simplificar tus impuestos cripto de forma libre y transparente.'
            ),
        },

        'ja-JP': {
            'title': _('Eisphora - オープンソースの税務アプリ'),
            'description': _(
                '暗号資産の税務申告を数秒で完了。Eisphoraは安全で、多言語対応、オープンソースのグローバルな税務プラットフォームです。'
            ),
            '4_words': _('シンプル、安全、オープン、グローバル'),
            '3_words': _('明確、簡単、安心'),
            'og': _(
                '税務のストレスを解消。Eisphoraで暗号資産の申告を簡単に。'
            ),
            'make_love': _(
                '愛を込めて開発 ❤、税務申告を簡単にする自由で透明なツールです。'
            ),
        },

        'ko-KR': {
            'title': _('Eisphora - 오픈소스 세금 플랫폼'),
            'description': _(
                '암호화폐 세금 신고를 몇 초 만에. Eisphora는 안전하고 다국어 지원, 오픈소스 기반의 글로벌 세금 플랫폼입니다.'
            ),
            '4_words': _('간단. 안전. 오픈소스. 글로벌.'),
            '3_words': _('명확성. 단순함. 평온함.'),
            'og': _(
                '세금 스트레스 없이. Eisphora로 암호화폐 세금을 쉽게 신고하세요.'
            ),
            'make_love': _(
                '사랑으로 만든 ❤, 암호화폐 세금신고를 단순하고 투명하게 도와주는 무료 툴입니다.'
            ),
              },
    },

    # Valeurs par défaut
    'default_language': 'en-us',
    'default_locale': 'en-US',

    # Hreflang
    'hreflang': {
        'en-US': 'http://127.0.0.1:8000/en',
        'fr-FR': 'http://127.0.0.1:8000/fr',
    },

}

# json_ld 
def get_json_ld(self, request):
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": self.site_name,
        "url": self.site_url,
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "All",
        "offers": {
            "@type": "Offer",
            "price": "0.00",
            "priceCurrency": "USD"
        },
        "softwareVersion": "1.0.0",
        "inLanguage": list(self.meta.keys()),  # ['en', 'fr', 'it', ...]
        "author": {
            "@type": "Organization",
            "name": "Eisphora",
            "url": self.site_url
        },
        "description": self.current_meta["description"],
        "image": self.site_logo
    },

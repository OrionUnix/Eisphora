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

# Boost SEO IA
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

# Metadata par locale (Sécurisées juridiquement)
    'metadata_by_locale': {
        'en-US': {
            'title': _('Eisphora - Crypto Tax Estimation Aid'),
            'description': _('Eisphora is a free, open-source tool designed to help you estimate your crypto taxes. It provides a baseline calculation, not official financial advice.'),
            '4_words': _('Easy. Secure. Open-source. Independent.'),
            '3_words': _('Simulation. Transparency. Aid.'),
            'og': _('Estimate your crypto taxes with this open-source community tool.'),
            'make_love': _('Made with love ❤. Eisphora is a free, open-source tool designed to help you estimate your crypto taxes. It provides a baseline calculation, not official financial advice. Always verify with a tax professional.'),  
        },

        'fr-FR': {
            'title': _('Eisphora - Aide à l\'estimation fiscale crypto'),
            'description': _('Eisphora est un outil gratuit et open source conçu pour vous aider à estimer votre fiscalité crypto. Il fournit une base de calcul indicative et non un conseil financier officiel.'),
            '4_words': _('Facile. Sécurisé. Open-source. Indépendant.'),
            '3_words': _('Simulation. Transparence. Aide.'),
            'og': _('Estimez votre fiscalité crypto avec cet outil open source communautaire.'),
            'make_love': _('Fait avec amour ❤. Eisphora est un outil gratuit et open source conçu pour vous aider à estimer votre fiscalité crypto. Il fournit une base de calcul indicative et non un conseil financier officiel. Vérifiez toujours avec un professionnel.'),  
        },

        'it-IT': {
            'title': _('Eisphora - Aiuto per la stima fiscale crypto'),
            'description': _('Eisphora è uno strumento gratuito e open source progettato per aiutarti a stimare le tue tasse crypto. Fornisce un calcolo di base, non una consulenza finanziaria ufficiale.'),
            '4_words': _('Facile. Sicuro. Open-source. Indipendente.'),
            '3_words': _('Simulazione. Trasparenza. Aiuto.'),
            'og': _('Stima le tue tasse crypto con questo strumento open source comunitario.'),
            'make_love': _('Fatto con amore ❤. Eisphora ti aiuta a stimare le tasse crypto. Fornisce un calcolo di base, non una consulenza ufficiale. Verifica sempre con un professionista.'),
        },

        'es-ES': {
            'title': _('Eisphora - Ayuda para la estimación fiscal cripto'),
            'description': _('Eisphora es una herramienta gratuita y de código abierto diseñada para ayudarte a estimar tus impuestos cripto. Proporciona un cálculo base, no asesoramiento financiero oficial.'),
            '4_words': _('Fácil. Seguro. Open-source. Independiente.'),
            '3_words': _('Simulación. Transparencia. Ayuda.'),
            'og': _('Estima tus impuestos cripto con esta herramienta de código abierto comunitaria.'),
            'make_love': _('Hecho con amor ❤. Eisphora te ayuda a estimar tus impuestos cripto. Proporciona un cálculo base, no asesoramiento oficial. Verifica siempre con un profesional.'),
        },

        'ja-JP': {
            'title': _('Eisphora - 暗号資産の税務見積もり支援'),
            'description': _('Eisphoraは、暗号資産の税金を見積もるための無料のオープンソースツールです。基本的な計算を提供するものであり、公式な財務アドバイスではありません。'),
            '4_words': _('簡単・安全・オープン・独立'),
            '3_words': _('シミュレーション・透明性・支援'),
            'og': _('このコミュニティ主導のオープンソースツールで暗号資産の税金を見積もりましょう。'),
            'make_love': _('愛を込めて開発 ❤。Eisphoraは税金の見積もりを支援する無料ツールです。公式なアドバイスではないため、必ず税務の専門家にご確認ください。'),
        },

        'ko-KR': {
            'title': _('Eisphora - 암호화폐 세금 예상 도구'),
            'description': _('Eisphora는 암호화폐 세금을 예상하는 데 도움을 주기 위해 설계된 무료 오픈소스 도구입니다. 기본적인 계산을 제공하며 공식적인 재무 조언이 아닙니다.'),
            '4_words': _('쉽고. 안전한. 오픈소스. 독립적인.'),
            '3_words': _('시뮬레이션. 투명성. 지원.'),
            'og': _('커뮤니티가 만든 오픈소스 도구로 암호화폐 세금을 예상해보세요.'),
            'make_love': _('사랑으로 만듦 ❤. Eisphora는 세금 예상을 돕는 무료 도구입니다. 공식적인 조언이 아니므로 반드시 세무 전문가와 확인하세요.'),
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
 "inLanguage": locales,  # ['en', 'fr', 'it', 'es', 'ja', 'ko']
        "author": {
            "@type": "Organization",
            "name": "Eisphora",
            "url": self.site_url
        },
        "description": self.current_meta["description"],
        "image": self.site_logo
    },

// src/app/(public)/seo.config.ts

export const seoConfig = {
  siteName: 'Eisphora',
  siteUrl: 'https://eisphora.org', // URL
  siteLogo: '/next.svg', // Logo 
  googleAnalyticsId: process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID || '',

  // Social Network
  socialLinks: {
    GitHubUrl: 'https://github.com/OrionUnix/Eisphora',
    TwitterUrl: 'https://x.com/OrionDeimos',
    DiscordUrl: 'https://x.com/OrionDeimos',
    InstagramUrl: 'https://x.com/OrionDeimos',
    FacebookUrl: 'https://x.com/OrionDeimos',
    DribbleUrl: 'https://x.com/OrionDeimos',
  },


  // Metadata by Location
  metadataByLocale: {
    'en-US': {
      title: 'Eisphora – Open-Source Tax Platform',
      description: 'Multilingual, secure tax reporting. From crypto to global compliance.',
    },
    'fr-FR': {
      title: 'Eisphora – Plateforme fiscale open source',
      description: 'Simplifiez vos impôts avec une application multilingue, sécurisée et transparente.',
    },
  },

  // default config 
  language: 'en-us',
  locale: 'en-US',

  // Support multilingue
  hreflang: {
    'en-US': 'https://eisphora.org/en',
    'fr-FR': 'https://eisphora.org/fr',
  },
};

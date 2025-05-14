import Head from 'next/head';
import { useRouter } from 'next/router';
import { seoConfig } from '../../seo.config';

interface SEOProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
}

export default function SEO({
  title,
  description,
  image,
  url,
}: SEOProps) {
  const { locale, asPath } = useRouter();

  const meta =
    seoConfig.metadataByLocale?.[locale] || seoConfig.metadata;

  const metaTitle = title || meta.title;
  const metaDescription = description || meta.description;
  const metaUrl = url || `${seoConfig.siteUrl}${asPath}`;
  const metaImage = image || `${seoConfig.siteUrl}/eisphora-preview.png`; // à personnaliser

  return (
    <Head>
      <title>{metaTitle}</title>
      <meta name="description" content={metaDescription} />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta charSet="utf-8" />
      <meta name="robots" content="index, follow" />
      <link rel="canonical" href={metaUrl} />

      {/* Open Graph */}
      <meta property="og:title" content={metaTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:url" content={metaUrl} />
      <meta property="og:type" content="website" />
      <meta property="og:image" content={metaImage} />

      {/* Twitter Cards */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={metaTitle} />
      <meta name="twitter:description" content={metaDescription} />
      <meta name="twitter:image" content={metaImage} />
      <meta name="twitter:site" content="@OrionDeimos" /> {/* si tu veux */}

      {/* Favicon (à personnaliser) */}
      <link rel="icon" href="/favicon.ico" />
    </Head>
  );
}

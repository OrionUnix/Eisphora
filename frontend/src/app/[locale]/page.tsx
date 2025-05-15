import Hero from '@/app/[locale]/components/Hero';
import Parallax from '@/app/[locale]/components/Parallax';
import FAQ from '@/app/[locale]/components/FAQ';
import { seoConfig } from '@/app/[locale]/seo.config';

const HomePage: React.FC = () => {
  return (
    <>

      <Parallax />
      <Hero />
      <FAQ />

    </>
  );
};

export default HomePage;

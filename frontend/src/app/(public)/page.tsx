import Hero from './components/Hero'; // Corrected import path
import Parallax from './components/Parallax';
import FAQ from './components/FAQ';

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

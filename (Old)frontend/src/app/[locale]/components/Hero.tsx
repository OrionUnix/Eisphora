'use client';
import React from 'react';
import Image from 'next/image';
import { seoConfig } from "@seoConfig";


const Hero: React.FC = () => {
  return (
    <section
      id="hero"
       className="relative w-full h-screen overflow-hidden flex items-center justify-center"
  style={{ background: 'linear-gradient(to bottom, #282A57, #64748B)' }}
    >
      {/* Background stars */}
      <Image
        src="next.svg"
        alt="Stars background"
        fill
        className="object-cover z-0"
        priority
      />

      {/* Content */}
      <div className="relative z-10 text-white text-center px-4">
        <h1 className="text-4xl md:text-6xl font-bold mb-4"> {seoConfig.siteName} </h1>
        <p className="text-lg md:text-xl max-w-xl mx-auto"> </p>
      </div>
    </section>
  );
};

export default Hero;

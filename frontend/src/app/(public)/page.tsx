"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import "../styles/landing.css";

export default function LandingPage() {
  const parallaxRef = useRef<HTMLDivElement>(null);
  const [showTitle, setShowTitle] = useState(false);

  // Parallax
  useEffect(() => {
    const handleScroll = () => {
      if (!parallaxRef.current) return;
      const scrollY = window.scrollY;
      parallaxRef.current
        .querySelectorAll<HTMLElement>("[data-speed]")
        .forEach((el) => {
          const speed = parseFloat(el.dataset.speed!);
          el.style.transform = `translateY(${scrollY * speed}px)`;
        });

      // Déclenche l’apparition du titre après 200px
      setShowTitle(scrollY > 200);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="relative h-screen overflow-hidden">
      {/* Dégradé plein écran */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-900 via-purple-700 to-pink-600"></div>

      {/* Calques SVG */}
      <div ref={parallaxRef} className="relative h-full">
        {[
          { src: "/landing/stars.svg", speed: 0.4, className: "top-0 w-full" },
          { src: "/landing/clouds-left.svg", speed: 0.15, className: "left-0 w-1/4 top-1/4" },
          { src: "/landing/clouds-right.svg", speed: 0.12, className: "right-0 w-1/4 top-1/3" },
          { src: "/landing/sun.svg", speed: 0.05, className: "w-2/5 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" },
          { src: "/landing/mountain-1.svg", speed: 0.3, className: "bottom-0 w-full" },
          { src: "/landing/mountain-2.svg", speed: 0.2, className: "bottom-0 w-full" },
          { src: "/landing/mountain-3.svg", speed: 0.1, className: "bottom-0 w-full" },
        ].map(({ src, speed, className }, i) => (
          <img
            key={i}
            data-speed={speed}
            src={src}
            alt=""
            className={`absolute ${className}`}
          />
        ))}
      </div>

      {/* Titre de l’appli qui fade-in */}
      <h1
        className={`
          fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2
          text-6xl font-extrabold text-white transition-opacity duration-700
          ${showTitle ? "opacity-100" : "opacity-0"}
        `}
      >
        NomDeVotreAppli
      </h1>

      {/* Contenu sous le parallax */}
      <div className="relative mt-screen h-screen bg-white text-gray-800 flex flex-col items-center justify-center">
        <h2 className="text-4xl mb-4">Bienvenue chez nous !</h2>
        <p className="max-w-xl text-center mb-8">
          Faites défiler pour découvrir plus de merveilles.
        </p>
        <div className="flex gap-4">
          <Link href="/admin/login" className="btn-primary">Commencer</Link>
          <Link href="https://nextjs.org/docs" className="btn-secondary">
            Lire la Doc
          </Link>
        </div>
      </div>
    </div>
  );
}

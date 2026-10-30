import React from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, FileText } from "lucide-react";
import heroImage from "../assets/images/hero-cv.png";

const HeroSection = () => {
  return (
    <section className="hero-section">
      {/* Cercles décoratifs */}
      <div className="hero-decor">
        <div className="decor-circle decor-circle-left"></div>
        <div className="decor-circle decor-circle-right"></div>
      </div>

      <div className="hero-container">
        <div className="hero-grid">
          {/* Colonne gauche */}
          <div className="text-content">

            <h1 className="hero-title">
              Transformez vos CV en{" "}
              <span className="gradient-text">documents standardisés</span>
            </h1>

            <p className="hero-subtitle">
              Extrayez les informations de CV PDF texte ou DOCX et
              générez des documents standardisés en JSON, Word et PDF.
            </p>

            <div className="hero-buttons">
              <NavLink to="/start" className="btn-primary group">
                Commencer maintenant
                <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </NavLink>

              <NavLink to="/example" className="btn-secondary">
                <FileText className="w-5 h-5" />
                Voir un exemple
              </NavLink>
            </div>

            <div className="hero-stats">
              <div><div className="stat-value orange">PDF / DOCX</div><div className="stat-label">Documents source</div></div>
              <div><div className="stat-value red">spaCy</div><div className="stat-label">NER et règles</div></div>
              <div><div className="stat-value light-orange">JSON</div><div className="stat-label">Données structurées</div></div>
            </div>
          </div>

          {/* Image droite */}
          <div className="hero-image-container">
            <div className="hero-image-wrapper">
              <img src={heroImage} alt="Illustration de documents CV" />
              <div className="image-overlay"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;

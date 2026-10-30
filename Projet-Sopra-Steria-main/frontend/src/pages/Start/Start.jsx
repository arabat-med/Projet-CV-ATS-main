import React, { useState } from 'react';
import Navbar from '../../components/Navbar';
import { apiUrl, validateUpload } from '../../utils/api';
import {
  Upload,
  FileText,
  ArrowRight,
  Download,
  BarChart3,
  FileDown,
  Eye
} from 'lucide-react';
import './Start.css';

// Présence des rubriques uniquement : aucune mesure de précision NLP.
const computeCompleteness = (result) => {
  if (!result) return 0;
  const fields = [result.contact?.nom, result.contact?.email,
    result.formations?.length, result.experiences?.length,
    result.competences?.length, result.langues?.length];
  return Math.round(fields.filter(Boolean).length / fields.length * 100);
};

const downloadJson = (result) => {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: 'application/json'
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'cv_analyse.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const Start = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [modifiedDocx, setModifiedDocx] = useState(null);

// --- Conversion DOCX modifié en PDF ---
  const convertDocxToPdf = async () => {
    if (!modifiedDocx) {
      alert("Veuillez sélectionner un fichier .docx modifié.");
      return;
    }
  
    const formData = new FormData();
    formData.append("file", modifiedDocx);
  
    try {
      const response = await fetch(apiUrl("/api/cv/convert"), {
        method: "POST",
        body: formData,
      });
  
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Erreur lors de la conversion");
      }
  
      // Récupérer le PDF retourné
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
  
      const a = document.createElement("a");
      a.href = url;
      a.download = "CV_Final.pdf";
      a.click();
  
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("Erreur : " + e.message);
    }
  };
  

  // --- Gestion du drag & drop ---
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect({ target: { files: [file] } });
  };

  // --- Sélection du fichier ---
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    const validationError = validateUpload(file, ['.docx', '.pdf']);
    if (!validationError) {
      setSelectedFile(file);
      setError(null);
      setResult(null);
    } else {
      setError(validationError);
    }
  };

  // --- Soumission vers le backend ---
  const handleSubmit = async () => {
    if (!selectedFile) return alert('Veuillez sélectionner un fichier');

    const formData = new FormData();
    formData.append('file', selectedFile);

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(apiUrl('/api/cv/analyze'), {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Erreur lors de l’analyse');

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const extractionScore = computeCompleteness(result);

  return (
    <div className="start-page">
      <Navbar />
      <main className="start-section">
        <div className="start-container text-center max-w-5xl mx-auto">
          <h1 className="hero-title">
            Analysez votre <span className="gradient-text">CV</span>
          </h1>
          <p className="hero-subtitle">
            Téléversez votre CV (.docx ou .pdf) pour une extraction automatique des informations clés.
          </p>

          {/* Zone de téléchargement */}
          <div className="mt-10 relative">
            <div
              className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".docx,.pdf"
                onChange={handleFileSelect}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="upload-content">
                <Upload className="upload-icon" />
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="file-selected">
                      <FileText className="file-selected-icon" />
                      <span className="file-selected-name">{selectedFile.name}</span>
                    </div>
                    <p className="file-ready">Fichier prêt à être analysé</p>
                  </div>
                ) : (
                  <>
                    <h3 className="upload-title">Glissez-déposez votre CV ici</h3>
                    <p className="upload-description">ou cliquez pour sélectionner un fichier</p>
                    <p className="upload-format">Formats acceptés : .docx, .pdf texte · 10 Mio maximum</p>
                  </>
                )}
              </div>
            </div>

            {/* Bouton de traitement */}
            {selectedFile && (
              <div className="submit-section">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="submit-button"
                >
                  {loading ? 'Analyse en cours...' : 'Analyser le CV'}
                  <ArrowRight />
                </button>
              </div>
            )}
          </div>

          {/* Gestion des erreurs */}
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          <p className="mt-4 text-sm text-gray-500">
            Traitement sur le serveur configuré. Sources supprimées après traitement ; résultats temporaires
            (expiration configurable, 1 h par défaut). Vérifiez les informations extraites avant utilisation.
          </p>

          {/* Résultat affiché */}
          {result && (
            <div className="result-section text-left mt-10">

              {/* Barre d’outils / résumé */}
              <div className="result-toolbar">

                {/* Score extraction */}
                <div className="score-block">
                  <span className="score-label">Complétude des rubriques</span>
                  <div className="score-value">
                    <BarChart3 size={18} />
                    <span>{extractionScore}%</span>
                    </div>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: `${extractionScore}%` }}
                      />
                  </div>
                  
                  <p className="text-sm">Présence des rubriques détectées, sans mesure de précision ni évaluation du candidat.</p>
                </div>
                <div className="xp-block">
                  <span className="xp-label">Expériences détectées</span>
                  <span className="xp-pill">{result.experiences?.length || 0}</span>
                </div>

                <div className="export-buttons">
                  <button
                    className="export-btn"
                    onClick={() => downloadJson(result)}
                    >
                    <Download size={16} />
                    JSON
                  </button>
                  <button
                    className="export-btn"
                    onClick={() => {
                      if (!result?.pdf_filename) {
                        alert("Aucun PDF généré par le backend.");
                        return;
                      }
                      window.open(apiUrl(`/api/cv/pdf/${encodeURIComponent(result.pdf_filename)}`), "_blank", "noopener,noreferrer");
                    }}
                  >
                    <FileDown size={16} />
                    PDF
                  </button>

                  <button
                    className="export-btn"
                    onClick={() => {
                      if (!result?.json_filename) {
                        alert("Aucun JSON trouvé pour générer le Word.");
                        return;
                      }

                      const baseName = result.json_filename.replace(".json", "");

                      window.open(
                        apiUrl(`/api/cv/docx/${encodeURIComponent(baseName)}`),
                        "_blank", "noopener,noreferrer"
                      );
                    }}
                  >
                    <FileText size={16} />
                    DOCX
                  </button>
                  {/* Sélection du CV Word modifié */}
                  <input
                    type="file"
                    accept=".docx"
                    style={{ display: "none" }}
                    id="upload-modified-docx"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      const validationError = validateUpload(file, ['.docx']);
                      setModifiedDocx(validationError ? null : file);
                      setError(validationError);
                    }}
                  />

                  <label htmlFor="upload-modified-docx" className="export-btn">
                    <Upload size={16} />
                    Importer DOCX modifié
                  </label>

                  {/* Convertir en PDF */}
                  <button
                    className="export-btn"
                    onClick={convertDocxToPdf}
                    disabled={!modifiedDocx}
                  >
                    <FileDown size={16} />
                    Convertir en PDF
                  </button>

                                  </div>
              </div>

              {/* Grille principale */}
              <div className="result-wrapper">

                {/* CONTACT */}
                <div className="result-card">
                  <h3 className="result-title">📞 Contact</h3>
                  <ul className="result-list text-gray-700">
                    {result.contact.nom && <li><strong>Nom :</strong> {result.contact.nom}</li>}
                    {result.contact.email && <li><strong>Email :</strong> {result.contact.email}</li>}
                    {result.contact.telephone && <li><strong>Téléphone :</strong> {result.contact.telephone}</li>}
                    {result.contact.adresse && <li><strong>Adresse :</strong> {result.contact.adresse}</li>}
                  </ul>
                </div>

                {/* FORMATIONS */}
                {result.formations?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🎓 Formations</h3>
                    <ul className="result-list text-gray-700">
                      {result.formations.map((f, i) => (
                        <li key={i}><strong>{f.etablissement}</strong> — {f.dates}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* EXPERIENCES */}
                {result.experiences?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">💼 Expériences</h3>
                    <ul className="result-list text-gray-700">
                      {result.experiences.map((e, i) => (
                        <li key={i}>
                          <strong>{e.entreprise}</strong> — {e.poste || '—'} ({e.dates})
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* PROJETS */}
                {result.projets?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🚀 Projets</h3>
                    <ul className="result-list text-gray-700">
                      {result.projets.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                )}
                
                {/* COMPETENCES (tags + radar) */}
                {result.competences?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🧠 Compétences</h3>
                    <div className="skills-tags">
                      {result.competences.map((c, i) => (
                        <span key={i} className="skill-tag">{c}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* LANGUES */}
                {result.langues?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🌍 Langues</h3>
                    <ul className="result-list text-gray-700">
                      {result.langues.map((l, i) => <li key={i}>{l}</li>)}
                    </ul>
                  </div>
                )}

                {/* CERTIFICATIONS */}
                {result.certifications?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🏅 Certifications</h3>
                    <ul className="result-list text-gray-700">
                      {result.certifications.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                )}

                {/* LOISIRS */}
                {result.loisirs?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🎯 Loisirs</h3>
                    <ul className="result-list text-gray-700">
                      {result.loisirs.map((l, i) => <li key={i}>{l}</li>)}
                    </ul>
                  </div>
                )}

                {/* DISPONIBILITE */}
                {result.disponibilite && (
                  <div className="result-card">
                    <h3 className="result-title">📅 Disponibilité</h3>
                    <p className="text-gray-700">{result.disponibilite}</p>
                  </div>
                )}

                {/* DATES BRUTES */}
                {result.dates?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🗂 Dates détectées</h3>
                    <ul className="result-list text-gray-700">
                      {result.dates.map((d, i) => <li key={i}>{d}</li>)}
                    </ul>
                  </div>
                )}

                {/* CV RECONSTITUÉ */}
                <div className="result-card cv-preview-card">
                  <h3 className="result-title">
                    <Eye size={18} /> CV reconstitué (vue synthèse)
                  </h3>
                  <div className="cv-preview-body">
                    <h4>{result.contact.nom}</h4>
                    <p className="cv-preview-contact">
                      {result.contact.email} ··· {result.contact.telephone} ··· {result.contact.adresse}
                    </p>

                    {result.formations?.length > 0 && (
                      <>
                        <h5>Formations</h5>
                        <ul>
                          {result.formations.map((f, i) => (
                            <li key={i}>
                              <strong>{f.etablissement}</strong> — {f.dates}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}

                    {result.experiences?.length > 0 && (
                      <>
                        <h5>Expériences</h5>
                        <ul>
                          {result.experiences.map((e, i) => (
                            <li key={i}>
                              <strong>{e.entreprise}</strong> — {e.poste || '—'} ({e.dates})
                            </li>
                          ))}
                        </ul>
                      </>
                    )}

                    {result.projets?.length > 0 && (
                      <>
                        <h5>Projets</h5>
                        <ul>
                          {result.projets.map((p, i) => <li key={i}>{p}</li>)}
                        </ul>
                      </>
                    )}

                    {result.competences?.length > 0 && (
                      <>
                        <h5>Compétences clés</h5>
                        <p>{result.competences.join(' · ')}</p>
                      </>
                    )}

                    {result.langues?.length > 0 && (
                      <>
                        <h5>Langues</h5>
                        <p>{result.langues.join(' · ')}</p>
                      </>
                    )}

                    {result.disponibilite && (
                      <>
                        <h5>Disponibilité</h5>
                        <p>{result.disponibilite}</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Étapes visuelles */}
          <div className="process-steps mt-16">
            <div className="process-step">
              <div className="step-icon"><Upload /></div>
              <h3 className="step-title">1. Téléversez</h3>
              <p className="step-description">Choisissez votre CV .docx ou .pdf</p>
            </div>

            <div className="process-step">
              <div className="step-icon"><FileText /></div>
              <h3 className="step-title">2. Analyse</h3>
              <p className="step-description">Extraction automatique des données</p>
            </div>

            <div className="process-step">
              <div className="step-icon"><ArrowRight /></div>
              <h3 className="step-title">3. Résultat</h3>
              <p className="step-description">Dashboard d’analyse structuré</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Start;

import os
import subprocess
import time
from pathlib import Path

def convert_docx_to_pdf(input_docx, output_pdf):
    """
    Convertir un DOCX en PDF using plusieurs méthodes:
    1. LibreOffice (meilleure qualité)
    2. pandoc (conversion markup)
    3. python-pptx pour fallback
    """
    input_path = Path(input_docx)
    output_path = Path(output_pdf)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Le fichier DOCX n'existe pas: {input_docx}")
    
    # Créer le répertoire de sortie s'il n'existe pas
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Essayer avec pandoc (léger et efficace)
    try:
        result = subprocess.run(
            ["pandoc", str(input_path), "-o", str(output_path)],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0 and output_path.exists():
            print(f"✓ PDF créé avec pandoc")
            return str(output_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"⚠️ Pandoc failed: {e}")
    
    # 2. Essayer avec LibreOffice
    try:
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        
        libreoffice_path = None
        for path in possible_paths:
            if os.path.exists(path):
                libreoffice_path = path
                break
        
        if libreoffice_path:
            cmd = [
                libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_path.parent),
                str(input_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and output_path.exists():
                print(f"✓ PDF créé avec LibreOffice")
                return str(output_path)
    except Exception as e:
        print(f"⚠️ LibreOffice failed: {e}")
    
    # 3. Fallback: Créer un PDF simple à partir du DOCX
    try:
        from docx import Document
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        doc_source = Document(str(input_path))
        
        # Créer le PDF avec reportlab
        pdf_doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
        )
        
        styles = getSampleStyleSheet()
        
        # Style personnalisé pour le texte normal
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=6,
        )
        
        story = []
        
        # Extraire le texte des paragraphes du DOCX
        for para in doc_source.paragraphs:
            if para.text.strip():
                # Gérer les listes (puces)
                if para.text.strip().startswith('•'):
                    para_style = ParagraphStyle(
                        'BulletStyle',
                        parent=styles['Normal'],
                        fontSize=11,
                        leftIndent=20,
                        spaceAfter=6,
                    )
                else:
                    para_style = normal_style
                
                # Ajouter le paragraphe
                story.append(Paragraph(para.text, para_style))
            else:
                # Ajouter un espace pour les paragraphes vides
                story.append(Spacer(1, 0.1*inch))
        
        # Générer le PDF
        pdf_doc.build(story)
        
        if output_path.exists():
            print(f"✓ PDF créé avec reportlab (fallback)")
            return str(output_path)
        else:
            raise Exception("Le PDF n'a pas pu être créé")
            
    except ImportError as ie:
        raise Exception(f"Dépendances manquantes pour la conversion: {ie}. Installez reportlab avec: pip install reportlab")
    except Exception as e:
        raise Exception(f"Erreur de conversion DOCX→PDF: {str(e)}")

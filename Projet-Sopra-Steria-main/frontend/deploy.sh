#!/bin/bash

# 🚀 SCRIPT DÉPLOIEMENT RAPIDE VERCEL

echo "================================"
echo "🚀 CV Generator - Deploy Script"
echo "================================"
echo ""

# Vérifier si on est dans le bon dossier
if [ ! -f "package.json" ]; then
    echo "❌ Erreur: package.json non trouvé!"
    echo "Assurez-vous d'être dans le dossier 'frontend'"
    exit 1
fi

# 1. Nettoyage
echo "🧹 Nettoyage des fichiers temporaires..."
rm -rf node_modules/.cache
rm -rf .next
rm -rf dist
echo "✅ Nettoyage terminé"
echo ""

# 2. Installation des dépendances
echo "📦 Installation des dépendances..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi
echo "✅ Dépendances installées"
echo ""

# 3. Build test local
echo "🔨 Test du build local..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du build"
    exit 1
fi
echo "✅ Build réussi!"
echo ""

# 4. Vérifier Git
echo "🔍 Vérification du repository Git..."
if [ ! -d ".git" ]; then
    echo "⚠️  Pas de repository Git détecté"
    echo "Initialisation de Git..."
    git init
fi
echo "✅ Repository Git OK"
echo ""

# 5. Push vers GitHub
echo "📤 Préparation du push GitHub..."
read -p "Entrez le message de commit: " commit_msg
git add -A
git commit -m "$commit_msg"
git push origin main
if [ $? -ne 0 ]; then
    echo "⚠️  Push échoué (pas de remote ou erreur)"
    echo "Assurez-vous d'avoir configuré le remote 'origin'"
fi
echo ""

# 6. Déployer sur Vercel
echo "🚀 Déploiement sur Vercel..."
echo ""
echo "Deux options:"
echo "1. Vercel CLI (rapide)"
echo "2. Dashboard Vercel (interface web)"
echo ""
read -p "Choisissez (1 ou 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Vérification de Vercel CLI..."
    if ! command -v vercel &> /dev/null; then
        echo "📥 Installation de Vercel CLI..."
        npm install -g vercel
    fi

    echo ""
    echo "Lancement du déploiement..."
    vercel
else
    echo ""
    echo "✅ Allez sur https://vercel.com"
    echo "   → Connectez-vous"
    echo "   → Add New Project"
    echo "   → Sélectionnez votre repository GitHub"
    echo "   → Déployez!"
fi

echo ""
echo "================================"
echo "✅ Script terminé!"
echo "================================"

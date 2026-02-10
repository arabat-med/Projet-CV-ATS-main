# 🚀 Guide de Déploiement Vercel - CV-ATS

## 🔴 ERREUR 404 NOT_FOUND - SOLUTION

L'erreur `404: NOT_FOUND` sur Vercel signifie que **Vercel ne trouve pas votre application**.

### Causes possibles:
1. ❌ **Root Directory mal configuré** sur Vercel
2. ❌ **Build Command incorrect**
3. ❌ **Output Directory incorrect**
4. ❌ **vercel.json mal placé ou mal configuré**

---

## ✅ SOLUTION RAPIDE

### Étape 1: Vérifier la Configuration Vercel

Sur https://vercel.com → Votre projet → **Settings** → **General**

Vérifiez ces paramètres:

| Paramètre | Valeur Correcte |
|-----------|-----------------|
| **Framework Preset** | `Vite` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |
| **Install Command** | `npm install` |

### Étape 2: Déplacer vercel.json à la racine

Le fichier `vercel.json` doit être **à la racine du projet** (pas dans frontend/).

---

## 📁 Structure Correcte du Projet

```
Projet-Sopra-Steria-main/
├── vercel.json          ← À LA RACINE !
├── frontend/
│   ├── dist/            ← Build output
│   ├── public/
│   │   └── _redirects
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── backend/
    ├── api.py
    └── requirements.txt
```

---

## 📝 Configuration vercel.json (À LA RACINE)

Créez ou modifiez `vercel.json` **à la racine du projet**:

```json
{
  "version": 2,
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 🔧 Commandes à Exécuter

```bash
# 1. Aller à la racine du projet
cd Projet-Sopra-Steria-main

# 2. Vérifier que le build fonctionne
cd frontend && npm install && npm run build && cd ..

# 3. Vérifier que dist existe
ls -la frontend/dist/

# 4. Commit et push
git add .
git commit -m "fix: Configuration Vercel corrigée"
git push origin main
```

---

## 🔄 Sur Vercel Dashboard

1. Allez sur https://vercel.com
2. Sélectionnez votre projet
3. Allez dans **Settings** → **General**
4. Modifiez:
   - **Root Directory**: Laissez VIDE (ou `.`)
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Output Directory**: `frontend/dist`
5. Allez dans **Deployments**
6. Cliquez **Redeploy** sur le dernier déploiement

---

## ⚠️ Si ça ne marche toujours pas

### Option B: Déployer uniquement le frontend

1. Sur Vercel Settings:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

2. Le fichier `frontend/vercel.json` doit contenir:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

3. Redéployez

---

## 🧪 Test après déploiement

```bash
curl -I https://votre-app.vercel.app/
# Doit retourner 200

curl -I https://votre-app.vercel.app/start
# Doit retourner 200
```

# Myntra Discovery Engine — Cloud Deployment Plan

This guide provides step-by-step instructions to deploy the **FastAPI Backend on Railway** and the **Next.js Frontend on Vercel** using the pushed GitHub repository:
👉 **Repository:** `https://github.com/danias120/Myntra-Discovery-Engine.git`

---

## 🏗 Deployment Architecture

```mermaid
flowchart TD
    subgraph Client ["Client / End User"]
        Browser["User Browser"]
    end

    subgraph Vercel ["Vercel (Frontend Hosting)"]
        NextApp["Next.js 14 App Router\n(frontend/)"]
    end

    subgraph Railway ["Railway (Backend Hosting)"]
        FastAPI["FastAPI App (backend/)\nUvicorn Server"]
        RAG["RAG Engine (BGE-small + Cross-Encoder)"]
        Corpus[("Clean Corpus (2,065 records)\n& Themes JSON")]
    end

    subgraph External ["External AI Services"]
        Gemini["Google Gemini 2.5 API"]
    end

    Browser -->|HTTPS| NextApp
    NextApp -->|REST / SSE (NEXT_PUBLIC_API_URL)| FastAPI
    FastAPI --> RAG
    RAG --> Corpus
    FastAPI -->|LLM Synthesis| Gemini
```

---

## 📋 Pre-Deployment Checklist

Before beginning, make sure you have:
1. **GitHub Account**: Access to [`https://github.com/danias120/Myntra-Discovery-Engine`](https://github.com/danias120/Myntra-Discovery-Engine).
2. **Railway Account**: Sign up or log in at [railway.app](https://railway.app).
3. **Vercel Account**: Sign up or log in at [vercel.com](https://vercel.com).
4. **Google Gemini API Key**: Obtainable from [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 PART 1: Deploy Backend on Railway

Deploy the backend first so you can obtain its public URL for the frontend.

### Step 1: Create a New Project on Railway
1. Go to your **[Railway Dashboard](https://railway.app/dashboard)**.
2. Click **"+ New Project"**.
3. Select **"Deploy from GitHub repo"**.
4. Choose **`danias120/Myntra-Discovery-Engine`**.
5. Click **"Deploy Now"**.

### Step 2: Configure the Root Directory
Railway needs to know that the backend lives in the `backend/` folder:
1. In the Railway dashboard, click on your newly created service tile.
2. Navigate to the **"Settings"** tab.
3. Scroll down to **"Root Directory"**.
4. Set the Root Directory to:
   ```text
   backend
   ```
5. Click **"Save"**.

### Step 3: Add Environment Variables
1. In your service settings, navigate to the **"Variables"** tab.
2. Add the following environment variables:

| Variable Name | Recommended Value | Description |
|---|---|---|
| `GEMINI_API_KEY` | `AIzaSy...` *(Your Gemini API Key)* | Required for AI Analyst LLM synthesis |
| `CHROMA_PERSIST_DIR` | `data/chroma` | Persistent ChromaDB storage path |
| `FRONTEND_URL` | `*` *(or your Vercel URL later)* | CORS allowed origins |
| `PYTHONUNBUFFERED` | `1` | Ensures real-time logging in Railway |

### Step 4: Generate a Public Domain
1. In your service, navigate to the **"Settings"** tab.
2. Under **"Networking"**, click **"Generate Domain"**.
3. Railway will generate a public URL such as:
   ```text
   https://myntra-discovery-engine-production.up.railway.app
   ```
4. **Copy this URL** (you will need it for Vercel in Part 2).

### Step 5: Verify Backend Health
Open your browser or terminal and test the health endpoint:
```bash
curl https://<your-railway-domain>.up.railway.app/api/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "myntra-discovery-engine",
  "vector_store": {
    "corpus_collection_count": 2065,
    "themes_collection_count": 15
  }
}
```

---

## ⚡ PART 2: Deploy Frontend on Vercel

### Step 1: Import Project to Vercel
1. Go to your **[Vercel Dashboard](https://vercel.com/dashboard)**.
2. Click **"Add New..."** $\to$ **"Project"**.
3. Under *Import Git Repository*, select **`danias120/Myntra-Discovery-Engine`**.

### Step 2: Configure Project Settings
In the configuration screen before clicking Deploy:
1. **Project Name**: `myntra-discovery-engine` (or your preferred name).
2. **Framework Preset**: `Next.js` (automatically detected).
3. **Root Directory**: Click **Edit** and select:
   ```text
   frontend
   ```
4. **Build & Output Settings**:
   * Build Command: `npm run build` (default)
   * Output Directory: `.next` (default)
   * Install Command: `npm install` (default)

### Step 3: Configure Environment Variables
Expand the **"Environment Variables"** accordion and add:

| Key | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-domain>.up.railway.app` | The Railway backend URL copied from Part 1 |

> [!IMPORTANT]
> Do NOT include a trailing slash in `NEXT_PUBLIC_API_URL` (e.g. use `https://xyz.up.railway.app`, not `https://xyz.up.railway.app/`).

### Step 4: Click Deploy
1. Click **"Deploy"**.
2. Wait 60–90 seconds for the production build to finish.
3. Once complete, click **"Continue to Dashboard"** or click on the preview window to visit your live site:
   ```text
   https://myntra-discovery-engine.vercel.app
   ```

---

## 🔒 PART 3: Post-Deployment Security & CORS Lockdown (Optional)

Once your frontend is live on Vercel:
1. Return to your **Railway Backend Dashboard** $\to$ **Variables**.
2. Update `FRONTEND_URL` from `*` to your actual Vercel production URL:
   ```text
   FRONTEND_URL = https://myntra-discovery-engine.vercel.app
   ```
3. Railway will automatically redeploy with strict CORS protection.

---

## ✅ PART 4: Verification & Quality Gates

Verify the 5 core routes on your live Vercel deployment:

| Page | URL Path | Verification Checks |
|---|---|---|
| **Overview** | `/` | KPI metrics display (5,538 collected, 2,065 usable), Top 3 Actionable Insights render, Shopper Segments render. |
| **Reviews Intelligence** | `/reviews` | Source pills filter reviews, Explorer displays 10 records/page, sentiment badges appear. |
| **AI Analyst** | `/ai-analyst` | Ask *"Who are our shopper segments?"* and verify streaming LLM response with clean citations. |
| **Full Hypotheses** | `/ai-analyst` | Ask *"List all our hypotheses with validation status"* and verify the two score-ranked tables (Priority `H1`–`H10` & Emergent `NH1`–`NH6`). |
| **FAQs** | `/faqs` | All 10 canonical research questions display closed by default; clicking "View Source Evidence" opens the modal. |
| **Engine Info** | `/engine-info` | Myntra logo displays without text in header; 8 Ingestion sources breakdown displays correctly. |

---

## 🛠 Troubleshooting & FAQs

### 1. Frontend shows "Failed to load data" or "Network Error"
* **Check:** Ensure `NEXT_PUBLIC_API_URL` on Vercel is set to your exact Railway backend URL without a trailing slash.
* **Fix:** After updating variables on Vercel, go to **Deployments** $\to$ Click the latest deployment $\to$ **Redeploy**.

### 2. Backend fails during build on Railway
* **Check:** Verify that the **Root Directory** on Railway is set to `backend`.
* **Fix:** In Railway settings, ensure `railway.toml` and `Procfile` are being detected.

### 3. AI Analyst returns "Rate limit" or "Authentication failed"
* **Check:** Verify that `GEMINI_API_KEY` is added to Railway environment variables and is active.

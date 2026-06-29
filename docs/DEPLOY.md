# Deploy the 24/7 Cloud Version (Free)

The app runs in the cloud using a **free hosted LLM (Groq)** instead of local Ollama.
RAG is disabled in the cloud (it needs local embeddings); the agents still run.

**Free stack:** Render (hosting) + Neon (Postgres) + Groq (LLM).

---

## 1. Get a free Groq API key (the LLM)
1. Go to https://console.groq.com → sign up (free).
2. **API Keys** → **Create API Key** → copy it (starts with `gsk_...`).

## 2. Get a free Neon Postgres database
1. Go to https://neon.tech → sign up (free).
2. Create a project → copy the **connection string**.
3. ⚠️ Make it SQLAlchemy/psycopg-friendly: it should look like
   `postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require`
   (change the `postgresql://` prefix to `postgresql+psycopg://`).

## 3. Deploy on Render
1. Go to https://render.com → sign up → **New** → **Blueprint**.
2. Connect your GitHub and pick the **ai-incident-manager** repo. Render reads `render.yaml`.
3. When prompted, set the secret env vars:
   - `GROQ_API_KEY` = your `gsk_...` key
   - `DATABASE_URL` = your Neon `postgresql+psycopg://...` string
   (`SECRET_KEY` is auto-generated; `LLM_PROVIDER=groq` and `RAG_ENABLED=false` are preset.)
4. Click **Apply / Deploy**. First build takes a few minutes.
5. When live, open `https://<your-service>.onrender.com/analyze` 🎉

---

## Notes
- **Free Render web services sleep after ~15 min idle** → the first request after idle is slow (~30s cold start), then fast. Fine for a portfolio/demo.
- The DB tables are auto-created on startup. To seed an admin user, register via the app, then in Neon's SQL editor run:
  `UPDATE users SET role='admin' WHERE email='you@example.com';`
- To re-enable RAG in the cloud later, you'd add a hosted embeddings provider — out of scope for the free tier.
- **Local dev is unchanged:** `LLM_PROVIDER=ollama` (default) keeps using your local model.

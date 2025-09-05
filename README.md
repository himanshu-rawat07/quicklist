# QuickList — Advanced To-Do App ✅

QuickList is a **Streamlit-based To-Do app** with SQLite persistence, subtasks, CSV import/export, search, sort, and basic stats.  
It can be run locally or deployed easily on Streamlit Cloud, Render, or Docker.

---

## 🚀 Features
- ✅ Add, edit, delete tasks  
- 🗂️ Subtasks support  
- 🔎 Search, filter, and sort by priority/due date  
- 📊 Stats panel (total, done, overdue)  
- 💾 SQLite persistence  
- 📥 CSV import / 📤 export  
- 🎨 Streamlit modern UI  

---

## 📂 Project Structure
```
quicklist/
│── app.py              # Main Streamlit app
│── requirements.txt     # Python dependencies
│── Dockerfile           # For containerized deploys
│── Procfile             # For Heroku/Render style deploys
│── .dockerignore        # Ignore unnecessary files in Docker build
│── .gitignore           # Ignore venv, db, caches, etc.
│── README.md            # Project documentation
└── quicklist.db         # SQLite database (auto-created, not committed)
```

---

## ⚡ Run Locally
1. Clone the repo:
```bash
git clone <your-repo-url>
cd quicklist
```

2. Create virtual environment & install dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

Visit 👉 http://localhost:8501

---

## 🌐 Deploy

### Streamlit Community Cloud (Fastest)
1. Push repo to GitHub.
2. Go to [Streamlit Cloud](https://share.streamlit.io).
3. Connect repo and deploy.

⚠️ Note: DB persistence (`quicklist.db`) may reset on redeploys.

---

### Render / Heroku
- Uses **Procfile**:
```
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### Docker
Build & run locally:
```bash
docker build -t quicklist .
docker run -p 8501:8501 -v $(pwd)/quicklist.db:/app/quicklist.db quicklist
```

---

## 📦 Requirements
See `requirements.txt`:
```
streamlit>=1.30
pandas
python-dateutil
```

---

## 🔮 Next Steps
- Multi-user support (switch SQLite → PostgreSQL)  
- User authentication  
- Email reminders / notifications  
- Cloud persistence (Supabase / Render PostgreSQL)  

---

Made with ❤️ using Streamlit

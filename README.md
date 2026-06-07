# CareerLens 🚀

**CareerLens** is an ultra-premium, AI-powered ATS (Applicant Tracking System) optimization and resume parsing platform. It lets candidates see their resumes directly through the eyes of recruiters, extracting key metrics, calculating compliance scores, identifying missing skill keywords, generating custom learning roadmaps, and rendering professional PDF feedback reports.

---

## Key Features

1. **AI ATS Scoring Engine** — Simulates how enterprise parsing algorithms score candidate resumes.
2. **Semantic Similarity Parsing** — Uses TF-IDF vectorization with cosine similarity to compare the resume's text semantically to target job description requirements. Lightweight and fast with minimal memory overhead.
3. **Skill Gap Intelligence** — Cross-references technical terms to locate critical missing qualifications.
4. **Chronological Roadmaps** — Generates step-by-step learning schedules to bridge identified gaps.
5. **Database-backed Search Logs** — Secure, session-based scan logs powered by SQLite. Scans are persistent server-side but locked to each visitor's session to preserve absolute privacy.
6. **Report PDF Generator** — Exports parsed metrics, checklist items, and recommendations to a downloadable PDF.
7. **OCR Fallback** — Uses Tesseract OCR to scan image-only or poorly formatted PDF resumes when normal text layers cannot be read.

---

## Technical Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom Grey & White Design System), Vanilla JavaScript (IntersectionObserver for scroll reveals, active state micro-interactions), Chart.js (Radar & Donut charts), Bootstrap 5.
* **Backend**: Python 3.10+, Flask, SQLite (Data persistence), PyMuPDF (PDF extraction), PyTesseract (OCR layers), scikit-learn TF-IDF (semantic similarity), ReportLab (PDF reporting).

---

## Local Setup & Installation

### 1. Prerequisites
* **Python 3.10+** installed on your system.
* **Tesseract OCR** (optional, needed for image-only OCR fallback):
  * **Windows**: Download the installer from UB-Mannheim and install it to `C:\Program Files\Tesseract-OCR\`.
  * **Mac**: Install via Homebrew: `brew install tesseract`.
  * **Linux**: Install via apt: `sudo apt-get install tesseract-ocr`.

### 2. Configure Virtual Environment & Install Dependencies
Clone the repository, navigate into the directory, and set up the environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Server
Start the local server:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## Database Schema Configuration

The application automatically creates a local SQLite database file named `careerlens.db` upon startup. It contains the `scans` table which tracks scan history:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary key (auto-incrementing). |
| `session_id` | `TEXT` | Secure UUID stored in Flask user cookie to isolate history logs. |
| `timestamp` | `DATETIME` | Time the scan was completed. |
| `filename` | `TEXT` | Name of the parsed PDF file. |
| `extraction_method` | `TEXT` | Parsing strategy (`PDF Text Extraction` or `OCR Extraction`). |
| `job_description` | `TEXT` | Paste text of target requirements. |
| `final_score` | `REAL` | Overall compatibility index. |
| `skill_match` | `REAL` | Exact keyword overlap score. |
| `semantic_match` | `REAL` | Embedding cosine similarity score. |
| `resume_strength` | `REAL` | Score based on required resume sections. |
| `badge` | `TEXT` | Strength rating (`Job Ready`, `Advanced`, `Intermediate`, `Beginner`). |
| `results_json` | `TEXT` | Full JSON results payload (allows instant local scan reloading). |

---

## Production Deployment (Render + Docker)

CareerLens uses lightweight TF-IDF for semantic matching instead of heavy ML models, making it an ideal fit for Render's free tier:
- ✅ **Minimal RAM usage** (~50MB vs 400MB+ with Sentence Transformers)
- ✅ **Fast cold starts** (heavy libraries are lazy-loaded on first request, not at boot)
- ✅ **Docker support** with automatic Tesseract OCR installation

### One-Click Deployment Setup

We have included a `render.yaml` blueprint and a custom `Dockerfile` in the root:

1. Push this project repository to **GitHub**.
2. Go to your **Render Dashboard**, click **Blueprints**, and connect your Github repository.
3. Render will parse `render.yaml` and configure:
   * A Python web service built via the `Dockerfile`.
   * Automatic installation of `tesseract-ocr` for OCR.
   * Auto-mapping of Port `5000` to Render's public router.

Alternatively, you can create a new **Web Service** manually on Render, choose **Docker** as the environment runtime, and click **Deploy**.

### Environment Variables

Create a `.env` file in the project root (or configure via Render dashboard) with the following variables:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here

# Database Path (optional, defaults to careerlens.db)
# DATABASE_PATH=/data/careerlens.db

# Tesseract OCR Path (Docker sets this automatically)
# TESSERACT_CMD=/usr/bin/tesseract

# Port (Render sets this automatically)
PORT=5000
```

**Important**: Generate a secure `SECRET_KEY` for production:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then set it in Render's Environment Variables dashboard.

---

## Keeping Your Free Tier Awake (Render)

Render's free tier spins down your container after **15 minutes of inactivity**, causing a 30-50 second cold-start delay for the next visitor. To keep your app warm 24/7:

### Option 1: UptimeRobot (Recommended — Free)
1. Create a free account at [UptimeRobot.com](https://uptimerobot.com/)
2. Add a new **HTTP(s) Monitor**:
   - **URL**: `https://your-app-name.onrender.com/`
   - **Monitoring Interval**: `5 minutes`
3. UptimeRobot will ping your app every 5 minutes, keeping the container alive.

### Option 2: Cron-job.org (Free)
1. Create a free account at [cron-job.org](https://cron-job.org/)
2. Create a new cron job:
   - **URL**: `https://your-app-name.onrender.com/`
   - **Schedule**: Every 12 minutes (`*/12 * * * *`)
3. The service will send an HTTP GET request on schedule to prevent sleep.

### Option 3: Render Starter Plan ($7/month)
Upgrade to Render's Starter tier for always-on containers with zero cold starts.

---

## Deployment Troubleshooting

### Issue: "No such file or directory: 'tesseract.exe'"
**Solution**: On Render/Linux, Tesseract is installed via apt in the Dockerfile. The code automatically detects it at `/usr/bin/tesseract`.

### Issue: Database permission errors on Render
**Solution**: Use an absolute path for the database in a writable directory, or use the environment variable:
```env
DATABASE_PATH=/tmp/careerlens.db
```

---

## File Structure

```
CareerLens/
├── app.py                # Main Flask application
├── database.py           # SQLite database management
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration
├── render.yaml           # Render deployment blueprint
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
├── static/
│   ├── css/style.css     # Frontend styles
│   └── js/app.js         # Frontend logic
├── templates/
│   ├── index.html        # Home page
│   └── result.html       # Results page
└── uploads/              # Temporary file uploads
```

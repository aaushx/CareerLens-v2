# CareerLens 🚀

**CareerLens** is an ultra-premium, AI-powered ATS (Applicant Tracking System) optimization and resume parsing platform. It lets candidates see their resumes directly through the eyes of recruiters, extracting key metrics, calculating compliance scores, identifying missing skill keywords, generating custom learning roadmaps, and rendering professional PDF feedback reports.

---

## Key Features

1. **AI ATS Scoring Engine** — Simulates how enterprise parsing algorithms score candidate resumes.
2. **Semantic Similarity Parsing** — Uses Sentence Transformers (`all-MiniLM-L6-v2`) to compare the resume's text semantically to target job description requirements.
3. **Skill Gap Intelligence** — Cross-references technical terms to locate critical missing qualifications.
4. **Chronological Roadmaps** — Generates step-by-step learning schedules to bridge identified gaps.
5. **Database-backed Search Logs** — Secure, session-based scan logs powered by SQLite. Scans are persistent server-side but locked to each visitor's session to preserve absolute privacy.
6. **Report PDF Generator** — Exports parsed metrics, checklist items, and recommendations to a downloadable PDF.
7. **OCR Fallback** — Uses Tesseract OCR to scan image-only or poorly formatted PDF resumes when normal text layers cannot be read.

---

## Technical Stack

* **Frontend**: HTML5, Vanilla CSS3 (Custom Grey & White Design System), Vanilla JavaScript (IntersectionObserver for scroll reveals, active state micro-interactions), Chart.js (Radar & Donut charts), Bootstrap 5.
* **Backend**: Python 3.10+, Flask, SQLite (Data persistence), PyMuPDF (PDF extraction), PyTesseract (OCR layers), Sentence Transformers (semantic embeddings), ReportLab (PDF reporting).

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

Since **Sentence Transformers** and **PyTorch** can have a heavy disk and memory footprint, deploying standard packages directly can exceed free-tier limitations (e.g. Render's 512MB RAM ceiling). 

To deploy successfully on Render:
1. We use **Docker** (Render's Docker build environment installs native Linux apt packages like `tesseract-ocr` automatically).
2. We install the **CPU-only PyTorch build** (`--index-url https://download.pytorch.org/whl/cpu`), which reduces the image size from >2GB to under 300MB and fits well within memory limits.

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

## Deployment Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'torch'"
**Solution**: The Dockerfile installs CPU-only PyTorch via a specific index URL. Ensure Docker build is being used, not pip install from environment.

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

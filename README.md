# CareerLens 🚀

**CareerLens** is an ultra-premium, AI-powered Applicant Tracking System (ATS) optimization and resume parsing platform. It lets candidates analyze their resumes directly through the eyes of recruiters, extracting key metrics, calculating compatibility scores, mapping missing skill keywords, generating custom weekly learning roadmaps, and producing professional ReportLab PDF feedback reports.

---

## 🛠️ Key Features

1.  **AI ATS Scoring Engine** — Computes weighted compatibility indexes based on keywords, layout headers, contact presence, active action verbs, and quantified accomplishments.
2.  **Semantic Match Parsing** — Utilizes scikit-learn TF-IDF vocabulary extraction and cosine similarity to compare resume text directly against job descriptions, avoiding heavy model overheads.
3.  **Skill Gap Intelligence** — Cross-references technical qualifiers to locate missing capabilities.
4.  **Chronological Learning Roadmaps** — Automatically structures step-by-step weekly learning timelines to bridge identified gaps.
5.  **Database-backed Scan Logs** — Encapsulates secure, session-isolated SQL logs to reload historical scans.
6.  **Report PDF Generator** — Compiles metrics and checklists into downloadable, professional feedback reports.
7.  **OCR Fallback Parser** — Invokes Tesseract OCR to scan image-only or poorly formatted PDF resumes when standard text extraction fails.
8.  **Accessible UI/UX Design** — High-contrast elements, screen-reader ARIA tags, keyboard focus rings, drag-and-drop file uploaders, and animated skeleton loading states.

---

## 🖥️ Technology Stack

*   **Frontend:** HTML5 (ARIA tagged), CSS3 (Dark/Light visual systems, skeleton animations), JavaScript (IntersectionObserver, Chart.js).
*   **Backend:** Python 3.12, Flask, SQLite (indexed queries), PyMuPDF (PDF parsing), PyTesseract (OCR engine), scikit-learn TF-IDF (cosine similarity), ReportLab (PDF reporting).

---

## 🚀 Local Installation & Quick Start

Follow these steps to install and run CareerLens locally on your PC:

### 1. Prerequisites
*   **Python 3.12** installed on your system.
*   **Tesseract OCR Engine** *(Optional, required only for scanned PDF resumes)*:
    *   *Windows:* Install to `C:\Program Files\Tesseract-OCR\`.
    *   *macOS:* Install via Homebrew: `brew install tesseract`.
    *   *Linux:* Install via apt: `sudo apt-get install tesseract-ocr`.

### 2. Setup Commands

Open your terminal or command prompt:

```bash
# 1. Clone the repository and enter the folder
git clone https://github.com/aaushx/CareerLens-v2.git
cd CareerLens-v2

# 2. Create a virtual environment and activate it
# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

# 2. Install package dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Initialize the SQLite Database
python -c "from app.database import init_db; init_db()"

# 4. Start local Flask development server
# On Windows (PowerShell):
$env:FLASK_ENV="development"
python wsgi.py

# On macOS/Linux:
export FLASK_ENV="development"
python wsgi.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser!

---

## 📂 Repository Layout

```
CareerLens/
├── app/                       # Core python source packages
│   ├── __init__.py            # Application Factory configuration
│   ├── config.py              # Upload limits and binary configurations
│   ├── database.py            # SQLite schema and query index
│   ├── routes.py              # Route endpoints blueprints
│   ├── data/                  # Static domain dictionaries
│   └── services/              # PDF, NLP, OCR parsing modules
├── static/                    # Frontend style and logic scripts
├── templates/                 # HTML templates
├── uploads/                   # Temporary upload cache directory
├── wsgi.py                    # Web app starter script
├── requirements.txt           # Production packages
└── README.md                  # Project landing page (this document)
```

---

## 📄 License
This project is licensed under the MIT License.

---

## 👥 Authors
*   **CareerLens Core Engineering Team** - [GitHub](https://github.com/your-username/CareerLens)

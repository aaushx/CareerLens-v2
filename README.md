# CareerLens 🚀

[![CI/CD Build](https://github.com/your-username/CareerLens/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/CareerLens/actions)
[![Python Version](https://img.shields.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Test Coverage](https://img.shields.shields.io/badge/coverage-80%25-green.svg)](docs/walkthrough.md#-verification-results)
[![License](https://img.shields.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![A11y Compliant](https://img.shields.shields.io/badge/a11y-WCAG%20AA-brightgreen.svg)](docs/walkthrough.md#accessibility-a11y-responsiveness)

**CareerLens** is an ultra-premium, AI-powered Applicant Tracking System (ATS) optimization and resume parsing platform. It lets candidates analyze their resumes directly through the eyes of recruiters, extracting key metrics, calculating compatibility scores, mapping missing skill keywords, generating custom weekly learning roadmaps, and producing professional ReportLab PDF feedback reports.

---

## 📖 Complete Documentation Index

For detailed guides, please refer to the following resources in the **[docs/](docs/)** directory:

*   📖 **[Local Installation Guide](docs/INSTALLATION.md)** — Detailed setups for Windows, Linux, and macOS.
*   🚀 **[Quick Clone Guide](docs/CLONE_GUIDE.md)** — Step-by-step instructions for beginners to clone and run the app.
*   🗺️ **[System Architecture](docs/ARCHITECTURE.md)** — Detailed pipeline explanations and Mermaid workflow charts.
*   🔌 **[API Documentation](docs/API.md)** — Comprehensive REST endpoint request payloads and response definitions.
*   🚢 **[Production Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** — Gunicorn configurations, Docker non-root users, and cloud blueprints.
*   🤝 **[Contributing Guidelines](docs/CONTRIBUTING.md)** — Branch naming structures, Git Commit rules, and Quality QA gates.
*   📂 **[Repository Folder Map](docs/PROJECT_STRUCTURE.md)** — Detailed listing of file locations and purposes.
*   📜 **[Milestone Changelog](docs/CHANGELOG.md)** — Keeping a Changelog log tracking sprint updates from v1.0.0 through v5.0.0.

---

## 🛠️ Key Features

1.  **AI ATS Scoring Engine** — Computes weighted compatibility indexes based on keywords, layout headers, contact presence, active action verbs, and quantified accomplishments.
2.  **Semantic Match Parsing** — Utilizes scikit-learn TF-IDF vectorization and cosine similarity to compare resume text directly against job descriptions, avoiding heavy model overheads.
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
*   **DevOps:** Docker (runs under non-root system user `careerlens`), Render blueprints, GitHub Actions CI.

---

## 🚀 Quick Start (Local Run)

Navigate to your workspace, create a virtual environment, install dependencies, and run:

```bash
# Clone and enter directory
git clone https://github.com/your-username/CareerLens.git
cd CareerLens

# Activate environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env config, initialize database, and start development server
cp .env.example .env
python -c "from app.database import init_db; init_db()"
export FLASK_ENV="development" # On Windows: $env:FLASK_ENV="development"
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 📂 Repository Layout

```
CareerLens/
├── app/                       # Core python source packages
├── docs/                      # Technical documentation and guides
├── static/                    # Frontend style and logic scripts
├── templates/                 # HTML templates
├── tests/                     # Automated testing suite
├── scratch/                   # DB performance benchmarking scripts
├── LICENSE                    # MIT License
├── README.md                  # Project landing page (this document)
├── requirements.txt           # Production packages
└── requirements-dev.txt       # Local developer tools
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors
*   **CareerLens Core Engineering Team** - [GitHub](https://github.com/your-username/CareerLens)

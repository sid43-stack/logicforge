# NetSage — AI-Based Network Troubleshooting Expert System

NetSage is a Knowledge-Based Expert System (KBES) designed to diagnose common computer network connectivity problems through logical reasoning, production rules, dynamic inquiry, and dual-chaining inference (forward & backward chaining).

---

## Key Features

- **Pure Python Custom Expert System Core**: Completely handcrafted inference engine without third-party rule engines (no `Experta`, `PyKnow`, or LLMs).
- **Tri-State Logic Working Memory**: Explicit truth maintenance distinguishing `TRUE`, `FALSE`, and `UNKNOWN`.
- **Chained Production Rules**: Over 25 production rules structured into 6 diagnostic problem categories (DNS, DHCP, Gateway, Wi-Fi, Packet Loss/Latency, ISP).
- **Dynamic Question Generation**: Intelligent question selection driven by backward-chaining hypotheses and unresolved conditions.
- **WHY & HOW Explanation Facilities**: Contextual justification for every diagnostic inquiry and full audit trace for the final diagnosis.
- **Inference Tree Visualization**: Visual trace graph of facts, rules, and diagnoses.
- **Interactive Knowledge Base Explorer**: Browser for domain axioms, production rules, and chaining dependencies.
- **FastAPI + SQLite Persistence**: Complete session auditing, answer history, and remediation plans.
- **React + TypeScript + Tailwind CSS Frontend**: Responsive interface with a warm ivory, brass, and espresso color palette.

---

## Project Structure

```text
NetSage/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints (health, diagnostics, knowledge, history)
│   │   ├── core/                # Configuration & environment settings
│   │   ├── database/            # SQLAlchemy database engine and session factory
│   │   ├── expert_system/       # Handcrafted Pure Python Expert System Core
│   │   ├── models/              # SQLAlchemy models (sessions, answers, traces, recommendations)
│   │   ├── schemas/             # Pydantic v2 schemas and data validation
│   │   ├── services/            # Application business logic services
│   │   └── main.py              # FastAPI application entrypoint
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt         # Pinned backend dependencies
│   └── pytest.ini               # Pytest configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components (Navbar, Footer, Spinner)
│   │   ├── pages/               # 7 application pages (Landing, Dashboard, Wizard, Result, Explain, History, Knowledge)
│   │   ├── services/            # Axios API client
│   │   ├── types/               # TypeScript type definitions
│   │   ├── App.tsx              # React router configuration
│   │   └── main.tsx             # React entrypoint
│   ├── package.json             # Pinned frontend dependencies
│   └── vite.config.ts           # Vite tooling & backend proxy
│
├── docs/                        # Architectural documentation and specifications
├── PLAN.md                      # Comprehensive project specification and phase plan
└── README.md
```

---

## Getting Started

### Backend Setup
```bash
# 1. Activate Python virtual environment
.\.venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run backend tests
python -m pytest backend -v

# 4. Start backend development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir backend
```

### Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start frontend development server
npm run dev
```
Access the application at `http://localhost:5173`.

### Deploy on Render

The repository includes a `render.yaml` Blueprint and a multi-stage `Dockerfile`. In Render, create a new Blueprint from `sid43-stack/logicforge` and apply the `netsage` web service and `netsage-db` PostgreSQL database. The service builds the React frontend and serves it together with the FastAPI API.

The included Blueprint selects free resources for demonstration use. Render's free web service sleeps after 15 minutes without traffic, and its free PostgreSQL database expires after 30 days. Upgrade the database before it expires to keep stored diagnostic history. Local SQLite is intended for development; Render uses the `DATABASE_URL` supplied by its PostgreSQL service.


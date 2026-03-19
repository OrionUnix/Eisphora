# Eisphora

> 🧾 **Eisphora** is an open-source, secure-by-design crypto tax app — built in Django with no exposed REST API.  
> 🧠 Local key derivation (Argon2/PBKDF2), AES-256 encryption, FIFO-based reporting, Julia-powered calculations.  
> 🔐 Frontend uses Django Templates + Tailwind + GSAP/Vue.js — minimal JS, no attack surface.  
> 🇫🇷🇺🇸🇱🇺 Focused on privacy, legal clarity, and multilingual support.  
> ⚠️ Built by one developer, security first. Next.js/React-ready for future versions.

**Eisphora** is an open-source web application designed to simplify crypto-related tax management. Initially focused on the French tax system, it aims to support the US, Luxembourg, and other jurisdictions. Developed by a solo developer, the project emphasizes **security**, **clarity**, and **long-term maintainability**.

> ✦ Multilingual, auditable, and privacy-first.  
> ✦ Built without exposing a REST API or relying on external frontend runtimes like Next.js.

---
![alt text](image.png)

## 🔒 The "Stateless" Security Model

Most tax applications store your financial history in databases (PostgreSQL, MongoDB), requiring complex encryption mechanisms (AES-256) and creating massive honeypots for hackers. 

**Eisphora takes a different approach:**
1. **In-Memory Processing:** Uploaded CSV files (like Coinbase exports) are handled strictly in RAM via Django's `MemoryFileUploadHandler`.
2. **Zero-Disk Policy:** Once the FIFO calculations are done and the HTML results are rendered to your screen, the memory is wiped. 
3. **No User Accounts Needed:** By not forcing users to create accounts, we eliminate the risks of token leakage, password breaches, or identity theft.

---
## 🔒 Why This Architecture?

The project originally used a React/Next.js frontend connected to Django via REST APIs. This introduced:

- A broader attack surface (CORS, CSRF, token leakage risks),
- An overcomplicated setup for a local or low-userbase deployment,
- An unnecessary architectural split for a secure, single-user tool.

Instead, Eisphora now uses **Django Templates** for rendering, along with modern frontend libraries (Tailwind, GSAP, Vue.js) directly embedded into the server-rendered flow. Data encryption and key management are **performed locally** in the browser using `IndexedDB` and `PBKDF2/Argon2`.

> Nothing prevents future reintegration of a modern frontend stack (like Next.js), but only once the app is secure and stable enough to justify it.

---

## ✨ Features

- Tax reporting based on FIFO method and income brackets
- Advanced transaction management
- Multilingual UI (English, French, Spanish)
- AES-256 secure data encryption (local + server)
- Heavy computation offloading using Julia
- Transformer-based LLM for tax interpretation
- Declarative BPMN workflows with Camunda
- Document and reporting generation
- GDPR-friendly by design

---

## 🧠 Architecture Overview

Here is the updated architecture diagram reflecting the current stack:

```mermaid
graph TD
    A[User] -->|HTTPS| B[Frontend: Django Templates]
    subgraph Frontend
        B -->|Tailwind CSS| C[Responsive UI]
        B -->|GSAP| D[Parallax Animations]
        B -->|Vue.js| E[Lightweight Interactions]
        B -->|IndexedDB| F[Local Key Storage]
        F -->|PBKDF2/Argon2| G[Key Derivation]
    end
    B --> H[Django Server]
    subgraph Backend_Django
        H --> I[Apps]
        I --> J[core: Global Models, Utils]
        I --> K[users: Signup & Login]
        I --> L[calculator_FIFO: FIFO Engine]
        I --> M[taxes: Country-specific Logic]
        I --> N[documents: Reports & Exports]
        I --> O[analytics: Dashboards & Metrics]
        H --> P[Celery Tasks]
        H -->|AES-256| Q[django-cryptography]
        H --> R[django-otp]
        H --> S[django-gdpr-assistant]
        H --> T[Julia via pyjulia]
        H --> U[LLM Transformers]
        H --> V[Camunda BPMN Engine]
    end
    H --> W[Webhooks]
    H --> X[PostgreSQL]
    X --> Y[pg_cron]
    X --> Z[pgjwt]
    X --> AA[TOAST Compression]
    X --> AB[Readonly Role]
    H --> AC[Redis]
    H --> AD[MinIO]
    H --> AE[Azure Key Vault]
```

##  🚀 Installation Guide

### 1. Clone the Repository

```git clone https://github.com/OrionUnix/Eisphora.git
cd Eisphora
```

#### 2. Configure Environment Variables

**Backend**
Copy or create a .env file at the project root:

```bash
cp .env.example .env
# Edit it with your DB credentials, secret keys, etc.
```

**_Frontend (Optional)  _**
Only if you reintroduce the frontend build process (Vue/Next.js/etc.):

```touch frontend/.env.local
# Example:
NEXT_PUBLIC_BASE_URL=http://localhost:8000

```

### Install Backend Dependencies

```cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### 4. (Optional) Install Frontend Dependencies

Only if you re-enable JS assets:

```cd ../frontend
npm install```

### 5. Apply Database Migrations

```cd ../backend
python manage.py migrate

```

### 6. Build Frontend Assets (Optional)

```./build_frontend.sh
# or manually: cd frontend && npm run build
```

### 7. Run the Server

``` cd backend
python manage.py runserver
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to the project.

## 📄 License

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details.

## 🧭 Roadmap

 * Expand tax logic to US, Luxembourg, Germany
 * Improve local encryption UX (password entropy hints, key backup)
 * Add PDF export of tax reports
 * Consider reintroducing REST API + external frontend (as an opt-in)

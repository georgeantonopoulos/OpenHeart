# OpenHeart Cyprus

**Open-source Cardiology EMR for Cypriot Cardiologists**

[![License: Polyform Noncommercial](https://img.shields.io/badge/License-Polyform%20NC-purple.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

OpenHeart is a modern, GDPR-compliant Electronic Medical Records (EMR) system designed specifically for cardiologists practicing in Cyprus. It combines clinical decision support, DICOM imaging integration, and seamless Gesy (General Healthcare System) compatibility.

## Features

### Clinical Decision Support System (CDSS)

Evidence-based risk calculators validated against ESC Guidelines:

- **GRACE Score** - Acute Coronary Syndrome risk stratification
- **CHA₂DS₂-VASc** - Stroke risk in Atrial Fibrillation
- **HAS-BLED** - Bleeding risk assessment for anticoagulation decisions

### Clinical Documentation

- Version-controlled clinical notes with full audit history
- SOAP note structure with structured cardiac parameters
- File attachments with automatic text extraction
- Full-text search across all documentation

### DICOM Imaging

- Integrated Orthanc PACS server
- OHIF Viewer for study visualization
- DICOMweb (WADO-RS) protocol support
- Echo reports with LVEF, wall motion, valve status

### Compliance & Security

- **GDPR** (EU General Data Protection Regulation)
- **Cyprus Law 125(I)/2018** (Personal Data Protection)
- **Gesy** integration ready
- PII encryption at rest (Fernet)
- Complete audit logging with 15-year retention
- Row-Level Security for multi-tenant isolation

### Localization

- Greek and English language support
- Cyprus date format (DD/MM/YYYY)
- Cyprus phone format (+357)
- Cyprus ID and ARC number validation

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Shadcn UI |
| **Backend** | FastAPI, Python 3.11, Pydantic, SQLAlchemy |
| **Database** | PostgreSQL 16 with pgvector |
| **Caching** | Redis 7 |
| **File Storage** | MinIO (S3-compatible) |
| **DICOM** | Orthanc + OHIF Viewer |
| **DevOps** | Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/georgeantonopoulos/OpenHeart.git
cd OpenHeart
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your secure passwords
```

Generate secure keys:

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate PII_ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Start the Stack

```bash
docker-compose up
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend | <http://localhost:3000> |
| Backend API | <http://localhost:8000> |
| API Documentation | <http://localhost:8000/docs> |
| Orthanc DICOM | <http://localhost:8042> |
| MinIO Console | <http://localhost:9001> |

## Project Structure

```
OpenHeart/
├── backend/
│   ├── app/
│   │   ├── core/           # Security, audit, encryption
│   │   ├── db/             # Database session, base models
│   │   ├── integrations/   # Gesy, FHIR adapters
│   │   └── modules/
│   │       ├── cardiology/ # CDSS calculators
│   │       ├── notes/      # Clinical documentation
│   │       ├── patient/    # Patient management
│   │       └── encounter/  # Visit/encounter tracking
│   └── alembic/            # Database migrations
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React components
│   │   └── locales/        # i18n translations
│   └── tailwind.config.ts
├── docker-compose.yml
└── .env.example
```

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with hot reload (requires running services)
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Running Tests

```bash
# Backend tests
pytest backend/

# Frontend tests
npm run test --prefix frontend

# Backend with coverage
pytest backend/ --cov=app --cov-report=html
```

## API Documentation

When running in development mode, interactive API documentation is available at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/cdss/grace` | Calculate GRACE Score |
| `POST /api/cdss/cha2ds2-vasc` | Calculate CHA₂DS₂-VASc |
| `POST /api/cdss/has-bled` | Calculate HAS-BLED |
| `GET /api/notes/{patient_id}` | List patient notes |
| `POST /api/notes` | Create clinical note |
| `GET /health` | Health check with service status |

## Cardiology Domain

OpenHeart uses cardiology-specific fields and structures:

### Cardiac Parameters

- **LVEF** (Left Ventricular Ejection Fraction)
- **NYHA Class** (I-IV)
- **Killip Class** (I-IV)
- **Syntax Score** for PCI complexity
- **Wall Motion** abnormalities
- **Valve Status** (stenosis/regurgitation grades)

### Procedure Documentation

- Catheterization access site (Radial/Femoral)
- Stent details (type, dimensions, location)
- Contrast volume and radiation dose

## Security

### GDPR Compliance

All access to patient data is logged to the `security_audit` table:

- User ID and role
- IP address and user agent
- Resource accessed
- Action performed (READ, CREATE, UPDATE, DELETE)
- Timestamp

### PII Encryption

Sensitive fields are encrypted at rest using Fernet symmetric encryption:

- Patient names
- Cyprus ID / ARC numbers
- Contact information
- Addresses

### Authentication

- JWT-based authentication with 15-minute expiry
- Refresh token rotation
- Session management via Redis

## Gesy Integration

OpenHeart is designed for seamless Gesy integration using an adapter pattern:

```python
from app.integrations.gesy import get_gesy_provider

gesy = get_gesy_provider()
eligibility = await gesy.check_eligibility(patient_id="CY12345678")
```

The `IGesyProvider` interface allows:

- Mock implementation for development
- Real API integration for production
- Easy testing without external dependencies

## Contributing

We welcome contributions! Please see our contributing guidelines (coming soon).

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` and `npm test`)
5. Commit with descriptive message
6. Push to your fork
7. Open a Pull Request

## Roadmap

- [ ] Patient registration and demographics
- [ ] Encounter/visit management
- [ ] ECG module with interpretation
- [ ] Echocardiography reporting
- [ ] Catheterization lab module
- [ ] FHIR R4 export/import
- [ ] Gesy API integration
- [ ] Mobile-responsive design
- [ ] Offline capability (PWA)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [ESC Guidelines](https://www.escardio.org/Guidelines) for clinical algorithms
- [GRACE ACS Risk Calculator](https://www.outcomes-umassmed.org/grace/)
- [Orthanc DICOM Server](https://www.orthanc-server.com/)
- [OHIF Viewer](https://ohif.org/)

---

**Disclaimer**: OpenHeart is a clinical decision support tool. All risk scores and recommendations are for informational purposes only. Final treatment decisions must be made by qualified healthcare professionals based on complete clinical assessment.

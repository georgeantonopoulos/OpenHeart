# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenHeart Cyprus is an open-source Cardiology EMR tailored for Cypriot cardiologists. Key constraints:

- **Compliance:** GDPR (EU), Law 125(I)/2018, Gesy (General Healthcare System) compatibility
- **Localization:** Dates as DD/MM/YYYY, phone numbers +357 format, Patient IDs use ID Card or ARC (Alien Registration Certificate)
- **i18n:** Greek/English support required from day one

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, Shadcn UI |
| Backend | FastAPI (Python 3.11), Pydantic, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 (with pgvector for future AI search) |
| Cache/Sessions | Redis 7 |
| File Storage | MinIO (S3-compatible) |
| Imaging | Orthanc (DICOM Server) + OHIF Viewer |
| DevOps | Docker Compose (6 services) |

## Commands

```bash
# Run development stack (all 6 services)
docker compose up

# Run with rebuild
docker compose up --build

# Backend tests (CDSS has 40+ tests)
cd backend && pytest

# Frontend tests (Jest configured, tests pending)
cd frontend && npm test
```

## Architecture

**Backend Structure:** `backend/app/`

- `core/` - Security infrastructure (JWT, RBAC, audit, encryption)
- `modules/` - Feature-based modules
- `db/` - SQLAlchemy base, session management, mixins
- `integrations/` - External system adapters (Gesy, DICOM, FHIR)

**Frontend Structure:** `frontend/src/`

- `app/` - Next.js App Router pages
- `components/` - Reusable UI components
- `lib/` - Utilities and API clients

**CDSS Engine:** Located in `backend/app/modules/cardiology/cdss/`. Implements GRACE, CHA₂DS₂-VASc, and HAS-BLED calculators with comprehensive test coverage.

**DICOM Integration:** Uses WADO-RS protocol to communicate with Orthanc server. OHIF Viewer for study viewing. (Infrastructure ready, implementation pending)

## Coding Standards

**Python:**

- Black formatter
- Strict type hints enforced
- Pydantic for all data validation

**TypeScript:**

- Strict mode enabled
- Functional components only
- Zod for validation

## Cardiology Domain Rules

- Use cardiology-specific fields (e.g., "NYHA Class" not generic "Status", LVEF, Syntax Score)
- Clinical notes must use structured data for cardiac parameters
- Echo reports need: LVEF %, Wall Motion, Valve status
- Catheterization needs: Access site (Radial/Femoral), Stents placed

## Current Implementation Status

| Module           | Status      | Location                                                 |
| ---------------- | ----------- | -------------------------------------------------------- |
| CDSS Calculators | Complete    | `backend/app/modules/cardiology/cdss/`                   |
| Clinical Notes   | Complete    | `backend/app/modules/notes/`                             |
| Security Core    | Partial     | `backend/app/core/` (design complete, endpoints pending) |
| Patient Models   | Models Only | `backend/app/modules/patient/` (no API)                  |
| User Management  | Not Started | See `agents/user_management_plan.md`                     |
| Frontend App     | Shell Only  | Login page placeholder, no API integration               |

**Critical Gap:** User authentication and management is designed but not implemented. See [agents/user_management_plan.md](agents/user_management_plan.md) for the complete implementation plan.

## Security Requirements (GDPR)

- PII must be isolated and encrypted at rest (Fernet encryption in `core/encryption.py`)
- All data access logged to `security_audit` table
- Audit captures: User ID, IP address, timestamp, resource accessed
- MFA required for clinical staff (TOTP support designed, implementation pending)
- Password hashing with Argon2id (planned upgrade from bcrypt)

## RBAC Roles

Defined in `backend/app/core/permissions.py`:

- `SYSTEM_ADMIN` - Full system access
- `CLINIC_ADMIN` - Clinic-level management
- `CARDIOLOGIST` - Full clinical access
- `NURSE` - Limited clinical access
- `RECEPTIONIST` - Patient demographics only
- `LAB_TECH` - Lab results access
- `BILLING_STAFF` - Billing/claims only
- `AUDITOR` - Read-only audit access

## Integration Patterns

**Gesy:** Use adapter pattern with `IGesyProvider` interface - allows mock implementation for testing and real API swap later. Mock provider implemented in `backend/app/integrations/gesy/`.

**DICOM:** Orthanc server at port 8042 (API) and 4242 (DICOM protocol). Integration stub exists but implementation pending.

**FHIR:** Stub exists at `backend/app/integrations/fhir/`, implementation pending.

## API Patterns

- All endpoints use async/await with SQLAlchemy 2.0
- Permission decorators: `@require_permission(Permission.PERMISSION_NAME)`
- Audit middleware logs all requests automatically
- Health check at `/health` probes all services
- API docs at `http://localhost:8000/docs`

## SQLAlchemy 2.0 Notes

- Raw SQL requires `text()` wrapper: `await conn.execute(text("SELECT 1"))`
- Use `select()` not `session.query()`
- All sessions are async via `AsyncSession`
- Base mixins: `TimestampMixin`, `SoftDeleteMixin`, `AuditMixin`

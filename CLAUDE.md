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
| Backend | FastAPI (Python 3.11), Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 (with pgvector for future AI search) |
| Imaging | Orthanc (DICOM Server) + OHIF Viewer |
| DevOps | Docker Compose |

## Commands

```bash
# Run development stack
docker-compose up

# Backend tests
pytest backend/

# Frontend tests
npm run test --prefix frontend
```

## Architecture

**Feature-based folder structure:** `modules/patient`, `modules/ecg`, etc.

**CDSS Engine:** The [cardio_rish_engine.py](cardio_rish_engine.py) contains risk score calculations (GRACE, ASCVD). Uses Pydantic models for validation and returns structured recommendations.

**DICOM Integration:** Uses WADO-RS protocol to communicate with Orthanc server. OHIF Viewer embedded in React components for study viewing.

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

## Security Requirements (GDPR)

- PII must be isolated and encrypted at rest
- All data access logged to `security_audit` table
- Audit captures: User ID, IP address, timestamp, resource accessed

## Integration Patterns

**Gesy:** Use adapter pattern with `IGesyProvider` interface - allows mock implementation for testing and real API swap later.

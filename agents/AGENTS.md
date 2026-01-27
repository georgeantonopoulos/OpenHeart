# OpenHeart Cyprus - Agents Knowledge Base

## Overview

This file tracks findings, architectural decisions, and integration requirements discovered by AI agents working on the OpenHeart Cyprus EMR.

## Key Findings (2026-01-21)

### 1. Regulatory & Compliance (Cyprus)

- **Law 125(I)/2018**: Implements GDPR with strict rules on biometric/genetic data (prohibited for insurance processing).
- **Data Retention**: Patient records must be kept for **15 years** after death or the last record entry.
- **Audit Logging**: Mandatory clinical audit trails must be partitioned (e.g., by month) to maintain performance over long retention periods.

### 2. Clinical Decision Support (Cardiology)

- **PREVENT Equations (2023)**: Recommended over the 2013 ASCVD Pooled Cohort Equations. PREVENT is race-agnostic and includes Heart Failure risk.
- **EuroSCORE II**: Critical for "Heart Team" surgical vs interventional decisions; must be treated as a high-priority algorithm.
- **Clinical UX**: Move away from pop-up alerts to passive "Clinical Banners" to reduce alert fatigue.

### 3. Interoperability & Integration

- **FHIR R4**: The base standard for exchange.
- **Cyprus Core Profiles**: Need for localization of FHIR resources (e.g., Cyprus ID/ARC identifiers).
- **HL7 v2**: Still required for majority of private clinical labs in Cyprus; requires an MLLP/v2 parser-to-FHIR mapper.
- **DICOM MWL (Modality Worklist)**: Essential for synchronizing patient data with Echo machines to prevent manual entry errors.
- **DICOM SR (Structured Reporting)**: Essential for importing measurements (LVEF, etc.) directly from machines into EMR forms.

### 4. GHeSY (Gesy) Specifics

- **Adapter Pattern**: Mandatory due to the lack of public API documentation; allows testing with mock providers.
- **e-Prescription**: Workflow must be integrated; prescriptions are legally electronic in Cyprus.

## Current Architecture State

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (App Router)
- **Database**: PostgreSQL + pgvector
- **Cache**: Redis (Session & CDSS caching)
- **Imaging**: Orthanc + OHIF Viewer

### 5. Authentication & Session Security (Phase 4)

- **Redis Blacklisting**: Implemented for immediate token revocation on logout.
- **Session Tracking**: JWTs are linked to a server-side session in `user_sessions` for global logout and security monitoring.
- **Asynchronous Auditing**: Audit logs are written to the database using `asyncio.create_task` to prevent blocking the request pipeline.
- **Graceful Degradation**: The system is designed to fall back to standard JWT validation if Redis becomes temporarily unavailable.

### 6. Development & Dependencies (2026-01-23)

- **Package Updates**: Updated `npm` to 11.8.0 and `frontend` dependencies to latest minor versions.
- **Tailwind CSS v4**: Attempted major upgrade to v4, but it requires significant manual migration of CSS (PostCSS config, imports, and `@layer` usage) and currently conflicts with the Next.js 14 setup. Stayed on v3.4 for stability.
- **Next.js & React**: Stayed on Next.js 14 and React 18 for now to maintain full compatibility with existing components and shadcn/ui-based parts.
- **Assets**: Created a cardiology-themed SVG favicon (`favicon.svg`) at `frontend/public/` featuring a heart with an ECG rhythm line.

### 7. Environment & Deployment Separation (2026-01-23)

- **Override Pattern**: Tunnel/remote testing config is separated from the base `docker-compose.yml` using Docker Compose's `-f` multi-file merging. Base file uses localhost URLs only.
- **Gitignored Files**: `docker-compose.tunnel.yml` (CORS/URL overrides) and `tunnel-config.yml` (Cloudflare tunnel ID + credentials) are excluded from version control.
- **Cloudflare Tunnel**: Routes `openheart-demo.sequencyapp.com` → frontend:3000 and `openheart-api.sequencyapp.com` → backend:8000 for remote testing without port forwarding.

### 8. GDPR & Patient Management (2026-01-23)

- **Right to Erasure (Art 17)**: Implemented full erasure request lifecycle (Pending → Approved → 72h Cool-off → Executed). Execution involves Tier 2 PII anonymization while preserving clinical records under Art 17(3)(c) exemptions.
- **Data Retention**: Automated 15-year retention logic added to `backend/app/core/retention.py`. System tracks last clinical encounter to calculate expiry according to Cyprus Law 125(I)/2018.
- **Bug Fixes**: Resolved critical 500 errors in patient/note creation caused by async lazy loading and invalid INET fallback values. Improved frontend API error reporting to surface Pydantic validation errors.
- **UX Improvements**: Added a searchable patient selector to the appointment form and implemented the Patient Edit page.

### 9. Clinical UX & Real-time Updates (2026-01-23)

- **Timeline Redesign**: Replaced generic 'red' clinical notes (which looked like errors) with a premium indigo palette. Implemented glassmorphism and sidebar accents for a sophisticated, professional medical interface.
- **Real-time Feel**: Configured `react-query` with `staleTime: 5000` and `refetchOnWindowFocus: true` globally. Added `refetchOnMount: 'always'` to critical clinical views to ensure data is always fresh when navigating back/forth.
- **Active Encounter Overlay**: Implemented a global floating component that tracks 'in-progress' encounters. Features a live timer, MRN display, and quick 'Resume'/'End Session' actions. This ensures physicians never lose track of active patient sessions regardless of where they are in the app.
- **Security hardening**: Improved `get_current_user` dependency in the backend to explicitly reject refresh tokens for authenticated requests, closing a potential security gap.

## Key Findings (2026-01-24)

### 10. Prescription Data & Clinical Logic

- **Cyprus Data Sources**: Confirmed `data.gov.cy` (Registered Medicines & Price List) and `gesy.org.cy` (Health Insurance Organisation) as the authoritative sources for the prescription module.
- **ESC 2024 Updates**:
  - **Triple Therapy**: Duration for AF post-PCI (DOAC + 2 antiplatelets) is now recommended for 1-4 weeks maximum (Class I, Level A).
  - **Beta-blockers + Non-DHP CCBs**: Now a Level II B recommendation for angina control, but strictly **contraindicated in Heart Failure** or reduced LVEF.
  - **Ivabradine**: Contraindicated in patients with LVEF >40% without clinical heart failure (ESC 2024 CCS).
  - **Statins + Fibrates**: Gemfibrozil specifically increases rhabdomyolysis risk; Fenofibrate remains the preferred alternative if needed.
- **e-Prescribing**: Legally mandatory via GHS/GeSY since 2019; system must support INN (generic) prescribing and HIO product codes.

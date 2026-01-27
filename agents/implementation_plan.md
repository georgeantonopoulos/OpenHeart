---
title: OpenHeart Cyprus - Cardiology EMR Implementation Plan
version: 1.0
status: planning
created: 2026-01-21
description: >
  Implementation plan for building "OpenHeart Cyprus," a high-performance, 
  open-source EMR tailored for Cypriot cardiologists using Claude Code CLI.
---

# Cardiology EMR Implementation Plan

## 1. Executive Summary

**Goal:** Build "OpenHeart Cyprus," a high-performance, open-source EMR tailored for Cypriot cardiologists.

### Core Differentiators

- **Gesy (GHS) Readiness:** Architecture designed for the General Healthcare System of Cyprus.
- **Cardiology First:** Native DICOM viewing (Echo/Angio) and CDSS (Risk Scoring) out of the box.
- **Agent-Native:** Built entirely using Anthropic's "Claude Code" CLI.

---

## 2. Technology Stack

*Selected for AI-Generation Efficiency*

| Layer           | Technology                 | Rationale                                                               |
| :-------------- | :------------------------- | :---------------------------------------------------------------------- |
| **Frontend**    | Next.js 14+ (App Router)   | React is easy for Claude to generate; excellent ecosystem for medical dashboards |
| **Backend**     | FastAPI (Python)           | Python is mandatory for the CDSS (AI models) and DICOM handling (pydicom) |
| **Database**    | PostgreSQL with pgvector   | For patient data and future AI search capabilities                      |
| **Caching/Session** | Redis                    | Essential for session management, rate limiting, and CDSS result caching |
| **PACS Integration** | Orthanc (Open Source DICOM server) | Lightweight and REST API-friendly                                       |
| **Imaging**     | OHIF Viewer (React-based)  | The gold standard open-source web viewer                                |

---

## 3. Phase 1: The "Claude Code" Setup

**Objective:** Configure the AI agent's environment so it understands the mission.

### 3.1 Initialize Repository

```bash
mkdir openheart-cyprus
cd openheart-cyprus
git init

# Copy the provided CLAUDE.md into this directory
```

### 3.2 Scaffold via Agent

Run `claude` in your terminal and issue this prompt:

> "Read CLAUDE.md. Initialize a monorepo structure. I need a 'frontend' folder with Next.js (TypeScript, Tailwind) and a 'backend' folder with FastAPI (Python 3.11). Create a docker-compose.yml that orchestrates both along with a PostgreSQL container."

---

## 4. Phase 2: Core Architecture & Cyprus Compliance

**Objective:** Build the secure foundation required by EU Law 125(I)/2018.

### 4.1 GDPR & Data Sovereignty

- **Encryption:** Database columns for PII (Patient Identifiable Information) must be encrypted at rest (AES-256).
- **MFA:** Multi-Factor Authentication (TOTP or WebAuthn) is mandatory for all clinical accounts.
- **Audit Logging:** Every view, edit, or data export must be logged to a partitioned audit table.

**Prompt for Claude:**

> "Create a middleware in FastAPI that logs every request to a 'security_audit' table. Ensure it captures User ID, IP address, timestamp, and the resource accessed. This is for GDPR compliance."

### 4.2 Gesy (GHS) Integration Layer

> **Note:** Gesy API documentation often requires provider credentials. We will build a "Mock Adapter" pattern so you can swap in the real API later.

**Prompt for Claude:**

> "Create a Python interface named `IGesyProvider`. It should have methods for `verify_beneficiary(id)`, `submit_claim()`, and `get_referral()`. Then, create a `MockGesyProvider` implementation that returns dummy data for testing."

### 4.3 Patient Demographics (Cypriot Context)

- **Fields:** ARC (Alien Registration Certificate), ID Number, Phone (+357 format)
- **Language:** UI must support i18n (English & Greek)

---

## 5. Phase 3: Cardiology-Specific Modules

*Based on the "Multimodal Data-Driven" paper and "Essential Features" uploads.*

### 5.1 Clinical Decision Support System (CDSS)

We will implement the algorithms mentioned in your uploaded files (GRACE, ASCVD).

- **Implementation:** See `cardio_risk_engine.py` (file provided below)
- **Agent Workflow:** Ask Claude to create the API endpoints that wrap this logic

### 5.2 DICOM & Imaging

**Strategy:** Don't build a viewer from scratch. Integrate OHIF.

**Prompt for Claude:**

> "I need to embed the OHIF Viewer into a React component in the Next.js frontend. The viewer should load a study InstanceUID passed via props. Assume we have an Orthanc server running at `localhost:8042`."

### 5.3 Specialty Templates (The "Cardiologist's Best" Touch)

Instead of generic text boxes, we need structured data for:

| Template        | Key Fields                      |
| :-------------- | :------------------------------ |
| **Echo Reports** | LVEF %, Wall Motion, Valve status |
| **Catheterization** | Access site (Radial/Femoral), Stents placed |

**Prompt for Claude:**

> "Create a 'SOAP' note component specifically for Cardiology. The 'Objective' section should have specific number inputs for BP, HR, and a sub-form for Echocardiogram parameters (LVEF, E/A ratio)."

---

## 6. Phase 4: Execution & Deployment

**Objective:** Go from code to production.

### 6.1 Testing Strategy

| Layer      | Framework                 |
| :--------- | :------------------------ |
| **Backend** | pytest for all risk calculations and API endpoints |
| **Frontend** | Jest and React Testing Library |

**Command:**

```bash
claude "Run the backend tests. If any fail, analyze the error and fix the code."
```

### 6.2 Docker Deployment

Ensure the final deliverable is a self-contained `docker-compose` stack that a doctor's IT admin can spin up easily.

### 6.3 Security Hardening

- **Automated Scanning:** Integrate `bandit` for Python security checks and `snyk` or `npm audit` for frontend dependencies.
- **Penetration Testing:** Issue a prompt to Claude to simulate a security auditor.

**Prompt for Claude:**

> "Analyze the current FastAPI codebase for OWASP Top 10 vulnerabilities. Specifically check for SQL injection in the patient search, insecure session management, and lack of rate limiting on the login endpoint."

---

## 7. Supporting Documentation

The following detailed guides have been prepared to support implementation:

| Document                       | Description                                                     |
| :----------------------------- | :-------------------------------------------------------------- |
| [security_architecture.md](security_architecture.md) | GDPR compliance, PostgreSQL RLS, audit logging, encryption patterns |
| [cdss_algorithms.md](cdss_algorithms.md) | GRACE, CHA₂DS₂-VASc, HAS-BLED, ASCVD algorithms with exact point tables |
| [fhir_interoperability.md](fhir_interoperability.md) | FHIR R4 resources, REST API patterns, Gesy code systems         |
| [dicom_integration.md](dicom_integration.md) | Orthanc setup, DICOMweb API, OHIF Viewer integration            |
| [gesy_integration.md](gesy_integration.md) | Gesy adapter pattern, codification standards, referral workflow |
| [emr_best_practices.md](emr_best_practices.md) | Lessons from OpenMRS/OpenEMR, module architecture, testing patterns |
| [user_management_plan.md](user_management_plan.md) | **CRITICAL** User authentication, registration, RBAC, MFA |

---

## ⚠️ CRITICAL GAP IDENTIFIED (2026-01-22)

**The original plan failed to address how users come into existence in the system.**

This is a fundamental oversight - the plan assumed authentication exists without defining:

- User registration/onboarding workflow
- Admin user management
- Password reset flow
- MFA setup
- Role assignment
- Developer testing access

**Resolution:** See [user_management_plan.md](user_management_plan.md) for comprehensive coverage.

---

## Progress Tracking

- [x] Phase 1: Repository Setup ✅ Complete
  - [x] Monorepo structure (frontend/backend)
  - [x] Docker Compose orchestration
  - [x] Database, Redis, MinIO, Orthanc configured
- [x] Phase 2: Core Architecture (Partial)
  - [x] GDPR audit middleware
  - [x] PII encryption module
  - [x] RBAC skeleton (permissions.py)
  - [ ] **User Management** ← BLOCKED - see user_management_plan.md
  - [ ] Gesy Integration (Mock adapter)
- [x] Phase 3: Cardiology Modules (Partial)
  - [x] CDSS: GRACE Score (40+ tests)
  - [x] CDSS: CHA₂DS₂-VASc
  - [x] CDSS: HAS-BLED
  - [x] Clinical Notes module
  - [ ] DICOM/OHIF integration
  - [ ] Specialty templates
- [ ] Phase 4: Deployment & Testing
  - [x] Docker Compose working
  - [ ] Production hardening
  - [ ] Security audit

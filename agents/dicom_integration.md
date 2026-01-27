---
title: DICOM & PACS Integration Guide
version: 1.0
status: planning
created: 2026-01-21
description: DICOM integration patterns using Orthanc DICOM server and OHIF Viewer for OpenHeart Cyprus EMR.
---

# DICOM & PACS Integration Guide

## 1. Overview

OpenHeart Cyprus integrates with DICOM imaging (echocardiograms, angiograms, cardiac CT/MRI) using:

- **Orthanc**: Lightweight open-source DICOM server with REST API
- **OHIF Viewer**: React-based web viewer for medical imaging
- **DICOMweb**: RESTful API standard (WADO-RS, STOW-RS, QIDO-RS)
- **Modality Worklist (MWL)**: For automated patient data synchronization with Echo/Cath machines

## 2. Architecture

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Echo Machine  │────▶│  Orthanc DICOM  │◀────│   CT Scanner    │
│   (DICOM Push)  │     │     Server      │     │   (DICOM Push)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │ DICOMweb API
                                 ▼
                        ┌─────────────────┐
                        │   FastAPI       │
                        │   Backend       │
                        └────────┬────────┘
                                 │
                                 │ REST API
                                 ▼
                        ┌─────────────────┐
                        │   Next.js       │
                        │   Frontend      │
                        │   + OHIF Viewer │
                        └─────────────────┘
```

## 3. Docker Compose Configuration

```yaml
# docker-compose.yml
services:
  orthanc:
    image: orthancteam/orthanc:24.1.0
    container_name: openheart-orthanc
    ports:
      - "4242:4242"   # DICOM port
      - "8042:8042"   # HTTP API
    environment:
      - ORTHANC__DICOM_AET=OPENHEART
      - ORTHANC__DICOM_PORT=4242
      - ORTHANC__REGISTERED_USERS={"admin": "orthanc-secure-password"}
      - ORTHANC__AUTHENTICATION_ENABLED=true
      - ORTHANC__DICOM_WEB__ENABLE=true
      - ORTHANC__DICOM_WEB__ROOT=/dicom-web/
      - ORTHANC__CORS_ENABLED=true
      - ORTHANC__CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
    volumes:
      - orthanc-data:/var/lib/orthanc/db
    networks:
      - openheart-network

volumes:
  orthanc-data:

networks:
  openheart-network:
    driver: bridge
```

## 4. Orthanc REST API Reference

### List Studies

```bash
# Get all studies
GET http://localhost:8042/studies

# Response
[
  "e6b67c8a-4b3d5e1f-9a2c8d7b-3f1e4a6c-8d9b2e5f",
  "a1b2c3d4-e5f6g7h8-i9j0k1l2-m3n4o5p6-q7r8s9t0"
]
```

### Get Study Details

```bash
GET http://localhost:8042/studies/{study-id}

# Response
{
  "ID": "e6b67c8a-...",
  "MainDicomTags": {
    "StudyDate": "20260121",
    "StudyDescription": "ECHOCARDIOGRAM",
    "PatientID": "CY12345678",
    "PatientName": "PAPADOPOULOS^NIKOS"
  },
  "Series": ["series-uuid-1", "series-uuid-2"]
}
```

### DICOMweb QIDO-RS (Query Studies)

```bash
# Search studies by patient ID
GET http://localhost:8042/dicom-web/studies?PatientID=CY12345678

# Search by date range
GET http://localhost:8042/dicom-web/studies?StudyDate=20260101-20260121

# Search by modality
GET http://localhost:8042/dicom-web/studies?ModalitiesInStudy=US  # Ultrasound (Echo)
GET http://localhost:8042/dicom-web/studies?ModalitiesInStudy=XA  # Angiography
```

### DICOMweb WADO-RS (Retrieve)

```bash
# Get study metadata
GET http://localhost:8042/dicom-web/studies/{study-uid}/metadata

# Get series
GET http://localhost:8042/dicom-web/studies/{study-uid}/series

### Get instance (image)
```bash
GET http://localhost:8042/dicom-web/studies/{study-uid}/series/{series-uid}/instances/{instance-uid}
```

---

## 5. Modality Worklist (MWL) Setup

To prevent manual data entry errors on Echo/Cath machines, OpenHeart provides a DICOM Modality Worklist.

**Workflow:**

1. Patient is scheduled in Next.js frontend.
2. FastAPI creates a `.wl` file or inserts into Orthanc's Worklist database.
3. Echo machine queries Orthanc via C-FIND and sees the patient list.

**Orthanc Worklist Plugin Config:**

```json
{
  "Worklists" : {
    "Enable": true,
    "Database": "/var/lib/orthanc/db/worklists"
  }
}
```

```

## 5. FastAPI DICOM Service

```python
# services/dicom_service.py
import httpx
from typing import List, Optional
from pydantic import BaseModel

class DicomStudy(BaseModel):
    study_instance_uid: str
    study_date: str
    study_description: Optional[str]
    patient_id: str
    patient_name: str
    modality: str
    series_count: int

class DicomService:
    def __init__(self, orthanc_url: str, username: str, password: str):
        self.orthanc_url = orthanc_url
        self.auth = (username, password)

    async def search_studies(
        self,
        patient_id: Optional[str] = None,
        study_date: Optional[str] = None,
        modality: Optional[str] = None
    ) -> List[DicomStudy]:
        """Query studies using DICOMweb QIDO-RS."""

        params = {}
        if patient_id:
            params["PatientID"] = patient_id
        if study_date:
            params["StudyDate"] = study_date
        if modality:
            params["ModalitiesInStudy"] = modality

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.orthanc_url}/dicom-web/studies",
                params=params,
                auth=self.auth,
                headers={"Accept": "application/dicom+json"}
            )
            response.raise_for_status()

            studies = []
            for item in response.json():
                studies.append(self._parse_study(item))
            return studies

    async def get_study_metadata(self, study_uid: str) -> dict:
        """Get detailed metadata for a study."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.orthanc_url}/dicom-web/studies/{study_uid}/metadata",
                auth=self.auth,
                headers={"Accept": "application/dicom+json"}
            )
            response.raise_for_status()
            return response.json()

    async def get_wado_url(self, study_uid: str) -> str:
        """Generate WADO-RS URL for OHIF Viewer."""
        return f"{self.orthanc_url}/dicom-web/studies/{study_uid}"

    def _parse_study(self, dicom_json: dict) -> DicomStudy:
        """Parse DICOM JSON to study model."""
        return DicomStudy(
            study_instance_uid=dicom_json.get("0020000D", {}).get("Value", [""])[0],
            study_date=dicom_json.get("00080020", {}).get("Value", [""])[0],
            study_description=dicom_json.get("00081030", {}).get("Value", [""])[0],
            patient_id=dicom_json.get("00100020", {}).get("Value", [""])[0],
            patient_name=dicom_json.get("00100010", {}).get("Value", [{}])[0].get("Alphabetic", ""),
            modality=dicom_json.get("00080060", {}).get("Value", [""])[0],
            series_count=len(dicom_json.get("series", []))
        )
```

### FastAPI DICOM Endpoints

```python
# api/dicom/router.py
from fastapi import APIRouter, Depends, Query
from services.dicom_service import DicomService

dicom_router = APIRouter(prefix="/api/dicom", tags=["DICOM"])

@dicom_router.get("/studies")
async def list_studies(
    patient_id: str = Query(None, description="Patient ID (Cyprus ID or ARC)"),
    study_date: str = Query(None, description="Study date (YYYYMMDD or range)"),
    modality: str = Query(None, description="US=Echo, XA=Angio, CT, MR"),
    dicom_service: DicomService = Depends(get_dicom_service)
):
    """List DICOM studies with optional filters."""
    return await dicom_service.search_studies(
        patient_id=patient_id,
        study_date=study_date,
        modality=modality
    )

@dicom_router.get("/studies/{study_uid}/viewer-url")
async def get_viewer_url(
    study_uid: str,
    dicom_service: DicomService = Depends(get_dicom_service)
):
    """Get URL to open study in OHIF Viewer."""
    wado_url = await dicom_service.get_wado_url(study_uid)
    return {
        "viewer_url": f"/viewer?StudyInstanceUIDs={study_uid}",
        "wado_url": wado_url
    }
```

## 6. OHIF Viewer Integration (Next.js)

### Installation

```bash
npm install @ohif/viewer
```

### Configuration

```typescript
// config/ohif.ts
export const ohifConfig = {
  routerBasename: '/viewer',
  showStudyList: false,
  dataSources: [
    {
      namespace: '@ohif/extension-default.dataSourcesModule.dicomweb',
      sourceName: 'orthanc',
      configuration: {
        friendlyName: 'Orthanc Server',
        name: 'orthanc',
        wadoUriRoot: process.env.NEXT_PUBLIC_ORTHANC_URL + '/wado',
        qidoRoot: process.env.NEXT_PUBLIC_ORTHANC_URL + '/dicom-web',
        wadoRoot: process.env.NEXT_PUBLIC_ORTHANC_URL + '/dicom-web',
        qidoSupportsIncludeField: false,
        imageRendering: 'wadors',
        thumbnailRendering: 'wadors',
        enableStudyLazyLoad: true,
        supportsFuzzyMatching: false,
        supportsWildcard: true,
      },
    },
  ],
  defaultDataSourceName: 'orthanc',
};
```

### React Component (iframe approach for isolation)

```tsx
// components/DicomViewer.tsx
import { useEffect, useRef } from 'react';

interface DicomViewerProps {
  studyInstanceUID: string;
}

export function DicomViewer({ studyInstanceUID }: DicomViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const viewerUrl = `/ohif/viewer?StudyInstanceUIDs=${studyInstanceUID}`;

  return (
    <div className="w-full h-[800px] border rounded-lg overflow-hidden">
      <iframe
        ref={iframeRef}
        src={viewerUrl}
        className="w-full h-full"
        title="DICOM Viewer"
        allow="fullscreen"
      />
    </div>
  );
}
```

### Direct React Integration (advanced)

```tsx
// components/EmbeddedOHIF.tsx
import { useEffect, useRef } from 'react';
import { App as OHIFApp } from '@ohif/viewer';
import { ohifConfig } from '@/config/ohif';

interface EmbeddedOHIFProps {
  studyInstanceUID: string;
}

export function EmbeddedOHIF({ studyInstanceUID }: EmbeddedOHIFProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      // Initialize OHIF in the container
      const config = {
        ...ohifConfig,
        // Override for specific study
        routerBasename: '/',
      };

      // Note: This approach may have React version conflicts
      // Consider iframe approach for production
    }
  }, [studyInstanceUID]);

  return (
    <div
      ref={containerRef}
      id="ohif-container"
      className="w-full h-[800px]"
    />
  );
}
```

## 7. Patient Study List Component

```tsx
// components/PatientStudyList.tsx
import { useState, useEffect } from 'react';
import { DicomViewer } from './DicomViewer';

interface Study {
  study_instance_uid: string;
  study_date: string;
  study_description: string;
  modality: string;
}

interface PatientStudyListProps {
  patientId: string;
}

export function PatientStudyList({ patientId }: PatientStudyListProps) {
  const [studies, setStudies] = useState<Study[]>([]);
  const [selectedStudy, setSelectedStudy] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/dicom/studies?patient_id=${patientId}`)
      .then(res => res.json())
      .then(setStudies);
  }, [patientId]);

  const formatDate = (dicomDate: string) => {
    // Convert YYYYMMDD to DD/MM/YYYY (Cyprus format)
    if (dicomDate.length === 8) {
      return `${dicomDate.slice(6, 8)}/${dicomDate.slice(4, 6)}/${dicomDate.slice(0, 4)}`;
    }
    return dicomDate;
  };

  const getModalityLabel = (modality: string) => {
    const labels: Record<string, string> = {
      'US': 'Echocardiogram',
      'XA': 'Angiography',
      'CT': 'CT Scan',
      'MR': 'MRI',
    };
    return labels[modality] || modality;
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Imaging Studies</h3>

      <div className="grid gap-2">
        {studies.map(study => (
          <button
            key={study.study_instance_uid}
            onClick={() => setSelectedStudy(study.study_instance_uid)}
            className={`p-3 text-left border rounded-lg hover:bg-gray-50 ${
              selectedStudy === study.study_instance_uid ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            <div className="flex justify-between">
              <span className="font-medium">{getModalityLabel(study.modality)}</span>
              <span className="text-gray-500">{formatDate(study.study_date)}</span>
            </div>
            <div className="text-sm text-gray-600">{study.study_description}</div>
          </button>
        ))}
      </div>

      {selectedStudy && (
        <DicomViewer studyInstanceUID={selectedStudy} />
      )}
    </div>
  );
}
```

## 8. Cardiology-Specific Modalities

| Modality Code | Description | Common Use |
|---------------|-------------|------------|
| US | Ultrasound | Transthoracic Echo (TTE), TEE |
| XA | X-Ray Angiography | Coronary Angiography, PCI |
| CT | Computed Tomography | Coronary CT Angiography |
| MR | Magnetic Resonance | Cardiac MRI |
| NM | Nuclear Medicine | SPECT, PET |
| ECG | Electrocardiogram | 12-lead ECG (if DICOM) |

## 9. DICOM Tags for Cardiology

| Tag | Name | Example |
|-----|------|---------|
| (0008,0060) | Modality | US |
| (0008,1030) | Study Description | ECHOCARDIOGRAM |
| (0010,0020) | Patient ID | CY12345678 |
| (0020,000D) | Study Instance UID | 1.2.840... |
| (0018,0010) | Contrast/Bolus Agent | (for angio) |
| (0018,1020) | Software Versions | GE EchoPAC |
| (0028,0010) | Rows | 480 |
| (0028,0011) | Columns | 640 |

## 11. Advanced Cardiology Features

### 11.1 Cine-Loop Optimization

Cardiology studies (Echo/Angio) contain high-frame-rate cine loops.

- **WADO-RS Streaming**: Use `multipart/related; type="application/dicom"` to stream frames without loading the entire file.
- **Client-side Caching**: Ensure browser cache is configured for large DICOM binaries.

### 11.2 Structured Reporting (SR) Import

Many Echo machines (GE, Philips) export measurements (LVEF, Valve areas) as DICOM SR.

- **Auto-populate**: OpenHeart should parse `(0040,A730) Content Sequence` to automatically fill EMR forms.
- **Workflow**: Doctor clicks "Import from Echo", system parses latest SR for that patient.

## 12. Security Considerations

1. **Authentication**: Always enable Orthanc authentication in production
2. **CORS**: Restrict to specific frontend origins
3. **Proxy**: Route DICOM requests through FastAPI to add authorization
4. **Audit**: Log all study access to security_audit table
5. **Encryption**: Use HTTPS for all DICOMweb communications

```python
# middleware/dicom_audit.py
async def audit_dicom_access(study_uid: str, user_id: int, action: str):
    """Log DICOM study access for compliance."""
    await insert_audit_log({
        "action": action,
        "resource_type": "dicom_study",
        "resource_id": study_uid,
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    })
```

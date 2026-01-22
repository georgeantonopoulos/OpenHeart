"""
DICOM Service for OpenHeart Cyprus.

Provides DICOMweb client for Orthanc PACS server integration.
Uses QIDO-RS for queries and WADO-RS for retrieving images/metadata.

Reference: https://www.dicomstandard.org/using/dicomweb
"""

import logging
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

import httpx

from app.config import settings
from app.integrations.dicom.schemas import (
    DicomInstance,
    DicomPatient,
    DicomSeries,
    DicomStudy,
    DicomStudyList,
    EchoMeasurements,
    Modality,
    StudySearchRequest,
    StudyStatus,
    ViewerUrlResponse,
)

logger = logging.getLogger(__name__)

# DICOM tag constants for parsing
DICOM_TAGS = {
    "StudyInstanceUID": "0020000D",
    "SeriesInstanceUID": "0020000E",
    "SOPInstanceUID": "00080018",
    "StudyDate": "00080020",
    "StudyTime": "00080030",
    "StudyDescription": "00081030",
    "AccessionNumber": "00080050",
    "Modality": "00080060",
    "PatientID": "00100020",
    "PatientName": "00100010",
    "PatientBirthDate": "00100030",
    "PatientSex": "00100040",
    "ReferringPhysicianName": "00080090",
    "InstitutionName": "00080080",
    "SeriesDescription": "0008103E",
    "SeriesNumber": "00200011",
    "BodyPartExamined": "00180015",
    "InstanceNumber": "00200013",
    "NumberOfFrames": "00280008",
    "Rows": "00280010",
    "Columns": "00280011",
    "SOPClassUID": "00080016",
    "TransferSyntaxUID": "00020010",
    "NumberOfStudyRelatedSeries": "00201206",
    "NumberOfStudyRelatedInstances": "00201208",
}


def get_tag_value(data: dict, tag_name: str, default=None):
    """
    Extract value from DICOM JSON format.

    DICOM JSON format: {"00100010": {"vr": "PN", "Value": [{"Alphabetic": "DOE^JOHN"}]}}
    """
    tag = DICOM_TAGS.get(tag_name, tag_name)
    tag_data = data.get(tag, {})
    values = tag_data.get("Value", [])
    if not values:
        return default

    value = values[0]

    # Handle different value representations
    if isinstance(value, dict):
        # PersonName has Alphabetic component
        if "Alphabetic" in value:
            return value["Alphabetic"]
        return str(value)
    return value


def parse_dicom_date(date_str: Optional[str]) -> Optional[date]:
    """Parse DICOM date format (YYYYMMDD) to Python date."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        return None


class DicomService:
    """
    DICOMweb client for Orthanc PACS server.

    Provides methods to query, retrieve, and manage DICOM studies.
    Uses async httpx for non-blocking HTTP requests.
    """

    def __init__(self):
        """Initialize DICOM service with Orthanc configuration."""
        self.orthanc_url = getattr(settings, "orthanc_url", "http://orthanc:8042")
        self.orthanc_username = getattr(settings, "orthanc_username", "orthanc")
        self.orthanc_password = getattr(settings, "orthanc_password", "orthanc")
        self.ohif_url = getattr(settings, "ohif_url", "http://localhost:3001")
        self.dicomweb_url = f"{self.orthanc_url}/dicom-web"

    def _get_auth(self) -> tuple[str, str]:
        """Get Basic Auth credentials for Orthanc."""
        return (self.orthanc_username, self.orthanc_password)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        accept: str = "application/dicom+json",
    ) -> dict | list:
        """
        Make HTTP request to Orthanc DICOMweb API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (relative to DICOMweb root)
            params: Query parameters
            json_data: JSON body for POST requests
            accept: Accept header value

        Returns:
            Parsed JSON response

        Raises:
            httpx.HTTPError: On connection or HTTP errors
        """
        url = f"{self.dicomweb_url}/{path.lstrip('/')}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                auth=self._get_auth(),
                headers={"Accept": accept},
            )
            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

    async def search_studies(
        self,
        request: StudySearchRequest,
    ) -> DicomStudyList:
        """
        Search for DICOM studies using QIDO-RS.

        Args:
            request: Search parameters

        Returns:
            Paginated list of matching studies
        """
        # Build QIDO-RS query parameters
        params = {
            "limit": request.per_page,
            "offset": (request.page - 1) * request.per_page,
            # Request these fields in response
            "includefield": ",".join([
                "00080020",  # StudyDate
                "00080030",  # StudyTime
                "00081030",  # StudyDescription
                "00080050",  # AccessionNumber
                "00080060",  # ModalitiesInStudy
                "00100010",  # PatientName
                "00100020",  # PatientID
                "00100030",  # PatientBirthDate
                "00100040",  # PatientSex
                "00080090",  # ReferringPhysician
                "00080080",  # InstitutionName
                "00201206",  # NumberOfStudyRelatedSeries
                "00201208",  # NumberOfStudyRelatedInstances
            ]),
        }

        # Add search filters
        if request.patient_id:
            params["PatientID"] = request.patient_id
        if request.patient_name:
            params["PatientName"] = f"*{request.patient_name}*"
        if request.accession_number:
            params["AccessionNumber"] = request.accession_number
        if request.study_description:
            params["StudyDescription"] = f"*{request.study_description}*"
        if request.modality:
            params["ModalitiesInStudy"] = request.modality.value

        # Date range filter (DICOM format: YYYYMMDD-YYYYMMDD)
        if request.study_date_from or request.study_date_to:
            date_from = request.study_date_from.strftime("%Y%m%d") if request.study_date_from else ""
            date_to = request.study_date_to.strftime("%Y%m%d") if request.study_date_to else ""
            params["StudyDate"] = f"{date_from}-{date_to}"

        try:
            results = await self._request("GET", "/studies", params=params)
        except httpx.HTTPError as e:
            logger.error(f"DICOM search failed: {e}")
            return DicomStudyList(
                studies=[],
                total=0,
                page=request.page,
                per_page=request.per_page,
            )

        # Parse results
        studies = []
        for study_data in results:
            study = self._parse_study(study_data)
            if study:
                studies.append(study)

        # Note: QIDO-RS doesn't always return total count
        # In production, you might need a separate count query
        total = len(studies) if len(studies) < request.per_page else request.page * request.per_page + 1

        return DicomStudyList(
            studies=studies,
            total=total,
            page=request.page,
            per_page=request.per_page,
        )

    def _parse_study(self, data: dict) -> Optional[DicomStudy]:
        """Parse DICOM JSON study response into DicomStudy model."""
        study_uid = get_tag_value(data, "StudyInstanceUID")
        if not study_uid:
            return None

        # Parse modalities (may be a list)
        modalities_raw = data.get(DICOM_TAGS["Modality"], {}).get("Value", [])
        modalities = []
        for mod in modalities_raw:
            try:
                modalities.append(Modality(mod))
            except ValueError:
                pass

        # Parse patient info
        patient = DicomPatient(
            patient_id=get_tag_value(data, "PatientID", ""),
            patient_name=get_tag_value(data, "PatientName", "Unknown"),
            birth_date=parse_dicom_date(get_tag_value(data, "PatientBirthDate")),
            sex=get_tag_value(data, "PatientSex"),
        )

        return DicomStudy(
            study_instance_uid=study_uid,
            study_id=get_tag_value(data, "StudyID"),
            accession_number=get_tag_value(data, "AccessionNumber"),
            study_date=parse_dicom_date(get_tag_value(data, "StudyDate")),
            study_time=get_tag_value(data, "StudyTime"),
            study_description=get_tag_value(data, "StudyDescription"),
            referring_physician=get_tag_value(data, "ReferringPhysicianName"),
            institution_name=get_tag_value(data, "InstitutionName"),
            patient=patient,
            modalities=modalities,
            series_count=int(get_tag_value(data, "NumberOfStudyRelatedSeries", 0) or 0),
            status=StudyStatus.NEW,
        )

    async def get_study(self, study_uid: str) -> Optional[DicomStudy]:
        """
        Get detailed study metadata including series.

        Args:
            study_uid: Study Instance UID

        Returns:
            DicomStudy with series details, or None if not found
        """
        try:
            # Get study metadata
            studies = await self._request(
                "GET",
                f"/studies/{study_uid}/metadata",
            )

            if not studies:
                return None

            # Get study-level info
            study_results = await self._request(
                "GET",
                "/studies",
                params={"StudyInstanceUID": study_uid},
            )

            if not study_results:
                return None

            study = self._parse_study(study_results[0])
            if not study:
                return None

            # Get series for this study
            series_results = await self._request(
                "GET",
                f"/studies/{study_uid}/series",
            )

            for series_data in series_results:
                series = self._parse_series(series_data)
                if series:
                    study.series.append(series)

            return study

        except httpx.HTTPError as e:
            logger.error(f"Failed to get study {study_uid}: {e}")
            return None

    def _parse_series(self, data: dict) -> Optional[DicomSeries]:
        """Parse DICOM JSON series response."""
        series_uid = get_tag_value(data, "SeriesInstanceUID")
        if not series_uid:
            return None

        modality_str = get_tag_value(data, "Modality", "OT")
        try:
            modality = Modality(modality_str)
        except ValueError:
            modality = Modality.SR  # Default to SR for unknown

        return DicomSeries(
            series_instance_uid=series_uid,
            series_number=int(get_tag_value(data, "SeriesNumber", 0) or 0),
            series_description=get_tag_value(data, "SeriesDescription"),
            modality=modality,
            body_part=get_tag_value(data, "BodyPartExamined"),
            instance_count=0,  # Would need separate query
        )

    async def get_viewer_url(self, study_uid: str) -> ViewerUrlResponse:
        """
        Generate OHIF Viewer URL for a study.

        The OHIF viewer is configured to use DICOMweb to fetch images
        from Orthanc.

        Args:
            study_uid: Study Instance UID

        Returns:
            ViewerUrlResponse with OHIF viewer URL
        """
        # OHIF viewer URL format with StudyInstanceUID
        viewer_url = f"{self.ohif_url}/viewer?StudyInstanceUIDs={study_uid}"

        return ViewerUrlResponse(
            viewer_url=viewer_url,
            study_instance_uid=study_uid,
        )

    async def get_study_thumbnail(self, study_uid: str) -> Optional[bytes]:
        """
        Get thumbnail image for study preview.

        Args:
            study_uid: Study Instance UID

        Returns:
            JPEG thumbnail bytes or None
        """
        try:
            # Get first series
            series_results = await self._request(
                "GET",
                f"/studies/{study_uid}/series",
            )

            if not series_results:
                return None

            series_uid = get_tag_value(series_results[0], "SeriesInstanceUID")
            if not series_uid:
                return None

            # Get thumbnail via WADO-RS
            url = f"{self.dicomweb_url}/studies/{study_uid}/series/{series_uid}/thumbnail"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    auth=self._get_auth(),
                    headers={"Accept": "image/jpeg"},
                )
                response.raise_for_status()
                return response.content

        except httpx.HTTPError as e:
            logger.warning(f"Failed to get thumbnail for {study_uid}: {e}")
            return None

    async def get_echo_measurements(self, study_uid: str) -> Optional[EchoMeasurements]:
        """
        Extract Echo measurements from DICOM Structured Report.

        Parses DICOM SR (Structured Report) to extract quantitative
        measurements following the TID 5100 template.

        Args:
            study_uid: Study Instance UID

        Returns:
            EchoMeasurements if SR found, None otherwise
        """
        try:
            # Find SR series in the study
            series_results = await self._request(
                "GET",
                f"/studies/{study_uid}/series",
            )

            sr_series = None
            for series_data in series_results:
                modality = get_tag_value(series_data, "Modality")
                if modality == "SR":
                    sr_series = get_tag_value(series_data, "SeriesInstanceUID")
                    break

            if not sr_series:
                logger.info(f"No SR series found for study {study_uid}")
                return None

            # Get SR instances
            instances = await self._request(
                "GET",
                f"/studies/{study_uid}/series/{sr_series}/instances",
            )

            if not instances:
                return None

            # Get first SR content
            instance_uid = get_tag_value(instances[0], "SOPInstanceUID")
            metadata = await self._request(
                "GET",
                f"/studies/{study_uid}/series/{sr_series}/instances/{instance_uid}/metadata",
            )

            # Parse SR content (simplified - real implementation would parse
            # the full SR document tree using pydicom)
            # This is a placeholder for the complex SR parsing logic
            return EchoMeasurements(
                study_instance_uid=study_uid,
                findings="SR parsing not yet implemented",
            )

        except httpx.HTTPError as e:
            logger.error(f"Failed to get echo measurements for {study_uid}: {e}")
            return None

    async def store_instance(self, dicom_data: bytes) -> Optional[str]:
        """
        Store a DICOM instance via STOW-RS.

        Args:
            dicom_data: Raw DICOM P10 file bytes

        Returns:
            SOPInstanceUID if successful, None otherwise
        """
        try:
            url = f"{self.dicomweb_url}/studies"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    content=dicom_data,
                    auth=self._get_auth(),
                    headers={
                        "Content-Type": "application/dicom",
                        "Accept": "application/dicom+json",
                    },
                )
                response.raise_for_status()
                # Parse response for stored instance UID
                result = response.json()
                return result.get("00081199", {}).get("Value", [{}])[0].get("00081155", {}).get("Value", [None])[0]

        except httpx.HTTPError as e:
            logger.error(f"Failed to store DICOM instance: {e}")
            return None

    async def delete_study(self, study_uid: str) -> bool:
        """
        Delete a study from Orthanc.

        Note: This uses Orthanc REST API, not DICOMweb (which doesn't support DELETE).

        Args:
            study_uid: Study Instance UID

        Returns:
            True if deleted successfully
        """
        try:
            # Orthanc uses its own resource IDs, need to look up first
            url = f"{self.orthanc_url}/tools/lookup"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    data=study_uid,
                    auth=self._get_auth(),
                )
                response.raise_for_status()
                resources = response.json()

                if not resources:
                    return False

                # Delete by Orthanc ID
                orthanc_id = resources[0]["ID"]
                delete_response = await client.delete(
                    f"{self.orthanc_url}/studies/{orthanc_id}",
                    auth=self._get_auth(),
                )
                delete_response.raise_for_status()
                return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to delete study {study_uid}: {e}")
            return False

    async def check_connection(self) -> bool:
        """
        Check connectivity to Orthanc server.

        Returns:
            True if Orthanc is reachable
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.orthanc_url}/system",
                    auth=self._get_auth(),
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError:
            return False

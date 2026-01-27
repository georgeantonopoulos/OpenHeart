# OpenHeart Cyprus - TODO List

This list contains bugs and missing functionalities identified during initial testing of the OpenHeart Cardiology EMR.

## 🔴 High Priority: Critical Bugs

- [ ] **Fix 401 Unauthorized API Errors:**
  - `GET /api/patients/search` returns 401 even when logged in.
  - `GET /api/appointments` returns 401 even when logged in.
  - *Likely Cause:* NextAuth session token is not being correctly attached to API requests in `frontend/src/lib/api/` clients.
- [ ] **Fix "Patient Not Found" on Profile Page:**
  - Navigating from Dashboard to a patient profile (e.g., `/patients/103`) results in "Patient Not Found".
  - *Investigation:* Verify mapping between Dashboard's mock/partial data and the Profile page's API call.
- [ ] **Fix 404 Missing Routes:**
  - `/imaging` -> Not Found
  - `/procedures` -> Not Found
  - `/referrals/incoming` -> Not Found
  - `/billing/claims` -> Not Found
  - `/procedures/schedule` (Quick Action) -> Not Found

## 🟡 Medium Priority: Functional Gaps

- [ ] **Implement Auth Missing Features:**
  - [ ] Asychronous insertion into `security_audit` table in `AuthService`.
  - [ ] Email sending for password reset links.
  - [ ] Session invalidation on password reset.
  - [ ] Token blacklisting in Redis upon logout.
- [ ] **Connect Dashboard to Real Data:**
  - [ ] `RecentPatients.tsx` currently uses mock/local data.
  - [ ] `QuickStats.tsx` currently uses mock data.
  - [ ] `TodayAppointments.tsx` currently uses mock data.
- [ ] **Finish DICOM/Imaging Integration:**
  - [ ] Ensure Orthanc connectivity is stable (logs showed platform mismatch warnings).
  - [ ] Verify OHIF viewer mapping to patient studies.

## 🟢 Low Priority: UI/UX & Polish

- [ ] **Optimize Initial Load Time:**
  - Login page has a 5-7 second "Loading..." delay before showing the form.
  - Root page also stays on "Loading..." for a long time.
- [ ] **Implement Command Palette:**
  - Dashboard has a shortcut (CMD+K) button that is currently a TODO.
- [ ] **Audit MFA Verification:**
  - Token return logic for `mfa_verified=True` in `auth/router.py` is marked as TODO.

---
*Created on 2026-01-22 following initial Docker deployment.*

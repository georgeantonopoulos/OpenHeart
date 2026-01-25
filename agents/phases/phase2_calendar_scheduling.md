# Phase 2: Enhanced Calendar & Scheduling UI

## Priority: HIGH | Dependencies: None | Can Run in Parallel with Phase 1

---

## Executive Summary

The backend appointment system is **substantially complete** with conflict detection, check-in workflows, encounter handover, and available slot finding. The frontend has functional week/day views. This phase focuses on UX enhancements that make the calendar usable for daily practice: month view, recurring appointments, working hours configuration, drag-and-drop rescheduling, and patient reminders.

---

## Existing Infrastructure (Comprehensive)

### Backend - Fully Implemented
| Feature | Location | Status |
|---------|----------|--------|
| Appointment CRUD | `backend/app/modules/appointment/router.py` | Complete |
| 8 appointment types | `models.py` | consultation, follow_up, echo, stress_test, holter, procedure, ecg, pre_op |
| 7 status states | `models.py` | scheduled, confirmed, checked_in, in_progress, completed, cancelled, no_show |
| Conflict detection | `service.py` | Provider double-booking prevention |
| Available slots | `service.py` | Gap-finding in 07:00-21:00 window |
| Duration warnings | `service.py` | Warns if slot < 75% of expected duration |
| Check-in workflow | `router.py` | `POST /appointments/{id}/check-in` |
| Encounter handover | `router.py` | `POST /appointments/{id}/start-encounter` |
| Appointment update | `router.py` | `PUT /appointments/{id}` with re-conflict check |
| Cancellation | `router.py` | `DELETE /appointments/{id}` with reason |
| Patient name decrypt | `service.py` | Batch PII decryption for display |
| Gesy referral link | `models.py` | `gesy_referral_id` field |
| Clinic-level RLS | `models.py` | Row-level security by clinic_id |

### Backend - Encounter Integration
| Feature | Location | Status |
|---------|----------|--------|
| Encounter lifecycle | `backend/app/modules/encounter/` | Complete |
| Vitals recording | `encounter/router.py` | `POST /encounters/{id}/vitals` |
| Today's encounters | `encounter/router.py` | `GET /encounters/today` |
| Discharge/diagnoses | `encounter/service.py` | On encounter completion |
| Active encounter overlay | `frontend/src/components/ActiveEncounterOverlay.tsx` | Complete - live timer, end session |

### Frontend - Calendar Views
| Feature | Location | Status |
|---------|----------|--------|
| Week view | `frontend/src/components/calendar/WeekView.tsx` | Complete - 7-day × 15-hour grid |
| Day view | `frontend/src/components/calendar/DayView.tsx` | Complete - hourly detail |
| View toggle | `frontend/src/app/appointments/page.tsx` | Week/Day switch |
| Date navigation | Same | Previous/Next/Today buttons |
| Status color coding | `frontend/src/lib/api/appointments.ts` | 7 status colors |
| Quick actions | WeekView + DayView | Check-in, Start Session on hover |
| Create appointment | `frontend/src/app/appointments/new/page.tsx` | 3-step wizard |
| Conflict display | Same | Real-time conflict checking during creation |
| Duration warnings | Same | Visual warning for undersized slots |
| Dashboard widget | `frontend/src/app/dashboard/components/TodayAppointments.tsx` | Today's schedule |
| Patient timeline | `frontend/src/app/patients/[id]/components/Timeline.tsx` | Shows encounters |
| API client | `frontend/src/lib/api/appointments.ts` | Complete with all helpers |

### Modality Worklist (Imaging Procedures)
| Feature | Location | Status |
|---------|----------|--------|
| Schedule procedures | `frontend/src/app/procedures/schedule/page.tsx` | Complete - 3-step wizard |
| Worklist view | `frontend/src/app/procedures/worklist/page.tsx` | Complete - grouped by status |
| Station config | `backend/app/integrations/dicom/mwl_models.py` | WorklistStation model |
| DICOM MWL | `backend/app/integrations/dicom/mwl_router.py` | Full MWL support |

---

## What's Missing (Implementation Required)

### 1. Month Calendar View

**`frontend/src/components/calendar/MonthView.tsx`**

```typescript
// Grid: 7 columns (Mon-Sun) × 5-6 rows
// Each cell shows:
//   - Day number (current month regular, adjacent months muted)
//   - Appointment count badge
//   - Up to 3 appointment previews (time + type)
//   - "+N more" overflow link
//   - Color-coded dots for status distribution
// Click on day → switches to DayView for that date
// Today cell highlighted with border
```

**Backend requirement:** None - existing `GET /appointments` with date range filter is sufficient.

### 2. Recurring Appointments

#### Backend: New Endpoint

**`POST /api/appointments/recurring`**

```python
class RecurringAppointmentCreate(BaseModel):
    patient_id: int
    provider_id: Optional[int] = None  # Default: current user
    start_date: date
    start_time: time  # HH:MM
    duration_minutes: int = 30
    appointment_type: AppointmentType
    reason: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    # Recurrence pattern
    recurrence_type: str  # weekly, biweekly, monthly, custom
    day_of_week: Optional[int] = None  # 0=Mon, 6=Sun (for weekly/biweekly)
    day_of_month: Optional[int] = None  # 1-28 (for monthly)
    custom_interval_days: Optional[int] = None  # For custom

    occurrences: int  # Max appointments to create (cap at 52)
    skip_conflicts: bool = False  # Skip slots with conflicts vs. fail
```

**Response:**
```python
class RecurringAppointmentResponse(BaseModel):
    recurrence_group_id: UUID
    created_count: int
    skipped_count: int  # Slots skipped due to conflicts
    skipped_dates: list[date]
    appointments: list[AppointmentResponse]
```

#### Database Changes

**Add to appointments table (migration `0009` or separate):**
```sql
ALTER TABLE appointments ADD COLUMN recurrence_group_id UUID;
ALTER TABLE appointments ADD COLUMN recurrence_index INTEGER; -- 1, 2, 3... in series
CREATE INDEX idx_appointments_recurrence ON appointments(recurrence_group_id);
```

**New endpoints:**
```python
GET  /api/appointments/recurring/{group_id}     # List all in series
DELETE /api/appointments/recurring/{group_id}    # Cancel remaining in series
PUT  /api/appointments/recurring/{group_id}      # Reschedule remaining
```

#### Frontend: Recurring UI

**In appointment creation wizard, add Step 2.5: Recurrence**
- Toggle: "Make recurring" checkbox
- Pattern: Weekly / Biweekly / Monthly / Custom interval
- End condition: Number of occurrences (1-52)
- Preview: Show generated dates with conflict indicators
- Option: "Skip conflicting dates" vs. "Fail if any conflict"

### 3. Working Hours Configuration

#### Backend: Clinic/Provider Settings

**New table (migration):**
```sql
CREATE TABLE provider_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id INTEGER NOT NULL REFERENCES users(id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    day_of_week INTEGER NOT NULL, -- 0=Monday, 6=Sunday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    slot_duration_minutes INTEGER NOT NULL DEFAULT 30,
    break_start TIME,
    break_end TIME,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_until DATE, -- NULL = indefinite
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider_id, clinic_id, day_of_week, effective_from)
);

CREATE TABLE clinic_closures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    closure_date DATE NOT NULL,
    reason VARCHAR(200), -- "Public Holiday", "Renovation", etc.
    is_recurring_annual BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(clinic_id, closure_date)
);
```

**Endpoints:**
```python
GET    /api/schedules/provider/{id}              # Get provider's weekly schedule
PUT    /api/schedules/provider/{id}              # Update schedule
GET    /api/schedules/clinic/{id}/closures       # List closures
POST   /api/schedules/clinic/{id}/closures       # Add closure
DELETE /api/schedules/clinic/{id}/closures/{id}  # Remove closure
```

**Impact on available slots:** Modify `get_available_slots()` to use provider_schedules instead of hardcoded 07:00-21:00.

#### Frontend: Schedule Configuration

**`frontend/src/app/settings/schedules/page.tsx`** (Admin/Clinic Admin only)
- Weekly grid editor: drag to set available hours per day
- Break time configuration
- Slot duration default per provider
- Closure calendar: add/remove clinic closure dates
- Cyprus public holidays pre-loaded

### 4. Drag-and-Drop Rescheduling

**WeekView/DayView enhancement:**
- Install `@dnd-kit/core` and `@dnd-kit/sortable`
- Appointment cards become draggable
- Drop zones on time slots
- On drop: call `PUT /appointments/{id}` with new time
- Show conflict warning if drop target has existing appointment
- Undo notification (5-second toast with "Undo" button)

### 5. No-Show Tracking & Analytics

#### Backend Enhancements

**Add to patient model or create patient_metrics table:**
```sql
-- Denormalized counter on patients table
ALTER TABLE patients ADD COLUMN no_show_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE patients ADD COLUMN last_no_show_date DATE;
```

**Update no-show endpoint to increment counter:**
```python
# In appointment service, when marking no-show:
patient.no_show_count += 1
patient.last_no_show_date = appointment.start_time.date()
```

**New analytics endpoint:**
```python
GET /api/appointments/analytics?from=&to=  # Returns:
{
    "total_appointments": int,
    "completed": int,
    "no_shows": int,
    "cancellations": int,
    "no_show_rate": float,  # percentage
    "avg_duration_minutes": float,
    "busiest_day": str,  # "Monday"
    "busiest_hour": int,  # 10 (for 10:00)
}
```

#### Frontend: No-Show Indicator
- Show no-show count badge on patient card in booking flow
- Warning message: "This patient has X no-shows in the last 6 months"
- No-show rate in appointment analytics dashboard

### 6. Appointment Confirmation Workflow

#### Backend: Confirmation Status

**Extend status enum or add confirmation field:**
```python
# Add to appointment model:
confirmation_sent_at: Optional[datetime]
confirmation_method: Optional[str]  # sms, email, phone
confirmed_at: Optional[datetime]
reminder_sent_at: Optional[datetime]
```

**Endpoints:**
```python
POST /api/appointments/{id}/send-confirmation   # Trigger confirmation
POST /api/appointments/{id}/confirm             # Patient confirms (via link)
POST /api/appointments/{id}/send-reminder       # Trigger reminder
```

#### Frontend: Confirmation UI
- "Send Confirmation" button on appointment detail
- Confirmation status indicator on calendar cards
- Bulk confirmation send for next day's appointments

### 7. Appointment Templates

#### Backend

**New table:**
```sql
CREATE TABLE appointment_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    name VARCHAR(100) NOT NULL,
    appointment_type VARCHAR(30) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    default_location VARCHAR(100),
    preparation_instructions TEXT, -- "NPO 12h before", "Bring prior ECGs"
    follow_up_template_id UUID REFERENCES appointment_templates(id), -- Chain templates
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Endpoints:**
```python
GET    /api/appointment-templates          # List active templates
POST   /api/appointment-templates          # Create template (Admin)
PUT    /api/appointment-templates/{id}     # Update
DELETE /api/appointment-templates/{id}     # Deactivate
```

#### Frontend: Template Integration
- Template picker in appointment creation wizard
- Auto-fills type, duration, location, and preparation instructions
- "Create from existing appointment" quick-template action

---

## Cross-Cutting Gaps Identified

| Gap | Impact on Phase 2 | Addressed In |
|-----|-------------------|-------------|
| No SMS/email service | Can't send reminders or confirmations | Infrastructure |
| No background job scheduler | Can't schedule reminder sends | Infrastructure |
| User management endpoints missing | Can't configure provider schedules | Pre-existing gap |
| No patient portal | Patients can't self-confirm or self-schedule | Future |
| No notification system | Can't push real-time updates to calendar | Infrastructure |
| No WebSocket support | Calendar doesn't live-update when colleagues book | Infrastructure |
| Prescription not linked to appointments | Can't see "medication review" appointment type | Phase 1 |
| No waiting room queue | After check-in, no visible queue order | Future enhancement |
| No multi-provider view | Can't see all providers side-by-side in day view | Enhancement |

---

## Implementation Order

1. Month view (frontend only, no backend changes)
2. Recurring appointments (backend endpoint + frontend UI)
3. Working hours configuration (backend table + settings page)
4. Update available slots to use working hours
5. Drag-and-drop rescheduling (frontend enhancement)
6. No-show tracking (backend counter + frontend indicator)
7. Appointment templates (backend + frontend)
8. Confirmation workflow (backend + frontend, requires SMS service)

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/calendar/MonthView.tsx` | CREATE | Month calendar grid |
| `frontend/src/app/appointments/page.tsx` | MODIFY | Add month view toggle |
| `backend/app/modules/appointment/schemas.py` | MODIFY | Add recurring schemas |
| `backend/app/modules/appointment/service.py` | MODIFY | Add recurring logic, working hours |
| `backend/app/modules/appointment/router.py` | MODIFY | Add recurring endpoints |
| `backend/alembic/versions/0009b_schedules.py` | CREATE | Provider schedules + closures tables |
| `frontend/src/app/settings/schedules/page.tsx` | CREATE | Schedule configuration |
| `frontend/src/components/calendar/WeekView.tsx` | MODIFY | Add drag-drop |
| `frontend/src/components/calendar/DayView.tsx` | MODIFY | Add drag-drop |
| `frontend/src/app/appointments/new/page.tsx` | MODIFY | Add recurrence step |
| `backend/app/modules/appointment/models.py` | MODIFY | Add recurrence fields |
| `frontend/src/lib/api/appointments.ts` | MODIFY | Add recurring + schedule APIs |
| `backend/app/modules/appointment/templates.py` | CREATE | Template model + service |

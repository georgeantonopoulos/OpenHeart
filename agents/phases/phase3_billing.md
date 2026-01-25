# Phase 3: Revenue Cycle Management (Billing Backend)

## Priority: HIGH | Dependencies: Encounter system (exists), Gesy adapter (exists) | Can Start in Parallel with Phase 1-2

---

## Executive Summary

The frontend billing UI at `/billing/claims` already exists with a claims console, rejection resolution panel, and status filtering. The Gesy integration backend is complete with a mock provider implementing the full `IGesyProvider` interface (beneficiary verification, referrals, claims). What's missing is the **internal billing engine**: invoice generation, payment recording, financial reporting, and wiring the frontend to real APIs.

---

## Existing Infrastructure (Comprehensive)

### Backend - Gesy Integration (Complete)
| Feature | Location | Status |
|---------|----------|--------|
| IGesyProvider interface | `backend/app/integrations/gesy/interface.py` | Abstract base - 10 methods |
| MockGesyProvider | `backend/app/integrations/gesy/mock_provider.py` | Full implementation with test data |
| Gesy router | `backend/app/integrations/gesy/router.py` | 11 endpoints |
| Gesy schemas | `backend/app/integrations/gesy/schemas.py` | BeneficiaryStatus, GesyReferral, GesyClaim, GesyClaimLineItem |
| Beneficiary verification | Router + mock | By Gesy ID or Cyprus ID card |
| Referral management | Router + mock | Create, get, close, list |
| Claims submission | Router + mock | Submit, get status, list |
| Code validation | Router + mock | ICD-10 and CPT validation |
| Specialties list | Router + mock | Cardiology-specific specialty codes |

### Backend - Medical Coding (Complete)
| Feature | Location | Status |
|---------|----------|--------|
| ICD-10 codes | `backend/app/modules/coding/` | 86 cardiac diagnosis codes seeded |
| CPT codes | Same | 60+ cardiology procedures seeded |
| HIO service codes | Same | 20+ with base_price_eur |
| Search APIs | `coding/router.py` | All code types searchable |
| Greek text support | `coding/service.py` | PostgreSQL unaccent extension |

### Backend - Encounter Billing Fields
| Feature | Location | Status |
|---------|----------|--------|
| billing_status field | `encounter/models.py` | ENUM: pending, submitted, approved, rejected, paid |
| gesy_claim_id field | `encounter/models.py` | VARCHAR, nullable |
| gesy_referral_id field | `encounter/models.py` | VARCHAR, nullable |

### Frontend - Billing UI (Exists, Needs Wiring)
| Feature | Location | Status |
|---------|----------|--------|
| Claims console | `frontend/src/app/billing/claims/page.tsx` | Complete UI - dark theme |
| Status filtering | Same | draft/submitted/under_review/approved/rejected/paid |
| Statistics cards | Same | Total Claimed/Approved/Pending/Rejected |
| Claims list | Same | Claim ID, status, service date, amounts |
| Rejection panel | Same | Reason, line items with approval status, Fix & Resubmit |
| Referrals incoming | `frontend/src/app/referrals/incoming/page.tsx` | List + filter |
| Referral details | `frontend/src/app/referrals/[id]/page.tsx` | Full detail + create claim link |
| Dashboard quick actions | `frontend/src/app/dashboard/components/QuickActions.tsx` | Claims + Referrals buttons |
| Gesy API client | `frontend/src/lib/api/gesy.ts` | All Gesy functions |
| Coding API client | `frontend/src/lib/api/coding.ts` | Code search functions |

### Permissions (Already Defined)
```python
BILLING_READ = "billing:read"          # Cardiologist, Receptionist, Billing Staff
BILLING_WRITE = "billing:write"        # Cardiologist, Billing Staff
GESY_CLAIM_READ = "gesy:claim:read"    # Cardiologist, Billing Staff
GESY_CLAIM_WRITE = "gesy:claim:write"  # Cardiologist, Billing Staff
```

---

## What's Missing (Implementation Required)

### 1. Database Migration: `0010_billing.py`

**Location:** `backend/alembic/versions/20240110_0010_billing.py`

#### Table: `invoices`
```sql
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(encounter_id),

    -- Invoice identification
    invoice_number VARCHAR(20) NOT NULL UNIQUE,
        -- Format: OH-YYYY-NNNNN (auto-generated sequence per clinic per year)

    -- Dates
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL, -- Default: issue_date + 30 days

    -- Financial
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5,4) NOT NULL DEFAULT 0, -- Cyprus: 0% for medical services
    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_reason VARCHAR(200),
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    amount_paid DECIMAL(10,2) NOT NULL DEFAULT 0,
    balance DECIMAL(10,2) GENERATED ALWAYS AS (total_amount - amount_paid) STORED,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
        -- draft, issued, partially_paid, paid, overdue, cancelled, written_off

    -- Payment info
    payment_method VARCHAR(30), -- cash, card, bank_transfer, gesy, insurance, mixed

    -- Gesy linkage
    gesy_claim_id VARCHAR(50), -- Links to GesyClaim
    is_gesy_covered BOOLEAN NOT NULL DEFAULT FALSE,
    gesy_coverage_amount DECIMAL(10,2) DEFAULT 0, -- Amount covered by Gesy
    patient_copay DECIMAL(10,2) DEFAULT 0, -- Patient's share

    -- Provider info
    provider_id INTEGER REFERENCES users(id), -- Treating physician

    -- Notes
    notes TEXT,
    internal_notes TEXT, -- Staff-only notes

    -- Audit
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancelled_by INTEGER REFERENCES users(id),
    cancellation_reason TEXT
);

CREATE INDEX idx_invoices_patient ON invoices(patient_id, issue_date DESC);
CREATE INDEX idx_invoices_status ON invoices(status) WHERE status NOT IN ('cancelled', 'written_off');
CREATE INDEX idx_invoices_clinic_date ON invoices(clinic_id, issue_date DESC);
CREATE INDEX idx_invoices_due ON invoices(due_date) WHERE status IN ('issued', 'partially_paid');
CREATE INDEX idx_invoices_gesy ON invoices(gesy_claim_id) WHERE gesy_claim_id IS NOT NULL;
CREATE INDEX idx_invoices_number ON invoices(invoice_number);

-- Invoice number sequence per clinic
CREATE SEQUENCE invoice_number_seq START 1;
```

#### Table: `invoice_line_items`
```sql
CREATE TABLE invoice_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,

    -- Service identification
    description VARCHAR(500) NOT NULL,
    cpt_code VARCHAR(10),                            -- CPT procedure code
    hio_service_code VARCHAR(20),                    -- Cyprus HIO code
    icd10_codes JSONB DEFAULT '[]',                  -- Linked diagnosis codes

    -- Financial
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL, -- quantity * unit_price * (1 - discount_percent/100)

    -- Gesy
    is_gesy_covered BOOLEAN NOT NULL DEFAULT FALSE,
    gesy_approved_amount DECIMAL(10,2), -- Amount Gesy approved (may differ from claimed)
    gesy_rejection_reason VARCHAR(500),

    -- Ordering
    line_number INTEGER NOT NULL DEFAULT 1,

    -- Metadata
    service_date DATE, -- Date service was rendered (may differ from invoice date)
    performing_provider_id INTEGER REFERENCES users(id),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_line_items_invoice ON invoice_line_items(invoice_id, line_number);
```

#### Table: `payments`
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    clinic_id INTEGER NOT NULL REFERENCES clinics(id),

    -- Payment details
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    payment_method VARCHAR(30) NOT NULL,
        -- cash, credit_card, debit_card, bank_transfer, gesy_reimbursement, cheque

    -- Reference
    reference_number VARCHAR(100), -- Card receipt, bank ref, cheque number
    transaction_id VARCHAR(100),   -- POS terminal transaction ID

    -- Gesy-specific
    is_gesy_payment BOOLEAN NOT NULL DEFAULT FALSE,
    gesy_payment_reference VARCHAR(50),

    -- Notes
    notes TEXT,

    -- Receipt
    receipt_number VARCHAR(20), -- Auto-generated: RCP-YYYY-NNNNN

    -- Audit
    recorded_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    voided_at TIMESTAMP WITH TIME ZONE,
    voided_by INTEGER REFERENCES users(id),
    void_reason TEXT
);

CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_patient ON payments(patient_id, payment_date DESC);
CREATE INDEX idx_payments_clinic_date ON payments(clinic_id, payment_date DESC);
CREATE INDEX idx_payments_method ON payments(payment_method, payment_date);
```

### 2. Backend Module: `backend/app/modules/billing/`

#### File Structure
```
backend/app/modules/billing/
    __init__.py
    models.py           - SQLAlchemy ORM models (Invoice, LineItem, Payment)
    schemas.py          - Pydantic schemas
    service.py          - Invoice generation, payment recording, status management
    router.py           - API endpoints
    invoice_generator.py - Auto-generate invoice from encounter
    reports.py          - Financial reporting queries
```

#### `service.py` - Key Business Logic

```python
class BillingService:
    async def generate_invoice_from_encounter(self, encounter_id: UUID, user: User) -> InvoiceResponse:
        """
        1. Get encounter with services rendered
        2. Look up HIO service codes and prices
        3. Check if patient is Gesy beneficiary
        4. Create invoice with line items
        5. If Gesy: split into covered vs. copay amounts
        6. Generate invoice_number (OH-{year}-{sequence})
        7. Set due_date (issue_date + 30 days)
        8. Return created invoice
        """

    async def create_manual_invoice(self, data: InvoiceCreate, user: User) -> InvoiceResponse:
        """Create invoice without encounter link (for ad-hoc billing)"""

    async def add_line_item(self, invoice_id: UUID, item: LineItemCreate, user: User):
        """Add line item to draft invoice, recalculate totals"""

    async def remove_line_item(self, invoice_id: UUID, item_id: UUID, user: User):
        """Remove line item, recalculate totals"""

    async def issue_invoice(self, invoice_id: UUID, user: User):
        """Transition draft → issued (validates completeness)"""

    async def record_payment(self, invoice_id: UUID, payment: PaymentCreate, user: User):
        """
        1. Validate payment amount <= balance
        2. Create payment record
        3. Update invoice.amount_paid
        4. If fully paid: status → 'paid'
        5. If partially paid: status → 'partially_paid'
        6. Generate receipt_number
        """

    async def void_payment(self, payment_id: UUID, reason: str, user: User):
        """Reverse a payment (e.g., bounced cheque), recalculate invoice"""

    async def submit_gesy_claim(self, invoice_id: UUID, user: User):
        """
        1. Validate invoice has Gesy beneficiary
        2. Validate encounter has referral
        3. Build GesyClaimCreate from invoice line items
        4. Call gesy_provider.submit_claim()
        5. Store claim_id on invoice
        6. Update encounter.billing_status = 'submitted'
        """

    async def sync_gesy_claim_status(self, invoice_id: UUID):
        """Poll Gesy for claim status updates, update invoice accordingly"""

    async def cancel_invoice(self, invoice_id: UUID, reason: str, user: User):
        """Cancel invoice with reason (must be draft or issued, not paid)"""

    async def write_off_invoice(self, invoice_id: UUID, reason: str, user: User):
        """Write off unpaid balance (requires BILLING_WRITE)"""

    async def check_overdue_invoices(self):
        """Background task: Mark invoices past due_date as 'overdue'"""
```

#### `reports.py` - Financial Reporting

```python
class BillingReports:
    async def get_dashboard(self, clinic_id: int, period: str) -> BillingDashboard:
        """
        Returns:
        - revenue_today / this_week / this_month
        - outstanding_balance (total unpaid)
        - pending_gesy_claims (count + amount)
        - payment_breakdown_by_method (pie chart data)
        - appointments_billed_vs_unbilled (today)
        """

    async def get_aging_report(self, clinic_id: int) -> AgingReport:
        """
        Overdue invoices grouped by age:
        - Current (not yet due)
        - 1-30 days overdue
        - 31-60 days overdue
        - 61-90 days overdue
        - 90+ days overdue
        Each bucket: count, total amount, list of invoices
        """

    async def get_revenue_report(self, clinic_id: int, from_date: date, to_date: date) -> RevenueReport:
        """
        - Total revenue by day/week/month
        - Revenue by service type (CPT code grouping)
        - Revenue by provider
        - Gesy vs. private pay breakdown
        - Average invoice amount
        - Collection rate (paid / total issued)
        """

    async def get_gesy_claims_report(self, clinic_id: int) -> GesyClaimsReport:
        """
        - Claims by status (submitted/approved/rejected/paid)
        - Rejection rate and common rejection reasons
        - Average time to payment
        - Total claimed vs. approved amounts
        """
```

#### `router.py` - API Endpoints

```python
# Invoice Management
POST   /api/billing/invoices                        # Create manual invoice
POST   /api/billing/invoices/from-encounter/{id}    # Generate from encounter
GET    /api/billing/invoices                        # List with filters
GET    /api/billing/invoices/{id}                   # Invoice detail
PUT    /api/billing/invoices/{id}                   # Update draft invoice
POST   /api/billing/invoices/{id}/issue             # Issue invoice
POST   /api/billing/invoices/{id}/cancel            # Cancel with reason
POST   /api/billing/invoices/{id}/write-off         # Write off balance

# Line Items
POST   /api/billing/invoices/{id}/items             # Add line item
PUT    /api/billing/invoices/{id}/items/{item_id}   # Update line item
DELETE /api/billing/invoices/{id}/items/{item_id}   # Remove line item

# Payments
POST   /api/billing/invoices/{id}/payments          # Record payment
GET    /api/billing/invoices/{id}/payments          # List payments for invoice
POST   /api/billing/payments/{id}/void              # Void payment

# Gesy Claims
POST   /api/billing/invoices/{id}/submit-gesy       # Submit to Gesy
GET    /api/billing/invoices/{id}/gesy-status       # Check Gesy status

# Reports
GET    /api/billing/dashboard                       # Revenue dashboard
GET    /api/billing/reports/aging                   # Aging report
GET    /api/billing/reports/revenue                 # Revenue report (date range)
GET    /api/billing/reports/gesy-claims             # Gesy claims report

# Patient Billing
GET    /api/patients/{id}/invoices                  # Patient's invoices
GET    /api/patients/{id}/balance                   # Outstanding balance
```

### 3. Frontend Implementation

#### Wire Existing Claims UI

**`frontend/src/app/billing/claims/page.tsx`** - Modifications needed:
- Replace mock/static data with real API calls to `/api/billing/invoices`
- Wire status filter to query parameters
- Wire statistics cards to dashboard API
- Wire rejection panel to real claim details
- Add "Create Invoice" button linking to invoice creation flow

#### New Pages

**`frontend/src/app/billing/invoices/page.tsx`** - Invoice List
- List all invoices with filters (status, date range, patient, provider)
- Search by invoice number
- Quick stats: Total, Paid, Outstanding, Overdue
- Each row: invoice #, patient name, date, amount, status badge, actions

**`frontend/src/app/billing/invoices/new/page.tsx`** - Create Invoice
- Patient search/select
- Optional encounter link
- Line item builder:
  - Search CPT/HIO codes (auto-fills description and price)
  - Manual entry option
  - Quantity, unit price, discount
  - Link ICD-10 diagnosis codes
- Subtotal/tax/total calculation
- Gesy coverage estimation (if beneficiary)
- Save as draft or issue immediately

**`frontend/src/app/billing/invoices/[id]/page.tsx`** - Invoice Detail
- Full invoice information with line items
- Payment history
- Actions: Issue, Record Payment, Submit to Gesy, Cancel, Print
- Status timeline (draft → issued → paid)
- Gesy claim status (if submitted)

**`frontend/src/app/billing/dashboard/page.tsx`** - Billing Dashboard
- Revenue cards: Today, This Week, This Month
- Outstanding balance card
- Charts:
  - Revenue trend (line chart, last 30 days)
  - Payment method breakdown (pie chart)
  - Gesy vs. Private (stacked bar)
- Aging report summary (bar chart)
- Recent activity (latest payments, invoices, claim updates)

**`frontend/src/app/billing/reports/page.tsx`** - Reports Hub
- Aging report table
- Revenue report with date range picker
- Gesy claims analysis
- Export to CSV/PDF

#### New Components

**`frontend/src/components/billing/InvoiceForm.tsx`**
- Line item editor (add/remove/edit)
- CPT/HIO code search integration
- Totals calculation
- Gesy coverage preview

**`frontend/src/components/billing/PaymentModal.tsx`**
- Payment amount (default: full balance)
- Payment method selector
- Reference number input
- Date picker
- Receipt preview

**`frontend/src/components/billing/InvoicePrint.tsx`**
- Cyprus-standard invoice format
- Clinic details, patient info, line items
- Payment terms, bank details
- VAT exemption note (medical services)
- Print/PDF export

**`frontend/src/components/billing/RevenueChart.tsx`**
- Line chart using Recharts (already installed)
- Daily/weekly/monthly aggregation toggle
- Comparison with previous period

#### API Client

**`frontend/src/lib/api/billing.ts`**
```typescript
// Invoices
createInvoice(token, data)
createInvoiceFromEncounter(token, encounterId)
listInvoices(token, filters?)
getInvoice(token, invoiceId)
updateInvoice(token, invoiceId, data)
issueInvoice(token, invoiceId)
cancelInvoice(token, invoiceId, reason)

// Line Items
addLineItem(token, invoiceId, item)
updateLineItem(token, invoiceId, itemId, data)
removeLineItem(token, invoiceId, itemId)

// Payments
recordPayment(token, invoiceId, payment)
listPayments(token, invoiceId)
voidPayment(token, paymentId, reason)

// Gesy
submitGesyClaim(token, invoiceId)
getGesyClaimStatus(token, invoiceId)

// Reports
getBillingDashboard(token)
getAgingReport(token)
getRevenueReport(token, from, to)
getGesyClaimsReport(token)

// Patient
getPatientInvoices(token, patientId)
getPatientBalance(token, patientId)

// Helpers
formatCurrency(amount) → "€123.45"
getInvoiceStatusColor(status)
formatInvoiceStatus(status)
```

### 4. Encounter → Invoice Flow

**Integration with existing encounter completion:**

When an encounter is completed (`POST /encounters/{id}/complete`), add option to auto-generate invoice:

```python
# In encounter completion flow:
class EncounterComplete(BaseModel):
    # ... existing fields ...
    generate_invoice: bool = False  # New field

# If generate_invoice is True:
# 1. Determine services from appointment_type + procedures performed
# 2. Look up HIO prices
# 3. Create invoice with line items
# 4. If patient is Gesy beneficiary with valid referral:
#    - Mark as gesy_covered
#    - Calculate copay vs coverage
# 5. Return invoice_id in response
```

### 5. Gesy Claim Lifecycle (Complete Workflow)

```
Encounter Complete
      │
      ▼
Invoice Generated (auto or manual)
      │ status: 'draft'
      ▼
Invoice Reviewed & Issued
      │ status: 'issued'
      ▼
[Is Gesy Beneficiary with Referral?]
      │
      ├── YES ──► Submit Gesy Claim
      │            │ invoice.gesy_claim_id = claim_id
      │            │ encounter.billing_status = 'submitted'
      │            ▼
      │          [Gesy Reviews]
      │            │
      │            ├── Approved ──► Mark items approved
      │            │                 Update gesy_coverage_amount
      │            │                 Wait for Gesy payment
      │            │                 │
      │            │                 ▼
      │            │              Gesy Pays ──► Record payment (is_gesy_payment=true)
      │            │                            Remaining balance = patient copay
      │            │                            Patient pays copay ──► Invoice paid
      │            │
      │            ├── Partially Approved ──► Show rejected line items
      │            │                          Option: Fix & Resubmit
      │            │                          Or: Invoice patient for rejected portion
      │            │
      │            └── Rejected ──► Show rejection reason
      │                             Option: Appeal (resubmit with notes)
      │                             Or: Convert to private invoice
      │
      └── NO ───► Patient pays full amount
                   Record payment ──► Invoice paid
```

---

## Cross-Cutting Gaps Identified

| Gap | Impact on Phase 3 | Addressed In |
|-----|-------------------|-------------|
| No prescription module | Can't bill for dispensed medications | Phase 1 |
| No lab results storage | Can't bill for lab orders | Phase 4 |
| Real Gesy API not connected | Claims use mock provider | Phase 6 |
| No PDF generation library | Can't export invoices as PDF | Infrastructure |
| No email service | Can't email invoices to patients | Infrastructure |
| No patient portal | Patients can't view/pay invoices online | Future |
| Encounter services not structured | No way to auto-determine what services were rendered | Enhancement |
| No POS terminal integration | Card payments manual entry only | Hardware |
| No accounting export | Can't export to accounting software (SAP, etc.) | Future |
| User management incomplete | Can't verify billing staff credentials | Pre-existing |

---

## Testing

**`backend/tests/test_billing.py`:**
- Invoice generation from encounter (with and without Gesy)
- Line item CRUD and total recalculation
- Payment recording (full, partial, overpay rejection)
- Payment voiding and balance recalculation
- Invoice status transitions (valid and invalid)
- Gesy claim submission flow
- Aging report calculation
- Revenue dashboard aggregation
- Permission enforcement (Nurse can't create invoices)
- Invoice number sequence uniqueness
- Currency rounding (EUR cents)

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/alembic/versions/20240110_0010_billing.py` | CREATE | Billing tables migration |
| `backend/app/modules/billing/__init__.py` | CREATE | Module init |
| `backend/app/modules/billing/models.py` | CREATE | Invoice, LineItem, Payment models |
| `backend/app/modules/billing/schemas.py` | CREATE | Pydantic schemas |
| `backend/app/modules/billing/service.py` | CREATE | Business logic |
| `backend/app/modules/billing/router.py` | CREATE | API endpoints |
| `backend/app/modules/billing/invoice_generator.py` | CREATE | Encounter → Invoice logic |
| `backend/app/modules/billing/reports.py` | CREATE | Financial reporting |
| `backend/app/main.py` | MODIFY | Register billing_router |
| `frontend/src/app/billing/claims/page.tsx` | MODIFY | Wire to real APIs |
| `frontend/src/app/billing/invoices/page.tsx` | CREATE | Invoice list |
| `frontend/src/app/billing/invoices/new/page.tsx` | CREATE | Create invoice |
| `frontend/src/app/billing/invoices/[id]/page.tsx` | CREATE | Invoice detail |
| `frontend/src/app/billing/dashboard/page.tsx` | CREATE | Revenue dashboard |
| `frontend/src/app/billing/reports/page.tsx` | CREATE | Reports hub |
| `frontend/src/components/billing/InvoiceForm.tsx` | CREATE | Line item editor |
| `frontend/src/components/billing/PaymentModal.tsx` | CREATE | Payment recording |
| `frontend/src/components/billing/InvoicePrint.tsx` | CREATE | Print format |
| `frontend/src/components/billing/RevenueChart.tsx` | CREATE | Revenue charts |
| `frontend/src/lib/api/billing.ts` | CREATE | Billing API client |
| `backend/app/modules/encounter/service.py` | MODIFY | Add invoice generation on complete |
| `backend/app/modules/encounter/schemas.py` | MODIFY | Add generate_invoice field |
| `backend/tests/test_billing.py` | CREATE | Test suite |

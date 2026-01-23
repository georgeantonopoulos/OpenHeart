/**
 * Auth API client for OpenHeart Cyprus.
 *
 * Handles authentication, MFA, password reset, and invitation operations.
 */

// TODO: This was incorrectly using NEXT_PUBLIC_API_URL directly, which doesn't include /api.
// The fallback included /api but the env var (http://localhost:8000) did not, causing 404s on MFA/auth endpoints.
const API_BASE = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api`;

// =============================================================================
// Types
// =============================================================================

export interface UserInfo {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  clinic_id: number;
  clinic_name: string;
}

export interface InvitationDetails {
  valid: boolean;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  clinic_name: string;
  title?: string;
  specialty?: string;
  message?: string;
  expires_at: string;
}

export interface InvitationCreateData {
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  clinic_id: number;
  title?: string;
  specialty?: string;
  license_number?: string;
  message?: string;
}

export interface InvitationResponse {
  invitation_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  clinic_id: number;
  clinic_name: string;
  status: string;
  invited_by_name?: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string;
}

export interface InvitationListResponse {
  invitations: InvitationResponse[];
  total: number;
  page: number;
  per_page: number;
}

export interface InvitationAcceptData {
  password: string;
  confirm_password: string;
  gdpr_consent: boolean;
  terms_accepted: boolean;
}

export interface MFASetupResponse {
  secret: string;
  provisioning_uri: string;
}

export interface MFAEnableResponse {
  enabled: boolean;
  backup_codes: string[];
  message: string;
}

export interface MFAStatusResponse {
  enabled: boolean;
  backup_codes_remaining: number;
  has_secret: boolean;
}

export interface PasswordStrength {
  score: number;
  strength: 'weak' | 'moderate' | 'strong';
  feedback: string[];
  meets_requirements: boolean;
}

// =============================================================================
// Invitation API (Admin)
// =============================================================================

export async function createInvitation(
  token: string,
  data: InvitationCreateData
): Promise<InvitationResponse> {
  const res = await fetch(`${API_BASE}/auth/admin/users/invite`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to create invitation');
  }

  return res.json();
}

export async function listInvitations(
  token: string,
  params?: {
    clinic_id?: number;
    status?: string;
    page?: number;
    per_page?: number;
  }
): Promise<InvitationListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.clinic_id) searchParams.set('clinic_id', params.clinic_id.toString());
  if (params?.status) searchParams.set('invitation_status', params.status);
  if (params?.page) searchParams.set('page', params.page.toString());
  if (params?.per_page) searchParams.set('per_page', params.per_page.toString());

  const res = await fetch(`${API_BASE}/auth/admin/invitations?${searchParams}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to list invitations');
  }

  return res.json();
}

export async function revokeInvitation(token: string, invitationId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/admin/invitations/${invitationId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to revoke invitation');
  }
}

// =============================================================================
// Invitation API (Public)
// =============================================================================

export async function validateInvitation(inviteToken: string): Promise<InvitationDetails> {
  const res = await fetch(`${API_BASE}/auth/invitations/${inviteToken}`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Invalid or expired invitation');
  }

  return res.json();
}

export async function acceptInvitation(
  inviteToken: string,
  data: InvitationAcceptData
): Promise<UserInfo> {
  const res = await fetch(`${API_BASE}/auth/invitations/${inviteToken}/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to accept invitation');
  }

  return res.json();
}

// =============================================================================
// MFA API
// =============================================================================

export async function setupMFA(token: string): Promise<MFASetupResponse> {
  const res = await fetch(`${API_BASE}/auth/me/mfa/setup`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to setup MFA');
  }

  return res.json();
}

export async function verifyAndEnableMFA(token: string, code: string): Promise<MFAEnableResponse> {
  const res = await fetch(`${API_BASE}/auth/me/mfa/verify?code=${encodeURIComponent(code)}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Invalid verification code');
  }

  return res.json();
}

export async function getMFAStatus(token: string): Promise<MFAStatusResponse> {
  const res = await fetch(`${API_BASE}/auth/me/mfa/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to get MFA status');
  }

  return res.json();
}

export async function disableMFA(token: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/me/mfa?password=${encodeURIComponent(password)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to disable MFA');
  }
}

export async function regenerateBackupCodes(token: string, code: string): Promise<string[]> {
  const res = await fetch(`${API_BASE}/auth/me/mfa/backup-codes?code=${encodeURIComponent(code)}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to regenerate backup codes');
  }

  const data = await res.json();
  return data.backup_codes;
}

// =============================================================================
// Password Reset API
// =============================================================================

export async function requestPasswordReset(email: string): Promise<void> {
  const res = await fetch(
    `${API_BASE}/auth/auth/password/reset-request?email=${encodeURIComponent(email)}`,
    { method: 'POST' }
  );

  // Always succeeds to prevent email enumeration
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to request password reset');
  }
}

export async function validateResetToken(
  resetToken: string
): Promise<{ valid: boolean; email: string; expires_at: string }> {
  const res = await fetch(`${API_BASE}/auth/auth/password/reset/${resetToken}`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Invalid or expired reset token');
  }

  return res.json();
}

export async function resetPassword(resetToken: string, newPassword: string): Promise<void> {
  const params = new URLSearchParams();
  params.set('token', resetToken);
  params.set('new_password', newPassword);

  const res = await fetch(`${API_BASE}/auth/auth/password/reset?${params}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to reset password');
  }
}

export async function changePassword(
  token: string,
  currentPassword: string,
  newPassword: string
): Promise<void> {
  const params = new URLSearchParams();
  params.set('current_password', currentPassword);
  params.set('new_password', newPassword);

  const res = await fetch(`${API_BASE}/auth/me/password?${params}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to change password');
  }
}

// =============================================================================
// Password Strength Checker (Client-side)
// =============================================================================

export function checkPasswordStrength(password: string): PasswordStrength {
  let score = 0;
  const feedback: string[] = [];

  // Length check
  if (password.length >= 12) {
    score += 1;
  } else {
    feedback.push('Use at least 12 characters');
  }

  if (password.length >= 16) {
    score += 1;
  }

  // Character variety
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]/.test(password);

  if (hasUpper) {
    score += 1;
  } else {
    feedback.push('Add uppercase letters');
  }

  if (hasLower) {
    score += 1;
  } else {
    feedback.push('Add lowercase letters');
  }

  if (hasDigit) {
    score += 1;
  } else {
    feedback.push('Add numbers');
  }

  if (hasSpecial) {
    score += 1;
  } else {
    feedback.push('Add special characters (!@#$%^&*)');
  }

  // Common patterns
  const commonPatterns = ['password', '123456', 'qwerty', 'letmein', 'admin'];
  if (commonPatterns.some((p) => password.toLowerCase().includes(p))) {
    score = Math.max(0, score - 2);
    feedback.push('Avoid common passwords');
  }

  let strength: 'weak' | 'moderate' | 'strong';
  if (score <= 2) {
    strength = 'weak';
  } else if (score <= 4) {
    strength = 'moderate';
  } else {
    strength = 'strong';
  }

  const meetsRequirements =
    password.length >= 12 && hasUpper && hasLower && hasDigit && hasSpecial;

  return {
    score: Math.min(score, 6),
    strength,
    feedback: feedback.length ? feedback : ['Password meets all requirements'],
    meets_requirements: meetsRequirements,
  };
}

// =============================================================================
// Session Management
// =============================================================================

export interface ActiveSession {
  id: string;
  device_name: string;
  ip_address: string;
  last_activity: string;
  created_at: string;
  is_current: boolean;
}

/**
 * Auth API helper for session management.
 * Uses session cookie for authentication.
 */
export const authApi = {
  async getSessions(): Promise<ActiveSession[]> {
    const res = await fetch(`${API_BASE}/auth/me/sessions`, {
      credentials: 'include',
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to load sessions' }));
      throw new Error(error.detail || 'Failed to load sessions');
    }
    return res.json();
  },

  async revokeSession(sessionId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/me/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to revoke session' }));
      throw new Error(error.detail || 'Failed to revoke session');
    }
  },

  async revokeAllSessions(): Promise<{ revoked_count: number }> {
    const res = await fetch(`${API_BASE}/auth/me/sessions`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to revoke sessions' }));
      throw new Error(error.detail || 'Failed to revoke sessions');
    }
    return res.json();
  },
};

// Role display helpers
export const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrator',
  cardiologist: 'Cardiologist',
  nurse: 'Nurse',
  receptionist: 'Receptionist',
  lab_tech: 'Lab Technician',
  auditor: 'Auditor',
};

export const ROLE_COLORS: Record<string, { bg: string; text: string }> = {
  admin: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  cardiologist: { bg: 'bg-rose-500/20', text: 'text-rose-400' },
  nurse: { bg: 'bg-teal-500/20', text: 'text-teal-400' },
  receptionist: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  lab_tech: { bg: 'bg-amber-500/20', text: 'text-amber-400' },
  auditor: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
};

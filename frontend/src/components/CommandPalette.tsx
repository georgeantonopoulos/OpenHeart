'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Command } from 'cmdk';
import {
  Search,
  Users,
  Calendar,
  Activity,
  Image,
  Settings,
  Heart,
  ClipboardList,
  UserPlus,
  Stethoscope,
  FileText,
} from 'lucide-react';
import type { Patient } from '@/lib/api/patients';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const { data: session } = useSession();
  const [search, setSearch] = useState('');
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Reset state when closed
  useEffect(() => {
    if (!open) {
      setSearch('');
      setPatientResults([]);
    }
  }, [open]);

  // Debounced patient search
  useEffect(() => {
    if (search.length < 2 || !session?.accessToken) {
      setPatientResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(
          `${API_BASE}/api/patients/search?q=${encodeURIComponent(search)}&page_size=5`,
          { headers: { Authorization: `Bearer ${session.accessToken}` } }
        );
        if (res.ok) {
          const data = await res.json();
          setPatientResults(data.items || []);
        }
      } catch {
        // Silently handle search errors
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [search, session?.accessToken]);

  const navigate = useCallback((path: string) => {
    onOpenChange(false);
    router.push(path);
  }, [router, onOpenChange]);

  // Navigation items
  const navItems = [
    { icon: Users, label: 'Patients', path: '/patients', keywords: 'patient list search' },
    { icon: Calendar, label: 'Appointments', path: '/appointments', keywords: 'schedule calendar booking' },
    { icon: Activity, label: 'CDSS Calculators', path: '/cdss', keywords: 'clinical decision grace hasbled cha2ds2vasc' },
    { icon: Image, label: 'Imaging Browser', path: '/imaging', keywords: 'dicom xray echo ultrasound' },
    { icon: ClipboardList, label: 'Procedure Worklist', path: '/procedures/worklist', keywords: 'cath pci echo schedule' },
    { icon: FileText, label: 'Referrals', path: '/referrals/incoming', keywords: 'refer incoming gesy' },
    { icon: Heart, label: 'Dashboard', path: '/dashboard', keywords: 'home overview stats' },
    { icon: Settings, label: 'Profile & Security', path: '/profile', keywords: 'account password mfa settings' },
  ];

  // Quick actions
  const actions = [
    { icon: UserPlus, label: 'New Patient', path: '/patients/new', keywords: 'create add register patient' },
    { icon: Calendar, label: 'New Appointment', path: '/appointments/new', keywords: 'schedule book appointment' },
    { icon: Stethoscope, label: 'Schedule Procedure', path: '/procedures/schedule', keywords: 'cath pci book procedure' },
  ];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Command dialog */}
      <div className="absolute left-1/2 top-[20%] -translate-x-1/2 w-full max-w-lg px-4">
        <Command
          className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden"
          shouldFilter={true}
        >
          <div className="flex items-center border-b border-slate-800 px-4">
            <Search className="w-5 h-5 text-slate-500 shrink-0" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Search patients, pages, actions..."
              className="w-full py-4 px-3 bg-transparent text-white text-sm placeholder:text-slate-500 focus:outline-none"
            />
            <kbd className="shrink-0 px-2 py-1 text-xs text-slate-500 bg-slate-800 rounded">
              ESC
            </kbd>
          </div>

          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-slate-500">
              {isSearching ? 'Searching...' : 'No results found.'}
            </Command.Empty>

            {/* Patient search results */}
            {patientResults.length > 0 && (
              <Command.Group
                heading="Patients"
                className="[&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-slate-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
              >
                {patientResults.map((patient) => (
                  <Command.Item
                    key={patient.patient_id}
                    value={`patient ${patient.first_name} ${patient.last_name} ${patient.mrn}`}
                    onSelect={() => navigate(`/patients/${patient.patient_id}`)}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 cursor-pointer data-[selected=true]:bg-slate-800 data-[selected=true]:text-white"
                  >
                    <Users className="w-4 h-4 text-rose-500 shrink-0" />
                    <div className="min-w-0">
                      <div className="truncate">
                        {patient.first_name} {patient.last_name}
                      </div>
                      <div className="text-xs text-slate-500">
                        MRN: {patient.mrn}
                      </div>
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Navigation */}
            <Command.Group
              heading="Pages"
              className="[&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-slate-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              {navItems.map((item) => (
                <Command.Item
                  key={item.path}
                  value={`${item.label} ${item.keywords}`}
                  onSelect={() => navigate(item.path)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 cursor-pointer data-[selected=true]:bg-slate-800 data-[selected=true]:text-white"
                >
                  <item.icon className="w-4 h-4 text-slate-500 shrink-0" />
                  {item.label}
                </Command.Item>
              ))}
            </Command.Group>

            {/* Quick Actions */}
            <Command.Group
              heading="Quick Actions"
              className="[&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-slate-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              {actions.map((action) => (
                <Command.Item
                  key={action.path}
                  value={`${action.label} ${action.keywords}`}
                  onSelect={() => navigate(action.path)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 cursor-pointer data-[selected=true]:bg-slate-800 data-[selected=true]:text-white"
                >
                  <action.icon className="w-4 h-4 text-teal-500 shrink-0" />
                  {action.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

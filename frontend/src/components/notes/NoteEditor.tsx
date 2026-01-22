'use client';

/**
 * NoteEditor Component
 *
 * Rich text editor for clinical notes with:
 * - Formatting toolbar (bold, italic, lists, tables)
 * - Template selection (SOAP, Procedure, Consultation)
 * - Auto-save with visual indicator
 * - Version history sidebar trigger
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Table,
  Undo,
  Redo,
  Save,
  Clock,
  FileText,
  AlertCircle,
  Check,
  Loader2,
} from 'lucide-react';

type NoteType = 'free_text' | 'soap' | 'procedure' | 'consultation' | 'discharge' | 'progress';

interface SOAPContent {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

interface NoteEditorProps {
  initialContent?: string;
  initialStructuredData?: SOAPContent;
  noteType?: NoteType;
  onSave: (content: string, structuredData?: SOAPContent) => Promise<void>;
  onAutoSave?: (content: string, structuredData?: SOAPContent) => void;
  isLocked?: boolean;
  lockedReason?: string;
  className?: string;
}

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

const NOTE_TEMPLATES: Record<NoteType, { label: string; template: string }> = {
  free_text: {
    label: 'Free Text',
    template: '',
  },
  soap: {
    label: 'SOAP Note',
    template: `**Subjective:**


**Objective:**


**Assessment:**


**Plan:**

`,
  },
  procedure: {
    label: 'Procedure Note',
    template: `**Procedure:**
**Date:**
**Indication:**

**Technique:**


**Findings:**


**Complications:** None

**Impression:**


**Recommendations:**

`,
  },
  consultation: {
    label: 'Consultation',
    template: `**Reason for Consultation:**


**History of Present Illness:**


**Past Medical History:**


**Medications:**


**Physical Examination:**


**Assessment:**


**Recommendations:**

`,
  },
  discharge: {
    label: 'Discharge Summary',
    template: `**Admission Date:**
**Discharge Date:**

**Diagnosis:**


**Hospital Course:**


**Discharge Medications:**


**Follow-up:**


**Instructions:**

`,
  },
  progress: {
    label: 'Progress Note',
    template: `**Date:**
**Time:**

**Interval History:**


**Current Status:**


**Plan:**

`,
  },
};

export function NoteEditor({
  initialContent = '',
  initialStructuredData,
  noteType = 'free_text',
  onSave,
  onAutoSave,
  isLocked = false,
  lockedReason,
  className = '',
}: NoteEditorProps) {
  const { t } = useTranslation('cardiology');
  const [content, setContent] = useState(initialContent);
  const [structuredData, setStructuredData] = useState<SOAPContent | undefined>(
    initialStructuredData
  );
  const [selectedType, setSelectedType] = useState<NoteType>(noteType);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-save functionality
  useEffect(() => {
    if (!onAutoSave || isLocked) return;

    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    if (hasUnsavedChanges) {
      autoSaveTimerRef.current = setTimeout(() => {
        onAutoSave(content, structuredData);
        setSaveStatus('saved');
        setLastSaved(new Date());
        setHasUnsavedChanges(false);

        // Reset status after 2 seconds
        setTimeout(() => setSaveStatus('idle'), 2000);
      }, 3000); // Auto-save after 3 seconds of inactivity
    }

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [content, structuredData, hasUnsavedChanges, onAutoSave, isLocked]);

  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    setHasUnsavedChanges(true);
    setSaveStatus('idle');
  }, []);

  const handleStructuredDataChange = useCallback(
    (field: keyof SOAPContent, value: string) => {
      setStructuredData((prev) => ({
        subjective: prev?.subjective || '',
        objective: prev?.objective || '',
        assessment: prev?.assessment || '',
        plan: prev?.plan || '',
        [field]: value,
      }));
      setHasUnsavedChanges(true);
      setSaveStatus('idle');
    },
    []
  );

  const handleSave = useCallback(async () => {
    if (isLocked) return;

    setSaveStatus('saving');
    try {
      await onSave(content, structuredData);
      setSaveStatus('saved');
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch (error) {
      setSaveStatus('error');
      console.error('Failed to save note:', error);
    }
  }, [content, structuredData, onSave, isLocked]);

  const handleTemplateChange = useCallback((type: NoteType) => {
    setSelectedType(type);
    if (type === 'soap') {
      setStructuredData({
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
      });
    } else {
      setStructuredData(undefined);
      if (!content) {
        setContent(NOTE_TEMPLATES[type].template);
      }
    }
  }, [content]);

  const insertFormatting = useCallback(
    (before: string, after: string = before) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const selectedText = content.substring(start, end);

      const newContent =
        content.substring(0, start) +
        before +
        selectedText +
        after +
        content.substring(end);

      setContent(newContent);
      setHasUnsavedChanges(true);

      // Restore cursor position
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(
          start + before.length,
          end + before.length
        );
      }, 0);
    },
    [content]
  );

  const formatBold = () => insertFormatting('**');
  const formatItalic = () => insertFormatting('*');
  const formatBulletList = () => insertFormatting('\n- ');
  const formatNumberedList = () => insertFormatting('\n1. ');
  const insertTable = () => {
    insertFormatting(
      '\n| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n',
      ''
    );
  };

  const SaveStatusIndicator = () => {
    switch (saveStatus) {
      case 'saving':
        return (
          <span className="flex items-center text-blue-600 text-sm">
            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            Saving...
          </span>
        );
      case 'saved':
        return (
          <span className="flex items-center text-green-600 text-sm">
            <Check className="h-4 w-4 mr-1" />
            Saved
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center text-red-600 text-sm">
            <AlertCircle className="h-4 w-4 mr-1" />
            Error saving
          </span>
        );
      default:
        if (hasUnsavedChanges) {
          return (
            <span className="flex items-center text-amber-600 text-sm">
              <Clock className="h-4 w-4 mr-1" />
              Unsaved changes
            </span>
          );
        }
        if (lastSaved) {
          return (
            <span className="text-gray-500 text-sm">
              Last saved: {lastSaved.toLocaleTimeString()}
            </span>
          );
        }
        return null;
    }
  };

  if (isLocked) {
    return (
      <div className={`rounded-lg border border-amber-200 bg-amber-50 p-4 ${className}`}>
        <div className="flex items-center text-amber-800 mb-2">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="font-medium">Note is locked</span>
        </div>
        <p className="text-amber-700 text-sm">{lockedReason || 'This note cannot be edited.'}</p>
        <div className="mt-4 bg-white rounded border p-4">
          <pre className="whitespace-pre-wrap font-sans text-sm">{content}</pre>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border bg-white ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b px-4 py-2 bg-gray-50">
        <div className="flex items-center space-x-1">
          {/* Template Selector */}
          <select
            value={selectedType}
            onChange={(e) => handleTemplateChange(e.target.value as NoteType)}
            className="mr-4 rounded border px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {Object.entries(NOTE_TEMPLATES).map(([type, { label }]) => (
              <option key={type} value={type}>
                {label}
              </option>
            ))}
          </select>

          <div className="w-px h-6 bg-gray-300 mx-2" />

          {/* Formatting buttons */}
          <button
            onClick={formatBold}
            className="p-1.5 rounded hover:bg-gray-200 transition-colors"
            title="Bold (Ctrl+B)"
          >
            <Bold className="h-4 w-4" />
          </button>
          <button
            onClick={formatItalic}
            className="p-1.5 rounded hover:bg-gray-200 transition-colors"
            title="Italic (Ctrl+I)"
          >
            <Italic className="h-4 w-4" />
          </button>
          <button
            onClick={formatBulletList}
            className="p-1.5 rounded hover:bg-gray-200 transition-colors"
            title="Bullet List"
          >
            <List className="h-4 w-4" />
          </button>
          <button
            onClick={formatNumberedList}
            className="p-1.5 rounded hover:bg-gray-200 transition-colors"
            title="Numbered List"
          >
            <ListOrdered className="h-4 w-4" />
          </button>
          <button
            onClick={insertTable}
            className="p-1.5 rounded hover:bg-gray-200 transition-colors"
            title="Insert Table"
          >
            <Table className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center space-x-4">
          <SaveStatusIndicator />
          <button
            onClick={handleSave}
            disabled={saveStatus === 'saving' || !hasUnsavedChanges}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="h-4 w-4 mr-1" />
            Save
          </button>
        </div>
      </div>

      {/* Editor Area */}
      <div className="p-4">
        {selectedType === 'soap' ? (
          <div className="space-y-4">
            {(['subjective', 'objective', 'assessment', 'plan'] as const).map((field) => (
              <div key={field}>
                <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                  {field}
                </label>
                <textarea
                  value={structuredData?.[field] || ''}
                  onChange={(e) => handleStructuredDataChange(field, e.target.value)}
                  className="w-full rounded border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows={field === 'objective' || field === 'plan' ? 6 : 4}
                  placeholder={
                    field === 'subjective'
                      ? "Patient's chief complaint and history..."
                      : field === 'objective'
                      ? 'Physical exam findings, vitals, test results...'
                      : field === 'assessment'
                      ? 'Diagnosis and clinical impression...'
                      : 'Treatment plan and follow-up...'
                  }
                />
              </div>
            ))}
          </div>
        ) : (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            className="w-full min-h-[400px] rounded border border-gray-300 p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-mono text-sm"
            placeholder="Enter clinical note..."
          />
        )}
      </div>
    </div>
  );
}

export default NoteEditor;

'use client';

/**
 * NoteTimeline Component
 *
 * Displays chronological list of clinical notes for a patient with:
 * - Search and filtering
 * - Note type badges
 * - Version indicators
 * - Quick preview
 */

import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  Filter,
  FileText,
  Clock,
  User,
  ChevronRight,
  Paperclip,
  History,
  Eye,
} from 'lucide-react';

type NoteType = 'free_text' | 'soap' | 'procedure' | 'consultation' | 'discharge' | 'progress';

interface NoteItem {
  noteId: number;
  patientId: number;
  title: string;
  noteType: NoteType;
  currentVersion: number;
  contentPreview: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  attachmentCount: number;
  isLocked: boolean;
}

interface NoteTimelineProps {
  notes: NoteItem[];
  onNoteClick: (noteId: number) => void;
  onCreateNote?: () => void;
  className?: string;
}

const NOTE_TYPE_CONFIG: Record<NoteType, { label: string; color: string }> = {
  free_text: { label: 'Note', color: 'bg-gray-100 text-gray-700' },
  soap: { label: 'SOAP', color: 'bg-blue-100 text-blue-700' },
  procedure: { label: 'Procedure', color: 'bg-purple-100 text-purple-700' },
  consultation: { label: 'Consult', color: 'bg-green-100 text-green-700' },
  discharge: { label: 'Discharge', color: 'bg-amber-100 text-amber-700' },
  progress: { label: 'Progress', color: 'bg-teal-100 text-teal-700' },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-CY', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-CY', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function NoteCard({
  note,
  onClick,
}: {
  note: NoteItem;
  onClick: () => void;
}) {
  const typeConfig = NOTE_TYPE_CONFIG[note.noteType];

  return (
    <div
      onClick={onClick}
      className="group border rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer bg-white"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${typeConfig.color}`}
          >
            {typeConfig.label}
          </span>
          {note.isLocked && (
            <span className="px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-700">
              Locked
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2 text-gray-400">
          {note.attachmentCount > 0 && (
            <span className="flex items-center text-xs">
              <Paperclip className="h-3 w-3 mr-0.5" />
              {note.attachmentCount}
            </span>
          )}
          {note.currentVersion > 1 && (
            <span className="flex items-center text-xs">
              <History className="h-3 w-3 mr-0.5" />
              v{note.currentVersion}
            </span>
          )}
        </div>
      </div>

      <h3 className="font-medium text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
        {note.title}
      </h3>

      <p className="text-sm text-gray-600 line-clamp-2 mb-3">
        {note.contentPreview}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-3">
          <span className="flex items-center">
            <User className="h-3 w-3 mr-1" />
            {note.createdBy}
          </span>
          <span className="flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {formatDate(note.createdAt)} at {formatTime(note.createdAt)}
          </span>
        </div>
        <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-blue-500 transition-colors" />
      </div>
    </div>
  );
}

export function NoteTimeline({
  notes,
  onNoteClick,
  onCreateNote,
  className = '',
}: NoteTimelineProps) {
  const { t } = useTranslation('cardiology');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<NoteType | 'all'>('all');
  const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');

  const filteredNotes = useMemo(() => {
    let result = [...notes];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (note) =>
          note.title.toLowerCase().includes(query) ||
          note.contentPreview.toLowerCase().includes(query) ||
          note.createdBy.toLowerCase().includes(query)
      );
    }

    // Type filter
    if (filterType !== 'all') {
      result = result.filter((note) => note.noteType === filterType);
    }

    // Sort
    result.sort((a, b) => {
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return result;
  }, [notes, searchQuery, filterType, sortOrder]);

  // Group notes by date
  const groupedNotes = useMemo(() => {
    const groups: Record<string, NoteItem[]> = {};

    filteredNotes.forEach((note) => {
      const dateKey = formatDate(note.createdAt);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(note);
    });

    return groups;
  }, [filteredNotes]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Clinical Notes</h2>
        {onCreateNote && (
          <button
            onClick={onCreateNote}
            className="flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
          >
            <FileText className="h-4 w-4 mr-1" />
            New Note
          </button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as NoteType | 'all')}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Types</option>
          {Object.entries(NOTE_TYPE_CONFIG).map(([type, { label }]) => (
            <option key={type} value={type}>
              {label}
            </option>
          ))}
        </select>

        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value as 'newest' | 'oldest')}
          className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="newest">Newest First</option>
          <option value="oldest">Oldest First</option>
        </select>
      </div>

      {/* Results count */}
      <div className="text-sm text-gray-500 mb-3">
        {filteredNotes.length} note{filteredNotes.length !== 1 ? 's' : ''}
        {searchQuery && ` matching "${searchQuery}"`}
      </div>

      {/* Notes List */}
      <div className="flex-1 overflow-y-auto space-y-6">
        {Object.entries(groupedNotes).length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              {searchQuery ? 'No notes match your search' : 'No clinical notes yet'}
            </p>
            {onCreateNote && !searchQuery && (
              <button
                onClick={onCreateNote}
                className="mt-4 text-blue-600 hover:text-blue-700 text-sm"
              >
                Create the first note
              </button>
            )}
          </div>
        ) : (
          Object.entries(groupedNotes).map(([date, dateNotes]) => (
            <div key={date}>
              <div className="flex items-center mb-3">
                <div className="h-px flex-1 bg-gray-200" />
                <span className="px-3 text-xs font-medium text-gray-500 uppercase">
                  {date}
                </span>
                <div className="h-px flex-1 bg-gray-200" />
              </div>

              <div className="space-y-3">
                {dateNotes.map((note) => (
                  <NoteCard
                    key={note.noteId}
                    note={note}
                    onClick={() => onNoteClick(note.noteId)}
                  />
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default NoteTimeline;

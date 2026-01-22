'use client';

/**
 * VersionHistory Component
 *
 * Displays version history for a clinical note with:
 * - List of all versions with timestamps
 * - Diff highlighting between versions
 * - Version comparison modal
 * - Restore capability (creates new version)
 */

import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  History,
  Clock,
  User,
  ChevronDown,
  ChevronUp,
  Eye,
  GitCompare,
  RotateCcw,
  X,
  Plus,
  Minus,
} from 'lucide-react';

interface NoteVersion {
  versionId: number;
  versionNumber: number;
  contentText: string;
  editedBy: string;
  editReason: string | null;
  wordCount: number;
  charCount: number;
  createdAt: string;
}

interface DiffHunk {
  lineStart: number;
  lineEnd: number;
  oldContent: string;
  newContent: string;
  changeType: 'add' | 'delete' | 'modify';
}

interface VersionHistoryProps {
  versions: NoteVersion[];
  currentVersion: number;
  onViewVersion: (versionNumber: number) => void;
  onCompareVersions: (fromVersion: number, toVersion: number) => Promise<{
    hunks: DiffHunk[];
    additions: number;
    deletions: number;
  }>;
  onRestoreVersion?: (versionNumber: number) => void;
  className?: string;
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-CY', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDateTime(dateString);
}

function DiffView({ hunks }: { hunks: DiffHunk[] }) {
  if (hunks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No differences found - versions are identical
      </div>
    );
  }

  return (
    <div className="space-y-4 font-mono text-sm">
      {hunks.map((hunk, index) => (
        <div key={index} className="border rounded overflow-hidden">
          <div className="bg-gray-100 px-3 py-1 text-xs text-gray-600">
            Lines {hunk.lineStart}-{hunk.lineEnd}
          </div>
          {hunk.changeType === 'delete' || hunk.changeType === 'modify' ? (
            <div className="bg-red-50 border-l-4 border-red-400 p-2">
              {hunk.oldContent.split('\n').map((line, i) => (
                <div key={`old-${i}`} className="flex items-start">
                  <Minus className="h-4 w-4 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-red-800">{line || ' '}</span>
                </div>
              ))}
            </div>
          ) : null}
          {hunk.changeType === 'add' || hunk.changeType === 'modify' ? (
            <div className="bg-green-50 border-l-4 border-green-400 p-2">
              {hunk.newContent.split('\n').map((line, i) => (
                <div key={`new-${i}`} className="flex items-start">
                  <Plus className="h-4 w-4 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span className="text-green-800">{line || ' '}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function VersionHistory({
  versions,
  currentVersion,
  onViewVersion,
  onCompareVersions,
  onRestoreVersion,
  className = '',
}: VersionHistoryProps) {
  const { t } = useTranslation('cardiology');
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [compareFrom, setCompareFrom] = useState<number | null>(null);
  const [compareTo, setCompareTo] = useState<number | null>(null);
  const [diffResult, setDiffResult] = useState<{
    hunks: DiffHunk[];
    additions: number;
    deletions: number;
  } | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const sortedVersions = useMemo(
    () => [...versions].sort((a, b) => b.versionNumber - a.versionNumber),
    [versions]
  );

  const handleCompare = async () => {
    if (!compareFrom || !compareTo) return;

    setIsComparing(true);
    try {
      const result = await onCompareVersions(compareFrom, compareTo);
      setDiffResult(result);
    } catch (error) {
      console.error('Failed to compare versions:', error);
    } finally {
      setIsComparing(false);
    }
  };

  const toggleVersionExpand = (versionNumber: number) => {
    setExpandedVersion(
      expandedVersion === versionNumber ? null : versionNumber
    );
  };

  const handleVersionSelect = (versionNumber: number) => {
    if (!compareMode) {
      onViewVersion(versionNumber);
      return;
    }

    if (!compareFrom) {
      setCompareFrom(versionNumber);
    } else if (!compareTo) {
      setCompareTo(versionNumber);
    } else {
      // Reset and start over
      setCompareFrom(versionNumber);
      setCompareTo(null);
      setDiffResult(null);
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <History className="h-5 w-5 text-gray-500 mr-2" />
          <h3 className="font-medium text-gray-900">Version History</h3>
          <span className="ml-2 text-sm text-gray-500">
            ({versions.length} version{versions.length !== 1 ? 's' : ''})
          </span>
        </div>
        <button
          onClick={() => {
            setCompareMode(!compareMode);
            setCompareFrom(null);
            setCompareTo(null);
            setDiffResult(null);
          }}
          className={`flex items-center px-2 py-1 text-sm rounded transition-colors ${
            compareMode
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <GitCompare className="h-4 w-4 mr-1" />
          Compare
        </button>
      </div>

      {/* Compare Mode Instructions */}
      {compareMode && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-700 mb-2">
            Select two versions to compare:
          </p>
          <div className="flex items-center space-x-2 text-sm">
            <span
              className={`px-2 py-1 rounded ${
                compareFrom
                  ? 'bg-blue-200 text-blue-800'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {compareFrom ? `v${compareFrom}` : 'Select first'}
            </span>
            <span className="text-gray-400">→</span>
            <span
              className={`px-2 py-1 rounded ${
                compareTo
                  ? 'bg-blue-200 text-blue-800'
                  : 'bg-gray-200 text-gray-500'
              }`}
            >
              {compareTo ? `v${compareTo}` : 'Select second'}
            </span>
            {compareFrom && compareTo && (
              <button
                onClick={handleCompare}
                disabled={isComparing}
                className="ml-auto px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {isComparing ? 'Comparing...' : 'Compare'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Diff Result */}
      {diffResult && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-3 text-sm">
              <span className="text-green-600">+{diffResult.additions} additions</span>
              <span className="text-red-600">-{diffResult.deletions} deletions</span>
            </div>
            <button
              onClick={() => setDiffResult(null)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="max-h-64 overflow-y-auto border rounded-lg p-3 bg-gray-50">
            <DiffView hunks={diffResult.hunks} />
          </div>
        </div>
      )}

      {/* Version List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {sortedVersions.map((version) => {
          const isExpanded = expandedVersion === version.versionNumber;
          const isCurrent = version.versionNumber === currentVersion;
          const isSelected =
            compareMode &&
            (compareFrom === version.versionNumber ||
              compareTo === version.versionNumber);

          return (
            <div
              key={version.versionId}
              className={`border rounded-lg overflow-hidden transition-all ${
                isSelected
                  ? 'border-blue-300 bg-blue-50'
                  : isCurrent
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {/* Version Header */}
              <div
                onClick={() =>
                  compareMode
                    ? handleVersionSelect(version.versionNumber)
                    : toggleVersionExpand(version.versionNumber)
                }
                className="flex items-center justify-between p-3 cursor-pointer"
              >
                <div className="flex items-center space-x-3">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      isCurrent
                        ? 'bg-green-200 text-green-800'
                        : 'bg-gray-200 text-gray-700'
                    }`}
                  >
                    v{version.versionNumber}
                    {isCurrent && ' (current)'}
                  </span>
                  <span className="text-sm text-gray-600">
                    {version.editReason || 'Initial version'}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-gray-400">
                  <span className="text-xs">
                    {formatRelativeTime(version.createdAt)}
                  </span>
                  {!compareMode &&
                    (isExpanded ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    ))}
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && !compareMode && (
                <div className="border-t bg-white p-3 space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4 text-gray-500">
                      <span className="flex items-center">
                        <User className="h-4 w-4 mr-1" />
                        {version.editedBy}
                      </span>
                      <span className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {formatDateTime(version.createdAt)}
                      </span>
                    </div>
                    <span className="text-gray-400">
                      {version.wordCount} words
                    </span>
                  </div>

                  {/* Content Preview */}
                  <div className="bg-gray-50 rounded p-2 max-h-32 overflow-y-auto">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                      {version.contentText.substring(0, 500)}
                      {version.contentText.length > 500 && '...'}
                    </pre>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onViewVersion(version.versionNumber)}
                      className="flex items-center px-2 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View Full
                    </button>
                    {onRestoreVersion && !isCurrent && (
                      <button
                        onClick={() => onRestoreVersion(version.versionNumber)}
                        className="flex items-center px-2 py-1 text-sm text-amber-600 hover:bg-amber-50 rounded"
                      >
                        <RotateCcw className="h-4 w-4 mr-1" />
                        Restore
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VersionHistory;

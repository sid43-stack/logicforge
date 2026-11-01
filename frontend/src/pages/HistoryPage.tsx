import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  History as HistoryIcon,
  Search,
  RotateCcw,
  Play,
  Trash2,
  Eye,
  FileText,
  GitBranch,
  Clock,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  ShieldAlert,
} from 'lucide-react';
import { historyApi } from '../api/history';
import { SessionSummary, SessionDetailResponse } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const HistoryPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const pageSize = 15;

  // Modals state
  const [inspectSessionId, setInspectSessionId] = useState<string | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [deleteSessionId, setDeleteSessionId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await historyApi.listSessions(page * pageSize, pageSize, statusFilter);
      setSessions(data.items);
      setTotalCount(data.total);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load historical diagnostic sessions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [page, statusFilter]);

  const handleInspectSession = async (sessionId: string) => {
    setInspectSessionId(sessionId);
    setDetailLoading(true);
    setDetailError(null);
    try {
      const detail = await historyApi.getSessionDetail(sessionId);
      setSessionDetail(detail);
    } catch (err: any) {
      setDetailError(err?.detail || 'Failed to retrieve detailed session audit records.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteSessionId) return;
    setIsDeleting(true);
    try {
      await historyApi.deleteSession(deleteSessionId);
      setDeleteSessionId(null);
      await fetchSessions();
    } catch (err: any) {
      alert(`Delete failed: ${err?.detail || 'Unexpected error'}`);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCopyId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Client-side search filtering across the fetched page items
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const q = searchQuery.toLowerCase().trim();
    return sessions.filter((s) => {
      const matchId = s.id.toLowerCase().includes(q);
      const matchDiag = s.final_diagnosis?.toLowerCase().includes(q);
      const matchCat = s.diagnosis_category?.toLowerCase().includes(q);
      return matchId || matchDiag || matchCat;
    });
  }, [sessions, searchQuery]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const statusPills: { label: string; value: string }[] = [
    { label: 'All Sessions', value: 'ALL' },
    { label: 'Completed', value: 'COMPLETED' },
    { label: 'In Progress', value: 'IN_PROGRESS' },
    { label: 'Inconclusive', value: 'INCONCLUSIVE' },
    { label: 'Conflicts', value: 'CONFLICT_DETECTED' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8D0C0] pb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#FFFCF5] border border-stone-300 text-gold-700">
            <HistoryIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#2B2822] tracking-tight">Diagnostic Session History</h1>
            <p className="text-sm text-stone-600">
              Historical audit log of troubleshooting runs, dynamic questions asked, and verified root-cause diagnoses.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<RotateCcw className="w-3.5 h-3.5" />}
            onClick={() => fetchSessions()}
          >
            Refresh
          </Button>
          <Link to="/diagnose">
            <Button variant="primary" size="md" icon={<Play className="w-4 h-4" />}>
              New Diagnosis
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorMessage error={error} onRetry={fetchSessions} />}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-[#FFFCF5] border border-[#D8D0C0] p-3.5 rounded-xl">
        {/* Status Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {statusPills.map((pill) => (
            <button
              key={pill.value}
              onClick={() => {
                setStatusFilter(pill.value);
                setPage(0);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === pill.value
                  ? 'bg-gold-600 text-[#2B2822] shadow-sm'
                  : 'bg-[#EAE3D8]/80 text-stone-700 hover:bg-[#EAE3D8] hover:text-[#2B2822]'
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-stone-600" />
          <input
            type="text"
            placeholder="Search diagnosis or session ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-[#FFFCF5] border border-stone-400/80 rounded-lg text-xs text-[#2B2822] placeholder-stone-500 focus:outline-none focus:ring-1 focus:ring-gold-500 focus:border-gold-500"
          />
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <LoadingSpinner message="Loading historical diagnostic sessions..." />
      ) : filteredSessions.length === 0 ? (
        <Card className="text-center py-12 space-y-4">
          <HistoryIcon className="w-10 h-10 text-stone-700 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-stone-800">No diagnostic sessions found</h3>
            <p className="text-xs text-stone-600 max-w-md mx-auto">
              {searchQuery || statusFilter !== 'ALL'
                ? 'No recorded sessions match the selected status or search filter.'
                : 'You have not run any network troubleshooting sessions yet.'}
            </p>
          </div>
          <div className="pt-2">
            <Link to="/diagnose">
              <Button variant="primary" size="sm" icon={<Play className="w-3.5 h-3.5" />}>
                Launch New Diagnostic
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="bg-[#FFFCF5] border border-[#D8D0C0] rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#FFFCF5]/90 border-b border-[#D8D0C0] text-stone-600 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Session ID</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Diagnosis / Outcome</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Questions</th>
                    <th className="py-3 px-4">Created Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D8D0C0] text-stone-700">
                  {filteredSessions.map((sess) => (
                    <tr
                      key={sess.id}
                      className="hover:bg-[#EAE3D8]/40 transition-colors group cursor-pointer"
                      onClick={() => handleInspectSession(sess.id)}
                    >
                      {/* Session ID */}
                      <td className="py-3 px-4 font-mono text-[11px] text-stone-600">
                        <div className="flex items-center gap-1.5">
                          <span>{sess.id.substring(0, 8)}...</span>
                          <button
                            onClick={(e) => handleCopyId(sess.id, e)}
                            className="p-1 rounded hover:bg-[#D8D0C0] text-stone-600 hover:text-stone-700 transition-colors"
                            title="Copy full UUID"
                          >
                            {copiedId === sess.id ? (
                              <Check className="w-3 h-3 text-emerald-700" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <Badge variant="status" value={sess.status} size="sm" />
                      </td>

                      {/* Diagnosis */}
                      <td className="py-3 px-4 font-medium text-stone-800 max-w-xs truncate">
                        {sess.final_diagnosis ? (
                          sess.final_diagnosis
                        ) : sess.status === 'IN_PROGRESS' ? (
                          <span className="text-gold-700 italic">In progress...</span>
                        ) : sess.status === 'CONFLICT_DETECTED' ? (
                          <span className="text-red-700 italic">Contradictory evidence</span>
                        ) : (
                          <span className="text-amber-700 italic">Inconclusive outcome</span>
                        )}
                      </td>

                      {/* Category */}
                      <td className="py-3 px-4">
                        {sess.diagnosis_category ? (
                          <Badge variant="category" value={sess.diagnosis_category} size="sm" />
                        ) : (
                          <span className="text-stone-600">—</span>
                        )}
                      </td>

                      {/* Severity */}
                      <td className="py-3 px-4">
                        {sess.severity ? (
                          <Badge variant="severity" value={sess.severity} size="sm" />
                        ) : (
                          <span className="text-stone-600">—</span>
                        )}
                      </td>

                      {/* Questions */}
                      <td className="py-3 px-4 text-stone-600">
                        {sess.answers_count} {sess.answers_count === 1 ? 'answer' : 'answers'}
                      </td>

                      {/* Date */}
                      <td className="py-3 px-4 text-stone-600">
                        {new Date(sess.created_at).toLocaleString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </td>

                      {/* Actions */}
                      <td
                        className="py-3 px-4 text-right space-x-1.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Eye className="w-3.5 h-3.5" />}
                          onClick={() => handleInspectSession(sess.id)}
                          title="Inspect audit trail"
                          className="px-2 py-1 text-xs text-stone-700 hover:text-[#2B2822]"
                        >
                          Audit
                        </Button>

                        {sess.status === 'IN_PROGRESS' ? (
                          <Link to={`/diagnose?session_id=${sess.id}`}>
                            <Button
                              variant="primary"
                              size="sm"
                              className="px-2.5 py-1 text-xs"
                            >
                              Resume
                            </Button>
                          </Link>
                        ) : (
                          <>
                            <Link to={`/results/${sess.id}`}>
                              <Button
                                variant="outline"
                                size="sm"
                                icon={<FileText className="w-3.5 h-3.5" />}
                                className="px-2 py-1 text-xs text-stone-700 hover:text-[#2B2822]"
                              >
                                Plan
                              </Button>
                            </Link>
                            <Link to={`/explain/${sess.id}`}>
                              <Button
                                variant="outline"
                                size="sm"
                                icon={<GitBranch className="w-3.5 h-3.5" />}
                                className="px-2 py-1 text-xs text-gold-700 border-gold-500/30 hover:bg-gold-950/40"
                              >
                                DAG
                              </Button>
                            </Link>
                          </>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 className="w-3.5 h-3.5 text-red-700" />}
                          onClick={() => setDeleteSessionId(sess.id)}
                          title="Delete session"
                          className="px-2 py-1 hover:bg-red-950/30 text-red-700 hover:text-red-800"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination footer */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#FFFCF5]/60 border-t border-[#D8D0C0] text-xs text-stone-600">
              <div>
                Showing <span className="font-semibold text-stone-800">{page * pageSize + 1}</span> to{' '}
                <span className="font-semibold text-stone-800">
                  {Math.min((page + 1) * pageSize, totalCount)}
                </span>{' '}
                of <span className="font-semibold text-stone-800">{totalCount}</span> sessions
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  icon={<ChevronLeft className="w-3.5 h-3.5" />}
                >
                  Previous
                </Button>
                <span className="text-stone-600 text-xs px-2">
                  Page {page + 1} of {Math.max(1, totalPages)}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page + 1 >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  icon={<ChevronRight className="w-3.5 h-3.5" />}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Session Audit Detail Modal */}
      <Modal
        isOpen={!!inspectSessionId}
        onClose={() => {
          setInspectSessionId(null);
          setSessionDetail(null);
        }}
        title="Diagnostic Audit Trail"
        description={inspectSessionId ? `Session ID: ${inspectSessionId}` : undefined}
        maxWidth="lg"
      >
        {detailLoading ? (
          <div className="py-8">
            <LoadingSpinner message="Retrieving session audit details..." />
          </div>
        ) : detailError ? (
          <ErrorMessage error={detailError} />
        ) : sessionDetail ? (
          <div className="space-y-6">
            {/* Outcome Overview */}
            <div className="p-4 rounded-xl bg-[#FFFCF5]/80 border border-stone-300 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
                  Diagnostic Outcome
                </span>
                <Badge variant="status" value={sessionDetail.status} size="sm" />
              </div>
              <div>
                <h4 className="text-base font-bold text-[#2B2822]">
                  {sessionDetail.final_diagnosis || 'Diagnostic Inconclusive or In Progress'}
                </h4>
                {sessionDetail.summary && (
                  <p className="text-xs text-stone-700 mt-1 leading-relaxed">
                    {sessionDetail.summary}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-stone-300">
                {sessionDetail.diagnosis_category && (
                  <Badge variant="category" value={sessionDetail.diagnosis_category} size="sm" />
                )}
                {sessionDetail.severity && (
                  <Badge variant="severity" value={sessionDetail.severity} size="sm" />
                )}
                <span className="text-xs text-stone-600 ml-auto font-mono">
                  {sessionDetail.traces_count} rules fired
                </span>
              </div>
            </div>

            {/* Answered Questions Timeline */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-stone-700 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-gold-700" />
                Inquiry Question & Answer Log ({sessionDetail.answers.length})
              </h4>

              {sessionDetail.answers.length === 0 ? (
                <p className="text-xs text-stone-600 italic p-3 rounded-lg bg-[#FFFCF5] border border-stone-300">
                  No questions were answered during this session.
                </p>
              ) : (
                <div className="space-y-2.5 max-h-[40vh] overflow-y-auto pr-1">
                  {sessionDetail.answers.map((ans, idx) => (
                    <div
                      key={ans.id}
                      className="p-3 rounded-lg bg-[#FFFCF5] border border-stone-300/80 flex items-start justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-stone-600">
                          Step #{idx + 1} • {ans.question_id}
                        </span>
                        <p className="text-xs text-stone-800 font-medium">{ans.question_text}</p>
                        <span className="text-[10px] text-stone-600">
                          {new Date(ans.answered_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <div>
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                            ans.answer === 'TRUE'
                              ? 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/20'
                              : ans.answer === 'FALSE'
                              ? 'bg-red-500/10 text-red-700 border border-red-500/20'
                              : 'bg-amber-500/10 text-amber-700 border border-amber-500/20'
                          }`}
                        >
                          {ans.answer === 'TRUE' ? 'Yes' : ans.answer === 'FALSE' ? 'No' : 'Unknown'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Direct Navigation Links */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-stone-300">
              {sessionDetail.status === 'IN_PROGRESS' ? (
                <Link to={`/diagnose?session_id=${sessionDetail.id}`}>
                  <Button variant="primary" size="sm">
                    Resume Diagnostic
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to={`/results/${sessionDetail.id}`}>
                    <Button variant="outline" size="sm" icon={<FileText className="w-3.5 h-3.5" />}>
                      View Full Recommendation
                    </Button>
                  </Link>
                  <Link to={`/explain/${sessionDetail.id}`}>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<GitBranch className="w-3.5 h-3.5" />}
                    >
                      Interactive DAG
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteSessionId}
        onClose={() => setDeleteSessionId(null)}
        title="Delete Diagnostic Session"
        description="This action cannot be undone."
        maxWidth="sm"
        footer={
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteSessionId(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isDeleting}
              onClick={handleDeleteConfirm}
              icon={<Trash2 className="w-3.5 h-3.5" />}
            >
              Confirm Delete
            </Button>
          </div>
        }
      >
        <div className="flex items-start gap-3 py-2">
          <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-700">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <p className="text-xs text-stone-700 leading-relaxed">
            Are you sure you want to permanently delete session{' '}
            <span className="font-mono text-[#2B2822] font-semibold">
              {deleteSessionId?.substring(0, 8)}...
            </span>
            ? This will remove all associated user answers, rule traces, and persisted recommendations.
          </p>
        </div>
      </Modal>
    </div>
  );
};

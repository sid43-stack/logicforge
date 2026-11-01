import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import {
  Check,
  X,
  HelpCircle as QuestionIcon,
  RotateCcw,
  Info,
  Terminal,
  Activity,
  ShieldAlert,
} from 'lucide-react';
import { diagnosticsApi } from '../api/diagnostics';
import { Question, WhyExplanation, ApiError } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Modal } from '../components/common/Modal';

export const DiagnosticWizardPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answeredCount, setAnsweredCount] = useState<number>(0);
  const [showWhy, setShowWhy] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<ApiError | string | null>(null);
  const [conflictModalOpen, setConflictModalOpen] = useState<boolean>(false);
  const [conflictMessage, setConflictMessage] = useState<string>('');
  const [restartModalOpen, setRestartModalOpen] = useState<boolean>(false);

  // Initialize or resume session
  const initSession = async () => {
    setLoading(true);
    setError(null);

    const querySessionId = searchParams.get('session_id') || sessionStorage.getItem('netsage_active_session_id');

    if (querySessionId) {
      try {
        const question = await diagnosticsApi.getCurrentQuestion(querySessionId);
        setSessionId(querySessionId);
        setCurrentQuestion(question);
        sessionStorage.setItem('netsage_active_session_id', querySessionId);
        setLoading(false);
        return;
      } catch (err: any) {
        // If session was completed, redirect to results
        if (err?.detail?.includes('COMPLETED') || err?.detail?.includes('INCONCLUSIVE')) {
          sessionStorage.removeItem('netsage_active_session_id');
          navigate(`/results/${querySessionId}`);
          return;
        }
        // If session in conflict
        if (err?.status_code === 409 || err?.detail?.includes('CONFLICT_DETECTED')) {
          setSessionId(querySessionId);
          setConflictMessage(err?.detail || 'Inference halted: Contradictory evidence detected.');
          setConflictModalOpen(true);
          setLoading(false);
          return;
        }
        // Otherwise start fresh
        console.warn('Cannot resume session, starting fresh:', err);
      }
    }

    // Start a fresh session
    try {
      const resp = await diagnosticsApi.startSession();
      setSessionId(resp.session_id);
      setCurrentQuestion(resp.current_question || null);
      setAnsweredCount(0);
      sessionStorage.setItem('netsage_active_session_id', resp.session_id);
      setSearchParams({ session_id: resp.session_id }, { replace: true });

      // If initial session already established diagnosis
      if (resp.status === 'COMPLETED' || resp.status === 'INCONCLUSIVE') {
        sessionStorage.removeItem('netsage_active_session_id');
        navigate(`/results/${resp.session_id}`);
      }
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initSession();
  }, []);

  const handleAnswer = async (answer: 'YES' | 'NO' | 'UNKNOWN') => {
    if (!sessionId || !currentQuestion || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      const resp = await diagnosticsApi.submitAnswer(sessionId, currentQuestion.id, answer);

      setAnsweredCount((prev) => prev + 1);

      if (resp.is_completed || resp.status === 'COMPLETED' || resp.status === 'INCONCLUSIVE') {
        sessionStorage.removeItem('netsage_active_session_id');
        navigate(`/results/${sessionId}`);
        return;
      }

      if (resp.next_question) {
        setCurrentQuestion(resp.next_question);
      } else {
        // If no further question, check result
        navigate(`/results/${sessionId}`);
      }
    } catch (err: any) {
      if (err?.status_code === 409 || err?.error_code === 'CONFLICT_DETECTED') {
        setConflictMessage(
          typeof err?.detail === 'string'
            ? err.detail
            : 'Contradictory evidence was asserted. The expert system detected conflicting premises and safely halted inference.'
        );
        setConflictModalOpen(true);
      } else {
        setError(err);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleRestart = async () => {
    setRestartModalOpen(false);
    if (!sessionId) {
      initSession();
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const resp = await diagnosticsApi.restartSession(sessionId);
      setCurrentQuestion(resp.current_question || null);
      setAnsweredCount(0);
    } catch (err: any) {
      // If restart fails, start fresh session
      sessionStorage.removeItem('netsage_active_session_id');
      initSession();
    } finally {
      setLoading(false);
    }
  };

  const startFreshSession = () => {
    sessionStorage.removeItem('netsage_active_session_id');
    setSearchParams({}, { replace: true });
    setConflictModalOpen(false);
    initSession();
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20">
        <LoadingSpinner message="Consulting production rules & selecting next inquiry..." />
      </div>
    );
  }

  const why: WhyExplanation | undefined | null = currentQuestion?.why_explanation;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      {/* Top Session Progress Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#FFFCF5] border border-[#D8D0C0] rounded-xl px-5 py-3.5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-gold-400 animate-pulse" />
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-stone-700">Session:</span>
            <span className="text-xs font-mono text-stone-600">
              {sessionId ? `${sessionId.substring(0, 8)}...` : 'Initializing'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-stone-600">
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-gold-700" />
            <span>Questions Answered: <strong className="text-[#2B2822]">{answeredCount}</strong></span>
          </div>
          <button
            onClick={() => setRestartModalOpen(true)}
            className="flex items-center gap-1 text-stone-600 hover:text-[#2B2822] transition-colors"
            title="Restart diagnostic session"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {error && <ErrorMessage error={error} onRetry={() => initSession()} />}

      {/* Main Question Card */}
      {currentQuestion && (
        <Card className="border-stone-300 bg-[#FFFCF5] p-6 sm:p-8 space-y-6 shadow-xl">
          {/* Question Metadata Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-300 pb-4">
            <div className="flex items-center gap-2">
              <span data-testid="question-id" className="px-2.5 py-1 rounded-md bg-gold-500/10 border border-gold-500/20 text-gold-700 text-xs font-mono font-bold">
                {currentQuestion.id}
              </span>
              <Badge variant="category" value={currentQuestion.category} size="sm" />
            </div>
            {why && (
              <span className="text-xs text-stone-600 flex items-center gap-1">
                Target: <span className="text-stone-800 font-medium">{why.investigating_hypothesis}</span>
              </span>
            )}
          </div>

          {/* Question Title */}
          <div className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-bold text-[#2B2822] tracking-tight leading-snug">
              {currentQuestion.text}
            </h2>

            {/* Verification Guidance */}
            {currentQuestion.guidance && (
              <div className="rounded-lg bg-[#FFFCF5]/90 border border-stone-300 p-3.5 flex items-start gap-3">
                <Terminal className="w-4 h-4 text-gold-700 flex-shrink-0 mt-0.5" />
                <div className="text-xs leading-relaxed">
                  <span className="font-semibold text-gold-800 block mb-0.5">How to test on your computer:</span>
                  <span className="text-stone-700 font-mono text-[11px]">{currentQuestion.guidance}</span>
                </div>
              </div>
            )}
          </div>

          {/* Answer Choice Buttons */}
          <div className="space-y-3 pt-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-stone-600">
              Select Your Observed Result:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                type="button"
                data-testid="answer-yes"
                disabled={submitting}
                onClick={() => handleAnswer('YES')}
                className="group flex items-center justify-center gap-2.5 py-3.5 px-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-800 font-semibold text-sm transition-all shadow-sm hover:border-emerald-500/50 disabled:opacity-50"
              >
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Check className="w-3.5 h-3.5 text-emerald-700" />
                </div>
                <span>YES</span>
              </button>

              <button
                type="button"
                data-testid="answer-no"
                disabled={submitting}
                onClick={() => handleAnswer('NO')}
                className="group flex items-center justify-center gap-2.5 py-3.5 px-4 rounded-xl border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-800 font-semibold text-sm transition-all shadow-sm hover:border-red-500/50 disabled:opacity-50"
              >
                <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <X className="w-3.5 h-3.5 text-red-700" />
                </div>
                <span>NO</span>
              </button>

              <button
                type="button"
                data-testid="answer-unknown"
                disabled={submitting}
                onClick={() => handleAnswer('UNKNOWN')}
                className="group flex items-center justify-center gap-2.5 py-3.5 px-4 rounded-xl border border-stone-400 bg-[#EAE3D8]/80 hover:bg-[#EAE3D8] text-stone-700 font-medium text-sm transition-all shadow-sm hover:border-stone-500 disabled:opacity-50"
              >
                <div className="w-5 h-5 rounded-full bg-[#D8D0C0] flex items-center justify-center group-hover:scale-110 transition-transform">
                  <QuestionIcon className="w-3.5 h-3.5 text-stone-600" />
                </div>
                <span>NOT SURE</span>
              </button>
            </div>
            <p className="text-[11px] text-stone-600 text-center pt-1">
              Selecting &quot;NOT SURE&quot; marks this condition as UNKNOWN in working memory without falsely assuming it is false.
            </p>
          </div>

          {/* Dynamic WHY Explanation Section */}
          {why && (
            <div className="pt-4 border-t border-stone-300">
              <button
                onClick={() => setShowWhy(!showWhy)}
                className="flex items-center justify-between w-full text-xs font-semibold text-gold-700 hover:text-gold-800 py-1"
              >
                <span className="flex items-center gap-1.5">
                  <Info className="w-4 h-4" />
                  WHY is NetSage asking this question? (Dynamic Expert System Rationale)
                </span>
                <span>{showWhy ? 'Collapse' : 'Expand'}</span>
              </button>

              {showWhy && (
                <div className="mt-3 rounded-xl bg-[#FFFCF5]/80 border border-gold-500/20 p-4 space-y-3 text-xs leading-relaxed animate-fadeIn">
                  <div>
                    <span className="font-semibold text-stone-700 block mb-1">Inference Rationale:</span>
                    <p className="text-stone-600">{why.rationale}</p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-stone-300">
                    <div className="bg-[#F2EEE4]/50 p-2.5 rounded-lg border border-stone-300/80">
                      <span className="font-semibold text-emerald-700 block mb-1">If Answer is YES:</span>
                      <p className="text-stone-600 text-[11px]">{why.impact_if_yes}</p>
                    </div>
                    <div className="bg-[#F2EEE4]/50 p-2.5 rounded-lg border border-stone-300/80">
                      <span className="font-semibold text-rose-700 block mb-1">If Answer is NO:</span>
                      <p className="text-stone-600 text-[11px]">{why.impact_if_no}</p>
                    </div>
                  </div>

                  <div className="text-[10px] text-stone-600 flex items-center justify-between pt-1">
                    <span>Targeted Rule: <strong className="text-gold-800">{why.triggering_rule_id}</strong> ({why.triggering_rule_name})</span>
                    <span>Hypothesis Category: <strong className="text-stone-600">{why.hypothesis_category}</strong></span>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      )}

      {/* Contradiction / Conflict Detected Modal */}
      <Modal
        isOpen={conflictModalOpen}
        onClose={() => setConflictModalOpen(false)}
        title="Diagnostic Conflict Detected"
        description="The inference engine detected contradictory diagnostic evidence."
        footer={
          <div className="flex gap-2">
            {sessionId && (
              <Link to={`/results/${sessionId}`}>
                <Button variant="outline" size="sm">
                  View Conflict Summary
                </Button>
              </Link>
            )}
            <Button variant="primary" size="sm" onClick={startFreshSession}>
              Start Fresh Session
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-800 text-xs flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-red-700 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold block text-red-800">Inference Soundness Rule:</span>
              <p className="leading-relaxed">{conflictMessage}</p>
            </div>
          </div>
          <p className="text-xs text-stone-600 leading-relaxed">
            NetSage strictly refuses to pick a random diagnosis when user answers contradict established network facts.
            Please restart and re-verify your network symptoms.
          </p>
        </div>
      </Modal>

      {/* Restart Confirmation Modal */}
      <Modal
        isOpen={restartModalOpen}
        onClose={() => setRestartModalOpen(false)}
        title="Reset Diagnostic Session?"
        description="This will clear your answered questions for this session."
        footer={
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => setRestartModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" size="sm" onClick={handleRestart}>
              Yes, Reset Session
            </Button>
          </div>
        }
      >
        <p className="text-xs text-stone-700 leading-relaxed">
          Resetting will clear working memory and restart backward-chaining inquiry from the beginning.
        </p>
      </Modal>
    </div>
  );
};

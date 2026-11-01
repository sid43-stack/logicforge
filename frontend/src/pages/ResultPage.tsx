import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  Copy,
  Check,
  Terminal,
  GitBranch,
  ShieldCheck,
  RotateCcw,
  LayoutDashboard,
  ExternalLink,
} from 'lucide-react';
import { diagnosticsApi } from '../api/diagnostics';
import { historyApi } from '../api/history';
import { DiagnosticResult, SessionDetailResponse, ApiError } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const ResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const fetchResults = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    try {
      const [resData, histData] = await Promise.all([
        diagnosticsApi.getResult(id),
        historyApi.getSessionDetail(id).catch(() => null),
      ]);
      setResult(resData);
      setSessionDetail(histData);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [id]);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20">
        <LoadingSpinner message="Retrieving confirmed terminal diagnosis and remediation plan..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 space-y-4">
        <ErrorMessage error={error} onRetry={fetchResults} />
        <div className="flex gap-3">
          <Link to="/diagnose">
            <Button variant="primary" size="sm">Start New Diagnosis</Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="outline" size="sm">Return to Dashboard</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const isCompleted = result.status === 'COMPLETED';
  const isInconclusive = result.status === 'INCONCLUSIVE';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      {/* Session Breadcrumb & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#D8D0C0] pb-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-stone-600">Diagnostic Session:</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#EAE3D8] text-stone-700 border border-stone-400">
            {result.session_id}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="status" value={result.status} />
          {result.severity && <Badge variant="severity" value={result.severity} />}
        </div>
      </div>

      {/* Main Diagnosis Banner */}
      <Card
        className={`border-l-4 ${
          isCompleted
            ? 'border-l-emerald-500 bg-[#FFFCF5]'
            : isInconclusive
            ? 'border-l-amber-500 bg-[#FFFCF5]'
            : 'border-l-red-500 bg-[#FFFCF5]'
        } p-6 sm:p-8 space-y-4 shadow-xl`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-mono font-bold px-2 py-1 rounded bg-[#EAE3D8]/80 text-gold-700 border border-stone-400">
            {result.diagnosis_code || 'CODE_PENDING'}
          </span>
          {result.category && <Badge variant="category" value={result.category} size="sm" />}
        </div>

        <div>
          <div className="flex items-center gap-3">
            {isCompleted ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-700 flex-shrink-0" />
            ) : isInconclusive ? (
              <HelpCircle className="w-8 h-8 text-amber-700 flex-shrink-0" />
            ) : (
              <ShieldAlert className="w-8 h-8 text-red-700 flex-shrink-0" />
            )}
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#2B2822] tracking-tight leading-tight">
              {result.diagnosis_name || 'Inconclusive Diagnostic Outcome'}
            </h1>
          </div>

          <p className="text-sm text-stone-700 mt-3 leading-relaxed">
            {result.summary}
          </p>
        </div>

        {/* Probable Diagnosis Transparency Disclaimer */}
        <div className="rounded-lg bg-[#FFFCF5]/80 border border-stone-300 p-3 text-xs text-stone-600 flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-gold-700 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Expert System Assessment:</strong> This is a probable diagnosis formally deduced by
            production rules based on user-supplied answers. Verify physical cables and router hardware before performing disruptive resets.
          </span>
        </div>
      </Card>

      {/* Recommended Troubleshooting Steps */}
      {result.steps && result.steps.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#2B2822] tracking-tight">
              Actionable Troubleshooting Procedures
            </h2>
            <span className="text-xs text-stone-600 font-mono">
              {result.steps.length} Prioritized Step{result.steps.length > 1 ? 's' : ''}
            </span>
          </div>

          <div className="space-y-4">
            {result.steps.map((step, idx) => (
              <Card key={step.order} className="border-stone-300 bg-[#FFFCF5] p-5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-gold-600/20 border border-gold-500/30 text-gold-800 font-bold text-xs flex items-center justify-center">
                      {step.order}
                    </span>
                    <h3 className="text-sm font-semibold text-stone-900">{step.action}</h3>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {step.requires_admin && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-800 border border-amber-500/20">
                        Admin Required
                      </span>
                    )}
                    {step.is_disruptive && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-800 border border-red-500/20">
                        Temporary Disruption
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-stone-700 leading-relaxed">{step.description}</p>

                {/* Optional CLI Command Block */}
                {step.command && (
                  <div className="rounded-lg bg-[#F2EEE4] border border-stone-300 p-3 flex items-center justify-between gap-2 font-mono text-xs">
                    <div className="flex items-center gap-2 overflow-x-auto text-emerald-700">
                      <Terminal className="w-4 h-4 text-stone-600 flex-shrink-0" />
                      <code>{step.command}</code>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(step.command!, idx)}
                      className="text-xs px-2 py-1 text-stone-600 hover:text-[#2B2822]"
                      title="Copy command"
                    >
                      {copiedIndex === idx ? (
                        <Check className="w-3.5 h-3.5 text-emerald-700" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </Button>
                  </div>
                )}

                <div className="text-[11px] text-stone-600 flex items-center gap-1 pt-1">
                  <span className="text-stone-600 font-medium">Expected Result:</span>
                  <span>{step.expected_outcome}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Disruption Warnings & Escalation Advice */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {result.warnings && result.warnings.length > 0 && (
          <Card className="border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
            <h4 className="text-xs font-semibold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-700" />
              Precautionary Warnings
            </h4>
            <ul className="text-xs text-stone-700 space-y-1.5 list-disc list-inside">
              {result.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </Card>
        )}

        {result.escalation_advice && (
          <Card className="border-gold-500/20 bg-gold-500/5 p-4 space-y-2">
            <h4 className="text-xs font-semibold text-gold-800 uppercase tracking-wider flex items-center gap-1.5">
              <ExternalLink className="w-4 h-4 text-gold-700" />
              Escalation Guidance
            </h4>
            <p className="text-xs text-stone-700 leading-relaxed">
              {result.escalation_advice}
            </p>
          </Card>
        )}
      </div>

      {/* Supporting Diagnostic Evidence (Answered Questions) */}
      {sessionDetail && sessionDetail.answers && sessionDetail.answers.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-bold text-[#2B2822] tracking-tight">
            User Diagnostic Evidence Asserted
          </h2>
          <div className="rounded-xl bg-[#FFFCF5] border border-[#D8D0C0] divide-y divide-[#D8D0C0] overflow-hidden text-xs">
            {sessionDetail.answers.map((ans) => (
              <div key={ans.id} className="p-3.5 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="font-mono text-[10px] text-gold-700 font-bold px-1.5 py-0.2 rounded bg-gold-500/10 border border-gold-500/20">
                    {ans.question_id}
                  </span>
                  <p className="text-stone-700 mt-1">{ans.question_text}</p>
                </div>
                <span
                  className={`font-semibold px-2 py-0.5 rounded text-[11px] font-mono ${
                    ans.answer === 'YES'
                      ? 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/20'
                      : ans.answer === 'NO'
                      ? 'bg-red-500/10 text-red-700 border border-red-500/20'
                      : 'bg-[#EAE3D8] text-stone-600 border border-stone-400'
                  }`}
                >
                  {ans.answer}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Primary Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#D8D0C0]">
        <Link to={`/explain/${result.session_id}`} className="w-full sm:w-auto">
          <Button
            variant="primary"
            size="md"
            icon={<GitBranch className="w-4 h-4" />}
            className="w-full sm:w-auto shadow-md shadow-gold-600/20"
          >
            View Full Inference DAG & Narrative
          </Button>
        </Link>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Link to="/diagnose" className="w-full sm:w-auto">
            <Button variant="outline" size="md" icon={<RotateCcw className="w-4 h-4" />} className="w-full sm:w-auto">
              Start Another Diagnosis
            </Button>
          </Link>
          <Link to="/dashboard" className="w-full sm:w-auto">
            <Button variant="ghost" size="md" icon={<LayoutDashboard className="w-4 h-4" />} className="w-full sm:w-auto">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

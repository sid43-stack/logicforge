import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Play,
  CheckCircle2,
  HelpCircle,
  Layers,
  ArrowRight,
  Server,
  Network,
  Globe,
  Wifi,
  Gauge,
  Radio,
  Clock,
  Activity,
  RotateCcw,
} from 'lucide-react';
import { historyApi } from '../api/history';
import { knowledgeApi } from '../api/knowledge';
import { SessionSummary, KnowledgeStats } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const DashboardPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [historyData, knowledgeStats] = await Promise.all([
        historyApi.listSessions(0, 10),
        knowledgeApi.getStats(),
      ]);
      setSessions(historyData.items);
      setStats(knowledgeStats);
    } catch (err: any) {
      setError(err?.detail || 'Failed to retrieve dashboard metrics from backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const totalSessionsCount = sessions.length;
  const completedCount = sessions.filter((s) => s.status === 'COMPLETED').length;
  const inconclusiveCount = sessions.filter((s) => s.status === 'INCONCLUSIVE').length;

  const categories = [
    { id: 'IP_DHCP', name: 'IP & DHCP', icon: <Server className="w-4 h-4 text-gold-700" />, rules: stats?.rules_by_category['IP_DHCP'] || 5 },
    { id: 'GATEWAY', name: 'Gateway / Segment', icon: <Network className="w-4 h-4 text-gold-700" />, rules: stats?.rules_by_category['GATEWAY'] || 5 },
    { id: 'DNS', name: 'DNS Resolution', icon: <Globe className="w-4 h-4 text-gold-700" />, rules: stats?.rules_by_category['DNS'] || 5 },
    { id: 'WIFI', name: 'Wi-Fi RF Link', icon: <Wifi className="w-4 h-4 text-emerald-700" />, rules: stats?.rules_by_category['WIFI'] || 5 },
    { id: 'PERFORMANCE', name: 'Latency & Buffering', icon: <Gauge className="w-4 h-4 text-amber-700" />, rules: stats?.rules_by_category['PERFORMANCE'] || 4 },
    { id: 'ISP', name: 'WAN / ISP Line', icon: <Radio className="w-4 h-4 text-gold-700" />, rules: stats?.rules_by_category['ISP'] || 4 },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8D0C0] pb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#2B2822] tracking-tight">Expert System Dashboard</h1>
          <p className="text-sm text-stone-600 mt-1">
            Real-time inference overview, active diagnostic sessions, and verified knowledge base rules.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<RotateCcw className="w-3.5 h-3.5" />}
            onClick={fetchDashboardData}
          >
            Refresh
          </Button>
          <Link to="/diagnose">
            <Button variant="primary" size="md" icon={<Play className="w-4 h-4" />}>
              Start New Diagnosis
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorMessage error={error} onRetry={fetchDashboardData} />}

      {loading ? (
        <LoadingSpinner message="Querying expert system status and session history..." />
      ) : (
        <>
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-stone-300 bg-[#FFFCF5]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
                  Total Sessions
                </span>
                <Clock className="w-4 h-4 text-stone-600" />
              </div>
              <p className="text-3xl font-bold text-[#2B2822] mt-2">{totalSessionsCount}</p>
              <p className="text-xs text-stone-600 mt-1">Recorded in persistent database</p>
            </Card>

            <Card className="border-stone-300 bg-[#FFFCF5]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                  Confirmed Diagnoses
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              </div>
              <p className="text-3xl font-bold text-emerald-700 mt-2">{completedCount}</p>
              <p className="text-xs text-stone-600 mt-1">Terminal production rules fired</p>
            </Card>

            <Card className="border-stone-300 bg-[#FFFCF5]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
                  Inconclusive / Inquiries
                </span>
                <HelpCircle className="w-4 h-4 text-amber-700" />
              </div>
              <p className="text-3xl font-bold text-amber-700 mt-2">{inconclusiveCount}</p>
              <p className="text-xs text-stone-600 mt-1">Rules exhausted without terminal diagnosis</p>
            </Card>

            <Card className="border-stone-300 bg-[#FFFCF5]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gold-700 uppercase tracking-wider">
                  Production Rules
                </span>
                <Layers className="w-4 h-4 text-gold-700" />
              </div>
              <p className="text-3xl font-bold text-gold-700 mt-2">{stats?.total_rules ?? 28}</p>
              <p className="text-xs text-stone-600 mt-1">
                {stats?.terminal_rules_count ?? 13} Terminal • {stats?.intermediate_rules_count ?? 15} Intermediate
              </p>
            </Card>
          </div>

          {/* Diagnostic Categories Overview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-[#2B2822] tracking-tight">Diagnostic Problem Categories</h2>
              <Link to="/knowledge" className="text-xs font-semibold text-gold-700 hover:text-gold-800 flex items-center gap-1">
                Knowledge Explorer <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {categories.map((cat) => (
                <div
                  key={cat.id}
                  className="p-3.5 rounded-xl bg-[#FFFCF5] border border-stone-300/80 flex flex-col justify-between space-y-2 hover:border-stone-400 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="p-1.5 rounded-lg bg-[#EAE3D8]">{cat.icon}</div>
                    <span className="text-[10px] font-mono text-stone-600 px-1.5 py-0.5 rounded bg-[#EAE3D8]">
                      {cat.rules} rules
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-stone-800">{cat.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Diagnostic History */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-[#2B2822] tracking-tight">Recent Diagnostic Sessions</h2>
                <p className="text-xs text-stone-600">Past troubleshooting workflows and verified inference outcomes.</p>
              </div>
              <Link to="/history" className="text-xs font-semibold text-gold-700 hover:text-gold-800 flex items-center gap-1">
                View Full History <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {sessions.length === 0 ? (
              <Card className="text-center py-10 space-y-3">
                <Activity className="w-8 h-8 text-stone-600 mx-auto" />
                <h3 className="text-sm font-semibold text-stone-700">No diagnostic sessions recorded yet</h3>
                <p className="text-xs text-stone-600 max-w-sm mx-auto">
                  Start your first diagnostic session to run dynamic inference and identify network faults.
                </p>
                <div className="pt-2">
                  <Link to="/diagnose">
                    <Button variant="primary" size="sm" icon={<Play className="w-3.5 h-3.5" />}>
                      Begin First Diagnosis
                    </Button>
                  </Link>
                </div>
              </Card>
            ) : (
              <div className="bg-[#FFFCF5] border border-[#D8D0C0] rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#FFFCF5]/80 border-b border-[#D8D0C0] text-stone-600 uppercase tracking-wider font-semibold">
                      <tr>
                        <th className="py-3 px-4">Session ID</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4">Diagnosis / Outcome</th>
                        <th className="py-3 px-4">Severity</th>
                        <th className="py-3 px-4">Questions Answered</th>
                        <th className="py-3 px-4">Date / Time</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#D8D0C0] text-stone-700">
                      {sessions.map((sess) => (
                        <tr key={sess.id} className="hover:bg-[#EAE3D8]/40 transition-colors">
                          <td className="py-3 px-4 font-mono text-[11px] text-stone-600">
                            {sess.id.substring(0, 8)}...
                          </td>
                          <td className="py-3 px-4">
                            <Badge variant="status" value={sess.status} size="sm" />
                          </td>
                          <td className="py-3 px-4 font-medium text-stone-800">
                            {sess.final_diagnosis || (
                              <span className="text-stone-600 italic">In progress...</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            {sess.severity ? (
                              <Badge variant="severity" value={sess.severity} size="sm" />
                            ) : (
                              <span className="text-stone-600">—</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-stone-600">
                            {sess.answers_count} questions
                          </td>
                          <td className="py-3 px-4 text-stone-600">
                            {new Date(sess.created_at).toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-right space-x-2">
                            {sess.status === 'COMPLETED' || sess.status === 'INCONCLUSIVE' ? (
                              <>
                                <Link to={`/results/${sess.id}`}>
                                  <Button variant="outline" size="sm" className="text-xs px-2.5 py-1">
                                    Result
                                  </Button>
                                </Link>
                                <Link to={`/explain/${sess.id}`}>
                                  <Button variant="ghost" size="sm" className="text-xs px-2.5 py-1 text-gold-700">
                                    DAG Tree
                                  </Button>
                                </Link>
                              </>
                            ) : (
                              <Link to={`/diagnose?session_id=${sess.id}`}>
                                <Button variant="primary" size="sm" className="text-xs px-2.5 py-1">
                                  Resume
                                </Button>
                              </Link>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

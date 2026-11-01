import React, { useEffect, useState, useMemo } from 'react';
import {
  Database,
  Layers,
  GitFork,
  Search,
  CheckCircle2,
  Cpu,
  BookOpen,
  Zap,
} from 'lucide-react';
import { knowledgeApi } from '../api/knowledge';
import { Fact, ProductionRule, KnowledgeStats } from '../types';
import { Card, CardHeader } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export const KnowledgeExplorerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'facts' | 'rules' | 'topology'>('facts');

  const [facts, setFacts] = useState<Fact[]>([]);
  const [rules, setRules] = useState<ProductionRule[]>([]);
  const [stats, setStats] = useState<KnowledgeStats | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters for Facts
  const [factCategory, setFactCategory] = useState<string>('ALL');
  const [factSourceType, setFactSourceType] = useState<string>('ALL');
  const [factSearch, setFactSearch] = useState<string>('');

  // Filters for Rules
  const [ruleCategory, setRuleCategory] = useState<string>('ALL');
  const [ruleClassification, setRuleClassification] = useState<string>('ALL');
  const [ruleSearch, setRuleSearch] = useState<string>('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [fetchedFacts, fetchedRules, fetchedStats] = await Promise.all([
        knowledgeApi.getFacts(),
        knowledgeApi.getRules(),
        knowledgeApi.getStats(),
      ]);
      setFacts(fetchedFacts);
      setRules(fetchedRules);
      setStats(fetchedStats);
    } catch (err: any) {
      setError(err?.detail || 'Failed to load knowledge base and production rule data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered facts calculation
  const filteredFacts = useMemo(() => {
    return facts.filter((f) => {
      const matchCat = factCategory === 'ALL' || f.category.toUpperCase() === factCategory.toUpperCase();
      const matchSource = factSourceType === 'ALL' || f.source_type.toUpperCase() === factSourceType.toUpperCase();
      const q = factSearch.toLowerCase().trim();
      const matchQuery =
        !q ||
        f.id.toLowerCase().includes(q) ||
        f.key.toLowerCase().includes(q) ||
        f.statement.toLowerCase().includes(q) ||
        f.description.toLowerCase().includes(q);

      return matchCat && matchSource && matchQuery;
    });
  }, [facts, factCategory, factSourceType, factSearch]);

  // Filtered rules calculation
  const filteredRules = useMemo(() => {
    return rules.filter((r) => {
      const matchCat = ruleCategory === 'ALL' || r.category.toUpperCase() === ruleCategory.toUpperCase();
      const matchClass =
        ruleClassification === 'ALL' || r.classification.toUpperCase() === ruleClassification.toUpperCase();
      const q = ruleSearch.toLowerCase().trim();
      const matchQuery =
        !q ||
        r.id.toLowerCase().includes(q) ||
        r.name.toLowerCase().includes(q) ||
        r.explanation.toLowerCase().includes(q) ||
        Object.keys(r.conclusions).some((k) => k.toLowerCase().includes(q)) ||
        r.conditions.some((c) => c.fact_key.toLowerCase().includes(q));

      return matchCat && matchClass && matchQuery;
    });
  }, [rules, ruleCategory, ruleClassification, ruleSearch]);

  const categories = [
    { label: 'All Categories', value: 'ALL' },
    { label: 'IP & DHCP', value: 'IP_DHCP' },
    { label: 'Gateway', value: 'GATEWAY' },
    { label: 'DNS', value: 'DNS' },
    { label: 'Wi-Fi', value: 'WIFI' },
    { label: 'Performance', value: 'PERFORMANCE' },
    { label: 'ISP / WAN', value: 'ISP' },
    { label: 'General', value: 'GENERAL' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8D0C0] pb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#FFFCF5] border border-stone-300 text-gold-700">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[#2B2822] tracking-tight">
              Interactive Knowledge Base Explorer
            </h1>
            <p className="text-sm text-stone-600">
              Inspect verified domain facts, production rules, conditional antecedents, and rule chaining graph topology.
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center p-1 rounded-xl bg-[#FFFCF5] border border-stone-300 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('facts')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'facts'
                ? 'bg-gold-600 text-[#2B2822] shadow-sm'
                : 'text-stone-600 hover:text-stone-800'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Domain Facts ({facts.length})
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'rules'
                ? 'bg-gold-600 text-[#2B2822] shadow-sm'
                : 'text-stone-600 hover:text-stone-800'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Production Rules ({rules.length})
          </button>
          <button
            onClick={() => setActiveTab('topology')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === 'topology'
                ? 'bg-gold-600 text-[#2B2822] shadow-sm'
                : 'text-stone-600 hover:text-stone-800'
            }`}
          >
            <GitFork className="w-3.5 h-3.5" />
            Dependency Topology
          </button>
        </div>
      </div>

      {error && <ErrorMessage error={error} onRetry={loadData} />}

      {loading ? (
        <LoadingSpinner message="Parsing knowledge base facts and rule base models..." />
      ) : (
        <>
          {/* TAB 1: DOMAIN FACTS EXPLORER */}
          {activeTab === 'facts' && (
            <div className="space-y-6">
              {/* Filter controls */}
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-[#FFFCF5] border border-[#D8D0C0] p-4 rounded-xl">
                {/* Category & Source Type Filters */}
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-stone-600 font-medium">Category:</span>
                    <select
                      value={factCategory}
                      onChange={(e) => setFactCategory(e.target.value)}
                      className="bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-stone-800 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      {categories.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-stone-600 font-medium">Source Tier:</span>
                    <select
                      value={factSourceType}
                      onChange={(e) => setFactSourceType(e.target.value)}
                      className="bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-stone-800 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      <option value="ALL">All Source Tiers</option>
                      <option value="STATIC_DOMAIN">Static Domain Knowledge</option>
                      <option value="USER_INPUT">User Diagnostic Evidence</option>
                      <option value="RULE_DERIVED">Rule-Derived Facts</option>
                    </select>
                  </div>
                </div>

                {/* Search */}
                <div className="relative min-w-[280px]">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-stone-600" />
                  <input
                    type="text"
                    placeholder="Search facts by key, statement, or ID..."
                    value={factSearch}
                    onChange={(e) => setFactSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-1.5 bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-[#2B2822] placeholder-stone-500 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
              </div>

              {/* Source Tier Legend Card */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-gold-500/5 border border-gold-500/20 flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-gold-400" />
                  <div>
                    <h4 className="text-xs font-semibold text-gold-800">STATIC_DOMAIN</h4>
                    <p className="text-[11px] text-stone-600">Fixed RFC/domain standards and defaults</p>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-gold-500/5 border border-gold-500/20 flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-gold-400" />
                  <div>
                    <h4 className="text-xs font-semibold text-gold-800">USER_INPUT</h4>
                    <p className="text-[11px] text-stone-600">Diagnostic observations gathered via questions</p>
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <div>
                    <h4 className="text-xs font-semibold text-emerald-800">RULE_DERIVED</h4>
                    <p className="text-[11px] text-stone-600">Asserted by forward inference execution</p>
                  </div>
                </div>
              </div>

              {/* Facts Grid */}
              {filteredFacts.length === 0 ? (
                <Card className="text-center py-12 text-stone-600 text-xs">
                  No facts match the current search and filter criteria.
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredFacts.map((fact) => (
                    <Card
                      key={fact.id}
                      className="flex flex-col justify-between space-y-3 border-stone-300/80 hover:border-stone-400 transition-all bg-[#FFFCF5]"
                    >
                      <div className="space-y-2">
                        {/* Header Badges */}
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-xs font-bold text-stone-700 bg-[#EAE3D8]/80 px-2 py-0.5 rounded border border-stone-400">
                            {fact.id}
                          </span>
                          <Badge variant="tier" value={fact.source_type} size="sm" />
                        </div>

                        {/* Fact Key */}
                        <div className="font-mono text-[11px] text-gold-700 font-semibold break-all">
                          {fact.key}
                        </div>

                        {/* Statement */}
                        <p className="text-xs font-semibold text-stone-900 leading-snug">
                          {fact.statement}
                        </p>

                        {/* Description */}
                        <p className="text-[11px] text-stone-600 leading-relaxed">
                          {fact.description}
                        </p>
                      </div>

                      {/* Diagnostic Relevance */}
                      <div className="pt-2 border-t border-stone-300/80">
                        <div className="flex items-center justify-between text-[10px] text-stone-600 mb-1">
                          <span className="font-semibold uppercase tracking-wider">Diagnostic Relevance</span>
                          <Badge variant="category" value={fact.category} size="sm" />
                        </div>
                        <p className="text-[11px] text-stone-600 italic">
                          {fact.diagnostic_relevance}
                        </p>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PRODUCTION RULES EXPLORER */}
          {activeTab === 'rules' && (
            <div className="space-y-6">
              {/* Filter controls */}
              <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-[#FFFCF5] border border-[#D8D0C0] p-4 rounded-xl">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-stone-600 font-medium">Category:</span>
                    <select
                      value={ruleCategory}
                      onChange={(e) => setRuleCategory(e.target.value)}
                      className="bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-stone-800 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      {categories.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-stone-600 font-medium">Classification:</span>
                    <select
                      value={ruleClassification}
                      onChange={(e) => setRuleClassification(e.target.value)}
                      className="bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-stone-800 px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-gold-500"
                    >
                      <option value="ALL">All Classifications</option>
                      <option value="INTERMEDIATE">Intermediate Rule</option>
                      <option value="TERMINAL_DIAGNOSIS">Terminal Diagnosis</option>
                    </select>
                  </div>
                </div>

                {/* Search */}
                <div className="relative min-w-[280px]">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-stone-600" />
                  <input
                    type="text"
                    placeholder="Search rules by ID, name, or fact key..."
                    value={ruleSearch}
                    onChange={(e) => setRuleSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-1.5 bg-[#FFFCF5] border border-stone-400 rounded-lg text-xs text-[#2B2822] placeholder-stone-500 focus:outline-none focus:ring-1 focus:ring-gold-500"
                  />
                </div>
              </div>

              {/* Rules List */}
              {filteredRules.length === 0 ? (
                <Card className="text-center py-12 text-stone-600 text-xs">
                  No production rules match the current search and filter criteria.
                </Card>
              ) : (
                <div className="space-y-4">
                  {filteredRules.map((rule) => {
                    const isTerminal = rule.classification === 'TERMINAL_DIAGNOSIS';

                    return (
                      <Card
                        key={rule.id}
                        className={`space-y-4 border-stone-300 bg-[#FFFCF5] hover:border-stone-400 transition-colors ${
                          isTerminal ? 'border-l-4 border-l-emerald-500' : 'border-l-4 border-l-gold-500'
                        }`}
                      >
                        {/* Header line */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D8D0C0] pb-3">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-xs font-bold text-[#2B2822] bg-[#EAE3D8] px-2.5 py-1 rounded border border-stone-400">
                              {rule.id}
                            </span>
                            <h3 className="text-sm font-bold text-[#2B2822]">{rule.name}</h3>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-stone-600 px-2 py-0.5 rounded bg-[#EAE3D8] border border-stone-400">
                              Priority: {rule.priority}
                            </span>
                            <Badge
                              variant="category"
                              value={rule.category}
                              size="sm"
                            />
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                                isTerminal
                                  ? 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20'
                                  : 'bg-gold-500/10 text-gold-700 border-gold-500/20'
                              }`}
                            >
                              {isTerminal ? 'Terminal Diagnosis' : 'Intermediate'}
                            </span>
                          </div>
                        </div>

                        {/* Condition & Conclusion Blocks */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {/* IF Conditions (Antecedents) */}
                          <div className="space-y-2 p-3.5 rounded-lg bg-[#FFFCF5]/80 border border-stone-300">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1">
                              <Zap className="w-3 h-3" />
                              IF (Antecedent Conditions):
                            </span>
                            <div className="space-y-1.5 font-mono text-xs">
                              {rule.conditions.map((cond, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="flex items-center gap-2 p-1.5 rounded bg-[#EAE3D8]/60 border border-stone-400/60 text-stone-700"
                                >
                                  <span className="text-gold-700 font-semibold">{cond.fact_key}</span>
                                  <span className="text-amber-700 font-bold">{cond.operator}</span>
                                  <span className="text-emerald-700 font-bold">
                                    {String(cond.expected_value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* THEN Conclusions (Consequents) */}
                          <div className="space-y-2 p-3.5 rounded-lg bg-[#FFFCF5]/80 border border-stone-300">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              THEN (Consequent Assertions):
                            </span>
                            <div className="space-y-1.5 font-mono text-xs">
                              {Object.entries(rule.conclusions).map(([factKey, val], kIdx) => (
                                <div
                                  key={kIdx}
                                  className="flex items-center gap-2 p-1.5 rounded bg-[#EAE3D8]/60 border border-stone-400/60 text-stone-700"
                                >
                                  <span className="text-gold-700 font-semibold">{factKey}</span>
                                  <span className="text-stone-600">=</span>
                                  <span className="text-emerald-700 font-bold">{String(val)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Explanation Narrative */}
                        <div className="text-xs text-stone-600 leading-relaxed bg-[#FFFCF5]/40 p-3 rounded-lg border border-stone-300/60">
                          <span className="font-semibold text-stone-700 block mb-0.5">
                            Domain Rationale:
                          </span>
                          {rule.explanation}
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: GRAPH TOPOLOGY & STRUCTURAL METRICS */}
          {activeTab === 'topology' && (
            <div className="space-y-6">
              {/* Metric Highlights */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Total Facts
                  </span>
                  <p className="text-2xl font-bold text-[#2B2822] mt-1">{stats?.total_facts ?? 30}</p>
                  <span className="text-[10px] text-stone-600">Domain axioms</span>
                </Card>

                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Total Rules
                  </span>
                  <p className="text-2xl font-bold text-gold-700 mt-1">{stats?.total_rules ?? 28}</p>
                  <span className="text-[10px] text-stone-600">Production rules</span>
                </Card>

                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Intermediate
                  </span>
                  <p className="text-2xl font-bold text-gold-700 mt-1">
                    {stats?.intermediate_rules_count ?? 15}
                  </p>
                  <span className="text-[10px] text-stone-600">Multi-level chaining</span>
                </Card>

                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Terminal Rules
                  </span>
                  <p className="text-2xl font-bold text-emerald-700 mt-1">
                    {stats?.terminal_rules_count ?? 13}
                  </p>
                  <span className="text-[10px] text-stone-600">Root-cause diagnoses</span>
                </Card>

                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Chaining Paths
                  </span>
                  <p className="text-2xl font-bold text-amber-700 mt-1">
                    {stats?.chaining_paths_count ?? 21}
                  </p>
                  <span className="text-[10px] text-stone-600">Acyclic paths</span>
                </Card>

                <Card className="border-stone-300 bg-[#FFFCF5] text-center p-4">
                  <span className="text-[10px] font-bold text-stone-600 uppercase tracking-wider">
                    Max Depth
                  </span>
                  <p className="text-2xl font-bold text-gold-700 mt-1">
                    {stats?.max_chaining_depth ?? 3}
                  </p>
                  <span className="text-[10px] text-stone-600">Inference cascade</span>
                </Card>
              </div>

              {/* Categorical Distribution Charts / Tables */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Rules by Category */}
                <Card className="border-stone-300 bg-[#FFFCF5] space-y-4">
                  <CardHeader
                    title="Production Rules per Category"
                    subtitle="Distribution of expert rules across network functional domains"
                    icon={<Layers className="w-4 h-4 text-gold-700" />}
                  />
                  <div className="space-y-3">
                    {stats &&
                      Object.entries(stats.rules_by_category).map(([cat, count]) => {
                        const pct = Math.round((count / stats.total_rules) * 100);
                        return (
                          <div key={cat} className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-medium text-stone-700">{cat.replace('_', ' ')}</span>
                              <span className="font-mono text-stone-600">
                                {count} rules ({pct}%)
                              </span>
                            </div>
                            <div className="w-full bg-[#EAE3D8] h-2 rounded-full overflow-hidden">
                              <div
                                className="bg-gold-500 h-full rounded-full transition-all duration-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </Card>

                {/* Facts by Source Type */}
                <Card className="border-stone-300 bg-[#FFFCF5] space-y-4">
                  <CardHeader
                    title="Fact Source Classification"
                    subtitle="Truth maintenance provenance partitioning"
                    icon={<Database className="w-4 h-4 text-emerald-700" />}
                  />
                  <div className="space-y-4">
                    {stats &&
                      Object.entries(stats.facts_by_source_type).map(([tier, count]) => {
                        const pct = Math.round((count / stats.total_facts) * 100);
                        const tierColor =
                          tier === 'STATIC_DOMAIN'
                            ? 'bg-gold-500'
                            : tier === 'USER_INPUT'
                            ? 'bg-gold-500'
                            : 'bg-emerald-500';

                        return (
                          <div key={tier} className="space-y-1.5 p-3 rounded-lg bg-[#FFFCF5] border border-stone-300">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-mono font-semibold text-stone-800">{tier}</span>
                              <span className="font-mono text-stone-600">
                                {count} facts ({pct}%)
                              </span>
                            </div>
                            <div className="w-full bg-[#EAE3D8] h-2 rounded-full overflow-hidden">
                              <div
                                className={`${tierColor} h-full rounded-full transition-all duration-500`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </Card>
              </div>

              {/* Chaining Cascade Architecture Architecture Callout */}
              <div className="p-5 rounded-xl bg-[#FFFCF5]/90 border border-stone-300 space-y-4">
                <div className="flex items-center gap-2.5">
                  <Cpu className="w-5 h-5 text-gold-700" />
                  <h3 className="text-sm font-bold text-[#2B2822]">
                    Multi-Level Chaining & Acyclic Dependency Guarantees
                  </h3>
                </div>

                <p className="text-xs text-stone-700 leading-relaxed">
                  NetSage implements an automated Tarjan / topological cycle detection pass during engine initialization.
                  The knowledge base comprises <span className="font-semibold text-[#2B2822]">21 distinct chaining paths</span> with a
                  maximum inference depth of <span className="font-semibold text-[#2B2822]">3</span>, guaranteeing deterministic termination without recursive infinite loops.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-3 rounded-lg bg-[#FFFCF5] border border-[#D8D0C0] space-y-1">
                    <span className="text-[10px] font-bold text-gold-700 uppercase">Level 1: Inquiry</span>
                    <p className="text-xs text-stone-700">
                      User diagnostic observations asserted into Working Memory with origin <code className="text-gold-800">USER_INPUT</code>.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#FFFCF5] border border-[#D8D0C0] space-y-1">
                    <span className="text-[10px] font-bold text-gold-700 uppercase">Level 2: Intermediate</span>
                    <p className="text-xs text-stone-700">
                      Forward chaining derives intermediate state facts (e.g. <code className="text-gold-800">ip_configuration_issue</code>) without terminating.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#FFFCF5] border border-[#D8D0C0] space-y-1">
                    <span className="text-[10px] font-bold text-emerald-700 uppercase">Level 3: Terminal</span>
                    <p className="text-xs text-stone-700">
                      Terminal rules consume derived facts and conclude verified root causes (e.g. <code className="text-emerald-800">DHCP_SERVER_UNRESPONSIVE</code>).
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

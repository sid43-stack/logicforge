import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import {
  GitBranch,
  Layers,
  CheckCircle2,
  ListOrdered,
  Info,
  FileText,
} from 'lucide-react';
import { diagnosticsApi } from '../api/diagnostics';
import { ExplanationResponse, InferenceTreeNode, ApiError } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

// Custom Node Layout using Dagre
const getLayoutedElements = (rawNodes: InferenceTreeNode[], rawEdges: any[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: 'LR', ranksep: 90, nodesep: 50 });

  rawNodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 240, height: 90 });
  });

  rawEdges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const nodes: Node[] = rawNodes.map((n) => {
    const nodeWithPos = dagreGraph.node(n.id) || { x: 0, y: 0 };

    // Determine visual style according to node type
    let borderClass = 'border-stone-400 bg-[#FFFCF5] text-stone-800';
    let typeBadge = 'Fact';
    let badgeBg = 'bg-[#EAE3D8] text-stone-600';

    if (n.type === 'USER_FACT') {
      borderClass = 'border-gold-500/40 bg-[#F6F1E7] text-gold-800 shadow-sm shadow-gold-900/20';
      typeBadge = 'User Fact';
      badgeBg = 'bg-gold-500/10 text-gold-700 border border-gold-500/30';
    } else if (n.type === 'RULE') {
      borderClass = 'border-gold-500/40 bg-[#F2EBDD] text-gold-800 shadow-sm shadow-gold-900/20';
      typeBadge = 'Rule';
      badgeBg = 'bg-gold-500/10 text-gold-700 border border-gold-500/30';
    } else if (n.type === 'DERIVED_FACT') {
      borderClass = 'border-emerald-500/40 bg-[#E8F0E6] text-emerald-800 shadow-sm shadow-emerald-900/20';
      typeBadge = 'Derived Fact';
      badgeBg = 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/30';
    } else if (n.type === 'TERMINAL_DIAGNOSIS') {
      borderClass = 'border-amber-500/50 bg-[#F4EAD3] text-amber-800 shadow-md shadow-amber-900/30 ring-1 ring-amber-500/20';
      typeBadge = 'Terminal Diagnosis';
      badgeBg = 'bg-amber-500/20 text-amber-800 border border-amber-500/40 font-bold';
    }

    return {
      id: n.id,
      position: {
        x: (nodeWithPos.x || 0) - 120,
        y: (nodeWithPos.y || 0) - 45,
      },
      data: {
        label: (
          <div className="p-3 text-left space-y-1.5 w-[220px]">
            <div className="flex items-center justify-between">
              <span className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded ${badgeBg}`}>
                {typeBadge}
              </span>
              <span className="text-[10px] font-semibold text-stone-600">{n.status}</span>
            </div>
            <p className="text-xs font-semibold leading-snug line-clamp-2">{n.label}</p>
          </div>
        ),
        rawNode: n,
      },
      style: {
        borderRadius: '12px',
        border: '1px solid',
        padding: 0,
        width: 220,
      },
      className: borderClass,
    };
  });

  const edges: Edge[] = rawEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label || undefined,
    animated: true,
    style: { stroke: '#C9A64B', strokeWidth: 1.5 },
    labelStyle: { fill: '#746D62', fontSize: 10, fontFamily: 'monospace' },
    labelBgStyle: { fill: '#FFFCF5', fillOpacity: 0.9 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#C9A64B',
      width: 15,
      height: 15,
    },
  }));

  return { nodes, edges };
};

export const ExplanationCenterPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | string | null>(null);
  const [selectedNode, setSelectedNode] = useState<InferenceTreeNode | null>(null);
  const [activeTab, setActiveTab] = useState<'DAG' | 'NARRATIVE' | 'FACTS'>('DAG');

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const fetchExplanation = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    try {
      const data = await diagnosticsApi.getExplanation(id);
      setExplanation(data);

      if (data.inference_tree && data.inference_tree.nodes.length > 0) {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          data.inference_tree.nodes,
          data.inference_tree.edges
        );
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
      }
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExplanation();
  }, [id]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (node.data?.rawNode) {
      setSelectedNode(node.data.rawNode);
    }
  }, []);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20">
        <LoadingSpinner message="Generating inference DAG tree and reasoning narrative..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 space-y-4">
        <ErrorMessage error={error} onRetry={fetchExplanation} />
        <Link to="/history">
          <Button variant="outline" size="sm">Back to History</Button>
        </Link>
      </div>
    );
  }

  if (!explanation) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8D0C0] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-[#2B2822] tracking-tight">Explanation Center</h1>
            <Badge variant="status" value={explanation.status} size="sm" />
          </div>
          <p className="text-xs text-stone-600 mt-1">
            Session: <span className="font-mono text-stone-700">{explanation.session_id}</span> •{' '}
            {explanation.fired_rules_count} Production Rule{explanation.fired_rules_count === 1 ? '' : 's'} Fired
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link to={`/results/${explanation.session_id}`}>
            <Button variant="outline" size="sm">View Diagnosis & Action Plan</Button>
          </Link>
          <Link to="/diagnose">
            <Button variant="primary" size="sm">New Diagnosis</Button>
          </Link>
        </div>
      </div>

      {/* Tabs Switcher */}
      <div className="flex items-center gap-2 border-b border-[#D8D0C0] pb-2">
        <button
          onClick={() => setActiveTab('DAG')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'DAG'
              ? 'bg-gold-600 text-[#2B2822] shadow-sm'
              : 'text-stone-600 hover:text-[#2B2822] hover:bg-[#EAE3D8]'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>Inference DAG Tree</span>
        </button>

        <button
          onClick={() => setActiveTab('NARRATIVE')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'NARRATIVE'
              ? 'bg-gold-600 text-[#2B2822] shadow-sm'
              : 'text-stone-600 hover:text-[#2B2822] hover:bg-[#EAE3D8]'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Reasoning Narrative</span>
        </button>

        <button
          onClick={() => setActiveTab('FACTS')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'FACTS'
              ? 'bg-gold-600 text-[#2B2822] shadow-sm'
              : 'text-stone-600 hover:text-[#2B2822] hover:bg-[#EAE3D8]'
          }`}
        >
          <ListOrdered className="w-4 h-4" />
          <span>Facts & Fired Rules Matrix</span>
        </button>
      </div>

      {/* TAB 1: REACT FLOW DAG VISUALIZATION */}
      {activeTab === 'DAG' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between text-xs text-stone-600 bg-[#FFFCF5]/60 p-3 rounded-lg border border-stone-300">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-gold-400" /> User Fact
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-gold-400" /> Production Rule
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Intermediate Derived Fact
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Terminal Diagnosis
              </span>
            </div>
            <span className="text-[11px] text-stone-600">
              Interactive DAG: Click nodes to inspect premise conditions and firing metadata
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3 h-[580px] bg-[#F2EEE4] border border-[#D8D0C0] rounded-xl overflow-hidden relative shadow-inner">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                fitView
                attributionPosition="bottom-left"
              >
                <Background color="#D8D0C0" gap={18} size={1} variant={BackgroundVariant.Dots} />
                <Controls className="bg-[#FFFCF5] border-stone-300 text-stone-800 fill-current" />
                <MiniMap
                  nodeColor={(n: any) => {
                    const raw = n.data?.rawNode;
                    if (raw?.type === 'USER_FACT') return '#A98329';
                    if (raw?.type === 'RULE') return '#C9A64B';
                    if (raw?.type === 'DERIVED_FACT') return '#10B981';
                    if (raw?.type === 'TERMINAL_DIAGNOSIS') return '#F59E0B';
                    return '#746D62';
                  }}
                  className="bg-[#F2EEE4]/90 border border-stone-300 rounded-lg overflow-hidden"
                />
              </ReactFlow>
            </div>

            {/* Node Inspector Drawer */}
            <div className="bg-[#FFFCF5] border border-[#D8D0C0] rounded-xl p-4 flex flex-col justify-between space-y-4">
              <div>
                <h3 className="text-xs font-semibold text-stone-600 uppercase tracking-wider mb-2">
                  Node Inspector
                </h3>
                {selectedNode ? (
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-[10px] font-mono text-gold-700 uppercase px-1.5 py-0.5 rounded bg-gold-500/10 border border-gold-500/20">
                        {selectedNode.type}
                      </span>
                      <h4 className="text-sm font-bold text-[#2B2822] mt-1.5">{selectedNode.label}</h4>
                      <p className="text-stone-600 text-[11px] mt-0.5 font-mono">ID: {selectedNode.id}</p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-[#FFFCF5] border border-stone-300 space-y-1">
                      <span className="text-[11px] font-semibold text-stone-700">Status:</span>
                      <p className="text-stone-600 text-xs font-mono">{selectedNode.status}</p>
                    </div>

                    {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[11px] font-semibold text-stone-700">Metadata:</span>
                        <pre className="p-2 rounded bg-[#F2EEE4] border border-stone-300 text-[10px] text-stone-700 overflow-x-auto font-mono">
                          {JSON.stringify(selectedNode.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-16 space-y-2 text-stone-600">
                    <Info className="w-8 h-8 mx-auto text-stone-700" />
                    <p className="text-xs">Click any node in the DAG graph to inspect antecedent conditions and evaluation metrics.</p>
                  </div>
                )}
              </div>

              <div className="text-[10px] text-stone-600 border-t border-stone-300 pt-3">
                DAG generated directly from working memory & rule chaining execution trace.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CHRONOLOGICAL REASONING NARRATIVE */}
      {activeTab === 'NARRATIVE' && (
        <Card className="border-stone-300 bg-[#FFFCF5] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-stone-300 pb-3">
            <h2 className="text-base font-bold text-[#2B2822]">Chronological Expert System Narrative</h2>
            <span className="text-xs text-stone-600 font-mono">
              {explanation.reasoning_narrative.length} Step{explanation.reasoning_narrative.length === 1 ? '' : 's'}
            </span>
          </div>

          <div className="space-y-3">
            {explanation.reasoning_narrative.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FFFCF5]/70 border border-stone-300/80 text-xs leading-relaxed"
              >
                <div className="w-5 h-5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-700 font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">
                  {idx + 1}
                </div>
                <p className="text-stone-700 font-medium">{item}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* TAB 3: FACTS & FIRED RULES MATRIX */}
      {activeTab === 'FACTS' && (
        <div className="space-y-6">
          {/* Initial User Evidence */}
          <Card className="border-stone-300 bg-[#FFFCF5] p-5 space-y-3">
            <h3 className="text-sm font-bold text-[#2B2822] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-gold-700" />
              Initial User-Asserted Evidence
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
              {Object.entries(explanation.initial_user_evidence).map(([key, val]) => (
                <div key={key} className="p-2.5 rounded-lg bg-[#FFFCF5] border border-stone-300 flex items-center justify-between">
                  <span className="font-mono text-stone-700 text-[11px]">{key}</span>
                  <span className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] ${
                    val === true ? 'bg-emerald-500/10 text-emerald-700' : val === false ? 'bg-red-500/10 text-red-700' : 'bg-[#EAE3D8] text-stone-600'
                  }`}>
                    {String(val).toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Derived Intermediate Facts */}
          {Object.keys(explanation.derived_intermediate_facts).length > 0 && (
            <Card className="border-stone-300 bg-[#FFFCF5] p-5 space-y-3">
              <h3 className="text-sm font-bold text-[#2B2822] flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-700" />
                Derived Intermediate Diagnostic Conclusions
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
                {Object.entries(explanation.derived_intermediate_facts).map(([key, val]) => (
                  <div key={key} className="p-2.5 rounded-lg bg-[#FFFCF5] border border-stone-300 flex items-center justify-between">
                    <span className="font-mono text-stone-700 text-[11px]">{key}</span>
                    <span className="font-mono font-bold px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-700">
                      {String(val).toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Fired Rules Execution Trace */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-[#2B2822]">Rule Execution Trace</h3>
            <div className="space-y-3">
              {explanation.execution_steps.map((step) => (
                <Card key={step.order} className="border-stone-300 bg-[#FFFCF5] p-4 space-y-2 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-300/80 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-gold-600/20 text-gold-700 font-bold text-[10px] flex items-center justify-center">
                        {step.order}
                      </span>
                      <span className="font-mono font-bold text-gold-800">{step.rule_id}</span>
                      <span className="text-stone-800 font-semibold">{step.rule_name}</span>
                    </div>
                    <Badge variant="category" value={step.category} size="sm" />
                  </div>

                  <p className="text-stone-700 leading-relaxed">{step.explanation}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                    <div className="p-2 rounded bg-[#F2EEE4] border border-stone-300">
                      <span className="text-stone-600 block mb-0.5">Satisfied Conditions:</span>
                      <pre className="text-stone-700 overflow-x-auto">{JSON.stringify(step.conditions, null, 2)}</pre>
                    </div>
                    <div className="p-2 rounded bg-[#F2EEE4] border border-stone-300">
                      <span className="text-emerald-500/80 block mb-0.5">Derived Assertions:</span>
                      <pre className="text-emerald-800 overflow-x-auto">{JSON.stringify(step.derived_facts, null, 2)}</pre>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

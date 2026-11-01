/**
 * NetSage Frontend TypeScript Definitions.
 * Strictly typed against the backend Pydantic models and API responses.
 */

export type TriState = 'TRUE' | 'FALSE' | 'UNKNOWN';

export type SessionStatus =
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'INCONCLUSIVE'
  | 'CONFLICT_DETECTED';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FactCategory =
  | 'GENERAL'
  | 'IP_DHCP'
  | 'GATEWAY'
  | 'DNS'
  | 'WIFI'
  | 'PERFORMANCE'
  | 'ISP';

export type FactSourceType = 'STATIC_DOMAIN' | 'USER_INPUT' | 'RULE_DERIVED';

export type RuleClassification = 'INTERMEDIATE' | 'TERMINAL_DIAGNOSIS';

// -----------------------------------------------------------------------------
// Diagnostic Wizard & Inquiry
// -----------------------------------------------------------------------------

export interface WhyExplanation {
  question_id: string;
  question_text: string;
  fact_key: string;
  investigating_hypothesis: string;
  hypothesis_category: string;
  triggering_rule_id: string;
  triggering_rule_name: string;
  rationale: string;
  impact_if_yes: string;
  impact_if_no: string;
}

export interface Question {
  id: string;
  fact_key: string;
  text: string;
  category: string;
  guidance: string;
  answer_type: string;
  available_options: string[];
  why_explanation?: WhyExplanation | null;
}

export interface StartSessionResponse {
  session_id: string;
  status: SessionStatus;
  created_at: string;
  current_question?: Question | null;
}

export interface DiagnosticStep {
  order: number;
  action: string;
  command?: string | null;
  description: string;
  expected_outcome: string;
  is_disruptive: boolean;
  requires_admin: boolean;
}

export interface DiagnosticResult {
  session_id: string;
  status: SessionStatus;
  diagnosis_name?: string | null;
  diagnosis_code?: string | null;
  category?: string | null;
  severity?: SeverityLevel | null;
  summary?: string | null;
  steps: DiagnosticStep[];
  warnings: string[];
  escalation_advice?: string | null;
  completed_at?: string | null;
}

export interface AnswerResponse {
  session_id: string;
  status: SessionStatus;
  is_completed: boolean;
  next_question?: Question | null;
  result?: DiagnosticResult | null;
  message?: string | null;
}

// -----------------------------------------------------------------------------
// Explanation Center & DAG
// -----------------------------------------------------------------------------

export interface InferenceTraceStep {
  order: number;
  rule_id: string;
  rule_name: string;
  category: string;
  conditions: Record<string, any>;
  derived_facts: Record<string, any>;
  explanation: string;
  timestamp: string;
}

export interface InferenceTreeNode {
  id: string;
  label: string;
  type: 'USER_FACT' | 'RULE' | 'DERIVED_FACT' | 'TERMINAL_DIAGNOSIS';
  status: string;
  metadata: Record<string, any>;
}

export interface InferenceTreeEdge {
  id: string;
  source: string;
  target: string;
  label?: string | null;
}

export interface InferenceTreeGraph {
  nodes: InferenceTreeNode[];
  edges: InferenceTreeEdge[];
}

export interface ExplanationResponse {
  session_id: string;
  status: string;
  final_diagnosis?: string | null;
  diagnosis_category?: string | null;
  diagnosis_severity?: SeverityLevel | null;
  initial_user_evidence: Record<string, any>;
  derived_intermediate_facts: Record<string, any>;
  fired_rules_count: number;
  execution_steps: InferenceTraceStep[];
  reasoning_narrative: string[];
  inference_tree: InferenceTreeGraph;
}

// -----------------------------------------------------------------------------
// Knowledge Base Explorer
// -----------------------------------------------------------------------------

export interface Fact {
  id: string;
  key: string;
  statement: string;
  category: string;
  source_type: FactSourceType;
  description: string;
  diagnostic_relevance: string;
}

export interface RuleCondition {
  fact_key: string;
  expected_value: any;
  operator: string;
}

export interface ProductionRule {
  id: string;
  name: string;
  category: string;
  classification: RuleClassification;
  priority: number;
  conditions: RuleCondition[];
  conclusions: Record<string, any>;
  explanation: string;
}

export interface KnowledgeStats {
  total_facts: number;
  total_rules: number;
  facts_by_source_type: Record<string, number>;
  facts_by_category: Record<string, number>;
  rules_by_category: Record<string, number>;
  rules_by_classification: Record<string, number>;
  terminal_rules_count: number;
  intermediate_rules_count: number;
  chaining_paths_count: number;
  max_chaining_depth: number;
}

// -----------------------------------------------------------------------------
// Diagnostic History
// -----------------------------------------------------------------------------

export interface DiagnosticAnswerSummary {
  id: number;
  question_id: string;
  question_text: string;
  answer: string;
  answered_at: string;
}

export interface SessionSummary {
  id: string;
  created_at: string;
  completed_at?: string | null;
  status: SessionStatus;
  final_diagnosis?: string | null;
  diagnosis_category?: string | null;
  severity?: SeverityLevel | null;
  answers_count: number;
}

export interface SessionListResponse {
  total: number;
  items: SessionSummary[];
}

export interface SessionDetailResponse {
  id: string;
  created_at: string;
  completed_at?: string | null;
  status: SessionStatus;
  final_diagnosis?: string | null;
  diagnosis_category?: string | null;
  severity?: SeverityLevel | null;
  recommendation_code?: string | null;
  summary?: string | null;
  answers: DiagnosticAnswerSummary[];
  traces_count: number;
  recommendation?: DiagnosticResult | null;
}

// -----------------------------------------------------------------------------
// API Error Schema
// -----------------------------------------------------------------------------

export interface ApiError {
  detail: string | any[];
  error_code: string;
  status_code: number;
}

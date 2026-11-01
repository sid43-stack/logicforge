# NetSage Architecture & Design Specification

## 1. Overview
NetSage is a modular Knowledge-Based Expert System (KBES) built to diagnose computer network connectivity issues using pure Python logical inference, FastAPI, and React.

## 2. Core Architectural Principles

### 2.1 Three-Layer Knowledge Representation
NetSage strictly segregates knowledge and data into three distinct tiers:
1. **Static Domain Knowledge**: Immutable networking principles and axioms (e.g. F01-F28) loaded at startup.
2. **User-Provided Diagnostic Facts**: Direct answers asserted by the user in response to diagnostic questions (annotated with `source="USER"` and timestamp).
3. **Rule-Derived Inferred Facts**: Intermediate conclusions and terminal diagnoses asserted exclusively by fired production rules (annotated with `source=rule_id`, firing order, and supporting premises).

### 2.2 Tri-State Logic (True / False / Unknown)
Every fact in Working Memory conforms to tri-state semantics:
- `TRUE`: Positively confirmed.
- `FALSE`: Positively refuted.
- `UNKNOWN`: Not yet evaluated or explicitly marked uncertain by the user. An unknown fact is never conflated with `FALSE`.

### 2.3 Production Rules & Chaining
Rules are defined as:
```text
IF condition_1 AND condition_2 ...
THEN assert conclusion_1, conclusion_2 ...
```
- **Forward Chaining (Data-Driven)**: Evaluates rules against current working memory, firing all satisfied rules iteratively until a fix-point is reached.
- **Rule Chaining**: Output conclusions from rule $R_i$ immediately become input facts for rule $R_j$.

### 2.4 Strengthened Backward Chaining & Dynamic Question Selection
- Backward chaining operates over candidate diagnostic hypotheses (e.g. `dns_server_failure`, `dhcp_assignment_failure`, `gateway_unreachable`, `isp_outage`).
- For an active hypothesis $H$, the engine identifies rules concluding $H$.
- It recurses through unresolved conditions to find askable leaf premises.
- It dynamically chooses the next question that has maximum discriminating power within the active problem cluster.

### 2.5 Conflict Detection & Inconsistent Evidence Validation
1. **Contradictory Diagnosis Conflict Detection**:
   - If two or more rules fire and assert mutually exclusive terminal conclusions (e.g. `isp_outage` AND `router_hardware_fault`), the engine flags a `CONFLICT_DETECTED` state.
   - NetSage never silently selects an arbitrary diagnosis. It captures conflicting evidence in the explanation trace and requests clarification or flags ambiguity.
2. **User Evidence Consistency Validation**:
   - Before asserting a user answer into working memory, the validator checks against established physical constraints (e.g., claiming "No network connection" while asserting "Can open websites by domain name").
   - Inconsistent responses trigger a clarification prompt or invalidity warning.

### 2.6 Explanation Facilities & Visualizations
1. **WHY Explanation**: Displayed alongside each diagnostic question, explaining which hypothesis is under investigation and why this premise is required.
2. **HOW Explanation**: Post-diagnosis trace displaying:
   - Initial user inputs.
   - Chronological rule firing chain.
   - Intermediate conclusions asserted.
   - Terminal diagnosis and actionable recommendations.
3. **Inference Tree Visualization**: Visual DAG rendered in the Explanation Center showing nodes (facts, rules, diagnoses) and edges representing logical deductions.
4. **Interactive Knowledge Base Explorer**: Visual browser allowing users to inspect domain facts, filter production rules by category, view condition-conclusion relationships, and understand dependency graphs.

## 3. Technology Stack & Directory Structure
- **Backend**: FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic v2, Pytest.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router, Axios.
- **Architecture**: Monorepo with completely decoupled backend expert system and frontend presentation layer.


# NetSage REST API Specification

This document provides the complete API reference for the NetSage Expert System backend, exposed via FastAPI under the `/api` prefix.

---

## Architecture & Conventions

- **Base URL**: `http://localhost:8000/api`
- **Data Format**: `application/json` for all requests and responses
- **Error Format**: All error responses return a structured JSON object:
  ```json
  {
    "detail": "Descriptive error message or validation errors array",
    "error_code": "NOT_FOUND | BAD_REQUEST | CONFLICT_DETECTED | VALIDATION_ERROR | INTERNAL_SERVER_ERROR",
    "status_code": 404
  }
  ```
- **Tri-State Logic Representation**:
  - Answers can be submitted as `"YES"`, `"NO"`, or `"UNKNOWN"`.
  - Missing facts default to `UNKNOWN` and never satisfy negative conditions without affirmative evidence.

---

## Diagnostics Endpoints

### 1. Start Diagnostic Session
Initiates a brand new network troubleshooting session, creates an isolated working memory state, and dynamically selects the first question based on highest-priority candidate hypotheses.

- **Method & Path**: `POST /api/diagnostics/start`
- **Status Code**: `201 Created`
- **Request Headers**: `Content-Type: application/json`
- **Request Body** (optional):
  ```json
  {
    "initial_facts": {
      "device_connected": true
    }
  }
  ```
- **Response Body**:
  ```json
  {
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "IN_PROGRESS",
    "created_at": "2026-11-01T11:45:00.000000Z",
    "current_question": {
      "id": "Q05",
      "fact_key": "external_ip_reachable",
      "text": "Can you ping a known external IP address on the internet (e.g., 8.8.8.8 or 1.1.1.1)?",
      "category": "DNS",
      "guidance": "Open a command prompt and run 'ping 8.8.8.8' to test external IP layer 3 routing.",
      "answer_type": "boolean",
      "available_options": ["YES", "NO", "UNKNOWN"],
      "why_explanation": {
        "question_id": "Q05",
        "question_text": "Can you ping a known external IP address on the internet (e.g., 8.8.8.8 or 1.1.1.1)?",
        "fact_key": "external_ip_reachable",
        "investigating_hypothesis": "Upstream DNS Provider Outage",
        "hypothesis_category": "DNS",
        "triggering_rule_id": "R11",
        "triggering_rule_name": "DNS Resolution Failure Detection",
        "rationale": "Testing public IP reachability determines whether the failure is isolated to Layer 7 DNS hostname resolution.",
        "impact_if_yes": "If YES, rules out physical gateway and WAN link failure, pointing directly to DNS resolvers.",
        "impact_if_no": "If NO, eliminates DNS outages from primary consideration and directs diagnosis towards ISP WAN failure."
      }
    }
  }
  ```

---

### 2. Submit Diagnostic Answer
Submits user evidence for an active question. Evaluates forward chaining, detects contradictions or terminal diagnoses, and dynamically recalculates backward chaining goals.

- **Method & Path**: `POST /api/diagnostics/{session_id}/answer`
- **Path Parameters**:
  - `session_id` (string, required): Active UUID session identifier.
- **Request Body**:
  ```json
  {
    "question_id": "Q05",
    "answer": "YES"
  }
  ```
- **Responses**:
  - **In-Progress Continuation** (`200 OK`):
    ```json
    {
      "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "status": "IN_PROGRESS",
      "is_completed": false,
      "next_question": {
        "id": "Q06",
        "fact_key": "domain_access",
        "text": "Can you open websites in your browser using their domain names (e.g., google.com)?",
        "category": "DNS",
        "guidance": "Try opening 'https://www.google.com' in your web browser.",
        "answer_type": "boolean",
        "available_options": ["YES", "NO", "UNKNOWN"],
        "why_explanation": { ... }
      },
      "result": null,
      "message": "Answer accepted. Next question generated dynamically."
    }
    ```
  - **Terminal Diagnosis Completed** (`200 OK`):
    ```json
    {
      "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "status": "COMPLETED",
      "is_completed": true,
      "next_question": null,
      "result": {
        "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "status": "COMPLETED",
        "diagnosis_name": "Upstream DNS Provider Outage",
        "diagnosis_code": "REC_DNS_UPSTREAM",
        "category": "DNS",
        "severity": "HIGH",
        "summary": "External IP addresses are reachable, but primary and upstream DNS servers fail to resolve domain names.",
        "steps": [
          {
            "order": 1,
            "action": "Configure Public DNS Resolvers",
            "command": "netsh interface ip set dns name=\"Wi-Fi\" static 8.8.8.8",
            "description": "Switch local network adapter settings to Google Public DNS (8.8.8.8) or Cloudflare DNS (1.1.1.1).",
            "expected_outcome": "Domain resolution succeeds immediately via alternate upstream servers.",
            "is_disruptive": false,
            "requires_admin": true
          },
          {
            "order": 2,
            "action": "Flush Local DNS Cache",
            "command": "ipconfig /flushdns",
            "description": "Clear negative cache entries from Windows DNS Client Resolver Cache.",
            "expected_outcome": "Purges cached SERVFAIL and NXDOMAIN responses.",
            "is_disruptive": false,
            "requires_admin": true
          }
        ],
        "warnings": [
          "Switching DNS resolvers bypasses ISP-specific content filters."
        ],
        "escalation_advice": "If public DNS servers also fail to respond, check router firewall settings for UDP port 53 blocking.",
        "completed_at": "2026-11-01T11:46:12.000000Z"
      },
      "message": "Diagnostic established successfully."
    }
    ```
  - **Contradiction Detected** (`409 Conflict`):
    ```json
    {
      "detail": "Contradictory evidence detected in session '...': Contradiction on fact 'gateway_reachable': existing=True, asserted=False",
      "error_code": "CONFLICT_DETECTED",
      "status_code": 409
    }
    ```

---

### 3. Get Current Question
Retrieves the currently pending diagnostic question for an in-progress session.

- **Method & Path**: `GET /api/diagnostics/{session_id}/question`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**: Identical to `current_question` schema in `POST /start`.
- **Errors**:
  - `400 Bad Request`: If session is already `COMPLETED`, `INCONCLUSIVE`, or `CONFLICT_DETECTED`.
  - `404 Not Found`: If session does not exist.

---

### 4. Get Diagnostic Result
Retrieves the confirmed diagnosis and prioritized remediation actions for a completed session.

- **Method & Path**: `GET /api/diagnostics/{session_id}/result`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**: See `result` object in `POST /answer`.
- **Errors**:
  - `400 Bad Request`: If session is still `IN_PROGRESS`.
  - `404 Not Found`: If session does not exist.

---

### 5. Get HOW Diagnostic Explanation
Generates the comprehensive audit narrative and directed acyclic graph (DAG) representation for the Explanation Center.

- **Method & Path**: `GET /api/diagnostics/{session_id}/explanation`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "COMPLETED",
    "final_diagnosis": "Upstream DNS Provider Outage",
    "diagnosis_category": "DNS",
    "diagnosis_severity": "HIGH",
    "initial_user_evidence": {
      "external_ip_reachable": true,
      "domain_access": false,
      "dns_server_reachable": false,
      "multiple_devices_affected": true
    },
    "derived_intermediate_facts": {
      "dns_failure_suspected": true,
      "dns_server_failure_suspected": true
    },
    "fired_rules_count": 3,
    "execution_steps": [
      {
        "order": 1,
        "rule_id": "R11",
        "rule_name": "DNS Resolution Failure Detection",
        "category": "DNS",
        "conditions": {
          "external_ip_reachable": true,
          "domain_access": false
        },
        "derived_facts": {
          "dns_failure_suspected": true
        },
        "explanation": "External IP is directly reachable, but domain names cannot be resolved.",
        "timestamp": "2026-11-01T11:45:10.000000Z"
      }
    ],
    "reasoning_narrative": [
      "Diagnostic inquiry targeted hypotheses across the DNS problem category.",
      "Rule R11 evaluated true based on external_ip_reachable=True and domain_access=False, deriving dns_failure_suspected=True.",
      "Rule R12 fired after discovering dns_server_reachable=False.",
      "Rule R13 confirmed terminal diagnosis: 'Upstream DNS Provider Outage'."
    ],
    "inference_tree": {
      "nodes": [
        {
          "id": "external_ip_reachable",
          "label": "external_ip_reachable: True",
          "type": "USER_FACT",
          "status": "PROVEN",
          "metadata": {}
        },
        {
          "id": "R11",
          "label": "R11: DNS Resolution Failure Detection",
          "type": "RULE",
          "status": "FIRED",
          "metadata": { "priority": 85 }
        },
        {
          "id": "terminal_Upstream DNS Provider Outage",
          "label": "Diagnosis: Upstream DNS Provider Outage",
          "type": "TERMINAL_DIAGNOSIS",
          "status": "PROVEN",
          "metadata": {}
        }
      ],
      "edges": [
        {
          "id": "e_external_ip_reachable_R11",
          "source": "external_ip_reachable",
          "target": "R11",
          "label": "premise"
        },
        {
          "id": "e_R13_terminal",
          "source": "R13",
          "target": "terminal_Upstream DNS Provider Outage",
          "label": "concludes"
        }
      ]
    }
  }
  ```

---

### 6. Restart Diagnostic Session
Resets an existing session back to initial state, wiping past answers, traces, and conclusions.

- **Method & Path**: `POST /api/diagnostics/{session_id}/restart`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**: Identical to `POST /start` response body with the same `session_id`.

---

## Knowledge Base Explorer Endpoints

### 7. Get Domain Facts
Returns all networking facts catalogued in the knowledge base, with optional filtering.

- **Method & Path**: `GET /api/knowledge/facts`
- **Query Parameters**:
  - `category` (string, optional): e.g. `IP_DHCP`, `DNS`, `GATEWAY`, `WIFI`, `PERFORMANCE`, `ISP`.
  - `source_type` (string, optional): `STATIC_DOMAIN`, `USER_INPUT`, `RULE_DERIVED`.
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  [
    {
      "id": "F01",
      "key": "router_function",
      "statement": "A router connects a local area network (LAN) to external networks and routes IP packets.",
      "category": "GENERAL",
      "source_type": "STATIC_DOMAIN",
      "description": "Routers operate at OSI Layer 3 (Network) to forward packets between distinct IP subnets.",
      "diagnostic_relevance": "If the local device cannot reach the router, no external internet communication is possible."
    }
  ]
  ```

---

### 8. Get Production Rules
Returns production rules with conditions, conclusions, priority, and explanations.

- **Method & Path**: `GET /api/knowledge/rules`
- **Query Parameters**:
  - `category` (string, optional): e.g. `IP_DHCP`, `DNS`, `GATEWAY`, `WIFI`, `PERFORMANCE`, `ISP`.
  - `classification` (string, optional): `INTERMEDIATE`, `TERMINAL_DIAGNOSIS`.
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  [
    {
      "id": "R01",
      "name": "Automatic IP Configuration Failure (APIPA Detection)",
      "category": "IP_DHCP",
      "classification": "INTERMEDIATE",
      "priority": 80,
      "conditions": [
        {
          "fact_key": "device_connected",
          "expected_value": true,
          "operator": "=="
        },
        {
          "fact_key": "ip_is_apipa",
          "expected_value": true,
          "operator": "=="
        }
      ],
      "conclusions": {
        "dhcp_failure_suspected": true
      },
      "explanation": "Device is connected to the network but received an APIPA address (169.254.x.x), indicating DHCP assignment failed."
    }
  ]
  ```

---

### 9. Get Knowledge Base Statistics
Returns aggregate structural metrics across facts, production rules, and the dependency graph.

- **Method & Path**: `GET /api/knowledge/stats`
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "total_facts": 30,
    "total_rules": 28,
    "facts_by_source_type": {
      "STATIC_DOMAIN": 30
    },
    "facts_by_category": {
      "GENERAL": 4,
      "IP_DHCP": 5,
      "GATEWAY": 4,
      "DNS": 5,
      "WIFI": 5,
      "PERFORMANCE": 4,
      "ISP": 3
    },
    "rules_by_category": {
      "IP_DHCP": 5,
      "GATEWAY": 5,
      "DNS": 5,
      "WIFI": 5,
      "PERFORMANCE": 4,
      "ISP": 4
    },
    "rules_by_classification": {
      "INTERMEDIATE": 15,
      "TERMINAL_DIAGNOSIS": 13
    },
    "terminal_rules_count": 13,
    "intermediate_rules_count": 15,
    "chaining_paths_count": 21,
    "max_chaining_depth": 3
  }
  ```

---

## History & Session Management Endpoints

### 10. List Diagnostic Sessions
Returns paginated list of historical sessions.

- **Method & Path**: `GET /api/history`
- **Query Parameters**:
  - `skip` (integer, default `0`): Pagination offset.
  - `limit` (integer, default `20`, max `100`): Page size limit.
  - `status` (string, optional): `IN_PROGRESS`, `COMPLETED`, `INCONCLUSIVE`, `CONFLICT_DETECTED`.
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "total": 5,
    "items": [
      {
        "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "created_at": "2026-11-01T11:45:00.000000Z",
        "completed_at": "2026-11-01T11:46:12.000000Z",
        "status": "COMPLETED",
        "final_diagnosis": "Upstream DNS Provider Outage",
        "diagnosis_category": "DNS",
        "severity": "HIGH",
        "answers_count": 4
      }
    ]
  }
  ```

---

### 11. Get Historical Session Detail
Returns full historical audit details for a specific session.

- **Method & Path**: `GET /api/history/{session_id}`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "created_at": "2026-11-01T11:45:00.000000Z",
    "completed_at": "2026-11-01T11:46:12.000000Z",
    "status": "COMPLETED",
    "final_diagnosis": "Upstream DNS Provider Outage",
    "diagnosis_category": "DNS",
    "severity": "HIGH",
    "recommendation_code": "REC_DNS_UPSTREAM",
    "summary": "External IP addresses are reachable, but primary and upstream DNS servers fail to resolve domain names.",
    "answers": [
      {
        "id": 1,
        "question_id": "Q05",
        "question_text": "Can you ping a known external IP address...",
        "answer": "YES",
        "answered_at": "2026-11-01T11:45:10.000000Z"
      }
    ],
    "traces_count": 3,
    "recommendation": { ... }
  }
  ```

---

### 12. Delete Session
Deletes a session and all its child answers, execution traces, and recommendations via database foreign-key cascade.

- **Method & Path**: `DELETE /api/history/{session_id}`
- **Path Parameters**: `session_id` (string, required)
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "message": "Diagnostic session '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d' deleted successfully.",
    "deleted_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
  }
  ```
- **Errors**: `404 Not Found` if session does not exist.

---

## Health Endpoint

### 13. System Health Check
Verifies service status, project identity, and version.

- **Method & Path**: `GET /api/health`
- **Status Code**: `200 OK`
- **Response Body**:
  ```json
  {
    "status": "healthy",
    "project": "NetSage",
    "version": "1.0.0",
    "timestamp": "2026-11-01T11:47:00.000000Z"
  }
  ```


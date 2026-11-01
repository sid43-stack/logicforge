# NetSage

## AI-Based Network Troubleshooting Expert System

**Project Type:** Knowledge-Based Expert System (KBES)
**Application Platform:** Web Application
**Project Complexity:** Advanced Academic Mini Project
**Domain:** Computer Networks / Artificial Intelligence
**Primary Language:** Python
**Frontend:** React + TypeScript
**Backend:** FastAPI
**Inference Technique:** Forward Chaining + Backward Chaining

---

# 1. PROJECT OVERVIEW

## 1.1 Project Introduction

NetSage is a web-based Knowledge-Based Expert System designed to diagnose common computer network connectivity problems through an intelligent question-and-answer interface.

The system uses a predefined networking knowledge base, a collection of IF-THEN production rules, and a custom-built inference engine to identify probable network faults and recommend appropriate troubleshooting solutions.

Unlike conventional troubleshooting applications that simply provide generic instructions, NetSage dynamically asks users a series of YES/NO questions based on their previous responses.

It analyses the collected information using forward chaining and backward chaining techniques to reach a diagnosis.

The system also includes an explanation facility that explains:

- WHY a particular question is being asked.
- HOW the system reached its final diagnosis.
- WHICH rules were triggered.
- WHAT facts and conditions contributed to the conclusion.

The entire expert system will be implemented in Python without using ready-made expert system frameworks or inference engine libraries.

## 1.2 Problem Statement

Network connectivity problems can occur due to several reasons, including:

- Incorrect IP configuration.
- DNS resolution failures.
- Gateway connectivity problems.
- DHCP assignment failures.
- Weak Wi-Fi signals.
- High network latency.
- Packet loss.
- Router or ISP-related problems.

For non-technical users, identifying the actual cause of these problems can be difficult.

NetSage addresses this problem by providing an interactive troubleshooting system that applies networking knowledge and logical inference to identify possible faults and guide users towards appropriate solutions.

## 1.3 Project Objectives

1. Develop a knowledge-based system for diagnosing common network problems.
2. Create a networking knowledge base containing at least 15 facts.
3. Implement at least 15 IF-THEN production rules.
4. Implement a custom inference engine using Python.
5. Support forward chaining and backward chaining.
6. Dynamically generate YES/NO diagnostic questions.
7. Implement a WHY and HOW explanation facility.
8. Generate understandable troubleshooting recommendations.
9. Provide a modern, interactive web interface.
10. Maintain diagnostic session history.

---

# 2. PROJECT SCOPE

The initial version will focus on six major categories of network problems.

| ID  | Network Problem                     | Description                                                              |
| --- | ----------------------------------- | ------------------------------------------------------------------------ |
| N01 | DNS Resolution Failure              | Domain names cannot be resolved into IP addresses.                       |
| N02 | IP / DHCP Configuration Failure     | Device has incorrect or missing IP configuration.                        |
| N03 | Gateway Connectivity Failure        | Device cannot communicate with its default gateway.                      |
| N04 | Weak Wi-Fi Signal                   | Poor wireless signal causes instability or disconnections.               |
| N05 | Packet Loss / High Latency          | Network performance is degraded.                                         |
| N06 | ISP / Internet Connectivity Failure | Internet connectivity is unavailable despite local network connectivity. |

### Out of Scope

The following features should NOT be included in the initial implementation:

- Desktop application.
- Automatic modification of operating system network settings.
- Machine learning model training.
- LLM-based diagnosis.
- Enterprise network monitoring.
- Real-time packet inspection.
- Router configuration automation.
- Advanced network security scanning.

The focus must remain on building a functional Knowledge-Based Expert System.

---

# 3. TECHNOLOGY STACK

## 3.1 Frontend

| Technology   | Purpose                       |
| ------------ | ----------------------------- |
| React.js     | Frontend application          |
| TypeScript   | Type safety                   |
| Vite         | Development and build tooling |
| Tailwind CSS | Styling                       |
| shadcn/ui    | UI components                 |
| Lucide React | Icons                         |
| Recharts     | Diagnostic visualizations     |
| React Router | Application routing           |
| Axios        | API communication             |

## 3.2 Backend

| Technology | Purpose                   |
| ---------- | ------------------------- |
| Python     | Core programming language |
| FastAPI    | REST API                  |
| Pydantic   | Data validation           |
| SQLAlchemy | Database ORM              |
| SQLite     | Local diagnostic history  |
| Uvicorn    | ASGI server               |

## 3.3 Expert System

The expert system must be developed from scratch using native Python.

Components:

- Knowledge Base.
- Rule Base.
- Working Memory.
- Forward Chaining Engine.
- Backward Chaining Engine.
- Question Selection Engine.
- Explanation Engine.
- Recommendation Engine.

Do not use ready-made expert system shells or inference engine libraries.

---

# 4. SYSTEM ARCHITECTURE

The application will follow a modular architecture.

```text
                  NETSAGE
                     |
          React Web Application
                     |
               REST API
                     |
               FastAPI
                     |
          Application Services
                     |
          Expert System Engine
                     |
     --------------------------------
     |              |               |
 Knowledge       Rule Base      Working Memory
   Base
     |              |               |
     --------------------------------
                     |
               Inference Engine
                     |
          ---------------------
          |                   |
    Forward Chaining    Backward Chaining
          |                   |
          ---------------------
                     |
          Question Selection
                     |
           Explanation Engine
                     |
          Recommendation Engine
                     |
              Final Diagnosis
                     |
               SQLite DB
```

## 4.1 Architectural Responsibilities

### Frontend

Responsible for:

- Displaying the dashboard.
- Starting diagnostic sessions.
- Presenting dynamic questions.
- Collecting YES/NO responses.
- Showing diagnosis results.
- Displaying explanation traces.
- Showing troubleshooting recommendations.
- Displaying diagnostic history.

### Backend

Responsible for:

- Managing diagnostic sessions.
- Communicating with the inference engine.
- Validating responses.
- Managing diagnostic results.
- Returning questions and explanations.
- Storing session history.

### Expert System Engine

Responsible for:

- Managing facts and rules.
- Maintaining working memory.
- Applying inference techniques.
- Deriving intermediate conclusions.
- Selecting diagnostic questions.
- Producing final diagnoses.
- Generating explanations.

---

# 5. KNOWLEDGE BASE DESIGN

The knowledge base represents the networking knowledge used by NetSage.

It must contain at least 15 facts. The initial implementation should contain approximately 25–30 facts.

Facts should be represented using structured Python objects rather than unstructured strings.

## 5.1 Initial Knowledge Base

| ID  | Fact                                                                                  | Description           |
| --- | ------------------------------------------------------------------------------------- | --------------------- |
| F01 | A router connects a local network to external networks.                               | Router functionality  |
| F02 | A default gateway provides an exit point from a local network.                        | Gateway functionality |
| F03 | DNS translates domain names into IP addresses.                                        | DNS functionality     |
| F04 | DHCP automatically assigns IP configuration to devices.                               | DHCP functionality    |
| F05 | An APIPA address commonly falls within 169.254.0.0/16.                                | IP configuration      |
| F06 | A device requires valid network configuration for normal network communication.       | Networking principle  |
| F07 | An unreachable gateway can indicate a local connectivity problem.                     | Gateway diagnosis     |
| F08 | DNS failure can prevent access to websites by domain name.                            | DNS diagnosis         |
| F09 | External IP connectivity may work even when DNS resolution fails.                     | DNS diagnosis         |
| F10 | Weak Wi-Fi signals can cause unstable connectivity.                                   | Wireless networking   |
| F11 | Physical distance and obstacles can weaken Wi-Fi signals.                             | Wireless networking   |
| F12 | Packet loss represents packets that fail to reach their destination.                  | Network performance   |
| F13 | High latency increases communication delay.                                           | Network performance   |
| F14 | Network congestion can increase latency and packet loss.                              | Network performance   |
| F15 | Multiple devices experiencing internet failure may indicate a shared network problem. | ISP diagnosis         |
| F16 | A router reboot can resolve certain temporary router problems.                        | Troubleshooting       |
| F17 | An incorrect DNS server configuration can cause name-resolution problems.             | DNS diagnosis         |
| F18 | An incorrect IP configuration can prevent network communication.                      | IP diagnosis          |
| F19 | Ethernet connections are not affected by Wi-Fi signal strength.                       | Connection type       |
| F20 | A functioning gateway does not guarantee external internet connectivity.              | Internet connectivity |
| F21 | A device connected to Wi-Fi may still lack internet access.                           | Connectivity          |
| F22 | High latency and packet loss can degrade network performance.                         | Performance           |
| F23 | DHCP lease renewal may resolve temporary IP assignment problems.                      | DHCP troubleshooting  |
| F24 | Changing DNS servers may help resolve certain DNS configuration problems.             | DNS troubleshooting   |
| F25 | ISP outages can interrupt external internet connectivity.                             | ISP diagnosis         |
| F26 | Restarting network equipment can resolve some temporary connectivity issues.          | Troubleshooting       |
| F27 | A reachable external IP does not necessarily indicate that DNS is functioning.        | DNS diagnosis         |
| F28 | A device with a valid IP address may still have gateway or DNS problems.              | Network diagnosis     |

These facts form the initial domain knowledge. Additional facts can be added during testing.

---

# 6. RULE BASE DESIGN

The system must contain at least 15 IF-THEN rules.

The initial implementation should target 25–30 rules.

Rules should be represented using structured objects.

Each rule must contain:

- Rule ID.
- Rule name.
- Conditions.
- Conclusion.
- Explanation.
- Priority.

## 6.1 Diagnostic Rules

### Category A: IP / DHCP Problems

**R01 — Automatic IP Configuration Failure**

IF:

- Device is connected to a network.
- Device has an IP address beginning with 169.254.

THEN:

- Diagnose possible DHCP assignment failure.

**R02 — Invalid IP Configuration**

IF:

- Device is connected.
- Device does not have a valid IP configuration.

THEN:

- Diagnose IP configuration failure.

**R03 — DHCP Server Unavailable**

IF:

- DHCP assignment appears to have failed.
- Device cannot obtain a valid IP address.

THEN:

- Suspect DHCP server unavailability.

**R04 — DHCP Troubleshooting Recommendation**

IF:

- DHCP failure is suspected.

THEN:

- Recommend checking router DHCP settings and renewing the IP lease.

### Category B: Gateway Problems

**R05 — Gateway Connectivity Failure**

IF:

- Device has valid IP configuration.
- Default gateway is unreachable.

THEN:

- Diagnose gateway connectivity failure.

**R06 — Local Network Problem**

IF:

- Device cannot communicate with the gateway.

THEN:

- Suspect local network connectivity failure.

**R07 — Possible Router Problem**

IF:

- Gateway is unreachable.
- Multiple devices are affected.

THEN:

- Suspect router or local network equipment failure.

**R08 — Gateway Troubleshooting Recommendation**

IF:

- Gateway failure is suspected.

THEN:

- Recommend checking router power, connection and network configuration.

### Category C: DNS Problems

**R09 — DNS Resolution Failure**

IF:

- External IP connectivity is available.
- Domain-name access is unavailable.

THEN:

- Diagnose DNS resolution failure.

**R10 — DNS Server Failure**

IF:

- DNS resolution failure is suspected.
- Configured DNS server is unreachable.

THEN:

- Diagnose possible DNS server failure.

**R11 — DNS Configuration Problem**

IF:

- DNS resolution fails.
- External IP connectivity works.
- Alternative DNS testing succeeds.

THEN:

- Suspect incorrect DNS configuration.

**R12 — DNS Troubleshooting Recommendation**

IF:

- DNS failure is diagnosed.

THEN:

- Recommend checking DNS configuration, flushing the DNS cache and testing an alternative DNS server.

### Category D: Wi-Fi Problems

**R13 — Weak Wi-Fi Signal**

IF:

- Connection type is Wi-Fi.
- Signal strength is weak.

THEN:

- Diagnose weak Wi-Fi signal.

**R14 — Wireless Instability**

IF:

- Wi-Fi signal is weak.
- Frequent disconnections occur.

THEN:

- Diagnose wireless connectivity instability.

**R15 — Wireless Improvement Recommendation**

IF:

- Weak Wi-Fi signal is diagnosed.

THEN:

- Recommend moving closer to the router and reducing physical obstructions.

### Category E: Network Performance Problems

**R16 — High Latency**

IF:

- Network latency is consistently high.

THEN:

- Diagnose high-latency conditions.

**R17 — Packet Loss**

IF:

- Packet loss is consistently above an acceptable threshold.

THEN:

- Diagnose packet-loss conditions.

**R18 — Network Congestion**

IF:

- High latency exists.
- Multiple devices are using the network heavily.

THEN:

- Suspect network congestion.

**R19 — Network Instability**

IF:

- High latency exists.
- Packet loss is present.

THEN:

- Diagnose network instability.

**R20 — Performance Troubleshooting Recommendation**

IF:

- High latency or packet loss is diagnosed.

THEN:

- Recommend checking network usage, connection quality and router placement.

### Category F: ISP / Internet Problems

**R21 — Possible ISP Failure**

IF:

- Gateway is reachable.
- External IP connectivity is unavailable.

THEN:

- Suspect an internet connectivity or ISP problem.

**R22 — Possible ISP Outage**

IF:

- Gateway is reachable.
- External IP connectivity is unavailable.
- Multiple devices are affected.

THEN:

- Diagnose a possible ISP outage.

**R23 — Single Device Connectivity Problem**

IF:

- Other devices have internet access.
- The current device does not have internet access.

THEN:

- Suspect a device-specific network configuration problem.

**R24 — Router Restart Recommendation**

IF:

- A temporary router connectivity problem is suspected.

THEN:

- Recommend restarting the router after checking the connection status of other devices.

**R25 — Internet Connectivity Recommendation**

IF:

- An ISP connectivity problem is suspected.

THEN:

- Recommend checking ISP service status and contacting the service provider if the issue persists.

## 6.2 Rule Chaining Requirement

Rules must support chained inference.

Example:

```text
User Responses:
    valid_ip = True
    gateway_reachable = True
    external_ip_reachable = True
    domain_access = False

                  |
                  v

                 R09

                  |
                  v

       dns_failure_suspected = True

                  |
                  v

                 R10

                  |
                  v

       dns_server_failure = True

                  |
                  v

          Final Diagnosis
```

The conclusion of one rule must be available as a fact for subsequent rules.

Do not hardcode the final diagnosis directly into the user interface.

---

# 7. INFERENCE ENGINE IMPLEMENTATION

This is the most important component of the entire project.

The inference engine must be implemented manually using Python.

Do not use:

- Experta.
- PyKnow.
- Ready-made expert system shells.
- External rule-engine libraries.

## 7.1 Working Memory

Working memory stores:

1. Initial user responses.
2. Known networking facts.
3. Intermediate conclusions.
4. Final diagnostic conclusions.

Example:

```python
working_memory = {
    "device_connected": True,
    "valid_ip": True,
    "gateway_reachable": True,
    "external_ip_reachable": True,
    "domain_access": False
}
```

Unknown facts must not automatically be treated as FALSE.

The engine must distinguish between:

- TRUE.
- FALSE.
- UNKNOWN.

## 7.2 Forward Chaining

Implement a forward chaining algorithm.

### Algorithm

1. Initialize working memory with known facts.
2. Load all applicable production rules.
3. Evaluate the conditions of each rule.
4. If all conditions are satisfied, fire the rule.
5. Add the rule conclusion to working memory.
6. Record the fired rule in the explanation trace.
7. Repeat until no new conclusions can be generated.
8. Return all derived conclusions.

### Pseudocode

```python
def forward_chaining(facts, rules):

    working_memory = facts.copy()
    fired_rules = []

    changed = True

    while changed:

        changed = False

        for rule in rules:

            if rule_already_fired(rule, fired_rules):
                continue

            if all_conditions_satisfied(rule, working_memory):

                add_conclusion(
                    rule,
                    working_memory
                )

                fired_rules.append(rule.id)

                changed = True

    return working_memory, fired_rules
```

Implement proper duplicate prevention and conflict handling.

## 7.3 Backward Chaining

Backward chaining should start with a diagnostic goal.

Example:

```text
Goal:
    Is the network experiencing DNS failure?

Required conditions:

    1. Is external IP connectivity available?
    2. Can the user access websites using domain names?

If either fact is UNKNOWN:
    Ask the user the relevant question.

If both conditions are satisfied:
    Confirm the DNS failure hypothesis.
```

### Algorithm

1. Select a diagnostic goal.
2. Identify rules that can establish that goal.
3. Examine the conditions of those rules.
4. Check whether each condition is known.
5. If unknown, generate an appropriate question.
6. Collect the response.
7. Continue until the goal is established or rejected.

The system should use backward chaining for intelligent question selection.

## 7.4 Hybrid Inference Workflow

The final diagnostic process should combine both methods:

1. Start with backward chaining to identify relevant questions.
2. Ask the user one question at a time.
3. Store responses in working memory.
4. Use forward chaining to derive intermediate facts.
5. Use backward chaining to investigate unresolved diagnostic goals.
6. Repeat until a diagnosis is reached or no supported conclusion is possible.
7. Generate an explanation trace.

---

# 8. DYNAMIC QUESTION GENERATION

The diagnostic interface must not show a fixed questionnaire.

Questions should be selected according to the user's previous answers.

## 8.1 Initial Questions

Q01: Is your device connected to a network?

Q02: Are you using Wi-Fi?

Q03: Does your device have a valid IP address?

Q04: Can your device communicate with the default gateway?

Q05: Can you access an external IP address?

Q06: Can you open websites using their domain names?

Q07: Are other devices experiencing the same problem?

Q08: Are you experiencing frequent disconnections?

Q09: Is your Wi-Fi signal weak?

Q10: Are you experiencing unusually slow internet?

Q11: Are you experiencing frequent buffering or interruptions?

Q12: Does your device have an IP address beginning with 169.254?

Q13: Is your configured DNS server reachable?

Q14: Does the problem occur on both Wi-Fi and Ethernet?

Q15: Does restarting the router temporarily resolve the problem?

These are starting questions, not a mandatory sequence.

The inference engine should select only the questions relevant to the current diagnostic goal.

## 8.2 Question Metadata

Each question should include:

```python
{
    "id": "Q05",
    "question": "Can you access an external IP address?",
    "related_fact": "external_ip_reachable",
    "why": (
        "This helps determine whether the problem "
        "is related to internet connectivity or DNS."
    ),
    "expected_answer": "boolean"
}
```

## 8.3 User Interface Behavior

The diagnostic wizard should:

- Display one question at a time.
- Provide YES and NO buttons.
- Display a WHY THIS QUESTION? option.
- Show diagnostic progress.
- Allow users to review previous responses.
- Avoid asking questions that have already been answered.
- Display a diagnosis when sufficient evidence is available.

An optional UNKNOWN response can be considered for questions the user cannot answer. If implemented, it must remain distinct from NO.

---

# 9. EXPLANATION FACILITY

This is a mandatory teacher requirement.

The application must explain both WHY and HOW.

## 9.1 WHY Explanation

Whenever the system asks a question, it must explain why the answer is required.

Example:

Question:

"Can you access a website using its domain name?"

WHY?

"Your device appears to have external IP connectivity. We need to determine whether domain-name resolution is working correctly. This helps distinguish DNS problems from general internet connectivity problems."

## 9.2 HOW Explanation

After diagnosis, the system must show the reasoning behind its conclusion.

Example:

Diagnosis: DNS Resolution Failure

Rules Applied:

R09:

Conditions:

- External IP connectivity = TRUE
- Domain access = FALSE

Conclusion:

- DNS failure suspected.

R10:

Conditions:

- DNS failure suspected = TRUE
- Configured DNS server reachable = FALSE

Conclusion:

- DNS server failure suspected.

Final Result:

Possible DNS Server Failure.

## 9.3 Explanation Trace Structure

Store the following information for every fired rule:

```python
{
    "rule_id": "R09",
    "rule_name": "DNS Resolution Failure",
    "conditions": {
        "external_ip_reachable": True,
        "domain_access": False
    },
    "conditions_satisfied": True,
    "conclusion": {
        "dns_failure_suspected": True
    },
    "explanation": (
        "External IP access works, but domain-name "
        "resolution is unavailable."
    )
}
```

The frontend should display this as a readable inference chain.

---

# 10. RECOMMENDATION ENGINE

Each diagnostic conclusion should have an associated troubleshooting recommendation.

Examples:

### DNS Resolution Failure

1. Check the configured DNS server.
2. Flush the DNS cache.
3. Test an alternative DNS server.
4. Restart the network connection.
5. Repeat the diagnostic test.

### DHCP Configuration Failure

1. Check whether the router's DHCP service is enabled.
2. Verify that the DHCP address pool is available.
3. Renew the IP lease.
4. Restart the network connection.

### Gateway Connectivity Failure

1. Check the router's power.
2. Verify the device's connection to the router.
3. Check the default gateway configuration.
4. Restart the router if appropriate.

### Weak Wi-Fi Signal

1. Move closer to the router.
2. Reduce physical obstructions.
3. Check interference from nearby devices.
4. Consider using the 5 GHz or 2.4 GHz band as appropriate.

### Packet Loss / High Latency

1. Check network congestion.
2. Reduce unnecessary bandwidth usage.
3. Test with a wired connection.
4. Check router placement and connection quality.

### ISP Connectivity Failure

1. Check the ISP service status.
2. Verify that the router has an active internet connection.
3. Contact the ISP if the issue persists.

Recommendations must be connected to the diagnostic conclusions, not randomly generated.

---

# 11. USER INTERFACE DESIGN

The application should have a modern, professional SaaS dashboard aesthetic.

## 11.1 Design Direction

Visual style:

- Dark-first interface.
- Modern technical dashboard.
- Clean typography.
- Subtle gradients.
- Rounded cards.
- Minimal animations.
- Clear information hierarchy.
- Responsive design.

Suggested colors:

- Background: #0B0F19
- Card background: #111827
- Primary: #6366F1
- Success: #22C55E
- Warning: #F59E0B
- Error: #EF4444
- Primary text: #F9FAFB
- Secondary text: #9CA3AF

Use consistent spacing and accessible contrast.

## 11.2 Application Pages

### Page 1: Landing Page

Include:

- NetSage logo and branding.
- Project introduction.
- How it works section.
- Supported network problems.
- Start Troubleshooting CTA.
- Technical information.

### Page 2: Dashboard

Display:

- Welcome section.
- Start New Diagnosis button.
- Total diagnostic sessions.
- Commonly identified issues.
- Recent diagnostic activity.
- Knowledge base overview.

### Page 3: Diagnostic Wizard

Display:

- Current diagnostic question.
- YES and NO buttons.
- WHY THIS QUESTION? expandable section.
- Progress indicator.
- Previous response summary.
- Cancel diagnostic option.

### Page 4: Diagnosis Results

Display:

- Main diagnosis.
- Problem category.
- Severity indicator.
- Explanation summary.
- Supporting evidence.
- Recommended troubleshooting steps.
- Start New Diagnosis button.

### Page 5: Explanation Center

Display:

- Initial facts.
- Derived facts.
- Rules fired.
- Forward chaining trace.
- Backward chaining reasoning.
- Complete diagnostic decision path.

### Page 6: Diagnostic History

Display:

- Previous sessions.
- Date and time.
- Diagnosed issue.
- Session status.
- Detailed report access.

### Page 7: Knowledge Base Explorer

Display:

- Domain facts.
- Rule ID.
- Rule conditions.
- Rule conclusions.
- Rule explanations.

This page is especially useful for demonstrating the project's internal expert system.

---

# 12. BACKEND API DESIGN

Use FastAPI.

Suggested endpoints:

## Diagnostic APIs

POST /api/diagnostics/start

Creates a new diagnostic session.

POST /api/diagnostics/{session_id}/answer

Submits a YES/NO response and processes inference.

GET /api/diagnostics/{session_id}/question

Returns the next question.

GET /api/diagnostics/{session_id}/result

Returns the final diagnosis.

GET /api/diagnostics/{session_id}/explanation

Returns the explanation trace.

POST /api/diagnostics/{session_id}/restart

Restarts the diagnostic session.

## Knowledge Base APIs

GET /api/knowledge/facts

Returns all knowledge base facts.

GET /api/knowledge/rules

Returns all production rules.

GET /api/knowledge/stats

Returns knowledge base statistics.

## History APIs

GET /api/history

Returns previous diagnostic sessions.

GET /api/history/{session_id}

Returns an individual diagnostic report.

DELETE /api/history/{session_id}

Deletes a diagnostic session.

Use Pydantic schemas for request and response validation.

---

# 13. DATABASE DESIGN

Use SQLite for the initial implementation.

### Table: diagnostic_sessions

Fields:

- id
- created_at
- completed_at
- status
- final_diagnosis
- diagnosis_category
- summary

### Table: diagnostic_answers

Fields:

- id
- session_id
- question_id
- question_text
- answer
- answered_at

### Table: inference_traces

Fields:

- id
- session_id
- rule_id
- rule_name
- conditions
- conclusion
- explanation
- execution_order

### Table: recommendations

Fields:

- id
- session_id
- recommendation_text
- priority
- completed

The knowledge base and rules should initially remain in version-controlled Python files rather than being stored in the database.

---

# 14. PROJECT DIRECTORY STRUCTURE

Use a monorepo architecture.

```text
netsage/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── diagnostic/
│   │   │   ├── explanation/
│   │   │   └── layout/
│   │   │
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   │
│   │   ├── expert_system/
│   │   │   ├── knowledge_base.py
│   │   │   ├── rules.py
│   │   │   ├── working_memory.py
│   │   │   ├── forward_chaining.py
│   │   │   ├── backward_chaining.py
│   │   │   ├── question_engine.py
│   │   │   ├── explanation_engine.py
│   │   │   ├── recommendation_engine.py
│   │   │   └── inference_engine.py
│   │   │
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── test_knowledge_base.py
│   │   ├── test_rules.py
│   │   ├── test_forward_chaining.py
│   │   ├── test_backward_chaining.py
│   │   ├── test_explanations.py
│   │   └── test_diagnostics.py
│   │
│   └── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── knowledge-base.md
│   ├── rule-base.md
│   ├── inference-engine.md
│   └── sample-runs.md
│
├── README.md
└── .gitignore
```

---

# 15. TESTING STRATEGY

The expert system must be tested independently before frontend integration.

## 15.1 Unit Testing

Test:

- Knowledge base initialization.
- Rule condition evaluation.
- Rule chaining.
- Working memory updates.
- Forward chaining termination.
- Backward chaining goal resolution.
- Question selection.
- Explanation generation.
- Recommendation generation.

## 15.2 Sample Diagnostic Runs

The final project must demonstrate at least three different diagnostic scenarios.

### Sample Run 1: DNS Resolution Failure

User responses:

```text
Device connected to network? YES

Valid IP configuration? YES

Gateway reachable? YES

External IP accessible? YES

Can websites be accessed by domain name? NO

Is the configured DNS server reachable? NO
```

Expected result:

Possible DNS Server Failure.

Expected inference:

R09 → R10

Recommended solution:

Check DNS configuration, flush DNS cache and test an alternative DNS server.

### Sample Run 2: DHCP Failure

User responses:

```text
Device connected to network? YES

Valid IP configuration? NO

Does the IP address begin with 169.254? YES
```

Expected result:

Possible DHCP Assignment Failure.

Expected inference:

R01 → R03 → R04

Recommended solution:

Check router DHCP configuration and renew the IP lease.

### Sample Run 3: Gateway Connectivity Failure

User responses:

```text
Device connected to network? YES

Valid IP configuration? YES

Gateway reachable? NO

Are other devices affected? YES
```

Expected result:

Possible Router or Gateway Connectivity Failure.

Expected inference:

R05 → R06 → R07 → R08

Recommended solution:

Check router power, physical connections and local network equipment.

These scenarios must be implemented as actual executable tests, not just screenshots or hardcoded frontend outputs.

---

# 16. DEVELOPMENT PHASES

Build the project incrementally.

## Phase 1 — Project Foundation

Tasks:

- Initialize Git repository.
- Configure React + TypeScript + Vite.
- Configure FastAPI.
- Create backend project structure.
- Configure SQLite and SQLAlchemy.
- Verify frontend-backend communication.
- Establish API error handling.

Deliverable:

Working frontend and backend foundations.

## Phase 2 — Knowledge Base and Rule Base

Tasks:

- Implement networking facts.
- Define at least 25 IF-THEN rules.
- Create structured rule objects.
- Define conditions and conclusions.
- Implement rule validation.
- Write initial unit tests.

Deliverable:

A working, independently testable knowledge and rule base.

## Phase 3 — Inference Engine

Tasks:

- Implement working memory.
- Implement condition evaluation.
- Implement forward chaining.
- Implement backward chaining.
- Implement chained inference.
- Prevent duplicate rule execution.
- Handle unknown facts.
- Resolve conflicting conclusions.

Deliverable:

Functional custom-built inference engine.

## Phase 4 — Explanation and Question Engine

Tasks:

- Implement dynamic question selection.
- Implement WHY explanations.
- Implement HOW explanations.
- Track fired rules.
- Track derived facts.
- Generate diagnostic reasoning paths.
- Implement recommendation mapping.

Deliverable:

Complete expert system core.

## Phase 5 — Backend Integration

Tasks:

- Create diagnostic APIs.
- Implement session management.
- Connect APIs to the inference engine.
- Implement answer processing.
- Return dynamic questions.
- Store diagnostic history.
- Return explanations and recommendations.

Deliverable:

Complete backend functionality.

## Phase 6 — Frontend Development

Tasks:

- Build landing page.
- Build dashboard.
- Build diagnostic wizard.
- Build result page.
- Build explanation center.
- Build knowledge base explorer.
- Build diagnostic history.
- Integrate all APIs.

Deliverable:

Complete web application.

## Phase 7 — Testing and Refinement

Tasks:

- Test all diagnostic categories.
- Test chained rules.
- Test both inference strategies.
- Test incomplete user responses.
- Test conflicting or ambiguous symptoms.
- Validate explanations.
- Improve user experience.
- Verify all teacher requirements.

Deliverable:

Stable, demonstrable project.

## Phase 8 — Documentation and Submission

Prepare:

- Project README.
- Problem statement.
- Knowledge base documentation.
- Rule base documentation.
- Inference algorithm explanation.
- System architecture diagram.
- Three sample execution runs.
- Screenshots.
- Final project report.
- Viva preparation notes.

Deliverable:

Complete academic project submission.

---

# 17. IMPORTANT DEVELOPMENT CONSTRAINTS

Antigravity must follow these instructions throughout development.

1. The core project is a Knowledge-Based Expert System, not an LLM chatbot.
2. All networking facts must be explicitly represented in the knowledge base.
3. All production rules must be defined separately from application logic.
4. The inference engine must be implemented manually in Python.
5. Both forward and backward chaining must work.
6. Intermediate conclusions must be reusable by other rules.
7. The system must maintain a working memory.
8. The question engine must dynamically select relevant questions.
9. WHY and HOW explanations are mandatory.
10. Every final diagnosis must have an identifiable reasoning path.
11. Do not hardcode diagnostic results in React.
12. Do not use random diagnosis generation.
13. Do not fabricate confidence percentages.
14. Do not treat UNKNOWN facts as FALSE.
15. Do not use ready-made expert system frameworks.
16. Keep the backend modular and maintainable.
17. Write comments for important algorithms and inference logic.
18. Implement proper error handling.
19. Keep the frontend responsive.
20. Do not start the next development phase until the current phase is tested.

## Important Networking Limitation

This is a web-based questionnaire-driven expert system.

The initial version does not directly inspect the visitor's operating system, router, or live network.

It uses answers supplied by the user to perform logical diagnosis.

Do not claim that the application has performed an actual ping, traceroute, DNS lookup or packet inspection unless those tests have genuinely been implemented.

The diagnostic conclusions should be presented as probable causes based on the available evidence.

---

# 18. ACCEPTANCE CRITERIA

The project will be considered complete when:

| Requirement             | Target                       |
| ----------------------- | ---------------------------- |
| Knowledge base          | Minimum 15 facts; target 25+ |
| Rule base               | Minimum 15 rules; target 25+ |
| Chained inference       | Working                      |
| Forward chaining        | Working                      |
| Backward chaining       | Working                      |
| Custom inference engine | Implemented in Python        |
| Working memory          | Implemented                  |
| Dynamic questions       | Working                      |
| WHY explanation         | Working                      |
| HOW explanation         | Working                      |
| Troubleshooting advice  | Working                      |
| Web interface           | Functional                   |
| Backend APIs            | Functional                   |
| Diagnostic history      | Functional                   |
| Sample diagnostic runs  | At least 3                   |
| Automated tests         | Passing                      |
| Documentation           | Complete                     |

---

# 19. INSTRUCTIONS FOR ANTIGRAVITY

Treat this document as the primary source of truth for the NetSage project.

You are acting as a senior full-stack engineer and AI systems architect.

Your responsibility is to implement the complete project according to the requirements above.

### Development approach

- First inspect the existing repository.
- Identify existing code before creating new files.
- Follow the defined architecture.
- Implement the expert system independently of the frontend.
- Prioritize correctness of the inference algorithms.
- Write tests for the knowledge base, rule base and inference engine.
- Integrate the backend only after the core engine works.
- Build the frontend around actual backend responses.
- Do not replace the expert system with hardcoded conditions inside React.
- Do not introduce unnecessary technologies.
- Maintain consistent coding standards.
- Update the README and documentation as development progresses.

### Phase-based execution

Work phase by phase.

For every phase:

1. Explain the implementation plan.
2. Implement the required functionality.
3. Run relevant tests.
4. Fix errors.
5. Summarize completed work.
6. Identify remaining tasks.
7. Wait for approval before proceeding to the next major phase.

### Final objective

Deliver a fully functional web-based Knowledge-Based Network Troubleshooting Expert System that demonstrates:

- Knowledge representation.
- Production rules.
- Forward chaining.
- Backward chaining.
- Rule chaining.
- Dynamic question generation.
- Explanation facilities.
- Logical network fault diagnosis.
- Troubleshooting recommendations.

The quality and correctness of the expert system take priority over visual complexity.

**Project Identity: NetSage — Intelligent Network Troubleshooting Expert System.**

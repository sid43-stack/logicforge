# NetSage Inference Engine Documentation

The NetSage custom inference engine is a native, handcrafted Python expert system engine designed without third-party rule engines (e.g. `Experta`, `PyKnow`) or machine learning models.

---

## 1. Engine Components & Architecture

```text
                     +---------------------------------------+
                     |            InferenceEngine            |
                     |               (Facade)                |
                     +-------------------+-------------------+
                                         |
            +----------------------------+----------------------------+
            |                            |                            |
            v                            v                            v
  +-------------------+        +--------------------+       +--------------------+
  |   WorkingMemory   |        |  Forward Chaining  |       | Backward Chaining  |
  |  (3-Valued Logic) |<------>|      (Deduction)   |<----->|   (Goal Resolution)|
  +-------------------+        +--------------------+       +--------------------+
```

### 1.1 Tri-State Working Memory (`WorkingMemory`)
- **Truth States**:
  - `TRUE`: Confirmed true fact.
  - `FALSE`: Confirmed false fact.
  - `UNKNOWN`: Missing or unasked fact. An unasked fact is **never** conflated with `FALSE`.
- **Knowledge Tiers**:
  - `USER_INPUT`: Answers provided by the user.
  - `RULE_DERIVED`: Inferred facts asserted by fired production rules.
  - `STATIC_DOMAIN`: Axioms loaded from domain knowledge.
- **Change Tracking & Audit Log**: Ordered history of every assertion and update with timestamps.
- **Snapshot Persistence**: Serializes complete memory to JSON-compatible dictionaries and restores state with 100% fidelity.
- **Contradiction Guard**: Flags contradictory assertions (e.g. attempting to assert `False` when `True` is already established).

### 1.2 Forward Chaining Engine (`ForwardChainingEngine`)
- **Data-Driven Deduction Loop**:
  1. Find rules where `rule.id not in fired_rule_ids`.
  2. Evaluate conditions: rule fires **only** if all conditions evaluate to `TriState.TRUE`.
  3. **Conflict Resolution**: Sort eligible rules by `priority DESC`, then `id ASC`.
  4. Fire the top rule, asserting conclusions into `WorkingMemory` with `source_type=RULE_DERIVED`.
  5. Record detailed `InferenceTraceStep`.
  6. Repeat until no more rules can fire (fix-point reached).
- **Cycle Guard**: Iteration limit prevents infinite loops in cyclic rule bases.
- **Contradiction Detection**: Captures conflicting terminal diagnoses if multiple mutually exclusive conclusions are generated.

### 1.3 Backward Chaining Engine (`BackwardChainingEngine`)
- **Goal-Directed Hypothesis Resolution**:
  1. Identifies supporting rules concluding the target hypothesis ($H$).
  2. Recursively evaluates rule premises against `WorkingMemory`.
  3. Condition already `TRUE` $\to$ satisfied.
  4. Condition already `FALSE` $\to$ rule eliminated.
  5. Condition `UNKNOWN` $\to$ checks if producible by a sub-rule (recurses with call-stack cycle guard) or marks as an **askable premise**.
- **Dynamic Question Selection**:
  - Scans active diagnostic hypotheses in priority order.
  - Computes the most informative unasked premise to query the user next.
- **Goal Trees**: Constructs `GoalTreeNode` and `RuleGoalNode` trees for the Explanation Center.

---

## 2. Complete Execution Traces Across All 6 Diagnostic Categories

### Scenario 1: Category A — IP / DHCP Configuration Failure
**User Responses**:
- `device_connected = True`
- `ip_is_apipa = True`
- `valid_ip = False`
- `multiple_devices_affected = True`

**Execution Trace**:
```text
Step 1: Rule R01 fired (APIPA Detection)
  Conditions: device_connected=True, ip_is_apipa=True
  Conclusion: dhcp_failure_suspected=True
  Classification: INTERMEDIATE

Step 2: Rule R03 fired (DHCP Server Unavailability Chaining)
  Conditions: dhcp_failure_suspected=True, valid_ip=False
  Conclusion: dhcp_server_unavailable=True
  Classification: INTERMEDIATE

Step 3: Rule R04 fired (Router DHCP Server Failure Diagnosis)
  Conditions: dhcp_server_unavailable=True, multiple_devices_affected=True
  Conclusion: diagnosis="Router DHCP Server Failure", severity="HIGH"
  Classification: TERMINAL_DIAGNOSIS
```

---

### Scenario 2: Category B — Gateway Connectivity Failure
**User Responses**:
- `valid_ip = True`
- `gateway_reachable = False`
- `multiple_devices_affected = True`
- `router_reboot_temporarily_fixed = True`

**Execution Trace**:
```text
Step 1: Rule R06 fired (Default Gateway Unreachable Detection)
  Conditions: valid_ip=True, gateway_reachable=False
  Conclusion: gateway_failure_suspected=True
  Classification: INTERMEDIATE

Step 2: Rule R07 fired (Local Segment Link Problem Chaining)
  Conditions: gateway_failure_suspected=True
  Conclusion: local_network_problem=True
  Classification: INTERMEDIATE

Step 3: Rule R08 fired (Router Hardware Failure Suspicion)
  Conditions: gateway_failure_suspected=True, multiple_devices_affected=True
  Conclusion: router_hardware_suspected=True
  Classification: INTERMEDIATE

Step 4: Rule R09 fired (Router Gateway Crash / Hardware Overload Diagnosis)
  Conditions: router_hardware_suspected=True, router_reboot_temporarily_fixed=True
  Conclusion: diagnosis="Router Gateway Crash / Hardware Overload", severity="HIGH"
  Classification: TERMINAL_DIAGNOSIS
```

---

### Scenario 3: Category C — DNS Resolution Failure
**User Responses**:
- `external_ip_reachable = True`
- `domain_access = False`
- `dns_server_reachable = False`
- `multiple_devices_affected = True`

**Execution Trace**:
```text
Step 1: Rule R11 fired (DNS Resolution Failure Detection)
  Conditions: external_ip_reachable=True, domain_access=False
  Conclusion: dns_failure_suspected=True
  Classification: INTERMEDIATE

Step 2: Rule R12 fired (DNS Server Reachability Chaining)
  Conditions: dns_failure_suspected=True, dns_server_reachable=False
  Conclusion: dns_server_failure_suspected=True
  Classification: INTERMEDIATE

Step 3: Rule R13 fired (Upstream DNS Provider Outage Diagnosis)
  Conditions: dns_server_failure_suspected=True, multiple_devices_affected=True
  Conclusion: diagnosis="Upstream DNS Provider Outage", severity="HIGH"
  Classification: TERMINAL_DIAGNOSIS
```

---

### Scenario 4: Category D — Wi-Fi Weak Signal & Range Limitation
**User Responses**:
- `using_wifi = True`
- `wifi_signal_weak = True`
- `frequent_disconnections = True`
- `problem_on_ethernet_too = False`

**Execution Trace**:
```text
Step 1: Rule R17 fired (Weak Wi-Fi Signal Detection)
  Conditions: using_wifi=True, wifi_signal_weak=True
  Conclusion: weak_wifi_suspected=True
  Classification: INTERMEDIATE

Step 2: Rule R18 fired (Wireless Link Instability Chaining)
  Conditions: weak_wifi_suspected=True, frequent_disconnections=True
  Conclusion: wireless_instability_suspected=True
  Classification: INTERMEDIATE

Step 3: Rule R19 fired (Wi-Fi Signal Attenuation & Range Limitation Diagnosis)
  Conditions: wireless_instability_suspected=True, problem_on_ethernet_too=False
  Conclusion: diagnosis="Wi-Fi Signal Attenuation and Range Limitation", severity="MEDIUM"
  Classification: TERMINAL_DIAGNOSIS
```

---

### Scenario 5: Category E — Network Bufferbloat & Latency Congestion
**User Responses**:
- `high_latency_observed = True`
- `heavy_bandwidth_usage = True`

**Execution Trace**:
```text
Step 1: Rule R21 fired (Network Degradation Detection)
  Conditions: high_latency_observed=True
  Conclusion: network_performance_degraded=True
  Classification: INTERMEDIATE

Step 2: Rule R22 fired (Network Congestion Chaining)
  Conditions: network_performance_degraded=True, heavy_bandwidth_usage=True
  Conclusion: network_congestion_suspected=True
  Classification: INTERMEDIATE

Step 3: Rule R23 fired (Local Network Bufferbloat & Congestion Diagnosis)
  Conditions: network_congestion_suspected=True
  Conclusion: diagnosis="Local Network Bufferbloat & Bandwidth Saturation", severity="MEDIUM"
  Classification: TERMINAL_DIAGNOSIS
```

---

### Scenario 6: Category F — Wide-Area ISP Service Outage
**User Responses**:
- `gateway_reachable = True`
- `external_ip_reachable = False`
- `multiple_devices_affected = True`

**Execution Trace**:
```text
Step 1: Rule R25 fired (ISP External Connectivity Failure Detection)
  Conditions: gateway_reachable=True, external_ip_reachable=False
  Conclusion: isp_failure_suspected=True
  Classification: INTERMEDIATE

Step 2: Rule R26 fired (ISP Outage Chaining)
  Conditions: isp_failure_suspected=True, multiple_devices_affected=True
  Conclusion: isp_outage_suspected=True
  Classification: INTERMEDIATE

Step 3: Rule R27 fired (Wide-Area ISP Service Outage Diagnosis)
  Conditions: isp_outage_suspected=True
  Conclusion: diagnosis="Wide-Area ISP Service Outage", severity="CRITICAL"
  Classification: TERMINAL_DIAGNOSIS
```


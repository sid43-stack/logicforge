"""NetSage Production Rule Base - IF-THEN Diagnostic Rules.

Strictly decoupled from FastAPI and React.
Defines 28 logically sound, verified production rules with genuine multi-step
rule chaining across all six diagnostic categories:
- Category A: IP / DHCP Configuration (R01 - R05)
- Category B: Gateway Connectivity (R06 - R10)
- Category C: DNS Resolution (R11 - R16)
- Category D: Wi-Fi Wireless (R17 - R20)
- Category E: Network Performance & Latency (R21 - R24)
- Category F: ISP / External Connectivity (R25 - R28)
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.expert_system.types import (
    TriState,
    Condition,
    Operator,
    RuleCategory,
    RuleClassification,
)


class Rule(BaseModel):
    """Represents a formal IF-THEN production rule in the NetSage Rule Base."""
    id: str = Field(..., description="Unique rule identifier, e.g., R01")
    name: str = Field(..., description="Descriptive human-readable rule name")
    category: RuleCategory = Field(..., description="Problem domain category")
    priority: int = Field(default=75, description="Firing priority: higher value fires first")
    classification: RuleClassification = Field(
        default=RuleClassification.INTERMEDIATE,
        description="Whether this rule derives an intermediate fact or a terminal diagnosis"
    )
    conditions: List[Condition] = Field(..., description="Antecedent conditions (conjunction AND)")
    conclusions: Dict[str, Any] = Field(..., description="Consequent assertions added to working memory")
    explanation: str = Field(..., description="Clear reasoning why this rule fired")

    def evaluate_conditions(self, facts: Dict[str, Any]) -> TriState:
        """Evaluates antecedent conditions under 3-valued logic (TRUE, FALSE, UNKNOWN).
        
        Logic Rules for Conjunction (AND):
        - If ANY condition is FALSE -> Rule is definitively FALSE (refuted).
        - If NO condition is FALSE, but AT LEAST ONE is UNKNOWN -> Rule is UNKNOWN (candidate for backward inquiry).
        - If ALL conditions are TRUE -> Rule is TRUE (ready to fire).
        """
        has_unknown = False
        for condition in self.conditions:
            actual_val = facts.get(condition.fact_key, TriState.UNKNOWN)
            result = condition.evaluate(actual_val)
            if result == TriState.FALSE:
                return TriState.FALSE
            if result == TriState.UNKNOWN:
                has_unknown = True

        return TriState.UNKNOWN if has_unknown else TriState.TRUE


# -------------------------------------------------------------------------
# NetSage Production Rule Definitions (R01 - R28)
# -------------------------------------------------------------------------

PRODUCTION_RULES: List[Rule] = [
    # =====================================================================
    # CATEGORY A: IP / DHCP PROBLEMS (R01 - R05)
    # =====================================================================
    Rule(
        id="R01",
        name="Automatic IP Configuration Failure (APIPA Detection)",
        category=RuleCategory.IP_DHCP,
        priority=80,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="ip_is_apipa", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"dhcp_failure_suspected": True},
        explanation="Device is connected to the network but received an APIPA address (169.254.x.x), indicating DHCP assignment failed."
    ),
    Rule(
        id="R02",
        name="Invalid IP Configuration Detection",
        category=RuleCategory.IP_DHCP,
        priority=75,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="device_connected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="valid_ip", operator=Operator.EQUALS, value=False),
            Condition(fact_key="ip_is_apipa", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"ip_config_failure": True},
        explanation="Device is connected but does not possess a valid routable IP configuration."
    ),
    Rule(
        id="R03",
        name="DHCP Server Unavailability Chaining",
        category=RuleCategory.IP_DHCP,
        priority=85,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="dhcp_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="valid_ip", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"dhcp_server_unavailable": True},
        explanation="DHCP failure is suspected and device lacks a valid IP, confirming the local DHCP service is unavailable."
    ),
    Rule(
        id="R04",
        name="Router DHCP Server Failure Diagnosis",
        category=RuleCategory.IP_DHCP,
        priority=90,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="dhcp_server_unavailable", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "Router DHCP Server Failure",
            "diagnosis_category": "IP_DHCP",
            "diagnosis_severity": "HIGH",
            "recommendation_code": "REC_DHCP_ROUTER"
        },
        explanation="Multiple devices are unable to obtain IP addresses via DHCP, pointing to a router DHCP daemon failure or address pool exhaustion."
    ),
    Rule(
        id="R05",
        name="Host DHCP Client Lease Failure Diagnosis",
        category=RuleCategory.IP_DHCP,
        priority=88,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="dhcp_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Host DHCP Client Lease Failure",
            "diagnosis_category": "IP_DHCP",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_DHCP_CLIENT"
        },
        explanation="DHCP failure is isolated to this single host, indicating a local network adapter or DHCP client service failure."
    ),

    # =====================================================================
    # CATEGORY B: GATEWAY CONNECTIVITY PROBLEMS (R06 - R10)
    # =====================================================================
    Rule(
        id="R06",
        name="Default Gateway Unreachable Detection",
        category=RuleCategory.GATEWAY,
        priority=80,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="valid_ip", operator=Operator.EQUALS, value=True),
            Condition(fact_key="gateway_reachable", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"gateway_failure_suspected": True},
        explanation="Device holds a valid IP address but cannot reach or ping its default gateway."
    ),
    Rule(
        id="R07",
        name="Local Segment Link Problem Chaining",
        category=RuleCategory.GATEWAY,
        priority=75,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="gateway_failure_suspected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"local_network_problem": True},
        explanation="Inability to communicate with default gateway isolates the problem to the local physical or Layer 2 segment."
    ),
    Rule(
        id="R08",
        name="Router Hardware Failure Suspicion",
        category=RuleCategory.GATEWAY,
        priority=85,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="gateway_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"router_hardware_suspected": True},
        explanation="Gateway is unreachable across multiple devices, indicating a router hardware, crash, or local switch failure."
    ),
    Rule(
        id="R09",
        name="Router Gateway Crash / Hardware Overload Diagnosis",
        category=RuleCategory.GATEWAY,
        priority=90,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="router_hardware_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="router_reboot_temporarily_fixed", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "Router Gateway Crash / Hardware Overload",
            "diagnosis_category": "GATEWAY",
            "diagnosis_severity": "HIGH",
            "recommendation_code": "REC_GATEWAY_REBOOT"
        },
        explanation="Router gateway locks up under load and reboot temporarily restores communication, confirming router firmware or RAM exhaustion."
    ),
    Rule(
        id="R10",
        name="Host Gateway Route / ARP Failure Diagnosis",
        category=RuleCategory.GATEWAY,
        priority=88,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="gateway_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Local Gateway Connectivity Failure (Host Specific)",
            "diagnosis_category": "GATEWAY",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_GATEWAY_LOCAL"
        },
        explanation="Only this device cannot ping the gateway while other devices can, pointing to a local subnet mismatch, bad static route, or corrupted ARP cache."
    ),

    # =====================================================================
    # CATEGORY C: DNS PROBLEMS (R11 - R16)
    # =====================================================================
    Rule(
        id="R11",
        name="DNS Resolution Failure Detection",
        category=RuleCategory.DNS,
        priority=85,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="external_ip_reachable", operator=Operator.EQUALS, value=True),
            Condition(fact_key="domain_access", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"dns_failure_suspected": True},
        explanation="External IP is directly reachable (proving internet routing works), but domain names cannot be resolved."
    ),
    Rule(
        id="R12",
        name="DNS Server Reachability Chaining",
        category=RuleCategory.DNS,
        priority=88,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="dns_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="dns_server_reachable", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"dns_server_failure_suspected": True},
        explanation="DNS failure is suspected and the assigned DNS server IP does not respond to ping."
    ),
    Rule(
        id="R13",
        name="Upstream DNS Provider Outage Diagnosis",
        category=RuleCategory.DNS,
        priority=92,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="dns_server_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "Upstream DNS Provider Outage",
            "diagnosis_category": "DNS",
            "diagnosis_severity": "HIGH",
            "recommendation_code": "REC_DNS_UPSTREAM"
        },
        explanation="Configured DNS server is unreachable across multiple devices on the network, confirming an upstream ISP or DNS provider outage."
    ),
    Rule(
        id="R14",
        name="Invalid Host DNS Server Configuration Diagnosis",
        category=RuleCategory.DNS,
        priority=90,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="dns_server_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Invalid Local DNS Server Configuration",
            "diagnosis_category": "DNS",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_DNS_LOCAL"
        },
        explanation="Assigned DNS server is unreachable only on this host, indicating incorrect static DNS entry or host-level firewall block."
    ),
    Rule(
        id="R15",
        name="DNS Cache or Resolver Glitch Chaining",
        category=RuleCategory.DNS,
        priority=86,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="dns_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="dns_server_reachable", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"dns_config_problem_suspected": True},
        explanation="DNS server is reachable via ping, but name resolution fails, indicating cached corrupt records or port 53 UDP filtering."
    ),
    Rule(
        id="R16",
        name="DNS Cache Corruption / Local Resolver Failure Diagnosis",
        category=RuleCategory.DNS,
        priority=84,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="dns_config_problem_suspected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "DNS Cache Corruption / Local Resolver Failure",
            "diagnosis_category": "DNS",
            "diagnosis_severity": "LOW",
            "recommendation_code": "REC_DNS_FLUSH"
        },
        explanation="DNS server responds but lookup fails, pointing to stale OS DNS resolver cache or corrupted hosts file."
    ),

    # =====================================================================
    # CATEGORY D: WI-FI PROBLEMS (R17 - R20)
    # =====================================================================
    Rule(
        id="R17",
        name="Weak Wi-Fi Signal Detection",
        category=RuleCategory.WIFI,
        priority=75,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="using_wifi", operator=Operator.EQUALS, value=True),
            Condition(fact_key="wifi_signal_weak", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"weak_wifi_suspected": True},
        explanation="Device is connected to Wi-Fi with weak radio signal strength (low RSSI)."
    ),
    Rule(
        id="R18",
        name="Wireless Link Instability Chaining",
        category=RuleCategory.WIFI,
        priority=80,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="weak_wifi_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="frequent_disconnections", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"wireless_instability_suspected": True},
        explanation="Weak Wi-Fi signal combined with frequent disconnections confirms severe RF link instability."
    ),
    Rule(
        id="R19",
        name="Wi-Fi Signal Attenuation & Range Limitation Diagnosis",
        category=RuleCategory.WIFI,
        priority=85,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="wireless_instability_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="problem_on_ethernet_too", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Wi-Fi Signal Attenuation and Range Limitation",
            "diagnosis_category": "WIFI",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_WIFI_RANGE"
        },
        explanation="Wireless connection suffers drops due to low signal while Ethernet works cleanly, confirming excessive physical distance or RF obstruction."
    ),
    Rule(
        id="R20",
        name="Wireless Radio Interference / Channel Congestion Diagnosis",
        category=RuleCategory.WIFI,
        priority=82,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="using_wifi", operator=Operator.EQUALS, value=True),
            Condition(fact_key="wifi_signal_weak", operator=Operator.EQUALS, value=False),
            Condition(fact_key="frequent_disconnections", operator=Operator.EQUALS, value=True),
            Condition(fact_key="problem_on_ethernet_too", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Wireless Radio Interference / Channel Congestion",
            "diagnosis_category": "WIFI",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_WIFI_INTERFERENCE"
        },
        explanation="Wi-Fi signal strength is strong yet disconnections occur only on Wi-Fi, indicating co-channel interference from neighboring APs or microwave/Bluetooth sources."
    ),

    # =====================================================================
    # CATEGORY E: PERFORMANCE / LATENCY / PACKET LOSS (R21 - R24)
    # =====================================================================
    Rule(
        id="R21",
        name="Network Degradation Detection",
        category=RuleCategory.PERFORMANCE,
        priority=70,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="high_latency_observed", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"network_performance_degraded": True},
        explanation="Consistent round-trip latency exceeding normal thresholds indicates network performance degradation."
    ),
    Rule(
        id="R22",
        name="Network Congestion Chaining",
        category=RuleCategory.PERFORMANCE,
        priority=75,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="network_performance_degraded", operator=Operator.EQUALS, value=True),
            Condition(fact_key="heavy_bandwidth_usage", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"network_congestion_suspected": True},
        explanation="High latency concurrent with heavy local bandwidth usage confirms local egress queue congestion."
    ),
    Rule(
        id="R23",
        name="Local Network Bufferbloat & Congestion Diagnosis",
        category=RuleCategory.PERFORMANCE,
        priority=80,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="network_congestion_suspected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "Local Network Bufferbloat & Bandwidth Saturation",
            "diagnosis_category": "PERFORMANCE",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_PERF_CONGESTION"
        },
        explanation="Heavy traffic saturating router egress queues causes router bufferbloat and latency spikes."
    ),
    Rule(
        id="R24",
        name="Physical Line Degradation / Upstream Packet Loss Diagnosis",
        category=RuleCategory.PERFORMANCE,
        priority=82,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="network_performance_degraded", operator=Operator.EQUALS, value=True),
            Condition(fact_key="packet_loss_observed", operator=Operator.EQUALS, value=True),
            Condition(fact_key="heavy_bandwidth_usage", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Physical Line Degradation or ISP Packet Loss",
            "diagnosis_category": "PERFORMANCE",
            "diagnosis_severity": "HIGH",
            "recommendation_code": "REC_PERF_PACKETLOSS"
        },
        explanation="Packet loss occurs without local bandwidth saturation, indicating physical line noise, bad Ethernet cabling, or upstream ISP router drops."
    ),

    # =====================================================================
    # CATEGORY F: ISP / INTERNET CONNECTIVITY PROBLEMS (R25 - R28)
    # =====================================================================
    Rule(
        id="R25",
        name="ISP External Connectivity Failure Detection",
        category=RuleCategory.ISP,
        priority=85,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="gateway_reachable", operator=Operator.EQUALS, value=True),
            Condition(fact_key="external_ip_reachable", operator=Operator.EQUALS, value=False),
        ],
        conclusions={"isp_failure_suspected": True},
        explanation="Local gateway is reachable, but outside public IP addresses cannot be reached, isolating the fault to the WAN interface or ISP."
    ),
    Rule(
        id="R26",
        name="ISP Outage Chaining",
        category=RuleCategory.ISP,
        priority=90,
        classification=RuleClassification.INTERMEDIATE,
        conditions=[
            Condition(fact_key="isp_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={"isp_outage_suspected": True},
        explanation="External IP unreachable across multiple independent devices confirms an infrastructure-wide internet outage."
    ),
    Rule(
        id="R27",
        name="Wide-Area ISP Service Outage Diagnosis",
        category=RuleCategory.ISP,
        priority=95,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="isp_outage_suspected", operator=Operator.EQUALS, value=True),
        ],
        conclusions={
            "diagnosis": "Wide-Area ISP Service Outage",
            "diagnosis_category": "ISP",
            "diagnosis_severity": "CRITICAL",
            "recommendation_code": "REC_ISP_OUTAGE"
        },
        explanation="All local clients communicate with the gateway but cannot reach external internet, confirming an ISP fiber cut, DSLAM failure, or authentication outage."
    ),
    Rule(
        id="R28",
        name="Host Gateway Routing or Firewall Block Diagnosis",
        category=RuleCategory.ISP,
        priority=88,
        classification=RuleClassification.TERMINAL_DIAGNOSIS,
        conditions=[
            Condition(fact_key="isp_failure_suspected", operator=Operator.EQUALS, value=True),
            Condition(fact_key="multiple_devices_affected", operator=Operator.EQUALS, value=False),
        ],
        conclusions={
            "diagnosis": "Host-Specific Gateway Routing or Firewall Block",
            "diagnosis_category": "ISP",
            "diagnosis_severity": "MEDIUM",
            "recommendation_code": "REC_HOST_FIREWALL"
        },
        explanation="Other local network devices have internet access while this host cannot reach external IPs, pointing to a host firewall rule or router parental control/MAC filter."
    ),
]


# Map Rule ID to Rule object
RULES_BY_ID: Dict[str, Rule] = {rule.id: rule for rule in PRODUCTION_RULES}


def get_rule(rule_id: str) -> Optional[Rule]:
    """Retrieve a production rule by its ID."""
    return RULES_BY_ID.get(rule_id)


def get_all_rules() -> List[Rule]:
    """Return all production rules."""
    return list(PRODUCTION_RULES)


def get_rules_by_category(category: RuleCategory) -> List[Rule]:
    """Filter production rules by category."""
    return [rule for rule in PRODUCTION_RULES if rule.category == category]


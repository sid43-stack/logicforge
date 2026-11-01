"""NetSage Knowledge Base - Static Domain Axioms and Fact Definitions.

Strictly decoupled from FastAPI and React.
Defines 30 verified computer networking domain facts and formally registers
user-askable facts and rule-derived intermediate facts.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.expert_system.types import FactCategory, FactSourceType


class Fact(BaseModel):
    """Represents a structured domain fact in the NetSage Knowledge Base."""
    id: str = Field(..., description="Unique fact identifier, e.g., F01")
    key: str = Field(..., description="Internal variable key for inference")
    statement: str = Field(..., description="Human-readable factual principle")
    category: FactCategory = Field(..., description="Networking problem category")
    description: str = Field(..., description="Detailed technical explanation")
    source_type: FactSourceType = Field(default=FactSourceType.STATIC_DOMAIN)
    diagnostic_relevance: str = Field(..., description="How this fact guides diagnosis")


# -------------------------------------------------------------------------
# Static Domain Knowledge Base (30 Verified Networking Axioms)
# -------------------------------------------------------------------------

DOMAIN_FACTS: List[Fact] = [
    Fact(
        id="F01",
        key="router_function",
        statement="A router connects a local area network (LAN) to external networks and routes IP packets.",
        category=FactCategory.GENERAL,
        description="Routers operate at OSI Layer 3 (Network) to forward packets between distinct IP subnets.",
        diagnostic_relevance="If the local device cannot reach the router, no external internet communication is possible."
    ),
    Fact(
        id="F02",
        key="gateway_function",
        statement="A default gateway provides an exit point from a local subnet to remote destinations.",
        category=FactCategory.GATEWAY,
        description="Traffic destined outside the local broadcast domain must be forwarded to the gateway MAC address.",
        diagnostic_relevance="An unreachable gateway pinpoints the fault to the local link or router rather than remote servers."
    ),
    Fact(
        id="F03",
        key="dns_function",
        statement="DNS translates human-readable domain names into numeric IP addresses.",
        category=FactCategory.DNS,
        description="The Domain Name System translates hostnames (e.g., google.com) into IP addresses (e.g., 142.250.190.46).",
        diagnostic_relevance="Differentiates between total connectivity loss and name-resolution failure."
    ),
    Fact(
        id="F04",
        key="dhcp_function",
        statement="DHCP automatically leases IP configuration, subnet mask, default gateway, and DNS servers to clients.",
        category=FactCategory.IP_DHCP,
        description="Dynamic Host Configuration Protocol simplifies host configuration via DORA (Discover, Offer, Request, Ack).",
        diagnostic_relevance="DHCP failure prevents the client from obtaining valid IP configuration to communicate."
    ),
    Fact(
        id="F05",
        key="apipa_addressing",
        statement="An Automatic Private IP Address (APIPA) in 169.254.0.0/16 indicates an unfulfilled DHCP request.",
        category=FactCategory.IP_DHCP,
        description="When DHCP discovery times out, IPv4 link-local address autoconfiguration assigns an address from 169.254.0.0/16.",
        diagnostic_relevance="Direct evidence that the client cannot communicate with any active DHCP server on the local link."
    ),
    Fact(
        id="F06",
        key="valid_config_requirement",
        statement="A host requires a valid IP address, subnet mask, and default gateway for routable network communication.",
        category=FactCategory.GENERAL,
        description="Without a valid IP and subnet mask, IP stack initialization cannot route packets beyond loopback.",
        diagnostic_relevance="Validates whether basic host network stack initialization has succeeded."
    ),
    Fact(
        id="F07",
        key="unreachable_gateway_local_fault",
        statement="An unreachable default gateway indicates a local layer-1, layer-2, or router crash problem.",
        category=FactCategory.GATEWAY,
        description="If ARP fails or ICMP to the gateway yields no reply, the fault is isolated to the local segment.",
        diagnostic_relevance="Eliminates remote WAN or cloud service outages as the root cause."
    ),
    Fact(
        id="F08",
        key="dns_failure_domain_impact",
        statement="DNS resolution failure prevents accessing websites by hostname while raw IP access continues to function.",
        category=FactCategory.DNS,
        description="When DNS servers fail to answer queries, socket connections by name abort with resolution errors.",
        diagnostic_relevance="Signature symptom of DNS failure: pinging an external IP succeeds, but pinging domain names fails."
    ),
    Fact(
        id="F09",
        key="external_ip_connectivity_isolation",
        statement="Successful external IP ping confirms Layer 3 WAN routing and eliminates local gateway or ISP link failure.",
        category=FactCategory.DNS,
        description="Reaching public IPs (e.g. 8.8.8.8) proves routing and NAT are active through the ISP.",
        diagnostic_relevance="Crucial boundary test: rules out physical link, gateway, and ISP layer-3 outages."
    ),
    Fact(
        id="F10",
        key="weak_wifi_instability",
        statement="Low Received Signal Strength Indicator (RSSI below -75 dBm) causes frame drops and connection instability.",
        category=FactCategory.WIFI,
        description="Weak RF signals decrease Signal-to-Noise Ratio (SNR), triggering MCS rate drops and high retry rates.",
        diagnostic_relevance="Identifies RF propagation limitations as the root cause of intermittent drops."
    ),
    Fact(
        id="F11",
        key="rf_attenuation_factors",
        statement="Physical obstacles (concrete walls, metal) and distance severely attenuate 2.4 GHz and 5 GHz Wi-Fi signals.",
        category=FactCategory.WIFI,
        description="Free space path loss and material absorption attenuate wireless RF energy exponentially with distance.",
        diagnostic_relevance="Explains why Wi-Fi degradation is localized to specific rooms or physical locations."
    ),
    Fact(
        id="F12",
        key="packet_loss_consequence",
        statement="Packet loss causes TCP retransmissions, head-of-line blocking, and catastrophic throughput degradation.",
        category=FactCategory.PERFORMANCE,
        description="Dropped packets force TCP congestion windows to collapse, drastically degrading transfer speeds.",
        diagnostic_relevance="Distinguishes high-latency but intact links from damaged physical media or congested queues."
    ),
    Fact(
        id="F13",
        key="latency_impact",
        statement="High Round-Trip Time (RTT) increases communication delay and degrades interactive applications.",
        category=FactCategory.PERFORMANCE,
        description="Network latency represents propagation delay, serialization delay, and queuing delay across hops.",
        diagnostic_relevance="Explains poor real-time performance (buffering, VoIP drops, gaming lag) despite nominal bandwidth."
    ),
    Fact(
        id="F14",
        key="network_congestion_causes",
        statement="Heavy concurrent bandwidth consumption causes router bufferbloat, spiking latency and packet loss.",
        category=FactCategory.PERFORMANCE,
        description="When egress queues fill faster than the link can drain, latency inflates and excess packets are dropped.",
        diagnostic_relevance="Distinguishes equipment breakdown from temporary multi-user bandwidth saturation."
    ),
    Fact(
        id="F15",
        key="multiple_device_correlation",
        statement="Simultaneous connectivity failure on multiple independent devices proves an infrastructure-level fault.",
        category=FactCategory.ISP,
        description="Correlation across disparate OS and client hardware isolates the fault to shared network infrastructure.",
        diagnostic_relevance="Distinguishes host-specific driver/OS misconfigurations from router or ISP-wide failures."
    ),
    Fact(
        id="F16",
        key="router_reboot_clears_state",
        statement="Rebooting network hardware flushes routing tables, clears ARP caches, and resets exhausted NAT states.",
        category=FactCategory.GATEWAY,
        description="Consumer routers frequently lock up when connection tracking (conntrack) tables overflow.",
        diagnostic_relevance="If a reboot temporarily fixes the problem, router hardware exhaustion or firmware bug is diagnosed."
    ),
    Fact(
        id="F17",
        key="dns_server_misconfiguration",
        statement="An incorrect or unassigned DNS server IP in client network settings prevents all name resolution.",
        category=FactCategory.DNS,
        description="Clients querying non-existent or unreachable DNS server IPs encounter connection timeouts.",
        diagnostic_relevance="Focuses remediation on changing client or router DNS resolver addresses (e.g. to 8.8.8.8)."
    ),
    Fact(
        id="F18",
        key="ip_subnet_mismatch",
        statement="An IP address outside the gateway subnet prevents direct Layer 2 ARP communication with the gateway.",
        category=FactCategory.IP_DHCP,
        description="Hosts must reside on the identical IP subnet as their configured default gateway to exchange frames.",
        diagnostic_relevance="Diagnoses invalid manual static IP configuration."
    ),
    Fact(
        id="F19",
        key="ethernet_wifi_isolation",
        statement="Wired Ethernet connections bypass radio frequency interference and signal attenuation entirely.",
        category=FactCategory.WIFI,
        description="Ethernet utilizes shielded twisted pair cabling with dedicated collision domains (full-duplex CSMA/CD).",
        diagnostic_relevance="If wired Ethernet works while Wi-Fi fails, the issue is exclusively wireless."
    ),
    Fact(
        id="F20",
        key="gateway_reachability_scope",
        statement="Reaching the local default gateway only proves LAN integrity and does not guarantee WAN connectivity.",
        category=FactCategory.GATEWAY,
        description="The gateway may have active LAN interfaces while its WAN interface is down or disconnected from ISP.",
        diagnostic_relevance="Prevents premature conclusion that internet works just because the router pings successfully."
    ),
    Fact(
        id="F21",
        key="wifi_association_vs_internet",
        statement="Successful Wi-Fi association (layer 2) does not guarantee Layer 3 IP assignment or internet access.",
        category=FactCategory.WIFI,
        description="A client can authenticate and associate with an AP (SSID) while having no IP or internet route.",
        diagnostic_relevance="Explains the common user condition 'Connected to Wi-Fi, No Internet Access'."
    ),
    Fact(
        id="F22",
        key="jitter_performance_degradation",
        statement="Variable packet delay (jitter) and packet loss severely degrade streaming and voice calls.",
        category=FactCategory.PERFORMANCE,
        description="RTP and UDP real-time protocols cannot buffer extensive jitter without audible clipping or dropouts.",
        diagnostic_relevance="Guides diagnosis for users reporting video conference stuttering or call drops."
    ),
    Fact(
        id="F23",
        key="dhcp_renewal_clears_lease",
        statement="Releasing and renewing a DHCP lease requests fresh IP parameters and clears stale lease assignments.",
        category=FactCategory.IP_DHCP,
        description="Executing DHCPREQUEST forces the DHCP server to validate or re-issue address allocation parameters.",
        diagnostic_relevance="Primary first-line remediation step for IP assignment anomalies."
    ),
    Fact(
        id="F24",
        key="public_dns_fallback",
        statement="Configuring public recursive resolvers (e.g., 1.1.1.1, 8.8.8.8) bypasses ISP DNS outages.",
        category=FactCategory.DNS,
        description="ISP DNS servers often suffer rate-limiting, slow recursion, or regional outages.",
        diagnostic_relevance="Determines whether DNS issue is local configuration or upstream ISP resolver failure."
    ),
    Fact(
        id="F25",
        key="isp_outage_scope",
        statement="An ISP outage disrupts external IP routing and WAN PPPoE/DHCP links across an entire neighborhood.",
        category=FactCategory.ISP,
        description="Physical optical fiber cuts, DSLAM failure, or upstream BGP routing withdrawal by transit providers.",
        diagnostic_relevance="Diagnoses scenarios where all local network devices fail to reach external IP targets."
    ),
    Fact(
        id="F26",
        key="hardware_power_cycle_flushes_capacitors",
        statement="A 30-second power cycle fully discharges power capacitors and forces complete hardware reboot.",
        category=FactCategory.GENERAL,
        description="Clears corrupt volatile memory registers, frozen network processor cores, and locked MAC tables.",
        diagnostic_relevance="Standard hardware recovery procedure for frozen networking gateways."
    ),
    Fact(
        id="F27",
        key="ip_vs_dns_orthogonality",
        statement="Layer 3 ICMP ping to an external IP operates completely independently of Layer 7 DNS name resolution.",
        category=FactCategory.DNS,
        description="ICMP echo requests use numeric IP headers directly without invoking DNS getaddrinfo().",
        diagnostic_relevance="Provides the definitive diagnostic test separating DNS faults from internet outages."
    ),
    Fact(
        id="F28",
        key="valid_ip_gateway_independence",
        statement="A valid statically configured IP address does not guarantee that the default gateway is functional.",
        category=FactCategory.GATEWAY,
        description="A host can hold a valid RFC 1918 address while the gateway hardware is powered down or disconnected.",
        diagnostic_relevance="Ensures that validating host IP does not bypass checking gateway availability."
    ),
    Fact(
        id="F29",
        key="captive_portal_interception",
        statement="Captive portals intercept HTTP traffic and spoof DNS queries until web-based authorization completes.",
        category=FactCategory.GENERAL,
        description="Common on public/hotel Wi-Fi: redirects all initial unauthenticated TCP port 80/443 traffic.",
        diagnostic_relevance="Explains why device is connected with IP and DNS working, yet ordinary internet access is redirected."
    ),
    Fact(
        id="F30",
        key="mtu_black_hole_loss",
        statement="MTU mismatches drop packets exceeding maximum transmission unit when Path MTU Discovery (PMTUD) fails.",
        category=FactCategory.PERFORMANCE,
        description="Firewalls blocking ICMP Type 3 Code 4 (Fragmentation Needed) cause large packet drops.",
        diagnostic_relevance="Explains why ping works fine (small packets), but opening full web pages or file downloads hangs."
    ),
]


# Map fact ID to Fact object
FACTS_BY_ID: Dict[str, Fact] = {fact.id: fact for fact in DOMAIN_FACTS}
FACTS_BY_KEY: Dict[str, Fact] = {fact.key: fact for fact in DOMAIN_FACTS}


# -------------------------------------------------------------------------
# Dynamic User-Askable Facts (Inputs to Working Memory)
# -------------------------------------------------------------------------

USER_FACT_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "device_connected": {
        "statement": "Device is physically or wirelessly connected to a local network.",
        "category": FactCategory.GENERAL.value,
        "type": "boolean"
    },
    "using_wifi": {
        "statement": "Device is currently using a Wi-Fi wireless network connection.",
        "category": FactCategory.WIFI.value,
        "type": "boolean"
    },
    "valid_ip": {
        "statement": "Device has been assigned a valid, usable local IP address.",
        "category": FactCategory.IP_DHCP.value,
        "type": "boolean"
    },
    "ip_is_apipa": {
        "statement": "Device IP address begins with 169.254 (APIPA autoconfiguration).",
        "category": FactCategory.IP_DHCP.value,
        "type": "boolean"
    },
    "gateway_reachable": {
        "statement": "Device can successfully ping or communicate with its default gateway.",
        "category": FactCategory.GATEWAY.value,
        "type": "boolean"
    },
    "external_ip_reachable": {
        "statement": "Device can reach a known public IP address (e.g., 8.8.8.8) on the internet.",
        "category": FactCategory.DNS.value,
        "type": "boolean"
    },
    "domain_access": {
        "statement": "Device can open websites using domain names (e.g., google.com).",
        "category": FactCategory.DNS.value,
        "type": "boolean"
    },
    "multiple_devices_affected": {
        "statement": "Other devices on the same local network are experiencing the exact same issue.",
        "category": FactCategory.ISP.value,
        "type": "boolean"
    },
    "frequent_disconnections": {
        "statement": "Network connection repeatedly drops and reconnects.",
        "category": FactCategory.WIFI.value,
        "type": "boolean"
    },
    "wifi_signal_weak": {
        "statement": "Wi-Fi signal strength indicator is low (1-2 bars or RSSI below -75 dBm).",
        "category": FactCategory.WIFI.value,
        "type": "boolean"
    },
    "high_latency_observed": {
        "statement": "Consistently high latency or ping response times (above 150ms).",
        "category": FactCategory.PERFORMANCE.value,
        "type": "boolean"
    },
    "packet_loss_observed": {
        "statement": "Measurable packet loss detected during ping or gaming/streaming.",
        "category": FactCategory.PERFORMANCE.value,
        "type": "boolean"
    },
    "heavy_bandwidth_usage": {
        "statement": "Multiple users or devices are concurrently downloading, streaming 4K, or gaming.",
        "category": FactCategory.PERFORMANCE.value,
        "type": "boolean"
    },
    "dns_server_reachable": {
        "statement": "Configured DNS server IP responds to direct ping requests.",
        "category": FactCategory.DNS.value,
        "type": "boolean"
    },
    "problem_on_ethernet_too": {
        "statement": "The problem still persists when connecting via a wired Ethernet cable.",
        "category": FactCategory.WIFI.value,
        "type": "boolean"
    },
    "router_reboot_temporarily_fixed": {
        "statement": "Restarting or power-cycling the router temporarily resolved the problem before it returned.",
        "category": FactCategory.GATEWAY.value,
        "type": "boolean"
    },
}


# -------------------------------------------------------------------------
# Rule-Derived Intermediate Facts (Generated by Production Rules)
# -------------------------------------------------------------------------

DERIVED_FACT_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "dhcp_failure_suspected": {
        "statement": "DHCP IP configuration assignment appears to have failed.",
        "category": FactCategory.IP_DHCP.value
    },
    "ip_config_failure": {
        "statement": "Host network interface lacks a valid operational IP configuration.",
        "category": FactCategory.IP_DHCP.value
    },
    "dhcp_server_unavailable": {
        "statement": "Local DHCP server is offline, exhausted, or unreachable.",
        "category": FactCategory.IP_DHCP.value
    },
    "gateway_failure_suspected": {
        "statement": "Default gateway is unreachable despite valid local IP.",
        "category": FactCategory.GATEWAY.value
    },
    "local_network_problem": {
        "statement": "A fault exists on the local physical link or Layer 2 switch/AP.",
        "category": FactCategory.GATEWAY.value
    },
    "router_hardware_suspected": {
        "statement": "Router hardware crash, lockup, or resource exhaustion is suspected.",
        "category": FactCategory.GATEWAY.value
    },
    "dns_failure_suspected": {
        "statement": "DNS name resolution failure confirmed by external IP reachability.",
        "category": FactCategory.DNS.value
    },
    "dns_server_failure_suspected": {
        "statement": "Assigned DNS server is unresponsive or failing queries.",
        "category": FactCategory.DNS.value
    },
    "dns_config_problem_suspected": {
        "statement": "Local DNS cache or resolver configuration is corrupted.",
        "category": FactCategory.DNS.value
    },
    "weak_wifi_suspected": {
        "statement": "Weak wireless RF signal is degrading connection quality.",
        "category": FactCategory.WIFI.value
    },
    "wireless_instability_suspected": {
        "statement": "Severe wireless RF instability and packet retransmissions.",
        "category": FactCategory.WIFI.value
    },
    "network_performance_degraded": {
        "statement": "Network connection is suffering from latency or packet loss.",
        "category": FactCategory.PERFORMANCE.value
    },
    "network_congestion_suspected": {
        "statement": "Local bandwidth saturation and bufferbloat is causing congestion.",
        "category": FactCategory.PERFORMANCE.value
    },
    "isp_failure_suspected": {
        "statement": "WAN internet connectivity is down while local gateway is reachable.",
        "category": FactCategory.ISP.value
    },
    "isp_outage_suspected": {
        "statement": "External internet service provider outage affecting multiple hosts.",
        "category": FactCategory.ISP.value
    },
}


# -------------------------------------------------------------------------
# Knowledge Base Access API
# -------------------------------------------------------------------------

def get_fact(fact_id_or_key: str) -> Optional[Fact]:
    """Retrieve a domain fact by either its ID (e.g. 'F01') or its key."""
    if fact_id_or_key in FACTS_BY_ID:
        return FACTS_BY_ID[fact_id_or_key]
    return FACTS_BY_KEY.get(fact_id_or_key)


def get_all_facts() -> List[Fact]:
    """Return all 30 static domain facts."""
    return list(DOMAIN_FACTS)


def get_facts_by_category(category: FactCategory) -> List[Fact]:
    """Filter static domain facts by networking category."""
    return [fact for fact in DOMAIN_FACTS if fact.category == category]


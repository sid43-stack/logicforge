"""NetSage Recommendation Engine - Actionable Remediation Plans.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Maps confirmed terminal network diagnoses to structured, prioritized troubleshooting
procedures, expected outcomes, disruption warnings, and escalation advice.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TroubleshootingStep(BaseModel):
    """An individual actionable troubleshooting action."""
    order: int = Field(..., description="1-based execution sequence")
    action: str = Field(..., description="Imperative command (e.g., 'Flush Local DNS Cache')")
    command: Optional[str] = Field(None, description="CLI command if applicable (e.g. 'ipconfig /flushdns')")
    description: str = Field(..., description="Detailed instructions for executing this step")
    expected_outcome: str = Field(..., description="What success looks like after performing this action")
    is_disruptive: bool = Field(default=False, description="Whether this action temporarily drops connection")
    requires_admin: bool = Field(default=False, description="Whether administrative privileges are required")


class RecommendationPlan(BaseModel):
    """Comprehensive troubleshooting remediation plan for a network diagnosis."""
    code: str = Field(..., description="Unique recommendation plan code, e.g., REC_DNS_UPSTREAM")
    diagnosis: str = Field(..., description="Target network fault diagnosis")
    category: str = Field(..., description="Problem category")
    severity: str = Field(..., description="Fault severity (LOW, MEDIUM, HIGH, CRITICAL)")
    summary: str = Field(..., description="Concise diagnostic summary")
    steps: List[TroubleshootingStep] = Field(..., description="Ordered remediation actions")
    warnings: List[str] = Field(default_factory=list, description="Safety precautions or service disruption caveats")
    escalation_advice: str = Field(..., description="Guidance if local troubleshooting does not resolve the fault")


# -------------------------------------------------------------------------
# Recommendation Registry (All 13 Terminal Diagnoses + Inconclusive Plan)
# -------------------------------------------------------------------------

RECOMMENDATIONS_DATA: Dict[str, RecommendationPlan] = {
    # 1. Router DHCP Server Failure (R04)
    "REC_DHCP_ROUTER": RecommendationPlan(
        code="REC_DHCP_ROUTER",
        diagnosis="Router DHCP Server Failure",
        category="IP_DHCP",
        severity="HIGH",
        summary="The local router's DHCP service is unresponsive or has exhausted its available IP address pool.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Restart the Local Gateway / Router",
                command=None,
                description="Power-cycle the router by unplugging the AC power adapter for 30 seconds, then reconnecting it.",
                expected_outcome="Restarts the embedded DHCP daemon and clears stale lease tables.",
                is_disruptive=True,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Verify DHCP Pool Range in Router Admin Console",
                command=None,
                description="Log into the router web interface (e.g. 192.168.1.1) and inspect DHCP server settings. Verify the subnet pool has available unallocated IP addresses.",
                expected_outcome="Confirms the DHCP pool range (e.g., 192.168.1.100 to .254) is enabled and not depleted.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Release and Renew Local IP Address",
                command="ipconfig /release && ipconfig /renew",
                description="Open command prompt and issue lease renewal commands to request a new IP address from the rebooted DHCP server.",
                expected_outcome="The host receives a valid local IP address in place of the 169.254.x.x APIPA address.",
                is_disruptive=True,
                requires_admin=True
            ),
        ],
        warnings=[
            "Power-cycling the router will temporarily disconnect all wired and wireless devices on the network."
        ],
        escalation_advice="If the router repeatedly fails to allocate IP leases after reboots, update the router firmware or replace the router hardware."
    ),

    # 2. Host DHCP Client Lease Failure (R05)
    "REC_DHCP_CLIENT": RecommendationPlan(
        code="REC_DHCP_CLIENT",
        diagnosis="Host DHCP Client Lease Failure",
        category="IP_DHCP",
        severity="MEDIUM",
        summary="DHCP failure is isolated to this specific host, pointing to a local adapter issue or corrupted TCP/IP stack.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Renew Host DHCP Lease",
                command="ipconfig /renew",
                description="Force the operating system to send a DHCPREQUEST packet to the router DHCP server.",
                expected_outcome="A fresh IP lease is granted without restarting other devices.",
                is_disruptive=True,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Disable and Re-enable Network Interface",
                command=None,
                description="In Network Connections, right-click your network adapter, click Disable, wait 10 seconds, then click Enable.",
                expected_outcome="Reinitializes the network adapter hardware and driver stack.",
                is_disruptive=True,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Reset TCP/IP and Winsock Catalog",
                command="netsh int ip reset && netsh winsock reset",
                description="Reset the operating system IP routing and sockets catalog to default factory state, then restart your PC.",
                expected_outcome="Clears corrupt registry keys or third-party filter drivers blocking DHCP packets.",
                is_disruptive=True,
                requires_admin=True
            ),
        ],
        warnings=[
            "Executing TCP/IP reset requires administrative permissions and a system restart."
        ],
        escalation_advice="If the host still receives 169.254.x.x while other devices connect fine, reinstall the network adapter manufacturer drivers."
    ),

    # 3. Router Gateway Crash / Hardware Overload (R09)
    "REC_GATEWAY_REBOOT": RecommendationPlan(
        code="REC_GATEWAY_REBOOT",
        diagnosis="Router Gateway Crash / Hardware Overload",
        category="GATEWAY",
        severity="HIGH",
        summary="The default gateway freezes under load due to NAT connection tracking table exhaustion or firmware deadlock.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Perform a Clean 30-Second Hardware Power Cycle",
                command=None,
                description="Disconnect the DC power plug from the router, wait 30 seconds for all internal capacitors to drain, and plug it back in.",
                expected_outcome="Restores router memory registers, flushes full connection tables, and recovers ping response.",
                is_disruptive=True,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Inspect Router Ventilation and Ambient Temperature",
                command=None,
                description="Ensure the router is placed in an open, well-ventilated area away from direct heat sources or stacked electronics.",
                expected_outcome="Prevents thermal throttling and subsequent processor lockups under heavy routing load.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=3,
                action="Update Router Firmware to Latest Stable Release",
                command=None,
                description="Access router management portal, check firmware version, and apply available vendor bug-fix updates.",
                expected_outcome="Patches known memory leaks and kernel crashes in older router firmware builds.",
                is_disruptive=True,
                requires_admin=True
            ),
        ],
        warnings=[
            "Do not power off the router while a firmware update is being written to flash memory."
        ],
        escalation_advice="If the router continues crashing multiple times per week despite firmware updates, the internal flash/RAM is failing and the device must be replaced."
    ),

    # 4. Local Gateway Connectivity Failure (Host Specific) (R10)
    "REC_GATEWAY_LOCAL": RecommendationPlan(
        code="REC_GATEWAY_LOCAL",
        diagnosis="Local Gateway Connectivity Failure (Host Specific)",
        category="GATEWAY",
        severity="MEDIUM",
        summary="This specific device cannot reach the gateway, indicating an incorrect static IP, invalid subnet mask, or stale ARP entry.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Flush Local ARP Cache",
                command="arp -d *",
                description="Clear stale Layer 2 MAC-to-IP address bindings in the local operating system.",
                expected_outcome="Forces the host to broadcast a fresh ARP request for the gateway MAC address.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Switch from Static IP to Automatic (DHCP)",
                command=None,
                description="Open network adapter IPv4 properties and ensure 'Obtain an IP address automatically' is selected.",
                expected_outcome="Eliminates IP subnet mismatches or duplicate IP address collisions on the local subnet.",
                is_disruptive=True,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Verify Local Subnet and Gateway Consistency",
                command="ipconfig /all",
                description="Verify that your IP address and the Default Gateway share the exact same subnet prefix (e.g. 192.168.1.x with 255.255.255.0).",
                expected_outcome="Confirms Layer 3 routing can reach the default gateway without exiting local segment.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[
            "Switching off a required static IP in corporate environments may require assistance from your network administrator."
        ],
        escalation_advice="If wired, test with a different Ethernet patch cable and switch port to eliminate physical Layer 1 damage."
    ),

    # 5. Upstream DNS Provider Outage (R13)
    "REC_DNS_UPSTREAM": RecommendationPlan(
        code="REC_DNS_UPSTREAM",
        diagnosis="Upstream DNS Provider Outage",
        category="DNS",
        severity="HIGH",
        summary="Your internet connection is active, but your ISP or configured DNS resolvers are unresponsive to domain queries.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Configure Public Recursive DNS Resolvers",
                command=None,
                description="Change IPv4 DNS server addresses in router or adapter settings to Google DNS (8.8.8.8, 8.8.4.4) or Cloudflare DNS (1.1.1.1, 1.0.0.1).",
                expected_outcome="Bypasses the failing upstream ISP resolver and immediately restores domain name browsing.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Flush Host DNS Resolver Cache",
                command="ipconfig /flushdns",
                description="Clear cached negative DNS responses from the local operating system cache.",
                expected_outcome="Ensures subsequent browser requests query the newly configured public DNS resolvers.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Verify DNS Resolution via Command Line",
                command="nslookup google.com 1.1.1.1",
                description="Perform a direct DNS lookup query against Cloudflare DNS to verify resolution works.",
                expected_outcome="Returns valid IP addresses for the target domain.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[
            "If your network uses a corporate intranet with internal domain names (.corp, .local), public DNS will not resolve internal enterprise resources."
        ],
        escalation_advice="If changing DNS servers on your router does not restore domain lookup, check with your ISP for upstream fiber cuts or regional transit issues."
    ),

    # 6. Invalid Local DNS Server Configuration (R14)
    "REC_DNS_LOCAL": RecommendationPlan(
        code="REC_DNS_LOCAL",
        diagnosis="Invalid Local DNS Server Configuration",
        category="DNS",
        severity="MEDIUM",
        summary="A non-existent or unreachable DNS server IP has been manually configured on this computer.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Set DNS Server Assignment to Automatic (DHCP)",
                command=None,
                description="Open network adapter IPv4 properties and select 'Obtain DNS server address automatically'.",
                expected_outcome="The host adopts the functioning DNS resolver addresses assigned by your local router.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Flush DNS Cache",
                command="ipconfig /flushdns",
                description="Purge the DNS resolver cache to delete stale negative cache entries.",
                expected_outcome="Empties stale cache so fresh DNS queries can succeed.",
                is_disruptive=False,
                requires_admin=True
            ),
        ],
        warnings=[
            "Administrator credentials are required to modify network adapter DNS settings."
        ],
        escalation_advice="Check for third-party VPN software or anti-virus firewalls that might be redirecting port 53 UDP traffic."
    ),

    # 7. DNS Cache Corruption / Local Resolver Failure (R16)
    "REC_DNS_FLUSH": RecommendationPlan(
        code="REC_DNS_FLUSH",
        diagnosis="DNS Cache Corruption / Local Resolver Failure",
        category="DNS",
        severity="LOW",
        summary="The DNS server responds to ping, but local resolution fails due to corrupted cached records or hosts file entries.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Flush Local DNS Resolver Cache",
                command="ipconfig /flushdns",
                description="Execute flushdns in terminal to discard all cached hostname records.",
                expected_outcome="Returns 'Successfully flushed the DNS Resolver Cache'.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Inspect and Clean the System Hosts File",
                command="notepad C:\\Windows\\System32\\drivers\\etc\\hosts",
                description="Check for malicious or outdated manual hostname-to-IP overrides in the hosts file.",
                expected_outcome="Removes erroneous IP mappings that override real DNS queries.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Restart the OS DNS Client Service",
                command="net stop dnscache && net start dnscache",
                description="Restart the local DNS caching daemon in services.msc.",
                expected_outcome="Restores clean operating system resolver state.",
                is_disruptive=False,
                requires_admin=True
            ),
        ],
        warnings=[
            "Modifying the hosts file requires running your text editor as Administrator."
        ],
        escalation_advice="Run a security scan if unknown IP addresses were discovered mapped to common websites inside your hosts file."
    ),

    # 8. Wi-Fi Signal Attenuation and Range Limitation (R19)
    "REC_WIFI_RANGE": RecommendationPlan(
        code="REC_WIFI_RANGE",
        diagnosis="Wi-Fi Signal Attenuation and Range Limitation",
        category="WIFI",
        severity="MEDIUM",
        summary="Excessive physical distance or dense physical obstacles (walls, metal) severely degrade wireless signal strength.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Move Closer to the Wireless Router / Access Point",
                command=None,
                description="Test connectivity within line-of-sight of the router (5–10 feet) to confirm if signal strength and stability improve.",
                expected_outcome="Wi-Fi signal jumps to 4–5 bars and frequent disconnections cease.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Switch to the 2.4 GHz Wireless Frequency Band",
                command=None,
                description="If connected to a 5 GHz SSID, switch to the 2.4 GHz SSID. 2.4 GHz has longer radio waves that penetrate walls much more effectively.",
                expected_outcome="Improved range and link resilience through interior walls and furniture.",
                is_disruptive=True,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=3,
                action="Elevate and Reposition Router Antennas",
                command=None,
                description="Place the router on an elevated table or shelf away from metal cabinets, appliances, or reflective mirrors.",
                expected_outcome="Expands effective RF toroidal radiation pattern across your home or office.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[
            "2.4 GHz provides superior wall penetration but lower maximum peak throughput compared to 5 GHz."
        ],
        escalation_advice="Consider installing a dedicated Wi-Fi mesh node or a hardwired Ethernet wireless access point for large properties."
    ),

    # 9. Wireless Radio Interference / Channel Congestion (R20)
    "REC_WIFI_INTERFERENCE": RecommendationPlan(
        code="REC_WIFI_INTERFERENCE",
        diagnosis="Wireless Radio Interference / Channel Congestion",
        category="WIFI",
        severity="MEDIUM",
        summary="Wi-Fi signal is strong but unstable due to co-channel radio interference from neighboring networks, Bluetooth, or microwave ovens.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Switch Wi-Fi Channel in Router Settings",
                command=None,
                description="Log into router console and change the Wi-Fi channel from 'Auto' to a clean non-overlapping channel (1, 6, or 11 for 2.4 GHz, or an uncrowded 5 GHz channel).",
                expected_outcome="Avoids co-channel collisions and drastically reduces wireless frame retry rates.",
                is_disruptive=True,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Connect to the 5 GHz Wi-Fi Frequency Band",
                command=None,
                description="Switch to your router's 5 GHz band, which has significantly more non-overlapping channels and zero microwave interference.",
                expected_outcome="Eliminates 2.4 GHz RF congestion and delivers stable low-latency transmission.",
                is_disruptive=True,
                requires_admin=False
            ),
        ],
        warnings=[
            "Changing wireless channels will momentarily disconnect all active wireless clients."
        ],
        escalation_advice="Use a free Wi-Fi analyzer mobile app to inspect which channels neighboring access points are occupying."
    ),

    # 10. Local Network Bufferbloat & Bandwidth Saturation (R23)
    "REC_PERF_CONGESTION": RecommendationPlan(
        code="REC_PERF_CONGESTION",
        diagnosis="Local Network Bufferbloat & Bandwidth Saturation",
        category="PERFORMANCE",
        severity="MEDIUM",
        summary="Heavy concurrent bandwidth consumption has saturated router queues, causing packet delays and high ping latency.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Pause Unnecessary Bandwidth-Intensive Downloads",
                command=None,
                description="Pause large cloud backups, Steam/Xbox game updates, and peer-to-peer torrent clients running on local network devices.",
                expected_outcome="Router egress buffer clears, immediately dropping ping latency back to normal levels.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Enable Quality of Service (QoS) in Router Settings",
                command=None,
                description="Log into the router web portal and enable Smart Queue Management (SQM) or QoS to prioritize interactive latency-sensitive traffic.",
                expected_outcome="Prevents file downloads from choking gaming, VoIP, and video conference packets.",
                is_disruptive=False,
                requires_admin=True
            ),
        ],
        warnings=[
            "Enabling QoS on budget routers with weak processors may reduce maximum WAN download speeds."
        ],
        escalation_advice="If bandwidth saturation occurs during regular daily activities, consider upgrading your ISP subscription speed tier."
    ),

    # 11. Physical Line Degradation or ISP Packet Loss (R24)
    "REC_PERF_PACKETLOSS": RecommendationPlan(
        code="REC_PERF_PACKETLOSS",
        diagnosis="Physical Line Degradation or ISP Packet Loss",
        category="PERFORMANCE",
        severity="HIGH",
        summary="Packet loss is occurring without local network saturation, pointing to damaged physical cabling, line noise, or upstream ISP router drops.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Replace Local Ethernet Patch Cables",
                command=None,
                description="Inspect the Ethernet cable connecting your PC or router. Replace any kinked, damaged, or unshielded Cat5 cables with Cat6.",
                expected_outcome="Eliminates local CRC frame errors caused by broken internal copper pairs.",
                is_disruptive=True,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Run Continuous MTR / PathPing Test",
                command="pathping 8.8.8.8",
                description="Execute pathping to isolate exactly which intermediate network hop is dropping packets.",
                expected_outcome="Identifies whether packet loss begins at the local gateway or upstream at an ISP routing node.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[
            "PathPing takes approximately 3 to 5 minutes to complete comprehensive statistical sampling."
        ],
        escalation_advice="Provide the PathPing / MTR results showing upstream packet loss to your ISP customer support for line technician dispatch."
    ),

    # 12. Wide-Area ISP Service Outage (R27)
    "REC_ISP_OUTAGE": RecommendationPlan(
        code="REC_ISP_OUTAGE",
        diagnosis="Wide-Area ISP Service Outage",
        category="ISP",
        severity="CRITICAL",
        summary="Local network and router are functional, but all external internet connectivity is severed across your provider's network.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Inspect Optical Terminal (ONT) or Modem Status LEDs",
                command=None,
                description="Check the 'PON', 'WAN', 'Internet', or 'LOS' (Loss of Signal) light on your modem/ONT. A red or blinking light indicates lost physical carrier signal.",
                expected_outcome="Confirms whether the fiber/coaxial signal from the street has been severed.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Check ISP Service Status Page on Cellular Data",
                command=None,
                description="Use your smartphone cellular mobile data to check your ISP's mobile app or status website for reported regional outages.",
                expected_outcome="Provides estimated time of repair for neighborhood infrastructure faults.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=3,
                action="Report Outage to Internet Service Provider",
                command=None,
                description="Contact ISP support helpline and log a fault ticket with your customer account identifier.",
                expected_outcome="Prompts network operations center to investigate line cuts or transit node failure.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[
            "Do not factory-reset your router during an external ISP outage; doing so erases your PPPoE/VLAN credentials."
        ],
        escalation_advice="ISP-level outages cannot be repaired locally. Switch to mobile hotspot tethering as a temporary fallback."
    ),

    # 13. Host-Specific Gateway Routing or Firewall Block (R28)
    "REC_HOST_FIREWALL": RecommendationPlan(
        code="REC_HOST_FIREWALL",
        diagnosis="Host-Specific Gateway Routing or Firewall Block",
        category="ISP",
        severity="MEDIUM",
        summary="Other devices on your network access the internet normally, but this computer is blocked from reaching external IPs.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Temporarily Disable Host Firewall for Testing",
                command=None,
                description="Temporarily turn off local firewall (e.g. Windows Defender Firewall) and test pinging 8.8.8.8.",
                expected_outcome="Identifies if an outbound firewall rule or security suite is blocking internet traffic.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=2,
                action="Check Router Parental Controls and MAC Filtering",
                command=None,
                description="Log into the router web portal and ensure this device's MAC address has not been restricted by access schedules or parental controls.",
                expected_outcome="Restores WAN access permissions for the host on the router firewall.",
                is_disruptive=False,
                requires_admin=True
            ),
            TroubleshootingStep(
                order=3,
                action="Reset Windows Firewall Rules to Default",
                command="netsh advfirewall reset",
                description="Reset all firewall policies to clean system defaults.",
                expected_outcome="Deletes corrupted third-party security suite block rules.",
                is_disruptive=False,
                requires_admin=True
            ),
        ],
        warnings=[
            "Remember to re-enable your firewall immediately after diagnostic testing."
        ],
        escalation_advice="Check for active VPN adapters (e.g. OpenVPN, WireGuard, corporate VPN) with broken kill-switch configurations."
    ),

    # Fallback / Inconclusive Plan
    "REC_INCONCLUSIVE": RecommendationPlan(
        code="REC_INCONCLUSIVE",
        diagnosis="Inconclusive / No Fault Detected",
        category="GENERAL",
        severity="LOW",
        summary="All tested network parameters appear normal. No specific network failure condition could be established.",
        steps=[
            TroubleshootingStep(
                order=1,
                action="Verify Target Website or Application Server Status",
                command=None,
                description="If you are experiencing issues with a single specific website, check downdetector.com to see if the remote web service is down.",
                expected_outcome="Confirms whether the problem is on the remote server side rather than your local network.",
                is_disruptive=False,
                requires_admin=False
            ),
            TroubleshootingStep(
                order=2,
                action="Clear Web Browser Cache and Cookies",
                command=None,
                description="Clear browsing data in your web browser settings and test opening the page in an Incognito / Private window.",
                expected_outcome="Clears corrupt session cookies or cached scripts.",
                is_disruptive=False,
                requires_admin=False
            ),
        ],
        warnings=[],
        escalation_advice="If you continue having connectivity problems, restart both your computer and router and re-run this diagnostic expert system."
    ),
}


class RecommendationEngine:
    """Provides structured troubleshooting plans mapped to terminal diagnoses."""

    def __init__(self, data: Optional[Dict[str, RecommendationPlan]] = None):
        self._registry = data if data is not None else dict(RECOMMENDATIONS_DATA)

    def get_recommendation_by_code(self, code: str) -> Optional[RecommendationPlan]:
        """Look up recommendation plan by recommendation code (e.g. 'REC_DHCP_ROUTER')."""
        return self._registry.get(code)

    def get_recommendation_for_diagnosis(
        self,
        diagnosis_name: Optional[str] = None,
        code: Optional[str] = None,
    ) -> RecommendationPlan:
        """Retrieves the troubleshooting plan for a given diagnosis or recommendation code.
        
        Falls back gracefully to REC_INCONCLUSIVE if unmapped.
        """
        if code and code in self._registry:
            return self._registry[code]

        if diagnosis_name:
            for plan in self._registry.values():
                if plan.diagnosis.lower() == diagnosis_name.lower():
                    return plan

        return self._registry["REC_INCONCLUSIVE"]

    def get_recommendation_by_diagnosis(self, diagnosis_name: str) -> Optional[RecommendationPlan]:
        """Look up recommendation plan by diagnosis name."""
        return self.get_recommendation_for_diagnosis(diagnosis_name=diagnosis_name)

    def get_inconclusive_plan(self) -> RecommendationPlan:
        """Returns the fallback troubleshooting plan for inconclusive diagnostic sessions."""
        return self._registry["REC_INCONCLUSIVE"]


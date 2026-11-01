# NetSage Recommendation Engine Documentation

The NetSage Recommendation Engine maps confirmed network diagnoses to prioritized, structured troubleshooting plans.

---

## 1. Remediation Plan Architecture

Every confirmed terminal diagnosis yields a `RecommendationPlan` composed of:
1. `code`: Unique remediation code matching the rule conclusion (e.g. `REC_DHCP_ROUTER`).
2. `diagnosis`: Verified fault name.
3. `summary`: Concise technical overview of the problem.
4. `steps`: Ordered, numbered actions (`TroubleshootingStep`).
   - `order`: Execution sequence ($1, 2, 3$).
   - `action`: Clear imperative action header.
   - `command`: CLI command if applicable (e.g. `ipconfig /flushdns`, `arp -d *`).
   - `description`: Detailed step-by-step instructions.
   - `expected_outcome`: What normal operation looks like after completion.
   - `is_disruptive`: Flag indicating if executing this step drops the connection.
   - `requires_admin`: Flag indicating if elevation / root privileges are required.
5. `warnings`: Precautions (e.g. disrupting active calls, erasing router credentials).
6. `escalation_advice`: Professional escalation guidance when local remediation fails (e.g. ISP technician dispatch).

---

## 2. Recommendation Registry Index

| Plan Code | Diagnosis Name | Category | Severity | Primary Step 1 Action | Disruptive? |
|:---|:---|:---|:---:|:---|:---:|
| `REC_DHCP_ROUTER` | Router DHCP Server Failure | `IP_DHCP` | `HIGH` | Power-cycle local router / gateway | YES |
| `REC_DHCP_CLIENT` | Host DHCP Client Lease Failure | `IP_DHCP` | `MEDIUM` | Renew host DHCP lease (`ipconfig /renew`) | YES |
| `REC_GATEWAY_REBOOT` | Router Gateway Crash / Hardware Overload | `GATEWAY` | `HIGH` | 30-second hardware power cycle | YES |
| `REC_GATEWAY_LOCAL` | Local Gateway Connectivity Failure | `GATEWAY` | `MEDIUM` | Flush local ARP cache (`arp -d *`) | NO |
| `REC_DNS_UPSTREAM` | Upstream DNS Provider Outage | `DNS` | `HIGH` | Configure Public DNS (1.1.1.1, 8.8.8.8) | NO |
| `REC_DNS_LOCAL` | Invalid Local DNS Server Configuration | `DNS` | `MEDIUM` | Set DNS assignment to Automatic (DHCP) | NO |
| `REC_DNS_FLUSH` | DNS Cache Corruption / Local Resolver Failure | `DNS` | `LOW` | Flush local DNS cache (`ipconfig /flushdns`) | NO |
| `REC_WIFI_RANGE` | Wi-Fi Signal Attenuation & Range Limitation | `WIFI` | `MEDIUM` | Move closer to wireless access point | NO |
| `REC_WIFI_INTERFERENCE`| Wireless Radio Interference / Channel Congestion | `WIFI` | `MEDIUM` | Switch Wi-Fi channel in router console | YES |
| `REC_PERF_CONGESTION` | Local Bufferbloat & Bandwidth Saturation | `PERFORMANCE` | `MEDIUM` | Pause bandwidth-intensive background downloads | NO |
| `REC_PERF_PACKETLOSS` | Physical Line Degradation / Upstream Loss | `PERFORMANCE` | `HIGH` | Inspect and replace damaged Ethernet patch cables | YES |
| `REC_ISP_OUTAGE` | Wide-Area ISP Service Outage | `ISP` | `CRITICAL` | Inspect modem/ONT optical LOS LED indicator | NO |
| `REC_HOST_FIREWALL` | Host Gateway Routing or Firewall Block | `ISP` | `MEDIUM` | Temporarily test with local firewall disabled | NO |
| `REC_INCONCLUSIVE` | Inconclusive / No Fault Detected | `GENERAL` | `LOW` | Check remote server status on downdetector.com | NO |

---

## 3. Transparency & Technical Disclaimers

NetSage adheres strictly to expert system ethics:
- It **never** claims to have automatically repaired or reconfigured the user's operating system or router.
- It **never** fabricates fake ping latency or traceroute numbers.
- It provides structured guidance empowering the user or technician to resolve network issues systematically.


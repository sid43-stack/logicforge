# NetSage Question Engine Documentation

The NetSage Question Engine manages the interactive inquiry lifecycle. It replaces static rigid questionnaires with an intelligent, dynamic inquiry system driven by backward-chaining goal resolution.

---

## 1. Architecture & Design Principles

```text
       +------------------------------------+
       |       BackwardChainingEngine       |
       |  (Evaluates Unresolved Premises)   |
       +-----------------+------------------+
                         |
                 next_fact_key
                         v
       +------------------------------------+
       |          QuestionEngine            |
       |  (Registry Lookup & Input Parsing) |
       +-----------------+------------------+
                         |
                  Question Object
                         v
           Diagnostic Wizard Presentation
```

### Core Principles
1. **Fact-to-Question 1:1 Mapping**: Every diagnostic question directly binds to an unambiguous, user-answerable fact key in `USER_FACT_DEFINITIONS`.
2. **Dynamic Non-Linear Sequencing**: Questions are selected exclusively based on active, unproven backward-chaining hypotheses.
3. **No Repeated Questioning**: Once a question is answered (whether `True`, `False`, or explicitly `UNKNOWN`), it is tracked in Working Memory (`is_known(key) == True`) and is **never** asked again.
4. **Answer Normalization**: Translates raw text inputs (`"yes"`, `"no"`, `"unknown"`, `"y"`, `"n"`) into formal `True`, `False`, or `TriState.UNKNOWN` types.
5. **Guidance Metadata**: Each question includes diagnostic guidance instructing non-technical users on how to check symptoms (e.g. running `ping 8.8.8.8` or checking `ipconfig`).

---

## 2. Question Registry Inventory (Q01 – Q16)

| ID | Fact Key | Question Text | Category | Priority | Guidance Instructions |
|:---|:---|:---|:---|:---:|:---|
| **Q01** | `device_connected` | Is your device connected to the network via Wi-Fi or an Ethernet cable? | `GENERAL` | 100 | Check system tray network icon or Ethernet cable seating. |
| **Q02** | `using_wifi` | Are you currently using a Wi-Fi wireless connection? | `WIFI` | 95 | Verify whether the active interface is Wi-Fi or wired cable. |
| **Q03** | `valid_ip` | Does your device have a valid local IP address assigned? | `IP_DHCP` | 90 | Run `ipconfig` and verify IPv4 address is not blank or 0.0.0.0. |
| **Q04** | `gateway_reachable` | Can your device reach or ping its default gateway IP address? | `GATEWAY` | 88 | Ping your default gateway IP (e.g. `ping 192.168.1.1`). |
| **Q05** | `external_ip_reachable` | Can you ping a known external IP address on the internet (e.g., 8.8.8.8)? | `DNS` | 86 | Run `ping 8.8.8.8` in terminal to test raw WAN routing. |
| **Q06** | `domain_access` | Can you open websites in your browser using their domain names? | `DNS` | 85 | Open `https://www.google.com` in web browser. |
| **Q07** | `multiple_devices_affected` | Are other devices on the same network experiencing the exact same problem? | `ISP` | 84 | Check if phones or other laptops on the same Wi-Fi are down. |
| **Q08** | `frequent_disconnections` | Are you experiencing frequent intermittent disconnections and reconnects? | `WIFI` | 80 | Observe if the connection drops repeatedly every few minutes. |
| **Q09** | `wifi_signal_weak` | Is your Wi-Fi signal strength indicator weak (1 to 2 bars or low signal)? | `WIFI` | 78 | Check signal bars on taskbar or phone status bar. |
| **Q10** | `high_latency_observed` | Are you experiencing unusually high ping times, severe lag, or sluggish page loads? | `PERFORMANCE` | 75 | Check if ping response times exceed 150ms. |
| **Q11** | `packet_loss_observed` | Are you experiencing measurable packet loss during online activities? | `PERFORMANCE` | 74 | Run `ping -n 20 8.8.8.8` and verify if packet loss > 0%. |
| **Q12** | `ip_is_apipa` | Does your device's IP address begin with 169.254 (APIPA autoconfiguration)? | `IP_DHCP` | 92 | Check `ipconfig` to see if IPv4 starts with 169.254.x.x. |
| **Q13** | `dns_server_reachable` | Can your device reach or ping its configured DNS server IP address? | `DNS` | 82 | Find DNS server IP in `ipconfig /all` and run `ping <dns_ip>`. |
| **Q14** | `problem_on_ethernet_too` | Does the connectivity problem persist when you connect via an Ethernet cable? | `WIFI` | 76 | Connect Ethernet cable to router and test if problem vanishes. |
| **Q15** | `router_reboot_temporarily_fixed`| Does restarting or power-cycling your router temporarily restore the connection? | `GATEWAY` | 72 | Recall if a 30-second power cycle temporarily restored access. |
| **Q16** | `heavy_bandwidth_usage` | Are other devices on the network actively downloading, streaming 4K, or gaming? | `PERFORMANCE` | 70 | Check if concurrent household users are streaming or downloading. |


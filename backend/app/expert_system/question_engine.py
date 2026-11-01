"""NetSage Question Engine - Dynamic Diagnostic Inquiry System.

Strictly independent of FastAPI, SQLAlchemy, and frontend frameworks.
Manages the structured question registry, maps user-answerable fact keys to rich questions,
parses user inputs (YES/NO/UNKNOWN), and dynamically selects the next question
driven by backward chaining.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from app.expert_system.types import TriState, FactCategory
from app.expert_system.knowledge_base import USER_FACT_DEFINITIONS
from app.expert_system.inference_engine import InferenceEngine


class Question(BaseModel):
    """Structured diagnostic question presented to the user."""
    id: str = Field(..., description="Unique question identifier, e.g., Q01")
    fact_key: str = Field(..., description="Fact key in working memory this question establishes")
    text: str = Field(..., description="User-facing diagnostic question text")
    answer_type: str = Field(default="boolean", description="Expected answer format ('boolean')")
    priority: int = Field(default=80, description="Base display priority")
    category: FactCategory = Field(..., description="Problem domain category")
    guidance: str = Field(..., description="Practical instructions on how a user can test or verify this")
    default_why: str = Field(..., description="Baseline explanation of why this question matters")


# -------------------------------------------------------------------------
# Question Registry (16 Questions mapped 1:1 to User Fact Keys)
# -------------------------------------------------------------------------

QUESTIONS_DATA: List[Question] = [
    Question(
        id="Q01",
        fact_key="device_connected",
        text="Is your device connected to the network via Wi-Fi or an Ethernet cable?",
        category=FactCategory.GENERAL,
        priority=100,
        guidance="Check your network icon in the system tray or verify the network cable is securely plugged in.",
        default_why="Verifies that the physical or link-layer connection exists before analyzing higher layer protocols."
    ),
    Question(
        id="Q02",
        fact_key="using_wifi",
        text="Are you currently using a Wi-Fi wireless connection?",
        category=FactCategory.WIFI,
        priority=95,
        guidance="Check whether your active network connection is wireless Wi-Fi or a wired Ethernet cable.",
        default_why="Determines whether wireless radio frequency issues (attenuation, interference) should be evaluated."
    ),
    Question(
        id="Q03",
        fact_key="valid_ip",
        text="Does your device have a valid local IP address assigned (e.g. 192.168.x.x or 10.x.x.x)?",
        category=FactCategory.IP_DHCP,
        priority=90,
        guidance="Run 'ipconfig' (Windows) or 'ifconfig/ip addr' (Mac/Linux) and inspect IPv4 Address.",
        default_why="Establishes whether the local host has received an operational Layer 3 IP configuration."
    ),
    Question(
        id="Q04",
        fact_key="gateway_reachable",
        text="Can your device reach or ping its default gateway IP address?",
        category=FactCategory.GATEWAY,
        priority=88,
        guidance="Find your default gateway IP in 'ipconfig' (e.g., 192.168.1.1) and run 'ping <gateway_ip>'.",
        default_why="Tests if the device can communicate across the local segment to its router exit point."
    ),
    Question(
        id="Q05",
        fact_key="external_ip_reachable",
        text="Can you ping a known external IP address on the internet (e.g., 8.8.8.8 or 1.1.1.1)?",
        category=FactCategory.DNS,
        priority=86,
        guidance="Open a command prompt and run 'ping 8.8.8.8' to test external IP layer 3 routing.",
        default_why="Crucial test separating DNS name-resolution faults from general internet connectivity outages."
    ),
    Question(
        id="Q06",
        fact_key="domain_access",
        text="Can you open websites in your browser using their domain names (e.g., google.com)?",
        category=FactCategory.DNS,
        priority=85,
        guidance="Try opening 'https://www.google.com' or 'https://www.wikipedia.org' in your web browser.",
        default_why="Checks if Layer 7 Domain Name System (DNS) translation is converting hostnames into IP addresses."
    ),
    Question(
        id="Q07",
        fact_key="multiple_devices_affected",
        text="Are other phones, computers, or devices on the same network experiencing the exact same problem?",
        category=FactCategory.ISP,
        priority=84,
        guidance="Check if your smartphone, smart TV, or another computer on the same Wi-Fi also lacks connection.",
        default_why="Distinguishes between a host-specific driver/OS misconfiguration and a shared router/ISP outage."
    ),
    Question(
        id="Q08",
        fact_key="frequent_disconnections",
        text="Are you experiencing frequent intermittent disconnections and reconnects?",
        category=FactCategory.WIFI,
        priority=80,
        guidance="Observe whether your network connection randomly drops and reconnects every few minutes.",
        default_why="Points to wireless radio signal attenuation, channel interference, or router memory crashes."
    ),
    Question(
        id="Q09",
        fact_key="wifi_signal_weak",
        text="Is your Wi-Fi signal strength indicator weak (1 to 2 bars or low signal)?",
        category=FactCategory.WIFI,
        priority=78,
        guidance="Check the Wi-Fi icon on your taskbar or status bar for the number of active signal bars.",
        default_why="Identifies physical distance or wall attenuation as the cause of wireless link degradation."
    ),
    Question(
        id="Q10",
        fact_key="high_latency_observed",
        text="Are you experiencing unusually high ping times, severe lag, or sluggish page loads?",
        category=FactCategory.PERFORMANCE,
        priority=75,
        guidance="Run 'ping 8.8.8.8' or a speed test and note if average response times exceed 150ms.",
        default_why="Evaluates whether the network connection suffers from bufferbloat, congestion, or long transit delays."
    ),
    Question(
        id="Q11",
        fact_key="packet_loss_observed",
        text="Are you experiencing measurable packet loss during ping tests, voice calls, or online gaming?",
        category=FactCategory.PERFORMANCE,
        priority=74,
        guidance="Run 'ping -n 20 8.8.8.8' (Windows) and check if the packet loss percentage is greater than 0%.",
        default_why="Distinguishes high-latency but intact links from noisy physical media, line damage, or dropping queues."
    ),
    Question(
        id="Q12",
        fact_key="ip_is_apipa",
        text="Does your device's IP address begin with 169.254 (an APIPA autoconfigured address)?",
        category=FactCategory.IP_DHCP,
        priority=92,
        guidance="Look at 'IPv4 Address' in 'ipconfig'; check if it starts with 169.254.x.x.",
        default_why="Direct hallmark of DHCP discovery failure: the OS failed to obtain an IP lease from any DHCP server."
    ),
    Question(
        id="Q13",
        fact_key="dns_server_reachable",
        text="Can your device reach or ping its configured DNS server IP address?",
        category=FactCategory.DNS,
        priority=82,
        guidance="Find your DNS server IP under 'ipconfig /all' and run 'ping <dns_server_ip>'.",
        default_why="Separates local DNS cache/configuration errors from dead or unresponsive upstream DNS servers."
    ),
    Question(
        id="Q14",
        fact_key="problem_on_ethernet_too",
        text="Does the connectivity problem persist when you connect your device via an Ethernet cable?",
        category=FactCategory.WIFI,
        priority=76,
        guidance="Plug an Ethernet cable from your router into your laptop/PC and test if the issue disappears.",
        default_why="Definitively isolates RF wireless problems from general router or ISP connectivity faults."
    ),
    Question(
        id="Q15",
        fact_key="router_reboot_temporarily_fixed",
        text="Does restarting or power-cycling your router temporarily restore the connection?",
        category=FactCategory.GATEWAY,
        priority=72,
        guidance="Think back to the last time you restarted the router by unplugging its power cord for 30 seconds.",
        default_why="Differentiates hardware/firmware exhaustion (buffer overflow, NAT exhaustion) from persistent line cuts."
    ),
    Question(
        id="Q16",
        fact_key="heavy_bandwidth_usage",
        text="Are other devices on the network actively downloading, streaming 4K video, or gaming?",
        category=FactCategory.PERFORMANCE,
        priority=70,
        guidance="Check if family members or room-mates are streaming video, torrenting, or downloading game updates.",
        default_why="Determines whether latency spikes and packet drops are caused by bandwidth saturation (bufferbloat)."
    ),
]


class QuestionRegistry:
    """Manages diagnostic questions and mappings to fact keys."""

    def __init__(self, questions: Optional[List[Question]] = None):
        self._questions = questions if questions is not None else list(QUESTIONS_DATA)
        self._by_id: Dict[str, Question] = {q.id: q for q in self._questions}
        self._by_fact_key: Dict[str, Question] = {q.fact_key: q for q in self._questions}

    def get_by_id(self, question_id: str) -> Optional[Question]:
        """Look up a question by ID (e.g. 'Q05')."""
        return self._by_id.get(question_id)

    def get_by_fact_key(self, fact_key: str) -> Optional[Question]:
        """Look up a question by the fact key it determines."""
        return self._by_fact_key.get(fact_key)

    def get_all(self) -> List[Question]:
        """Return all registered questions."""
        return list(self._questions)

    def count(self) -> int:
        return len(self._questions)


class QuestionEngine:
    """Coordinates dynamic question selection using backward chaining and inference state."""

    def __init__(self, registry: Optional[QuestionRegistry] = None):
        self.registry = registry if registry is not None else QuestionRegistry()

    @staticmethod
    def parse_user_answer(raw_answer: Union[str, bool, TriState]) -> Union[bool, TriState]:
        """Parses user answer ('yes', 'no', 'unknown', True, False) to standard boolean or TriState."""
        if isinstance(raw_answer, bool):
            return raw_answer
        if isinstance(raw_answer, TriState):
            return raw_answer

        normalized = str(raw_answer).strip().upper()
        if normalized in ("YES", "Y", "TRUE", "1"):
            return True
        elif normalized in ("NO", "N", "FALSE", "0"):
            return False
        elif normalized in ("UNKNOWN", "U", "DONT_KNOW", "UNSURE", "NONE"):
            return TriState.UNKNOWN
        else:
            raise ValueError(f"Unrecognized answer format: '{raw_answer}'. Expected YES, NO, or UNKNOWN.")

    def select_next_question(self, engine: InferenceEngine) -> Optional[Question]:
        """Dynamically selects the next question relevant to the active backward-chaining goal.
        
        Returns None if diagnosis is completed, conflicting, or all questions are exhausted.
        """
        # 1. If session is already completed or in conflict, no further question is asked
        if engine.has_terminal_diagnosis() or engine.has_conflict():
            return None

        # 2. Get the next askable premise deemed most informative by backward chaining
        next_fact_key = engine.get_next_question_premise()
        if not next_fact_key:
            return None

        # 3. Retrieve question mapped to this fact key
        question = self.registry.get_by_fact_key(next_fact_key)
        if question is None:
            # Fallback question generation if key is unmapped
            question = Question(
                id=f"Q_{next_fact_key}",
                fact_key=next_fact_key,
                text=f"Is the following network condition present: {next_fact_key.replace('_', ' ')}?",
                category=FactCategory.GENERAL,
                priority=50,
                guidance="Verify whether this network symptom is currently occurring.",
                default_why=f"Required by inference engine to evaluate active diagnostic hypotheses."
            )

        return question


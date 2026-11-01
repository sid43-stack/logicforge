import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Cpu,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Wifi,
  Server,
  Globe,
  Radio,
  Gauge,
  Network,
  Terminal,
  Layers,
  Sparkles,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';

export const LandingPage: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<{
    connected: boolean;
    project?: string;
    version?: string;
    error?: string;
  }>({ connected: false });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get('/health')
      .then((res) => {
        setBackendStatus({
          connected: true,
          project: res.data.project,
          version: res.data.version,
        });
        setLoading(false);
      })
      .catch((err) => {
        setBackendStatus({
          connected: false,
          error: err.message || 'Cannot connect to NetSage backend service on port 8000',
        });
        setLoading(false);
      });
  }, []);

  const categories = [
    {
      id: 'IP_DHCP',
      name: 'IP & DHCP Configuration',
      desc: 'APIPA assignment, DHCP pool exhaustion, gateway lease rejection, and client IP conflicts.',
      icon: <Server className="w-5 h-5 text-gold-700" />,
      tag: 'OSI Layer 3',
    },
    {
      id: 'GATEWAY',
      name: 'Gateway & Local Segment',
      desc: 'Default gateway unreachability, ARP failures, router crash/overload, and physical segment breaks.',
      icon: <Network className="w-5 h-5 text-gold-700" />,
      tag: 'OSI Layer 2/3',
    },
    {
      id: 'DNS',
      name: 'DNS Name Resolution',
      desc: 'Upstream recursive resolver outages, local DNS cache poisoning, and NXDOMAIN failures.',
      icon: <Globe className="w-5 h-5 text-gold-700" />,
      tag: 'OSI Layer 7',
    },
    {
      id: 'WIFI',
      name: 'Wi-Fi & Wireless RF',
      desc: 'Signal attenuation, interference, excessive distance from AP, and wireless beacon instability.',
      icon: <Wifi className="w-5 h-5 text-emerald-700" />,
      tag: 'OSI Layer 1/2',
    },
    {
      id: 'PERFORMANCE',
      name: 'Latency & Bufferbloat',
      desc: 'Excessive queue bufferbloat, local bandwidth saturation, packet retransmission, and jitter.',
      icon: <Gauge className="w-5 h-5 text-amber-700" />,
      tag: 'OSI Layer 4',
    },
    {
      id: 'ISP',
      name: 'WAN & ISP Infrastructure',
      desc: 'Wide-area ISP fiber cuts, uplink authentication failures, and carrier maintenance downtime.',
      icon: <Radio className="w-5 h-5 text-gold-700" />,
      tag: 'WAN Infrastructure',
    },
  ];

  return (
    <div className="space-y-24 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-6">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-800 text-xs font-semibold tracking-wide uppercase">
          <Cpu className="w-3.5 h-3.5" />
          <span>Knowledge-Based Expert System (KBES)</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-[#2B2822] max-w-4xl mx-auto leading-tight">
          Deterministic Computer Network Troubleshooting,{' '}
          <span className="text-gold-700">
            Powered by Pure Logic
          </span>
        </h1>

        <p className="text-base sm:text-lg text-stone-600 max-w-2xl mx-auto leading-relaxed">
          NetSage dynamically evaluates networking symptoms using classical production rules,
          dual forward-and-backward chaining, and truth-maintenance logic. Zero black-box hallucinations.
        </p>

        {/* Backend Connectivity Status Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FFFCF5] border border-stone-300 text-xs text-stone-700">
          {loading ? (
            <span className="text-stone-600">Connecting to Backend API...</span>
          ) : backendStatus.connected ? (
            <span className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              API Connected: {backendStatus.project} v{backendStatus.version} (Port 8000)
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-rose-700">
              <AlertCircle className="w-4 h-4 text-rose-700" />
              Backend Offline: Run python -m uvicorn app.main:app
            </span>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link to="/diagnose">
            <Button
              variant="primary"
              size="lg"
              icon={<ArrowRight className="w-5 h-5" />}
              className="w-full sm:w-auto shadow-lg shadow-gold-600/20"
            >
              Start Diagnostic Session
            </Button>
          </Link>
          <Link to="/knowledge">
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              Explore Knowledge Base (28 Rules)
            </Button>
          </Link>
        </div>

        <div className="pt-2 text-xs text-stone-600 max-w-xl mx-auto flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-stone-600 flex-shrink-0" />
          <span>
            NetSage generates probable diagnoses based strictly on user-reported symptoms.
            It does not scan or mutate your live network.
          </span>
        </div>
      </section>

      {/* How NetSage Works */}
      <section className="space-y-10">
        <div className="text-center space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-[#2B2822] tracking-tight">
            How the Expert System Works
          </h2>
          <p className="text-sm text-stone-600 max-w-xl mx-auto">
            Traditional tools perform superficial blind pings. NetSage models diagnostic reasoning
            like a veteran network engineer.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="relative overflow-hidden border-stone-300">
            <div className="w-8 h-8 rounded-lg bg-gold-500/10 border border-gold-500/20 text-gold-700 flex items-center justify-center font-bold text-sm mb-4">
              1
            </div>
            <h3 className="text-base font-semibold text-[#2B2822] mb-1.5">Backward Inquiry</h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              Target hypotheses recursively resolve goal conditions to select the single most informative
              unanswered question next.
            </p>
          </Card>

          <Card className="relative overflow-hidden border-stone-300">
            <div className="w-8 h-8 rounded-lg bg-gold-500/10 border border-gold-500/20 text-gold-700 flex items-center justify-center font-bold text-sm mb-4">
              2
            </div>
            <h3 className="text-base font-semibold text-[#2B2822] mb-1.5">Tri-State Memory</h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              Maintains TRUE, FALSE, and UNKNOWN states. Missing information is never treated as FALSE,
              preventing unjustified conclusions.
            </p>
          </Card>

          <Card className="relative overflow-hidden border-stone-300">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
              3
            </div>
            <h3 className="text-base font-semibold text-[#2B2822] mb-1.5">Forward Chaining</h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              When evidence is asserted, production rules fire to deduction fix-point, deriving intermediate
              facts and detecting contradictions.
            </p>
          </Card>

          <Card className="relative overflow-hidden border-stone-300">
            <div className="w-8 h-8 rounded-lg bg-gold-500/10 border border-gold-500/20 text-gold-700 flex items-center justify-center font-bold text-sm mb-4">
              4
            </div>
            <h3 className="text-base font-semibold text-[#2B2822] mb-1.5">Remediation & Trace</h3>
            <p className="text-xs text-stone-600 leading-relaxed">
              Provides step-by-step CLI remediation plans with safety warnings, plus full visual DAG
              explanation of the reasoning path.
            </p>
          </Card>
        </div>
      </section>

      {/* Supported Diagnostic Categories */}
      <section className="space-y-10">
        <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-[#2B2822] tracking-tight">
              Six Comprehensive Diagnostic Domains
            </h2>
            <p className="text-sm text-stone-600 mt-1 max-w-xl">
              28 production rules covering physical, data link, network, transport, and application layer failures.
            </p>
          </div>
          <Link to="/knowledge" className="text-xs font-semibold text-gold-700 hover:text-gold-800 flex items-center gap-1">
            Browse All Rules <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((c) => (
            <Card key={c.id} hoverable className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-2 rounded-lg bg-[#EAE3D8]/80 border border-stone-400/60">
                  {c.icon}
                </div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#EAE3D8] text-stone-600 border border-stone-400">
                  {c.tag}
                </span>
              </div>
              <h3 className="text-base font-semibold text-stone-900">{c.name}</h3>
              <p className="text-xs text-stone-600 leading-relaxed">{c.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Classical Expert System vs LLM Comparison */}
      <section className="bg-[#FFFCF5]/60 border border-stone-300 rounded-2xl p-8 sm:p-10 space-y-6">
        <div className="max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-gold-700 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Sound & Auditable Reasoning</span>
          </div>
          <h2 className="text-2xl font-bold text-[#2B2822] tracking-tight">
            Why Rule-Based Expert Systems Excel for Troubleshooting
          </h2>
          <p className="text-xs text-stone-600 leading-relaxed">
            Unlike probabilistic Large Language Models which may fabricate nonexistent commands or hallucinate
            network percentages, NetSage guarantees formal logical consistency.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="p-4 rounded-xl bg-[#EAE3D8]/50 border border-stone-400/50 space-y-2">
            <h4 className="text-sm font-semibold text-gold-800 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              100% Deterministic
            </h4>
            <p className="text-xs text-stone-600">
              Identical symptoms always yield identical deductions and recommendations. Zero randomness or variability.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#EAE3D8]/50 border border-stone-400/50 space-y-2">
            <h4 className="text-sm font-semibold text-gold-800 flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-gold-700" />
              Complete WHY/HOW Transparency
            </h4>
            <p className="text-xs text-stone-600">
              Every single question explains exactly which hypothesis demands it. Every conclusion links to fired rules.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#EAE3D8]/50 border border-stone-400/50 space-y-2">
            <h4 className="text-sm font-semibold text-gold-800 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-amber-700" />
              Strict Conflict Detection
            </h4>
            <p className="text-xs text-stone-600">
              Refuses to silently resolve contradictory claims. Alerts users when contradictory evidence is submitted.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Banner */}
      <section className="text-center py-8 space-y-4">
        <h2 className="text-3xl font-bold text-[#2B2822]">Ready to diagnose your connection?</h2>
        <p className="text-sm text-stone-600 max-w-md mx-auto">
          Start a guided step-by-step diagnostic session. Answer structured technical questions to isolate the root cause.
        </p>
        <div className="pt-2">
          <Link to="/diagnose">
            <Button size="lg" variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
              Launch NetSage Diagnostic Wizard
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
};

import React from 'react';
import { ShieldCheck, Cpu, Database, GitBranch } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#29261F] border-t border-[#4A4338] py-8 text-xs text-[#BDB4A5]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pb-6 border-b border-[#4A4338]/80">
          <div className="md:col-span-2">
            <h4 className="text-sm font-semibold text-[#D6CCBA] mb-2">NetSage Expert System</h4>
            <p className="text-[#BDB4A5] text-xs leading-relaxed max-w-md">
              A Knowledge-Based Expert System (KBES) for computer network troubleshooting.
              Evaluates diagnostic hypotheses using pure Python forward deduction and backward inquiry.
              Diagnoses are probable assessments derived solely from user-reported symptoms and networking axioms.
            </p>
          </div>
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-[#BDB4A5] mb-2">Architecture</h5>
            <ul className="space-y-1.5 text-[#BDB4A5]">
              <li className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-gold-300" />
                <span>Deterministic Tri-State Logic</span>
              </li>
              <li className="flex items-center gap-1.5">
                <GitBranch className="w-3.5 h-3.5 text-gold-300" />
                <span>Dual Forward & Backward Chaining</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-emerald-300" />
                <span>Truth-Maintenance SQLite Audit</span>
              </li>
            </ul>
          </div>
          <div>
            <h5 className="text-xs font-semibold uppercase tracking-wider text-[#BDB4A5] mb-2">Operational Boundary</h5>
            <div className="flex items-start gap-1.5 text-[#BDB4A5]">
              <ShieldCheck className="w-4 h-4 text-amber-300 flex-shrink-0 mt-0.5" />
              <span>
                NetSage does not perform automated intrusive port scanning or direct network mutations. All recommendations require verified administrative execution.
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between pt-6 gap-3">
          <p className="text-[#BDB4A5]">
            © {new Date().getFullYear()} NetSage. Academic Computer Networks Mini-Project.
          </p>
          <div className="flex items-center gap-4 text-[#BDB4A5]">
            <span>FastAPI 0.115</span>
            <span>•</span>
            <span>React 18 & TypeScript</span>
            <span>•</span>
            <span>Pure Python Inference</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

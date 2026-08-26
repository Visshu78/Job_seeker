import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  LayoutDashboard, Target, ShieldCheck, SendHorizontal, 
  FileText, Sliders, Radio, ArrowRight
} from 'lucide-react';

export function Sidebar() {
  const { activeTab, setActiveTab, stats } = useApp();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'matches', label: 'Match Explorer', icon: Target, badge: stats?.high_fit_matches_count ? `${stats.high_fit_matches_count} High` : null, badgeColor: 'bg-accent-emerald/20 text-accent-emerald border-accent-emerald/30' },
    { id: 'applications', label: 'Applications', icon: SendHorizontal, badge: stats?.applications_submitted ? `${stats.applications_submitted} Active` : null, badgeColor: 'bg-brand-500/20 text-brand-400 border-brand-500/30' },
    { id: 'profile', label: 'Resume & Profile', icon: FileText, badge: null },
    { id: 'preferences', label: 'Job Preferences', icon: Sliders, badge: null },
    { id: 'discovery', label: 'Discovery Hub', icon: Radio, badge: 'Live Feed', badgeColor: 'bg-accent-violet/20 text-accent-violet border-accent-violet/30' },
  ];

  return (
    <aside className="w-64 border-r border-border bg-surface/50 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {/* Navigation list */}
        <div className="space-y-1">
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Platform Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-600/30 to-brand-500/10 text-brand-400 border border-brand-500/30 shadow-glow-brand'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Human-in-the-Loop Safety Assurance Card (PRD Section 30) */}
        <div className="p-4 rounded-2xl bg-gradient-to-b from-surface-card to-surface-card/40 border border-border">
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck className="w-4 h-4 text-accent-emerald" />
            <span className="text-xs font-bold text-slate-200">Human-In-The-Loop</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Zero silent applications. Every submission requires your explicit verification and authorization.
          </p>
        </div>
      </div>

      {/* Footer stats badge */}
      <div className="pt-4 border-t border-border/60 text-xs text-slate-500 flex items-center justify-between">
        <span>Engine v1.0.0</span>
        <span className="flex items-center gap-1 text-accent-emerald font-medium">
          <span className="w-2 h-2 rounded-full bg-accent-emerald animate-ping"></span>
          Ready
        </span>
      </div>
    </aside>
  );
}

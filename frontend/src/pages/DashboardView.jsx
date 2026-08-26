import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  Sparkles, Target, SendHorizontal, CheckCircle2, TrendingUp, 
  MapPin, Briefcase, Award, ArrowUpRight, ShieldCheck, Flame, Compass
} from 'lucide-react';

export function DashboardView() {
  const { stats, profile, setActiveTab, openMatchDetail } = useApp();

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-900/60 via-surface-card to-brand-950/40 p-8 border border-brand-500/20 shadow-glow-brand">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            AI Career Agent Active
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Welcome back, {profile?.full_name?.split(' ')[0] || 'Vishal'}
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed max-w-2xl">
            Your personal career agent continuously monitors multiple job sources, analyzes your resume fit, flags missing vs transferable skills, and prepares tailored application materials with human verification.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4">
            <button
              onClick={() => setActiveTab('matches')}
              className="px-5 py-2.5 rounded-xl font-semibold text-sm bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
            >
              <Target className="w-4 h-4" />
              Explore High-Fit Matches
            </button>
            <button
              onClick={() => setActiveTab('applications')}
              className="px-5 py-2.5 rounded-xl font-semibold text-sm bg-surface-hover hover:bg-slate-700/60 text-slate-200 border border-border transition flex items-center gap-2"
            >
              <SendHorizontal className="w-4 h-4 text-accent-emerald" />
              View Application Pipeline
            </button>
          </div>
        </div>

        {/* Decorative ambient gradient */}
        <div className="absolute right-0 top-0 -mt-8 -mr-8 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl glass-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Jobs Discovered Today</span>
            <div className="p-2 rounded-xl bg-brand-500/10 text-brand-400">
              <Compass className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{stats?.jobs_discovered_today || 6}</span>
            <span className="text-xs text-accent-emerald font-semibold">+100% fresh</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Consolidated across sources</p>
        </div>

        <div className="p-5 rounded-2xl glass-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">High-Fit Opportunities</span>
            <div className="p-2 rounded-xl bg-accent-emerald/10 text-accent-emerald">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{stats?.high_fit_matches_count || 4}</span>
            <span className="text-xs text-accent-emerald font-semibold">&gt; 80% Match</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Strongly recommended to apply</p>
        </div>

        <div className="p-5 rounded-2xl glass-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Average Match Fit</span>
            <div className="p-2 rounded-xl bg-accent-amber/10 text-accent-amber">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{stats?.average_match_score || 88.5}%</span>
            <span className="text-xs text-slate-400">Weighted AI score</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Skill + Semantic + Exp + Prefs</p>
        </div>

        <div className="p-5 rounded-2xl glass-card">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Applications Tracked</span>
            <div className="p-2 rounded-xl bg-accent-violet/10 text-accent-violet">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{stats?.applications_total || 2}</span>
            <span className="text-xs text-brand-400 font-semibold">{stats?.applications_submitted || 1} submitted</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">100% human-verified submissions</p>
        </div>
      </div>

      {/* Career Intelligence Insights (PRD Section 34) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-6 rounded-3xl glass-panel lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-lg text-white">Personalized Career Intelligence</h3>
              <p className="text-xs text-slate-400">Continuous analysis of your skill clusters and market alignment</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
              PRD Formula Active
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-surface-card border border-border/80 space-y-1">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-brand-400" />
                Best Matching Role
              </span>
              <div className="font-bold text-sm text-slate-100">
                {stats?.best_matching_role || 'Computer Vision & AI Engineer'}
              </div>
              <span className="text-[10px] text-accent-emerald font-medium">95% role alignment</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-border/80 space-y-1">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-accent-rose" />
                Top Location Hub
              </span>
              <div className="font-bold text-sm text-slate-100">
                {stats?.top_location || 'Bangalore / Remote'}
              </div>
              <span className="text-[10px] text-brand-400 font-medium">Matches your preferences</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-border/80 space-y-1">
              <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-accent-emerald" />
                Strongest Skill Cluster
              </span>
              <div className="font-bold text-sm text-slate-100 truncate">
                {stats?.top_skill_cluster || 'PyTorch + Vision'}
              </div>
              <span className="text-[10px] text-accent-emerald font-medium">Transferable to TensorFlow</span>
            </div>
          </div>

          {/* Quick Guidance Box */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-950/50 to-surface-card border border-brand-500/20 flex items-start gap-4">
            <div className="p-2.5 rounded-xl bg-brand-500/20 text-brand-300 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="space-y-1 text-xs">
              <div className="font-semibold text-white">Agent Recommendation Strategy</div>
              <p className="text-slate-300 leading-relaxed">
                You have strong foundational PyTorch and Computer Vision skills. The system has ranked <span className="text-brand-300 font-semibold">XYZ Labs AI</span> and <span className="text-brand-300 font-semibold">VisionCraft AI</span> as top recommendations because their missing requirements (e.g. AWS/Docker) are marked as preferred rather than mandatory.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Profile Summary */}
        <div className="p-6 rounded-3xl glass-panel space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-white">Active Candidate Profile</h3>
            <button
              onClick={() => setActiveTab('profile')}
              className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"
            >
              Edit <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-[11px] text-slate-400 font-medium">Headline</span>
              <p className="text-xs text-slate-200 font-medium mt-0.5">{profile?.headline || 'AI/ML Engineer'}</p>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 font-medium">Extracted Verified Skills</span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {(profile?.skills || ['Python', 'PyTorch', 'OpenCV', 'Deep Learning', 'Docker', 'SQL']).slice(0, 8).map((sk) => (
                  <span key={sk} className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-card text-slate-200 border border-border">
                    {sk}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
              <span className="text-slate-400">Experience Level:</span>
              <span className="font-semibold text-slate-200">{profile?.experience_level || 'Fresher (0-1 yrs)'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

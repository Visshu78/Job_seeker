import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  X, Sparkles, CheckCircle2, AlertTriangle, ArrowRight, 
  Lightbulb, Building2, MapPin, Banknote, Calendar, ShieldCheck, 
  ExternalLink, Layers, Check
} from 'lucide-react';

export function MatchDetailModal() {
  const { selectedMatch, closeMatchDetail, openApplicationStudio } = useApp();

  if (!selectedMatch) return null;

  const m = selectedMatch;
  const j = m.job;
  const isHigh = m.recommendation_tier === 'HIGH_PRIORITY';

  const handleStartApply = () => {
    const jobToApply = j;
    closeMatchDetail();
    openApplicationStudio(jobToApply);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl glass-panel border border-border shadow-2xl p-6 sm:p-8 space-y-6 text-left">
        {/* Modal Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                isHigh ? 'badge-high' : 'badge-consider'
              }`}>
                {m.overall_score}% Match Score — {isHigh ? 'Strongly Recommended' : 'Consider'}
              </span>
              <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-surface text-slate-300 border border-border">
                {j.source_name || 'Direct Source'}
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">{j.title}</h2>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1 font-semibold text-slate-200">
                <Building2 className="w-3.5 h-3.5 text-brand-400" />
                {j.company_name}
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                {j.location} ({j.remote_type})
              </span>
              <span className="flex items-center gap-1 text-accent-emerald font-semibold">
                <Banknote className="w-3.5 h-3.5" />
                {j.stipend ? `₹${j.stipend.toLocaleString()}/month` : j.salary_min ? `₹${(j.salary_min/100000).toFixed(1)}L - ${(j.salary_max/100000).toFixed(1)}L/yr` : 'Competitive'}
              </span>
            </div>
          </div>

          <button
            onClick={closeMatchDetail}
            className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-400 hover:text-white border border-border transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 6-Factor Weighted Breakdown Bars */}
        <div className="p-5 rounded-2xl bg-surface-card/60 border border-border/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              6-Factor Match Evaluation (PRD Section 21)
            </span>
            <span className="text-xs font-bold text-brand-400">Total: {m.overall_score}/100</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Skill Match (30%)', val: m.skill_score, color: 'bg-accent-emerald' },
              { label: 'Semantic Fit (25%)', val: m.semantic_score, color: 'bg-brand-500' },
              { label: 'Experience (15%)', val: m.experience_score, color: 'bg-accent-violet' },
              { label: 'Preference (15%)', val: m.preference_score, color: 'bg-accent-cyan' },
              { label: 'Role Alignment (10%)', val: m.role_score, color: 'bg-accent-amber' },
              { label: 'Education (5%)', val: m.education_score, color: 'bg-slate-400' },
            ].map((f) => (
              <div key={f.label} className="p-2.5 rounded-xl bg-surface border border-border text-center space-y-1">
                <div className="text-[10px] text-slate-400 truncate">{f.label}</div>
                <div className="text-sm font-bold text-white">{f.val}%</div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div className={`h-full rounded-full ${f.color}`} style={{ width: `${Math.min(100, f.val)}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Why You? & Gap Analysis (PRD Section 23 & 24) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strengths & Transferable */}
          <div className="p-5 rounded-2xl bg-surface-card/40 border border-accent-emerald/20 space-y-3">
            <div className="flex items-center gap-2 text-accent-emerald font-bold text-sm">
              <CheckCircle2 className="w-4 h-4" />
              <span>Matched & Transferable Skills</span>
            </div>

            <div className="space-y-2">
              {m.matched_skills?.map((ms) => (
                <div key={ms.skill} className="flex items-center justify-between text-xs p-2 rounded-lg bg-surface/80 border border-border">
                  <span className="text-slate-200 font-medium">{ms.skill}</span>
                  <span className="text-[10px] font-bold text-accent-emerald uppercase">{ms.type}</span>
                </div>
              ))}

              {m.transferable_skills?.map((ts) => (
                <div key={ts.required} className="p-2.5 rounded-lg bg-cyan-950/20 border border-cyan-500/30 text-xs space-y-1">
                  <div className="flex items-center justify-between font-semibold text-cyan-300">
                    <span>⚡ {ts.required} (Transferable)</span>
                    <span className="text-[10px] bg-cyan-500/20 px-1.5 py-0.5 rounded text-cyan-200">via {ts.candidate_has}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">{ts.explanation}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Missing Skills & Severity */}
          <div className="p-5 rounded-2xl bg-surface-card/40 border border-amber-500/20 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <AlertTriangle className="w-4 h-4" />
              <span>Missing Requirements & Severity</span>
            </div>

            <div className="space-y-2">
              {m.missing_skills?.length === 0 ? (
                <p className="text-xs text-accent-emerald">Zero missing requirements! Perfect baseline match.</p>
              ) : (
                m.missing_skills?.map((mis) => (
                  <div key={mis.skill} className="flex items-center justify-between text-xs p-2 rounded-lg bg-surface/80 border border-border">
                    <span className="text-slate-300 font-medium">{mis.skill}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      mis.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                    }`}>
                      {mis.type} ({mis.severity} impact)
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* AI Resume Suggestions (Non-Hallucinatory) (PRD Section 25) */}
        {m.resume_suggestions?.length > 0 && (
          <div className="p-5 rounded-2xl bg-gradient-to-r from-brand-950/40 to-surface-card border border-brand-500/30 space-y-3">
            <div className="flex items-center gap-2 text-brand-300 font-bold text-sm">
              <Lightbulb className="w-4 h-4 text-brand-400" />
              <span>AI Application Optimization Suggestions (Non-Fabricating)</span>
            </div>

            <div className="space-y-2.5">
              {m.resume_suggestions.map((sug, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface/80 border border-border text-xs space-y-1">
                  <div className="font-semibold text-white">{sug.title}</div>
                  <p className="text-slate-300">{sug.suggestion}</p>
                  <div className="text-[11px] text-slate-500 italic">Evidence in your resume: {sug.evidence_in_resume}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Job Description Full Preview */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Job Description</h4>
          <div className="p-4 rounded-2xl bg-surface text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-line border border-border">
            {j.description}
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <a
            href={j.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition"
          >
            <span>View Source Posting</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <div className="flex items-center gap-3">
            <button
              onClick={closeMatchDetail}
              className="px-4 py-2 rounded-xl text-xs font-medium bg-surface-card hover:bg-surface-hover text-slate-300 border border-border"
            >
              Close
            </button>
            <button
              onClick={handleStartApply}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
            >
              <ShieldCheck className="w-4 h-4 text-accent-emerald" />
              <span>Launch Application Studio</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

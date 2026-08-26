import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  Target, Bookmark, BookmarkCheck, XCircle, ArrowRight, 
  Sparkles, CheckCircle2, AlertCircle, ArrowUpRight, Filter, 
  MapPin, Banknote, Clock, Building2, ChevronRight, Layers
} from 'lucide-react';

export function MatchesView() {
  const { openMatchDetail, openApplicationStudio } = useApp();
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterTier, setFilterTier] = useState('ALL'); // ALL, HIGH_PRIORITY, CONSIDER, SAVED
  const [searchQuery, setSearchQuery] = useState('');

  const loadMatches = async () => {
    setLoading(true);
    try {
      const data = await api.getMatches();
      setMatches(data);
    } catch (err) {
      console.error('Error fetching matches:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatches();
  }, []);

  const handleSave = async (e, matchId) => {
    e.stopPropagation();
    try {
      await api.saveMatch(matchId);
      setMatches(prev => prev.map(m => m.id === matchId ? { ...m, is_saved: true, is_skipped: false } : m));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSkip = async (e, matchId) => {
    e.stopPropagation();
    try {
      await api.skipMatch(matchId);
      setMatches(prev => prev.filter(m => m.id !== matchId));
    } catch (err) {
      console.error(err);
    }
  };

  const filteredMatches = matches.filter(m => {
    if (filterTier === 'HIGH_PRIORITY' && m.recommendation_tier !== 'HIGH_PRIORITY') return false;
    if (filterTier === 'CONSIDER' && m.recommendation_tier !== 'CONSIDER') return false;
    if (filterTier === 'SAVED' && !m.is_saved) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        m.job.title.toLowerCase().includes(q) ||
        m.job.company_name.toLowerCase().includes(q) ||
        m.job.location.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Opportunity Match Explorer</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-400 border border-brand-500/30">
              {filteredMatches.length} Opportunities
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Weighted 6-factor AI matching, transferable skill reasoning, and gap analysis.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'HIGH_PRIORITY', 'CONSIDER', 'SAVED'].map((tier) => (
            <button
              key={tier}
              onClick={() => setFilterTier(tier)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
                filterTier === tier
                  ? 'bg-brand-600 text-white shadow-glow-brand'
                  : 'bg-surface-card hover:bg-surface-hover text-slate-300 border border-border'
              }`}
            >
              {tier === 'ALL' ? 'All Matches' : tier === 'HIGH_PRIORITY' ? '🔥 High Priority' : tier === 'CONSIDER' ? '⚡ Consider' : '🔖 Saved'}
            </button>
          ))}
        </div>
      </div>

      {/* Match Cards List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl animate-pulse">
          Evaluating job fit with AI matching engine...
        </div>
      ) : filteredMatches.length === 0 ? (
        <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl space-y-3">
          <Target className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No opportunities match this filter</h3>
          <p className="text-xs text-slate-500">Try changing your filter settings or trigger a fresh job sync.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMatches.map((m) => {
            const isHigh = m.recommendation_tier === 'HIGH_PRIORITY';
            return (
              <div
                key={m.id}
                onClick={() => openMatchDetail(m)}
                className={`p-6 rounded-3xl glass-card cursor-pointer border ${
                  isHigh ? 'border-brand-500/30 hover:border-brand-500/60' : 'border-border'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  {/* Left Job Info */}
                  <div className="space-y-3 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        isHigh ? 'badge-high' : 'badge-consider'
                      }`}>
                        {m.overall_score}% Match — {isHigh ? 'Strongly Recommended' : 'Consider'}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface text-slate-400 border border-border">
                        {m.job.source_name || 'ATS Feed'}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface text-slate-400 border border-border">
                        {m.job.employment_type}
                      </span>
                    </div>

                    <div>
                      <h2 className="text-lg font-bold text-white group-hover:text-brand-300 transition">
                        {m.job.title}
                      </h2>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1 text-slate-200 font-medium">
                          <Building2 className="w-3.5 h-3.5 text-brand-400" />
                          {m.job.company_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {m.job.location} ({m.job.remote_type})
                        </span>
                        <span className="flex items-center gap-1 text-accent-emerald font-semibold">
                          <Banknote className="w-3.5 h-3.5" />
                          {m.job.stipend ? `₹${m.job.stipend.toLocaleString()}/month` : m.job.salary_min ? `₹${(m.job.salary_min/100000).toFixed(1)}L - ${(m.job.salary_max/100000).toFixed(1)}L/yr` : 'Competitive'}
                        </span>
                      </div>
                    </div>

                    {/* Why Recommended / Gap Summary Snippet */}
                    <div className="p-3 rounded-xl bg-surface/60 border border-border/80 text-xs space-y-1.5">
                      <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                        <Sparkles className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                        <span className="text-white">{m.why_recommended}</span>
                      </div>
                      {m.gap_summary && (
                        <div className="text-[11px] text-slate-400 pl-5">
                          {m.gap_summary}
                        </div>
                      )}
                    </div>

                    {/* Skill Tags: Matched (Green), Transferable (Cyan), Missing (Amber) */}
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      {/* Matched */}
                      {m.matched_skills?.slice(0, 4).map((ms) => (
                        <span key={ms.skill} className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-accent-emerald/15 text-accent-emerald border border-accent-emerald/30 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          {ms.skill}
                        </span>
                      ))}

                      {/* Transferable */}
                      {m.transferable_skills?.slice(0, 2).map((ts) => (
                        <span key={ts.required} className="px-2 py-0.5 rounded-md text-[10px] font-semibold badge-transferable flex items-center gap-1" title={ts.explanation}>
                          ⚡ {ts.required} (via {ts.candidate_has})
                        </span>
                      ))}

                      {/* Missing */}
                      {m.missing_skills?.slice(0, 2).map((mis) => (
                        <span key={mis.skill} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                          Missing: {mis.skill} ({mis.type?.toLowerCase()})
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right Score Breakdown & Action Buttons */}
                  <div className="flex lg:flex-col items-center lg:items-end justify-between gap-4 border-t lg:border-t-0 border-border pt-4 lg:pt-0 shrink-0">
                    {/* 6-Factor Mini Score Gauges */}
                    <div className="grid grid-cols-3 gap-2 text-center text-[10px] bg-surface p-2.5 rounded-xl border border-border/80">
                      <div>
                        <div className="text-slate-400">Skill</div>
                        <div className="font-bold text-accent-emerald">{m.skill_score}%</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Semantic</div>
                        <div className="font-bold text-brand-400">{m.semantic_score}%</div>
                      </div>
                      <div>
                        <div className="text-slate-400">Role</div>
                        <div className="font-bold text-white">{m.role_score}%</div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => handleSave(e, m.id)}
                        className={`p-2.5 rounded-xl border transition ${
                          m.is_saved
                            ? 'bg-brand-600/30 text-brand-400 border-brand-500/40'
                            : 'bg-surface-card hover:bg-surface-hover text-slate-400 hover:text-white border-border'
                        }`}
                        title={m.is_saved ? 'Saved' : 'Save Opportunity'}
                      >
                        {m.is_saved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
                      </button>

                      <button
                        onClick={(e) => handleSkip(e, m.id)}
                        className="p-2.5 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-400 hover:text-accent-rose border border-border transition"
                        title="Skip this opportunity"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openApplicationStudio(m.job);
                        }}
                        className="px-4 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-1.5 shadow-md shadow-brand-600/30"
                      >
                        <span>Apply</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  Radio, RefreshCw, Layers, CheckCircle2, 
  ExternalLink, Building2, MapPin, Database, Cpu, ShieldCheck
} from 'lucide-react';

export function DiscoveryHubView() {
  const { refreshUserData } = useApp();
  const [jobs, setJobs] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [syncStats, setSyncStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await api.getJobs();
      setJobs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleTriggerSync = async () => {
    setSyncing(true);
    try {
      const res = await api.syncJobs();
      setSyncStats(res.stats);
      await api.recalculateMatches();
      await loadJobs();
      await refreshUserData();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Multi-Source Discovery Engine</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-vendor ingestion (Greenhouse, Lever, RemoteOK, Adzuna) with cross-board deduplication.
          </p>
        </div>

        <button
          onClick={handleTriggerSync}
          disabled={syncing}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          <span>{syncing ? 'Ingesting Feeds...' : 'Sync Sources & Deduplicate'}</span>
        </button>
      </div>

      {/* Ingestion & Deduplication Stats Banner (PRD Section 16 & 43) */}
      {syncStats && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-accent-emerald/10 to-surface-card border border-accent-emerald/30 flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-accent-emerald" />
            <div className="text-xs">
              <span className="font-bold text-white">Ingestion Complete: </span>
              <span className="text-slate-300">
                Fetched {syncStats.fetched} postings | {syncStats.new_inserted} normalized | {syncStats.duplicates_filtered} duplicate postings consolidated
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Connected Source Registry */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {[
          { name: 'Delhi NCR Startups', type: 'Gurugram/Noida Map', status: 'Active', latency: '0.1s' },
          { name: 'Indian Startup Map', type: 'DPIIT 450K+ Register', status: 'Active', latency: '0.1s' },
          { name: 'Bangalore Startups', type: 'BLR / Koramangala Hub', status: 'Active', latency: '0.2s' },
          { name: 'LinkedIn Jobs', type: 'Professional Network Feed', status: 'Active', latency: '0.3s' },
          { name: 'Greenhouse ATS', type: 'Direct Company ATS', status: 'Active', latency: '0.4s' },
          { name: 'RemoteOK API', type: 'Global Tech Board', status: 'Active', latency: '0.6s' }
        ].map((src) => (
          <div key={src.name} className="p-4 rounded-2xl glass-card border border-border space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white">{src.name}</span>
              <span className="w-2 h-2 rounded-full bg-accent-emerald animate-pulse"></span>
            </div>
            <div className="text-[11px] text-slate-400">{src.type}</div>
            <div className="pt-2 border-t border-border flex items-center justify-between text-[10px] text-slate-500">
              <span>Status: <span className="text-accent-emerald font-semibold">{src.status}</span></span>
              <span>{src.latency}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Normalized Job Postings Stream */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
            Normalized Job Stream ({jobs.length} Active Positions)
          </h3>
          <span className="text-xs text-slate-500">Auto-deduplicated</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl animate-pulse">
            Loading normalized job stream...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jobs.map((job) => (
              <div key={job.id} className="p-5 rounded-2xl glass-card border border-border space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-base font-bold text-white">{job.title}</h4>
                    <div className="text-xs font-medium text-slate-300 flex items-center gap-1.5 mt-0.5">
                      <Building2 className="w-3.5 h-3.5 text-brand-400" />
                      {job.company_name} · <span className="text-slate-400">{job.location}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-surface text-brand-400 border border-border">
                    {job.source_name || 'Direct'}
                  </span>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                  {job.description}
                </p>

                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  {job.requirements?.required_skills?.map((sk) => (
                    <span key={sk} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-surface text-slate-300 border border-border">
                      {sk}
                    </span>
                  ))}
                </div>

                <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
                  <span className="text-accent-emerald font-semibold">
                    {job.stipend ? `₹${job.stipend.toLocaleString()}/mo` : job.salary_min ? `₹${(job.salary_min/100000).toFixed(1)}L/yr` : 'Competitive'}
                  </span>
                  <a
                    href={job.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-400 hover:text-brand-300 flex items-center gap-1 text-[11px] font-medium"
                  >
                    <span>Inspect Raw Posting</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

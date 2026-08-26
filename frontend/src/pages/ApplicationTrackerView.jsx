import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  SendHorizontal, CheckCircle2, Clock, Calendar, 
  MessageSquare, Building2, MapPin, ChevronDown, Award, AlertCircle
} from 'lucide-react';

const STATUS_PIPELINE = [
  { key: 'SAVED', label: 'Saved', color: 'border-slate-600 text-slate-300' },
  { key: 'PREPARING', label: 'Preparing', color: 'border-brand-500 text-brand-400' },
  { key: 'SUBMITTED', label: 'Submitted', color: 'border-accent-cyan text-accent-cyan' },
  { key: 'UNDER_REVIEW', label: 'Under Review', color: 'border-accent-violet text-accent-violet' },
  { key: 'INTERVIEW', label: 'Interview', color: 'border-accent-amber text-accent-amber' },
  { key: 'OFFER', label: 'Offer Received', color: 'border-accent-emerald text-accent-emerald' },
  { key: 'REJECTED', label: 'Archived / Rejected', color: 'border-rose-500/40 text-rose-400' },
];

export function ApplicationTrackerView() {
  const { refreshUserData } = useApp();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');

  const loadApplications = async () => {
    setLoading(true);
    try {
      const data = await api.getApplications();
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const handleStatusChange = async (appId, newStatus) => {
    try {
      await api.updateApplicationStatus(appId, newStatus, `Candidate moved status to ${newStatus}`);
      await loadApplications();
      await refreshUserData();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredApps = applications.filter(a => {
    if (statusFilter === 'ALL') return true;
    return a.status === statusFilter;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Application Pipeline & Tracker</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30">
              {applications.length} Tracked
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track status progression from explicit authorization to interviews and offers.
          </p>
        </div>

        {/* Pipeline Filter */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
              statusFilter === 'ALL'
                ? 'bg-brand-600 text-white'
                : 'bg-surface-card text-slate-400 hover:bg-surface-hover border border-border'
            }`}
          >
            All ({applications.length})
          </button>
          {STATUS_PIPELINE.map((st) => (
            <button
              key={st.key}
              onClick={() => setStatusFilter(st.key)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                statusFilter === st.key
                  ? 'bg-brand-600 text-white'
                  : 'bg-surface-card text-slate-400 hover:bg-surface-hover border border-border'
              }`}
            >
              {st.label}
            </button>
          ))}
        </div>
      </div>

      {/* Application Cards */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl animate-pulse">
          Loading tracked applications...
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl space-y-3">
          <SendHorizontal className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-300">No applications in this status</h3>
          <p className="text-xs text-slate-500">Go to Opportunity Match Explorer to prepare and apply to jobs.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredApps.map((app) => {
            const currentStage = STATUS_PIPELINE.find(s => s.key === app.status) || STATUS_PIPELINE[0];
            return (
              <div key={app.id} className="p-6 rounded-3xl glass-card border border-border space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${currentStage.color} bg-surface`}>
                        {currentStage.label}
                      </span>
                      {app.user_reviewed && app.user_authorized && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Human Verified
                        </span>
                      )}
                    </div>
                    <h2 className="text-lg font-bold text-white">{app.job.title}</h2>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1 font-semibold text-slate-200">
                        <Building2 className="w-3.5 h-3.5 text-brand-400" />
                        {app.job.company_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        {app.job.location}
                      </span>
                      <span className="flex items-center gap-1 text-slate-400">
                        <Clock className="w-3.5 h-3.5" />
                        Submitted on: {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : 'Pending'}
                      </span>
                    </div>
                  </div>

                  {/* Status Picker Dropdown */}
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-slate-400">Update Status:</span>
                    <select
                      value={app.status}
                      onChange={(e) => handleStatusChange(app.id, e.target.value)}
                      className="px-3 py-1.5 rounded-xl glass-input text-xs font-semibold text-white cursor-pointer"
                    >
                      {STATUS_PIPELINE.map((st) => (
                        <option key={st.key} value={st.key} className="bg-surface text-slate-200">
                          {st.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Audit & Notes */}
                {app.notes && (
                  <div className="p-3 rounded-xl bg-surface/60 border border-border/80 text-xs text-slate-400 flex items-center gap-2">
                    <MessageSquare className="w-3.5 h-3.5 text-brand-400 shrink-0" />
                    <span>{app.notes}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

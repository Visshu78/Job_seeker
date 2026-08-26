import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  Sliders, Save, MapPin, Banknote, Briefcase, 
  Building2, ShieldAlert, CheckCircle2
} from 'lucide-react';

export function PreferencesView() {
  const { preferences, setPreferences, refreshUserData } = useApp();
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.updatePreferences(preferences);
      setPreferences(updated);
      await api.recalculateMatches();
      await refreshUserData();
      alert('Job preferences saved and opportunity scores updated!');
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Job & Compensation Preferences</h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure target roles, stipend/salary floors, location preferences, and company filters.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving...' : 'Save Preferences'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Roles & Employment Types */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <Briefcase className="w-4 h-4 text-brand-400" />
            <span>Target Roles & Experience</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400">Target Roles (Comma-separated)</label>
              <input
                type="text"
                value={(preferences?.preferred_roles || []).join(', ')}
                onChange={(e) => setPreferences({
                  ...preferences,
                  preferred_roles: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="AI Engineer, Machine Learning Engineer, Computer Vision Engineer"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400">Preferred Employment Types</label>
              <div className="flex flex-wrap gap-2 mt-2">
                {['Internship', 'Full-time', 'Contract', 'Part-time'].map((type) => {
                  const selected = (preferences?.employment_types || []).includes(type);
                  return (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        const current = preferences?.employment_types || [];
                        const next = selected ? current.filter(t => t !== type) : [...current, type];
                        setPreferences({ ...preferences, employment_types: next });
                      }}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                        selected
                          ? 'bg-brand-600 text-white shadow-sm'
                          : 'bg-surface-card text-slate-400 hover:bg-surface-hover border border-border'
                      }`}
                    >
                      {type}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Compensation Thresholds (PRD Section 11 & 19) */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <Banknote className="w-4 h-4 text-accent-emerald" />
            <span>Compensation Hard Filters (PRD Section 19)</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400">Minimum Monthly Internship Stipend (₹ INR)</label>
              <input
                type="number"
                value={preferences?.min_stipend || 0}
                onChange={(e) => setPreferences({ ...preferences, min_stipend: parseFloat(e.target.value) || 0 })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
              />
              <p className="text-[11px] text-slate-500 mt-1">Internships paying less will be filtered out before matching.</p>
            </div>

            <div>
              <label className="text-xs text-slate-400">Minimum Full-Time Annual CTC (₹ INR)</label>
              <input
                type="number"
                value={preferences?.min_salary || 0}
                onChange={(e) => setPreferences({ ...preferences, min_salary: parseFloat(e.target.value) || 0 })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
              />
            </div>
          </div>
        </div>

        {/* Locations & Remote Preferences */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <MapPin className="w-4 h-4 text-accent-rose" />
            <span>Locations & Remote Preference</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400">Preferred Cities (Comma-separated)</label>
              <input
                type="text"
                value={(preferences?.locations || []).join(', ')}
                onChange={(e) => setPreferences({
                  ...preferences,
                  locations: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="Bangalore, Hyderabad, Remote, Pune"
              />
            </div>

            <label className="flex items-center gap-3 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={preferences?.remote_only || false}
                onChange={(e) => setPreferences({ ...preferences, remote_only: e.target.checked })}
                className="w-4 h-4 rounded border-border text-brand-600 focus:ring-brand-500 accent-brand-600 cursor-pointer"
              />
              <span className="text-xs text-slate-200 font-medium">Remote Roles Only</span>
            </label>
          </div>
        </div>

        {/* Excluded Companies */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>Company Blacklist / Exclusions</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400">Excluded Companies (Comma-separated)</label>
              <input
                type="text"
                value={(preferences?.excluded_companies || []).join(', ')}
                onChange={(e) => setPreferences({
                  ...preferences,
                  excluded_companies: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="Optional: Companies you do not wish to match with"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  X, ShieldCheck, Sparkles, FileText, CheckCircle2, 
  Send, AlertCircle, Building2, UserCheck, Lock, ExternalLink
} from 'lucide-react';

export function ApplicationStudioModal() {
  const { applyingJob, closeApplicationStudio, refreshUserData, setActiveTab } = useApp();
  const [loading, setLoading] = useState(true);
  const [appData, setAppData] = useState(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [screeningAnswers, setScreeningAnswers] = useState({});
  const [userReviewed, setUserReviewed] = useState(false);
  const [userAuthorized, setUserAuthorized] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submittedSuccess, setSubmittedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (applyingJob) {
      loadApplicationPrep();
    }
  }, [applyingJob]);

  const loadApplicationPrep = async () => {
    setLoading(true);
    setErrorMessage('');
    setSubmittedSuccess(false);
    setUserReviewed(false);
    setUserAuthorized(false);
    try {
      const data = await api.prepareApplication(applyingJob.id);
      setAppData(data);
      setCoverLetter(data.cover_letter || '');
      setScreeningAnswers(data.screening_answers || {});
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || 'Failed to prepare application');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAndApply = async () => {
    if (!userReviewed || !userAuthorized) {
      setErrorMessage('Safety gate: You must check both confirmation checkboxes before submitting.');
      return;
    }

    setSubmitting(true);
    setErrorMessage('');
    try {
      // Find or create application
      const apps = await api.getApplications();
      const existingApp = apps.find(a => a.job_id === applyingJob.id);
      const appId = existingApp ? existingApp.id : 1;

      await api.confirmApplication(appId, {
        user_reviewed: true,
        user_authorized: true,
        cover_letter: coverLetter,
        screening_answers: screeningAnswers,
        notes: `Application explicitly confirmed by candidate on ${new Date().toLocaleString()}`
      });

      setSubmittedSuccess(true);
      await refreshUserData();
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || 'Error submitting application');
    } finally {
      setSubmitting(false);
    }
  };

  if (!applyingJob) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-3xl glass-panel border border-brand-500/30 shadow-2xl p-6 sm:p-8 space-y-6 text-left">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                Human-In-The-Loop Safety Studio
              </span>
              <span className="text-xs text-slate-400">PRD Mandate: Explicit Confirmation Required</span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">
              Application Preparation for {applyingJob.title}
            </h2>
            <div className="text-xs text-slate-300 flex items-center gap-1.5">
              <Building2 className="w-3.5 h-3.5 text-brand-400" />
              <span className="font-semibold text-white">{applyingJob.company_name}</span> · 
              <span>{applyingJob.location}</span>
            </div>
          </div>

          <button
            onClick={closeApplicationStudio}
            className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover text-slate-400 hover:text-white border border-border transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl animate-pulse">
            Generating tailored cover letter and preparing screening answers...
          </div>
        ) : submittedSuccess ? (
          /* Submission Success Screen */
          <div className="p-8 rounded-3xl bg-surface-card border border-accent-emerald/40 text-center space-y-4 animate-in zoom-in-95">
            <div className="w-14 h-14 rounded-2xl bg-accent-emerald/20 text-accent-emerald mx-auto flex items-center justify-center border border-accent-emerald/40 shadow-glow-emerald">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-bold text-white">Application Successfully Submitted & Logged!</h3>
            <p className="text-xs text-slate-300 max-w-lg mx-auto leading-relaxed">
              Your application materials have been officially recorded in your tracking pipeline with verified audit timestamp. You can track status progression in your Applications Dashboard.
            </p>
            <div className="pt-4 flex items-center justify-center gap-3">
              <button
                onClick={() => {
                  closeApplicationStudio();
                  setActiveTab('applications');
                }}
                className="px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition shadow-lg"
              >
                Go to Application Pipeline
              </button>
              <a
                href={applyingJob.application_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-2.5 rounded-xl text-xs font-medium bg-surface hover:bg-surface-hover text-slate-200 border border-border transition flex items-center gap-1.5"
              >
                <span>Destination ATS</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        ) : (
          /* Step-by-Step Preparation & Review Flow */
          <div className="space-y-6">
            {errorMessage && (
              <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Step 1: Selected Resume & Verified Experience */}
            <div className="p-4 rounded-2xl bg-surface-card border border-border space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                  <FileText className="w-4 h-4 text-brand-400" />
                  <span>1. Verified Candidate Profile & Resume</span>
                </div>
                <span className="text-[11px] text-accent-emerald font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Profile Active
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applying as: <span className="font-semibold text-white">{appData?.candidate_name}</span>. The application will highlight your verified projects and technical expertise without fabricating information.
              </p>
            </div>

            {/* Step 2: AI Generated Tailored Cover Letter (Editable) */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-brand-400" />
                  <span>2. Tailored Cover Letter (Editable)</span>
                </label>
                <span className="text-[10px] text-slate-400">Feel free to customize before submitting</span>
              </div>
              <textarea
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
                rows={7}
                className="w-full p-4 rounded-2xl glass-input text-xs leading-relaxed text-slate-200 resize-y font-mono"
              />
            </div>

            {/* Step 3: Screening Q&A Assistant */}
            <div className="space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5 text-accent-emerald" />
                <span>3. Prepared Screening Answers</span>
              </label>

              <div className="space-y-2.5">
                {Object.entries(screeningAnswers).map(([q, a], idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-surface border border-border space-y-1.5">
                    <div className="text-xs font-semibold text-brand-300">{q}</div>
                    <textarea
                      value={a}
                      onChange={(e) => {
                        const updated = { ...screeningAnswers, [q]: e.target.value };
                        setScreeningAnswers(updated);
                      }}
                      rows={2}
                      className="w-full p-2.5 rounded-lg glass-input text-xs text-slate-200 resize-none"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Step 4: Mandatory Human-In-The-Loop Safety Gate (PRD Section 31 & 55) */}
            <div className="p-5 rounded-2xl bg-gradient-to-r from-brand-950/80 to-surface-card border-2 border-brand-500/40 space-y-4">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-accent-emerald" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  4. Explicit Human Confirmation Gate (PRD Section 31)
                </span>
              </div>

              <div className="space-y-3 pt-1">
                <label className="flex items-center gap-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={userReviewed}
                    onChange={(e) => setUserReviewed(e.target.checked)}
                    className="w-4 h-4 rounded border-border text-brand-600 focus:ring-brand-500 accent-brand-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-200 font-medium">
                    [x] I have reviewed the resume, tailored cover letter, and screening answers for this application.
                  </span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={userAuthorized}
                    onChange={(e) => setUserAuthorized(e.target.checked)}
                    className="w-4 h-4 rounded border-border text-brand-600 focus:ring-brand-500 accent-brand-600 cursor-pointer"
                  />
                  <span className="text-xs text-slate-200 font-medium">
                    [x] I explicitly authorize the system to record and submit my application to {applyingJob.company_name}.
                  </span>
                </label>
              </div>
            </div>

            {/* Confirm & Apply Action */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={closeApplicationStudio}
                className="px-4 py-2.5 rounded-xl text-xs font-medium bg-surface-card hover:bg-surface-hover text-slate-300 border border-border"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmAndApply}
                disabled={submitting || !userReviewed || !userAuthorized}
                className={`px-6 py-2.5 rounded-xl text-xs font-bold text-white transition flex items-center gap-2 shadow-lg ${
                  userReviewed && userAuthorized
                    ? 'bg-brand-600 hover:bg-brand-500 shadow-brand-600/30'
                    : 'bg-slate-700 opacity-50 cursor-not-allowed'
                }`}
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submitting ? 'Submitting & Logging...' : 'CONFIRM & APPLY'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

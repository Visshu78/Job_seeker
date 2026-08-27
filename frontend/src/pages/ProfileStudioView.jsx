import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';
import { 
  Upload, FileText, CheckCircle2, Plus, Trash2, 
  Sparkles, Save, User, Briefcase, GraduationCap, Code, Phone, School, Award
} from 'lucide-react';

export function ProfileStudioView() {
  const { profile, setProfile, refreshUserData } = useApp();
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [newSkill, setNewSkill] = useState('');

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadSuccess(false);
    try {
      const updatedProfile = await api.uploadResume(file);
      setProfile(updatedProfile);
      setUploadSuccess(true);
      await api.recalculateMatches();
      await refreshUserData();
    } catch (err) {
      console.error(err);
      alert('Failed to upload & parse resume: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const updated = await api.updateProfile(profile);
      setProfile(updated);
      await api.recalculateMatches();
      await refreshUserData();
      alert('Profile updated and match scores recalculated!');
    } catch (err) {
      console.error(err);
      alert('Failed to save profile: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const addSkill = () => {
    if (!newSkill.trim()) return;
    const current = profile?.skills || [];
    if (!current.includes(newSkill.trim())) {
      setProfile({ ...profile, skills: [...current, newSkill.trim()] });
    }
    setNewSkill('');
  };

  const removeSkill = (sk) => {
    const current = profile?.skills || [];
    setProfile({ ...profile, skills: current.filter(s => s !== sk) });
  };

  const schooling10 = profile?.schooling?.class_10th || {};
  const schooling12 = profile?.schooling?.class_12th || {};

  const handleSchoolingChange = (std, field, value) => {
    const currentSchooling = profile?.schooling || {};
    const updatedStd = { ...(currentSchooling[std] || {}), [field]: value };
    setProfile({
      ...profile,
      schooling: { ...currentSchooling, [std]: updatedStd }
    });
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Resume & Candidate Profile Studio</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your personal credentials, student academic background (College, CGPA, Schooling), and skills taxonomy.
          </p>
        </div>

        <button
          onClick={handleSaveProfile}
          disabled={saving}
          className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-500 text-white transition flex items-center gap-2 shadow-lg shadow-brand-600/30 cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving & Re-matching...' : 'Save Profile Changes'}</span>
        </button>
      </div>

      {/* Resume Upload Dropzone */}
      <div className="p-6 rounded-3xl glass-panel border-2 border-dashed border-border hover:border-brand-500/50 transition text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-400 mx-auto flex items-center justify-center">
          <Upload className={`w-6 h-6 ${uploading ? 'animate-bounce' : ''}`} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Upload New Resume Document</h3>
          <p className="text-xs text-slate-400 mt-0.5">Supports PDF, DOCX, or Plain Text. Automatically extracted into structured profile fields.</p>
        </div>
        <div>
          <label className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-surface-card hover:bg-surface-hover text-slate-200 border border-border cursor-pointer transition shadow-sm">
            <FileText className="w-4 h-4 text-brand-400" />
            <span>{uploading ? 'Parsing with AI Engine...' : 'Select File'}</span>
            <input type="file" accept=".pdf,.docx,.txt" onChange={handleFileUpload} className="hidden" />
          </label>
        </div>
        {uploadSuccess && (
          <div className="text-xs text-accent-emerald font-medium flex items-center justify-center gap-1.5 pt-1">
            <CheckCircle2 className="w-4 h-4" />
            Resume parsed successfully into candidate profile!
          </div>
        )}
      </div>

      {/* Profile Form Grids */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-left">
        {/* Personal & Contact Details */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <User className="w-4 h-4 text-brand-400" />
            <span>Personal & Contact Details</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300">Full Name</label>
              <input
                type="text"
                value={profile?.full_name || ''}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="e.g. Alex Chen / Priya Sharma"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-300">Email Address</label>
                <input
                  type="email"
                  value={profile?.email || ''}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  placeholder="e.g. candidate@gmail.com"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1">
                  <Phone className="w-3 h-3 text-brand-400" /> Phone Number
                </label>
                <input
                  type="text"
                  value={profile?.phone_number || profile?.phone || ''}
                  onChange={(e) => setProfile({ ...profile, phone_number: e.target.value, phone: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  placeholder="e.g. +91 9876543210"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-300">Current Location</label>
                <input
                  type="text"
                  value={profile?.location || ''}
                  onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  placeholder="e.g. Bangalore, Karnataka"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Experience Level</label>
                <select
                  value={profile?.experience_level || 'Fresher'}
                  onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1 bg-surface-card"
                >
                  <option value="Fresher">Fresher / Student</option>
                  <option value="0-1 years">0-1 years</option>
                  <option value="1-2 years">1-2 years</option>
                  <option value="2-3 years">2-3 years</option>
                  <option value="Mid-Level">Mid-Level (3+ years)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300">Professional Headline</label>
              <input
                type="text"
                value={profile?.headline || ''}
                onChange={(e) => setProfile({ ...profile, headline: e.target.value })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="e.g. AI / Computer Vision Engineer | PyTorch, Deep Learning"
              />
            </div>
          </div>
        </div>

        {/* Academic & College Background */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <GraduationCap className="w-4 h-4 text-brand-400" />
            <span>Higher Education & College</span>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-slate-300">College / University Name</label>
              <input
                type="text"
                value={profile?.college_name || ''}
                onChange={(e) => setProfile({ ...profile, college_name: e.target.value })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="e.g. IIT Delhi, BITS Pilani, NIT Trichy"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300">Degree & Major</label>
              <input
                type="text"
                value={profile?.degree || ''}
                onChange={(e) => setProfile({ ...profile, degree: e.target.value })}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="e.g. B.Tech in Computer Science & Engineering"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1">
                  <Award className="w-3 h-3 text-accent-amber" /> CGPA / Percentage
                </label>
                <input
                  type="text"
                  value={profile?.cgpa || ''}
                  onChange={(e) => setProfile({ ...profile, cgpa: e.target.value })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  placeholder="e.g. 8.8 / 10 or 88%"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300">Graduation Year</label>
                <input
                  type="number"
                  value={profile?.graduation_year || 2025}
                  onChange={(e) => setProfile({ ...profile, graduation_year: parseInt(e.target.value) || 2025 })}
                  className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  placeholder="e.g. 2025"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Schooling Background (10th & 12th) */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <School className="w-4 h-4 text-accent-cyan" />
            <span>Schooling Records (Class 10th & 12th)</span>
          </div>

          <div className="space-y-4">
            {/* Class 12th */}
            <div className="p-3.5 rounded-2xl bg-surface/80 border border-border/70 space-y-2">
              <span className="text-xs font-bold text-brand-300">Senior Secondary (Class 12th / PUC)</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="text"
                  placeholder="School Name"
                  value={schooling12.school || ''}
                  onChange={(e) => handleSchoolingChange('class_12th', 'school', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
                <input
                  type="text"
                  placeholder="Board (e.g. CBSE / State)"
                  value={schooling12.board || ''}
                  onChange={(e) => handleSchoolingChange('class_12th', 'board', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
                <input
                  type="text"
                  placeholder="Score (% or CGPA)"
                  value={schooling12.percentage || ''}
                  onChange={(e) => handleSchoolingChange('class_12th', 'percentage', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
              </div>
            </div>

            {/* Class 10th */}
            <div className="p-3.5 rounded-2xl bg-surface/80 border border-border/70 space-y-2">
              <span className="text-xs font-bold text-brand-300">High School (Class 10th / Matriculation)</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="text"
                  placeholder="School Name"
                  value={schooling10.school || ''}
                  onChange={(e) => handleSchoolingChange('class_10th', 'school', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
                <input
                  type="text"
                  placeholder="Board (e.g. CBSE / ICSE)"
                  value={schooling10.board || ''}
                  onChange={(e) => handleSchoolingChange('class_10th', 'board', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
                <input
                  type="text"
                  placeholder="Score (% or CGPA)"
                  value={schooling10.percentage || ''}
                  onChange={(e) => handleSchoolingChange('class_10th', 'percentage', e.target.value)}
                  className="p-2 rounded-xl glass-input text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Technical Skills Tag Manager */}
        <div className="p-6 rounded-3xl glass-panel space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-border pb-3">
            <Code className="w-4 h-4 text-accent-emerald" />
            <span>Extracted Technical Skills Taxonomy</span>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add skill (e.g. PyTorch, Docker, React)..."
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addSkill()}
              className="flex-1 p-2.5 rounded-xl glass-input text-xs"
            />
            <button
              onClick={addSkill}
              className="px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold transition flex items-center gap-1 cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>

          <div className="flex flex-wrap gap-2 max-h-52 overflow-y-auto p-3 rounded-2xl bg-surface border border-border/60">
            {(profile?.skills || []).map((sk) => (
              <span
                key={sk}
                className="px-3 py-1.5 rounded-xl text-xs font-medium bg-surface-card hover:bg-surface-hover text-slate-200 border border-border flex items-center gap-2 group transition"
              >
                <span>{sk}</span>
                <button
                  onClick={() => removeSkill(sk)}
                  className="text-slate-500 hover:text-accent-rose transition cursor-pointer"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

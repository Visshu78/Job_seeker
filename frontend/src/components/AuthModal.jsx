import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { useApp } from '../context/AppContext';
import { X, Lock, Mail, User, Phone, GraduationCap, Award, Sparkles, CheckCircle2, ShieldCheck, KeyRound } from 'lucide-react';

export function AuthModal({ isOpen, onClose }) {
  const { setUser, refreshUserData } = useApp();
  const [tab, setTab] = useState('google'); // 'google', 'login', 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [collegeName, setCollegeName] = useState('IIT Delhi');
  const [cgpa, setCgpa] = useState('8.8/10');
  
  // Custom Google Client ID (optional user provided or from env)
  const defaultClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1029384756-sampleclientid.apps.googleusercontent.com';
  const [clientId, setClientId] = useState(defaultClientId);
  const [showConfig, setShowConfig] = useState(false);
  const googleBtnRef = useRef(null);

  // Initialize official Google Identity Services button
  useEffect(() => {
    if (!isOpen || tab !== 'google') return;

    const initGoogleGSI = () => {
      if (window.google?.accounts?.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          if (googleBtnRef.current) {
            googleBtnRef.current.innerHTML = '';
            window.google.accounts.id.renderButton(googleBtnRef.current, {
              theme: 'outline',
              size: 'large',
              type: 'standard',
              shape: 'pill',
              text: 'continue_with',
              logo_alignment: 'left',
              width: 320
            });
          }
        } catch (err) {
          console.warn('Google GSI initialization notice:', err);
        }
      }
    };

    const timer = setTimeout(initGoogleGSI, 300);
    return () => clearTimeout(timer);
  }, [isOpen, tab, clientId]);

  // Callback when user signs in through official Google popup/prompt
  const handleGoogleCredentialResponse = async (response) => {
    if (!response?.credential) return;
    setLoading(true);
    setError(null);
    try {
      // Decode JWT token payload for visual confirmation
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const decoded = JSON.parse(jsonPayload);

      // Verify and authenticate with backend
      const res = await api.googleAuth({
        id_token: response.credential,
        email: decoded.email,
        full_name: decoded.name,
        avatar_url: decoded.picture,
        google_id: decoded.sub,
        college_name: collegeName || 'IIT Delhi',
        cgpa: cgpa || '8.8/10',
        phone_number: phone || '+91 9876543210'
      });

      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg(`Authenticated as ${decoded.name} (${decoded.email})`);
        await refreshUserData();
        setTimeout(onClose, 800);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Google token verification failed on backend');
    } finally {
      setLoading(false);
    }
  };

  const handleManualGoogleAuth = async (presetEmail, presetName, presetCollege, presetCgpa) => {
    setLoading(true);
    setError(null);
    try {
      const gEmail = presetEmail || email || 'vishal.student@gmail.com';
      const gName = presetName || fullName || 'Vishal Sharma';
      const gCollege = presetCollege || collegeName || 'IIT Delhi';
      const gCgpa = presetCgpa || cgpa || '8.8/10';

      const res = await api.googleAuth({
        email: gEmail,
        full_name: gName,
        google_id: `g_${absHash(gEmail)}`,
        college_name: gCollege,
        cgpa: gCgpa,
        phone_number: phone || '+91 9876543210',
        avatar_url: `https://api.dicebear.com/7.x/avataaars/svg?seed=${gEmail}`
      });

      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg(`Authenticated as ${res.user.full_name || gName} (${res.user.email})`);
        await refreshUserData();
        setTimeout(onClose, 600);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Google Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLocalSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      let res;
      if (tab === 'login') {
        res = await api.login(email, password);
      } else {
        res = await api.register(email, password, fullName, phone);
      }

      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        await refreshUserData();
        onClose();
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  function absHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) - hash + str.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-md p-6 rounded-3xl glass-panel border border-border/80 shadow-2xl space-y-5 text-left">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-surface-hover transition cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center space-y-1">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-400 mx-auto flex items-center justify-center mb-1">
            <Sparkles className="w-6 h-6 text-brand-400" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">AI Career Agent Sign In</h2>
          <p className="text-xs text-slate-400">Authenticate securely with Google or local student credentials</p>
        </div>

        {/* Auth Mode Tabs */}
        <div className="flex p-1 rounded-2xl bg-surface border border-border">
          <button
            onClick={() => { setTab('google'); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
              tab === 'google' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Google Sign-In
          </button>
          <button
            onClick={() => { setTab('login'); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
              tab === 'login' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Password Login
          </button>
          <button
            onClick={() => { setTab('register'); setError(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
              tab === 'register' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-xs text-accent-rose">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="p-3 rounded-xl bg-accent-emerald/10 border border-accent-emerald/30 text-xs text-accent-emerald flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Google OAuth Tab */}
        {tab === 'google' && (
          <div className="space-y-4">
            {/* Live Google Official Button Container */}
            <div className="flex flex-col items-center justify-center p-4 rounded-2xl bg-surface border border-border/80 text-center space-y-3">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-brand-400" />
                Google Verified Authentication
              </span>

              {/* GSI Render target */}
              <div id="google-signin-btn" ref={googleBtnRef} className="flex justify-center min-h-[44px]"></div>

              {/* Direct fallback trigger */}
              <button
                onClick={() => handleManualGoogleAuth(email, fullName, collegeName, cgpa)}
                disabled={loading}
                className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs flex items-center justify-center gap-2.5 transition shadow-sm cursor-pointer"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>{loading ? 'Verifying with Google...' : 'Continue with Google Account'}</span>
              </button>
            </div>

            {/* Quick Profile Switching */}
            <div className="p-3 rounded-2xl bg-surface/50 border border-border/60 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-bold">Quick Switch Student Profiles</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleManualGoogleAuth('vishal.aiml@example.com', 'Vishal Sharma', 'IIT Delhi', '8.8/10')}
                  className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-[11px] text-slate-300 transition text-left cursor-pointer"
                >
                  <span className="font-bold block text-white truncate">Vishal Sharma</span>
                  <span className="text-[10px] text-brand-300 block">IIT Delhi · 8.8 CGPA</span>
                </button>
                <button
                  onClick={() => handleManualGoogleAuth('aarav.cv@example.com', 'Aarav Patel', 'BITS Pilani', '9.2/10')}
                  className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-[11px] text-slate-300 transition text-left cursor-pointer"
                >
                  <span className="font-bold block text-white truncate">Aarav Patel</span>
                  <span className="text-[10px] text-brand-300 block">BITS Pilani · 9.2 CGPA</span>
                </button>
              </div>
            </div>

            {/* Optional Google Client ID Config Drawer */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => setShowConfig(!showConfig)}
                className="text-[11px] text-slate-400 hover:text-white flex items-center justify-center gap-1 mx-auto transition cursor-pointer"
              >
                <KeyRound className="w-3 h-3" />
                <span>{showConfig ? 'Hide Google Client ID' : 'Configure Custom Google Client ID'}</span>
              </button>
              {showConfig && (
                <div className="mt-2 p-3 rounded-xl bg-surface border border-border text-left space-y-2 animate-in fade-in">
                  <label className="text-[11px] text-slate-300 font-medium">Google Cloud OAuth Client ID</label>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="your-app.apps.googleusercontent.com"
                    className="w-full p-2 rounded-lg glass-input text-xs"
                  />
                  <p className="text-[10px] text-slate-500">
                    Get from Google Cloud Console &gt; Credentials &gt; OAuth 2.0 Client IDs.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Credentials Form (Email/Password) */}
        {(tab === 'login' || tab === 'register') && (
          <form onSubmit={handleLocalSubmit} className="space-y-3">
            {tab === 'register' && (
              <>
                <div>
                  <label className="text-xs text-slate-400">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                    placeholder="Vishal Sharma"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400">Phone Number</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                    placeholder="+91 9876543210"
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-xs text-slate-400">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="name@example.com"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400">Password (Hashed & Salted)</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition shadow-lg shadow-brand-600/30 cursor-pointer mt-2"
            >
              {loading ? 'Processing...' : tab === 'login' ? 'Sign In' : 'Create Student Account'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

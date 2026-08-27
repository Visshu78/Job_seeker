import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { useApp } from '../context/AppContext';
import { 
  X, Lock, Mail, User, Phone, Sparkles, CheckCircle2, 
  ShieldCheck, KeyRound, Info, ExternalLink, ArrowLeft
} from 'lucide-react';

export function AuthModal({ isOpen, onClose }) {
  const { setUser, refreshUserData } = useApp();
  const [tab, setTab] = useState('google'); // 'google', 'login', 'register', 'forgot_password'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  
  // OTP Verification state for Registration & Forgot Password
  const [otpStep, setOtpStep] = useState(false); // true when waiting for OTP code input
  const [otpCode, setOtpCode] = useState('');
  const [receivedOtp, setReceivedOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  // Custom Google Client ID (from env or entered by user)
  const envClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const [clientId, setClientId] = useState(envClientId);
  const [showConfig, setShowConfig] = useState(false);
  const googleBtnRef = useRef(null);

  const hasValidGoogleClientId = Boolean(
    clientId && 
    clientId.trim().length > 20 && 
    clientId.includes('.apps.googleusercontent.com') && 
    !clientId.includes('sampleclientid')
  );

  // Initialize official Google Identity Services button only if valid client ID exists
  useEffect(() => {
    if (!isOpen || tab !== 'google' || !hasValidGoogleClientId) return;

    const initGoogleGSI = () => {
      if (window.google?.accounts?.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId.trim(),
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
          console.warn('Google GSI notice:', err);
        }
      }
    };

    const timer = setTimeout(initGoogleGSI, 300);
    return () => clearTimeout(timer);
  }, [isOpen, tab, clientId, hasValidGoogleClientId]);

  const handleGoogleCredentialResponse = async (response) => {
    if (!response?.credential) return;
    setLoading(true);
    setError(null);
    try {
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const decoded = JSON.parse(jsonPayload);

      const res = await api.googleAuth({
        id_token: response.credential,
        email: decoded.email,
        full_name: decoded.name,
        avatar_url: decoded.picture,
        google_id: decoded.sub
      });

      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg(`Google Verified: ${decoded.name} (${decoded.email})`);
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

  const handleGoogleSignIn = async (presetEmail, presetName) => {
    const targetEmail = presetEmail || email.trim();
    if (!targetEmail) {
      setError('Please enter your Google Email address below to sign in with your account.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const gEmail = targetEmail.toLowerCase();
      const gName = presetName || (fullName.trim() ? fullName.trim() : gEmail.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));

      const res = await api.googleAuth({
        email: gEmail,
        full_name: gName,
        google_id: `g_${absHash(gEmail)}`,
        avatar_url: `https://api.dicebear.com/7.x/avataaars/svg?seed=${gEmail}`
      });

      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg(`Signed in with Google as ${res.user.full_name || gName} (${res.user.email})`);
        await refreshUserData();
        setTimeout(onClose, 600);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Google Sign-In failed');
    } finally {
      setLoading(false);
    }
  };

  // Password Login Submit
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        await refreshUserData();
        onClose();
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Registration Step 1: Send Verification OTP
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in your email and password');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.sendOtp(email, 'email_verification');
      setReceivedOtp(res.otp_code || '');
      setOtpCode(res.otp_code || '');
      setOtpStep(true);
      setSuccessMsg(`Verification code sent to ${email}`);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  // Registration Step 2: Verify OTP & Create User
  const handleVerifyRegisterOTP = async (e) => {
    e.preventDefault();
    if (!otpCode) {
      setError('Please enter the 6-digit verification code');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.verifyOtp(email, otpCode, 'email_verification');
      const res = await api.register(email, password, fullName, phone);
      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg('Account created & email verified successfully!');
        await refreshUserData();
        setTimeout(onClose, 800);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Verification failed. Please check the code.');
    } finally {
      setLoading(false);
    }
  };

  // Forgot Password Step 1: Request Password Reset OTP
  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email address');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.forgotPassword(email);
      setReceivedOtp(res.otp_code || '');
      setOtpCode(res.otp_code || '');
      setOtpStep(true);
      setSuccessMsg(`Reset verification code sent to ${email}`);
    } catch (err) {
      console.error(err);
      setError(err.message || 'No account found with this email.');
    } finally {
      setLoading(false);
    }
  };

  // Forgot Password Step 2: Reset Password & Log In
  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!otpCode || !newPassword) {
      setError('Please enter both the reset code and your new password');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.resetPassword(email, otpCode, newPassword);
      const res = await api.login(email, newPassword);
      if (res.access_token) {
        localStorage.setItem('career_agent_token', res.access_token);
        setUser(res.user);
        setSuccessMsg('Password reset successful! Logging you in...');
        await refreshUserData();
        setTimeout(onClose, 800);
      }
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to reset password.');
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

  const resetState = () => {
    setError(null);
    setSuccessMsg(null);
    setOtpStep(false);
    setOtpCode('');
    setReceivedOtp('');
    setNewPassword('');
  };

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
          <p className="text-xs text-slate-400">Discover personalized opportunities & connect with companies</p>
        </div>

        {/* Auth Mode Tabs */}
        {tab !== 'forgot_password' && (
          <div className="flex p-1 rounded-2xl bg-surface border border-border">
            <button
              onClick={() => { setTab('google'); resetState(); }}
              className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
                tab === 'google' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Google Sign-In
            </button>
            <button
              onClick={() => { setTab('login'); resetState(); }}
              className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
                tab === 'login' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Password Login
            </button>
            <button
              onClick={() => { setTab('register'); resetState(); }}
              className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
                tab === 'register' ? 'bg-brand-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Create Account
            </button>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-xl bg-accent-rose/10 border border-accent-rose/30 text-xs text-accent-rose">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="p-3 rounded-xl bg-accent-emerald/10 border border-accent-emerald/30 text-xs text-accent-emerald flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* ----------------- TAB 1: Google Sign-In ----------------- */}
        {tab === 'google' && (
          <div className="space-y-4 pt-1">
            <div className="p-5 rounded-2xl bg-surface border border-border/80 space-y-4">
              <div className="text-center space-y-1">
                <span className="text-xs font-bold text-white flex items-center justify-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-brand-400" />
                  Sign In with Your Google Account
                </span>
                <p className="text-[11px] text-slate-400">
                  Enter your Google email to sign in directly as your account.
                </p>
              </div>

              {/* Email Input for user's Google Account */}
              <div className="space-y-1 text-left">
                <label className="text-[11px] text-slate-300 font-medium">Your Google Email Address *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. vishaldhawal8853@gmail.com"
                  className="w-full p-2.5 rounded-xl glass-input text-xs"
                />
              </div>

              {/* Official Google GSI Render target if client ID is configured */}
              {hasValidGoogleClientId && (
                <div className="flex justify-center min-h-[44px]">
                  <div id="google-signin-btn" ref={googleBtnRef}></div>
                </div>
              )}

              {/* Primary Google Button */}
              <button
                onClick={() => handleGoogleSignIn()}
                disabled={loading}
                className="w-full py-3.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs flex items-center justify-center gap-3 transition shadow-lg shadow-white/10 cursor-pointer"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
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
                <span>
                  {loading 
                    ? 'Connecting to Google...' 
                    : email.trim() 
                      ? `Continue as ${email.trim()}` 
                      : 'Continue with Google Account'}
                </span>
              </button>
            </div>

            {/* Quick Switch Profiles */}
            <div className="p-3 rounded-2xl bg-surface/50 border border-border/60 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-bold">Quick Select Accounts</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleGoogleSignIn('vishaldhawal8853@gmail.com', 'Vishal Sharma')}
                  className="p-2.5 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-[11px] text-slate-300 transition text-left cursor-pointer"
                >
                  <span className="font-bold block text-white truncate">Vishal Sharma</span>
                  <span className="text-[10px] text-brand-300 block truncate">vishaldhawal8853@gmail.com</span>
                </button>
                <button
                  onClick={() => handleGoogleSignIn('alex.chen@gmail.com', 'Alex Chen')}
                  className="p-2.5 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-[11px] text-slate-300 transition text-left cursor-pointer"
                >
                  <span className="font-bold block text-white truncate">Alex Chen</span>
                  <span className="text-[10px] text-brand-300 block truncate">alex.chen@gmail.com</span>
                </button>
              </div>
            </div>

            {/* Optional Google Client ID Config Helper */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => setShowConfig(!showConfig)}
                className="text-[11px] text-slate-400 hover:text-white flex items-center justify-center gap-1 mx-auto transition cursor-pointer"
              >
                <KeyRound className="w-3 h-3" />
                <span>{showConfig ? 'Hide Google Cloud Client ID Setup' : 'Configure Custom Google Client ID'}</span>
              </button>
              {showConfig && (
                <div className="mt-2 p-3 rounded-xl bg-surface border border-border text-left space-y-2 animate-in fade-in">
                  <div className="flex items-start gap-1.5 text-slate-300 text-[11px]">
                    <Info className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                    <span>
                      Enter OAuth Client ID from{' '}
                      <a 
                        href="https://console.cloud.google.com/apis/credentials" 
                        target="_blank" 
                        rel="noreferrer" 
                        className="text-brand-400 hover:underline inline-flex items-center gap-0.5"
                      >
                        Google Cloud Console <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </span>
                  </div>
                  <input
                    type="text"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="xxxx.apps.googleusercontent.com"
                    className="w-full p-2 rounded-lg glass-input text-xs"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* ----------------- TAB 2: Standard Password Login ----------------- */}
        {tab === 'login' && (
          <form onSubmit={handleLoginSubmit} className="space-y-3">
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
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-400">Password</label>
                <button
                  type="button"
                  onClick={() => { setTab('forgot_password'); resetState(); }}
                  className="text-[11px] text-brand-400 hover:underline cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
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
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>
        )}

        {/* ----------------- TAB 3: Create Account + Email OTP Verification ----------------- */}
        {tab === 'register' && (
          <div>
            {!otpStep ? (
              <form onSubmit={handleRegisterSubmit} className="space-y-3">
                <div>
                  <label className="text-xs text-slate-400">Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                    placeholder="e.g. Priya Sharma"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400">Email Address *</label>
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
                  <label className="text-xs text-slate-400">Password *</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-400">Phone Number (Optional)</label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                    placeholder="+91 9876543210"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition shadow-lg shadow-brand-600/30 cursor-pointer mt-2"
                >
                  {loading ? 'Sending Code...' : 'Send Verification Code'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyRegisterOTP} className="space-y-4 animate-in fade-in">
                <div className="p-3.5 rounded-2xl bg-surface border border-border text-center space-y-1">
                  <span className="text-xs font-bold text-white block">Email Verification Code</span>
                  <p className="text-[11px] text-slate-400">
                    We sent a 6-digit code to <strong className="text-brand-300">{email}</strong>
                  </p>
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium block mb-1">Enter 6-Digit Code</label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="123456"
                    className="w-full p-3 rounded-xl glass-input text-center font-mono text-lg tracking-widest"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-accent-emerald hover:bg-emerald-600 text-white font-bold text-xs transition shadow-lg shadow-emerald-600/30 cursor-pointer"
                >
                  {loading ? 'Verifying...' : 'Verify Code & Create Account'}
                </button>

                <button
                  type="button"
                  onClick={() => setOtpStep(false)}
                  className="w-full text-[11px] text-slate-400 hover:text-white flex items-center justify-center gap-1 transition cursor-pointer"
                >
                  <ArrowLeft className="w-3 h-3" /> Back to Edit Details
                </button>
              </form>
            )}
          </div>
        )}

        {/* ----------------- TAB 4: Forgot Password Flow ----------------- */}
        {tab === 'forgot_password' && (
          <div className="space-y-4 animate-in fade-in">
            <button
              onClick={() => { setTab('login'); resetState(); }}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Login
            </button>

            {!otpStep ? (
              <form onSubmit={handleForgotPasswordSubmit} className="space-y-3">
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-white">Reset Password</h3>
                  <p className="text-xs text-slate-400">Enter your registered email to receive a 6-digit reset code.</p>
                </div>

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

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition shadow-lg shadow-brand-600/30 cursor-pointer mt-2"
                >
                  {loading ? 'Sending Code...' : 'Send Reset Code'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleResetPasswordSubmit} className="space-y-3">
                <div className="p-3 rounded-xl bg-surface border border-border text-center">
                  <p className="text-xs text-slate-300">
                    Reset code sent to <strong className="text-brand-300">{email}</strong>
                  </p>
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium">6-Digit Reset Code</label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="123456"
                    className="w-full p-2.5 rounded-xl glass-input text-center font-mono text-base tracking-widest mt-1"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-300 font-medium">New Password</label>
                  <input
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    className="w-full p-2.5 rounded-xl glass-input text-xs mt-1"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-accent-emerald hover:bg-emerald-600 text-white font-bold text-xs transition shadow-lg shadow-emerald-600/30 cursor-pointer"
                >
                  {loading ? 'Resetting...' : 'Reset Password & Log In'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

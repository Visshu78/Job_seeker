import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { 
  Sparkles, Bell, RefreshCw, ChevronDown, CheckCheck, GraduationCap, User, LogIn, LogOut
} from 'lucide-react';
import { api } from '../api';
import { AuthModal } from './AuthModal';

export function Navbar() {
  const { 
    user, profile, unreadCount, notifications, refreshUserData, 
    logout, setActiveTab 
  } = useApp();
  const [showNotifs, setShowNotifs] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSync = async () => {
    try {
      setSyncing(true);
      await api.syncJobs();
      await api.recalculateMatches();
      await refreshUserData();
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setSyncing(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      await refreshUserData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      <header className="h-16 border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-40 px-6 flex items-center justify-between">
        {/* Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-accent-violet flex items-center justify-center shadow-glow-brand">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-brand-400 bg-clip-text text-transparent">
                CareerAgent AI
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-brand-500/20 text-brand-400 border border-brand-500/30">
                Student & AI SaaS
              </span>
            </div>
            <p className="text-xs text-slate-400">Personalized Job Discovery & Human-In-The-Loop Agent</p>
          </div>
        </div>

        {/* Center Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium bg-surface-card hover:bg-surface-hover border border-border text-slate-300 hover:text-white transition-all shadow-sm cursor-pointer"
            title="Run Multi-Source Ingestion & AI Re-Matching"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-brand-400 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing 8 Sources...' : 'Sync Job Sources'}</span>
          </button>
        </div>

        {/* Right Controls: Google Auth & Notifications & User Profile */}
        <div className="flex items-center gap-3">
          {/* Google Auth / Switch Account Button */}
          <button
            onClick={() => setShowAuthModal(true)}
            className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-surface-card hover:bg-surface-hover border border-border text-slate-300 hover:text-white transition cursor-pointer"
            title="Google OAuth Sign-In & Student Credentials"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
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
            <span>{user?.auth_provider === 'google' ? 'Google Connected' : 'Google Auth'}</span>
          </button>

          {/* Notification Bell */}
          <div className="relative">
            <button
              onClick={() => setShowNotifs(!showNotifs)}
              className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-slate-300 hover:text-white transition relative cursor-pointer"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent-rose text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-bounce">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifs && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl glass-panel p-4 shadow-2xl border border-border/80 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-brand-400" />
                    <h4 className="font-semibold text-sm">Match Alerts & Notifications</h4>
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 cursor-pointer"
                    >
                      <CheckCheck className="w-3.5 h-3.5" /> Mark read
                    </button>
                  )}
                </div>

                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {notifications.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-6">No notifications yet</p>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        onClick={() => {
                          api.markNotificationRead(n.id);
                          setShowNotifs(false);
                          setActiveTab('matches');
                        }}
                        className={`p-3 rounded-xl cursor-pointer transition text-left ${
                          n.is_read ? 'bg-surface-card/40 opacity-70' : 'bg-surface-hover/80 border border-brand-500/30'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-semibold text-white truncate">{n.title}</span>
                          {n.score && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30">
                              {n.score}%
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">{n.message}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Pill & Account Menu */}
          <div className="relative">
            <button 
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-3 pl-2.5 pr-3.5 py-1.5 rounded-2xl bg-surface-card hover:bg-surface-hover border border-border cursor-pointer transition"
            >
              <img 
                src={user?.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.email || 'vishal'}`}
                alt="Avatar"
                className="w-8 h-8 rounded-xl object-cover bg-surface border border-border/80"
              />
              <div className="text-left hidden sm:block">
                <div className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                  <span>{profile?.full_name || user?.full_name || 'Vishal Sharma'}</span>
                  {profile?.cgpa && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-500/20 text-brand-300 font-bold border border-brand-500/30">
                      {profile.cgpa}
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1 truncate max-w-[140px]">
                  <GraduationCap className="w-3 h-3 text-brand-400 shrink-0" />
                  <span className="truncate">{profile?.college_name || 'IIT Delhi'}</span>
                </div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl glass-panel p-3 shadow-2xl border border-border/80 z-50 animate-in fade-in slide-in-from-top-2 duration-200 space-y-2 text-left">
                <div className="p-2 rounded-xl bg-surface border border-border/60">
                  <span className="text-[11px] text-slate-400 block">Signed in as</span>
                  <span className="text-xs font-bold text-white truncate block">{user?.email || profile?.email || 'vishal.aiml@example.com'}</span>
                  <span className="text-[10px] text-brand-400 font-medium">{user?.auth_provider === 'google' ? 'Google Authenticated' : 'Local Account'}</span>
                </div>

                <div className="space-y-1">
                  <button
                    onClick={() => { setShowUserMenu(false); setActiveTab('profile'); }}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold text-slate-200 hover:text-white hover:bg-surface-hover transition flex items-center gap-2 cursor-pointer text-left"
                  >
                    <User className="w-4 h-4 text-brand-400" />
                    <span>Candidate Profile & Studio</span>
                  </button>

                  <button
                    onClick={() => { setShowUserMenu(false); setShowAuthModal(true); }}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold text-slate-200 hover:text-white hover:bg-surface-hover transition flex items-center gap-2 cursor-pointer text-left"
                  >
                    <LogIn className="w-4 h-4 text-accent-cyan" />
                    <span>Switch Account / Google OAuth</span>
                  </button>

                  <button
                    onClick={async () => {
                      setShowUserMenu(false);
                      await logout();
                    }}
                    className="w-full px-3 py-2 rounded-xl text-xs font-semibold text-accent-rose hover:bg-accent-rose/10 transition flex items-center gap-2 cursor-pointer text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </>
  );
}

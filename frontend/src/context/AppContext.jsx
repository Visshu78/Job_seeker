import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [stats, setStats] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [selectedMatch, setSelectedMatch] = useState(null); // for detail modal
  const [applyingJob, setApplyingJob] = useState(null); // for application studio modal
  const [loading, setLoading] = useState(true);

  const refreshUserData = async () => {
    try {
      const [u, p, pref, st, notifs] = await Promise.allSettled([
        api.getMe(),
        api.getProfile(),
        api.getPreferences(),
        api.getStats(),
        api.getNotifications()
      ]);

      if (u.status === 'fulfilled') setUser(u.value);
      if (p.status === 'fulfilled') setProfile(p.value);
      if (pref.status === 'fulfilled') setPreferences(pref.value);
      if (st.status === 'fulfilled') setStats(st.value);
      if (notifs.status === 'fulfilled') {
        setNotifications(notifs.value);
        setUnreadCount(notifs.value.filter(n => !n.is_read).length);
      }
    } catch (err) {
      console.error('Error loading user data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUserData();
  }, []);

  const openMatchDetail = (match) => {
    setSelectedMatch(match);
  };

  const closeMatchDetail = () => {
    setSelectedMatch(null);
  };

  const openApplicationStudio = (job) => {
    setApplyingJob(job);
  };

  const closeApplicationStudio = () => {
    setApplyingJob(null);
  };

  const logout = async () => {
    api.logout();
    setUser(null);
    await refreshUserData();
  };

  return (
    <AppContext.Provider value={{
      activeTab,
      setActiveTab,
      user,
      profile,
      preferences,
      stats,
      notifications,
      unreadCount,
      selectedMatch,
      applyingJob,
      loading,
      refreshUserData,
      logout,
      openMatchDetail,
      closeMatchDetail,
      openApplicationStudio,
      closeApplicationStudio,
      setUser,
      setProfile,
      setPreferences
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}

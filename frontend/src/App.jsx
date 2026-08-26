import React from 'react';
import { useApp } from './context/AppContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { DashboardView } from './pages/DashboardView';
import { MatchesView } from './pages/MatchesView';
import { MatchDetailModal } from './pages/MatchDetailModal';
import { ApplicationStudioModal } from './pages/ApplicationStudioModal';
import { ApplicationTrackerView } from './pages/ApplicationTrackerView';
import { ProfileStudioView } from './pages/ProfileStudioView';
import { PreferencesView } from './pages/PreferencesView';
import { DiscoveryHubView } from './pages/DiscoveryHubView';

export function App() {
  const { activeTab, loading } = useApp();

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col selection:bg-brand-500/30 selection:text-brand-100">
      <Navbar />

      <div className="flex-1 flex max-w-[1600px] w-full mx-auto">
        <Sidebar />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-full overflow-x-hidden">
          {activeTab === 'dashboard' && <DashboardView />}
          {activeTab === 'matches' && <MatchesView />}
          {activeTab === 'applications' && <ApplicationTrackerView />}
          {activeTab === 'profile' && <ProfileStudioView />}
          {activeTab === 'preferences' && <PreferencesView />}
          {activeTab === 'discovery' && <DiscoveryHubView />}
        </main>
      </div>

      {/* Modals */}
      <MatchDetailModal />
      <ApplicationStudioModal />
    </div>
  );
}
export default App;

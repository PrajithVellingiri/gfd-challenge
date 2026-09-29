import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import CitizenPortal from './pages/CitizenPortal';
import CitizenRequestHistory from './components/CitizenRequestHistory';

function MainApp() {
  const { user, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('submit');

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
        Loading citizen services...
      </div>
    );
  }

  if (!user) {
    return (
      <div>
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
        <AuthModal />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main style={{ flex: 1, padding: '1rem 0 3rem 0' }}>
        {activeTab === 'submit' ? (
          <CitizenPortal onViewHistory={() => setActiveTab('history')} />
        ) : (
          <CitizenRequestHistory onNewRequest={() => setActiveTab('submit')} />
        )}
      </main>
      <footer style={{ borderTop: '1px solid #e2e8f0', padding: '1.5rem', textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8', backgroundColor: '#ffffff' }}>
        GFD Challenge — AI for Digital Public Infrastructure & Governance (Phase 3 Citizen Submission)
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

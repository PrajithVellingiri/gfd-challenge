import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Building2, User, LogOut, PlusCircle, History } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, signOut } = useAuth();

  return (
    <header style={{ backgroundColor: '#ffffff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 10 }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.875rem 1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ backgroundColor: '#2563eb', color: '#ffffff', padding: '0.5rem', borderRadius: '8px', display: 'flex' }}>
            <Building2 size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', lineHeight: 1.2 }}>GFD Citizen Portal</h1>
            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>Digital Public Infrastructure & Grievances</span>
          </div>
        </div>

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <nav style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className={`btn ${activeTab === 'submit' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveTab('submit')}
                style={{ padding: '0.45rem 0.875rem', fontSize: '0.8125rem' }}
              >
                <PlusCircle size={16} />
                <span>New Request</span>
              </button>
              <button
                className={`btn ${activeTab === 'history' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveTab('history')}
                style={{ padding: '0.45rem 0.875rem', fontSize: '0.8125rem' }}
              >
                <History size={16} />
                <span>My Submissions</span>
              </button>
            </nav>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', paddingLeft: '0.75rem', borderLeft: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem', color: '#475569' }}>
                <User size={16} />
                <span style={{ fontWeight: 600 }}>{user.name || user.email}</span>
              </div>
              <button
                onClick={signOut}
                title="Sign out"
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0.25rem', display: 'flex' }}
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

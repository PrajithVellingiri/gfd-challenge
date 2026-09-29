import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchCitizenRequests } from '../services/api';
import { Image, Mic, MapPin, Calendar, Clock, RefreshCw, AlertCircle } from 'lucide-react';

export default function CitizenRequestHistory({ onNewRequest }) {
  const { user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadRequests = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCitizenRequests(user.id);
      setRequests(data);
    } catch (err) {
      setError(err.message || 'Failed to load submissions.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
  }, [user]);

  const formatDate = (isoString) => {
    if (!isoString) return 'Recent';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  };

  const getUrgencyBadgeClass = (urgency) => {
    switch (urgency?.toLowerCase()) {
      case 'critical': return 'badge-critical';
      case 'high': return 'badge-high';
      case 'medium': return 'badge-medium';
      default: return 'badge-low';
    }
  };

  return (
    <div className="container" style={{ maxWidth: '800px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>My Grievance Submissions</h2>
          <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>Track status of your submitted infrastructure requests</p>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={loadRequests}
          disabled={loading}
          style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#b91c1c', backgroundColor: '#fee2e2' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading && requests.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
          Loading your submission history...
        </div>
      )}

      {!loading && requests.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
          <p style={{ color: '#64748b', marginBottom: '1rem' }}>You have not submitted any development requests yet.</p>
          <button type="button" className="btn btn-primary" onClick={onNewRequest}>
            Submit Your First Request
          </button>
        </div>
      )}

      {requests.map((req) => (
        <div key={req.id} className="card" style={{ padding: '1.25rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.875rem', color: '#2563eb' }}>
                REQ-{req.id.slice(0, 8).toUpperCase()}
              </span>
              <span className={`badge ${getUrgencyBadgeClass(req.urgency)}`}>
                {req.urgency}
              </span>
            </div>
            <span className="badge badge-status">
              {req.status}
            </span>
          </div>

          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', textTransform: 'capitalize', marginBottom: '0.375rem' }}>
            {req.category}
          </div>

          <p style={{ fontSize: '0.875rem', color: '#334155', marginBottom: '0.75rem', whiteSpace: 'pre-wrap' }}>
            {req.description}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.75rem', color: '#64748b', borderTop: '1px solid #f1f5f9', paddingTop: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Calendar size={13} />
                {formatDate(req.created_at)}
              </span>

              {(req.district_name || req.location_name) && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <MapPin size={13} />
                  {req.district_name || req.location_name}
                </span>
              )}
            </div>

            {/* Media attachments */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {req.image_path && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#0369a1', backgroundColor: '#e0f2fe', padding: '0.125rem 0.375rem', borderRadius: '4px' }}>
                  <Image size={12} />
                  <span>Photo</span>
                </span>
              )}
              {req.audio_path && (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#7c3aed', backgroundColor: '#f3e8ff', padding: '0.125rem 0.375rem', borderRadius: '4px' }}>
                  <Mic size={12} />
                  <span>Voice</span>
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

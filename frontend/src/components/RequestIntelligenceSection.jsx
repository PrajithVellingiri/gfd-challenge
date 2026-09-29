import React, { useState, useEffect } from 'react';
import { fetchSimilarRequests, fetchDuplicateRequests, triggerRequestIntelligence } from '../services/api';
import { Network, Copy, Layers, TrendingUp, RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react';

export default function RequestIntelligenceSection({ requestId, userId, category, districtName }) {
  const [similarRequests, setSimilarRequests] = useState([]);
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'similar' | 'duplicates'

  const loadIntelligence = async () => {
    if (!requestId) return;
    setLoading(true);
    setError(null);
    try {
      const [similarData, dupData] = await Promise.all([
        fetchSimilarRequests(requestId, userId, 10).catch(() => []),
        fetchDuplicateRequests(requestId, userId).catch(() => [])
      ]);
      setSimilarRequests(similarData);
      setDuplicates(dupData);
    } catch (err) {
      setError('Unable to load relational intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntelligence();
  }, [requestId, userId]);

  const handleCompute = async () => {
    setLoading(true);
    setError(null);
    try {
      await triggerRequestIntelligence(requestId, userId);
      await loadIntelligence();
    } catch (err) {
      setError(err.message || 'Intelligence processing failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      marginTop: '0.75rem',
      backgroundColor: '#f1f5f9',
      border: '1px solid #cbd5e1',
      borderRadius: '8px',
      padding: '0.875rem',
      fontSize: '0.8125rem'
    }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Network size={16} color="#0284c7" />
          <span style={{ fontWeight: 600, color: '#0f172a' }}>
            Request Intelligence & Relational Network
          </span>
          <span style={{ fontSize: '0.7rem', color: '#0369a1', backgroundColor: '#e0f2fe', padding: '0.1rem 0.35rem', borderRadius: '4px', fontWeight: 500 }}>
            Phase 5
          </span>
        </div>

        <button
          type="button"
          onClick={handleCompute}
          disabled={loading}
          className="btn btn-secondary"
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
          title="Refresh similarity graph"
        >
          <RefreshCw size={12} className={loading ? 'spin' : ''} />
          <span>{loading ? 'Analyzing...' : 'Scan Relational Network'}</span>
        </button>
      </div>

      {error && (
        <div style={{ marginTop: '0.5rem', padding: '0.375rem 0.625rem', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '4px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <AlertCircle size={13} />
          <span>{error}</span>
        </div>
      )}

      {/* Intelligence Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem', marginTop: '0.625rem' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Similar Demands</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0369a1' }}>
            {similarRequests.length}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Co-related civic needs</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Duplicate Group</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: duplicates.length > 0 ? '#b45309' : '#16a34a' }}>
            {duplicates.length > 0 ? `${duplicates.length} Near-Duplicates` : 'Unique Request'}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Locality-verified</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Domain Cluster</div>
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {category ? `${category} Demands` : 'Civic Cluster'}
          </div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>{districtName || 'District Level'}</div>
        </div>
      </div>

      {/* Similar Requests Anonymized Listing */}
      {similarRequests.length > 0 && (
        <div style={{ marginTop: '0.625rem', backgroundColor: '#ffffff', padding: '0.625rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
              Top Similar Requests in District
            </span>
            <span style={{ fontSize: '0.65rem', color: '#16a34a', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <ShieldCheck size={11} />
              <span>Privacy Anonymized</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
            {similarRequests.slice(0, 3).map((item, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.35rem 0.5rem',
                  backgroundColor: '#f8fafc',
                  borderRadius: '4px',
                  border: '1px solid #f1f5f9',
                  fontSize: '0.75rem'
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: '#1e293b' }}>
                    {item.sub_category || item.category || 'Infrastructure Grievance'}
                  </span>
                  <span style={{ marginLeft: '0.5rem', color: '#64748b', fontSize: '0.7rem' }}>
                    REQ-{item.request_id.slice(0, 6).toUpperCase()}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <span style={{
                    backgroundColor: item.similarity_score >= 0.90 ? '#fef3c7' : '#e0f2fe',
                    color: item.similarity_score >= 0.90 ? '#92400e' : '#0369a1',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 600
                  }}>
                    {(item.similarity_score * 100).toFixed(0)}% match
                  </span>
                  <span style={{
                    textTransform: 'capitalize',
                    fontSize: '0.65rem',
                    color: item.relationship_type === 'duplicate' ? '#b45309' : '#475569'
                  }}>
                    {item.relationship_type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Privacy Guarantee Note */}
      <div style={{ marginTop: '0.5rem', fontSize: '0.65rem', color: '#64748b', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
        <span>Aggregated intelligence does not expose personal names, contact info, or private text.</span>
      </div>
    </div>
  );
}

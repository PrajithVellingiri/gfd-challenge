import React from 'react';
import { CheckCircle, PlusCircle, History, Copy, Check } from 'lucide-react';

export default function SubmissionSuccess({ result, onReset, onViewHistory }) {
  const [copied, setCopied] = React.useState(false);

  const copyRequestId = () => {
    if (result?.request_id) {
      navigator.clipboard.writeText(result.request_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="card" style={{ textAlign: 'center', padding: '2.5rem 1.5rem', maxWidth: '600px', margin: '2rem auto' }}>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        backgroundColor: '#dcfce7',
        color: '#16a34a',
        marginBottom: '1rem'
      }}>
        <CheckCircle size={36} />
      </div>

      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
        Request Submitted Successfully
      </h2>
      <p style={{ color: '#64748b', fontSize: '0.9375rem', marginBottom: '1.5rem' }}>
        Your development request has been recorded in the Digital Public Infrastructure system.
      </p>

      {/* Request ID Display */}
      <div style={{
        backgroundColor: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.5rem'
      }}>
        <div style={{ textAlign: 'left' }}>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 600, color: '#64748b' }}>
            Request ID
          </span>
          <div style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '1rem', color: '#1e293b' }}>
            {result?.request_id}
          </div>
          {result?.district_name && (
            <div style={{ fontSize: '0.75rem', color: '#2563eb', marginTop: '0.25rem' }}>
              Resolved District: <strong>{result.district_name}</strong>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={copyRequestId}
          className="btn btn-secondary"
          style={{ padding: '0.375rem 0.625rem', fontSize: '0.75rem' }}
          title="Copy Request ID"
        >
          {copied ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onReset}
        >
          <PlusCircle size={16} />
          <span>Submit Another Request</span>
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={onViewHistory}
        >
          <History size={16} />
          <span>View Request History</span>
        </button>
      </div>
    </div>
  );
}

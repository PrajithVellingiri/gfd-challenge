import React, { useState, useEffect } from 'react';
import { triggerAIAnalysis, fetchAIAnalysis } from '../services/api';
import { Sparkles, Languages, Tag, AlertTriangle, FileText, CheckCircle2, XCircle, RefreshCw, Eye, Mic } from 'lucide-react';

export default function AIAnalysisCard({ requestId, userId, initialAnalysis = null }) {
  const [analysis, setAnalysis] = useState(initialAnalysis);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (initialAnalysis) {
      setAnalysis(initialAnalysis);
    } else if (requestId) {
      // Try fetching existing analysis quietly
      fetchAIAnalysis(requestId, userId)
        .then((data) => {
          if (data) {
            setAnalysis(data);
          }
        })
        .catch(() => {
          // No existing analysis, ignore
        });
    }
  }, [requestId, userId, initialAnalysis]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await triggerAIAnalysis(requestId, userId);
      setAnalysis(data);
      setExpanded(true);
    } catch (err) {
      setError(err.message || 'Failed to analyze request with AI');
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyBadge = (urgency) => {
    const u = urgency?.toLowerCase();
    if (u === 'critical') return { bg: '#fee2e2', color: '#991b1b', text: 'Critical' };
    if (u === 'high') return { bg: '#ffedd5', color: '#9a3412', text: 'High' };
    if (u === 'medium') return { bg: '#fef3c7', color: '#92400e', text: 'Medium' };
    return { bg: '#f1f5f9', color: '#475569', text: 'Low' };
  };

  return (
    <div style={{
      marginTop: '0.875rem',
      backgroundColor: '#f8fafc',
      border: '1px solid #e2e8f0',
      borderRadius: '8px',
      padding: '0.875rem',
      fontSize: '0.8125rem'
    }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={16} color="#4f46e5" />
          <span style={{ fontWeight: 600, color: '#1e293b' }}>
            Multimodal AI Intelligence
          </span>
          <span style={{ fontSize: '0.7rem', color: '#64748b', backgroundColor: '#e2e8f0', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>
            {analysis?.prompt_version || 'Gemini 1.5'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {!analysis && !loading && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleAnalyze}
              style={{ padding: '0.25rem 0.625rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              <Sparkles size={13} color="#4f46e5" />
              <span>Analyze with Gemini</span>
            </button>
          )}

          {analysis && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              style={{
                background: 'none',
                border: 'none',
                color: '#2563eb',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '0.25rem 0.5rem'
              }}
            >
              {expanded ? 'Collapse Insights' : 'View AI Insights'}
            </button>
          )}

          {analysis && (
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={loading}
              title="Re-run analysis"
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                padding: '0.25rem'
              }}
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
            </button>
          )}
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ padding: '0.75rem 0', color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <RefreshCw size={14} className="spin" />
          <span>Gemini Multimodal AI is processing text, speech, and imagery...</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#fee2e2', color: '#991b1b', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <XCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* Failed analysis status */}
      {analysis && analysis.processing_status === 'failed' && (
        <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: '#fef3c7', color: '#92400e', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <AlertTriangle size={14} />
          <span>Analysis failed: {analysis.error_message || 'Could not process submission.'}</span>
        </div>
      )}

      {/* Expanded Analysis Details */}
      {analysis && analysis.processing_status === 'completed' && expanded && (
        <div style={{ marginTop: '0.75rem', borderTop: '1px solid #e2e8f0', paddingTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {/* Summary */}
          {analysis.summary && (
            <div style={{ backgroundColor: '#ffffff', padding: '0.625rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', fontWeight: 700, color: '#64748b', marginBottom: '0.25rem' }}>
                Executive AI Summary
              </div>
              <p style={{ margin: 0, color: '#1e293b', fontWeight: 500, lineHeight: 1.4 }}>
                {analysis.summary}
              </p>
            </div>
          )}

          {/* Classification & Urgency Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.5rem' }}>
            <div style={{ backgroundColor: '#ffffff', padding: '0.5rem 0.625rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Canonical Category</div>
              <div style={{ fontWeight: 600, color: '#0f172a' }}>{analysis.category || 'Other'}</div>
              {analysis.sub_category && (
                <div style={{ fontSize: '0.75rem', color: '#2563eb', marginTop: '0.125rem' }}>
                  {analysis.sub_category}
                </div>
              )}
            </div>

            <div style={{ backgroundColor: '#ffffff', padding: '0.5rem 0.625rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Assessed Urgency</div>
              {(() => {
                const badge = getUrgencyBadge(analysis.urgency);
                return (
                  <span style={{
                    display: 'inline-block',
                    marginTop: '0.25rem',
                    backgroundColor: badge.bg,
                    color: badge.color,
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    fontWeight: 600
                  }}>
                    {badge.text}
                  </span>
                );
              })()}
            </div>

            <div style={{ backgroundColor: '#ffffff', padding: '0.5rem 0.625rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Language</div>
              <div style={{ fontWeight: 600, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Languages size={13} color="#64748b" />
                <span>{analysis.detected_language || 'English'}</span>
              </div>
            </div>
          </div>

          {/* Translation if detected non-English */}
          {analysis.translated_text && analysis.detected_language && analysis.detected_language.toLowerCase() !== 'english' && (
            <div style={{ backgroundColor: '#eff6ff', padding: '0.625rem', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '0.7rem', color: '#1d4ed8', fontWeight: 600, marginBottom: '0.25rem' }}>
                English Translation (Preserved Nuances)
              </div>
              <p style={{ margin: 0, color: '#1e3a8a', fontStyle: 'italic' }}>
                "{analysis.translated_text}"
              </p>
            </div>
          )}

          {/* Audio Transcript */}
          {analysis.transcript && (
            <div style={{ backgroundColor: '#faf5ff', padding: '0.625rem', borderRadius: '6px', border: '1px solid #e9d5ff' }}>
              <div style={{ fontSize: '0.7rem', color: '#7e22ce', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.25rem' }}>
                <Mic size={13} />
                <span>Audio Recording Transcript</span>
              </div>
              <p style={{ margin: 0, color: '#581c87', fontStyle: 'italic' }}>
                "{analysis.transcript}"
              </p>
            </div>
          )}

          {/* Image Analysis Observations */}
          {analysis.image_analysis && analysis.image_analysis.observations && analysis.image_analysis.observations.length > 0 && (
            <div style={{ backgroundColor: '#f0fdf4', padding: '0.625rem', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '0.7rem', color: '#15803d', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.25rem' }}>
                <Eye size={13} />
                <span>Visual Inspection ({analysis.image_analysis.infrastructure_type || 'Infrastructure'})</span>
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#166534' }}>
                {analysis.image_analysis.observations.map((obs, idx) => (
                  <li key={idx} style={{ marginBottom: '0.125rem' }}>{obs}</li>
                ))}
              </ul>
              {analysis.image_analysis.summary && (
                <div style={{ fontSize: '0.75rem', color: '#14532d', marginTop: '0.25rem', fontWeight: 500 }}>
                  Severity: {analysis.image_analysis.severity || 'Medium'} — {analysis.image_analysis.summary}
                </div>
              )}
            </div>
          )}

          {/* Keywords */}
          {analysis.keywords && analysis.keywords.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', flexWrap: 'wrap' }}>
              <Tag size={13} color="#64748b" />
              {analysis.keywords.map((kw, i) => (
                <span
                  key={i}
                  style={{
                    backgroundColor: '#e2e8f0',
                    color: '#334155',
                    fontSize: '0.7rem',
                    padding: '0.125rem 0.375rem',
                    borderRadius: '4px'
                  }}
                >
                  #{kw}
                </span>
              ))}
            </div>
          )}

          {/* Advisory banner */}
          <div style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic', borderTop: '1px dashed #cbd5e1', paddingTop: '0.375rem' }}>
            AI analysis provides automated decision-support triage for digital public infrastructure and does not replace official on-ground inspection.
          </div>
        </div>
      )}
    </div>
  );
}

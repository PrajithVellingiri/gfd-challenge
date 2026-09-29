import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Building2, User, Key, Mail, AlertCircle, ArrowRight } from 'lucide-react';

export default function AuthModal() {
  const { signIn, signUp, loginDemoCitizen } = useAuth();
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isSignUp) {
        if (!name.trim()) throw new Error('Please enter your full name.');
        await signUp(email, password, name);
      } else {
        await signIn(email, password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '440px', margin: '3rem auto', padding: '0 1rem' }}>
      <div className="card" style={{ padding: '2rem 1.75rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '52px',
            height: '52px',
            borderRadius: '12px',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            marginBottom: '0.75rem'
          }}>
            <Building2 size={28} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
            {isSignUp ? 'Citizen Registration' : 'Citizen Login'}
          </h2>
          <p style={{ fontSize: '0.8125rem', color: '#64748b' }}>
            Sign in to submit and track your local infrastructure grievances
          </p>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', backgroundColor: '#fee2e2', borderRadius: '8px', color: '#b91c1c', fontSize: '0.8125rem', marginBottom: '1rem' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isSignUp && (
            <div className="form-group">
              <label className="form-label" htmlFor="fullNameInput">Full Name</label>
              <div style={{ position: 'relative' }}>
                <input
                  id="fullNameInput"
                  type="text"
                  className="form-control"
                  placeholder="e.g. Ramesh Kumar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="emailInput">Email Address</label>
            <input
              id="emailInput"
              type="email"
              className="form-control"
              placeholder="citizen@example.gov.in"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="passwordInput">Password</label>
            <input
              id="passwordInput"
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: '1rem', padding: '0.625rem' }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : (isSignUp ? 'Create Citizen Account' : 'Sign In')}
          </button>
        </form>

        <div style={{ textAlign: 'center', margin: '0.75rem 0', position: 'relative' }}>
          <hr style={{ borderColor: '#e2e8f0' }} />
          <span style={{ position: 'absolute', top: '-10px', left: '50%', transform: 'translateX(-50%)', backgroundColor: '#ffffff', padding: '0 0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
            OR
          </span>
        </div>

        {/* Quick Demo Citizen Login */}
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => loginDemoCitizen('Citizen Ramesh', 'citizen.demo@dpi.gov.in')}
          style={{ width: '100%', marginBottom: '1rem', justifyContent: 'center' }}
        >
          <User size={16} color="#2563eb" />
          <span>Continue as Demo Citizen</span>
        </button>

        <div style={{ textAlign: 'center', fontSize: '0.8125rem', color: '#64748b' }}>
          {isSignUp ? (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setIsSignUp(false)}
                style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: 600, cursor: 'pointer', padding: 0 }}
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              New citizen?{' '}
              <button
                type="button"
                onClick={() => setIsSignUp(true)}
                style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: 600, cursor: 'pointer', padding: 0 }}
              >
                Register Here
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

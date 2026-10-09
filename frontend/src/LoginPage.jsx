import { useState } from 'react';
import { ArrowRight, Eye, EyeOff, LockKeyhole, MapPinned, ShieldCheck } from 'lucide-react';
import { loginOfficial } from './api.js';

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('official@roadsense.local');
  const [password, setPassword] = useState('RoadSense-Demo-2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const official = await loginOfficial({ username, password });
      onLogin(official);
    } catch (loginError) {
      setError(loginError.message.includes('401') ? 'Email or password was not recognized.' : loginError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-aside" aria-label="RoadSense information">
        <a className="brand login-brand" href="#login">
          <span className="brand-mark"><MapPinned size={20} strokeWidth={2.5} /></span>
          <span>roadsense<span className="brand-dot">.</span></span>
        </a>
        <div className="login-aside-copy">
          <span className="login-overline"><span /> MUNICIPAL ROAD OPERATIONS</span>
          <h1>Clear roads start with better decisions.</h1>
          <p>Review field reports, verify road conditions, and coordinate maintenance from one workspace.</p>
        </div>
        <div className="login-aside-footer"><ShieldCheck size={16} /> Restricted to authorized officials</div>
      </section>

      <section className="login-main" id="login">
        <div className="login-card">
          <div className="login-heading-icon"><LockKeyhole size={20} /></div>
          <p className="eyebrow">OFFICIAL ACCESS</p>
          <h2>Sign in to RoadSense</h2>
          <p className="login-subheading">Use your municipal account to continue.</p>

          <form className="login-form" onSubmit={submit}>
            <label className="login-field" htmlFor="official-username">
              Official email
              <input autoComplete="username" id="official-username" onChange={event => setUsername(event.target.value)} required type="email" value={username} />
            </label>
            <label className="login-field" htmlFor="official-password">
              Password
              <span className="password-input-wrap">
                <input autoComplete="current-password" id="official-password" onChange={event => setPassword(event.target.value)} required type={showPassword ? 'text' : 'password'} value={password} />
                <button aria-label={showPassword ? 'Hide password' : 'Show password'} className="password-toggle" onClick={() => setShowPassword(value => !value)} type="button">{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
              </span>
            </label>
            {error && <p className="login-error" role="alert">{error}</p>}
            <button className="login-submit" disabled={submitting} type="submit">
              <span>{submitting ? 'Signing in…' : 'Sign in securely'}</span>
              {!submitting && <ArrowRight size={17} />}
            </button>
          </form>

          <div className="demo-credentials"><span className="demo-tag">LOCAL DEMO</span><span>Credentials are prefilled for this prototype. Configure official credentials before deployment.</span></div>
        </div>
        <footer className="login-footer">RoadSense · Incident prioritization workspace <span>Prototype build</span></footer>
      </section>
    </main>
  );
}
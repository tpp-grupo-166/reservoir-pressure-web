import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { AuthLayout } from '../components/AuthLayout';
import { PasswordInput } from '../components/PasswordInput';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    navigate('/dashboard');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      pageTitle="Iniciar sesión"
      pageSubtitle="Accede para analizar datos y generar predicciones."
      footerText="¿No tienes una cuenta?"
      footerLinkLabel="CREAR CUENTA"
      footerLinkTo="/register"
    >
      <form onSubmit={handleSubmit} className="auth-form">
        {/* Campo: CORREO ELECTRÓNICO */}
        <div className="auth-field">
          <label htmlFor="email" className="auth-field__label">CORREO ELECTRÓNICO</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@company.com"
            required
            disabled={loading}
            className="auth-field__input"
          />
        </div>

        {/* Campo: CONTRASEÑA con toggle */}
        <div className="auth-field">
          <label htmlFor="password" className="auth-field__label">CONTRASEÑA</label>
          <PasswordInput
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            disabled={loading}
          />
        </div>

        {/* Error */}
        {error && <div className="auth-error">{error}</div>}

        {/* Submit */}
        <button type="submit" disabled={loading} className="auth-submit-btn">
          <span>{loading ? 'INICIANDO SESIÓN…' : 'INICIAR SESIÓN'}</span>
          <svg fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </form>
    </AuthLayout>
  );
}

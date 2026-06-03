import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { AuthLayout } from '../components/AuthLayout';
import { PasswordInput } from '../components/PasswordInput';
import { validateRegistration, type ValidationError } from '../utils/validation';

export function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    navigate('/dashboard');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    // Client-side validation
    const validation = validateRegistration(email, password);
    if (!validation.isValid) {
      const errors: Record<string, string> = {};
      validation.errors.forEach((err: ValidationError) => {
        errors[err.field] = err.message;
      });
      setFieldErrors(errors);
      return;
    }

    setLoading(true);

    try {
      await register(email, password);
      navigate('/login');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      // Check if it's an email already registered error
      if (errorMessage.toLowerCase().includes('email') || errorMessage.toLowerCase().includes('already')) {
        setError('El email ya está en uso');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      pageTitle="Crear una cuenta"
      pageSubtitle="Únete para analizar datos y generar predicciones."
      footerText="¿Ya tienes una cuenta?"
      footerLinkLabel="INICIAR SESIÓN"
      footerLinkTo="/login"
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
            disabled={loading}
            className={`auth-field__input ${fieldErrors.email ? 'auth-field__input--error' : ''}`}
          />
          {fieldErrors.email && <div className="auth-field__error">{fieldErrors.email}</div>}
        </div>

        {/* Campo: CONTRASEÑA con toggle */}
        <div className="auth-field">
          <label htmlFor="password" className="auth-field__label">CONTRASEÑA</label>
          <PasswordInput
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={loading}
            className={fieldErrors.password ? 'auth-field__input--error' : ''}
          />
          {fieldErrors.password && <div className="auth-field__error">{fieldErrors.password}</div>}
        </div>

        {/* General Error */}
        {error && <div className="auth-error">{error}</div>}

        {/* Submit */}
        <button type="submit" disabled={loading} className="auth-submit-btn">
          <span>{loading ? 'CREANDO CUENTA…' : 'CREAR CUENTA'}</span>
          <svg fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </form>
    </AuthLayout>
  );
}

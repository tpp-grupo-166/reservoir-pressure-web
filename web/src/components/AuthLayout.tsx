import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ThemeToggle } from './ThemeToggle';

interface AuthLayoutProps {
  pageTitle: string;
  pageSubtitle: string;
  children: ReactNode;
  footerText: string;
  footerLinkLabel: string;
  footerLinkTo: string;
}

export function AuthLayout({
  pageTitle,
  pageSubtitle,
  children,
  footerText,
  footerLinkLabel,
  footerLinkTo,
}: AuthLayoutProps) {
  return (
    <div className="auth-page">
      <ThemeToggle className="theme-toggle--floating" />
      <main className="auth-card">
        <header className="auth-card__header">
          <div className="auth-card__logo">
            <svg className="w-8 h-8" fill="none" stroke="white" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="auth-card__brand">PressureAnalytics</h1>
          <h2 className="auth-card__title">{pageTitle}</h2>
          <p className="auth-card__subtitle">{pageSubtitle}</p>
        </header>

        {children}

        <div className="auth-divider">
          <div className="auth-divider__line"></div>
          <span className="auth-divider__label">O</span>
          <div className="auth-divider__line"></div>
        </div>

        <p className="auth-footer-link">
          {footerText} <Link to={footerLinkTo}>{footerLinkLabel}</Link>
        </p>
      </main>

      <footer className="auth-page-footer">
        <div className="auth-page-footer__links">
          <a href="#">Política de Privacidad</a>
          <a href="#">Términos de Servicio</a>
          <a href="#">Soporte</a>
        </div>
        <p>© 2024 PressureAnalytics. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}

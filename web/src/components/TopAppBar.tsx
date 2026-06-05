import { ThemeToggle } from './ThemeToggle';

export function TopAppBar() {
  return (
    <header className="top-app-bar">
      <div className="top-app-bar__brand">
        <span
          className="material-symbols-outlined top-app-bar__brand-icon"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          waves
        </span>
        <span className="top-app-bar__brand-name">
          PressureAnalytics
        </span>
      </div>

      <div className="top-app-bar__actions">
        <ThemeToggle />
      </div>
    </header>
  );
}
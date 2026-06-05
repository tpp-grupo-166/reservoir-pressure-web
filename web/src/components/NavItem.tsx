interface NavItemProps {
  icon: string;
  label: string;
  active?: boolean;
  danger?: boolean;
  filled?: boolean;
  onClick?: () => void;
}

export function NavItem({ icon, label, active = false, danger = false, filled = false, onClick }: NavItemProps) {
  const classes = [
    'nav-item',
    active ? 'nav-item--active' : '',
    danger ? 'nav-item--danger' : '',
  ].filter(Boolean).join(' ');

  return (
    <button className={classes} onClick={onClick}>
      <span
        className="material-symbols-outlined nav-item__icon"
        style={filled ? { fontVariationSettings: "'FILL' 1" } : undefined}
      >
        {icon}
      </span>
      <span>{label}</span>
    </button>
  );
}

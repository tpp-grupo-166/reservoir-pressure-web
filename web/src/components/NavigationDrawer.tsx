import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { NavItem } from './NavItem';

interface NavigationDrawerProps {
  activeStep?: number; // 0 = Historia, 1 = Reservorio, 2 = PVT
}

const STEPS = [
  { icon: 'query_stats',              label: 'Historia de producción'      },
  { icon: 'settings_input_component', label: 'Propiedades del reservorio'  },
  { icon: 'science',                  label: 'Tabla PVT'                   },
];

export function NavigationDrawer({ activeStep = 0 }: NavigationDrawerProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="nav-drawer">
      <p className="nav-drawer__title">Predicción</p>

      <nav>
        {/* Sección "Datos" */}
        <div className="nav-drawer__section">
          <p className="nav-drawer__section-label">Datos</p>
          <div className="nav-drawer__items">
            {STEPS.map((step, i) => (
              <NavItem
                key={step.label}
                icon={step.icon}
                label={step.label}
                active={activeStep === i}
                filled={activeStep === i}
              />
            ))}
          </div>
        </div>

        {/* Sección "Análisis" */}
        <div className="nav-drawer__section">
          <p className="nav-drawer__section-label">Análisis</p>
          <div className="nav-drawer__items">
            <NavItem icon="history" label="Historial de predicciones" />
          </div>
        </div>
      </nav>

      <div className="nav-drawer__footer">
        <NavItem
          icon="logout"
          label="Cerrar sesión"
          danger
          onClick={handleLogout}
        />
      </div>
    </aside>
  );
}

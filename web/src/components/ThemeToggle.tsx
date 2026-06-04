import { useTheme } from "../hooks/useTheme";

interface Props {
  /** Clase extra para posicionar (ej. `theme-toggle--floating` en las páginas de auth). */
  className?: string;
}

/** Botón ☀/🌙 que alterna el tema claro/oscuro. */
export function ThemeToggle({ className = "" }: Props) {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      className={`theme-toggle ${className}`.trim()}
      title={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      aria-label="Cambiar tema"
    >
      {theme === "dark" ? "☀" : "🌙"}
    </button>
  );
}

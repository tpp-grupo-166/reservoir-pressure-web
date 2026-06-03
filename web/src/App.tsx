import { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import type { PredictResponse } from "./types";
import { Wizard } from "./components/Wizard";
import { TrajectoryChart } from "./components/TrajectoryChart";
import { VrrChart } from "./components/VrrChart";
import { DriversChart } from "./components/DriversChart";
import { ExplainPanel } from "./components/ExplainPanel";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { useAuth } from "./hooks/useAuth";

function Dashboard() {
  const [result, setResult] = useState<PredictResponse | null>(null);
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app">
      <header className="app__header">
        <div className="header-content">
          <div>
            <h1>Estimador de presión de reservorio</h1>
            <p>Cargá la historia de producción y la tabla PVT para estimar la trayectoria de presión.</p>
          </div>
          <div className="user-info">
            <span>{user?.email}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
      </header>

      {!result ? (
        <Wizard onResult={setResult} />
      ) : (
        <section className="result">
          <TrajectoryChart
            prediction={result.prediction}
            baseline={result.baseline}
            bubblePoint={result.bubble_point_psi}
          />
          <VrrChart tiempoDias={result.prediction.tiempo_dias} vrr={result.vrr} />
          <DriversChart tiempoDias={result.prediction.tiempo_dias} drivers={result.drivers} />
          <ExplainPanel explainability={result.explainability} modelInfo={result.model_info} />
          <button className="result__again" onClick={() => setResult(null)}>
            ← Nueva estimación
          </button>
        </section>
      )}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

import { Routes, Route } from 'react-router-dom';
import { Layout } from './layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Predictions } from './pages/Predictions';
import { Wheeling } from './pages/Wheeling';
import { Backtesting } from './pages/Backtesting';
import { Betting } from './pages/Betting';
import { BettingHistory } from './pages/BettingHistory';
import { Data } from './pages/Data';
import { Settings } from './pages/Settings';
import { ResultadosLaPrimitiva, ResultadosEuromillones, ResultadosElGordo } from './pages/resultados';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="resultados/la-primitiva" element={<ResultadosLaPrimitiva />} />
        <Route path="resultados/euromillones" element={<ResultadosEuromillones />} />
        <Route path="resultados/el-gordo" element={<ResultadosElGordo />} />
        <Route path="predictions" element={<Predictions />} />
        <Route path="wheeling" element={<Wheeling />} />
        <Route path="backtesting" element={<Backtesting />} />
        <Route path="betting" element={<Betting />} />
        <Route path="betting/history" element={<BettingHistory />} />
        <Route path="data" element={<Data />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;

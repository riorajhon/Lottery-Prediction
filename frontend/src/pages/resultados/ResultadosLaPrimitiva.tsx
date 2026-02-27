import { useState } from 'react';
import { ResultadosPage } from './ResultadosPage';
import { LaPrimitivaApuestasPanel } from './LaPrimitivaApuestasPanel';

type LaPrimitivaTab = 'results' | 'grafico';

export function ResultadosLaPrimitiva() {
  const [activeTab, setActiveTab] = useState<LaPrimitivaTab>('results');

  return (
    <div className="resultados-euromillones-layout">
      <div className="resultados-tabs" role="tablist" aria-label="La Primitiva">
        <button
          type="button"
          className={`resultados-tab ${activeTab === 'results' ? 'resultados-tab--active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'results'}
          onClick={() => setActiveTab('results')}
        >
          Resultados
        </button>
        <button
          type="button"
          className={`resultados-tab ${activeTab === 'grafico' ? 'resultados-tab--active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'grafico'}
          onClick={() => setActiveTab('grafico')}
        >
          Gráfico
        </button>
      </div>

      <div className="resultados-tab-content">
        {activeTab === 'results' && <ResultadosPage lottery="la-primitiva" />}
        {activeTab === 'grafico' && (
          <div className="resultados-euromillones-features">
            <LaPrimitivaApuestasPanel />
          </div>
        )}
      </div>
    </div>
  );
}

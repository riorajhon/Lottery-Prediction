import { useState } from 'react';
import { ResultadosPage } from './ResultadosPage';
import { EuromillonesFeaturesPanel } from './EuromillonesFeaturesPanel';

type EuromillonesTab = 'results' | 'prediction';

export function ResultadosEuromillones() {
  const [activeTab, setActiveTab] = useState<EuromillonesTab>('results');

  return (
    <div className="resultados-euromillones-layout">
      <div className="resultados-tabs" role="tablist" aria-label="Euromillones">
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
          className={`resultados-tab ${activeTab === 'prediction' ? 'resultados-tab--active' : ''}`}
          role="tab"
          aria-selected={activeTab === 'prediction'}
          onClick={() => setActiveTab('prediction')}
        >
          Predicción
        </button>
      </div>

      <div className="resultados-tab-content">
        {activeTab === 'results' ? (
          <ResultadosPage lottery="euromillones" />
        ) : (
          <div className="resultados-euromillones-features">
            <EuromillonesFeaturesPanel />
          </div>
        )}
      </div>
    </div>
  );
}

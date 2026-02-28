import { useState } from 'react';
import { ResultadosPage } from './ResultadosPage';
import { ElGordoApuestasPanel } from './ElGordoApuestasPanel';
import { ElGordoFeaturesPanel } from './ElGordoFeaturesPanel';

type ElGordoTab = 'results' | 'prediction' | 'grafico';

export function ResultadosElGordo() {
  const [activeTab, setActiveTab] = useState<ElGordoTab>('results');

  return (
    <div className="resultados-euromillones-layout">
      <div className="resultados-tabs" role="tablist" aria-label="El Gordo">
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
        {activeTab === 'results' && <ResultadosPage lottery="el-gordo" />}
        {activeTab === 'prediction' && (
          <div className="resultados-euromillones-features">
            <ElGordoFeaturesPanel />
          </div>
        )}
        {activeTab === 'grafico' && (
          <div className="resultados-euromillones-features">
            <ElGordoApuestasPanel />
          </div>
        )}
      </div>
    </div>
  );
}

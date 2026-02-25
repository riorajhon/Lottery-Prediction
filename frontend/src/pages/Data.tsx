import { MOCK_DATA_STATUS, MOCK_LOG_LINES } from '../mock/data';

export function Data() {
  return (
    <>
      <h1 className="page-title">Data status</h1>

      <div className="card" style={{ marginBottom: 'var(--space-lg)' }}>
        <p style={{ margin: '0 0 var(--space-md)' }}>
          Last run: 2025-02-24 00:02
        </p>
        <button type="button" disabled title="Backend not connected">Run now</button>
      </div>

      <div className="table-wrap" style={{ marginBottom: 'var(--space-lg)' }}>
        <table>
          <thead>
            <tr>
              <th>Lottery</th>
              <th>Last update</th>
              <th>Status</th>
              <th>Draws in DB</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_DATA_STATUS.map((row) => (
              <tr key={row.lottery}>
                <td>{row.lottery}</td>
                <td>{row.lastUpdate}</td>
                <td><span className={`status-${row.status}`}>✓ OK</span></td>
                <td>{row.drawsCount.toLocaleString()}</td>
                <td><button type="button">Details</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ margin: '0 0 var(--space-md)', fontSize: '1rem' }}>Log (last 20 lines, placeholder)</h2>
        <pre style={{ margin: 0, fontSize: '0.85rem', overflow: 'auto', maxHeight: 300 }}>
          {MOCK_LOG_LINES.join('\n')}
        </pre>
      </div>
    </>
  );
}

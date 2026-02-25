import { useState } from 'react';
import { LOTTERIES } from '../mock/data';
import { MOCK_BETTING_HISTORY } from '../mock/data';

export function BettingHistory() {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [lottery, setLottery] = useState('');

  return (
    <>
      <h1 className="page-title">Betting history</h1>

      <div className="form-row" style={{ marginBottom: 'var(--space-lg)' }}>
        <label htmlFor="bh-from">From</label>
        <input id="bh-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        <label htmlFor="bh-to">To</label>
        <input id="bh-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        <label htmlFor="bh-lottery">Lottery</label>
        <select id="bh-lottery" value={lottery} onChange={(e) => setLottery(e.target.value)}>
          <option value="">All</option>
          {LOTTERIES.map((l) => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
        <button type="button">Apply</button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Lottery</th>
              <th>Numbers</th>
              <th>Amount</th>
              <th>Receipt</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_BETTING_HISTORY.map((row) => (
              <tr key={row.id}>
                <td>{row.date}</td>
                <td>{row.lottery}</td>
                <td>{row.numbers}</td>
                <td>{row.amount}</td>
                <td><button type="button">View</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ marginTop: 'var(--space-md)', color: 'var(--color-text-muted)' }}>Pagination</p>
    </>
  );
}

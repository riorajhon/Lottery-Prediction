export const LOTTERIES = [
  { id: 'euromillones', name: 'Euromillones' },
  { id: 'la-primitiva', name: 'La Primitiva' },
  { id: 'el-gordo', name: 'El Gordo' },
] as const;

export const MODELS = [
  'Random Forest',
  'LSTM',
  'Genetic',
  'Bayesian',
] as const;

export const WHEEL_TYPES = [
  'Full Wheel',
  'Abbreviated Wheel',
  'Balanced Wheel',
  'Key Number Wheel',
  'Random Wheel',
  'Guarantee Wheel',
] as const;

export interface Draw {
  id: string;
  date: string;
  lottery: string;
  mainNumbers: number[];
  starsOrBonus: number[];
  jackpot: string;
}

export const MOCK_DRAWS: Draw[] = [
  { id: '1', date: '2025-02-21', lottery: 'Euromillones', mainNumbers: [12, 18, 23, 31, 42], starsOrBonus: [2, 7], jackpot: '€45M' },
  { id: '2', date: '2025-02-18', lottery: 'La Primitiva', mainNumbers: [3, 9, 15, 22, 28, 41], starsOrBonus: [8], jackpot: '€2.1M' },
  { id: '3', date: '2025-02-14', lottery: 'Euromillones', mainNumbers: [5, 11, 19, 27, 38], starsOrBonus: [3, 9], jackpot: '€42M' },
  { id: '4', date: '2025-02-11', lottery: 'El Gordo', mainNumbers: [1, 7, 14, 21, 35], starsOrBonus: [], jackpot: '€4M' },
];

export interface DataStatusRow {
  lottery: string;
  lastUpdate: string;
  status: 'ok' | 'warning' | 'error';
  drawsCount: number;
}

export const MOCK_DATA_STATUS: DataStatusRow[] = [
  { lottery: 'Euromillones', lastUpdate: '24 Feb 00:05', status: 'ok', drawsCount: 1234 },
  { lottery: 'La Primitiva', lastUpdate: '24 Feb 00:06', status: 'ok', drawsCount: 2100 },
  { lottery: 'El Gordo', lastUpdate: '23 Feb 00:04', status: 'ok', drawsCount: 890 },
];

export const MOCK_LOG_LINES = [
  '[2025-02-24 00:02] Job started',
  '[2025-02-24 00:05] Euromillones: 1 new draw saved',
  '[2025-02-24 00:06] La Primitiva: 1 new draw saved',
  '[2025-02-24 00:07] El Gordo: no new draw',
  '[2025-02-24 00:07] Job completed',
];

export interface PendingBet {
  id: string;
  lottery: string;
  drawDate: string;
  line: number[];
  stars: number[];
  amount: string;
}

export const MOCK_PENDING_BETS: PendingBet[] = [
  { id: 'b1', lottery: 'Euromillones', drawDate: 'Fri 28 Feb', line: [1, 5, 12, 18, 23], stars: [2, 7], amount: '€2.50' },
  { id: 'b2', lottery: 'Euromillones', drawDate: 'Fri 28 Feb', line: [3, 9, 15, 22, 31], stars: [1, 8], amount: '€2.50' },
];

export interface BettingHistoryRow {
  id: string;
  date: string;
  lottery: string;
  numbers: string;
  amount: string;
}

export const MOCK_BETTING_HISTORY: BettingHistoryRow[] = [
  { id: 'h1', date: '21 Feb 25', lottery: 'Euromillones', numbers: '12 18 23 31 42 (2 7)', amount: '€2.50' },
  { id: 'h2', date: '18 Feb 25', lottery: 'La Primitiva', numbers: '3 9 15 22 28 41 (8)', amount: '€1.50' },
];

export const NEXT_DRAWS = [
  { lottery: 'Euromillones', day: 'Fri 28 Feb' },
  { lottery: 'La Primitiva', day: 'Sat 1 Mar' },
  { lottery: 'El Gordo', day: 'Sun 2 Mar' },
];

export const CALENDAR_EVENTS = [
  { title: 'Euromillones', start: '2025-02-28', allDay: true },
  { title: 'La Primitiva', start: '2025-03-01', allDay: true },
  { title: 'El Gordo', start: '2025-03-02', allDay: true },
  { title: 'Euromillones', start: '2025-03-04', allDay: true },
  { title: 'La Primitiva', start: '2025-03-08', allDay: true },
];

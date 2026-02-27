export interface EscrutinioRow {
  tipo?: string;
  categoria?: number;
  premio?: string;
  ganadores?: string;
  ganadores_eu?: string;
  agraciados_espana?: string;
}

export interface Draw {
  id_sorteo: string;
  fecha_sorteo: string;
  game_id: string;
  game_name: string;
  combinacion: string;
  combinacion_acta?: string | null;
  numbers?: number[];
  complementario?: number | null;
  reintegro?: number | null;
  joker_combinacion?: string | null;
  premio_bote: string;
  escrutinio?: EscrutinioRow[] | null;
  // Euromillones extra stats (if present)
  apuestas?: string | number | null;
  aquestas?: string | number | null;
  recaudacion?: string | number | null;
  recaudacion_europea?: string | number | null;
  premios?: string | number | null;
  escrutinio_millon?: EscrutinioRow[] | null;
}

export type LotterySlug = 'la-primitiva' | 'euromillones' | 'el-gordo';

export const LOTTERY_CONFIG: Record<LotterySlug, { name: string; title: string; theme: string }> = {
  'la-primitiva': { name: 'La Primitiva', title: 'LA PRIMITIVA', theme: 'la-primitiva' },
  'euromillones': { name: 'Euromillones', title: 'EUROMILLONES', theme: 'euromillones' },
  'el-gordo': { name: 'El Gordo', title: 'EL GORDO', theme: 'el-gordo' },
};

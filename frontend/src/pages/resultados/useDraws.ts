import { useState, useCallback, useEffect } from 'react';
import type { Draw } from './types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const PAGE_SIZE = 20;

export function useDraws(lottery: string) {
  const [fromInput, setFromInput] = useState('');
  const [toInput, setToInput] = useState('');
  const [draws, setDraws] = useState<Draw[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDraws = useCallback(async () => {
    if (!lottery) {
      setDraws([]);
      setTotal(0);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('lottery', lottery);
      if (fromInput) params.set('from_date', fromInput);
      if (toInput) params.set('to_date', toInput);
      params.set('limit', String(PAGE_SIZE));
      params.set('skip', String(skip));
      const res = await fetch(`${API_URL}/api/draws?${params}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail ?? res.statusText);
        setDraws([]);
        setTotal(0);
        return;
      }
      setDraws(data.draws ?? []);
      setTotal(data.total ?? 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load draws');
      setDraws([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [lottery, fromInput, toInput, skip]);

  useEffect(() => {
    fetchDraws();
  }, [fetchDraws]);

  const search = useCallback(() => {
    setSkip(0);
  }, []);

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const currentPage = Math.floor(skip / PAGE_SIZE) + 1;

  const nextPage = useCallback(() => {
    setSkip((s) => s + PAGE_SIZE);
  }, []);

  const prevPage = useCallback(() => {
    setSkip((s) => Math.max(0, s - PAGE_SIZE));
  }, []);

  return {
    draws,
    total,
    loading,
    error,
    fromInput,
    toInput,
    setFromInput,
    setToInput,
    search,
    skip,
    PAGE_SIZE,
    totalPages,
    currentPage,
    nextPage,
    prevPage,
    refetch: fetchDraws,
  };
}

export { PAGE_SIZE };

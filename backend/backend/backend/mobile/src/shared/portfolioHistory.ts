import { useSyncExternalStore } from 'react';

type Point = { date: string; value: number };

let history: Point[] = [
  { date: '2023-09-08', value: 10000 },
  { date: '2023-10-08', value: 10200 },
  { date: '2023-11-08', value: 10500 },
  { date: '2023-12-08', value: 10800 },
  { date: '2024-01-08', value: 11000 },
  { date: '2024-02-08', value: 11200 },
  { date: '2024-03-08', value: 11500 },
  { date: '2024-04-08', value: 11800 },
  { date: '2024-05-08', value: 12000 },
  { date: '2024-06-08', value: 12200 },
  { date: '2024-07-08', value: 12500 },
  { date: '2024-08-08', value: 12800 },
  { date: '2024-08-15', value: 12900 },
  { date: '2024-08-22', value: 13000 },
  { date: '2024-08-29', value: 13050 },
  { date: '2024-09-01', value: 13100 },
  { date: '2024-09-08', value: 13100 },
];

const listeners = new Set<() => void>();
const emit = () => listeners.forEach(l => l());

export function setPortfolioHistory(next: Point[]) {
  history = next.slice().sort((a, b) => +new Date(a.date) - +new Date(b.date));
  emit();
}

export function appendHistoryPoint(p: Point) {
  setPortfolioHistory([...history, p]);
}

export function usePortfolioHistory() {
  return useSyncExternalStore(
    (l) => { listeners.add(l); return () => listeners.delete(l); },
    () => history,
    () => history
  );
}

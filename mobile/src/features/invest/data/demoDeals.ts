/**
 * Demo deal list — single source for list + service.
 * Replace with API when real data is available.
 */

import type { Deal } from '../types/privateMarketsTypes';

export const DEMO_DEALS: Deal[] = [
  { id: '1', name: 'Series B — Fintech', tagline: 'B2B payments infrastructure', score: 72, category: 'fintech' },
  { id: '2', name: 'Seed — Climate', tagline: 'Carbon tracking & offsets', score: 68, category: 'climate' },
  { id: '3', name: 'Series A — Health', tagline: 'Remote patient monitoring', score: 61, category: 'health' },
];

export type Intent =
  | { type: 'calm-goal'; amount?: number; cadence?: 'weekly' | 'monthly' }
  | { type: 'next-move' }
  | { type: 'unknown' };

/** Very small intent parser for voice/dev */
export function parseIntent(text: string): Intent {
  const t = (text || '').toLowerCase().trim();
  if (!t) return { type: 'unknown' };
  if (/(calm|goal).*(invest|dca|plan)/.test(t) || /set calm investing goal/.test(t)) {
    const amountMatch = t.match(/\$?(\d{1,3}(?:,\d{3})*|\d+)(?:\s*(?:dollars|usd))?/);
    const amount = amountMatch ? Number(amountMatch[1].replace(/,/g, '')) : undefined;
    const cadence = /week|weekly/.test(t) ? 'weekly' : /month|monthly/.test(t) ? 'monthly' : undefined;
    return { type: 'calm-goal', amount, cadence };
  }
  if (/next move|what's my next move|suggest trades?/.test(t)) return { type: 'next-move' };
  return { type: 'unknown' };
}



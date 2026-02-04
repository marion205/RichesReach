// Voice intent recognizer for calm/DCA goals.
// Parses transcript text and returns a suggested plan (cadence, amount, startNow).

export interface CalmGoalPlan {
  cadence: 'weekly' | 'biweekly' | 'monthly';
  amountUsd: number;
  startNow: boolean;
}

export function recognizeCalmGoalIntent(transcript: string): CalmGoalPlan | null {
  const t = transcript.toLowerCase();
  if (!t) return null;
  if (t.includes('calm') || t.includes('goal') || t.includes('dollar cost') || t.includes('dca')) {
    // Extract amount if present
    const m = t.match(/\$?(\d{1,4})/);
    const amount = m ? Math.max(5, Math.min(1000, parseInt(m[1], 10))) : 25;
    let cadence: CalmGoalPlan['cadence'] = 'weekly';
    if (t.includes('month')) cadence = 'monthly';
    if (t.includes('biweek')) cadence = 'biweekly';
    return { cadence, amountUsd: amount, startNow: true };
  }
  return null;
}



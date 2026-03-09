/**
 * Shared goal plan types and math — used by GoalPlanScreen and Portfolio plan cards.
 * One shape for all goal types; goalType drives copy and defaults.
 */

export const GOAL_TYPES = ['millionaire', 'retirement', 'house', 'emergency_fund', 'concentration'] as const;
export type GoalType = (typeof GOAL_TYPES)[number];

export interface SavedGoalPlan {
  goalType: GoalType;
  target: number;
  currentInvested: number;
  monthlyContribution: number;
  yearsToReach: number;
  targetAge: number;
}

const DEFAULT_RATE = 0.07;
export const MIN_TARGET = 10_000;
export const MAX_TARGET = 100_000_000;

export function formatGoalTarget(amount: number): string {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(amount % 1_000_000 === 0 ? 0 : 1)}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(amount % 1_000 === 0 ? 0 : 1)}K`;
  return `$${amount.toLocaleString()}`;
}

export function yearsToTargetAge(age: number | null, targetAge: number): number | null {
  if (age == null || age >= targetAge) return null;
  const y = targetAge - age;
  return y > 0 && y <= 50 ? y : null;
}

export function monthlyPmtToReach(goal: number, years: number, annualRate: number, pv: number): number {
  if (years <= 0) return 0;
  const r = annualRate / 12;
  const n = years * 12;
  const fvPv = pv * Math.pow(1 + r, n);
  if (fvPv >= goal) return 0;
  return Math.round(((goal - fvPv) * r) / (Math.pow(1 + r, n) - 1));
}

export function yearsToGoal(goal: number, pmt: number, annualRate: number, pv: number): number {
  if (pmt <= 0 && pv <= 0) return 99;
  const r = annualRate / 12;
  let months = 1;
  while (months < 600) {
    const fv = pv * Math.pow(1 + r, months) + pmt * (Math.pow(1 + r, months) - 1) / r;
    if (fv >= goal) return Math.round(months / 12);
    months++;
  }
  return 99;
}

export function getDefaultTarget(goalType: GoalType): number {
  switch (goalType) {
    case 'millionaire': return 1_000_000;
    case 'retirement': return 1_500_000;
    case 'house': return 80_000;   // down payment
    case 'emergency_fund': return 15_000; // ~3–6 months
    case 'concentration': return 50_000;  // max in single position
    default: return 1_000_000;
  }
}

export function getGoalTitle(goalType: GoalType, target: number): string {
  const formatted = formatGoalTarget(target);
  switch (goalType) {
    case 'millionaire': return `Your ${formatted} plan`;
    case 'retirement': return `Retirement: ${formatted}`;
    case 'house': return `House fund: ${formatted}`;
    case 'emergency_fund': return `Emergency fund: ${formatted}`;
    case 'concentration': return `Concentration: cap at ${formatted}`;
    default: return `Your ${formatted} plan`;
  }
}

export function getGoalSubtitle(goalType: GoalType): string {
  switch (goalType) {
    case 'millionaire': return 'Wealth goal';
    case 'retirement': return 'Retirement nest egg';
    case 'house': return 'Down payment / house fund';
    case 'emergency_fund': return '3–6 months expenses';
    case 'concentration': return 'Reduce single-stock exposure';
    default: return 'Savings goal';
  }
}

export { DEFAULT_RATE };

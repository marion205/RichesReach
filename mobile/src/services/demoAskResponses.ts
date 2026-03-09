/**
 * Demo-mode Ask responses for pitch events.
 * Used when EXPO_PUBLIC_DEMO_MODE=true so Ask works without the backend.
 *
 * Every response follows the diagnostic structure:
 *   1. Direct answer using their real numbers (portfolio, age, income)
 *   2. Personalised insight — what this means specifically for them
 *   3. 3 concrete scenarios they can act on
 *   4. One best next step
 *   5. Follow-up prompts to keep the conversation going
 */

export interface DemoAskProfile {
  name?: string | null;
  incomeProfile?: {
    age?: number | null;
    incomeBracket?: string | null;
    investmentHorizon?: string | null;
    riskTolerance?: string | null;
  } | null;
}

// ─── Math helpers ────────────────────────────────────────────────────────────

/** Parse income bracket string like "$75,000 - $100,000" to approximate midpoint. */
function parseIncomeBracketMidpoint(bracket: string | null | undefined): number | null {
  if (!bracket || typeof bracket !== 'string') return null;
  const numbers = bracket.replace(/[^0-9]/g, ' ').trim().split(/\s+/).filter(Boolean).map(Number);
  if (numbers.length === 0) return null;
  if (numbers.length === 1) return numbers[0];
  return Math.round((numbers[0] + numbers[numbers.length - 1]) / 2);
}

/** Years from age to targetAge (default 65). */
function yearsTo(age: number | null | undefined, targetAge = 65): number | null {
  if (age == null) return null;
  const y = targetAge - age;
  return y > 0 && y <= 50 ? y : null;
}

/**
 * Monthly PMT to accumulate `goal` in `years` at `annualRate`,
 * optionally with a `presentValue` lump-sum head start.
 */
function monthlyPMT(goal: number, years: number, annualRate: number, presentValue = 0): number {
  if (years <= 0 || annualRate <= 0) return Math.round(goal / (years * 12 || 1));
  const r = annualRate / 12;
  const n = years * 12;
  const fvPV = presentValue * Math.pow(1 + r, n); // future value of existing portfolio
  const gap = Math.max(0, goal - fvPV);
  if (gap === 0) return 0;
  return Math.round((gap * r) / (Math.pow(1 + r, n) - 1));
}

/** Future value of a PMT stream + lump sum. */
function futureValue(pmt: number, years: number, annualRate: number, pv = 0): number {
  const r = annualRate / 12;
  const n = years * 12;
  return Math.round(pv * Math.pow(1 + r, n) + pmt * ((Math.pow(1 + r, n) - 1) / r));
}

/** Years to reach a goal from a starting portfolio at a given monthly contribution. */
function yearsToGoal(goal: number, pmt: number, annualRate: number, pv = 0): number {
  if (pmt <= 0 && pv <= 0) return 99;
  const r = annualRate / 12;
  if (r === 0) {
    const months = pv >= goal ? 0 : (goal - pv) / pmt;
    return Math.round(months / 12);
  }
  // Solve n: goal = pv*(1+r)^n + pmt*((1+r)^n - 1)/r
  // Approximate by iteration (fast enough for demo)
  let months = 1;
  while (months < 600) {
    const fv = pv * Math.pow(1 + r, months) + pmt * ((Math.pow(1 + r, months) - 1) / r);
    if (fv >= goal) return Math.round(months / 12);
    months++;
  }
  return 99;
}

// ─── Demo constants (Alex's profile) ─────────────────────────────────────────
const DEMO_PORTFOLIO = 14303;
const DEMO_TOP_HOLDING = 'NVDA';
const DEMO_TOP_HOLDING_PCT = 38;
const DEMO_CREDIT_SCORE = 720;
const DEMO_CREDIT_UTIL = 22;

// ─── Main export ─────────────────────────────────────────────────────────────

export function getDemoAskResponse(userInput: string, profile?: DemoAskProfile | null): string {
  const q = userInput.toLowerCase().trim();
  const ip = profile?.incomeProfile;
  const name = profile?.name?.trim() || null;
  const age = ip?.age ?? 32;
  const bracket = ip?.incomeBracket ?? '$75,000 - $100,000';
  const incomeMid = parseIncomeBracketMidpoint(bracket) ?? 87500;
  const monthlyIncome = Math.round(incomeMid / 12);
  const hi = ip?.investmentHorizon ?? '5-10 years';
  const rt = ip?.riskTolerance ?? 'Moderate';
  const namePrefix = name ? `${name}, ` : '';

  // ── Wealth / millionaire / build wealth / get rich ──────────────────────────
  if (
    q.includes('million') || q.includes('millionaire') || q.includes('1m') ||
    q.includes('one m') || q.includes('get rich') || q.includes('become rich') ||
    q.includes('financially free') || q.includes('financial freedom') ||
    q.includes('retire early') || q.includes('fire ') ||
    q.includes('build wealth') || q.includes('grow wealth') ||
    q.includes('grow my wealth') || q.includes('how wealthy') ||
    (q.includes('how to make') && (q.includes('money') || q.includes('dollar'))) ||
    (q.includes('wealth') && (q.includes('build') || q.includes('grow')))
  ) {
    const yearsLeft = yearsTo(age) ?? 33;
    const targetPMT = monthlyPMT(1_000_000, yearsLeft, 0.07, DEMO_PORTFOLIO);
    const conservativePMT = Math.round(targetPMT * 0.75);
    const aggressivePMT = Math.round(targetPMT * 1.55);
    const yrsConservative = yearsToGoal(1_000_000, conservativePMT, 0.07, DEMO_PORTFOLIO);
    const yrsTarget = yearsToGoal(1_000_000, targetPMT, 0.07, DEMO_PORTFOLIO);
    const yrsAggressive = yearsToGoal(1_000_000, aggressivePMT, 0.07, DEMO_PORTFOLIO);
    const savingsAt15pct = Math.round(monthlyIncome * 0.15);

    return `${namePrefix}Based on your current portfolio of $${DEMO_PORTFOLIO.toLocaleString()}, here's your real path to $1M.

📍 Your situation
At ${age} with ~$${incomeMid.toLocaleString()} income and $${DEMO_PORTFOLIO.toLocaleString()} already invested, your biggest wealth lever right now is not stock-picking — it's how much you invest each month, consistently.

📊 3 paths to $1M
• Conservative — $${conservativePMT.toLocaleString()}/month → ~${yrsConservative} years
• Target — $${targetPMT.toLocaleString()}/month → ~${yrsTarget} years
• Aggressive — $${aggressivePMT.toLocaleString()}/month → ~${yrsAggressive} years

At 15% savings rate your investable income is ~$${savingsAt15pct.toLocaleString()}/month — which puts you on the ${savingsAt15pct >= aggressivePMT ? 'aggressive' : savingsAt15pct >= targetPMT ? 'target' : 'conservative'} path today.

💡 Key insight
Your $${DEMO_PORTFOLIO.toLocaleString()} head start already grows to ~$${Math.round(DEMO_PORTFOLIO * Math.pow(1.07, yearsLeft)).toLocaleString()} on its own at 7%. You're not starting from zero — you just need to close the remaining gap with monthly contributions.

Because your portfolio is still in early growth phase, avoiding concentration risk matters more than chasing returns. A single bad bet at this stage costs you years.

✅ Best next step
Automate your monthly contribution and increase it by 10% every 6 months as income grows. Max employer 401(k) match first — that's an instant 50–100% return before the market does anything.

Try next:
• "How fast do I get to $1M if I invest $1,000/month?"
• "Am I too concentrated to hit this goal safely?"
• "What if I increase contributions 10% every year?"`;
  }

  // ── Retirement / on track to retire / nest egg ───────────────────────────────
  if (
    (q.includes('retire') && (q.includes('when') || q.includes('on track') || q.includes('ready'))) ||
    q.includes('retirement') || q.includes('nest egg')
  ) {
    const yearsLeft = yearsTo(age) ?? 33;
    const target = 1_500_000;
    const targetPMT = monthlyPMT(target, yearsLeft, 0.07, DEMO_PORTFOLIO);
    return `${namePrefix}Here’s your retirement picture.

📍 Your situation
At ${age} with $${DEMO_PORTFOLIO.toLocaleString()} invested, you have about ${yearsLeft} years to build a nest egg. A common target is 10–12× income by 65.

📊 Path to $${(target / 1e6).toFixed(1)}M by 65
• About $${targetPMT.toLocaleString()}/month at 7% gets you there in ${yearsLeft} years.
• Your current portfolio grows to ~$${Math.round(DEMO_PORTFOLIO * Math.pow(1.07, yearsLeft)).toLocaleString()} on its own — the rest is closing the gap with contributions.

💡 Key insight
Retirement is a number, not an age. With your nest egg target and timeline, automating contributions matters more than timing the market.

✅ Best next step
Set your retirement number and monthly plan so you can track progress. Adjust as income grows.

Try next:
• "How much do I need to retire at 60?"
• "What if I save 20% for retirement?"`;
  }

  // ── House / down payment / first home ────────────────────────────────────────
  if (
    q.includes('house') || q.includes('down payment') || q.includes('first home') ||
    q.includes('buy a home') || q.includes('save for a home')
  ) {
    const target = 80_000;
    const years = 5;
    const targetPMT = monthlyPMT(target, years, 0.05, 0);
    return `${namePrefix}Here’s a simple house fund plan.

📍 Your situation
A typical down payment target is 10–20% of the home price. For a $${(target / 1000).toFixed(0)}K goal over ${years} years, you’d aim for about $${targetPMT.toLocaleString()}/month (assuming ~5% growth in a savings or conservative mix).

📊 Options
• Aggressive — save more per month and reach the target sooner.
• Steady — $${targetPMT.toLocaleString()}/month gets you there in ${years} years.
• Stretch — lower monthly, longer timeline.

💡 Key insight
Keeping the down payment in something stable (high-yield savings or short-term bonds) reduces the risk of a market dip right when you’re ready to buy.

✅ Best next step
Set your down payment target and monthly amount so you can track progress.

Try next:
• "How much should I save for a down payment?"
• "When can I afford a house?"`;
  }

  // ── Emergency fund ───────────────────────────────────────────────────────────
  if (
    q.includes('emergency fund') || q.includes('rainy day') || q.includes('3 months') ||
    q.includes('6 months') || q.includes('months of expenses')
  ) {
    const monthsExpenses = Math.round(monthlyIncome * 4);
    const target = Math.round(monthlyIncome * 6);
    const targetPMT = Math.round(monthlyIncome * 0.15);
    const monthsToFill = Math.ceil(target / targetPMT);
    return `${namePrefix}Here’s your emergency fund plan.

📍 Your situation
A common target is 3–6 months of expenses. At ~$${monthlyIncome.toLocaleString()}/month that’s about $${target.toLocaleString()} for 6 months.

📊 Path
• Saving $${targetPMT.toLocaleString()}/month gets you to $${target.toLocaleString()} in about ${monthsToFill} months.
• Keep it in a high-yield savings account so it’s available and not in the market.

💡 Key insight
Your emergency fund is your buffer — it’s not for growth, it’s for security. Once you hit 3–6 months, you can focus extra savings on investing.

✅ Best next step
Set your emergency fund target (e.g. 6 months of expenses) and a monthly amount; track until you hit it.

Try next:
• "How much should I keep in cash?"
• "Where should I keep my emergency fund?"`;
  }

  // ── Am I too concentrated? ───────────────────────────────────────────────────
  if (
    q.includes('concentrat') ||
    (q.includes('too much') && (q.includes('one stock') || q.includes('single'))) ||
    q.includes('nvda') || q.includes('nvidia') ||
    (q.includes('position') && (q.includes('large') || q.includes('big') || q.includes('too')))
  ) {
    const portfolioMinuTop = Math.round(DEMO_PORTFOLIO * (1 - DEMO_TOP_HOLDING_PCT / 100));
    const topValue = Math.round(DEMO_PORTFOLIO * DEMO_TOP_HOLDING_PCT / 100);
    const trimTarget = Math.round(DEMO_PORTFOLIO * 0.20); // 20% is the trim target
    const excessValue = topValue - trimTarget;

    return `${namePrefix}Yes — your ${DEMO_TOP_HOLDING} position is flagged.

📍 Your situation
${DEMO_TOP_HOLDING} is ~${DEMO_TOP_HOLDING_PCT}% of your $${DEMO_PORTFOLIO.toLocaleString()} portfolio (~$${topValue.toLocaleString()}). The standard threshold is 20–25% for a single position. You're above it.

The rest of your portfolio ($${portfolioMinuTop.toLocaleString()}) is spread across other holdings — which is reasonable, but ${DEMO_TOP_HOLDING}'s outsized weight means a 30% drop in that one stock would cut your total portfolio by ~9%.

📊 3 scenarios
• Keep it — highest upside if ${DEMO_TOP_HOLDING} continues, but also highest downside risk
• Trim to 20% — sell ~$${excessValue.toLocaleString()} worth, redeploy into a broad index. Reduces risk without fully exiting
• Full rebalance — bring all positions under 15%, maximise diversification

💡 Key insight
At your portfolio size, a concentration hit is harder to recover from than it would be at $500K+. The math of loss recovery works against you: a 40% loss requires a 67% gain just to break even.

Your ${rt.toLowerCase()} risk tolerance and ${hi} horizon suggest the trim-to-20% path is most aligned with your profile.

✅ Best next step
Trim ${DEMO_TOP_HOLDING} to ~20% of portfolio and redirect the proceeds into a total market ETF (VTI or similar). You keep the upside exposure without betting the portfolio on one name.

Try next:
• "How do I rebalance without a big tax hit?"
• "What should I buy with the proceeds?"
• "How do I reach $1M with my current portfolio?"`;
  }

  // ── Summarize my portfolio ───────────────────────────────────────────────────
  if (
    (q.includes('summarize') && q.includes('portfolio')) ||
    (q.includes('portfolio') && (q.includes('summary') || q.includes('overview') || q.includes('look like') || q.includes('how is')))
  ) {
    const returnPct = 17.7;
    const returnAmt = Math.round(DEMO_PORTFOLIO * returnPct / 100);

    return `${namePrefix}Here's your portfolio snapshot.

📍 Your situation
Total value: $${DEMO_PORTFOLIO.toLocaleString()} | Return: +$${returnAmt.toLocaleString()} (+${returnPct}%) since inception

Top holdings:
• ${DEMO_TOP_HOLDING}: ${DEMO_TOP_HOLDING_PCT}% of portfolio ⚠️ above 25% threshold
• AAPL: ~18% — within range
• MSFT: ~14% — within range
• Remainder: ~30% across other positions

💡 Key insight
Your portfolio is tech-heavy and concentrated. That's worked well in a bull market, but it means your returns are closely tied to one sector's performance. A broad market correction in tech would hit you harder than a diversified portfolio.

The +${returnPct}% return is solid — above the S&P 500 average for the same period. The risk is that it's driven largely by ${DEMO_TOP_HOLDING}'s run, not diversified growth.

📊 3 things to watch
• Concentration: ${DEMO_TOP_HOLDING} at ${DEMO_TOP_HOLDING_PCT}% is the main flag
• Sector: ~70% tech exposure — consider adding some defensive positions
• Cash/bonds: No buffer visible — fine at your age, but worth noting

✅ Best next step
Address the ${DEMO_TOP_HOLDING} concentration first — that's the highest-priority risk in this portfolio right now.

Try next:
• "Is my ${DEMO_TOP_HOLDING} position too large?"
• "How do I add diversification without selling everything?"
• "Am I on track to retire?"`;
  }

  // ── Budget / saving / spending ───────────────────────────────────────────────
  if (
    q.includes('budget') || q.includes('50/30/20') ||
    q.includes('spend') || q.includes('saving') ||
    q.includes('how much should i save') || q.includes('build a budget')
  ) {
    const needs = Math.round(monthlyIncome * 0.50);
    const wants = Math.round(monthlyIncome * 0.25);
    const savings = Math.round(monthlyIncome * 0.25);
    const investTarget = Math.round(monthlyIncome * 0.15);
    const emergencyTarget = Math.round(monthlyIncome * 3);

    return `${namePrefix}Here's a budget built around your actual numbers.

📍 Your situation
Estimated take-home on $${incomeMid.toLocaleString()}/year: ~$${monthlyIncome.toLocaleString()}/month

📊 Recommended split
• Needs (rent, food, transport): $${needs.toLocaleString()}/month (50%)
• Wants (dining, subscriptions, fun): $${wants.toLocaleString()}/month (25%)
• Savings + investing: $${savings.toLocaleString()}/month (25%)
  ↳ Emergency fund until 3 months covered (~$${emergencyTarget.toLocaleString()} target)
  ↳ Then investing: ~$${investTarget.toLocaleString()}/month into your portfolio

💡 Key insight
The biggest leak in most budgets at your income level isn't big purchases — it's subscriptions, delivery apps, and lifestyle creep. A typical audit finds $200–$400/month in painless cuts.

At $${investTarget.toLocaleString()}/month invested, you'd reach $1M in roughly ${yearsToGoal(1_000_000, investTarget, 0.07, DEMO_PORTFOLIO)} years. Bumping that to $${Math.round(investTarget * 1.3).toLocaleString()}/month shaves off several years.

✅ Best next step
Automate $${investTarget.toLocaleString()}/month into your investment account so the decision is already made. Then audit subscriptions this week — most people find at least $100/month they don't notice.

Try next:
• "How do I reach $1M on this budget?"
• "Should I pay off debt or invest first?"
• "What's the right emergency fund for me?"`;
  }

  // ── Retirement / on track ────────────────────────────────────────────────────
  if (
    q.includes('retirement') || q.includes('retire') ||
    q.includes('401k') || q.includes('401(k)') || q.includes('ira') ||
    q.includes('on track') || q.includes('when can i')
  ) {
    const yearsLeft = yearsTo(age) ?? 33;
    const retireAge = (age ?? 32) + yearsLeft;
    const currentPMT = Math.round(monthlyIncome * 0.10); // assume 10% savings rate baseline
    const fvAt10pct = futureValue(currentPMT, yearsLeft, 0.07, DEMO_PORTFOLIO);
    const fvAt15pct = futureValue(Math.round(monthlyIncome * 0.15), yearsLeft, 0.07, DEMO_PORTFOLIO);
    const fvAt20pct = futureValue(Math.round(monthlyIncome * 0.20), yearsLeft, 0.07, DEMO_PORTFOLIO);
    const withdrawalAt4pct = (n: number) => Math.round(n * 0.04 / 12);

    return `${namePrefix}Here's your retirement picture at ${age}.

📍 Your situation
$${DEMO_PORTFOLIO.toLocaleString()} invested today, targeting retirement at ${retireAge}. That's ${yearsLeft} years of compounding.

📊 3 retirement scenarios (at 7% growth)
• Save 10%/month (~$${currentPMT.toLocaleString()}) → retire with ~$${(fvAt10pct / 1000).toFixed(0)}K | ~$${withdrawalAt4pct(fvAt10pct).toLocaleString()}/month income
• Save 15%/month (~$${Math.round(monthlyIncome * 0.15).toLocaleString()}) → ~$${(fvAt15pct / 1000).toFixed(0)}K | ~$${withdrawalAt4pct(fvAt15pct).toLocaleString()}/month income
• Save 20%/month (~$${Math.round(monthlyIncome * 0.20).toLocaleString()}) → ~$${(fvAt20pct / 1000).toFixed(0)}K | ~$${withdrawalAt4pct(fvAt20pct).toLocaleString()}/month income

💡 Key insight
The jump from 10% to 15% savings rate adds ~$${Math.round((fvAt15pct - fvAt10pct) / 1000)}K to your retirement — that's one of the highest-leverage moves available to you. It costs less than you think if you automate it before it hits your checking account.

Your ${rt.toLowerCase()} risk tolerance is appropriate for your timeline. A 70/30 stock-bond split makes sense as you approach 50; for now, staying growth-oriented is the right call.

✅ Best next step
Increase your savings rate by just 2% this month. You won't feel it — but over ${yearsLeft} years it adds significantly to your final number. Max employer match first if you haven't already.

Try next:
• "How do I reach $1M before retirement?"
• "Roth vs Traditional IRA — which is right for me?"
• "How does my ${DEMO_TOP_HOLDING} position affect my retirement plan?"`;
  }

  // ── Debt ─────────────────────────────────────────────────────────────────────
  if (q.includes('debt') || q.includes('pay off') || q.includes('loan') || q.includes('credit card') || q.includes('interest rate')) {
    return `${namePrefix}Here's how to think about debt vs investing with your numbers.

📍 Your situation
The decision is simple: compare your debt's interest rate to your expected investment return (~7% for a diversified portfolio).

📊 3 scenarios
• High-interest debt (>8% APR — credit cards, personal loans): Pay these off first. It's a guaranteed 20%+ return — nothing in the market beats that on a risk-adjusted basis.
• Mid-rate debt (5–8% APR — student loans, car loans): Split: pay minimum + invest the rest. The math is roughly a wash, but investing builds the habit.
• Low-rate debt (<5% APR — mortgages, some student loans): Invest aggressively. Your expected market return likely outpaces the debt cost over time.

💡 Key insight
Paying off a 22% APR credit card is the same as earning 22% guaranteed on that money — better than any investment available. The psychological win of being debt-free also removes a major behavioral risk (people make worse investment decisions when they're stressed about debt).

✅ Best next step
List every debt with its interest rate. Anything above 8% gets paid down aggressively before you increase investment contributions.

Try next:
• "How do I build a budget to pay off debt faster?"
• "Should I invest while paying off student loans?"
• "How do I reach $1M even with current debt?"`;
  }

  // ── Credit score ─────────────────────────────────────────────────────────────
  if (q.includes('credit') || q.includes('score') || q.includes('utilization')) {
    const targetUtil = 9;
    const currentUtil = DEMO_CREDIT_UTIL;

    return `${namePrefix}Here's your credit picture.

📍 Your situation
Credit score: ${DEMO_CREDIT_SCORE} (Good range — qualifies for most loans, not yet at best rates)
Utilization: ${currentUtil}% — this is actually solid (under 30% is good, under 10% is optimal)

📊 3 ways to improve
• Get to 750+ → reduces mortgage/auto loan rates by 0.5–1.5%, worth tens of thousands over a loan term
• Drop utilization to ${targetUtil}% → fastest single lever to boost score 10–30 points
• Age your accounts → don't close old cards; length of credit history matters

💡 Key insight
Going from ${DEMO_CREDIT_SCORE} to 760+ is achievable in 6–12 months with no new debt — just utilization management and on-time payments. The financial payoff on a future mortgage is significant: on a $400K loan, a 0.5% rate difference saves ~$40K over 30 years.

✅ Best next step
Set every card to autopay the full balance monthly. Eliminates the biggest risk (missed payments) with zero effort. Then work on getting utilization under 10% on each card individually, not just in total.

Try next:
• "How does my credit score affect my investment strategy?"
• "Should I get a new card to improve my score?"
• "How do I use credit to build wealth faster?"`;
  }

  // ── ETF / index fund ─────────────────────────────────────────────────────────
  if (q.includes('etf') || q.includes('index fund') || q.includes('vti') || q.includes('spy') || q.includes('voo')) {
    return `${namePrefix}Here's the case for index funds with your situation in mind.

📍 Your situation
With a $${DEMO_PORTFOLIO.toLocaleString()} portfolio, a ${rt.toLowerCase()} risk tolerance and ${hi} horizon, low-cost index funds should be the foundation — not the whole portfolio, but the core.

📊 3 common approaches
• Total market (VTI/FSKAX) → broadest diversification, lowest cost (~0.03% expense ratio), set-and-forget
• S&P 500 (VOO/SPY) → large-cap focused, slightly less diversified but very similar long-term return
• 3-fund portfolio (US stocks + international + bonds) → adds global diversification and a bond buffer as you age

💡 Key insight
The fee difference between a 0.03% index fund and a 1% actively managed fund sounds small. On $${DEMO_PORTFOLIO.toLocaleString()} over 30 years at 7% growth, that 1% difference costs ~$${Math.round(futureValue(0, 30, 0.07, DEMO_PORTFOLIO) * (1 - Math.pow(0.9993/1.0093, 30)) / 1000)}K in lost compounding. Fees are the most predictable drag on returns.

✅ Best next step
Use index funds as your core (70–80% of portfolio), then your individual stock picks as satellite positions. This gives you diversified base growth while keeping room for conviction bets like ${DEMO_TOP_HOLDING}.

Try next:
• "Am I too concentrated in individual stocks?"
• "How do I rebalance into index funds without selling everything at once?"
• "What's the right mix for my risk tolerance?"`;
  }

  // ── Risk / safe ──────────────────────────────────────────────────────────────
  if (q.includes('risk') || q.includes('safe') || q.includes('conservative') || q.includes('volatile')) {
    return `${namePrefix}Here's how to think about risk with your actual profile.

📍 Your situation
Risk tolerance: ${rt} | Horizon: ${hi} | Age: ${age}
At ${age} with a ${hi} horizon, you have time to ride out volatility — which means you can afford more risk than someone at 55.

📊 3 risk levels and what they mean for you
• Conservative (40% stocks / 60% bonds) → lower volatility, lower growth. Appropriate if your timeline is <5 years or you sleep better this way
• Moderate (70/30) → balanced. Grows meaningfully, manageable drawdowns. Matches your stated profile
• Aggressive (90/10 or 100% stocks) → maximum growth potential, but 30–40% drawdowns are normal. Fine at your age if you won't panic-sell

💡 Key insight
The biggest risk for most investors isn't market volatility — it's their own reaction to it. Selling during a 30% drawdown locks in the loss and misses the recovery. A portfolio you'll actually hold through a down market is better than one optimised on paper but abandoned in practice.

Your ${DEMO_TOP_HOLDING} concentration at ${DEMO_TOP_HOLDING_PCT}% is currently your biggest real-world risk — more so than your asset allocation.

✅ Best next step
Make sure your asset allocation matches the risk level you'll actually hold through a -30% year, not the one that looks best on a spreadsheet. Then address the concentration issue.

Try next:
• "Is my ${DEMO_TOP_HOLDING} position too risky?"
• "How do I rebalance to reduce risk?"
• "What should my portfolio look like at my age?"`;
  }

  // ── Generic catch-all — still diagnostic, still uses their numbers ────────────
  const yearsLeft = yearsTo(age) ?? 33;
  const targetPMT = monthlyPMT(1_000_000, yearsLeft, 0.07, DEMO_PORTFOLIO);

  return `${namePrefix}Here's your quick financial snapshot.

📍 Your situation
Age: ${age} | Income: ${bracket} | Portfolio: $${DEMO_PORTFOLIO.toLocaleString()} | Risk: ${rt}

To reach $1M by ${(age ?? 32) + yearsLeft}: ~$${targetPMT.toLocaleString()}/month at 7% growth
Your ${DEMO_TOP_HOLDING} position (${DEMO_TOP_HOLDING_PCT}%) is the main flag in your current portfolio.

What do you want to tackle?
• "How do I become a millionaire?" — get your personalised path
• "Is my ${DEMO_TOP_HOLDING} position too large?" — concentration risk analysis
• "Am I on track to retire?" — retirement projection with your numbers
• "Help me build a budget" — spending plan based on your income`;
}

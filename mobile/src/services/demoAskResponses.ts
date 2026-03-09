/**
 * Demo-mode Ask responses for pitch events.
 * Used when EXPO_PUBLIC_DEMO_MODE=true so Ask works without the backend.
 * Responses are written to sound like a real financial copilot: specific, actionable, and professional.
 * When profile is provided (e.g. from GET_USER_PROFILE in demo), answers are personalized.
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

/** Parse income bracket string like "$75,000 - $100,000" to approximate midpoint in dollars. */
function parseIncomeBracketMidpoint(bracket: string | null | undefined): number | null {
  if (!bracket || typeof bracket !== 'string') return null;
  const numbers = bracket.replace(/[^0-9]/g, ' ').split(/\s+/).filter(Boolean).map(Number);
  if (numbers.length === 0) return null;
  if (numbers.length === 1) return numbers[0];
  return Math.round((numbers[0] + numbers[numbers.length - 1]) / 2);
}

/** Approximate years to reach goal from current age (e.g. years to 65). */
function yearsToRetirement(age: number | null | undefined, targetAge = 65): number | null {
  if (age == null || typeof age !== 'number') return null;
  const years = targetAge - age;
  return years > 0 && years <= 50 ? years : null;
}

/** Monthly contribution needed to reach $1M in N years at annual rate r (e.g. 0.07). */
function monthlyToReach1M(years: number, annualRate: number): number {
  if (years <= 0 || annualRate <= 0) return 3400;
  const monthlyRate = annualRate / 12;
  const months = years * 12;
  const fv = 1_000_000;
  const pmt = (fv * monthlyRate) / (Math.pow(1 + monthlyRate, months) - 1);
  return Math.round(pmt);
}

export function getDemoAskResponse(userInput: string, profile?: DemoAskProfile | null): string {
  const q = userInput.toLowerCase().trim();
  const ip = profile?.incomeProfile;
  const name = profile?.name?.trim() || null;

  // ── Wealth building / million / long-term goals ─────────────────────────────
  if (
    q.includes('million') ||
    q.includes('millionaire') ||
    q.includes('1m') ||
    q.includes('one m') ||
    q.includes('get rich') ||
    q.includes('become rich') ||
    q.includes('financially free') ||
    q.includes('financial freedom') ||
    q.includes('retire early') ||
    q.includes('fire ') ||
    q.includes('build wealth') ||
    q.includes('grow wealth') ||
    q.includes('grow my wealth') ||
    q.includes('how wealthy') ||
    (q.includes('how to make') && (q.includes('money') || q.includes('dollar'))) ||
    (q.includes('wealth') && (q.includes('build') || q.includes('grow')))
  ) {
    const age = ip?.age ?? null;
    const bracket = ip?.incomeBracket ?? null;
    const years = yearsToRetirement(age) ?? 15;
    const monthlyNeeded = monthlyToReach1M(years, 0.07);
    const incomeMid = parseIncomeBracketMidpoint(bracket);
    const savingsRatePct = 15;
    const savingsAt15Pct = incomeMid != null ? Math.round((incomeMid / 12) * (savingsRatePct / 100)) : null;

    let opening = 'Great question. ';
    if (name) opening = `${name}, ` + opening.toLowerCase();
    opening += "Hitting $1M is realistic with discipline and time. Here's the math that matters:\n\n";

    let personalBlock = '';
    if (age != null || bracket != null) {
      const parts: string[] = [];
      if (age != null && bracket) {
        parts.push(`At ${age} with an income in the ${bracket} range`);
      } else if (age != null) {
        parts.push(`At ${age}`);
      } else if (bracket) {
        parts.push(`With an income in the ${bracket} range`);
      }
      if (parts.length) {
        let line = 'For you: ' + parts.join(', ') + ', ';
        if (savingsAt15Pct != null) {
          line += `saving 15% of income would be about $${savingsAt15Pct.toLocaleString()}/month. `;
        }
        line += `To reach $1M in ${years} years at a 7% return you'd need to invest about $${monthlyNeeded.toLocaleString()}/month.`;
        if (savingsAt15Pct != null && monthlyNeeded > savingsAt15Pct) {
          line += " Consider increasing your savings rate over time or maxing out 401(k) and IRA first—that can close the gap.";
        }
        line += '\n\n';
        personalBlock = line;
      }
    }

    const genericBlock = `Compound growth: At a 7% annual return (roughly long-term market average), you'd need to invest about $${monthlyNeeded.toLocaleString()}/month for ${years} years to get to ~$1M. The earlier you start, the less you need each month.\n\nWhat actually works: Max out tax-advantaged accounts first (401(k), IRA). Get any employer match—that's free return. Then invest in low-cost index funds or ETFs so you're diversified and fees don't eat your growth. Automate contributions so you're not tempted to time the market.\n\nIn this app: Once your portfolio and goals are connected, I can show you a path tailored to your numbers and risk tolerance. Want to see "Am I on track?" or "Summarize my portfolio" next?`;

    return opening + personalBlock + genericBlock;
  }

  // ── Am I too concentrated? (quick prompt) ───────────────────────────────────
  if (
    q.includes('concentrat') ||
    q.includes('too much') && (q.includes('one stock') || q.includes('single'))
  ) {
    return `Concentration risk is real—putting too much in one stock or sector can wipe out gains in a downturn.

Rule of thumb: Many advisors suggest no single position above 10–15% of your portfolio, and no sector above 25–30%. If you’re over that, consider trimming winners and rebalancing into index funds or other sectors.

In your case: When your portfolio is connected, I can flag your top holdings and show what % each one is. You’ll see something like “AAPL is 22% of your portfolio—above the 15% guideline.” For now, check your Invest tab to see your allocation; we can dig into a rebalance plan next.`;
  }

  // ── Summarize my portfolio (quick prompt) ─────────────────────────────────
  if (
    q.includes('summarize') && q.includes('portfolio') ||
    q.includes('portfolio') && (q.includes('summary') || q.includes('overview') || q.includes('look like'))
  ) {
    return `Here’s how I’d summarize a typical portfolio once it’s connected:

Snapshot: Total value, cost basis, and return (dollars and %). Top 5–10 holdings with symbol, value, and % of portfolio. I’d call out any big concentration (e.g. “Your largest position is X at 18%”).

Allocation: Rough breakdown—e.g. “About 70% equities, 20% bonds, 10% cash/other.” I’d note if you’re light on diversification (e.g. all tech) or well spread.

One-line takeaway: Something like “You’re on track for a moderate-risk profile” or “Consider adding international or bonds to reduce volatility.”

Open the Invest tab to see your live numbers; once you’ve connected your accounts, I can give this summary in the chat with your real data.`;
  }

  // ── Budget / saving / spending ─────────────────────────────────────────────
  if (q.includes('budget') || q.includes('50/30/20') || (q.includes('saving') && q.includes('how')) || q.includes('spend')) {
    return `The 50/30/20 rule is a solid starting point: 50% needs (rent, utilities, groceries), 30% wants (dining, travel, subscriptions), 20% savings and debt payoff.

To make it real: Track spending for one month—every coffee and subscription. Most people are surprised where the money goes. Then set one small win: e.g. “I’ll save $200/month by cutting two subscriptions and cooking two more nights.” Automate that $200 into a savings or investment account so you don’t have to decide each month.

If you have high-interest debt: Pay that down before chasing big returns. Credit card interest usually beats market returns in the wrong direction. Once you’re connected here, I can factor in your cash flow and suggest a plan that fits your numbers.`;
  }

  // ── Investment / portfolio / diversify ────────────────────────────────────
  if (
    q.includes('invest') ||
    q.includes('portfolio') ||
    q.includes('diversif')
  ) {
    return `Diversification means not putting all your eggs in one basket—across stocks, sectors, and asset classes (e.g. some bonds, some international). That smooths out volatility and can improve risk‑adjusted returns over time.

Practical steps: Use low‑cost index funds or ETFs for the core of your portfolio (e.g. S&P 500, total market, or a target-date fund). Add bonds or cash based on your time horizon and risk tolerance. Rebalance once a year or when a position grows beyond your target (e.g. no single stock above 10–15%).

In this app: Your Invest tab shows your current allocation. Ask “Am I too concentrated?” to get a quick check, or connect your accounts so I can give advice tailored to your actual holdings.`;
  }

  // ── Stock / market / trading ──────────────────────────────────────────────
  if (q.includes('stock') || q.includes('market') || q.includes('trading')) {
    return `Stocks can build long‑term wealth, but they come with volatility. A few principles that hold up:

Time in the market: Trying to time entries and exits usually hurts returns. Staying invested in a diversified portfolio has historically worked better than jumping in and out.

Dollar-cost averaging: Investing a fixed amount on a schedule (e.g. every paycheck) smooths out the impact of price swings and can reduce the stress of “is now a good time?”

Risk: Only invest money you don’t need for at least 5–10 years. Keep an emergency fund in cash or something stable first. If you’d like, I can walk through “How much should I keep in cash?” or “Summarize my portfolio” using your data here.`;
  }

  // ── Retirement / 401k / IRA ──────────────────────────────────────────────
  if (q.includes('retirement') || q.includes('401k') || q.includes('401(k)') || q.includes('ira')) {
    return `Retirement savings work best when you start early and use tax‑advantaged accounts.

Order of operations: Contribute enough to your 401(k) to get the full employer match—that’s an instant return. Then max out an IRA (Roth if you expect to be in a higher tax bracket later). After that, bump 401(k) contributions. Aim for 15% of income if you can; even 10% plus a match can get you far.

Roth vs traditional: Roth = pay tax now, tax‑free in retirement. Traditional = deduction now, tax later. Roth often makes sense for younger or lower‑income savers; traditional can help if you’re in a high bracket now.

In the app: Once your accounts are linked, I can reference your current balance and suggest whether you’re on track for your target age and lifestyle.`;
  }

  // ── ETF / index fund ──────────────────────────────────────────────────────
  if (q.includes('etf') || q.includes('index fund')) {
    return `ETFs (exchange‑traded funds) and index funds are baskets of securities—often designed to track a market index like the S&P 500. You get broad diversification in one ticker, usually with low fees.

Why they're popular: Low cost, transparent, and you don’t have to pick individual stocks. They’re a core building block for most long‑term portfolios. The main choice is which index (U.S. total market, international, bonds) and whether you use a mutual fund or an ETF (ETFs trade like stocks; index mutual funds often have minimums).

In RichesReach: You can see how your portfolio is allocated in the Invest tab. If you’re heavy in one sector or stock, we can talk about adding an index fund to balance it.`;
  }

  // ── Credit / score / utilization ───────────────────────────────────────────
  if (q.includes('credit') || q.includes('score') || q.includes('utilization')) {
    return `Your credit score affects borrowing costs and approval for loans and cards. Utilization—how much of your total limit you use—is a big lever; many advisors suggest keeping it under 30%, and under 10% is even better for scoring.

Quick wins: Pay down revolving balances, avoid closing old cards (they help your history and total limit), and set up autopay so you never miss a due date. Errors on your report can drag scores down, so check your reports once a year and dispute any mistakes.

In this app: When your credit data is connected, I can tell you your current score and utilization and suggest steps that fit your situation.`;
  }

  // ── Risk / safe / conservative ────────────────────────────────────────────
  if (q.includes('risk') || q.includes('safe') || q.includes('conservative')) {
    return `“Safe” usually means lower volatility and less chance of big short‑term losses—think cash, short‑term bonds, or diversified bond funds. The tradeoff is lower long‑term return potential than stocks.

A balanced approach: Many people hold a mix: enough in cash or stable assets for emergencies and near‑term goals, and the rest in stocks or stock funds for growth. The right split depends on your time horizon and how much volatility you can stomach.

In the app: Your portfolio view and risk settings help you see how much you have in stocks vs bonds vs cash. I can walk through “Am I too concentrated?” or “Summarize my portfolio” so you know where you stand.`;
  }

  // ── Generic / catch‑all — use their numbers, not a generic intro ──────────
  const catchAllAge = ip?.age ?? null;
  const catchAllBracket = ip?.incomeBracket ?? null;
  const catchAllYears = yearsToRetirement(catchAllAge) ?? 15;
  const catchAllMonthly = monthlyToReach1M(catchAllYears, 0.07);
  const catchAllIncomeMid = parseIncomeBracketMidpoint(catchAllBracket);
  const catchAllSavings = catchAllIncomeMid != null ? Math.round((catchAllIncomeMid / 12) * 0.15) : null;

  let catchAllOpening = name ? `${name}, happy to help. ` : `Happy to help. `;

  if (catchAllAge != null && catchAllBracket) {
    catchAllOpening += `At ${catchAllAge} with an income in the ${catchAllBracket} range, here's your quick picture:\n\n`;
    catchAllOpening += `• To reach $1M in ${catchAllYears} years at 7% growth: ~$${catchAllMonthly.toLocaleString()}/month\n`;
    if (catchAllSavings != null) {
      catchAllOpening += `• Saving 15% of your income: ~$${catchAllSavings.toLocaleString()}/month\n`;
    }
    catchAllOpening += `\nWhat specifically do you want to tackle? `;
  }

  return catchAllOpening + `Try: "Am I too concentrated?", "Summarize my portfolio", "How do I budget better?", or "When can I retire?" — I'll give you a specific answer based on your situation.`;
}

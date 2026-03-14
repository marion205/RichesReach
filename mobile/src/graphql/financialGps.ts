import { gql } from '@apollo/client';

export const GET_WEALTH_ARRIVAL = gql`
  query GetWealthArrival($targetNetWorth: Float) {
    wealthArrival(targetNetWorth: $targetNetWorth) {
      userId
      currentNetWorth
      estimatedMonthlyIncome
      investableSurplusMonthly
      annualContribution
      savingsRatePct
      projectionYears
      riskTolerance
      targetNetWorth
      currentAge
      headlineSentence
      dataQuality
      primary {
        scenario
        annualReturn
        wealthArrivalYears
        finalNetWorth
        totalContributions
        totalGrowth
        milestones {
          targetAmount
          yearsAway
          arrivalYear
          alreadyAchieved
          label
        }
        yearByYear {
          year
          netWorth
          portfolioValue
          annualContribution
        }
      }
      scenarios {
        scenario
        annualReturn
        wealthArrivalYears
        finalNetWorth
        yearByYear {
          year
          netWorth
        }
      }
    }
  }
`;

export const GET_FINANCIAL_LEAKS = gql`
  query GetFinancialLeaks {
    financialLeaks {
      totalMonthlyLeak
      totalAnnualLeak
      savingsImpact5yr
      headlineSentence
      topLeak {
        merchantName
        normalizedName
        cadence
        confidence
        monthlyEquivalent
        category
        easyToForget
      }
      detectedSubscriptions {
        merchantName
        normalizedName
        cadence
        confidence
        monthlyEquivalent
        annualEquivalent
        category
        easyToForget
        occurrenceCount
        lastSeen
        amountVariance
      }
    }
  }
`;

export const GET_NET_WORTH_HISTORY = gql`
  query GetNetWorthHistory($days: Int) {
    netWorthHistory(days: $days) {
      userId
      currentNetWorth
      currentPortfolioValue
      currentSavingsBalance
      currentDebt
      change7d
      change30d
      change90d
      change1yr
      changePct30d
      allTimeHigh
      allTimeHighDate
      allTimeLow
      allTimeLowDate
      increaseStreakDays
      snapshotCapturedToday
      dataQuality
      headlineSentence
      history {
        capturedAt
        netWorth
        portfolioValue
        savingsBalance
        debt
      }
    }
  }
`;

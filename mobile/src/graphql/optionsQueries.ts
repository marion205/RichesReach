import { gql } from '@apollo/client';

export const GET_EDGE_PREDICTIONS = gql`
  query GetEdgePredictions($symbol: String!) {
    edgePredictions(symbol: $symbol) {
      strike
      expiration
      optionType
      currentEdge
      predictedEdge15min
      predictedEdge1hr
      predictedEdge1day
      confidence
      explanation
      edgeChangeDollars
      currentPremium
      predictedPremium15min
      predictedPremium1hr
    }
  }
`;

export const GET_ONE_TAP_TRADES = gql`
  query GetOneTapTrades($symbol: String!, $accountSize: Float, $riskTolerance: Float) {
    oneTapTrades(symbol: $symbol, accountSize: $accountSize, riskTolerance: $riskTolerance) {
      strategy
      entryPrice
      expectedEdge
      confidence
      takeProfit
      stopLoss
      reasoning
      maxLoss
      maxProfit
      probabilityOfProfit
      symbol
      legs {
        action
        optionType
        strike
        expiration
        quantity
        premium
      }
      strategyType
      daysToExpiration
      totalCost
      totalCredit
    }
  }
`;

export const GET_IV_SURFACE_FORECAST = gql`
  query GetIVSurfaceForecast($symbol: String!) {
    ivSurfaceForecast(symbol: $symbol) {
      symbol
      currentIv
      predictedIv1hr
      predictedIv24hr
      confidence
      regime
      ivChangeHeatmap {
        strike
        expiration
        currentIv
        predictedIv1hr
        predictedIv24hr
        ivChange1hrPct
        ivChange24hrPct
        confidence
      }
      timestamp
    }
  }
`;


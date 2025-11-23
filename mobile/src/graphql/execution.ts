import { gql } from '@apollo/client';

export const GET_EXECUTION_SUGGESTION = gql`
  query GetExecutionSuggestion($signal: JSONString!, $signalType: String!) {
    executionSuggestion(signal: $signal, signalType: $signalType) {
      orderType
      priceBand
      timeInForce
      entryStrategy
      bracketLegs {
        stop
        target1
        target2
        orderStructure
      }
      suggestedSize
      rationale
      microstructureSummary
    }
  }
`;

export const GET_ENTRY_TIMING_SUGGESTION = gql`
  query GetEntryTimingSuggestion($signal: JSONString!, $currentPrice: Float!) {
    entryTimingSuggestion(signal: $signal, currentPrice: $currentPrice) {
      recommendation
      waitReason
      pullbackTarget
      currentDistancePct
    }
  }
`;


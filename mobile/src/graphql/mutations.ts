import { gql } from '@apollo/client';

// Add to Watchlist Mutation
export const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($symbol: String!, $company_name: String, $notes: String) {
    addToWatchlist(symbol: $symbol, company_name: $company_name, notes: $notes) {
      success
      message
    }
  }
`;

// Remove from Watchlist Mutation
export const REMOVE_FROM_WATCHLIST = gql`
  mutation RemoveFromWatchlist($symbol: String!) {
    removeFromWatchlist(symbol: $symbol) {
      success
      message
    }
  }
`;

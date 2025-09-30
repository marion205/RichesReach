import { gql } from '@apollo/client';

export const GET_MY_FOLLOWS = gql`
  query GetMyFollows {
    me {
      id
      followedTickers
    }
  }
`;

export const FOLLOW_TICKER = gql`
  mutation FollowTicker($symbol: String!) {
    followTicker(symbol: $symbol) {
      success
      following { symbol }
    }
  }
`;

export const UNFOLLOW_TICKER = gql`
  mutation UnfollowTicker($symbol: String!) {
    unfollowTicker(symbol: $symbol) {
      success
      following { symbol }
    }
  }
`;

/* Optional push: new posts for tickers the user follows */
export const SUB_TICKER_POSTS = gql`
  subscription TickerPostCreated($symbols: [String!]!) {
    tickerPostCreated(symbols: $symbols) {
      id
      kind         # DISCUSSION | PREDICTION | POLL
      title
      tickers
      user { id name }
      createdAt
    }
  }
`;

/* Tiny quotes for chips */
export const MINI_QUOTES = gql`
  query MiniQuotes($symbols: [String!]!) {
    quotes(symbols: $symbols) {
      symbol
      last
      changePct
    }
  }
`;

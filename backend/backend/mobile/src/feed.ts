import { gql } from '@apollo/client';

export const GET_FOLLOWING_FEED = gql`
  query GetFollowingFeed($symbols: [String!]!, $limit: Int = 50) {
    feedByTickers(symbols: $symbols, limit: $limit) {
      id
      kind
      title
      content
      tickers
      score
      commentCount
      user {
        id
        name
        profilePic
      }
      createdAt
    }
  }
`;

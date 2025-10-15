// sboclGql.ts
import { gql } from '@apollo/client';

export const GET_SBLOC_OFFER = gql`
  query GetSblocOffer {
    sblocOffer {
      ltv                # e.g. 0.5
      apr                # e.g. 0.085 for 8.5%
      minDraw            # e.g. 1000
      maxDrawMultiplier  # e.g. 0.95 * (ltv*eligibleEquity)
      disclosures        # [String!]
      eligibleEquity     # server can compute; else pass from client
      updatedAt
    }
  }
`;

export const INITIATE_SBLOC_DRAW = gql`
  mutation InitiateSblocDraw($amount: Float!) {
    initiateSblocDraw(amount: $amount) {
      success
      message
      draw {
        id
        amount
        status
        createdAt
        estSettlementAt
      }
    }
  }
`;

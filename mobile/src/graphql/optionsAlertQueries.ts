import { gql } from '@apollo/client';

export const GET_OPTIONS_ALERTS = gql`
  query GetOptionsAlerts($status: String, $symbol: String) {
    optionsAlerts(status: $status, symbol: $symbol) {
      id
      symbol
      strike
      expiration
      optionType
      alertType
      targetValue
      direction
      status
      triggeredAt
      notificationSent
      createdAt
      updatedAt
    }
  }
`;

export const GET_OPTIONS_ALERT = gql`
  query GetOptionsAlert($id: ID!) {
    optionsAlert(id: $id) {
      id
      symbol
      strike
      expiration
      optionType
      alertType
      targetValue
      direction
      status
      triggeredAt
      notificationSent
      createdAt
      updatedAt
    }
  }
`;


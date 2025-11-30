import { gql } from '@apollo/client';

export const CREATE_OPTIONS_ALERT = gql`
  mutation CreateOptionsAlert(
    $symbol: String!
    $strike: Float
    $expiration: String
    $optionType: String
    $alertType: String!
    $targetValue: Float
    $direction: String
  ) {
    createOptionsAlert(
      symbol: $symbol
      strike: $strike
      expiration: $expiration
      optionType: $optionType
      alertType: $alertType
      targetValue: $targetValue
      direction: $direction
    ) {
      success
      alert {
        id
        symbol
        strike
        expiration
        optionType
        alertType
        targetValue
        direction
        status
      }
      error
    }
  }
`;

export const UPDATE_OPTIONS_ALERT = gql`
  mutation UpdateOptionsAlert(
    $id: ID!
    $targetValue: Float
    $direction: String
    $status: String
  ) {
    updateOptionsAlert(
      id: $id
      targetValue: $targetValue
      direction: $direction
      status: $status
    ) {
      success
      alert {
        id
        symbol
        strike
        expiration
        optionType
        alertType
        targetValue
        direction
        status
      }
      error
    }
  }
`;

export const DELETE_OPTIONS_ALERT = gql`
  mutation DeleteOptionsAlert($id: ID!) {
    deleteOptionsAlert(id: $id) {
      success
      error
    }
  }
`;


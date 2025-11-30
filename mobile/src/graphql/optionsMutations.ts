import { gql } from '@apollo/client';

export const PLACE_OPTIONS_ORDER = gql`
  mutation PlaceOptionsOrder(
    $symbol: String!
    $strike: Float!
    $expiration: String!
    $optionType: String!
    $side: String!
    $quantity: Int!
    $orderType: String!
    $limitPrice: Float
    $timeInForce: String!
    $estimatedPremium: Float
  ) {
    placeOptionsOrder(
      symbol: $symbol
      strike: $strike
      expiration: $expiration
      optionType: $optionType
      side: $side
      quantity: $quantity
      orderType: $orderType
      limitPrice: $limitPrice
      timeInForce: $timeInForce
      estimatedPremium: $estimatedPremium
    ) {
      success
      orderId
      alpacaOrderId
      status
      error
    }
  }
`;

export const PLACE_MULTI_LEG_OPTIONS_ORDER = gql`
  mutation PlaceMultiLegOptionsOrder(
    $symbol: String!
    $legs: [JSONString]!
    $strategyName: String
  ) {
    placeMultiLegOptionsOrder(
      symbol: $symbol
      legs: $legs
      strategyName: $strategyName
    ) {
      success
      orderIds
      error
    }
  }
`;

export const CLOSE_OPTIONS_POSITION = gql`
  mutation CloseOptionsPosition(
    $symbol: String!
    $quantity: Int
  ) {
    closeOptionsPosition(
      symbol: $symbol
      quantity: $quantity
    ) {
      success
      orderId
      error
    }
  }
`;

export const TAKE_OPTIONS_PROFITS = gql`
  mutation TakeOptionsProfits(
    $symbol: String!
    $quantity: Int
    $limitPrice: Float
  ) {
    takeOptionsProfits(
      symbol: $symbol
      quantity: $quantity
      limitPrice: $limitPrice
    ) {
      success
      orderId
      error
    }
  }
`;


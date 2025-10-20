import { gql } from '@apollo/client';
// Query to get all portfolios with holdings
export const GET_MY_PORTFOLIOS = gql`
query GetMyPortfolios {
myPortfolios {
totalPortfolios
totalValue
portfolios {
name
totalValue
holdingsCount
holdings {
id
stock {
symbol
}
shares
averagePrice
currentPrice
totalValue
}
}
}
}
`;
// Query to get just portfolio names
export const GET_PORTFOLIO_NAMES = gql`
query GetPortfolioNames {
portfolioNames
}
`;
// Mutation to create a new portfolio
export const CREATE_PORTFOLIO = gql`
mutation CreatePortfolio($portfolioName: String!) {
createPortfolio(portfolioName: $portfolioName) {
success
message
portfolioName
}
}
`;

// Mutation to add a stock to a specific portfolio
export const CREATE_PORTFOLIO_HOLDING = gql`
mutation CreatePortfolioHolding(
$stockId: ID!
$shares: Int!
$portfolioName: String!
$averagePrice: Float
$currentPrice: Float
) {
createPortfolioHolding(
stockId: $stockId
shares: $shares
portfolioName: $portfolioName
averagePrice: $averagePrice
currentPrice: $currentPrice
) {
success
message
holding {
id
stock {
symbol
}
shares
portfolioName
}
}
}
`;
// Mutation to move a holding to a different portfolio
export const UPDATE_PORTFOLIO_HOLDING = gql`
mutation UpdatePortfolioHolding(
$holdingId: ID!
$newPortfolioName: String!
) {
updatePortfolioHolding(
holdingId: $holdingId
newPortfolioName: $newPortfolioName
) {
success
message
holding {
id
stock {
symbol
}
shares
portfolioName
}
}
}
`;
// Mutation to update the number of shares for a holding
export const UPDATE_HOLDING_SHARES = gql`
mutation UpdateHoldingShares(
$holdingId: ID!
$newShares: Int!
) {
updateHoldingShares(
holdingId: $holdingId
newShares: $newShares
) {
success
message
holding {
id
stock {
symbol
}
shares
totalValue
}
}
}
`;
// Mutation to remove a holding from portfolio
export const REMOVE_PORTFOLIO_HOLDING = gql`
mutation RemovePortfolioHolding($holdingId: ID!) {
removePortfolioHolding(holdingId: $holdingId) {
success
message
}
}
`;
// Query to get stocks for portfolio creation
export const GET_STOCKS_FOR_PORTFOLIO = gql`
query GetStocksForPortfolio($search: String) {
stocks(search: $search) {
id
symbol
companyName
currentPrice
}
}
`;

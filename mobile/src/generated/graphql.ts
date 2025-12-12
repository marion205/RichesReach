export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  BigInt: { input: any; output: any; }
  Date: { input: any; output: any; }
  DateTime: { input: string; output: string; }
  Decimal: { input: any; output: any; }
  GenericScalar: { input: any; output: any; }
  JSONString: { input: any; output: any; }
  Time: { input: any; output: any; }
  UUID: { input: any; output: any; }
};

export type AiPortfolioRecommendationType = {
  __typename?: 'AIPortfolioRecommendationType';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  expectedPortfolioReturn?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  portfolioAllocation?: Maybe<Scalars['JSONString']['output']>;
  recommendedStocks?: Maybe<Array<Maybe<StockRecommendationType>>>;
  riskAssessment?: Maybe<Scalars['String']['output']>;
  riskProfile?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

/** AI predictions for a symbol */
export type AiPredictionsType = {
  __typename?: 'AIPredictionsType';
  predictions: Array<Maybe<PredictionType>>;
  sentimentAnalysis?: Maybe<SentimentAnalysisType>;
  symbol: Scalars['String']['output'];
  technicalAnalysis?: Maybe<TechnicalAnalysisType>;
};

/** AI-powered investment recommendation */
export type AiRecommendationType = {
  __typename?: 'AIRecommendationType';
  companyName?: Maybe<Scalars['String']['output']>;
  confidence?: Maybe<Scalars['Float']['output']>;
  consumerStrengthScore?: Maybe<Scalars['Float']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  currentReturn?: Maybe<Scalars['Float']['output']>;
  earningsScore?: Maybe<Scalars['Float']['output']>;
  expectedReturn?: Maybe<Scalars['Float']['output']>;
  insiderScore?: Maybe<Scalars['Float']['output']>;
  mlScore?: Maybe<Scalars['Float']['output']>;
  optionsFlowScore?: Maybe<Scalars['Float']['output']>;
  reasoning?: Maybe<Scalars['String']['output']>;
  recommendation?: Maybe<Scalars['String']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  spendingGrowth?: Maybe<Scalars['Float']['output']>;
  suggestedExitPrice?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  targetPrice?: Maybe<Scalars['Float']['output']>;
};

/** Complete AI recommendations package */
export type AiRecommendationsType = {
  __typename?: 'AIRecommendationsType';
  buyRecommendations?: Maybe<Array<Maybe<AiRecommendationType>>>;
  marketOutlook?: Maybe<MarketOutlookType>;
  portfolioAnalysis?: Maybe<PortfolioAnalysisType>;
  rebalanceSuggestions?: Maybe<Array<Maybe<RebalanceSuggestionType>>>;
  riskAssessment?: Maybe<RiskAssessmentType>;
  sellRecommendations?: Maybe<Array<Maybe<AiRecommendationType>>>;
  spendingInsights?: Maybe<SpendingInsightsType>;
};

/** Filters for AI Scans query */
export type AiScanFilters = {
  category?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  riskLevel?: InputMaybe<Scalars['String']['input']>;
  tags?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  timeHorizon?: InputMaybe<Scalars['String']['input']>;
};

/** AI Market Scan definition */
export type AiScanType = {
  __typename?: 'AIScanType';
  category?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isActive?: Maybe<Scalars['Boolean']['output']>;
  lastRun?: Maybe<Scalars['String']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  performance?: Maybe<PerformanceType>;
  playbook?: Maybe<PlaybookType>;
  results?: Maybe<Array<Maybe<ScanResultType>>>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  timeHorizon?: Maybe<Scalars['String']['output']>;
  version?: Maybe<Scalars['String']['output']>;
};

/** Activity feed item */
export type ActivityFeedItemType = {
  __typename?: 'ActivityFeedItemType';
  content?: Maybe<Scalars['JSONString']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
  userId?: Maybe<Scalars['Int']['output']>;
  userName?: Maybe<Scalars['String']['output']>;
};

/** Add a stock to user's watchlist */
export type AddToWatchlist = {
  __typename?: 'AddToWatchlist';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Alpaca crypto account type */
export type AlpacaCryptoAccountType = {
  __typename?: 'AlpacaCryptoAccountType';
  alpacaCryptoAccountId?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isApproved?: Maybe<Scalars['Boolean']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  totalCryptoValue?: Maybe<Scalars['Float']['output']>;
  usdBalance?: Maybe<Scalars['Float']['output']>;
};

/** Alpaca crypto balance type */
export type AlpacaCryptoBalanceType = {
  __typename?: 'AlpacaCryptoBalanceType';
  availableAmount?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  totalAmount?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['String']['output']>;
  usdValue?: Maybe<Scalars['Float']['output']>;
};

/** Alpaca crypto order type */
export type AlpacaCryptoOrderType = {
  __typename?: 'AlpacaCryptoOrderType';
  createdAt?: Maybe<Scalars['String']['output']>;
  filledAt?: Maybe<Scalars['String']['output']>;
  filledAvgPrice?: Maybe<Scalars['Float']['output']>;
  filledQty?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  limitPrice?: Maybe<Scalars['Float']['output']>;
  notional?: Maybe<Scalars['Float']['output']>;
  qty?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  stopPrice?: Maybe<Scalars['Float']['output']>;
  submittedAt?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  timeInForce?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for AutoTradingSettings */
export type AutoTradingSettingsType = {
  __typename?: 'AutoTradingSettingsType';
  allowedSymbols?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  blockedSymbols?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  createdAt: Scalars['DateTime']['output'];
  /** Enable/disable auto-trading for all strategies */
  enabled: Scalars['Boolean']['output'];
  /** Fixed position size in dollars (for FIXED method) */
  fixedPositionSize: Scalars['Decimal']['output'];
  id: Scalars['UUID']['output'];
  /** Maximum number of concurrent positions (0 = unlimited) */
  maxConcurrentPositions: Scalars['Int']['output'];
  /** Maximum daily loss percentage before auto-trading stops (0 = disabled) */
  maxDailyLossPercent: Scalars['Decimal']['output'];
  /** Maximum position size as percentage of equity */
  maxPositionSizePercent: Scalars['Decimal']['output'];
  /** Minimum confidence score to auto-execute (0.00-1.00) */
  minConfidenceThreshold: Scalars['Decimal']['output'];
  /** Only execute trades during market hours (9:30 AM - 4:00 PM ET) */
  onlyTradeMarketHours: Scalars['Boolean']['output'];
  /** Position size as percentage of account equity (for PERCENTAGE method) */
  positionSizePercent: Scalars['Decimal']['output'];
  /** Method for calculating position size */
  positionSizingMethod: CoreAutoTradingSettingsPositionSizingMethodChoices;
  /** Risk per trade as percentage of equity (for RISK_BASED method) */
  riskPerTradePercent: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

/** Bandit strategy context */
export type BanditContextType = {
  __typename?: 'BanditContextType';
  marketTrend?: Maybe<Scalars['String']['output']>;
  timeOfDay?: Maybe<Scalars['String']['output']>;
  vixLevel?: Maybe<Scalars['Float']['output']>;
  volatilityRegime?: Maybe<Scalars['String']['output']>;
};

/** Bandit performance by strategy */
export type BanditPerformanceType = {
  __typename?: 'BanditPerformanceType';
  breakout?: Maybe<BanditStrategyType>;
  etfRotation?: Maybe<BanditStrategyType>;
  meanReversion?: Maybe<BanditStrategyType>;
  momentum?: Maybe<BanditStrategyType>;
};

/** Bandit strategy selection result */
export type BanditStrategyResultType = {
  __typename?: 'BanditStrategyResultType';
  context?: Maybe<BanditContextType>;
  performance?: Maybe<BanditPerformanceType>;
  selectedStrategy?: Maybe<Scalars['String']['output']>;
};

/** Bandit strategy performance */
export type BanditStrategyType = {
  __typename?: 'BanditStrategyType';
  alpha?: Maybe<Scalars['Float']['output']>;
  beta?: Maybe<Scalars['Float']['output']>;
  confidence?: Maybe<Scalars['Float']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** Bandit performance by strategy */
export type BanditType = {
  __typename?: 'BanditType';
  breakout?: Maybe<BanditStrategyType>;
  etfRotation?: Maybe<BanditStrategyType>;
  meanReversion?: Maybe<BanditStrategyType>;
  momentum?: Maybe<BanditStrategyType>;
};

/** GraphQL type for bank account */
export type BankAccountType = {
  __typename?: 'BankAccountType';
  accountSubtype?: Maybe<Scalars['String']['output']>;
  accountType?: Maybe<Scalars['String']['output']>;
  balanceAvailable?: Maybe<Scalars['Float']['output']>;
  balanceCurrent?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  currency: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  isPrimary?: Maybe<Scalars['Boolean']['output']>;
  isVerified?: Maybe<Scalars['Boolean']['output']>;
  lastUpdated?: Maybe<Scalars['String']['output']>;
  mask: Scalars['String']['output'];
  name: Scalars['String']['output'];
  provider: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** GraphQL type for bank provider account */
export type BankProviderAccountType = {
  __typename?: 'BankProviderAccountType';
  createdAt: Scalars['DateTime']['output'];
  errorMessage: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  lastRefresh?: Maybe<Scalars['DateTime']['output']>;
  providerId: Scalars['String']['output'];
  providerName: Scalars['String']['output'];
  status: CoreBankProviderAccountStatusChoices;
  updatedAt: Scalars['DateTime']['output'];
};

/** GraphQL type for bank transaction */
export type BankTransactionType = {
  __typename?: 'BankTransactionType';
  amount?: Maybe<Scalars['Float']['output']>;
  category: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  currency: Scalars['String']['output'];
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  merchantName: Scalars['String']['output'];
  postedDate: Scalars['Date']['output'];
  status: CoreBankTransactionStatusChoices;
  subcategory: Scalars['String']['output'];
  transactionDate?: Maybe<Scalars['Date']['output']>;
  transactionType: CoreBankTransactionTransactionTypeChoices;
  updatedAt: Scalars['DateTime']['output'];
};

/** Individual data point in a benchmark series */
export type BenchmarkDataPointType = {
  __typename?: 'BenchmarkDataPointType';
  change?: Maybe<Scalars['Float']['output']>;
  changePercent?: Maybe<Scalars['Float']['output']>;
  timestamp: Scalars['String']['output'];
  value: Scalars['Float']['output'];
};

/** Benchmark series data for a given symbol and timeframe */
export type BenchmarkSeriesType = {
  __typename?: 'BenchmarkSeriesType';
  dataPoints: Array<Maybe<BenchmarkDataPointType>>;
  endValue: Scalars['Float']['output'];
  name: Scalars['String']['output'];
  startValue: Scalars['Float']['output'];
  symbol: Scalars['String']['output'];
  timeframe: Scalars['String']['output'];
  totalReturn: Scalars['Float']['output'];
  totalReturnPercent: Scalars['Float']['output'];
  volatility?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for bracket order legs */
export type BracketLegsType = {
  __typename?: 'BracketLegsType';
  /** Suggested order structure */
  orderStructure?: Maybe<Scalars['JSONString']['output']>;
  stop?: Maybe<Scalars['Float']['output']>;
  target1?: Maybe<Scalars['Float']['output']>;
  target2?: Maybe<Scalars['Float']['output']>;
};

export type BrokerAccountType = {
  __typename?: 'BrokerAccountType';
  accountNumber?: Maybe<Scalars['String']['output']>;
  activities: Array<BrokerActivityType>;
  alpacaAccountId?: Maybe<Scalars['String']['output']>;
  approvalReason?: Maybe<Scalars['String']['output']>;
  approvedAt?: Maybe<Scalars['DateTime']['output']>;
  buyingPower: Scalars['Decimal']['output'];
  cash: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  dayTradeCount: Scalars['Int']['output'];
  dayTradingBuyingPower: Scalars['Decimal']['output'];
  equity: Scalars['Decimal']['output'];
  fundingRecords: Array<BrokerFundingType>;
  id: Scalars['ID']['output'];
  kycStatus: CoreBrokerAccountKycStatusChoices;
  orders: Array<BrokerOrderType>;
  patternDayTrader: Scalars['Boolean']['output'];
  positions: Array<BrokerPositionType>;
  status?: Maybe<Scalars['String']['output']>;
  suitabilityFlags: Scalars['JSONString']['output'];
  tradingBlocked: Scalars['Boolean']['output'];
  transferBlocked: Scalars['Boolean']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

export type BrokerActivityType = {
  __typename?: 'BrokerActivityType';
  activityId: Scalars['String']['output'];
  activityType: CoreBrokerActivityActivityTypeChoices;
  brokerAccount: BrokerAccountType;
  createdAt: Scalars['DateTime']['output'];
  date: Scalars['Date']['output'];
  id: Scalars['ID']['output'];
  netAmount?: Maybe<Scalars['Decimal']['output']>;
  perShareAmount?: Maybe<Scalars['Decimal']['output']>;
  qty?: Maybe<Scalars['Int']['output']>;
  rawData: Scalars['JSONString']['output'];
  symbol?: Maybe<Scalars['String']['output']>;
};

export type BrokerFundingType = {
  __typename?: 'BrokerFundingType';
  achRelationshipId?: Maybe<Scalars['String']['output']>;
  alpacaTransferId?: Maybe<Scalars['String']['output']>;
  amount: Scalars['Decimal']['output'];
  bankLinkId?: Maybe<Scalars['String']['output']>;
  brokerAccount: BrokerAccountType;
  createdAt: Scalars['DateTime']['output'];
  estimatedSettlementDate?: Maybe<Scalars['Date']['output']>;
  id: Scalars['ID']['output'];
  microDepositVerified: Scalars['Boolean']['output'];
  settlementDate?: Maybe<Scalars['Date']['output']>;
  status: CoreBrokerFundingStatusChoices;
  transferType: CoreBrokerFundingTransferTypeChoices;
  updatedAt: Scalars['DateTime']['output'];
};

export type BrokerOrderType = {
  __typename?: 'BrokerOrderType';
  alpacaOrderId?: Maybe<Scalars['String']['output']>;
  alpacaResponse?: Maybe<Scalars['JSONString']['output']>;
  brokerAccount: BrokerAccountType;
  clientOrderId: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  filledAt?: Maybe<Scalars['DateTime']['output']>;
  filledAvgPrice?: Maybe<Scalars['Decimal']['output']>;
  filledQty: Scalars['Int']['output'];
  fills?: Maybe<Scalars['JSONString']['output']>;
  guardrailChecksPassed: Scalars['Boolean']['output'];
  guardrailRejectReason?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  limitPrice?: Maybe<Scalars['Decimal']['output']>;
  notional?: Maybe<Scalars['Decimal']['output']>;
  orderType: CoreBrokerOrderOrderTypeChoices;
  quantity: Scalars['Int']['output'];
  /** RAHA signal that triggered this order (if auto-traded) */
  rahaSignal?: Maybe<RahaSignalType>;
  rejectionReason?: Maybe<Scalars['String']['output']>;
  side: CoreBrokerOrderSideChoices;
  /** Order source: 'MANUAL', 'RAHA_AUTO', etc. */
  source?: Maybe<Scalars['String']['output']>;
  status: CoreBrokerOrderStatusChoices;
  stopPrice?: Maybe<Scalars['Decimal']['output']>;
  submittedAt?: Maybe<Scalars['DateTime']['output']>;
  symbol: Scalars['String']['output'];
  timeInForce: CoreBrokerOrderTimeInForceChoices;
  updatedAt: Scalars['DateTime']['output'];
};

export type BrokerPositionType = {
  __typename?: 'BrokerPositionType';
  avgEntryPrice: Scalars['Decimal']['output'];
  brokerAccount: BrokerAccountType;
  costBasis: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentPrice?: Maybe<Scalars['Decimal']['output']>;
  id: Scalars['ID']['output'];
  lastSyncedAt?: Maybe<Scalars['DateTime']['output']>;
  marketValue: Scalars['Decimal']['output'];
  qty: Scalars['Int']['output'];
  symbol: Scalars['String']['output'];
  unrealizedPl: Scalars['Decimal']['output'];
  unrealizedPlpc: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** Result of canceling Alpaca crypto order */
export type CancelAlpacaCryptoOrderResultType = {
  __typename?: 'CancelAlpacaCryptoOrderResultType';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Cancel a paper trading order */
export type CancelPaperOrder = {
  __typename?: 'CancelPaperOrder';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Cancel premium subscription */
export type CancelPremiumSubscription = {
  __typename?: 'CancelPremiumSubscription';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Change password for authenticated user */
export type ChangePassword = {
  __typename?: 'ChangePassword';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Type for a single chart data point (OHLCV) */
export type ChartDataPointType = {
  __typename?: 'ChartDataPointType';
  close: Scalars['Float']['output'];
  high: Scalars['Float']['output'];
  low: Scalars['Float']['output'];
  open: Scalars['Float']['output'];
  timestamp: Scalars['String']['output'];
  volume: Scalars['Int']['output'];
};

/** Enum for chart time ranges */
export enum ChartRangeEnum {
  ONE_MONTH = 'ONE_MONTH',
  ONE_YEAR = 'ONE_YEAR',
  SIX_MONTHS = 'SIX_MONTHS',
  THREE_MONTHS = 'THREE_MONTHS',
  YEAR_TO_DATE = 'YEAR_TO_DATE'
}

export type ChatMessageType = {
  __typename?: 'ChatMessageType';
  content: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  role: CoreChatMessageRoleChoices;
  session: ChatSessionType;
};

export type ChatSessionType = {
  __typename?: 'ChatSessionType';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  messages: Array<ChatMessageType>;
  user: UserType;
};

/** Close an options position (sell to close) */
export type CloseOptionsPosition = {
  __typename?: 'CloseOptionsPosition';
  error?: Maybe<Scalars['String']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Add a comment to a swing trading signal */
export type CommentSignal = {
  __typename?: 'CommentSignal';
  commentId?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type CommentType = {
  __typename?: 'CommentType';
  content: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  post: PostType;
  user: UserType;
};

/** Complete a KYC workflow */
export type CompleteKycWorkflow = {
  __typename?: 'CompleteKycWorkflow';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  nextSteps?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** GraphQL type for quest completion criteria */
export type CompletionCriteriaType = {
  __typename?: 'CompletionCriteriaType';
  scenariosCompleted?: Maybe<Scalars['Int']['output']>;
  successRate?: Maybe<Scalars['Float']['output']>;
};

/** Enhanced Consumer Strength Score with historical tracking */
export type ConsumerStrengthType = {
  __typename?: 'ConsumerStrengthType';
  components?: Maybe<Scalars['JSONString']['output']>;
  earningsScore?: Maybe<Scalars['Float']['output']>;
  historicalTrend?: Maybe<Scalars['String']['output']>;
  insiderScore?: Maybe<Scalars['Float']['output']>;
  optionsScore?: Maybe<Scalars['Float']['output']>;
  overallScore?: Maybe<Scalars['Float']['output']>;
  sectorScore?: Maybe<Scalars['Float']['output']>;
  spendingGrowth?: Maybe<Scalars['Float']['output']>;
  spendingScore?: Maybe<Scalars['Float']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** Copied trade result */
export type CopiedTradeType = {
  __typename?: 'CopiedTradeType';
  id?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  quantity?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** Copy trade mutation result */
export type CopyTradeResultType = {
  __typename?: 'CopyTradeResultType';
  copiedTrade?: Maybe<CopiedTradeType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** An enumeration. */
export enum CoreAutoTradingSettingsPositionSizingMethodChoices {
  /** Fixed Dollar Amount */
  FIXED = 'FIXED',
  /** Percentage of Equity */
  PERCENTAGE = 'PERCENTAGE',
  /** Risk-Based (R-Multiple) */
  RISK_BASED = 'RISK_BASED'
}

/** An enumeration. */
export enum CoreBankProviderAccountStatusChoices {
  /** Active */
  ACTIVE = 'ACTIVE',
  /** Deleted */
  DELETED = 'DELETED',
  /** Error */
  ERROR = 'ERROR',
  /** Inactive */
  INACTIVE = 'INACTIVE'
}

/** An enumeration. */
export enum CoreBankTransactionStatusChoices {
  /** Cancelled */
  CANCELLED = 'CANCELLED',
  /** Pending */
  PENDING = 'PENDING',
  /** Posted */
  POSTED = 'POSTED'
}

/** An enumeration. */
export enum CoreBankTransactionTransactionTypeChoices {
  /** Credit */
  CREDIT = 'CREDIT',
  /** Debit */
  DEBIT = 'DEBIT'
}

/** An enumeration. */
export enum CoreBrokerAccountKycStatusChoices {
  /** Approval Pending */
  APPROVAL_PENDING = 'APPROVAL_PENDING',
  /** Approved */
  APPROVED = 'APPROVED',
  /** Information Required */
  INFO_REQUIRED = 'INFO_REQUIRED',
  /** Not Started */
  NOT_STARTED = 'NOT_STARTED',
  /** Rejected */
  REJECTED = 'REJECTED',
  /** Submitted */
  SUBMITTED = 'SUBMITTED'
}

/** An enumeration. */
export enum CoreBrokerActivityActivityTypeChoices {
  /** Cash Settlement */
  CSD = 'CSD',
  /** Cash Receipt */
  CSR = 'CSR',
  /** Cash Withdrawal */
  CSW = 'CSW',
  /** Dividend */
  DIV = 'DIV',
  /** Fee */
  FEE = 'FEE',
  /** Fill */
  FILL = 'FILL',
  /** Interest */
  INT = 'INT',
  /** Journal (Cash) */
  JNLC = 'JNLC',
  /** Journal (Stock) */
  JNLS = 'JNLS',
  /** Journal */
  JRN = 'JRN',
  /** Transfer */
  TRANS = 'TRANS'
}

/** An enumeration. */
export enum CoreBrokerFundingStatusChoices {
  /** Completed */
  COMPLETED = 'COMPLETED',
  /** Failed */
  FAILED = 'FAILED',
  /** Pending */
  PENDING = 'PENDING',
  /** Processing */
  PROCESSING = 'PROCESSING',
  /** Reversed */
  REVERSED = 'REVERSED'
}

/** An enumeration. */
export enum CoreBrokerFundingTransferTypeChoices {
  /** Deposit */
  DEPOSIT = 'DEPOSIT',
  /** Withdrawal */
  WITHDRAWAL = 'WITHDRAWAL'
}

/** An enumeration. */
export enum CoreBrokerOrderOrderTypeChoices {
  /** Limit */
  LIMIT = 'LIMIT',
  /** Market */
  MARKET = 'MARKET',
  /** Stop */
  STOP = 'STOP',
  /** Stop Limit */
  STOP_LIMIT = 'STOP_LIMIT',
  /** Trailing Stop */
  TRAILING_STOP = 'TRAILING_STOP'
}

/** An enumeration. */
export enum CoreBrokerOrderSideChoices {
  /** Buy */
  BUY = 'BUY',
  /** Sell */
  SELL = 'SELL'
}

/** An enumeration. */
export enum CoreBrokerOrderStatusChoices {
  /** Accepted */
  ACCEPTED = 'ACCEPTED',
  /** Canceled */
  CANCELED = 'CANCELED',
  /** Done For Day */
  DONE_FOR_DAY = 'DONE_FOR_DAY',
  /** Expired */
  EXPIRED = 'EXPIRED',
  /** Filled */
  FILLED = 'FILLED',
  /** New */
  NEW = 'NEW',
  /** Partially Filled */
  PARTIALLY_FILLED = 'PARTIALLY_FILLED',
  /** Pending Cancel */
  PENDING_CANCEL = 'PENDING_CANCEL',
  /** Pending New */
  PENDING_NEW = 'PENDING_NEW',
  /** Pending Replace */
  PENDING_REPLACE = 'PENDING_REPLACE',
  /** Rejected */
  REJECTED = 'REJECTED',
  /** Replaced */
  REPLACED = 'REPLACED',
  /** Stopped */
  STOPPED = 'STOPPED'
}

/** An enumeration. */
export enum CoreBrokerOrderTimeInForceChoices {
  /** Closing */
  CLS = 'CLS',
  /** Day */
  DAY = 'DAY',
  /** Fill or Kill */
  FOK = 'FOK',
  /** Good Till Canceled */
  GTC = 'GTC',
  /** Immediate or Cancel */
  IOC = 'IOC',
  /** Opening */
  OPG = 'OPG'
}

/** An enumeration. */
export enum CoreChatMessageRoleChoices {
  /** Assistant */
  ASSISTANT = 'ASSISTANT',
  /** System */
  SYSTEM = 'SYSTEM',
  /** User */
  USER = 'USER'
}

/** An enumeration. */
export enum CorePaperTradingOrderOrderTypeChoices {
  /** Limit */
  LIMIT = 'LIMIT',
  /** Market */
  MARKET = 'MARKET',
  /** Stop */
  STOP = 'STOP',
  /** Stop Limit */
  STOP_LIMIT = 'STOP_LIMIT'
}

/** An enumeration. */
export enum CorePaperTradingOrderSideChoices {
  /** Buy */
  BUY = 'BUY',
  /** Sell */
  SELL = 'SELL'
}

/** An enumeration. */
export enum CorePaperTradingOrderStatusChoices {
  /** Cancelled */
  CANCELLED = 'CANCELLED',
  /** Filled */
  FILLED = 'FILLED',
  /** Pending */
  PENDING = 'PENDING',
  /** Rejected */
  REJECTED = 'REJECTED'
}

/** An enumeration. */
export enum CoreRahaBacktestRunStatusChoices {
  /** Completed */
  COMPLETED = 'COMPLETED',
  /** Failed */
  FAILED = 'FAILED',
  /** Pending */
  PENDING = 'PENDING',
  /** Running */
  RUNNING = 'RUNNING'
}

/** An enumeration. */
export enum CoreRahaSignalSignalTypeChoices {
  /** Entry Long */
  ENTRY_LONG = 'ENTRY_LONG',
  /** Entry Short */
  ENTRY_SHORT = 'ENTRY_SHORT',
  /** Exit */
  EXIT = 'EXIT',
  /** Stop Loss */
  STOP_LOSS = 'STOP_LOSS',
  /** Take Profit */
  TAKE_PROFIT = 'TAKE_PROFIT'
}

/** An enumeration. */
export enum CoreSblocSessionStatusChoices {
  /** Cancelled */
  CANCELLED = 'CANCELLED',
  /** Completed */
  COMPLETED = 'COMPLETED',
  /** Failed */
  FAILED = 'FAILED',
  /** In Progress */
  IN_PROGRESS = 'IN_PROGRESS',
  /** Pending */
  PENDING = 'PENDING'
}

/** An enumeration. */
export enum CoreStrategyCategoryChoices {
  /** Crypto */
  CRYPTO = 'CRYPTO',
  /** Forex */
  FOREX = 'FOREX',
  /** Futures */
  FUTURES = 'FUTURES',
  /** Momentum */
  MOMENTUM = 'MOMENTUM',
  /** Reversal */
  REVERSAL = 'REVERSAL',
  /** Swing */
  SWING = 'SWING'
}

/** An enumeration. */
export enum CoreStrategyMarketTypeChoices {
  /** Crypto */
  CRYPTO = 'CRYPTO',
  /** Forex */
  FOREX = 'FOREX',
  /** Futures */
  FUTURES = 'FUTURES',
  /** Options */
  OPTIONS = 'OPTIONS',
  /** Stocks */
  STOCKS = 'STOCKS'
}

/** Rust engine correlation analysis */
export type CorrelationAnalysisType = {
  __typename?: 'CorrelationAnalysisType';
  btcDominance?: Maybe<Scalars['Float']['output']>;
  correlation1d?: Maybe<Scalars['Float']['output']>;
  correlation7d?: Maybe<Scalars['Float']['output']>;
  correlation30d?: Maybe<Scalars['Float']['output']>;
  primarySymbol?: Maybe<Scalars['String']['output']>;
  regime?: Maybe<Scalars['String']['output']>;
  secondarySymbol?: Maybe<Scalars['String']['output']>;
  spyCorrelation?: Maybe<Scalars['Float']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** Result of creating Alpaca crypto order */
export type CreateAlpacaCryptoOrderResultType = {
  __typename?: 'CreateAlpacaCryptoOrderResultType';
  createdAt?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** Create/update broker account for KYC onboarding */
export type CreateBrokerAccount = {
  __typename?: 'CreateBrokerAccount';
  accountId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  kycStatus?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a brokerage account as part of KYC */
export type CreateBrokerageAccount = {
  __typename?: 'CreateBrokerageAccount';
  accountId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type CreateChatSession = {
  __typename?: 'CreateChatSession';
  message?: Maybe<Scalars['String']['output']>;
  session?: Maybe<ChatSessionType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type CreateComment = {
  __typename?: 'CreateComment';
  comment?: Maybe<CommentType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a custom user strategy */
export type CreateCustomStrategy = {
  __typename?: 'CreateCustomStrategy';
  message?: Maybe<Scalars['String']['output']>;
  strategy?: Maybe<StrategyType>;
  strategyVersion?: Maybe<StrategyVersionType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a comment on a discussion (Reddit-style) */
export type CreateDiscussionComment = {
  __typename?: 'CreateDiscussionComment';
  comment?: Maybe<DiscussionCommentType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create or update user's income profile */
export type CreateIncomeProfile = {
  __typename?: 'CreateIncomeProfile';
  incomeProfile?: Maybe<IncomeProfileType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create an options alert */
export type CreateOptionsAlert = {
  __typename?: 'CreateOptionsAlert';
  alert?: Maybe<OptionsAlertType>;
  error?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Add a stock holding to a specific portfolio */
export type CreatePortfolioHolding = {
  __typename?: 'CreatePortfolioHolding';
  holding?: Maybe<PortfolioHoldingType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type CreatePost = {
  __typename?: 'CreatePost';
  message?: Maybe<Scalars['String']['output']>;
  post?: Maybe<PostType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a new SBLOC application session */
export type CreateSblocSession = {
  __typename?: 'CreateSBLOCSession';
  applicationUrl?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  sessionId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a new stock discussion post (Reddit-style) */
export type CreateStockDiscussion = {
  __typename?: 'CreateStockDiscussion';
  discussion?: Maybe<StockDiscussionType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Create a new strategy blend with custom weights */
export type CreateStrategyBlend = {
  __typename?: 'CreateStrategyBlend';
  blend?: Maybe<StrategyBlendType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Enhanced user creation with security features */
export type CreateUser = {
  __typename?: 'CreateUser';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  user?: Maybe<UserType>;
};

/** GraphQL type for crypto holding */
export type CryptoHoldingType = {
  __typename?: 'CryptoHoldingType';
  averageCost?: Maybe<Scalars['Float']['output']>;
  collateralValue?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  cryptocurrency?: Maybe<CryptocurrencyType>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  currentValue?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isCollateralized?: Maybe<Scalars['Boolean']['output']>;
  loanAmount?: Maybe<Scalars['Float']['output']>;
  quantity?: Maybe<Scalars['Float']['output']>;
  stakedQuantity?: Maybe<Scalars['Float']['output']>;
  stakingApy?: Maybe<Scalars['Float']['output']>;
  stakingRewards?: Maybe<Scalars['Float']['output']>;
  unrealizedPnl?: Maybe<Scalars['Float']['output']>;
  unrealizedPnlPercentage?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for crypto ML signal */
export type CryptoMlSignalType = {
  __typename?: 'CryptoMlSignalType';
  confidenceLevel?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  expiresAt?: Maybe<Scalars['String']['output']>;
  explanation?: Maybe<Scalars['String']['output']>;
  featuresUsed?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  predictionType?: Maybe<Scalars['String']['output']>;
  probability?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for crypto portfolio */
export type CryptoPortfolioType = {
  __typename?: 'CryptoPortfolioType';
  createdAt?: Maybe<Scalars['String']['output']>;
  diversificationScore?: Maybe<Scalars['Float']['output']>;
  holdings?: Maybe<Array<Maybe<CryptoHoldingType>>>;
  id?: Maybe<Scalars['String']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  portfolioVolatility?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  topHoldingPercentage?: Maybe<Scalars['Float']['output']>;
  totalCostBasis?: Maybe<Scalars['Float']['output']>;
  totalPnl?: Maybe<Scalars['Float']['output']>;
  totalPnlPercentage?: Maybe<Scalars['Float']['output']>;
  totalValueUsd?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for crypto price */
export type CryptoPriceType = {
  __typename?: 'CryptoPriceType';
  id?: Maybe<Scalars['String']['output']>;
  marketCap?: Maybe<Scalars['Float']['output']>;
  momentumScore?: Maybe<Scalars['Float']['output']>;
  priceBtc?: Maybe<Scalars['Float']['output']>;
  priceChange24h?: Maybe<Scalars['Float']['output']>;
  priceChangePercentage24h?: Maybe<Scalars['Float']['output']>;
  priceUsd?: Maybe<Scalars['Float']['output']>;
  rsi14?: Maybe<Scalars['Float']['output']>;
  sentimentScore?: Maybe<Scalars['Float']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  volatility7d?: Maybe<Scalars['Float']['output']>;
  volatility30d?: Maybe<Scalars['Float']['output']>;
  volume24h?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for crypto recommendation */
export type CryptoRecommendationType = {
  __typename?: 'CryptoRecommendationType';
  confidenceLevel?: Maybe<Scalars['String']['output']>;
  liquidity24hUsd?: Maybe<Scalars['Float']['output']>;
  priceUsd?: Maybe<Scalars['Float']['output']>;
  probability?: Maybe<Scalars['Float']['output']>;
  rationale?: Maybe<Scalars['String']['output']>;
  recommendation?: Maybe<Scalars['String']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  volatilityTier?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for crypto SBLOC loan */
export type CryptoSblocLoanType = {
  __typename?: 'CryptoSblocLoanType';
  collateralQuantity?: Maybe<Scalars['Float']['output']>;
  collateralValueAtLoan?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  cryptocurrency?: Maybe<CryptocurrencyType>;
  id?: Maybe<Scalars['String']['output']>;
  interestRate?: Maybe<Scalars['Float']['output']>;
  liquidationThreshold?: Maybe<Scalars['Float']['output']>;
  loanAmount?: Maybe<Scalars['Float']['output']>;
  maintenanceMargin?: Maybe<Scalars['Float']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for cryptocurrency */
export type CryptocurrencyType = {
  __typename?: 'CryptocurrencyType';
  coingeckoId?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isSecCompliant?: Maybe<Scalars['Boolean']['output']>;
  isStakingAvailable?: Maybe<Scalars['Boolean']['output']>;
  minTradeAmount?: Maybe<Scalars['Float']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  precision?: Maybe<Scalars['Int']['output']>;
  regulatoryStatus?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  volatilityTier?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for daily quest */
export type DailyQuestType = {
  __typename?: 'DailyQuestType';
  completionCriteria?: Maybe<CompletionCriteriaType>;
  description?: Maybe<Scalars['String']['output']>;
  difficulty?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  questType?: Maybe<Scalars['String']['output']>;
  regimeContext?: Maybe<Scalars['String']['output']>;
  requiredSkills?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  timeLimitMinutes?: Maybe<Scalars['Int']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  voiceNarration?: Maybe<Scalars['String']['output']>;
  xpReward?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for day trading picks data */
export type DayTradingDataType = {
  __typename?: 'DayTradingDataType';
  asOf?: Maybe<Scalars['String']['output']>;
  /** Symbols that failed data fetching (API issues, market closed, etc.) */
  failedDataFetch?: Maybe<Scalars['Int']['output']>;
  /** Symbols filtered out by microstructure/execution quality */
  filteredByMicrostructure?: Maybe<Scalars['Int']['output']>;
  /** Symbols filtered out by momentum requirements */
  filteredByMomentum?: Maybe<Scalars['Int']['output']>;
  /** Symbols filtered out by volatility constraints */
  filteredByVolatility?: Maybe<Scalars['Int']['output']>;
  mode?: Maybe<Scalars['String']['output']>;
  /** Symbols that passed liquidity/volume filters */
  passedLiquidity?: Maybe<Scalars['Int']['output']>;
  /** Symbols that passed quality threshold */
  passedQuality?: Maybe<Scalars['Int']['output']>;
  picks?: Maybe<Array<Maybe<DayTradingPickType>>>;
  qualityThreshold?: Maybe<Scalars['Float']['output']>;
  /** Total symbols scanned from universe */
  scannedCount?: Maybe<Scalars['Int']['output']>;
  universeSize?: Maybe<Scalars['Int']['output']>;
  universeSource?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for day trading features */
export type DayTradingFeaturesType = {
  __typename?: 'DayTradingFeaturesType';
  /** Total ask depth in dollars (top 5 levels) */
  askDepth?: Maybe<Scalars['Float']['output']>;
  /** Total bid depth in dollars (top 5 levels) */
  bidDepth?: Maybe<Scalars['Float']['output']>;
  breakoutPct?: Maybe<Scalars['Float']['output']>;
  catalystScore?: Maybe<Scalars['Float']['output']>;
  /** Depth imbalance: (bid_depth - ask_depth) / total */
  depthImbalance?: Maybe<Scalars['Float']['output']>;
  /** Execution quality score: 0-10 (higher = better) */
  executionQualityScore?: Maybe<Scalars['Float']['output']>;
  /** True if execution quality is low (thin depth, wide spread) */
  microstructureRisky?: Maybe<Scalars['Boolean']['output']>;
  momentum15m?: Maybe<Scalars['Float']['output']>;
  /** Order imbalance: -1 (bearish) to +1 (bullish) */
  orderImbalance?: Maybe<Scalars['Float']['output']>;
  rvol10m?: Maybe<Scalars['Float']['output']>;
  spreadBps?: Maybe<Scalars['Float']['output']>;
  vwapDist?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for a day trading pick */
export type DayTradingPickType = {
  __typename?: 'DayTradingPickType';
  features?: Maybe<DayTradingFeaturesType>;
  notes?: Maybe<Scalars['String']['output']>;
  risk?: Maybe<DayTradingRiskType>;
  score?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for day trading risk metrics */
export type DayTradingRiskType = {
  __typename?: 'DayTradingRiskType';
  atr5m?: Maybe<Scalars['Float']['output']>;
  sizeShares?: Maybe<Scalars['Int']['output']>;
  stop?: Maybe<Scalars['Float']['output']>;
  targets?: Maybe<Array<Maybe<Scalars['Float']['output']>>>;
  timeStopMin?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for day trading strategy performance stats */
export type DayTradingStatsType = {
  __typename?: 'DayTradingStatsType';
  asOf?: Maybe<Scalars['String']['output']>;
  avgPnlPerSignal?: Maybe<Scalars['Float']['output']>;
  calmarRatio?: Maybe<Scalars['Float']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  mode?: Maybe<Scalars['String']['output']>;
  period?: Maybe<Scalars['String']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  signalsEvaluated?: Maybe<Scalars['Int']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  totalPnlPercent?: Maybe<Scalars['Float']['output']>;
  totalSignals?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** DeFi account information */
export type DefiAccountType = {
  __typename?: 'DefiAccountType';
  availableBorrowUsd?: Maybe<Scalars['Float']['output']>;
  borrows?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  collateralUsd?: Maybe<Scalars['Float']['output']>;
  debtUsd?: Maybe<Scalars['Float']['output']>;
  healthFactor?: Maybe<Scalars['Float']['output']>;
  liqThresholdWeighted?: Maybe<Scalars['Float']['output']>;
  ltvWeighted?: Maybe<Scalars['Float']['output']>;
  supplies?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
};

/** Borrow assets from DeFi protocol */
export type DefiBorrow = {
  __typename?: 'DefiBorrow';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** DeFi position information */
export type DefiPositionType = {
  __typename?: 'DefiPositionType';
  quantity?: Maybe<Scalars['Float']['output']>;
  useAsCollateral?: Maybe<Scalars['Boolean']['output']>;
};

/** DeFi reserve information */
export type DefiReserveType = {
  __typename?: 'DefiReserveType';
  canBeCollateral?: Maybe<Scalars['Boolean']['output']>;
  liquidationThreshold?: Maybe<Scalars['Float']['output']>;
  ltv?: Maybe<Scalars['Float']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  stableBorrowApy?: Maybe<Scalars['Float']['output']>;
  supplyApy?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  variableBorrowApy?: Maybe<Scalars['Float']['output']>;
};

/** Supply assets to DeFi protocol */
export type DefiSupply = {
  __typename?: 'DefiSupply';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  position?: Maybe<DefiPositionType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type DeleteComment = {
  __typename?: 'DeleteComment';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Delete a custom user strategy */
export type DeleteCustomStrategy = {
  __typename?: 'DeleteCustomStrategy';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Delete an options alert */
export type DeleteOptionsAlert = {
  __typename?: 'DeleteOptionsAlert';
  error?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Delete a strategy blend */
export type DeleteStrategyBlend = {
  __typename?: 'DeleteStrategyBlend';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Disable a strategy for a user */
export type DisableStrategy = {
  __typename?: 'DisableStrategy';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type DiscussionCommentType = {
  __typename?: 'DiscussionCommentType';
  content: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  discussion: StockDiscussionType;
  downvotes: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  isDeleted: Scalars['Boolean']['output'];
  parentComment?: Maybe<DiscussionCommentType>;
  replyCount?: Maybe<Scalars['Int']['output']>;
  score?: Maybe<Scalars['Int']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  upvotes: Scalars['Int']['output'];
  user?: Maybe<UserType>;
};

/** Dynamic stop loss calculation result */
export type DynamicStopType = {
  __typename?: 'DynamicStopType';
  atrStop?: Maybe<Scalars['Float']['output']>;
  method?: Maybe<Scalars['String']['output']>;
  pctStop?: Maybe<Scalars['Float']['output']>;
  riskPercentage?: Maybe<Scalars['Float']['output']>;
  srStop?: Maybe<Scalars['Float']['output']>;
  stopDistance?: Maybe<Scalars['Float']['output']>;
  stopPrice?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for edge prediction (mispricing forecast) */
export type EdgePredictionType = {
  __typename?: 'EdgePredictionType';
  confidence: Scalars['Float']['output'];
  currentEdge: Scalars['Float']['output'];
  currentPremium: Scalars['Float']['output'];
  edgeChangeDollars: Scalars['Float']['output'];
  expiration: Scalars['String']['output'];
  explanation: Scalars['String']['output'];
  optionType: Scalars['String']['output'];
  predictedEdge1day: Scalars['Float']['output'];
  predictedEdge1hr: Scalars['Float']['output'];
  predictedEdge15min: Scalars['Float']['output'];
  predictedPremium1hr: Scalars['Float']['output'];
  predictedPremium15min: Scalars['Float']['output'];
  strike: Scalars['Float']['output'];
};

/** Enable a strategy for a user with custom parameters */
export type EnableStrategy = {
  __typename?: 'EnableStrategy';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  userStrategySettings?: Maybe<UserStrategySettingsType>;
};

/** GraphQL type for entry timing suggestions */
export type EntryTimingSuggestionType = {
  __typename?: 'EntryTimingSuggestionType';
  currentDistancePct?: Maybe<Scalars['Float']['output']>;
  pullbackTarget?: Maybe<Scalars['Float']['output']>;
  /** ENTER_NOW or WAIT_FOR_PULLBACK */
  recommendation?: Maybe<Scalars['String']['output']>;
  waitReason?: Maybe<Scalars['String']['output']>;
};

/** Type for equity curve data points */
export type EquityPointType = {
  __typename?: 'EquityPointType';
  equity: Scalars['Float']['output'];
  timestamp: Scalars['DateTime']['output'];
};

/** GraphQL type for execution quality statistics */
export type ExecutionQualityStatsType = {
  __typename?: 'ExecutionQualityStatsType';
  /** Average execution quality score (0-10) */
  avgQualityScore?: Maybe<Scalars['Float']['output']>;
  /** Average slippage percentage */
  avgSlippagePct?: Maybe<Scalars['Float']['output']>;
  /** Number of times price was chased */
  chasedCount?: Maybe<Scalars['Int']['output']>;
  /** Coaching tips for improvement */
  improvementTips?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Number of days analyzed */
  periodDays?: Maybe<Scalars['Int']['output']>;
  /** Total number of fills analyzed */
  totalFills?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for execution order suggestions */
export type ExecutionSuggestionType = {
  __typename?: 'ExecutionSuggestionType';
  bracketLegs?: Maybe<BracketLegsType>;
  /** Human-readable entry strategy */
  entryStrategy?: Maybe<Scalars['String']['output']>;
  /** One-line microstructure hint: 'Spread 0.08% · Book: Bid-leaning · Liquidity: Strong' */
  microstructureSummary?: Maybe<Scalars['String']['output']>;
  /** LIMIT, MARKET, STOP_LIMIT, etc. */
  orderType?: Maybe<Scalars['String']['output']>;
  /** Suggested price range [min, max] */
  priceBand?: Maybe<Array<Maybe<Scalars['Float']['output']>>>;
  /** Explanation of the suggestion */
  rationale?: Maybe<Scalars['String']['output']>;
  suggestedSize?: Maybe<Scalars['Int']['output']>;
  /** DAY, IOC, GTC, etc. */
  timeInForce?: Maybe<Scalars['String']['output']>;
};

/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutation = {
  __typename?: 'ExtendedMutation';
  /** Add a stock to user's watchlist */
  addToWatchlist?: Maybe<AddToWatchlist>;
  aiRebalancePortfolio?: Maybe<RebalanceResultType>;
  /** Get bandit strategy recommendation */
  banditStrategy?: Maybe<BanditStrategyResultType>;
  /** Cancel Alpaca crypto order */
  cancelAlpacaCryptoOrder?: Maybe<CancelAlpacaCryptoOrderResultType>;
  /** Cancel a paper trading order */
  cancelPaperOrder?: Maybe<CancelPaperOrder>;
  /** Cancel premium subscription */
  cancelPremiumSubscription?: Maybe<CancelPremiumSubscription>;
  /** Change password for authenticated user */
  changePassword?: Maybe<ChangePassword>;
  /** Close an options position (sell to close) */
  closeOptionsPosition?: Maybe<CloseOptionsPosition>;
  /** Add a comment to a swing trading signal */
  commentSignal?: Maybe<CommentSignal>;
  /** Complete a KYC workflow */
  completeKycWorkflow?: Maybe<CompleteKycWorkflow>;
  /** Copy a trade from another trader */
  copyTrade?: Maybe<CopyTradeResultType>;
  /** Create Alpaca crypto order */
  createAlpacaCryptoOrder?: Maybe<CreateAlpacaCryptoOrderResultType>;
  /** Create/update broker account for KYC onboarding */
  createBrokerAccount?: Maybe<CreateBrokerAccount>;
  /** Create a brokerage account as part of KYC */
  createBrokerageAccount?: Maybe<CreateBrokerageAccount>;
  createChatSession?: Maybe<CreateChatSession>;
  createComment?: Maybe<CreateComment>;
  /** Create a custom user strategy */
  createCustomStrategy?: Maybe<CreateCustomStrategy>;
  /** Create a comment on a discussion (Reddit-style) */
  createDiscussionComment?: Maybe<CreateDiscussionComment>;
  /** Create or update user's income profile */
  createIncomeProfile?: Maybe<CreateIncomeProfile>;
  /** Create an options alert */
  createOptionsAlert?: Maybe<CreateOptionsAlert>;
  /** Add a stock holding to a specific portfolio */
  createPortfolioHolding?: Maybe<CreatePortfolioHolding>;
  createPost?: Maybe<CreatePost>;
  /** Create a new SBLOC application session */
  createSblocSession?: Maybe<CreateSblocSession>;
  /** Create a new stock discussion post (Reddit-style) */
  createStockDiscussion?: Maybe<CreateStockDiscussion>;
  /** Create a new strategy blend with custom weights */
  createStrategyBlend?: Maybe<CreateStrategyBlend>;
  /** Enhanced user creation with security features */
  createUser?: Maybe<CreateUser>;
  /** Borrow assets from DeFi protocol */
  defiBorrow?: Maybe<DefiBorrow>;
  /** Supply assets to DeFi protocol */
  defiSupply?: Maybe<DefiSupply>;
  deleteComment?: Maybe<DeleteComment>;
  /** Delete a custom user strategy */
  deleteCustomStrategy?: Maybe<DeleteCustomStrategy>;
  /** Delete an options alert */
  deleteOptionsAlert?: Maybe<DeleteOptionsAlert>;
  /** Delete a strategy blend */
  deleteStrategyBlend?: Maybe<DeleteStrategyBlend>;
  /** Disable a strategy for a user */
  disableStrategy?: Maybe<DisableStrategy>;
  /** Enable a strategy for a user with custom parameters */
  enableStrategy?: Maybe<EnableStrategy>;
  /** Follow a stock ticker */
  followTicker?: Maybe<FollowTickerResultType>;
  /** Follow a trader */
  followTrader?: Maybe<FollowTraderResultType>;
  /** Send password reset email */
  forgotPassword?: Maybe<ForgotPassword>;
  /** Generate AI portfolio recommendations based on user's income profile */
  generateAiRecommendations?: Maybe<GenerateAiRecommendations>;
  /** Generate RAHA signals for a strategy (live or historical) */
  generateRahaSignals?: Maybe<GenerateRahaSignals>;
  /** Generate and optionally email a research report */
  generateResearchReport?: Maybe<GenerateResearchReport>;
  getChatHistory?: Maybe<GetChatHistory>;
  /** Get news preferences (mutation for consistency with update) */
  getNewsPreferences?: Maybe<GetNewsPreferencesResultType>;
  /** Initiate funding transfer from bank account to broker account */
  initiateFunding?: Maybe<InitiateFunding>;
  /** Initiate a KYC workflow */
  initiateKycWorkflow?: Maybe<InitiateKycWorkflow>;
  /** Like a post */
  likePost?: Maybe<LikePostResultType>;
  /** Like or unlike a swing trading signal */
  likeSignal?: Maybe<LikeSignal>;
  /** Link a bank account manually (fallback when Yodlee is not available) */
  linkBankAccount?: Maybe<LinkBankAccount>;
  /** Log the outcome of a day trading pick */
  logDayTradingOutcome?: Maybe<LogDayTradingOutcome>;
  /** Mark all notifications as read */
  markAllNotificationsRead?: Maybe<MarkAllNotificationsRead>;
  /** Mark a notification as read */
  markNotificationRead?: Maybe<MarkNotificationRead>;
  /** Parse a voice command into a trading order */
  parseVoiceCommand?: Maybe<ParseVoiceCommand>;
  /** Place a bracket options order (parent + take profit + stop loss) */
  placeBracketOptionsOrder?: Maybe<PlaceBracketOptionsOrder>;
  /** Place a limit order (alias for placeOrder with order_type='LIMIT') */
  placeLimitOrder?: Maybe<PlaceLimitOrder>;
  /** Place a multi-leg options order (spreads, straddles, etc.) */
  placeMultiLegOptionsOrder?: Maybe<PlaceMultiLegOptionsOrder>;
  /** Place an options order with guardrails */
  placeOptionsOrder?: Maybe<PlaceOptionsOrder>;
  /** Place a broker order with guardrails */
  placeOrder?: Maybe<PlaceOrder>;
  /** Place a paper trading order */
  placePaperOrder?: Maybe<PlacePaperOrder>;
  /** Place a stock order (alias for placeOrder with stock-specific defaults) */
  placeStockOrder?: Maybe<PlaceStockOrder>;
  /** Record stake transaction */
  recordStakeTransaction?: Maybe<RecordStakeTransactionResultType>;
  /** Refresh bank account data from Yodlee */
  refreshBankAccount?: Maybe<RefreshBankAccount>;
  refreshToken?: Maybe<Refresh>;
  /** Remove a stock from user's watchlist */
  removeFromWatchlist?: Maybe<RemoveFromWatchlist>;
  /** Remove a holding from portfolio */
  removePortfolioHolding?: Maybe<RemovePortfolioHolding>;
  /** Reset password with token */
  resetPassword?: Maybe<ResetPassword>;
  /** Run a backtest for a strategy */
  runBacktest?: Maybe<RunBacktest>;
  saveInsight?: Maybe<SaveInsightResult>;
  /** Save user's portfolio holdings */
  savePortfolio?: Maybe<SavePortfolio>;
  sendMessage?: Maybe<SendMessage>;
  /** Set a bank account as primary */
  setPrimaryBankAccount?: Maybe<SetPrimaryBankAccount>;
  shareInsight?: Maybe<ShareInsightResult>;
  /** Create stake intent */
  stakeIntent?: Maybe<StakeIntentResultType>;
  /** Start a new lesson */
  startLesson?: Maybe<StartLesson>;
  /** Start a live trading simulation */
  startLiveSim?: Maybe<StartLiveSim>;
  /** Start a new quest */
  startQuest?: Maybe<StartQuest>;
  /** Submit quiz answers */
  submitQuiz?: Maybe<SubmitQuiz>;
  /** Subscribe to premium features */
  subscribeToPremium?: Maybe<SubscribeToPremium>;
  /** Sync transactions for a bank account */
  syncBankTransactions?: Maybe<SyncBankTransactions>;
  /** Sync SBLOC banks from aggregator service */
  syncSblocBanks?: Maybe<SyncSblocBanks>;
  /** Take profits on an options position (limit sell) */
  takeOptionsProfits?: Maybe<TakeOptionsProfits>;
  toggleFollow?: Maybe<ToggleFollow>;
  toggleLike?: Maybe<ToggleLike>;
  /** Obtain JSON Web Token mutation */
  tokenAuth?: Maybe<ObtainJsonWebToken>;
  /** Train a custom ML model on user's trading history */
  trainMlModel?: Maybe<TrainMlModel>;
  /** Train ML models */
  trainModels?: Maybe<TrainModelsResultType>;
  /** Unfollow a stock ticker */
  unfollowTicker?: Maybe<FollowTickerResultType>;
  /** Update user's auto-trading settings */
  updateAutoTradingSettings?: Maybe<UpdateAutoTradingSettings>;
  /** Update bandit reward */
  updateBanditReward?: Maybe<UpdateBanditRewardResultType>;
  /** Update a custom user strategy */
  updateCustomStrategy?: Maybe<UpdateCustomStrategy>;
  /** Update the number of shares for a holding */
  updateHoldingShares?: Maybe<UpdateHoldingShares>;
  /** Update a KYC workflow step */
  updateKycStep?: Maybe<UpdateKycStep>;
  /** Update news preferences */
  updateNewsPreferences?: Maybe<UpdateNewsPreferencesResultType>;
  /** Update user's RAHA notification preferences */
  updateNotificationPreferences?: Maybe<UpdateNotificationPreferences>;
  /** Update an options alert */
  updateOptionsAlert?: Maybe<UpdateOptionsAlert>;
  /** Move a holding to a different portfolio */
  updatePortfolioHolding?: Maybe<UpdatePortfolioHolding>;
  updatePrivacySettings?: Maybe<UpdatePrivacySettingsResult>;
  /** Update quest progress */
  updateQuestProgress?: Maybe<UpdateQuestProgress>;
  /** Update an existing strategy blend */
  updateStrategyBlend?: Maybe<UpdateStrategyBlend>;
  /** Upload a KYC document */
  uploadKycDocument?: Maybe<UploadKycDocument>;
  verifyToken?: Maybe<Verify>;
  /** Vote on a discussion (upvote/downvote) */
  voteDiscussion?: Maybe<VoteDiscussion>;
  /** Vote on a poll option */
  votePoll?: Maybe<VotePoll>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationAddToWatchlistArgs = {
  notes?: InputMaybe<Scalars['String']['input']>;
  stockSymbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationAiRebalancePortfolioArgs = {
  dryRun?: InputMaybe<Scalars['Boolean']['input']>;
  maxRebalancePercentage?: InputMaybe<Scalars['Float']['input']>;
  portfolioName?: InputMaybe<Scalars['String']['input']>;
  riskTolerance?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationBanditStrategyArgs = {
  context?: InputMaybe<Scalars['JSONString']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCancelAlpacaCryptoOrderArgs = {
  accountId: Scalars['Int']['input'];
  orderId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCancelPaperOrderArgs = {
  orderId: Scalars['Int']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationChangePasswordArgs = {
  currentPassword: Scalars['String']['input'];
  newPassword: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCloseOptionsPositionArgs = {
  quantity?: InputMaybe<Scalars['Int']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCommentSignalArgs = {
  comment: Scalars['String']['input'];
  signalId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCompleteKycWorkflowArgs = {
  workflowType: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCopyTradeArgs = {
  amount: Scalars['Float']['input'];
  tradeId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateAlpacaCryptoOrderArgs = {
  accountId: Scalars['Int']['input'];
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  notional?: InputMaybe<Scalars['Float']['input']>;
  qty?: InputMaybe<Scalars['Float']['input']>;
  side: Scalars['String']['input'];
  stopPrice?: InputMaybe<Scalars['Float']['input']>;
  symbol: Scalars['String']['input'];
  timeInForce: Scalars['String']['input'];
  type: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateBrokerAccountArgs = {
  city?: InputMaybe<Scalars['String']['input']>;
  country?: InputMaybe<Scalars['String']['input']>;
  dateOfBirth: Scalars['String']['input'];
  firstName: Scalars['String']['input'];
  fundingSource?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  lastName: Scalars['String']['input'];
  phoneNumber?: InputMaybe<Scalars['String']['input']>;
  postalCode?: InputMaybe<Scalars['String']['input']>;
  ssn: Scalars['String']['input'];
  state?: InputMaybe<Scalars['String']['input']>;
  streetAddress?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateBrokerageAccountArgs = {
  kycData: Scalars['JSONString']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateChatSessionArgs = {
  title?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateCommentArgs = {
  content: Scalars['String']['input'];
  postId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateCustomStrategyArgs = {
  category: Scalars['String']['input'];
  configSchema?: InputMaybe<Scalars['JSONString']['input']>;
  customLogic: Scalars['JSONString']['input'];
  description: Scalars['String']['input'];
  marketType: Scalars['String']['input'];
  name: Scalars['String']['input'];
  timeframeSupported?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateDiscussionCommentArgs = {
  content: Scalars['String']['input'];
  discussionId: Scalars['ID']['input'];
  parentCommentId?: InputMaybe<Scalars['ID']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateIncomeProfileArgs = {
  age?: InputMaybe<Scalars['Int']['input']>;
  incomeBracket?: InputMaybe<Scalars['String']['input']>;
  investmentGoals?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  investmentHorizon?: InputMaybe<Scalars['String']['input']>;
  riskTolerance?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateOptionsAlertArgs = {
  alertType: Scalars['String']['input'];
  direction?: InputMaybe<Scalars['String']['input']>;
  expiration?: InputMaybe<Scalars['String']['input']>;
  optionType?: InputMaybe<Scalars['String']['input']>;
  strike?: InputMaybe<Scalars['Float']['input']>;
  symbol: Scalars['String']['input'];
  targetValue?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreatePortfolioHoldingArgs = {
  averagePrice?: InputMaybe<Scalars['Float']['input']>;
  currentPrice?: InputMaybe<Scalars['Float']['input']>;
  portfolioName: Scalars['String']['input'];
  shares: Scalars['Int']['input'];
  stockId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreatePostArgs = {
  content: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateSblocSessionArgs = {
  amountUsd: Scalars['Int']['input'];
  bankId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateStockDiscussionArgs = {
  content: Scalars['String']['input'];
  discussionType?: InputMaybe<Scalars['String']['input']>;
  stockSymbol?: InputMaybe<Scalars['String']['input']>;
  title: Scalars['String']['input'];
  visibility?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateStrategyBlendArgs = {
  components: Array<InputMaybe<Scalars['JSONString']['input']>>;
  description?: InputMaybe<Scalars['String']['input']>;
  isDefault?: InputMaybe<Scalars['Boolean']['input']>;
  name: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationCreateUserArgs = {
  email: Scalars['String']['input'];
  name: Scalars['String']['input'];
  password: Scalars['String']['input'];
  profilePic?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDefiBorrowArgs = {
  amount: Scalars['Float']['input'];
  rateMode?: InputMaybe<Scalars['String']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDefiSupplyArgs = {
  quantity: Scalars['Float']['input'];
  symbol: Scalars['String']['input'];
  useAsCollateral?: InputMaybe<Scalars['Boolean']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDeleteCommentArgs = {
  commentId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDeleteCustomStrategyArgs = {
  strategyId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDeleteOptionsAlertArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDeleteStrategyBlendArgs = {
  blendId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationDisableStrategyArgs = {
  strategyVersionId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationEnableStrategyArgs = {
  autoTradeEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  maxConcurrentPositions?: InputMaybe<Scalars['Int']['input']>;
  maxDailyLossPercent?: InputMaybe<Scalars['Float']['input']>;
  parameters?: InputMaybe<Scalars['JSONString']['input']>;
  strategyVersionId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationFollowTickerArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationFollowTraderArgs = {
  traderId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationForgotPasswordArgs = {
  email: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationGenerateRahaSignalsArgs = {
  lookbackCandles?: InputMaybe<Scalars['Int']['input']>;
  parameters?: InputMaybe<Scalars['JSONString']['input']>;
  strategyVersionId: Scalars['ID']['input'];
  symbol: Scalars['String']['input'];
  timeframe?: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationGenerateResearchReportArgs = {
  reportType?: InputMaybe<Scalars['String']['input']>;
  sendEmail?: InputMaybe<Scalars['Boolean']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationGetChatHistoryArgs = {
  sessionId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationInitiateFundingArgs = {
  amount: Scalars['Float']['input'];
  bankAccountId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationInitiateKycWorkflowArgs = {
  workflowType: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationLikePostArgs = {
  postId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationLikeSignalArgs = {
  signalId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationLinkBankAccountArgs = {
  accountNumber: Scalars['String']['input'];
  bankName: Scalars['String']['input'];
  routingNumber: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationLogDayTradingOutcomeArgs = {
  input: Scalars['JSONString']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationMarkNotificationReadArgs = {
  notificationId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationParseVoiceCommandArgs = {
  input: Scalars['JSONString']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceBracketOptionsOrderArgs = {
  expiration: Scalars['String']['input'];
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  optionType: Scalars['String']['input'];
  orderType?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  stopLoss: Scalars['Float']['input'];
  strike: Scalars['Float']['input'];
  symbol: Scalars['String']['input'];
  takeProfit: Scalars['Float']['input'];
  timeInForce?: InputMaybe<Scalars['String']['input']>;
  usePaperTrading?: InputMaybe<Scalars['Boolean']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceLimitOrderArgs = {
  limitPrice: Scalars['Float']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  symbol: Scalars['String']['input'];
  timeInForce?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceMultiLegOptionsOrderArgs = {
  legs: Array<InputMaybe<Scalars['JSONString']['input']>>;
  strategyName?: InputMaybe<Scalars['String']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceOptionsOrderArgs = {
  estimatedPremium?: InputMaybe<Scalars['Float']['input']>;
  expiration: Scalars['String']['input'];
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  optionType: Scalars['String']['input'];
  orderType?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  strike: Scalars['Float']['input'];
  symbol: Scalars['String']['input'];
  timeInForce?: InputMaybe<Scalars['String']['input']>;
  usePaperTrading?: InputMaybe<Scalars['Boolean']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceOrderArgs = {
  estimatedPrice?: InputMaybe<Scalars['Float']['input']>;
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  orderType: Scalars['String']['input'];
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  stopPrice?: InputMaybe<Scalars['Float']['input']>;
  symbol: Scalars['String']['input'];
  timeInForce?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlacePaperOrderArgs = {
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  orderType?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  stopPrice?: InputMaybe<Scalars['Float']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationPlaceStockOrderArgs = {
  limitPrice?: InputMaybe<Scalars['Float']['input']>;
  orderType?: InputMaybe<Scalars['String']['input']>;
  quantity: Scalars['Int']['input'];
  side: Scalars['String']['input'];
  symbol: Scalars['String']['input'];
  timeInForce?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRecordStakeTransactionArgs = {
  amount: Scalars['Float']['input'];
  chainId: Scalars['Int']['input'];
  poolId: Scalars['String']['input'];
  txHash: Scalars['String']['input'];
  wallet: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRefreshBankAccountArgs = {
  accountId: Scalars['Int']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRefreshTokenArgs = {
  token?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRemoveFromWatchlistArgs = {
  stockSymbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRemovePortfolioHoldingArgs = {
  holdingId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationResetPasswordArgs = {
  newPassword: Scalars['String']['input'];
  token: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationRunBacktestArgs = {
  endDate: Scalars['Date']['input'];
  parameters?: InputMaybe<Scalars['JSONString']['input']>;
  startDate: Scalars['Date']['input'];
  strategyVersionId: Scalars['ID']['input'];
  symbol: Scalars['String']['input'];
  timeframe?: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSaveInsightArgs = {
  insightId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSavePortfolioArgs = {
  currentPrices?: InputMaybe<Array<InputMaybe<Scalars['Float']['input']>>>;
  notesList?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  sharesList: Array<InputMaybe<Scalars['Int']['input']>>;
  stockIds: Array<InputMaybe<Scalars['ID']['input']>>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSendMessageArgs = {
  content: Scalars['String']['input'];
  sessionId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSetPrimaryBankAccountArgs = {
  accountId: Scalars['Int']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationShareInsightArgs = {
  insightId: Scalars['ID']['input'];
  platform: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationStakeIntentArgs = {
  amount: Scalars['Float']['input'];
  poolId: Scalars['String']['input'];
  wallet: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationStartLessonArgs = {
  regime?: InputMaybe<Scalars['String']['input']>;
  topic: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationStartLiveSimArgs = {
  mode: Scalars['String']['input'];
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationStartQuestArgs = {
  difficulty: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSubmitQuizArgs = {
  answers: Array<InputMaybe<Scalars['Int']['input']>>;
  lessonId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSubscribeToPremiumArgs = {
  paymentMethod: Scalars['String']['input'];
  planType: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationSyncBankTransactionsArgs = {
  accountId: Scalars['Int']['input'];
  fromDate?: InputMaybe<Scalars['String']['input']>;
  toDate?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationTakeOptionsProfitsArgs = {
  limitPrice: Scalars['Float']['input'];
  quantity?: InputMaybe<Scalars['Int']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationToggleFollowArgs = {
  userId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationToggleLikeArgs = {
  postId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationTokenAuthArgs = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationTrainMlModelArgs = {
  lookbackDays?: InputMaybe<Scalars['Int']['input']>;
  modelType?: InputMaybe<Scalars['String']['input']>;
  strategyVersionId?: InputMaybe<Scalars['ID']['input']>;
  symbol?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationTrainModelsArgs = {
  modes?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUnfollowTickerArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateAutoTradingSettingsArgs = {
  allowedSymbols?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  blockedSymbols?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  enabled?: InputMaybe<Scalars['Boolean']['input']>;
  fixedPositionSize?: InputMaybe<Scalars['Float']['input']>;
  maxConcurrentPositions?: InputMaybe<Scalars['Int']['input']>;
  maxDailyLossPercent?: InputMaybe<Scalars['Float']['input']>;
  maxPositionSizePercent?: InputMaybe<Scalars['Float']['input']>;
  minConfidenceThreshold?: InputMaybe<Scalars['Float']['input']>;
  onlyTradeMarketHours?: InputMaybe<Scalars['Boolean']['input']>;
  positionSizePercent?: InputMaybe<Scalars['Float']['input']>;
  positionSizingMethod?: InputMaybe<Scalars['String']['input']>;
  riskPerTradePercent?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateBanditRewardArgs = {
  reward: Scalars['Float']['input'];
  strategy: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateCustomStrategyArgs = {
  configSchema?: InputMaybe<Scalars['JSONString']['input']>;
  customLogic?: InputMaybe<Scalars['JSONString']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  strategyId: Scalars['ID']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateHoldingSharesArgs = {
  holdingId: Scalars['ID']['input'];
  newShares: Scalars['Int']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateKycStepArgs = {
  data?: InputMaybe<Scalars['JSONString']['input']>;
  status: Scalars['String']['input'];
  step: Scalars['Int']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateNewsPreferencesArgs = {
  preferences: NewsPreferencesInputType;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateNotificationPreferencesArgs = {
  backtestNotificationsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  backtestSuccessOnly?: InputMaybe<Scalars['Boolean']['input']>;
  pushEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  pushToken?: InputMaybe<Scalars['String']['input']>;
  quietHoursEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  quietHoursEnd?: InputMaybe<Scalars['String']['input']>;
  quietHoursStart?: InputMaybe<Scalars['String']['input']>;
  signalConfidenceThreshold?: InputMaybe<Scalars['Float']['input']>;
  signalNotificationsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  signalSymbols?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateOptionsAlertArgs = {
  direction?: InputMaybe<Scalars['String']['input']>;
  id: Scalars['ID']['input'];
  status?: InputMaybe<Scalars['String']['input']>;
  targetValue?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdatePortfolioHoldingArgs = {
  holdingId: Scalars['ID']['input'];
  newPortfolioName: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdatePrivacySettingsArgs = {
  settings: PrivacySettingsInput;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateQuestProgressArgs = {
  completedScenarios: Scalars['Int']['input'];
  progress: Scalars['Float']['input'];
  questId: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUpdateStrategyBlendArgs = {
  blendId: Scalars['ID']['input'];
  components?: InputMaybe<Array<InputMaybe<Scalars['JSONString']['input']>>>;
  description?: InputMaybe<Scalars['String']['input']>;
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  isDefault?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationUploadKycDocumentArgs = {
  accountId: Scalars['String']['input'];
  content: Scalars['String']['input'];
  contentType: Scalars['String']['input'];
  documentType: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationVerifyTokenArgs = {
  token?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationVoteDiscussionArgs = {
  discussionId: Scalars['ID']['input'];
  voteType: Scalars['String']['input'];
};


/**
 * Final Mutation type exposed by the schema.
 *
 * - Includes base mutations (create_user, add_to_watchlist, etc.)
 * - Includes premium mutations (subscribe_to_premium, ai_rebalance_portfolio, etc.)
 * - Includes Broker, Banking, and SBLOC mutations
 */
export type ExtendedMutationVotePollArgs = {
  optionId: Scalars['ID']['input'];
  postId: Scalars['ID']['input'];
};

/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuery = {
  __typename?: 'ExtendedQuery';
  /** Get enhanced activity feed for current user */
  activityFeed?: Maybe<Array<Maybe<ActivityFeedItemType>>>;
  advancedStockScreening?: Maybe<Array<Maybe<StockScreeningResultType>>>;
  aiPortfolioRecommendations?: Maybe<Array<Maybe<AiPortfolioRecommendationType>>>;
  aiPredictions?: Maybe<AiPredictionsType>;
  aiRecommendations?: Maybe<AiRecommendationsType>;
  /** Get AI market scans with optional filters */
  aiScans?: Maybe<Array<Maybe<AiScanType>>>;
  /** Get AI-optimized yield portfolio (camelCase alias) */
  aiYieldOptimizer?: Maybe<YieldOptimizerResultType>;
  allPosts?: Maybe<Array<Maybe<PostType>>>;
  allUsers?: Maybe<Array<Maybe<UserType>>>;
  /** Deprecated alias for brokerAccount. Use brokerAccount instead. */
  alpacaAccount?: Maybe<BrokerAccountType>;
  /** Get Alpaca crypto account (camelCase alias) */
  alpacaCryptoAccount?: Maybe<AlpacaCryptoAccountType>;
  /** Get Alpaca crypto balances (camelCase alias) */
  alpacaCryptoBalances?: Maybe<Array<Maybe<AlpacaCryptoBalanceType>>>;
  /** Get Alpaca crypto orders (camelCase alias) */
  alpacaCryptoOrders?: Maybe<Array<Maybe<AlpacaCryptoOrderType>>>;
  /** Get user's auto-trading settings */
  autoTradingSettings?: Maybe<AutoTradingSettingsType>;
  availableBenchmarks?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Get a specific backtest run by ID */
  backtestRun?: Maybe<RahaBacktestRunType>;
  /** Get a specific bank account by ID */
  bankAccount?: Maybe<BankAccountType>;
  /** Get user's linked bank accounts (camelCase alias) */
  bankAccounts?: Maybe<Array<Maybe<BankAccountType>>>;
  /** Get user's bank provider accounts */
  bankProviderAccounts?: Maybe<Array<Maybe<BankProviderAccountType>>>;
  /** Get bank transactions */
  bankTransactions?: Maybe<Array<Maybe<BankTransactionType>>>;
  beginnerFriendlyStocks?: Maybe<Array<Maybe<StockType>>>;
  benchmarkSeries?: Maybe<BenchmarkSeriesType>;
  brokerAccount?: Maybe<BrokerAccountType>;
  brokerAccountInfo?: Maybe<Scalars['JSONString']['output']>;
  brokerActivities?: Maybe<Array<Maybe<BrokerActivityType>>>;
  brokerOrders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  brokerPositions?: Maybe<Array<Maybe<BrokerPositionType>>>;
  /** Calculate dynamic stop loss based on ATR and support/resistance */
  calculateDynamicStop?: Maybe<DynamicStopType>;
  /** Calculate optimal position size based on risk parameters */
  calculatePositionSize?: Maybe<PositionSizeType>;
  /** Calculate target price based on risk/reward ratio and technical levels */
  calculateTargetPrice?: Maybe<TargetPriceType>;
  chatMessages?: Maybe<Array<Maybe<ChatMessageType>>>;
  chatSession?: Maybe<ChatSessionType>;
  /** Get enhanced Consumer Strength Score with historical tracking */
  consumerStrength?: Maybe<ConsumerStrengthType>;
  /** Get historical Consumer Strength Scores */
  consumerStrengthHistory?: Maybe<Array<Maybe<ConsumerStrengthType>>>;
  /** Get crypto assets (camelCase alias) */
  cryptoAssets?: Maybe<Array<Maybe<CryptocurrencyType>>>;
  /** Get crypto ML signal (camelCase alias) */
  cryptoMlSignal?: Maybe<CryptoMlSignalType>;
  /** Get user's crypto portfolio (camelCase alias) */
  cryptoPortfolio?: Maybe<CryptoPortfolioType>;
  /** Get crypto price (camelCase alias) */
  cryptoPrice?: Maybe<CryptoPriceType>;
  /** Get crypto recommendations (camelCase alias) */
  cryptoRecommendations?: Maybe<Array<Maybe<CryptoRecommendationType>>>;
  /** Get crypto SBLOC loans (camelCase alias) */
  cryptoSblocLoans?: Maybe<Array<Maybe<CryptoSblocLoanType>>>;
  currentStockPrices?: Maybe<Array<Maybe<StockPriceType>>>;
  /** Get today's daily quest (camelCase alias) */
  dailyQuest?: Maybe<DailyQuestType>;
  dayTradingPicks?: Maybe<DayTradingDataType>;
  /** Get day trading strategy performance stats (Citadel Board) */
  dayTradingStats?: Maybe<Array<Maybe<DayTradingStatsType>>>;
  defiAccount?: Maybe<DefiAccountType>;
  defiReserves?: Maybe<Array<Maybe<DefiReserveType>>>;
  discussionDetail?: Maybe<StockDiscussionType>;
  edgePredictions?: Maybe<Array<Maybe<EdgePredictionType>>>;
  /** Get entry timing suggestion (enter now vs wait for pullback) */
  entryTimingSuggestion?: Maybe<EntryTimingSuggestionType>;
  /** Get execution quality statistics and coaching tips */
  executionQualityStats?: Maybe<ExecutionQualityStatsType>;
  /** Get smart order suggestion for a trading signal */
  executionSuggestion?: Maybe<ExecutionSuggestionType>;
  /** Get funding history for broker account (camelCase alias) */
  fundingHistory?: Maybe<Array<Maybe<FundingHistoryType>>>;
  /** Get active positions */
  getActivePositions?: Maybe<Array<Maybe<PositionType>>>;
  /** Get playbooks (alias for playbooks) */
  getPlaybooks?: Maybe<Array<Maybe<PlaybookType>>>;
  /** Get scan details (alias for scan) */
  getScanDetails?: Maybe<AiScanType>;
  /** Get governance proposals (camelCase alias) */
  governanceProposals?: Maybe<Array<Maybe<GovernanceProposalType>>>;
  hasIncomeProfile?: Maybe<Scalars['Boolean']['output']>;
  ivSurfaceForecast?: Maybe<IvSurfaceForecastType>;
  marketInsights?: Maybe<Array<Maybe<MarketInsightType>>>;
  marketRegime?: Maybe<MarketRegimeType>;
  marketSentiment?: Maybe<Scalars['JSONString']['output']>;
  me?: Maybe<UserType>;
  /** Get user's trained ML models (returns JSON strings) */
  mlModels?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  /** Get ML system status */
  mlSystemStatus?: Maybe<MlSystemStatusType>;
  myChatSessions?: Maybe<Array<Maybe<ChatSessionType>>>;
  myPortfolios?: Maybe<PortfolioSummaryType>;
  myWatchlist?: Maybe<Array<Maybe<WatchlistType>>>;
  /** Get user's RAHA notification preferences */
  notificationPreferences?: Maybe<NotificationPreferencesType>;
  notificationSettings?: Maybe<NotificationSettingsType>;
  notifications?: Maybe<Array<Maybe<NotificationType>>>;
  oneTapTrades?: Maybe<Array<Maybe<OneTapTradeType>>>;
  optionsAlert?: Maybe<OptionsAlertType>;
  optionsAlerts?: Maybe<Array<Maybe<OptionsAlertType>>>;
  optionsAnalysis?: Maybe<OptionsAnalysisType>;
  optionsFlow?: Maybe<OptionsFlowType>;
  oracleInsights?: Maybe<OracleInsightType>;
  /** Get comprehensive order monitoring dashboard data */
  orderDashboard?: Maybe<OrderDashboardType>;
  paperAccount?: Maybe<PaperTradingAccountType>;
  paperAccountSummary?: Maybe<PaperTradingAccountSummaryType>;
  paperOrders?: Maybe<Array<Maybe<PaperTradingOrderType>>>;
  paperPositions?: Maybe<Array<Maybe<PaperTradingPositionType>>>;
  paperTradeHistory?: Maybe<Array<Maybe<PaperTradingTradeType>>>;
  /** Get available trading playbooks */
  playbooks?: Maybe<Array<Maybe<PlaybookType>>>;
  /** Get pool analytics data (camelCase alias) */
  poolAnalytics?: Maybe<Array<Maybe<PoolAnalyticsPointType>>>;
  /** Get portfolio performance leaderboard */
  portfolioLeaderboard?: Maybe<Array<Maybe<LeaderboardEntryType>>>;
  portfolioMetrics?: Maybe<PortfolioMetricsType>;
  portfolioNames?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Get portfolio sharing information for current user */
  portfolioSharingInfo?: Maybe<PortfolioSharingInfoType>;
  /** Get signal updates for all portfolio positions */
  portfolioSignals?: Maybe<PortfolioSignalsType>;
  portfolioValue?: Maybe<Scalars['Float']['output']>;
  postComments?: Maybe<Array<Maybe<CommentType>>>;
  /** Get pre-market quality setups (4AM-9:30AM ET) */
  preMarketPicks?: Maybe<PreMarketDataType>;
  premiumPortfolioMetrics?: Maybe<PortfolioMetricsType>;
  privacySettings?: Maybe<PrivacySettingsType>;
  publicWatchlists?: Maybe<Array<Maybe<WatchlistType>>>;
  /** Get aggregated performance metrics for a strategy */
  rahaMetrics?: Maybe<RahaMetricsType>;
  /** Get RAHA signals with pagination (optionally filtered by symbol, timeframe, strategy) */
  rahaSignals?: Maybe<Array<Maybe<RahaSignalType>>>;
  /** Get comprehensive research data for a stock */
  researchHub?: Maybe<ResearchHubType>;
  /** Generate automated research report for a stock */
  researchReport?: Maybe<Scalars['JSONString']['output']>;
  /** Get risk summary for user's account */
  riskSummary?: Maybe<RiskSummaryType>;
  rustCorrelationAnalysis?: Maybe<CorrelationAnalysisType>;
  rustForexAnalysis?: Maybe<ForexAnalysisType>;
  rustOptionsAnalysis?: Maybe<RustOptionsAnalysisType>;
  rustSentimentAnalysis?: Maybe<SentimentAnalysisType>;
  rustStockAnalysis?: Maybe<RustStockAnalysisType>;
  /** Get a specific SBLOC bank by ID */
  sblocBank?: Maybe<SblocBankType>;
  /** Get list of available SBLOC banks (alias) */
  sblocBanks?: Maybe<Array<Maybe<SblocBankType>>>;
  /** Get SBLOC offer/quote for user's portfolio (camelCase alias) */
  sblocOffer?: Maybe<SblocOfferType>;
  /** Get SBLOC session by ID */
  sblocSession?: Maybe<SblocSessionType>;
  /** Get scan details by ID */
  scan?: Maybe<AiScanType>;
  scanOptions?: Maybe<Array<Maybe<ScannedOptionType>>>;
  searchUsers?: Maybe<Array<Maybe<UserType>>>;
  /** Compare stock's Consumer Strength to sector average */
  sectorComparison?: Maybe<SectorComparisonType>;
  /** Get real-time multi-signal updates for a stock */
  signalUpdates?: Maybe<SignalUpdatesType>;
  socialFeed?: Maybe<Array<Maybe<StockDiscussionType>>>;
  /** Get social trading feeds */
  socialFeeds?: Maybe<Array<Maybe<SocialFeedItemType>>>;
  stock?: Maybe<StockType>;
  /** Get stock chart data (OHLCV) for a symbol and timeframe. */
  stockChartData?: Maybe<StockChartDataType>;
  stockDiscussions?: Maybe<Array<Maybe<StockDiscussionType>>>;
  stockMoments?: Maybe<Array<Maybe<StockMomentType>>>;
  stockScreening?: Maybe<Array<Maybe<StockScreeningResultType>>>;
  stocks?: Maybe<Array<Maybe<StockType>>>;
  /** Get available RAHA strategies */
  strategies?: Maybe<Array<Maybe<StrategyType>>>;
  /** Get a specific strategy by ID or slug */
  strategy?: Maybe<StrategyType>;
  /** Get user's strategy blends */
  strategyBlends?: Maybe<Array<Maybe<StrategyBlendType>>>;
  /** Get dashboard data for all user's enabled strategies (returns JSON strings) */
  strategyDashboard?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  /** Get supported cryptocurrencies (camelCase alias) */
  supportedCurrencies?: Maybe<Array<Maybe<CryptocurrencyType>>>;
  /** Get swing trading signals with filtering */
  swingSignals?: Maybe<Array<Maybe<SwingSignalType>>>;
  /** Get swing trading picks (2-5 day holds). Strategy: MOMENTUM, BREAKOUT, or MEAN_REVERSION */
  swingTradingPicks?: Maybe<SwingTradingDataType>;
  /** Get swing trading strategy performance stats */
  swingTradingStats?: Maybe<Array<Maybe<SwingTradingStatsType>>>;
  testAiRecommendations?: Maybe<AiRecommendationsType>;
  testOptionsAnalysis?: Maybe<OptionsAnalysisType>;
  testPortfolioMetrics?: Maybe<PortfolioMetricsType>;
  testStockScreening?: Maybe<Array<Maybe<StockScreeningResultType>>>;
  topPerformers?: Maybe<Array<Maybe<StockType>>>;
  /** Get top traders by performance */
  topTraders?: Maybe<Array<Maybe<SocialFeedUserType>>>;
  /** Get top yield opportunities (camelCase alias) */
  topYields?: Maybe<Array<Maybe<YieldPoolType>>>;
  /** Deprecated alias for brokerAccount. Use brokerAccount instead. */
  tradingAccount?: Maybe<BrokerAccountType>;
  /** Deprecated alias for brokerOrders. Use brokerOrders instead. */
  tradingOrders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  /** Deprecated alias for brokerPositions. Use brokerPositions instead. */
  tradingPositions?: Maybe<Array<Maybe<BrokerPositionType>>>;
  /** Get trading quote (bid/ask) for a symbol */
  tradingQuote?: Maybe<TradingQuoteType>;
  /** Get trending stock discussions */
  trendingDiscussions?: Maybe<Array<Maybe<TrendingDiscussionType>>>;
  /** Get user's tutor progress (camelCase alias) */
  tutorProgress?: Maybe<TutorProgressType>;
  user?: Maybe<UserType>;
  /** Get user's backtest runs with pagination */
  userBacktests?: Maybe<Array<Maybe<RahaBacktestRunType>>>;
  /** Get user's NFTs (camelCase alias) */
  userNFTs?: Maybe<Array<Maybe<NftType>>>;
  /** Get user's NFTs */
  userNfts?: Maybe<Array<Maybe<NftType>>>;
  userPosts?: Maybe<Array<Maybe<PostType>>>;
  /** Get user's enabled strategy settings */
  userStrategySettings?: Maybe<Array<Maybe<UserStrategySettingsType>>>;
  /** Get user's voting power (camelCase alias) */
  userVotingPower?: Maybe<UserVotingPowerType>;
  /** Get user's yield positions (camelCase alias) */
  userYieldPositions?: Maybe<Array<Maybe<UserYieldPositionType>>>;
  wallPosts?: Maybe<Array<Maybe<PostType>>>;
  watchlist?: Maybe<WatchlistType>;
  /** Get signal updates for watchlist stocks above threshold */
  watchlistSignals?: Maybe<Array<Maybe<SignalUpdatesType>>>;
  watchlists?: Maybe<Array<Maybe<WatchlistType>>>;
  /** Get available yield opportunities (camelCase alias) */
  yieldOpportunities?: Maybe<Array<Maybe<YieldOpportunityType>>>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryActivityFeedArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAdvancedStockScreeningArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  maxMarketCap?: InputMaybe<Scalars['Float']['input']>;
  maxPeRatio?: InputMaybe<Scalars['Float']['input']>;
  minBeginnerScore?: InputMaybe<Scalars['Int']['input']>;
  minMarketCap?: InputMaybe<Scalars['Float']['input']>;
  minPeRatio?: InputMaybe<Scalars['Float']['input']>;
  sector?: InputMaybe<Scalars['String']['input']>;
  sortBy?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAiPortfolioRecommendationsArgs = {
  userId: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAiPredictionsArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAiRecommendationsArgs = {
  profile?: InputMaybe<ProfileInput>;
  usingDefaults?: InputMaybe<Scalars['Boolean']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAiScansArgs = {
  filters?: InputMaybe<AiScanFilters>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAiYieldOptimizerArgs = {
  chain?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  userRiskTolerance?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAlpacaAccountArgs = {
  userId: Scalars['Int']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAlpacaCryptoAccountArgs = {
  userId: Scalars['Int']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAlpacaCryptoBalancesArgs = {
  accountId: Scalars['Int']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryAlpacaCryptoOrdersArgs = {
  accountId: Scalars['Int']['input'];
  status?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBacktestRunArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBankAccountArgs = {
  id: Scalars['Int']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBankTransactionsArgs = {
  accountId?: InputMaybe<Scalars['Int']['input']>;
  fromDate?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  toDate?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBenchmarkSeriesArgs = {
  symbol: Scalars['String']['input'];
  timeframe: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBrokerActivitiesArgs = {
  activityType?: InputMaybe<Scalars['String']['input']>;
  date?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryBrokerOrdersArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCalculateDynamicStopArgs = {
  atr: Scalars['Float']['input'];
  atrMultiplier?: InputMaybe<Scalars['Float']['input']>;
  entryPrice: Scalars['Float']['input'];
  resistanceLevel?: InputMaybe<Scalars['Float']['input']>;
  signalType?: InputMaybe<Scalars['String']['input']>;
  supportLevel?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCalculatePositionSizeArgs = {
  accountEquity: Scalars['Float']['input'];
  confidence?: InputMaybe<Scalars['Float']['input']>;
  entryPrice: Scalars['Float']['input'];
  maxPositionPct?: InputMaybe<Scalars['Float']['input']>;
  riskPerTrade?: InputMaybe<Scalars['Float']['input']>;
  stopPrice: Scalars['Float']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCalculateTargetPriceArgs = {
  atr?: InputMaybe<Scalars['Float']['input']>;
  entryPrice: Scalars['Float']['input'];
  resistanceLevel?: InputMaybe<Scalars['Float']['input']>;
  riskRewardRatio?: InputMaybe<Scalars['Float']['input']>;
  signalType?: InputMaybe<Scalars['String']['input']>;
  stopPrice: Scalars['Float']['input'];
  supportLevel?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryChatMessagesArgs = {
  sessionId: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryChatSessionArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryConsumerStrengthArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryConsumerStrengthHistoryArgs = {
  days?: InputMaybe<Scalars['Int']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCryptoAssetsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCryptoMlSignalArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCryptoPriceArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCryptoRecommendationsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  symbols?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCryptoSblocLoansArgs = {
  symbol?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryCurrentStockPricesArgs = {
  symbols?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryDayTradingPicksArgs = {
  mode?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryDayTradingStatsArgs = {
  mode?: InputMaybe<Scalars['String']['input']>;
  period?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryDiscussionDetailArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryEdgePredictionsArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryEntryTimingSuggestionArgs = {
  currentPrice: Scalars['Float']['input'];
  signal: Scalars['JSONString']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryExecutionQualityStatsArgs = {
  days?: InputMaybe<Scalars['Int']['input']>;
  signalType?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryExecutionSuggestionArgs = {
  signal: Scalars['JSONString']['input'];
  signalType?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryGetScanDetailsArgs = {
  scanId: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryGovernanceProposalsArgs = {
  daoAddress: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryIvSurfaceForecastArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryMarketInsightsArgs = {
  category?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryMlModelsArgs = {
  modelType?: InputMaybe<Scalars['String']['input']>;
  strategyVersionId?: InputMaybe<Scalars['ID']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOneTapTradesArgs = {
  accountSize?: InputMaybe<Scalars['Float']['input']>;
  riskTolerance?: InputMaybe<Scalars['Float']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOptionsAlertArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOptionsAlertsArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
  symbol?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOptionsAnalysisArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOptionsFlowArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryOracleInsightsArgs = {
  query: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPaperOrdersArgs = {
  status?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPaperTradeHistoryArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPoolAnalyticsArgs = {
  days?: InputMaybe<Scalars['Int']['input']>;
  poolId: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPortfolioLeaderboardArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  timeframe?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPortfolioSignalsArgs = {
  threshold?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPostCommentsArgs = {
  postId: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPreMarketPicksArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  mode?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryPremiumPortfolioMetricsArgs = {
  portfolioName?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRahaMetricsArgs = {
  period?: InputMaybe<Scalars['String']['input']>;
  strategyVersionId: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRahaSignalsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  strategyVersionId?: InputMaybe<Scalars['ID']['input']>;
  symbol?: InputMaybe<Scalars['String']['input']>;
  timeframe?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryResearchHubArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryResearchReportArgs = {
  reportType?: InputMaybe<Scalars['String']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRustCorrelationAnalysisArgs = {
  primary: Scalars['String']['input'];
  secondary?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRustForexAnalysisArgs = {
  pair: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRustOptionsAnalysisArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRustSentimentAnalysisArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryRustStockAnalysisArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySblocBankArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySblocSessionArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryScanArgs = {
  id: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryScanOptionsArgs = {
  filters?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySearchUsersArgs = {
  query?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySectorComparisonArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySignalUpdatesArgs = {
  lookbackHours?: InputMaybe<Scalars['Int']['input']>;
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySocialFeedsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStockArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStockChartDataArgs = {
  symbol: Scalars['String']['input'];
  timeframe: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStockDiscussionsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  stockSymbol?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStockMomentsArgs = {
  range: ChartRangeEnum;
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStockScreeningArgs = {
  filters?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStocksArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStrategiesArgs = {
  category?: InputMaybe<Scalars['String']['input']>;
  marketType?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStrategyArgs = {
  id?: InputMaybe<Scalars['ID']['input']>;
  slug?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryStrategyBlendsArgs = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySwingSignalsArgs = {
  isActive?: InputMaybe<Scalars['Boolean']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  minMlScore?: InputMaybe<Scalars['Float']['input']>;
  signalType?: InputMaybe<Scalars['String']['input']>;
  symbol?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySwingTradingPicksArgs = {
  strategy?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQuerySwingTradingStatsArgs = {
  period?: InputMaybe<Scalars['String']['input']>;
  strategy?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTestOptionsAnalysisArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTopTradersArgs = {
  period?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTopYieldsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTradingOrdersArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTradingQuoteArgs = {
  symbol: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryTrendingDiscussionsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  timeframe?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserBacktestsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
  status?: InputMaybe<Scalars['String']['input']>;
  strategyVersionId?: InputMaybe<Scalars['ID']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserNfTsArgs = {
  address: Scalars['String']['input'];
  chain?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserNftsArgs = {
  address: Scalars['String']['input'];
  chain?: InputMaybe<Scalars['String']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserPostsArgs = {
  userId: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserVotingPowerArgs = {
  daoAddress: Scalars['String']['input'];
  userAddress: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryUserYieldPositionsArgs = {
  userAddress: Scalars['String']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryWatchlistArgs = {
  id: Scalars['ID']['input'];
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryWatchlistSignalsArgs = {
  threshold?: InputMaybe<Scalars['Float']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryWatchlistsArgs = {
  userId?: InputMaybe<Scalars['ID']['input']>;
};


/**
 * Final Query type exposed by the schema.
 *
 * - Inherits your existing base Query (stocks, dayTradingPicks, etc.)
 * - Adds PremiumQueries (premium_portfolio_metrics, ai_recommendations, etc.)
 * - Adds Broker, Banking, and SBLOC queries
 * - The base Query class has resolve_me which will be available here
 */
export type ExtendedQueryYieldOpportunitiesArgs = {
  asset?: InputMaybe<Scalars['String']['input']>;
  chain?: InputMaybe<Scalars['String']['input']>;
};

/** Result type for follow ticker mutation */
export type FollowTickerResultType = {
  __typename?: 'FollowTickerResultType';
  following?: Maybe<UserType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Follow trader mutation result */
export type FollowTraderResultType = {
  __typename?: 'FollowTraderResultType';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Rust engine forex analysis */
export type ForexAnalysisType = {
  __typename?: 'ForexAnalysisType';
  ask?: Maybe<Scalars['Float']['output']>;
  bid?: Maybe<Scalars['Float']['output']>;
  correlation24h?: Maybe<Scalars['Float']['output']>;
  pair?: Maybe<Scalars['String']['output']>;
  pipValue?: Maybe<Scalars['Float']['output']>;
  resistanceLevel?: Maybe<Scalars['Float']['output']>;
  spread?: Maybe<Scalars['Float']['output']>;
  supportLevel?: Maybe<Scalars['Float']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  trend?: Maybe<Scalars['String']['output']>;
  volatility?: Maybe<Scalars['Float']['output']>;
};

/** Send password reset email */
export type ForgotPassword = {
  __typename?: 'ForgotPassword';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Fundamental analysis scores */
export type FundamentalAnalysisType = {
  __typename?: 'FundamentalAnalysisType';
  debtScore?: Maybe<Scalars['Float']['output']>;
  dividendScore?: Maybe<Scalars['Float']['output']>;
  growthScore?: Maybe<Scalars['Float']['output']>;
  stabilityScore?: Maybe<Scalars['Float']['output']>;
  valuationScore?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for funding history */
export type FundingHistoryType = {
  __typename?: 'FundingHistoryType';
  amount?: Maybe<Scalars['Float']['output']>;
  bankAccountId?: Maybe<Scalars['String']['output']>;
  completedAt?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  initiatedAt?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for funding result */
export type FundingType = {
  __typename?: 'FundingType';
  amount?: Maybe<Scalars['Float']['output']>;
  estimatedCompletion?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  status?: Maybe<Scalars['String']['output']>;
};

/** Generate AI portfolio recommendations based on user's income profile */
export type GenerateAiRecommendations = {
  __typename?: 'GenerateAIRecommendations';
  message?: Maybe<Scalars['String']['output']>;
  recommendations?: Maybe<Array<Maybe<AiPortfolioRecommendationType>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Generate RAHA signals for a strategy (live or historical) */
export type GenerateRahaSignals = {
  __typename?: 'GenerateRAHASignals';
  message?: Maybe<Scalars['String']['output']>;
  signals?: Maybe<Array<Maybe<RahaSignalType>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Generate and optionally email a research report */
export type GenerateResearchReport = {
  __typename?: 'GenerateResearchReport';
  message?: Maybe<Scalars['String']['output']>;
  report?: Maybe<Scalars['JSONString']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type GetChatHistory = {
  __typename?: 'GetChatHistory';
  messages?: Maybe<Array<Maybe<ChatMessageType>>>;
  session?: Maybe<ChatSessionType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result of getting news preferences */
export type GetNewsPreferencesResultType = {
  __typename?: 'GetNewsPreferencesResultType';
  error?: Maybe<Scalars['String']['output']>;
  preferences?: Maybe<NewsPreferencesType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** GraphQL type for governance proposal */
export type GovernanceProposalType = {
  __typename?: 'GovernanceProposalType';
  abstainVotes?: Maybe<Scalars['Float']['output']>;
  actions?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  description?: Maybe<Scalars['String']['output']>;
  endBlock?: Maybe<Scalars['Int']['output']>;
  hasVoted?: Maybe<Scalars['Boolean']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  proposer?: Maybe<Scalars['String']['output']>;
  quorum?: Maybe<Scalars['Float']['output']>;
  startBlock?: Maybe<Scalars['Int']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  totalVotes?: Maybe<Scalars['Float']['output']>;
  userVote?: Maybe<Scalars['String']['output']>;
  votesAgainst?: Maybe<Scalars['Float']['output']>;
  votesFor?: Maybe<Scalars['Float']['output']>;
};

/** Options Greeks */
export type GreeksType = {
  __typename?: 'GreeksType';
  delta?: Maybe<Scalars['Float']['output']>;
  gamma?: Maybe<Scalars['Float']['output']>;
  rho?: Maybe<Scalars['Float']['output']>;
  theta?: Maybe<Scalars['Float']['output']>;
  vega?: Maybe<Scalars['Float']['output']>;
};

/** Detailed holding information */
export type HoldingDetailType = {
  __typename?: 'HoldingDetailType';
  companyName?: Maybe<Scalars['String']['output']>;
  costBasis?: Maybe<Scalars['Float']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  returnAmount?: Maybe<Scalars['Float']['output']>;
  returnPercent?: Maybe<Scalars['Float']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  shares?: Maybe<Scalars['Int']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for IV change point in heatmap */
export type IvChangePointType = {
  __typename?: 'IVChangePointType';
  confidence: Scalars['Float']['output'];
  currentIv: Scalars['Float']['output'];
  expiration: Scalars['String']['output'];
  ivChange1hrPct: Scalars['Float']['output'];
  ivChange24hrPct: Scalars['Float']['output'];
  predictedIv1hr: Scalars['Float']['output'];
  predictedIv24hr: Scalars['Float']['output'];
  strike: Scalars['Float']['output'];
};

/** GraphQL type for IV surface forecast */
export type IvSurfaceForecastType = {
  __typename?: 'IVSurfaceForecastType';
  confidence: Scalars['Float']['output'];
  currentIv: Scalars['JSONString']['output'];
  ivChangeHeatmap: Array<Maybe<IvChangePointType>>;
  predictedIv1hr: Scalars['JSONString']['output'];
  predictedIv24hr: Scalars['JSONString']['output'];
  regime: Scalars['String']['output'];
  symbol: Scalars['String']['output'];
  timestamp: Scalars['String']['output'];
};

export type IncomeProfileType = {
  __typename?: 'IncomeProfileType';
  age: Scalars['Int']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  incomeBracket?: Maybe<Scalars['String']['output']>;
  investmentGoals?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  investmentHorizon?: Maybe<Scalars['String']['output']>;
  riskTolerance?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

/** Initiate funding transfer from bank account to broker account */
export type InitiateFunding = {
  __typename?: 'InitiateFunding';
  funding?: Maybe<FundingType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Initiate a KYC workflow */
export type InitiateKycWorkflow = {
  __typename?: 'InitiateKycWorkflow';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  workflow?: Maybe<KycWorkflowType>;
};

/** Data associated with an insight */
export type InsightDataType = {
  __typename?: 'InsightDataType';
  priceTarget?: Maybe<Scalars['Float']['output']>;
  probability?: Maybe<Scalars['Float']['output']>;
  reasoning?: Maybe<Scalars['String']['output']>;
  timeframe?: Maybe<Scalars['String']['output']>;
};

/** KYC Workflow type */
export type KycWorkflowType = {
  __typename?: 'KycWorkflowType';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  currentStep?: Maybe<Scalars['Int']['output']>;
  estimatedCompletion?: Maybe<Scalars['DateTime']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  stepsRequired?: Maybe<Array<Maybe<Scalars['Int']['output']>>>;
  userId?: Maybe<Scalars['String']['output']>;
  workflowType?: Maybe<Scalars['String']['output']>;
};

/** Largest options trade */
export type LargestTradeType = {
  __typename?: 'LargestTradeType';
  contractSymbol?: Maybe<Scalars['String']['output']>;
  isBlock?: Maybe<Scalars['Boolean']['output']>;
  isCall?: Maybe<Scalars['Boolean']['output']>;
  isSweep?: Maybe<Scalars['Boolean']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  size?: Maybe<Scalars['Int']['output']>;
  time?: Maybe<Scalars['String']['output']>;
};

/** Last training timestamps */
export type LastTrainingType = {
  __typename?: 'LastTrainingType';
  AGGRESSIVE?: Maybe<Scalars['String']['output']>;
  SAFE?: Maybe<Scalars['String']['output']>;
};

/** Portfolio leaderboard entry */
export type LeaderboardEntryType = {
  __typename?: 'LeaderboardEntryType';
  bestPerformer?: Maybe<Scalars['String']['output']>;
  holdingsCount?: Maybe<Scalars['Int']['output']>;
  rank?: Maybe<Scalars['Int']['output']>;
  totalReturnPct?: Maybe<Scalars['Float']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
  userEmail?: Maybe<Scalars['String']['output']>;
  userId?: Maybe<Scalars['Int']['output']>;
  userName?: Maybe<Scalars['String']['output']>;
  worstPerformer?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for lesson */
export type LessonType = {
  __typename?: 'LessonType';
  difficulty?: Maybe<Scalars['String']['output']>;
  estimatedTimeMinutes?: Maybe<Scalars['Int']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  quiz?: Maybe<QuizType>;
  skillsTargeted?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  streak?: Maybe<Scalars['Int']['output']>;
  text?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  voiceNarration?: Maybe<Scalars['String']['output']>;
  xpEarned?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for level progress */
export type LevelProgressType = {
  __typename?: 'LevelProgressType';
  currentLevel?: Maybe<Scalars['Int']['output']>;
  currentXp?: Maybe<Scalars['Int']['output']>;
  nextLevelXp?: Maybe<Scalars['Int']['output']>;
  progressPercentage?: Maybe<Scalars['Float']['output']>;
};

/** Like post mutation result */
export type LikePostResultType = {
  __typename?: 'LikePostResultType';
  likes?: Maybe<Scalars['Int']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Like or unlike a swing trading signal */
export type LikeSignal = {
  __typename?: 'LikeSignal';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type LikeType = {
  __typename?: 'LikeType';
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  post: PostType;
  user: UserType;
};

/** Link a bank account manually (fallback when Yodlee is not available) */
export type LinkBankAccount = {
  __typename?: 'LinkBankAccount';
  bankAccount?: Maybe<LinkBankAccountResultType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result type for linkBankAccount mutation */
export type LinkBankAccountResultType = {
  __typename?: 'LinkBankAccountResultType';
  accountType?: Maybe<Scalars['String']['output']>;
  bankName?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  status?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for live simulation */
export type LiveSimType = {
  __typename?: 'LiveSimType';
  currentBalance?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  initialBalance?: Maybe<Scalars['Float']['output']>;
  learningObjectives?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  mode?: Maybe<Scalars['String']['output']>;
  performanceMetrics?: Maybe<PerformanceMetricsType>;
  regimeContext?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  voiceFeedbackEnabled?: Maybe<Scalars['Boolean']['output']>;
};

/** Log the outcome of a day trading pick */
export type LogDayTradingOutcome = {
  __typename?: 'LogDayTradingOutcome';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** ML system status */
export type MlSystemStatusType = {
  __typename?: 'MLSystemStatusType';
  bandit?: Maybe<BanditType>;
  lastTraining?: Maybe<LastTrainingType>;
  mlAvailable?: Maybe<Scalars['Boolean']['output']>;
  models?: Maybe<ModelsType>;
  outcomeTracking?: Maybe<OutcomeTrackingType>;
};

/** Macro market data */
export type MacroType = {
  __typename?: 'MacroType';
  marketSentiment?: Maybe<Scalars['String']['output']>;
  riskAppetite?: Maybe<Scalars['Float']['output']>;
  vix?: Maybe<Scalars['Float']['output']>;
};

/** Mark all notifications as read */
export type MarkAllNotificationsRead = {
  __typename?: 'MarkAllNotificationsRead';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Mark a notification as read */
export type MarkNotificationRead = {
  __typename?: 'MarkNotificationRead';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** AI-powered market insight */
export type MarketInsightType = {
  __typename?: 'MarketInsightType';
  category: Scalars['String']['output'];
  confidence: Scalars['Float']['output'];
  data?: Maybe<InsightDataType>;
  id: Scalars['ID']['output'];
  impact: Scalars['String']['output'];
  sentiment: Scalars['String']['output'];
  source?: Maybe<Scalars['String']['output']>;
  summary: Scalars['String']['output'];
  symbols?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  tags?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  timestamp: Scalars['DateTime']['output'];
  title: Scalars['String']['output'];
};

/** AI-powered market outlook */
export type MarketOutlookType = {
  __typename?: 'MarketOutlookType';
  confidence?: Maybe<Scalars['Float']['output']>;
  keyFactors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  overallSentiment?: Maybe<Scalars['String']['output']>;
  risks?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
};

/** Market regime indicators */
export type MarketRegimeIndicatorsType = {
  __typename?: 'MarketRegimeIndicatorsType';
  momentum?: Maybe<Scalars['Float']['output']>;
  trend?: Maybe<Scalars['String']['output']>;
  volatility?: Maybe<Scalars['Float']['output']>;
  volume?: Maybe<Scalars['Float']['output']>;
};

/** Market regime analysis */
export type MarketRegimeType = {
  __typename?: 'MarketRegimeType';
  confidence: Scalars['Float']['output'];
  current: Scalars['String']['output'];
  indicators?: Maybe<MarketRegimeIndicatorsType>;
  recommendations?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  transitions?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
};

/** Market sentiment from options data */
export type MarketSentimentType = {
  __typename?: 'MarketSentimentType';
  impliedVolatilityRank?: Maybe<Scalars['Float']['output']>;
  putCallRatio?: Maybe<Scalars['Float']['output']>;
  sentiment?: Maybe<Scalars['String']['output']>;
  sentimentDescription?: Maybe<Scalars['String']['output']>;
  sentimentScore?: Maybe<Scalars['Float']['output']>;
  skew?: Maybe<Scalars['Float']['output']>;
};

/** ML model training result */
export type ModelResultType = {
  __typename?: 'ModelResultType';
  auc?: Maybe<Scalars['Float']['output']>;
  avgReturn?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  hitRate?: Maybe<Scalars['Float']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  mode?: Maybe<Scalars['String']['output']>;
  modelId?: Maybe<Scalars['String']['output']>;
  precisionAt3?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  trainingSamples?: Maybe<Scalars['Int']['output']>;
  validationSamples?: Maybe<Scalars['Int']['output']>;
};

/** ML models information */
export type ModelsType = {
  __typename?: 'ModelsType';
  aggressiveModel?: Maybe<Scalars['String']['output']>;
  safeModel?: Maybe<Scalars['String']['output']>;
};

/** Enum for moment categories */
export enum MomentCategoryEnum {
  EARNINGS = 'EARNINGS',
  INSIDER = 'INSIDER',
  MACRO = 'MACRO',
  NEWS = 'NEWS',
  OTHER = 'OTHER',
  SENTIMENT = 'SENTIMENT'
}

/** GraphQL type for NFT */
export type NftType = {
  __typename?: 'NFTType';
  attributes?: Maybe<Array<Maybe<Scalars['JSONString']['output']>>>;
  chain?: Maybe<Scalars['String']['output']>;
  collectionName?: Maybe<Scalars['String']['output']>;
  contractAddress?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  floorPrice?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  imageUrl?: Maybe<Scalars['String']['output']>;
  lastSalePrice?: Maybe<Scalars['Float']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  tokenId?: Maybe<Scalars['String']['output']>;
};

/** News preferences input */
export type NewsPreferencesInputType = {
  breakingNews?: InputMaybe<Scalars['Boolean']['input']>;
  companyNews?: InputMaybe<Scalars['Boolean']['input']>;
  cryptoNews?: InputMaybe<Scalars['Boolean']['input']>;
  earningsNews?: InputMaybe<Scalars['Boolean']['input']>;
  frequency?: InputMaybe<Scalars['String']['input']>;
  marketNews?: InputMaybe<Scalars['Boolean']['input']>;
  personalStocks?: InputMaybe<Scalars['Boolean']['input']>;
  quietEnd?: InputMaybe<Scalars['String']['input']>;
  quietHours?: InputMaybe<Scalars['Boolean']['input']>;
  quietStart?: InputMaybe<Scalars['String']['input']>;
};

/** News preferences */
export type NewsPreferencesType = {
  __typename?: 'NewsPreferencesType';
  breakingNews?: Maybe<Scalars['Boolean']['output']>;
  companyNews?: Maybe<Scalars['Boolean']['output']>;
  cryptoNews?: Maybe<Scalars['Boolean']['output']>;
  earningsNews?: Maybe<Scalars['Boolean']['output']>;
  frequency?: Maybe<Scalars['String']['output']>;
  marketNews?: Maybe<Scalars['Boolean']['output']>;
  personalStocks?: Maybe<Scalars['Boolean']['output']>;
  quietEnd?: Maybe<Scalars['String']['output']>;
  quietHours?: Maybe<Scalars['Boolean']['output']>;
  quietStart?: Maybe<Scalars['String']['output']>;
};

/** News sentiment data */
export type NewsSentimentType = {
  __typename?: 'NewsSentimentType';
  articleCount?: Maybe<Scalars['Int']['output']>;
  negativeArticles?: Maybe<Scalars['Int']['output']>;
  neutralArticles?: Maybe<Scalars['Int']['output']>;
  positiveArticles?: Maybe<Scalars['Int']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  topHeadlines?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
};

/** GraphQL type for NotificationPreferences */
export type NotificationPreferencesType = {
  __typename?: 'NotificationPreferencesType';
  /** Enable notifications for backtest completion */
  backtestNotificationsEnabled: Scalars['Boolean']['output'];
  /** Only notify for successful backtests (win rate > 50%) */
  backtestSuccessOnly: Scalars['Boolean']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['UUID']['output'];
  /** Whether push notifications are enabled */
  pushEnabled: Scalars['Boolean']['output'];
  /** Expo push notification token */
  pushToken?: Maybe<Scalars['String']['output']>;
  /** Enable quiet hours */
  quietHoursEnabled: Scalars['Boolean']['output'];
  /** End of quiet hours (e.g., 08:00) */
  quietHoursEnd?: Maybe<Scalars['Time']['output']>;
  /** Start of quiet hours (e.g., 22:00) */
  quietHoursStart?: Maybe<Scalars['Time']['output']>;
  /** Minimum confidence score to trigger notification (0.00-1.00) */
  signalConfidenceThreshold: Scalars['Decimal']['output'];
  /** Enable notifications for new RAHA signals */
  signalNotificationsEnabled: Scalars['Boolean']['output'];
  signalSymbols?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

/** Notification settings type */
export type NotificationSettingsType = {
  __typename?: 'NotificationSettingsType';
  newsUpdates?: Maybe<Scalars['Boolean']['output']>;
  orderUpdates?: Maybe<Scalars['Boolean']['output']>;
  priceAlerts?: Maybe<Scalars['Boolean']['output']>;
  systemUpdates?: Maybe<Scalars['Boolean']['output']>;
};

/** Notification type */
export type NotificationType = {
  __typename?: 'NotificationType';
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isRead?: Maybe<Scalars['Boolean']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** Obtain JSON Web Token mutation */
export type ObtainJsonWebToken = {
  __typename?: 'ObtainJSONWebToken';
  payload: Scalars['GenericScalar']['output'];
  refreshExpiresIn: Scalars['Int']['output'];
  token: Scalars['String']['output'];
};

/** GraphQL type for one-tap trade leg */
export type OneTapLegType = {
  __typename?: 'OneTapLegType';
  action: Scalars['String']['output'];
  expiration: Scalars['String']['output'];
  optionType: Scalars['String']['output'];
  premium: Scalars['Float']['output'];
  quantity: Scalars['Int']['output'];
  strike: Scalars['Float']['output'];
};

/** GraphQL type for one-tap trade recommendation */
export type OneTapTradeType = {
  __typename?: 'OneTapTradeType';
  confidence: Scalars['Float']['output'];
  daysToExpiration: Scalars['Int']['output'];
  entryPrice: Scalars['Float']['output'];
  expectedEdge: Scalars['Float']['output'];
  legs: Array<Maybe<OneTapLegType>>;
  maxLoss: Scalars['Float']['output'];
  maxProfit: Scalars['Float']['output'];
  probabilityOfProfit: Scalars['Float']['output'];
  reasoning: Scalars['String']['output'];
  stopLoss: Scalars['Float']['output'];
  strategy: Scalars['String']['output'];
  strategyType: Scalars['String']['output'];
  symbol: Scalars['String']['output'];
  takeProfit: Scalars['Float']['output'];
  totalCost: Scalars['Float']['output'];
  totalCredit: Scalars['Float']['output'];
};

/** Optimized pool allocation */
export type OptimizedPoolType = {
  __typename?: 'OptimizedPoolType';
  apy?: Maybe<Scalars['Float']['output']>;
  chain?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  protocol?: Maybe<Scalars['String']['output']>;
  risk?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  tvl?: Maybe<Scalars['Float']['output']>;
  weight?: Maybe<Scalars['Float']['output']>;
};

/** Options alert notification GraphQL type */
export type OptionsAlertNotificationType = {
  __typename?: 'OptionsAlertNotificationType';
  id?: Maybe<Scalars['ID']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  notificationType?: Maybe<Scalars['String']['output']>;
  sentAt?: Maybe<Scalars['String']['output']>;
};

/** Options alert GraphQL type */
export type OptionsAlertType = {
  __typename?: 'OptionsAlertType';
  alertType?: Maybe<Scalars['String']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  direction?: Maybe<Scalars['String']['output']>;
  expiration?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  notificationSent?: Maybe<Scalars['Boolean']['output']>;
  optionType?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  strike?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  targetValue?: Maybe<Scalars['Float']['output']>;
  triggeredAt?: Maybe<Scalars['String']['output']>;
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** Complete options analysis */
export type OptionsAnalysisType = {
  __typename?: 'OptionsAnalysisType';
  impliedVolatilityRank?: Maybe<Scalars['Float']['output']>;
  marketSentiment?: Maybe<MarketSentimentType>;
  optionsChain?: Maybe<OptionsChainType>;
  putCallRatio?: Maybe<Scalars['Float']['output']>;
  recommendedStrategies?: Maybe<Array<Maybe<OptionsStrategyType>>>;
  sentimentDescription?: Maybe<Scalars['String']['output']>;
  sentimentScore?: Maybe<Scalars['Float']['output']>;
  skew?: Maybe<Scalars['Float']['output']>;
  underlyingPrice?: Maybe<Scalars['Float']['output']>;
  underlyingSymbol?: Maybe<Scalars['String']['output']>;
  unusualFlow?: Maybe<UnusualFlowSummaryType>;
  unusualFlowSummary?: Maybe<UnusualFlowSummaryType>;
};

/** Options chain for a symbol */
export type OptionsChainType = {
  __typename?: 'OptionsChainType';
  calls?: Maybe<Array<Maybe<OptionsContractType>>>;
  expirationDates?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  greeks?: Maybe<GreeksType>;
  puts?: Maybe<Array<Maybe<OptionsContractType>>>;
};

/** Individual options contract */
export type OptionsContractType = {
  __typename?: 'OptionsContractType';
  ask?: Maybe<Scalars['Float']['output']>;
  bid?: Maybe<Scalars['Float']['output']>;
  contractSymbol?: Maybe<Scalars['String']['output']>;
  daysToExpiration?: Maybe<Scalars['Int']['output']>;
  delta?: Maybe<Scalars['Float']['output']>;
  expirationDate?: Maybe<Scalars['String']['output']>;
  gamma?: Maybe<Scalars['Float']['output']>;
  impliedVolatility?: Maybe<Scalars['Float']['output']>;
  intrinsicValue?: Maybe<Scalars['Float']['output']>;
  lastPrice?: Maybe<Scalars['Float']['output']>;
  openInterest?: Maybe<Scalars['Int']['output']>;
  optionType?: Maybe<Scalars['String']['output']>;
  rho?: Maybe<Scalars['Float']['output']>;
  strike?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  theta?: Maybe<Scalars['Float']['output']>;
  timeValue?: Maybe<Scalars['Float']['output']>;
  vega?: Maybe<Scalars['Float']['output']>;
  volume?: Maybe<Scalars['Int']['output']>;
};

/** Options flow data point for smart money flow chart */
export type OptionsFlowDataPointType = {
  __typename?: 'OptionsFlowDataPointType';
  date?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  putCallRatio?: Maybe<Scalars['Float']['output']>;
  sweepCount?: Maybe<Scalars['Int']['output']>;
  unusualVolumePercent?: Maybe<Scalars['Float']['output']>;
};

/** Options flow data for a symbol */
export type OptionsFlowType = {
  __typename?: 'OptionsFlowType';
  largestTrades?: Maybe<Array<Maybe<LargestTradeType>>>;
  putCallRatio?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  totalCallVolume?: Maybe<Scalars['Int']['output']>;
  totalPutVolume?: Maybe<Scalars['Int']['output']>;
  unusualActivity?: Maybe<Array<Maybe<UnusualActivityType>>>;
};

/** Options trading strategy */
export type OptionsStrategyType = {
  __typename?: 'OptionsStrategyType';
  breakevenPoints?: Maybe<Array<Maybe<Scalars['Float']['output']>>>;
  daysToExpiration?: Maybe<Scalars['Int']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  marketOutlook?: Maybe<Scalars['String']['output']>;
  maxLoss?: Maybe<Scalars['Float']['output']>;
  maxProfit?: Maybe<Scalars['Float']['output']>;
  probabilityOfProfit?: Maybe<Scalars['Float']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  riskRewardRatio?: Maybe<Scalars['Float']['output']>;
  strategyName?: Maybe<Scalars['String']['output']>;
  strategyType?: Maybe<Scalars['String']['output']>;
  totalCost?: Maybe<Scalars['Float']['output']>;
  totalCredit?: Maybe<Scalars['Float']['output']>;
};

/** Oracle insight response */
export type OracleInsightType = {
  __typename?: 'OracleInsightType';
  answer: Scalars['String']['output'];
  confidence: Scalars['Float']['output'];
  id: Scalars['ID']['output'];
  question: Scalars['String']['output'];
  relatedInsights?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  sources?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  timestamp: Scalars['DateTime']['output'];
};

/** Complete order dashboard data */
export type OrderDashboardType = {
  __typename?: 'OrderDashboardType';
  activeOrders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  filledOrders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  /** Whether there are more filled orders to load */
  filledOrdersHasMore?: Maybe<Scalars['Boolean']['output']>;
  metrics?: Maybe<OrderMetricsType>;
  orders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  /** Whether there are more orders to load */
  ordersHasMore?: Maybe<Scalars['Boolean']['output']>;
  positions?: Maybe<Array<Maybe<BrokerPositionType>>>;
  rahaOrders?: Maybe<Array<Maybe<BrokerOrderType>>>;
  /** Whether there are more RAHA orders to load */
  rahaOrdersHasMore?: Maybe<Scalars['Boolean']['output']>;
  riskStatus?: Maybe<RiskStatusType>;
};

/** Metrics for order dashboard */
export type OrderMetricsType = {
  __typename?: 'OrderMetricsType';
  avgLoss?: Maybe<Scalars['Float']['output']>;
  avgWin?: Maybe<Scalars['Float']['output']>;
  largestLoss?: Maybe<Scalars['Float']['output']>;
  largestWin?: Maybe<Scalars['Float']['output']>;
  losingTrades?: Maybe<Scalars['Int']['output']>;
  profitFactor?: Maybe<Scalars['Float']['output']>;
  totalPnl?: Maybe<Scalars['Float']['output']>;
  totalPnlPercent?: Maybe<Scalars['Float']['output']>;
  totalTrades?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
  winningTrades?: Maybe<Scalars['Int']['output']>;
};

/** Outcome tracking information */
export type OutcomeTrackingType = {
  __typename?: 'OutcomeTrackingType';
  recentOutcomes?: Maybe<Scalars['Int']['output']>;
  totalOutcomes?: Maybe<Scalars['Int']['output']>;
};

/** Paper trading account summary */
export type PaperTradingAccountSummaryType = {
  __typename?: 'PaperTradingAccountSummaryType';
  account?: Maybe<PaperTradingAccountType>;
  openOrders?: Maybe<Array<Maybe<PaperTradingOrderType>>>;
  positions?: Maybe<Array<Maybe<PaperTradingPositionType>>>;
  recentTrades?: Maybe<Array<Maybe<PaperTradingTradeType>>>;
  statistics?: Maybe<PaperTradingStatisticsType>;
};

/** Paper trading account GraphQL type */
export type PaperTradingAccountType = {
  __typename?: 'PaperTradingAccountType';
  createdAt: Scalars['DateTime']['output'];
  currentBalance: Scalars['Decimal']['output'];
  id: Scalars['ID']['output'];
  initialBalance: Scalars['Decimal']['output'];
  losingTrades: Scalars['Int']['output'];
  orders: Array<PaperTradingOrderType>;
  positions: Array<PaperTradingPositionType>;
  realizedPnl: Scalars['Decimal']['output'];
  totalPnl: Scalars['Decimal']['output'];
  totalPnlPercent: Scalars['Decimal']['output'];
  totalTrades: Scalars['Int']['output'];
  totalValue: Scalars['Decimal']['output'];
  trades: Array<PaperTradingTradeType>;
  unrealizedPnl: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
  winRate: Scalars['Decimal']['output'];
  winningTrades: Scalars['Int']['output'];
};

/** Paper trading order GraphQL type */
export type PaperTradingOrderType = {
  __typename?: 'PaperTradingOrderType';
  account: PaperTradingAccountType;
  buyTrades: Array<PaperTradingTradeType>;
  commission: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  filledAt?: Maybe<Scalars['DateTime']['output']>;
  filledPrice?: Maybe<Scalars['Decimal']['output']>;
  filledQuantity: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  limitPrice?: Maybe<Scalars['Decimal']['output']>;
  orderType: CorePaperTradingOrderOrderTypeChoices;
  quantity: Scalars['Int']['output'];
  rejectionReason?: Maybe<Scalars['String']['output']>;
  sellTrades: Array<PaperTradingTradeType>;
  side: CorePaperTradingOrderSideChoices;
  status: CorePaperTradingOrderStatusChoices;
  stock: StockType;
  stockName?: Maybe<Scalars['String']['output']>;
  stockSymbol?: Maybe<Scalars['String']['output']>;
  stopPrice?: Maybe<Scalars['Decimal']['output']>;
  totalCost: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** Paper trading position GraphQL type */
export type PaperTradingPositionType = {
  __typename?: 'PaperTradingPositionType';
  account: PaperTradingAccountType;
  averagePrice: Scalars['Decimal']['output'];
  costBasis: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  currentPrice: Scalars['Decimal']['output'];
  id: Scalars['ID']['output'];
  marketValue: Scalars['Decimal']['output'];
  shares: Scalars['Int']['output'];
  stock: StockType;
  stockName?: Maybe<Scalars['String']['output']>;
  stockSymbol?: Maybe<Scalars['String']['output']>;
  unrealizedPnl: Scalars['Decimal']['output'];
  unrealizedPnlPercent: Scalars['Decimal']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

/** Paper trading statistics */
export type PaperTradingStatisticsType = {
  __typename?: 'PaperTradingStatisticsType';
  losingTrades?: Maybe<Scalars['Int']['output']>;
  realizedPnl?: Maybe<Scalars['Float']['output']>;
  totalPnl?: Maybe<Scalars['Float']['output']>;
  totalPnlPercent?: Maybe<Scalars['Float']['output']>;
  totalTrades?: Maybe<Scalars['Int']['output']>;
  unrealizedPnl?: Maybe<Scalars['Float']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
  winningTrades?: Maybe<Scalars['Int']['output']>;
};

/** Paper trading trade GraphQL type */
export type PaperTradingTradeType = {
  __typename?: 'PaperTradingTradeType';
  account: PaperTradingAccountType;
  buyOrder?: Maybe<PaperTradingOrderType>;
  commission: Scalars['Decimal']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  price: Scalars['Decimal']['output'];
  quantity: Scalars['Int']['output'];
  realizedPnl: Scalars['Decimal']['output'];
  realizedPnlPercent: Scalars['Decimal']['output'];
  sellOrder?: Maybe<PaperTradingOrderType>;
  side: Scalars['String']['output'];
  stock: StockType;
  stockName?: Maybe<Scalars['String']['output']>;
  stockSymbol?: Maybe<Scalars['String']['output']>;
  totalValue: Scalars['Decimal']['output'];
};

/** Parse a voice command into a trading order */
export type ParseVoiceCommand = {
  __typename?: 'ParseVoiceCommand';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  parsedOrder?: Maybe<ParsedOrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Parsed order from voice command */
export type ParsedOrderType = {
  __typename?: 'ParsedOrderType';
  confidence?: Maybe<Scalars['Float']['output']>;
  confirmationMessage?: Maybe<Scalars['String']['output']>;
  orderType?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  quantity?: Maybe<Scalars['Int']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** Pattern recognition for swing signals */
export type PatternRecognitionType = {
  __typename?: 'PatternRecognitionType';
  confidence?: Maybe<Scalars['Float']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  signal?: Maybe<Scalars['String']['output']>;
  timeframe?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for live simulation performance metrics */
export type PerformanceMetricsType = {
  __typename?: 'PerformanceMetricsType';
  returnPercentage?: Maybe<Scalars['Float']['output']>;
  totalPnL?: Maybe<Scalars['Float']['output']>;
  totalTrades?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** Performance metrics for scans and playbooks */
export type PerformanceType = {
  __typename?: 'PerformanceType';
  averageReturn?: Maybe<Scalars['Float']['output']>;
  avgHoldTime?: Maybe<Scalars['Int']['output']>;
  lastUpdated?: Maybe<Scalars['String']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  successRate?: Maybe<Scalars['Float']['output']>;
  totalRuns?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** Place a bracket options order (parent + take profit + stop loss) */
export type PlaceBracketOptionsOrder = {
  __typename?: 'PlaceBracketOptionsOrder';
  error?: Maybe<Scalars['String']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  parentOrderId?: Maybe<Scalars['String']['output']>;
  stopLossOrderId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  takeProfitOrderId?: Maybe<Scalars['String']['output']>;
};

/** Place a limit order (alias for placeOrder with order_type='LIMIT') */
export type PlaceLimitOrder = {
  __typename?: 'PlaceLimitOrder';
  error?: Maybe<Scalars['String']['output']>;
  order?: Maybe<BrokerOrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Place a multi-leg options order (spreads, straddles, etc.) */
export type PlaceMultiLegOptionsOrder = {
  __typename?: 'PlaceMultiLegOptionsOrder';
  error?: Maybe<Scalars['String']['output']>;
  orderIds?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Place an options order with guardrails */
export type PlaceOptionsOrder = {
  __typename?: 'PlaceOptionsOrder';
  alpacaOrderId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Place a broker order with guardrails */
export type PlaceOrder = {
  __typename?: 'PlaceOrder';
  alpacaOrderId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  /** Execution suggestion that was used */
  executionSuggestion?: Maybe<Scalars['JSONString']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Place a paper trading order */
export type PlacePaperOrder = {
  __typename?: 'PlacePaperOrder';
  message?: Maybe<Scalars['String']['output']>;
  order?: Maybe<PaperTradingOrderType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Place a stock order (alias for placeOrder with stock-specific defaults) */
export type PlaceStockOrder = {
  __typename?: 'PlaceStockOrder';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Playbook definition for institutional strategies */
export type PlaybookType = {
  __typename?: 'PlaybookType';
  author?: Maybe<Scalars['String']['output']>;
  category?: Maybe<Scalars['String']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isClonable?: Maybe<Scalars['Boolean']['output']>;
  isPublic?: Maybe<Scalars['Boolean']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  performance?: Maybe<PerformanceType>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  tags?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  version?: Maybe<Scalars['String']['output']>;
};

/** Pool analytics data point */
export type PoolAnalyticsPointType = {
  __typename?: 'PoolAnalyticsPointType';
  date?: Maybe<Scalars['String']['output']>;
  feeApy?: Maybe<Scalars['Float']['output']>;
  ilEstimate?: Maybe<Scalars['Float']['output']>;
  netApy?: Maybe<Scalars['Float']['output']>;
};

/** Portfolio analysis results */
export type PortfolioAnalysisType = {
  __typename?: 'PortfolioAnalysisType';
  diversificationScore?: Maybe<Scalars['Float']['output']>;
  numHoldings?: Maybe<Scalars['Int']['output']>;
  riskScore?: Maybe<Scalars['Float']['output']>;
  sectorBreakdown?: Maybe<Scalars['JSONString']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
};

/** Individual stock holding within a portfolio */
export type PortfolioHoldingType = {
  __typename?: 'PortfolioHoldingType';
  averagePrice?: Maybe<Scalars['Float']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  shares?: Maybe<Scalars['Int']['output']>;
  stock?: Maybe<StockType>;
  totalValue?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

/** Advanced portfolio performance metrics */
export type PortfolioMetricsType = {
  __typename?: 'PortfolioMetricsType';
  alpha?: Maybe<Scalars['Float']['output']>;
  beta?: Maybe<Scalars['Float']['output']>;
  dayChange?: Maybe<Scalars['Float']['output']>;
  dayChangePercent?: Maybe<Scalars['Float']['output']>;
  holdings?: Maybe<Array<Maybe<HoldingDetailType>>>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  riskMetrics?: Maybe<Scalars['JSONString']['output']>;
  sectorAllocation?: Maybe<Scalars['JSONString']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  totalCost?: Maybe<Scalars['Float']['output']>;
  totalReturn?: Maybe<Scalars['Float']['output']>;
  totalReturnPercent?: Maybe<Scalars['Float']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
  volatility?: Maybe<Scalars['Float']['output']>;
};

/** Portfolio sharing information */
export type PortfolioSharingInfoType = {
  __typename?: 'PortfolioSharingInfoType';
  isPublic?: Maybe<Scalars['Boolean']['output']>;
  portfolioSummary?: Maybe<Scalars['JSONString']['output']>;
  shareToken?: Maybe<Scalars['String']['output']>;
  totalFollowers?: Maybe<Scalars['Int']['output']>;
};

/** Portfolio-wide signal summary */
export type PortfolioSignalsType = {
  __typename?: 'PortfolioSignalsType';
  overallSentiment?: Maybe<Scalars['String']['output']>;
  portfolioSignals?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  strongBuyCount?: Maybe<Scalars['Int']['output']>;
  strongSellCount?: Maybe<Scalars['Int']['output']>;
  totalPositions?: Maybe<Scalars['Int']['output']>;
};

/** Summary of all user portfolios */
export type PortfolioSummaryType = {
  __typename?: 'PortfolioSummaryType';
  portfolios?: Maybe<Array<Maybe<PortfolioType>>>;
  totalPortfolios?: Maybe<Scalars['Int']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
};

/** Virtual portfolio containing multiple holdings */
export type PortfolioType = {
  __typename?: 'PortfolioType';
  holdings?: Maybe<Array<Maybe<PortfolioHoldingType>>>;
  holdingsCount?: Maybe<Scalars['Int']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
};

/** Position size calculation result */
export type PositionSizeType = {
  __typename?: 'PositionSizeType';
  dollarRisk?: Maybe<Scalars['Float']['output']>;
  maxSharesFixedRisk?: Maybe<Scalars['Int']['output']>;
  maxSharesPosition?: Maybe<Scalars['Int']['output']>;
  method?: Maybe<Scalars['String']['output']>;
  positionPct?: Maybe<Scalars['Float']['output']>;
  positionSize?: Maybe<Scalars['Int']['output']>;
  positionValue?: Maybe<Scalars['Float']['output']>;
  riskPerShare?: Maybe<Scalars['Float']['output']>;
  riskPerTradePct?: Maybe<Scalars['Float']['output']>;
};

/** Active position information */
export type PositionType = {
  __typename?: 'PositionType';
  atrStopPrice?: Maybe<Scalars['Float']['output']>;
  currentPnl?: Maybe<Scalars['Float']['output']>;
  entryPrice?: Maybe<Scalars['Float']['output']>;
  entryTime?: Maybe<Scalars['String']['output']>;
  maxHoldUntil?: Maybe<Scalars['String']['output']>;
  quantity?: Maybe<Scalars['Int']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  stopLossPrice?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  takeProfitPrice?: Maybe<Scalars['Float']['output']>;
  timeRemainingMinutes?: Maybe<Scalars['Int']['output']>;
};

export type PostType = {
  __typename?: 'PostType';
  comments: Array<CommentType>;
  content: Scalars['String']['output'];
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  image?: Maybe<Scalars['String']['output']>;
  likes: Array<LikeType>;
  user: UserType;
};

/** GraphQL type for pre-market scan results */
export type PreMarketDataType = {
  __typename?: 'PreMarketDataType';
  asOf?: Maybe<Scalars['String']['output']>;
  minutesUntilOpen?: Maybe<Scalars['Int']['output']>;
  mode?: Maybe<Scalars['String']['output']>;
  picks?: Maybe<Array<Maybe<PreMarketPickType>>>;
  totalScanned?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for pre-market pick */
export type PreMarketPickType = {
  __typename?: 'PreMarketPickType';
  marketCap?: Maybe<Scalars['Float']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  preMarketChangePct?: Maybe<Scalars['Float']['output']>;
  preMarketPrice?: Maybe<Scalars['Float']['output']>;
  prevClose?: Maybe<Scalars['Float']['output']>;
  scannedAt?: Maybe<Scalars['String']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  volume?: Maybe<Scalars['Int']['output']>;
};

/** AI prediction for a stock */
export type PredictionType = {
  __typename?: 'PredictionType';
  confidence: Scalars['Float']['output'];
  direction: Scalars['String']['output'];
  factors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  priceTarget: Scalars['Float']['output'];
  probability: Scalars['Float']['output'];
  timeframe: Scalars['String']['output'];
};

/** Input type for updating privacy settings */
export type PrivacySettingsInput = {
  aiAnalysisEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  analyticsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  dataRetentionDays?: InputMaybe<Scalars['Int']['input']>;
  dataSharingEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  mlPredictionsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  sessionTrackingEnabled?: InputMaybe<Scalars['Boolean']['input']>;
};

/** Privacy settings for a user */
export type PrivacySettingsType = {
  __typename?: 'PrivacySettingsType';
  aiAnalysisEnabled: Scalars['Boolean']['output'];
  analyticsEnabled: Scalars['Boolean']['output'];
  dataRetentionDays: Scalars['Int']['output'];
  dataSharingEnabled: Scalars['Boolean']['output'];
  lastUpdated?: Maybe<Scalars['DateTime']['output']>;
  mlPredictionsEnabled: Scalars['Boolean']['output'];
  sessionTrackingEnabled: Scalars['Boolean']['output'];
};

/** Profile input for AI recommendations */
export type ProfileInput = {
  /** User age */
  age?: InputMaybe<Scalars['Int']['input']>;
  /** Income bracket */
  incomeBracket?: InputMaybe<Scalars['String']['input']>;
  /** Investment goals */
  investmentGoals?: InputMaybe<Array<InputMaybe<Scalars['String']['input']>>>;
  /** Investment horizon in years */
  investmentHorizonYears?: InputMaybe<Scalars['Int']['input']>;
  /** Risk tolerance: Conservative, Moderate, Aggressive */
  riskTolerance?: InputMaybe<Scalars['String']['input']>;
};

/** GraphQL type for quest progress update result */
export type QuestProgressResultType = {
  __typename?: 'QuestProgressResultType';
  completed?: Maybe<Scalars['Boolean']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  nextQuestAvailable?: Maybe<Scalars['Boolean']['output']>;
  progress?: Maybe<Scalars['Float']['output']>;
  questId?: Maybe<Scalars['String']['output']>;
  rewardsEarned?: Maybe<Array<Maybe<RewardType>>>;
  streakBonus?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for quest */
export type QuestType = {
  __typename?: 'QuestType';
  difficulty?: Maybe<Scalars['String']['output']>;
  expiresAt?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  narration?: Maybe<Scalars['String']['output']>;
  progress?: Maybe<Scalars['Float']['output']>;
  questType?: Maybe<Scalars['String']['output']>;
  rewards?: Maybe<Array<Maybe<RewardType>>>;
  scenarios?: Maybe<Array<Maybe<ScenarioType>>>;
  timeLimitMinutes?: Maybe<Scalars['Int']['output']>;
  topic?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for quiz submission result */
export type QuizResultType = {
  __typename?: 'QuizResultType';
  badgesEarned?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  feedback?: Maybe<Scalars['String']['output']>;
  levelProgress?: Maybe<LevelProgressType>;
  nextRecommendation?: Maybe<Scalars['String']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  streakStatus?: Maybe<Scalars['String']['output']>;
  totalXp?: Maybe<Scalars['Int']['output']>;
  xpBonus?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for quiz */
export type QuizType = {
  __typename?: 'QuizType';
  correct?: Maybe<Scalars['Int']['output']>;
  explanation?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  options?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  question?: Maybe<Scalars['String']['output']>;
  voiceHint?: Maybe<Scalars['String']['output']>;
};

/** Stock quote data */
export type QuoteType = {
  __typename?: 'QuoteType';
  chg?: Maybe<Scalars['Float']['output']>;
  chgPct?: Maybe<Scalars['Float']['output']>;
  high?: Maybe<Scalars['Float']['output']>;
  low?: Maybe<Scalars['Float']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  volume?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for RAHA Backtest Run */
export type RahaBacktestRunType = {
  __typename?: 'RAHABacktestRunType';
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  createdAt: Scalars['DateTime']['output'];
  endDate: Scalars['Date']['output'];
  equityCurve?: Maybe<Array<Maybe<EquityPointType>>>;
  id: Scalars['UUID']['output'];
  metrics?: Maybe<Scalars['JSONString']['output']>;
  parameters?: Maybe<Scalars['JSONString']['output']>;
  startDate: Scalars['Date']['output'];
  status: CoreRahaBacktestRunStatusChoices;
  strategyVersion: StrategyVersionType;
  symbol: Scalars['String']['output'];
  timeframe: Scalars['String']['output'];
  tradeLog?: Maybe<Scalars['JSONString']['output']>;
  user: UserType;
};

/** Aggregated performance metrics for a strategy */
export type RahaMetricsType = {
  __typename?: 'RAHAMetricsType';
  avgLoss?: Maybe<Scalars['Float']['output']>;
  avgPnlPerSignal?: Maybe<Scalars['Float']['output']>;
  avgRMultiple?: Maybe<Scalars['Float']['output']>;
  avgWin?: Maybe<Scalars['Float']['output']>;
  bestRMultiple?: Maybe<Scalars['Float']['output']>;
  /** Expected value per trade (R-multiple) */
  expectancy?: Maybe<Scalars['Float']['output']>;
  losingSignals?: Maybe<Scalars['Int']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  maxDrawdownDurationDays?: Maybe<Scalars['Int']['output']>;
  period: Scalars['String']['output'];
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  strategyVersionId: Scalars['ID']['output'];
  totalPnlDollars?: Maybe<Scalars['Float']['output']>;
  totalPnlPercent?: Maybe<Scalars['Float']['output']>;
  totalSignals?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
  winningSignals?: Maybe<Scalars['Int']['output']>;
  worstRMultiple?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for RAHA Signal */
export type RahaSignalType = {
  __typename?: 'RAHASignalType';
  /** RAHA signal that triggered this order (if auto-traded) */
  brokerOrders: Array<BrokerOrderType>;
  /** ML confidence score (0-1) */
  confidenceScore: Scalars['Decimal']['output'];
  id: Scalars['UUID']['output'];
  meta?: Maybe<Scalars['JSONString']['output']>;
  price: Scalars['Decimal']['output'];
  signalType: CoreRahaSignalSignalTypeChoices;
  stopLoss?: Maybe<Scalars['Decimal']['output']>;
  strategyVersion: StrategyVersionType;
  symbol: Scalars['String']['output'];
  takeProfit?: Maybe<Scalars['Decimal']['output']>;
  timeframe: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
  /** Null for global signals, set for personalized signals */
  user?: Maybe<UserType>;
};

/** Result of AI rebalancing operation */
export type RebalanceResultType = {
  __typename?: 'RebalanceResultType';
  changesMade?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  estimatedImprovement?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  newPortfolioValue?: Maybe<Scalars['Float']['output']>;
  rebalanceCost?: Maybe<Scalars['Float']['output']>;
  stockTrades?: Maybe<Array<Maybe<StockTradeType>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Portfolio rebalancing suggestion */
export type RebalanceSuggestionType = {
  __typename?: 'RebalanceSuggestionType';
  action?: Maybe<Scalars['String']['output']>;
  currentAllocation?: Maybe<Scalars['Float']['output']>;
  priority?: Maybe<Scalars['String']['output']>;
  reasoning?: Maybe<Scalars['String']['output']>;
  suggestedAllocation?: Maybe<Scalars['Float']['output']>;
};

/** Recent trade for traders */
export type RecentTradeType = {
  __typename?: 'RecentTradeType';
  pnl?: Maybe<Scalars['Float']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  quantity?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** Record stake transaction result */
export type RecordStakeTransactionResultType = {
  __typename?: 'RecordStakeTransactionResultType';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type Refresh = {
  __typename?: 'Refresh';
  payload: Scalars['GenericScalar']['output'];
  refreshExpiresIn: Scalars['Int']['output'];
  token: Scalars['String']['output'];
};

/** Refresh bank account data from Yodlee */
export type RefreshBankAccount = {
  __typename?: 'RefreshBankAccount';
  account?: Maybe<BankAccountType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Remove a stock from user's watchlist */
export type RemoveFromWatchlist = {
  __typename?: 'RemoveFromWatchlist';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Remove a holding from portfolio */
export type RemovePortfolioHolding = {
  __typename?: 'RemovePortfolioHolding';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Complete research hub data for a stock */
export type ResearchHubType = {
  __typename?: 'ResearchHubType';
  macro?: Maybe<MacroType>;
  marketRegime?: Maybe<ResearchMarketRegimeType>;
  peers?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  quote?: Maybe<QuoteType>;
  sentiment?: Maybe<SentimentType>;
  snapshot?: Maybe<SnapshotType>;
  symbol?: Maybe<Scalars['String']['output']>;
  technical?: Maybe<TechnicalType>;
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** Market regime analysis for research hub */
export type ResearchMarketRegimeType = {
  __typename?: 'ResearchMarketRegimeType';
  confidence?: Maybe<Scalars['Float']['output']>;
  marketRegime?: Maybe<Scalars['String']['output']>;
  recommendedStrategy?: Maybe<Scalars['String']['output']>;
};

/** Reset password with token */
export type ResetPassword = {
  __typename?: 'ResetPassword';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** GraphQL type for quest/lesson rewards */
export type RewardType = {
  __typename?: 'RewardType';
  amount?: Maybe<Scalars['Int']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** Risk assessment results */
export type RiskAssessmentType = {
  __typename?: 'RiskAssessmentType';
  concentrationRisk?: Maybe<Scalars['String']['output']>;
  overallRisk?: Maybe<Scalars['String']['output']>;
  recommendations?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  sectorRisk?: Maybe<Scalars['String']['output']>;
  volatilityEstimate?: Maybe<Scalars['Float']['output']>;
};

/** Risk limits configuration */
export type RiskLimitsType = {
  __typename?: 'RiskLimitsType';
  maxConcurrentTrades?: Maybe<Scalars['Int']['output']>;
  maxDailyLoss?: Maybe<Scalars['Float']['output']>;
  maxPositionSize?: Maybe<Scalars['Float']['output']>;
  maxSectorExposure?: Maybe<Scalars['Float']['output']>;
};

/** Risk status for order dashboard */
export type RiskStatusType = {
  __typename?: 'RiskStatusType';
  accountEquity?: Maybe<Scalars['Float']['output']>;
  activePositionsCount?: Maybe<Scalars['Int']['output']>;
  dailyLimitWarning?: Maybe<Scalars['Boolean']['output']>;
  dailyNotionalLimit?: Maybe<Scalars['Float']['output']>;
  dailyNotionalRemaining?: Maybe<Scalars['Float']['output']>;
  dailyNotionalUsed?: Maybe<Scalars['Float']['output']>;
  dayTradeCount?: Maybe<Scalars['Int']['output']>;
  maxPositions?: Maybe<Scalars['Int']['output']>;
  patternDayTrader?: Maybe<Scalars['Boolean']['output']>;
  positionLimitWarning?: Maybe<Scalars['Boolean']['output']>;
  positionSizePercent?: Maybe<Scalars['Float']['output']>;
  totalPositionValue?: Maybe<Scalars['Float']['output']>;
  totalUnrealizedPnl?: Maybe<Scalars['Float']['output']>;
  tradingBlocked?: Maybe<Scalars['Boolean']['output']>;
};

/** Risk summary for user's account */
export type RiskSummaryType = {
  __typename?: 'RiskSummaryType';
  accountValue?: Maybe<Scalars['Float']['output']>;
  activePositions?: Maybe<Scalars['Int']['output']>;
  dailyPnl?: Maybe<Scalars['Float']['output']>;
  dailyPnlPct?: Maybe<Scalars['Float']['output']>;
  dailyTrades?: Maybe<Scalars['Int']['output']>;
  exposurePct?: Maybe<Scalars['Float']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  riskLimits?: Maybe<RiskLimitsType>;
  sectorExposure?: Maybe<Scalars['JSONString']['output']>;
  totalExposure?: Maybe<Scalars['Float']['output']>;
};

/** Run a backtest for a strategy */
export type RunBacktest = {
  __typename?: 'RunBacktest';
  backtestRun?: Maybe<RahaBacktestRunType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Rust engine options analysis */
export type RustOptionsAnalysisType = {
  __typename?: 'RustOptionsAnalysisType';
  greeks?: Maybe<GreeksType>;
  impliedVolatilityRank?: Maybe<Scalars['Float']['output']>;
  putCallRatio?: Maybe<Scalars['Float']['output']>;
  recommendedStrikes?: Maybe<Array<Maybe<StrikeRecommendationType>>>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  underlyingPrice?: Maybe<Scalars['Float']['output']>;
  volatilitySurface?: Maybe<VolatilitySurfaceType>;
};

/** Rust engine stock analysis */
export type RustStockAnalysisType = {
  __typename?: 'RustStockAnalysisType';
  beginnerFriendlyScore?: Maybe<Scalars['Float']['output']>;
  fundamentalAnalysis?: Maybe<FundamentalAnalysisType>;
  optionsFlowData?: Maybe<Array<Maybe<OptionsFlowDataPointType>>>;
  reasoning?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  recommendation?: Maybe<Scalars['String']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  shapExplanation?: Maybe<Scalars['String']['output']>;
  shapValues?: Maybe<Array<Maybe<ShapValueType>>>;
  signalContributions?: Maybe<Array<Maybe<SignalContributionType>>>;
  spendingData?: Maybe<Array<Maybe<SpendingDataPointType>>>;
  symbol?: Maybe<Scalars['String']['output']>;
  technicalIndicators?: Maybe<TechnicalIndicatorsType>;
};

/** GraphQL type for SBLOC Bank */
export type SblocBankType = {
  __typename?: 'SBLOCBankType';
  id: Scalars['ID']['output'];
  isActive: Scalars['Boolean']['output'];
  /** Bank logo URL */
  logoUrl?: Maybe<Scalars['String']['output']>;
  /** Maximum APR (as decimal) */
  maxApr?: Maybe<Scalars['Float']['output']>;
  /** Maximum LTV (as decimal) */
  maxLtv?: Maybe<Scalars['Float']['output']>;
  /** Minimum APR (as decimal) */
  minApr?: Maybe<Scalars['Float']['output']>;
  /** Minimum loan amount in USD */
  minLoanUsd?: Maybe<Scalars['Int']['output']>;
  /** Minimum LTV (as decimal) */
  minLtv?: Maybe<Scalars['Float']['output']>;
  name: Scalars['String']['output'];
  notes?: Maybe<Scalars['String']['output']>;
  /** Display priority (higher = shown first) */
  priority: Scalars['Int']['output'];
  /** Supported regions */
  regions?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
};

/** GraphQL type for SBLOC offer/quote */
export type SblocOfferType = {
  __typename?: 'SBLOCOfferType';
  /** Annual percentage rate (e.g., 0.085 for 8.5%) */
  apr?: Maybe<Scalars['Float']['output']>;
  /** Required disclosures */
  disclosures?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  /** Eligible equity value in USD */
  eligibleEquity?: Maybe<Scalars['Float']['output']>;
  /** Loan-to-value ratio (e.g., 0.5 for 50%) */
  ltv?: Maybe<Scalars['Float']['output']>;
  /** Maximum draw multiplier (e.g., 0.95) */
  maxDrawMultiplier?: Maybe<Scalars['Float']['output']>;
  /** Minimum draw amount in USD */
  minDraw?: Maybe<Scalars['Int']['output']>;
  /** Last updated timestamp */
  updatedAt?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for SBLOC Session */
export type SblocSessionType = {
  __typename?: 'SBLOCSessionType';
  /** Loan amount in USD */
  amountUsd?: Maybe<Scalars['Int']['output']>;
  /** Application URL */
  applicationUrl?: Maybe<Scalars['String']['output']>;
  bank: SblocBankType;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  /** Session ID */
  sessionId?: Maybe<Scalars['String']['output']>;
  status: CoreSblocSessionStatusChoices;
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

/** SHAP value for explainability */
export type ShapValueType = {
  __typename?: 'SHAPValueType';
  feature?: Maybe<Scalars['String']['output']>;
  importance?: Maybe<Scalars['Float']['output']>;
  value?: Maybe<Scalars['Float']['output']>;
};

/** Result of saving an insight */
export type SaveInsightResult = {
  __typename?: 'SaveInsightResult';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

/** Save user's portfolio holdings */
export type SavePortfolio = {
  __typename?: 'SavePortfolio';
  message?: Maybe<Scalars['String']['output']>;
  portfolio?: Maybe<Array<Maybe<PortfolioType>>>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Individual result from an AI scan */
export type ScanResultType = {
  __typename?: 'ScanResultType';
  change?: Maybe<Scalars['Float']['output']>;
  changePercent?: Maybe<Scalars['Float']['output']>;
  confidence?: Maybe<Scalars['Float']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  marketCap?: Maybe<Scalars['Float']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  opportunityFactors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  reasoning?: Maybe<Scalars['String']['output']>;
  riskFactors?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  score?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  volume?: Maybe<Scalars['Int']['output']>;
};

/** Scanned option result */
export type ScannedOptionType = {
  __typename?: 'ScannedOptionType';
  ask?: Maybe<Scalars['Float']['output']>;
  bid?: Maybe<Scalars['Float']['output']>;
  contractSymbol?: Maybe<Scalars['String']['output']>;
  delta?: Maybe<Scalars['Float']['output']>;
  expiration?: Maybe<Scalars['String']['output']>;
  impliedVolatility?: Maybe<Scalars['Float']['output']>;
  opportunity?: Maybe<Scalars['String']['output']>;
  optionType?: Maybe<Scalars['String']['output']>;
  score?: Maybe<Scalars['Int']['output']>;
  strike?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  theta?: Maybe<Scalars['Float']['output']>;
  volume?: Maybe<Scalars['Int']['output']>;
};

/** GraphQL type for quest scenario */
export type ScenarioType = {
  __typename?: 'ScenarioType';
  description?: Maybe<Scalars['String']['output']>;
  expectedOutcome?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  marketCondition?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** Sector comparison for Consumer Strength Score */
export type SectorComparisonType = {
  __typename?: 'SectorComparisonType';
  percentile?: Maybe<Scalars['Float']['output']>;
  sectorAverage?: Maybe<Scalars['Float']['output']>;
  sectorName?: Maybe<Scalars['String']['output']>;
  sectorRank?: Maybe<Scalars['Int']['output']>;
  stockScore?: Maybe<Scalars['Float']['output']>;
  totalInSector?: Maybe<Scalars['Int']['output']>;
};

export type SendMessage = {
  __typename?: 'SendMessage';
  message?: Maybe<ChatMessageType>;
  session?: Maybe<ChatSessionType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Rust engine sentiment analysis */
export type SentimentAnalysisType = {
  __typename?: 'SentimentAnalysisType';
  confidence?: Maybe<Scalars['Float']['output']>;
  newsSentiment?: Maybe<NewsSentimentType>;
  overallSentiment?: Maybe<Scalars['String']['output']>;
  sentimentScore?: Maybe<Scalars['Float']['output']>;
  socialSentiment?: Maybe<SocialSentimentType>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** Sentiment analysis data */
export type SentimentType = {
  __typename?: 'SentimentType';
  articleCount?: Maybe<Scalars['Int']['output']>;
  confidence?: Maybe<Scalars['Float']['output']>;
  label?: Maybe<Scalars['String']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
};

/** Set a bank account as primary */
export type SetPrimaryBankAccount = {
  __typename?: 'SetPrimaryBankAccount';
  account?: Maybe<BankAccountType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result of sharing an insight */
export type ShareInsightResult = {
  __typename?: 'ShareInsightResult';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

/** Signal alert */
export type SignalAlertType = {
  __typename?: 'SignalAlertType';
  message?: Maybe<Scalars['String']['output']>;
  severity?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  type?: Maybe<Scalars['String']['output']>;
};

/** Signal contribution for feature importance */
export type SignalContributionType = {
  __typename?: 'SignalContributionType';
  color?: Maybe<Scalars['String']['output']>;
  contribution?: Maybe<Scalars['Float']['output']>;
  description?: Maybe<Scalars['String']['output']>;
  name?: Maybe<Scalars['String']['output']>;
};

/** Multi-signal fusion updates */
export type SignalUpdatesType = {
  __typename?: 'SignalUpdatesType';
  alerts?: Maybe<Array<Maybe<SignalAlertType>>>;
  consumerStrength?: Maybe<Scalars['Float']['output']>;
  fusionScore?: Maybe<Scalars['Float']['output']>;
  recommendation?: Maybe<Scalars['String']['output']>;
  signals?: Maybe<Scalars['JSONString']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for skill mastery */
export type SkillMasteryType = {
  __typename?: 'SkillMasteryType';
  masteryLevel?: Maybe<Scalars['String']['output']>;
  masteryPercentage?: Maybe<Scalars['Float']['output']>;
  skill?: Maybe<Scalars['String']['output']>;
  status?: Maybe<Scalars['String']['output']>;
};

/** Company snapshot data */
export type SnapshotType = {
  __typename?: 'SnapshotType';
  country?: Maybe<Scalars['String']['output']>;
  marketCap?: Maybe<Scalars['Float']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  website?: Maybe<Scalars['String']['output']>;
};

/** Social feed item for social trading */
export type SocialFeedItemType = {
  __typename?: 'SocialFeedItemType';
  comments?: Maybe<Scalars['Int']['output']>;
  content?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  likes?: Maybe<Scalars['Int']['output']>;
  performance?: Maybe<PerformanceType>;
  shares?: Maybe<Scalars['Int']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
  tradeData?: Maybe<TradeDataType>;
  type?: Maybe<Scalars['String']['output']>;
  user?: Maybe<SocialFeedUserType>;
};

/** User info for social feeds */
export type SocialFeedUserType = {
  __typename?: 'SocialFeedUserType';
  avatar?: Maybe<Scalars['String']['output']>;
  followerCount?: Maybe<Scalars['Int']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  performance?: Maybe<TraderPerformanceType>;
  recentTrades?: Maybe<Array<Maybe<RecentTradeType>>>;
  username?: Maybe<Scalars['String']['output']>;
  verified?: Maybe<Scalars['Boolean']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** Social sentiment data */
export type SocialSentimentType = {
  __typename?: 'SocialSentimentType';
  engagementScore?: Maybe<Scalars['Float']['output']>;
  mentions24h?: Maybe<Scalars['Int']['output']>;
  negativeMentions?: Maybe<Scalars['Int']['output']>;
  positiveMentions?: Maybe<Scalars['Int']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  trending?: Maybe<Scalars['Boolean']['output']>;
};

/** Spending data point for consumer spending surge chart */
export type SpendingDataPointType = {
  __typename?: 'SpendingDataPointType';
  date?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  priceChange?: Maybe<Scalars['Float']['output']>;
  spending?: Maybe<Scalars['Float']['output']>;
  spendingChange?: Maybe<Scalars['Float']['output']>;
};

/** Spending insights for personalized recommendations */
export type SpendingInsightsType = {
  __typename?: 'SpendingInsightsType';
  discretionaryIncome?: Maybe<Scalars['Float']['output']>;
  sectorPreferences?: Maybe<Scalars['JSONString']['output']>;
  spendingHealth?: Maybe<Scalars['String']['output']>;
  suggestedBudget?: Maybe<Scalars['Float']['output']>;
  topCategories?: Maybe<Scalars['JSONString']['output']>;
};

/** Stake intent result */
export type StakeIntentResultType = {
  __typename?: 'StakeIntentResultType';
  amount?: Maybe<Scalars['Float']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  ok?: Maybe<Scalars['Boolean']['output']>;
  poolId?: Maybe<Scalars['String']['output']>;
};

/** Start a new lesson */
export type StartLesson = {
  __typename?: 'StartLesson';
  lesson?: Maybe<LessonType>;
};

/** Start a live trading simulation */
export type StartLiveSim = {
  __typename?: 'StartLiveSim';
  simulation?: Maybe<LiveSimType>;
};

/** Start a new quest */
export type StartQuest = {
  __typename?: 'StartQuest';
  quest?: Maybe<QuestType>;
};

/** Type for stock chart data */
export type StockChartDataType = {
  __typename?: 'StockChartDataType';
  data: Array<Maybe<ChartDataPointType>>;
  symbol: Scalars['String']['output'];
};

export type StockDiscussionType = {
  __typename?: 'StockDiscussionType';
  commentCount?: Maybe<Scalars['Int']['output']>;
  comments?: Maybe<Array<Maybe<DiscussionCommentType>>>;
  content: Scalars['String']['output'];
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  discussionType?: Maybe<Scalars['String']['output']>;
  downvotes: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  isLocked?: Maybe<Scalars['Boolean']['output']>;
  isPinned?: Maybe<Scalars['Boolean']['output']>;
  score?: Maybe<Scalars['Int']['output']>;
  stock?: Maybe<StockType>;
  title: Scalars['String']['output'];
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
  upvotes: Scalars['Int']['output'];
  user?: Maybe<UserType>;
  visibility?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for stock moments */
export type StockMomentType = {
  __typename?: 'StockMomentType';
  category?: Maybe<MomentCategoryEnum>;
  deepSummary?: Maybe<Scalars['String']['output']>;
  id: Scalars['UUID']['output'];
  impact1D?: Maybe<Scalars['Float']['output']>;
  impact1d?: Maybe<Scalars['Float']['output']>;
  impact7D?: Maybe<Scalars['Float']['output']>;
  impact7d?: Maybe<Scalars['Float']['output']>;
  importanceScore?: Maybe<Scalars['Float']['output']>;
  quickSummary?: Maybe<Scalars['String']['output']>;
  sourceLinks?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  symbol: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
  title: Scalars['String']['output'];
};

/** Type for current stock price data */
export type StockPriceType = {
  __typename?: 'StockPriceType';
  apiResponse?: Maybe<Scalars['JSONString']['output']>;
  change?: Maybe<Scalars['Float']['output']>;
  changePercent?: Maybe<Scalars['String']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  lastUpdated?: Maybe<Scalars['String']['output']>;
  source?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  verified?: Maybe<Scalars['Boolean']['output']>;
};

/** Individual stock recommendation within a portfolio */
export type StockRecommendationType = {
  __typename?: 'StockRecommendationType';
  allocation?: Maybe<Scalars['Float']['output']>;
  companyName?: Maybe<Scalars['String']['output']>;
  expectedReturn?: Maybe<Scalars['Float']['output']>;
  reasoning?: Maybe<Scalars['String']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** Advanced stock screening result */
export type StockScreeningResultType = {
  __typename?: 'StockScreeningResultType';
  beginnerFriendlyScore?: Maybe<Scalars['Int']['output']>;
  companyName?: Maybe<Scalars['String']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  growthPotential?: Maybe<Scalars['String']['output']>;
  marketCap?: Maybe<Scalars['Float']['output']>;
  mlScore?: Maybe<Scalars['Float']['output']>;
  peRatio?: Maybe<Scalars['Float']['output']>;
  riskLevel?: Maybe<Scalars['String']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** Individual stock trade in rebalancing */
export type StockTradeType = {
  __typename?: 'StockTradeType';
  action?: Maybe<Scalars['String']['output']>;
  companyName?: Maybe<Scalars['String']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  reason?: Maybe<Scalars['String']['output']>;
  shares?: Maybe<Scalars['Int']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  totalValue?: Maybe<Scalars['Float']['output']>;
};

export type StockType = {
  __typename?: 'StockType';
  beginnerFriendlyScore: Scalars['Int']['output'];
  companyName?: Maybe<Scalars['String']['output']>;
  currentPrice?: Maybe<Scalars['Float']['output']>;
  debtRatio?: Maybe<Scalars['Decimal']['output']>;
  dividendYield?: Maybe<Scalars['Decimal']['output']>;
  id: Scalars['ID']['output'];
  marketCap?: Maybe<Scalars['BigInt']['output']>;
  peRatio?: Maybe<Scalars['Decimal']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  symbol: Scalars['String']['output'];
  volatility?: Maybe<Scalars['Decimal']['output']>;
};

/** Type for a single strategy component in a blend */
export type StrategyBlendComponentType = {
  __typename?: 'StrategyBlendComponentType';
  strategyName?: Maybe<Scalars['String']['output']>;
  strategyVersionId: Scalars['ID']['output'];
  weight: Scalars['Float']['output'];
};

/** GraphQL type for Strategy Blend */
export type StrategyBlendType = {
  __typename?: 'StrategyBlendType';
  components?: Maybe<Array<Maybe<StrategyBlendComponentType>>>;
  createdAt: Scalars['DateTime']['output'];
  /** Optional description of the blend */
  description: Scalars['String']['output'];
  id: Scalars['UUID']['output'];
  /** Whether this blend is currently active for signal generation */
  isActive: Scalars['Boolean']['output'];
  /** Whether this is the default blend for the user (only one default per user) */
  isDefault: Scalars['Boolean']['output'];
  /** User-friendly name for this blend */
  name: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

/** GraphQL type for Strategy */
export type StrategyType = {
  __typename?: 'StrategyType';
  category: CoreStrategyCategoryChoices;
  createdAt: Scalars['DateTime']['output'];
  /** User who created this custom strategy (null for system strategies) */
  createdBy?: Maybe<UserType>;
  defaultVersion?: Maybe<StrategyVersionType>;
  description: Scalars['String']['output'];
  enabled: Scalars['Boolean']['output'];
  id: Scalars['UUID']['output'];
  /** Internal reference to influencer (e.g., 'pj_trades', 'ross_cameron') */
  influencerRef: Scalars['String']['output'];
  /** True if this is a user-created custom strategy */
  isCustom: Scalars['Boolean']['output'];
  marketType: CoreStrategyMarketTypeChoices;
  name: Scalars['String']['output'];
  slug: Scalars['String']['output'];
  timeframeSupported?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  updatedAt: Scalars['DateTime']['output'];
  versions: Array<StrategyVersionType>;
};

/** GraphQL type for StrategyVersion */
export type StrategyVersionType = {
  __typename?: 'StrategyVersionType';
  backtests: Array<RahaBacktestRunType>;
  configSchema?: Maybe<Scalars['JSONString']['output']>;
  createdAt: Scalars['DateTime']['output'];
  customLogic?: Maybe<Scalars['JSONString']['output']>;
  id: Scalars['UUID']['output'];
  isDefault: Scalars['Boolean']['output'];
  /** Reference to implementation (e.g., 'ORB_v1', 'MOMENTUM_BREAKOUT_v1', 'CUSTOM_<uuid>') */
  logicRef: Scalars['String']['output'];
  signals: Array<RahaSignalType>;
  strategy: StrategyType;
  userSettings: Array<UserStrategySettingsType>;
  version: Scalars['Int']['output'];
};

/** Recommended option strike */
export type StrikeRecommendationType = {
  __typename?: 'StrikeRecommendationType';
  expectedReturn?: Maybe<Scalars['Float']['output']>;
  expiration?: Maybe<Scalars['String']['output']>;
  greeks?: Maybe<GreeksType>;
  optionType?: Maybe<Scalars['String']['output']>;
  riskScore?: Maybe<Scalars['Float']['output']>;
  strike?: Maybe<Scalars['Float']['output']>;
};

/** Submit quiz answers */
export type SubmitQuiz = {
  __typename?: 'SubmitQuiz';
  result?: Maybe<QuizResultType>;
};

/** Subscribe to premium features */
export type SubscribeToPremium = {
  __typename?: 'SubscribeToPremium';
  message?: Maybe<Scalars['String']['output']>;
  subscriptionId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Swing trading signal with all fields */
export type SwingSignalType = {
  __typename?: 'SwingSignalType';
  createdBy?: Maybe<SwingSignalUserType>;
  daysSinceTriggered?: Maybe<Scalars['Int']['output']>;
  entryPrice?: Maybe<Scalars['Float']['output']>;
  features?: Maybe<Scalars['JSONString']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  isActive?: Maybe<Scalars['Boolean']['output']>;
  isLikedByUser?: Maybe<Scalars['Boolean']['output']>;
  isValidated?: Maybe<Scalars['Boolean']['output']>;
  mlScore?: Maybe<Scalars['Float']['output']>;
  patterns?: Maybe<Array<Maybe<PatternRecognitionType>>>;
  riskRewardRatio?: Maybe<Scalars['Float']['output']>;
  signalType?: Maybe<Scalars['String']['output']>;
  stopPrice?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  targetPrice?: Maybe<Scalars['Float']['output']>;
  technicalIndicators?: Maybe<Array<Maybe<TechnicalIndicatorType>>>;
  thesis?: Maybe<Scalars['String']['output']>;
  timeframe?: Maybe<Scalars['String']['output']>;
  triggeredAt?: Maybe<Scalars['String']['output']>;
  userLikeCount?: Maybe<Scalars['Int']['output']>;
  validationPrice?: Maybe<Scalars['Float']['output']>;
  validationTimestamp?: Maybe<Scalars['String']['output']>;
};

/** User who created the signal */
export type SwingSignalUserType = {
  __typename?: 'SwingSignalUserType';
  id?: Maybe<Scalars['String']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  username?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for swing trading picks data */
export type SwingTradingDataType = {
  __typename?: 'SwingTradingDataType';
  asOf?: Maybe<Scalars['String']['output']>;
  picks?: Maybe<Array<Maybe<SwingTradingPickType>>>;
  strategy?: Maybe<Scalars['String']['output']>;
  universeSize?: Maybe<Scalars['Int']['output']>;
  universeSource?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for swing trading features */
export type SwingTradingFeaturesType = {
  __typename?: 'SwingTradingFeaturesType';
  /** 1-day ATR */
  atr1d?: Maybe<Scalars['Float']['output']>;
  /** Breakout strength (for breakout strategy) */
  breakoutStrength?: Maybe<Scalars['Float']['output']>;
  /** Distance from 20-day MA (for mean reversion) */
  distFromMA20?: Maybe<Scalars['Float']['output']>;
  /** 20-day high (for breakout strategy) */
  high20d?: Maybe<Scalars['Float']['output']>;
  /** 5-day momentum */
  momentum5d?: Maybe<Scalars['Float']['output']>;
  /** Mean reversion potential */
  reversionPotential?: Maybe<Scalars['Float']['output']>;
  /** RSI (for mean reversion strategy) */
  rsi?: Maybe<Scalars['Float']['output']>;
  /** 5-day relative volume */
  rvol5d?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for a swing trading pick */
export type SwingTradingPickType = {
  __typename?: 'SwingTradingPickType';
  entryPrice?: Maybe<Scalars['Float']['output']>;
  features?: Maybe<SwingTradingFeaturesType>;
  notes?: Maybe<Scalars['String']['output']>;
  risk?: Maybe<SwingTradingRiskType>;
  score?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  strategy?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for swing trading risk metrics */
export type SwingTradingRiskType = {
  __typename?: 'SwingTradingRiskType';
  atr1d?: Maybe<Scalars['Float']['output']>;
  /** Expected hold period in days (2-5) */
  holdDays?: Maybe<Scalars['Int']['output']>;
  sizeShares?: Maybe<Scalars['Int']['output']>;
  stop?: Maybe<Scalars['Float']['output']>;
  targets?: Maybe<Array<Maybe<Scalars['Float']['output']>>>;
};

/** GraphQL type for swing trading strategy performance stats */
export type SwingTradingStatsType = {
  __typename?: 'SwingTradingStatsType';
  asOf?: Maybe<Scalars['String']['output']>;
  avgPnlPerSignal?: Maybe<Scalars['Float']['output']>;
  calmarRatio?: Maybe<Scalars['Float']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  period?: Maybe<Scalars['String']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  signalsEvaluated?: Maybe<Scalars['Int']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  strategy?: Maybe<Scalars['String']['output']>;
  totalPnlPercent?: Maybe<Scalars['Float']['output']>;
  totalSignals?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** Sync transactions for a bank account */
export type SyncBankTransactions = {
  __typename?: 'SyncBankTransactions';
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  transactionsCount?: Maybe<Scalars['Int']['output']>;
};

/** Sync SBLOC banks from aggregator service */
export type SyncSblocBanks = {
  __typename?: 'SyncSBLOCBanks';
  banksSynced?: Maybe<Scalars['Int']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Take profits on an options position (limit sell) */
export type TakeOptionsProfits = {
  __typename?: 'TakeOptionsProfits';
  error?: Maybe<Scalars['String']['output']>;
  orderId?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Target price calculation result */
export type TargetPriceType = {
  __typename?: 'TargetPriceType';
  atrTarget?: Maybe<Scalars['Float']['output']>;
  method?: Maybe<Scalars['String']['output']>;
  rewardDistance?: Maybe<Scalars['Float']['output']>;
  riskRewardRatio?: Maybe<Scalars['Float']['output']>;
  rrTarget?: Maybe<Scalars['Float']['output']>;
  srTarget?: Maybe<Scalars['Float']['output']>;
  targetPrice?: Maybe<Scalars['Float']['output']>;
};

/** Technical analysis data */
export type TechnicalAnalysisType = {
  __typename?: 'TechnicalAnalysisType';
  indicators?: Maybe<Scalars['JSONString']['output']>;
  resistance?: Maybe<Scalars['Float']['output']>;
  support?: Maybe<Scalars['Float']['output']>;
  trend: Scalars['String']['output'];
};

/** Technical indicator for swing signals */
export type TechnicalIndicatorType = {
  __typename?: 'TechnicalIndicatorType';
  description?: Maybe<Scalars['String']['output']>;
  name?: Maybe<Scalars['String']['output']>;
  signal?: Maybe<Scalars['String']['output']>;
  strength?: Maybe<Scalars['Float']['output']>;
  value?: Maybe<Scalars['Float']['output']>;
};

/** Technical indicators for stock analysis */
export type TechnicalIndicatorsType = {
  __typename?: 'TechnicalIndicatorsType';
  bollingerLower?: Maybe<Scalars['Float']['output']>;
  bollingerMiddle?: Maybe<Scalars['Float']['output']>;
  bollingerUpper?: Maybe<Scalars['Float']['output']>;
  ema12?: Maybe<Scalars['Float']['output']>;
  ema26?: Maybe<Scalars['Float']['output']>;
  macd?: Maybe<Scalars['Float']['output']>;
  macdHistogram?: Maybe<Scalars['Float']['output']>;
  macdSignal?: Maybe<Scalars['Float']['output']>;
  rsi?: Maybe<Scalars['Float']['output']>;
  sma20?: Maybe<Scalars['Float']['output']>;
  sma50?: Maybe<Scalars['Float']['output']>;
};

/** Technical analysis indicators */
export type TechnicalType = {
  __typename?: 'TechnicalType';
  impliedVolatility?: Maybe<Scalars['Float']['output']>;
  macd?: Maybe<Scalars['Float']['output']>;
  macdhistogram?: Maybe<Scalars['Float']['output']>;
  movingAverage50?: Maybe<Scalars['Float']['output']>;
  movingAverage200?: Maybe<Scalars['Float']['output']>;
  resistanceLevel?: Maybe<Scalars['Float']['output']>;
  rsi?: Maybe<Scalars['Float']['output']>;
  supportLevel?: Maybe<Scalars['Float']['output']>;
};

export type ToggleFollow = {
  __typename?: 'ToggleFollow';
  following?: Maybe<Scalars['Boolean']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  user?: Maybe<UserType>;
};

export type ToggleLike = {
  __typename?: 'ToggleLike';
  liked?: Maybe<Scalars['Boolean']['output']>;
  post?: Maybe<PostType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Trade data for social feed items */
export type TradeDataType = {
  __typename?: 'TradeDataType';
  pnl?: Maybe<Scalars['Float']['output']>;
  price?: Maybe<Scalars['Float']['output']>;
  quantity?: Maybe<Scalars['Float']['output']>;
  side?: Maybe<Scalars['String']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
};

/** Performance metrics for traders */
export type TraderPerformanceType = {
  __typename?: 'TraderPerformanceType';
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  totalReturn?: Maybe<Scalars['Float']['output']>;
  totalTrades?: Maybe<Scalars['Int']['output']>;
  winRate?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for trading quote (bid/ask) */
export type TradingQuoteType = {
  __typename?: 'TradingQuoteType';
  ask?: Maybe<Scalars['Float']['output']>;
  askSize?: Maybe<Scalars['Int']['output']>;
  bid?: Maybe<Scalars['Float']['output']>;
  bidSize?: Maybe<Scalars['Int']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  timestamp?: Maybe<Scalars['String']['output']>;
};

/** Train a custom ML model on user's trading history */
export type TrainMlModel = {
  __typename?: 'TrainMLModel';
  message?: Maybe<Scalars['String']['output']>;
  metrics?: Maybe<Scalars['JSONString']['output']>;
  modelId?: Maybe<Scalars['ID']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
  trainingSamples?: Maybe<Scalars['Int']['output']>;
};

/** Result of training models */
export type TrainModelsResultType = {
  __typename?: 'TrainModelsResultType';
  message?: Maybe<Scalars['String']['output']>;
  results?: Maybe<TrainingResultsType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Training results for both modes */
export type TrainingResultsType = {
  __typename?: 'TrainingResultsType';
  AGGRESSIVE?: Maybe<ModelResultType>;
  SAFE?: Maybe<ModelResultType>;
};

/** Trending discussion */
export type TrendingDiscussionType = {
  __typename?: 'TrendingDiscussionType';
  commentsCount?: Maybe<Scalars['Int']['output']>;
  createdAt?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['Int']['output']>;
  score?: Maybe<Scalars['Int']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  title?: Maybe<Scalars['String']['output']>;
  trendingReason?: Maybe<Scalars['String']['output']>;
  userName?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for tutor progress */
export type TutorProgressType = {
  __typename?: 'TutorProgressType';
  abilityEstimate?: Maybe<Scalars['Float']['output']>;
  badges?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  hearts?: Maybe<Scalars['Int']['output']>;
  level?: Maybe<Scalars['Int']['output']>;
  maxHearts?: Maybe<Scalars['Int']['output']>;
  skillMastery?: Maybe<Array<Maybe<SkillMasteryType>>>;
  streakDays?: Maybe<Scalars['Int']['output']>;
  userId?: Maybe<Scalars['String']['output']>;
  xp?: Maybe<Scalars['Int']['output']>;
};

/** Unusual options activity data point */
export type UnusualActivityType = {
  __typename?: 'UnusualActivityType';
  ask?: Maybe<Scalars['Float']['output']>;
  bid?: Maybe<Scalars['Float']['output']>;
  blockSize?: Maybe<Scalars['Int']['output']>;
  contractSymbol?: Maybe<Scalars['String']['output']>;
  expiration?: Maybe<Scalars['String']['output']>;
  impliedVolatility?: Maybe<Scalars['Float']['output']>;
  isDarkPool?: Maybe<Scalars['Boolean']['output']>;
  lastPrice?: Maybe<Scalars['Float']['output']>;
  openInterest?: Maybe<Scalars['Int']['output']>;
  optionType?: Maybe<Scalars['String']['output']>;
  strike?: Maybe<Scalars['Float']['output']>;
  sweepCount?: Maybe<Scalars['Int']['output']>;
  unusualVolumePercent?: Maybe<Scalars['Float']['output']>;
  volume?: Maybe<Scalars['Int']['output']>;
  volumeVsOI?: Maybe<Scalars['Float']['output']>;
};

/** Aggregated unusual flow summary (what UI expects) */
export type UnusualFlowSummaryType = {
  __typename?: 'UnusualFlowSummaryType';
  blockTrades?: Maybe<Scalars['Int']['output']>;
  lastUpdated?: Maybe<Scalars['String']['output']>;
  sweepTrades?: Maybe<Scalars['Int']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  topTrades?: Maybe<Array<Maybe<OptionsFlowType>>>;
  totalVolume?: Maybe<Scalars['Int']['output']>;
  unusualVolume?: Maybe<Scalars['Int']['output']>;
  unusualVolumePercent?: Maybe<Scalars['Float']['output']>;
};

/** Update user's auto-trading settings */
export type UpdateAutoTradingSettings = {
  __typename?: 'UpdateAutoTradingSettings';
  autoTradingSettings?: Maybe<AutoTradingSettingsType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result of updating bandit reward */
export type UpdateBanditRewardResultType = {
  __typename?: 'UpdateBanditRewardResultType';
  message?: Maybe<Scalars['String']['output']>;
  performance?: Maybe<BanditPerformanceType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Update a custom user strategy */
export type UpdateCustomStrategy = {
  __typename?: 'UpdateCustomStrategy';
  message?: Maybe<Scalars['String']['output']>;
  strategy?: Maybe<StrategyType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Update the number of shares for a holding */
export type UpdateHoldingShares = {
  __typename?: 'UpdateHoldingShares';
  holding?: Maybe<PortfolioHoldingType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Update a KYC workflow step */
export type UpdateKycStep = {
  __typename?: 'UpdateKycStep';
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result of updating news preferences */
export type UpdateNewsPreferencesResultType = {
  __typename?: 'UpdateNewsPreferencesResultType';
  error?: Maybe<Scalars['String']['output']>;
  preferences?: Maybe<NewsPreferencesType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Update user's RAHA notification preferences */
export type UpdateNotificationPreferences = {
  __typename?: 'UpdateNotificationPreferences';
  message?: Maybe<Scalars['String']['output']>;
  notificationPreferences?: Maybe<NotificationPreferencesType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Update an options alert */
export type UpdateOptionsAlert = {
  __typename?: 'UpdateOptionsAlert';
  alert?: Maybe<OptionsAlertType>;
  error?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Move a holding to a different portfolio */
export type UpdatePortfolioHolding = {
  __typename?: 'UpdatePortfolioHolding';
  holding?: Maybe<PortfolioHoldingType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Result of updating privacy settings */
export type UpdatePrivacySettingsResult = {
  __typename?: 'UpdatePrivacySettingsResult';
  message?: Maybe<Scalars['String']['output']>;
  success: Scalars['Boolean']['output'];
};

/** Update quest progress */
export type UpdateQuestProgress = {
  __typename?: 'UpdateQuestProgress';
  result?: Maybe<QuestProgressResultType>;
};

/** Update an existing strategy blend */
export type UpdateStrategyBlend = {
  __typename?: 'UpdateStrategyBlend';
  blend?: Maybe<StrategyBlendType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Upload a KYC document */
export type UploadKycDocument = {
  __typename?: 'UploadKycDocument';
  documentId?: Maybe<Scalars['String']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** GraphQL type for UserStrategySettings */
export type UserStrategySettingsType = {
  __typename?: 'UserStrategySettingsType';
  /** If true, signals will auto-execute (requires risk limits) */
  autoTradeEnabled: Scalars['Boolean']['output'];
  createdAt: Scalars['DateTime']['output'];
  enabled: Scalars['Boolean']['output'];
  id: Scalars['UUID']['output'];
  /** Maximum concurrent positions for this strategy */
  maxConcurrentPositions: Scalars['Int']['output'];
  /** Daily loss limit (e.g., 2.0 for 2%) */
  maxDailyLossPercent?: Maybe<Scalars['Decimal']['output']>;
  parameters?: Maybe<Scalars['JSONString']['output']>;
  strategyVersion: StrategyVersionType;
  updatedAt: Scalars['DateTime']['output'];
  user: UserType;
};

export type UserType = {
  __typename?: 'UserType';
  email: Scalars['String']['output'];
  followersCount?: Maybe<Scalars['Int']['output']>;
  followingCount?: Maybe<Scalars['Int']['output']>;
  hasPremiumAccess?: Maybe<Scalars['Boolean']['output']>;
  id: Scalars['ID']['output'];
  incomeProfile?: Maybe<IncomeProfileType>;
  isFollowedByUser?: Maybe<Scalars['Boolean']['output']>;
  isFollowingUser?: Maybe<Scalars['Boolean']['output']>;
  name: Scalars['String']['output'];
  profilePic?: Maybe<Scalars['String']['output']>;
  subscriptionTier?: Maybe<Scalars['String']['output']>;
};

/** GraphQL type for user voting power */
export type UserVotingPowerType = {
  __typename?: 'UserVotingPowerType';
  delegatedTo?: Maybe<Scalars['String']['output']>;
  delegators?: Maybe<Array<Maybe<Scalars['String']['output']>>>;
  proposalsVoted?: Maybe<Scalars['Int']['output']>;
  votingPower?: Maybe<Scalars['Float']['output']>;
};

/** GraphQL type for user yield position */
export type UserYieldPositionType = {
  __typename?: 'UserYieldPositionType';
  amount?: Maybe<Scalars['Float']['output']>;
  apy?: Maybe<Scalars['Float']['output']>;
  asset?: Maybe<Scalars['String']['output']>;
  chain?: Maybe<Scalars['String']['output']>;
  earned?: Maybe<Scalars['Float']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  protocol?: Maybe<Scalars['String']['output']>;
};

export type Verify = {
  __typename?: 'Verify';
  payload: Scalars['GenericScalar']['output'];
};

/** Volatility surface data */
export type VolatilitySurfaceType = {
  __typename?: 'VolatilitySurfaceType';
  atmVol?: Maybe<Scalars['Float']['output']>;
  skew?: Maybe<Scalars['Float']['output']>;
  termStructure?: Maybe<Scalars['JSONString']['output']>;
};

/** Vote on a discussion (upvote/downvote) */
export type VoteDiscussion = {
  __typename?: 'VoteDiscussion';
  discussion?: Maybe<StockDiscussionType>;
  message?: Maybe<Scalars['String']['output']>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

/** Vote on a poll option */
export type VotePoll = {
  __typename?: 'VotePoll';
  error?: Maybe<Scalars['String']['output']>;
  post?: Maybe<PostType>;
  success?: Maybe<Scalars['Boolean']['output']>;
};

export type WatchlistType = {
  __typename?: 'WatchlistType';
  addedAt?: Maybe<Scalars['DateTime']['output']>;
  createdAt?: Maybe<Scalars['DateTime']['output']>;
  id?: Maybe<Scalars['ID']['output']>;
  notes?: Maybe<Scalars['String']['output']>;
  stock?: Maybe<StockType>;
  targetPrice?: Maybe<Scalars['Float']['output']>;
  updatedAt?: Maybe<Scalars['DateTime']['output']>;
};

/** GraphQL type for yield opportunity */
export type YieldOpportunityType = {
  __typename?: 'YieldOpportunityType';
  apy?: Maybe<Scalars['Float']['output']>;
  asset?: Maybe<Scalars['String']['output']>;
  chain?: Maybe<Scalars['String']['output']>;
  contractAddress?: Maybe<Scalars['String']['output']>;
  minDeposit?: Maybe<Scalars['Float']['output']>;
  protocol?: Maybe<Scalars['String']['output']>;
  risk?: Maybe<Scalars['String']['output']>;
  strategy?: Maybe<Scalars['String']['output']>;
  tvl?: Maybe<Scalars['Float']['output']>;
};

/** AI yield optimizer result */
export type YieldOptimizerResultType = {
  __typename?: 'YieldOptimizerResultType';
  allocations?: Maybe<Array<Maybe<OptimizedPoolType>>>;
  expectedApy?: Maybe<Scalars['Float']['output']>;
  explanation?: Maybe<Scalars['String']['output']>;
  optimizationStatus?: Maybe<Scalars['String']['output']>;
  riskMetrics?: Maybe<Scalars['JSONString']['output']>;
  totalRisk?: Maybe<Scalars['Float']['output']>;
};

/** Yield pool information */
export type YieldPoolType = {
  __typename?: 'YieldPoolType';
  apy?: Maybe<Scalars['Float']['output']>;
  chain?: Maybe<Scalars['String']['output']>;
  id?: Maybe<Scalars['String']['output']>;
  poolAddress?: Maybe<Scalars['String']['output']>;
  protocol?: Maybe<Scalars['String']['output']>;
  risk?: Maybe<Scalars['Float']['output']>;
  symbol?: Maybe<Scalars['String']['output']>;
  tvl?: Maybe<Scalars['Float']['output']>;
};

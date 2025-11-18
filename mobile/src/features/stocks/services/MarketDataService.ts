import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';
// Market Data Interfaces
export interface StockQuote {
symbol: string;
price: number;
change: number;
changePercent: number;
volume: number;
high: number;
low: number;
open: number;
previousClose: number;
timestamp: string;
marketStatus: 'open' | 'closed' | 'pre-market' | 'after-hours';
}
export interface HistoricalData {
date: string;
open: number;
high: number;
low: number;
close: number;
volume: number;
}
export interface MarketNews {
id: string;
title: string;
summary: string;
source: string;
publishedAt: string;
url: string;
sentiment?: 'positive' | 'negative' | 'neutral';
relatedSymbols: string[];
}
export interface MarketStatus {
isOpen: boolean;
nextOpen?: string;
nextClose?: string;
timezone: string;
}
class MarketDataService {
// Kill switch to disable client-side market data calls
private MARKET_DATA_DISABLED = true; // Always disabled - use SecureMarketDataService instead

private apiKey: string = 'OHYSFF1AE446O7CR'; // Your Alpha Vantage API key
private newsApiKey: string = '94a335c7316145f79840edd62f77e11e'; // Your NewsAPI key
private baseUrl: string = 'https://www.alphavantage.co/query';
private newsBaseUrl: string = 'https://newsapi.org/v2';
private cache: Map<string, { data: any; timestamp: number }> = new Map();
private cacheTimeout: number = 24 * 60 * 60 * 1000; // 24 hour cache (since we have 25 calls per day)
constructor() {
this.loadApiKey();
}
private async loadApiKey() {
try {
const storedKey = await AsyncStorage.getItem('alpha_vantage_api_key');
if (storedKey) {
this.apiKey = storedKey;
}
} catch (error) {
}
}
public async setApiKey(apiKey: string) {
this.apiKey = apiKey;
try {
await AsyncStorage.setItem('alpha_vantage_api_key', apiKey);
} catch (error) {
      logger.error('Failed to save API key:', error);
}
}
  private async makeApiCall(params: Record<string, string>): Promise<any> {
    const cacheKey = JSON.stringify(params);
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    
    // Build URL manually for React Native compatibility
    const allParams = { ...params, apikey: this.apiKey };
    const queryString = Object.entries(allParams)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&');
    const url = `${this.baseUrl}?${queryString}`;
    
    try {
      const response = await fetch(url);
      const data = await response.json();
      // Cache the response
      this.cache.set(cacheKey, { data, timestamp: Date.now() });
      return data;
    } catch (error) {
      logger.error('API call failed:', error);
      throw error;
    }
  }
// Get real-time stock quote
public async getStockQuote(symbol: string): Promise<StockQuote> {
if (this.MARKET_DATA_DISABLED) {
  logger.warn('[MarketData] disabled in client; skipping', symbol);
  return this.getMockQuote(symbol);
}

try {
const data = await this.makeApiCall({
function: 'GLOBAL_QUOTE',
symbol: symbol.toUpperCase()
});
// Check for API errors
if (data['Error Message']) {
logger.warn(`API Error for ${symbol}:`, data['Error Message']);
return this.getMockQuote(symbol);
}
// Check for rate limit messages
if (data['Note']) {
logger.warn(`Rate limit for ${symbol}:`, data['Note']);
// For rate limits, try to use cached data first
const cached = this.cache.get(JSON.stringify({ function: 'GLOBAL_QUOTE', symbol: symbol.toUpperCase() }));
if (cached) {
const quote = cached.data['Global Quote'];
if (quote && quote['05. price']) {
return {
symbol: quote['01. symbol'],
price: parseFloat(quote['05. price']),
change: parseFloat(quote['09. change']),
changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
volume: parseInt(quote['06. volume']),
high: parseFloat(quote['03. high']),
low: parseFloat(quote['04. low']),
open: parseFloat(quote['02. open']),
previousClose: parseFloat(quote['08. previous close']),
timestamp: quote['07. latest trading day'],
marketStatus: this.getMarketStatus()
};
}
}
// Only use mock data if no cached data available
return this.getMockQuote(symbol);
}
// Check for invalid API key
if (data['Information'] && data['Information'].includes('API key')) {
logger.warn(`API key issue for ${symbol}:`, data['Information']);
return this.getMockQuote(symbol);
}
const quote = data['Global Quote'];
if (!quote || !quote['05. price']) {
logger.warn(`No quote data available for ${symbol}, using mock data`);
return this.getMockQuote(symbol);
}
return {
symbol: quote['01. symbol'],
price: parseFloat(quote['05. price']),
change: parseFloat(quote['09. change']),
changePercent: parseFloat(quote['10. change percent'].replace('%', '')),
volume: parseInt(quote['06. volume']),
high: parseFloat(quote['03. high']),
low: parseFloat(quote['04. low']),
open: parseFloat(quote['02. open']),
previousClose: parseFloat(quote['08. previous close']),
timestamp: quote['07. latest trading day'],
marketStatus: this.getMarketStatus()
};
} catch (error) {
logger.warn(`Failed to get quote for ${symbol}:`, error.message);
// Return mock data as fallback
return this.getMockQuote(symbol);
}
}
// Get multiple stock quotes with rate limiting
public async getMultipleQuotes(symbols: string[]): Promise<StockQuote[]> {
if (this.MARKET_DATA_DISABLED) {
  logger.warn('[MarketData] disabled in client; returning mock data for', symbols.length, 'symbols');
  return symbols.map(symbol => this.getMockQuote(symbol));
}

const quotes: StockQuote[] = [];
// Process symbols one by one to avoid rate limiting
for (let i = 0; i < symbols.length; i++) {
const symbol = symbols[i];
try {
const quote = await this.getStockQuote(symbol);
quotes.push(quote);
// Add delay between API calls to respect rate limits (25 calls per day)
if (i < symbols.length - 1) {
await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
}
} catch (error) {
logger.warn(`Failed to get quote for ${symbol}, using mock data`);
quotes.push(this.getMockQuote(symbol));
}
}
return quotes;
}
// Get historical data
public async getHistoricalData(symbol: string, interval: 'daily' | 'weekly' | 'monthly' = 'daily'): Promise<HistoricalData[]> {
try {
const functionMap = {
daily: 'TIME_SERIES_DAILY',
weekly: 'TIME_SERIES_WEEKLY',
monthly: 'TIME_SERIES_MONTHLY'
};
const data = await this.makeApiCall({
function: functionMap[interval],
symbol: symbol.toUpperCase(),
outputsize: 'compact'
});
if (data['Error Message']) {
throw new Error(data['Error Message']);
}
const timeSeries = data[`Time Series (${interval === 'daily' ? 'Daily' : interval === 'weekly' ? 'Weekly' : 'Monthly'})`];
if (!timeSeries) {
throw new Error('No historical data available');
}
return Object.entries(timeSeries).map(([date, values]: [string, any]) => ({
date,
open: parseFloat(values['1. open']),
high: parseFloat(values['2. high']),
low: parseFloat(values['3. low']),
close: parseFloat(values['4. close']),
volume: parseInt(values['5. volume'])
})).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
} catch (error) {
logger.error(`Failed to get historical data for ${symbol}:`, error);
return this.getMockHistoricalData(symbol);
}
}
// Get market news from NewsAPI
public async getMarketNews(topics: string[] = ['finance', 'stocks', 'market']): Promise<MarketNews[]> {
const cacheKey = 'market-news';
const cached = this.cache.get(cacheKey);
// Use cached news for 2 hours to respect rate limits
if (cached && Date.now() - cached.timestamp < 2 * 60 * 60 * 1000) {
return cached.data;
}
try {
const query = topics.join(' OR ');
const url = `${this.newsBaseUrl}/everything?q=${encodeURIComponent(query)}&apiKey=${this.newsApiKey}&sortBy=publishedAt&pageSize=20&language=en`;
const response = await fetch(url);
const data = await response.json();
if (data.status !== 'ok') {
if (data.code === 'rateLimited') {
logger.warn(' NewsAPI rate limit hit, using cached data if available');
if (cached) {
return cached.data;
}
}
throw new Error(data.message || 'Failed to fetch news');
}
const articles = data.articles || [];
const newsData = articles.map((article: any, index: number) => ({
id: `news-${index}-${Date.now()}`,
title: article.title,
summary: article.description || article.content?.substring(0, 200) + '...',
source: article.source.name,
publishedAt: article.publishedAt,
url: article.url,
sentiment: this.analyzeSentiment(article.title + ' ' + (article.description || '')),
relatedSymbols: this.extractStockSymbols(article.title + ' ' + (article.description || ''))
}));
// Cache the news for 2 hours
this.cache.set(cacheKey, { data: newsData, timestamp: Date.now() });
return newsData;
} catch (error) {
logger.error('Failed to get market news:', error);
if (cached) {
return cached.data;
}
return this.getMockNews();
}
}
// Get news for specific stock symbol
public async getStockNews(symbol: string): Promise<MarketNews[]> {
const cacheKey = `stock-news-${symbol}`;
const cached = this.cache.get(cacheKey);
// Use cached news for 2 hours to respect rate limits
if (cached && Date.now() - cached.timestamp < 2 * 60 * 60 * 1000) {
return cached.data;
}
try {
const url = `${this.newsBaseUrl}/everything?q=${encodeURIComponent(symbol)}&apiKey=${this.newsApiKey}&sortBy=publishedAt&pageSize=10&language=en`;
const response = await fetch(url);
const data = await response.json();
if (data.status !== 'ok') {
if (data.code === 'rateLimited') {
logger.warn(` NewsAPI rate limit hit for ${symbol}, using cached data if available`);
if (cached) {
return cached.data;
}
}
throw new Error(data.message || 'Failed to fetch stock news');
}
const articles = data.articles || [];
const newsData = articles.map((article: any, index: number) => ({
id: `stock-${symbol}-${index}-${Date.now()}`,
title: article.title,
summary: article.description || article.content?.substring(0, 200) + '...',
source: article.source.name,
publishedAt: article.publishedAt,
url: article.url,
sentiment: this.analyzeSentiment(article.title + ' ' + (article.description || '')),
relatedSymbols: [symbol]
}));
// Cache the news for 2 hours
this.cache.set(cacheKey, { data: newsData, timestamp: Date.now() });
return newsData;
} catch (error) {
logger.error(`Failed to get news for ${symbol}:`, error);
if (cached) {
return cached.data;
}
return [];
}
}
// Get market status
public getMarketStatus(): 'open' | 'closed' | 'pre-market' | 'after-hours' {
const now = new Date();
const day = now.getDay();
const hour = now.getHours();
const minute = now.getMinutes();
const timeInMinutes = hour * 60 + minute;
// Market is closed on weekends
if (day === 0 || day === 6) {
return 'closed';
}
// Market hours: 9:30 AM - 4:00 PM ET
const marketOpen = 9 * 60 + 30; // 9:30 AM
const marketClose = 16 * 60; // 4:00 PM
const preMarketStart = 4 * 60; // 4:00 AM
const afterHoursEnd = 20 * 60; // 8:00 PM
if (timeInMinutes >= marketOpen && timeInMinutes < marketClose) {
return 'open';
} else if (timeInMinutes >= preMarketStart && timeInMinutes < marketOpen) {
return 'pre-market';
} else if (timeInMinutes >= marketClose && timeInMinutes < afterHoursEnd) {
return 'after-hours';
} else {
return 'closed';
}
}
// Get next market open/close times
public getNextMarketTimes(): MarketStatus {
const now = new Date();
const day = now.getDay();
const hour = now.getHours();
const minute = now.getMinutes();
const timeInMinutes = hour * 60 + minute;
const marketOpen = 9 * 60 + 30; // 9:30 AM
const marketClose = 16 * 60; // 4:00 PM
let nextOpen: Date;
let nextClose: Date;
if (day >= 1 && day <= 5) { // Weekday
if (timeInMinutes < marketOpen) {
// Market opens today
nextOpen = new Date(now);
nextOpen.setHours(9, 30, 0, 0);
nextClose = new Date(now);
nextClose.setHours(16, 0, 0, 0);
} else if (timeInMinutes < marketClose) {
// Market is open, next close is today
nextOpen = new Date(now);
nextOpen.setDate(nextOpen.getDate() + 1);
nextOpen.setHours(9, 30, 0, 0);
nextClose = new Date(now);
nextClose.setHours(16, 0, 0, 0);
} else {
// Market closed, next open is tomorrow
nextOpen = new Date(now);
nextOpen.setDate(nextOpen.getDate() + 1);
nextOpen.setHours(9, 30, 0, 0);
nextClose = new Date(nextOpen);
nextClose.setHours(16, 0, 0, 0);
}
} else {
// Weekend, next open is Monday
const daysUntilMonday = day === 0 ? 1 : 8 - day; // Sunday = 0, Saturday = 6
nextOpen = new Date(now);
nextOpen.setDate(nextOpen.getDate() + daysUntilMonday);
nextOpen.setHours(9, 30, 0, 0);
nextClose = new Date(nextOpen);
nextClose.setHours(16, 0, 0, 0);
}
return {
isOpen: this.getMarketStatus() === 'open',
nextOpen: nextOpen.toISOString(),
nextClose: nextClose.toISOString(),
timezone: 'America/New_York'
};
}
// Search for stocks
public async searchStocks(query: string): Promise<any[]> {
try {
const data = await this.makeApiCall({
function: 'SYMBOL_SEARCH',
keywords: query
});
if (data['Error Message']) {
throw new Error(data['Error Message']);
}
const matches = data.bestMatches || [];
return matches.map((match: any) => ({
symbol: match['1. symbol'],
name: match['2. name'],
type: match['3. type'],
region: match['4. region'],
marketOpen: match['5. marketOpen'],
marketClose: match['6. marketClose'],
timezone: match['7. timezone'],
currency: match['8. currency'],
matchScore: match['9. matchScore']
}));
} catch (error) {
logger.error('Failed to search stocks:', error);
return [];
}
}
// Helper methods for fallback data
private getMockQuote(symbol: string): StockQuote {
// Use realistic base prices for known symbols
const symbolPrices: { [key: string]: number } = {
'AAPL': 239.69,
'MSFT': 495.00,
'GOOGL': 180.50,
'TSLA': 250.00,
'AMZN': 150.00,
'META': 350.00,
'NVDA': 800.00,
'NFLX': 400.00,
'AMD': 120.00,
'INTC': 45.00,
'CRM': 200.00,
'ADBE': 500.00,
'PYPL': 60.00,
'UBER': 70.00,
'LYFT': 15.00
};
const basePrice = symbolPrices[symbol] || (100 + Math.random() * 200);
const change = (Math.random() - 0.5) * (basePrice * 0.05); // ±5% change
const changePercent = (change / basePrice) * 100;
return {
symbol,
price: basePrice,
change,
changePercent,
volume: Math.floor(Math.random() * 10000000) + 1000000,
high: basePrice + Math.random() * (basePrice * 0.02),
low: basePrice - Math.random() * (basePrice * 0.02),
open: basePrice + (Math.random() - 0.5) * (basePrice * 0.01),
previousClose: basePrice - change,
timestamp: new Date().toISOString().split('T')[0],
marketStatus: this.getMarketStatus()
};
}
private getMockHistoricalData(symbol: string): HistoricalData[] {
const data: HistoricalData[] = [];
const basePrice = 100;
for (let i = 29; i >= 0; i--) {
const date = new Date();
date.setDate(date.getDate() - i);
const price = basePrice + (Math.random() - 0.5) * 20;
data.push({
date: date.toISOString().split('T')[0],
open: price + (Math.random() - 0.5) * 2,
high: price + Math.random() * 3,
low: price - Math.random() * 3,
close: price,
volume: Math.floor(Math.random() * 1000000)
});
}
return data;
}
private getMockNews(): MarketNews[] {
return [
{
id: '1',
title: 'Market Update: Tech Stocks Rally on Strong Earnings',
summary: 'Technology stocks showed strong performance today as major companies reported better-than-expected quarterly earnings. Apple, Microsoft, and Google led the gains.',
source: 'Financial News',
publishedAt: new Date().toISOString(),
url: 'https://example.com/news/1',
sentiment: 'positive',
relatedSymbols: ['AAPL', 'MSFT', 'GOOGL']
},
{
id: '2',
title: 'Federal Reserve Signals Potential Rate Changes',
summary: 'The Federal Reserve indicated possible adjustments to interest rates in response to current economic conditions and inflation data.',
source: 'Market Watch',
publishedAt: new Date(Date.now() - 3600000).toISOString(),
url: 'https://example.com/news/2',
sentiment: 'neutral',
relatedSymbols: []
},
{
id: '3',
title: 'Tesla Reports Record Vehicle Deliveries',
summary: 'Tesla announced record quarterly vehicle deliveries, beating analyst expectations and driving stock price higher in after-hours trading.',
source: 'Reuters',
publishedAt: new Date(Date.now() - 7200000).toISOString(),
url: 'https://example.com/news/3',
sentiment: 'positive',
relatedSymbols: ['TSLA']
},
{
id: '4',
title: 'Amazon Expands Cloud Services Globally',
summary: 'Amazon Web Services announced expansion into new markets, strengthening its position in the competitive cloud computing industry.',
source: 'TechCrunch',
publishedAt: new Date(Date.now() - 10800000).toISOString(),
url: 'https://example.com/news/4',
sentiment: 'positive',
relatedSymbols: ['AMZN']
},
{
id: '5',
title: 'Meta Platforms Invests in AI Research',
summary: 'Meta announced significant investment in artificial intelligence research and development, focusing on next-generation computing platforms.',
source: 'Bloomberg',
publishedAt: new Date(Date.now() - 14400000).toISOString(),
url: 'https://example.com/news/5',
sentiment: 'positive',
relatedSymbols: ['META']
},
{
id: '6',
title: 'NVIDIA Sees Strong Demand for AI Chips',
summary: 'NVIDIA reported strong demand for its AI and data center chips, with revenue exceeding expectations for the quarter.',
source: 'CNBC',
publishedAt: new Date(Date.now() - 18000000).toISOString(),
url: 'https://example.com/news/6',
sentiment: 'positive',
relatedSymbols: ['NVDA']
}
];
}
private mapSentiment(score: number): 'positive' | 'negative' | 'neutral' {
if (score > 0.1) return 'positive';
if (score < -0.1) return 'negative';
return 'neutral';
}
// Simple sentiment analysis based on keywords
private analyzeSentiment(text: string): 'positive' | 'negative' | 'neutral' {
const positiveWords = ['up', 'rise', 'gain', 'surge', 'rally', 'bullish', 'positive', 'growth', 'profit', 'success', 'strong', 'beat', 'exceed', 'outperform'];
const negativeWords = ['down', 'fall', 'drop', 'decline', 'crash', 'bearish', 'negative', 'loss', 'weak', 'miss', 'disappoint', 'underperform', 'concern', 'risk'];
const lowerText = text.toLowerCase();
let positiveScore = 0;
let negativeScore = 0;
positiveWords.forEach(word => {
if (lowerText.includes(word)) positiveScore++;
});
negativeWords.forEach(word => {
if (lowerText.includes(word)) negativeScore++;
});
if (positiveScore > negativeScore) return 'positive';
if (negativeScore > positiveScore) return 'negative';
return 'neutral';
}
// Extract stock symbols from text
private extractStockSymbols(text: string): string[] {
const symbols: string[] = [];
const commonSymbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT'];
commonSymbols.forEach(symbol => {
if (text.toUpperCase().includes(symbol)) {
symbols.push(symbol);
}
});
return symbols;
}
// Pre-populate cache with real data (call this once per day)
public async preloadPortfolioData(): Promise<void> {
const symbols = ['AAPL', 'MSFT', 'TSLA']; // Core portfolio symbols
for (const symbol of symbols) {
try {
const data = await this.makeApiCall({
function: 'GLOBAL_QUOTE',
symbol: symbol.toUpperCase()
});
if (data['Global Quote'] && data['Global Quote']['05. price']) {
} else if (data['Note']) {
break; // Stop if we hit rate limit
}
} catch (error) {
logger.warn(`Failed to pre-load ${symbol}:`, error);
}
}
}
// Clear cache
public clearCache() {
this.cache.clear();
}
}
export default new MarketDataService();

// Quick test to verify our stock data service is working
import { getStockComprehensive } from './stockDataService';

export async function testStockService() {
  console.log('🧪 Testing Stock Data Service...');
  
  try {
    const data = await getStockComprehensive('AAPL');
    
    if (data) {
      console.log('✅ Service working! Data structure:');
      console.log('- Symbol:', data.symbol);
      console.log('- Company:', data.companyName);
      console.log('- Current Price:', data.currentPrice);
      console.log('- Chart Data Points:', data.chartData?.length || 0);
      console.log('- News Articles:', data.news?.length || 0);
      console.log('- Insider Trades:', data.insiderTrades?.length || 0);
      console.log('- Institutional Holdings:', data.institutionalOwnership?.length || 0);
      console.log('- Sentiment Score:', data.sentiment?.overallScore);
      console.log('- Analyst Ratings:', data.analystRatings?.consensusRating);
      console.log('- Technical Indicators:', data.technicals ? 'Available' : 'None');
      console.log('- Peer Stocks:', data.peers?.length || 0);
      
      return true;
    } else {
      console.log('❌ Service returned null');
      return false;
    }
  } catch (error) {
    console.log('❌ Service error:', error);
    return false;
  }
}

// Run the test
testStockService();

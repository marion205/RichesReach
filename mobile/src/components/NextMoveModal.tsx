import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, FlatList, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, gql } from '@apollo/client';
import logger from '../utils/logger';

interface NextMoveModalProps {
  visible: boolean;
  onClose: () => void;
  portfolioValue?: number;
}

interface Idea { symbol: string; action: 'BUY' | 'HOLD' | 'TRIM'; conviction: 'calm' | 'balanced' | 'bold'; sizePct: number; thesis: string; }

const GET_AI_RECOMMENDATIONS = gql`
  query GetAIRecommendations($profile: ProfileInput, $usingDefaults: Boolean) {
    aiRecommendations(profile: $profile, usingDefaults: $usingDefaults) {
      portfolioAnalysis {
        totalValue
        numHoldings
        sectorBreakdown
        riskScore
        diversificationScore
      }
      buyRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        expectedReturn
        targetPrice
        currentPrice
      }
      sellRecommendations {
        symbol
        reasoning
      }
      rebalanceSuggestions {
        action
        currentAllocation
        suggestedAllocation
        reasoning
        priority
      }
      riskAssessment {
        overallRisk
        volatilityEstimate
        recommendations
      }
      marketOutlook {
        overallSentiment
        confidence
        keyFactors
      }
    }
  }
`;

export default function NextMoveModal({ visible, onClose, portfolioValue = 10000 }: NextMoveModalProps) {
  const [directFetchData, setDirectFetchData] = React.useState<any>(null);
  const [directFetchLoading, setDirectFetchLoading] = React.useState(false);
  const [directFetchError, setDirectFetchError] = React.useState<any>(null);
  const [useDirectFetch, setUseDirectFetch] = React.useState(false);
  const [retryCount, setRetryCount] = React.useState(0);
  const maxRetries = 3;

  // Apollo query - will fallback to direct fetch if it fails
  const { data, loading, error, refetch, networkStatus } = useQuery(GET_AI_RECOMMENDATIONS, {
    variables: { usingDefaults: true },
    skip: !visible || useDirectFetch, // Skip if using direct fetch
    fetchPolicy: 'network-only', // Always fetch from network for fresh data
    errorPolicy: 'all', // Return partial data even if there are errors
    notifyOnNetworkStatusChange: true,
    onCompleted: (data) => {
      logger.log('✅ NextMoveModal: AI Recommendations loaded via Apollo', {
        hasData: !!data?.aiRecommendations,
        buyCount: data?.aiRecommendations?.buyRecommendations?.length ?? 0,
        sellCount: data?.aiRecommendations?.sellRecommendations?.length ?? 0,
        rebalanceCount: data?.aiRecommendations?.rebalanceSuggestions?.length ?? 0,
      });
    },
    onError: (error) => {
      logger.error('❌ NextMoveModal: Apollo query failed, falling back to direct fetch', {
        message: error?.message,
        graphQLErrors: error?.graphQLErrors,
        networkError: error?.networkError,
      });
      // Fallback to direct fetch if Apollo fails
      if (visible && !useDirectFetch) {
        logger.log('🔄 Falling back to direct fetch...');
        setUseDirectFetch(true);
        performDirectFetch();
      }
    },
  });

  // Direct fetch function with retry limit
  const performDirectFetch = React.useCallback(async (attempt: number = 1) => {
    if (!visible) return;
    
    // Stop infinite loop
    if (attempt > maxRetries) {
      logger.error(`❌ NextMoveModal: Max retries (${maxRetries}) reached. Stopping.`);
      setDirectFetchError(new Error(`Failed after ${maxRetries} attempts`));
      setDirectFetchLoading(false);
      return;
    }
    
    setDirectFetchLoading(true);
    setDirectFetchError(null);
    setRetryCount(attempt);
    
    try {
      logger.log(`🔄 NextMoveModal: Performing direct fetch (attempt ${attempt}/${maxRetries})...`);
      
      // GraphQL query body - explicitly set operationName to match query name
      const queryBody = {
        query: `
          query GetAIRecommendations($usingDefaults: Boolean) {
            aiRecommendations(usingDefaults: $usingDefaults) {
              portfolioAnalysis {
                totalValue
                numHoldings
                sectorBreakdown
                riskScore
                diversificationScore
              }
              buyRecommendations {
                symbol
                companyName
                recommendation
                confidence
                reasoning
                expectedReturn
                targetPrice
                currentPrice
              }
              sellRecommendations {
                symbol
                reasoning
              }
              rebalanceSuggestions {
                action
                currentAllocation
                suggestedAllocation
                reasoning
                priority
              }
              riskAssessment {
                overallRisk
                volatilityEstimate
                recommendations
              }
              marketOutlook {
                overallSentiment
                confidence
                keyFactors
              }
            }
          }
        `,
        variables: { usingDefaults: true },
        operationName: 'GetAIRecommendations', // Explicitly set to match query name
      };
      
      // Use the centralized API config - CRITICAL: no hardcoded URLs
      const apiConfig = await import('../config/api');
      const { API_GRAPHQL, API_BASE } = apiConfig;
      
      // Ensure URL is clean and properly formatted
      let url = API_GRAPHQL;
      if (!url || url.includes('localhost') || url.includes('127.0.0.1')) {
        // Safety check: if somehow we got localhost, use API_BASE to construct correct URL
        logger.error('❌ [NextMoveModal] CRITICAL: API_GRAPHQL contains localhost!');
        logger.error('❌ [NextMoveModal] API_GRAPHQL was:', url);
        logger.error('❌ [NextMoveModal] API_BASE was:', API_BASE);
        // Use API_BASE from config instead of hardcoded IP
        url = `${API_BASE}/graphql/`;
        logger.error('❌ [NextMoveModal] Forcing override to:', url);
      }
      
      // Normalize URL (ensure single trailing slash for graphql endpoint)
      url = url.replace(/\/+$/, '') + '/';
      
      // Comprehensive logging BEFORE the fetch
      logger.log('🌐 [NextMoveModal] ========================================');
      logger.log('🌐 [NextMoveModal] Direct fetch URL:', url);
      logger.log('🌐 [NextMoveModal] API_BASE from config:', API_BASE);
      logger.log('🌐 [NextMoveModal] API_GRAPHQL from config:', API_GRAPHQL);
      logger.log('🌐 [NextMoveModal] Final URL being used:', url);
      logger.log('🌐 [NextMoveModal] ========================================');
      logger.log('🌐 [NextMoveModal] Variables:', JSON.stringify(queryBody.variables));
      logger.log('🌐 [NextMoveModal] Fetch config:', {
        method: 'POST',
        url: url,
        hasAuth: true,
        contentType: 'application/json',
      });
      
      // Perform the fetch with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      let response: Response;
      try {
        response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dev-token-1762831885',
          },
          body: JSON.stringify(queryBody),
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        
        // Enhanced error logging
        if (fetchError.name === 'AbortError') {
          logger.error('❌ [NextMoveModal] Request timeout after 30s');
          throw new Error('Request timeout - server did not respond');
        }
        
        logger.error('❌ [NextMoveModal] Network error in fetch:', {
          name: fetchError?.name,
          message: fetchError?.message,
          stack: fetchError?.stack,
          url: url,
        });
        throw fetchError;
      }
      
      // Log response status BEFORE trying to read body
      logger.log('🌐 [NextMoveModal] HTTP status:', response.status, response.statusText);
      logger.log('🌐 [NextMoveModal] Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        // Try to read error body for more context
        let errorText = '';
        try {
          errorText = await response.text();
          logger.error('❌ [NextMoveModal] HTTP error response body (first 500 chars):', errorText.slice(0, 500));
        } catch (e) {
          logger.error('❌ [NextMoveModal] Could not read error response body');
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}${errorText ? ` - ${errorText.slice(0, 200)}` : ''}`);
      }

      // Read response as text first, then parse (helps with debugging)
      const responseText = await response.text();
      logger.log('🌐 [NextMoveModal] Raw response (first 500 chars):', responseText.slice(0, 500));
      
      let json: any;
      try {
        json = JSON.parse(responseText);
      } catch (parseError) {
        logger.error('❌ [NextMoveModal] Failed to parse JSON response:', parseError);
        logger.error('❌ [NextMoveModal] Response text:', responseText);
        throw new Error(`Invalid JSON response: ${parseError}`);
      }
      
      // Log parsed response structure
      logger.log('📥 [NextMoveModal] Parsed response keys:', Object.keys(json));
      if (json.data) {
        logger.log('📥 [NextMoveModal] Response has data, keys:', Object.keys(json.data));
      }
      
      // Handle GraphQL errors gracefully - warn but don't throw if we have partial data
      if (json.errors?.length) {
        logger.warn('⚠️ [NextMoveModal] GraphQL errors in response:', JSON.stringify(json.errors, null, 2));
        // Don't throw immediately - check if we have usable data first
      }

      // Check response structure
      if (!json.data) {
        logger.error('❌ No "data" key in response. Full response:', json);
        throw new Error(`Invalid response: missing "data" key. Response keys: ${Object.keys(json).join(', ')}`);
      }
      
      // If we have errors but also have data, log warning but continue
      if (json.errors?.length && json.data && Object.keys(json.data).length > 0) {
        logger.warn('⚠️ [NextMoveModal] GraphQL errors present but continuing with partial data');
      }
      
      // Only throw if we have errors AND no usable data
      if (json.errors?.length && (!json.data || Object.keys(json.data).length === 0)) {
        logger.error('❌ [NextMoveModal] GraphQL errors and no usable data');
        throw new Error(`GraphQL errors: ${JSON.stringify(json.errors)}`);
      }

      // Log what keys are in data
      logger.log('📊 Response data keys:', Object.keys(json.data));
      
      const aiRecs = json.data?.aiRecommendations;
      
      if (!aiRecs) {
        logger.error('❌ No "aiRecommendations" in data. Data structure:', json.data);
        throw new Error(`Invalid response structure: missing aiRecommendations. Data keys: ${Object.keys(json.data || {}).join(', ')}`);
      }

      const buyRecs = aiRecs?.buyRecommendations || [];
      const portfolioAnalysis = aiRecs?.portfolioAnalysis;
      
      logger.log('✅ NextMoveModal: Direct fetch succeeded', {
        hasData: !!aiRecs,
        hasPortfolioAnalysis: !!portfolioAnalysis,
        portfolioValue: portfolioAnalysis?.totalValue,
        buyCount: buyRecs.length,
        buyRecs: buyRecs.map((r: any) => ({ symbol: r.symbol, companyName: r.companyName })),
        sellCount: aiRecs?.sellRecommendations?.length ?? 0,
        rebalanceCount: aiRecs?.rebalanceSuggestions?.length ?? 0,
        aiRecommendationsKeys: Object.keys(aiRecs),
      });
      
      logger.log('✅ Setting state with data...');
      setDirectFetchData(json.data);
      setDirectFetchError(null);
      setRetryCount(0); // Reset on success
      setDirectFetchLoading(false); // IMPORTANT: Set loading to false on success
      logger.log('✅ State updated - loading should be false now');
    } catch (error: any) {
      logger.error(`❌ NextMoveModal: Direct fetch failed (attempt ${attempt}):`, {
        message: error?.message,
        name: error?.name,
      });
      setDirectFetchError(error);
      
      // Retry with exponential backoff
      if (attempt < maxRetries) {
        const delay = 1000 * Math.pow(2, attempt - 1); // 1s, 2s, 4s
        logger.log(`⏳ Retrying in ${delay}ms...`);
        setTimeout(() => {
          performDirectFetch(attempt + 1);
        }, delay);
      } else {
        setDirectFetchLoading(false); // Stop loading on final failure
      }
    }
  }, [visible]);

  // Auto-trigger direct fetch if Apollo hangs (after 2 seconds for faster UX)
  React.useEffect(() => {
    if (visible && loading && !data && !error && !useDirectFetch && !directFetchData) {
      const timeoutId = setTimeout(() => {
        logger.log('⏱️ Apollo query taking too long (>2s), switching to direct fetch');
        setUseDirectFetch(true);
        performDirectFetch();
      }, 2000); // Wait 2 seconds for Apollo, then fallback (faster UX)
      return () => clearTimeout(timeoutId);
    }
  }, [visible, loading, data, error, useDirectFetch, directFetchData, performDirectFetch]);

  // Use direct fetch if Apollo fails
  React.useEffect(() => {
    if (visible && error && !useDirectFetch && retryCount === 0) {
      // Apollo failed, try direct fetch
      logger.log('🔄 Apollo failed, switching to direct fetch');
      setUseDirectFetch(true);
      performDirectFetch(1);
    } else if (visible && useDirectFetch && !directFetchData && !directFetchLoading && retryCount === 0) {
      // Use direct fetch as primary if enabled (only trigger once)
      performDirectFetch(1);
    }
  }, [visible, error, useDirectFetch, directFetchData, directFetchLoading, retryCount, performDirectFetch]);

  // Additional debug logging
  React.useEffect(() => {
    logger.log('🔍 NextMoveModal: Query state', {
      visible,
      apolloLoading: loading,
      apolloHasData: !!data,
      apolloHasError: !!error,
      directFetchLoading,
      directFetchHasData: !!directFetchData,
      directFetchHasError: !!directFetchError,
      useDirectFetch,
      networkStatus,
      apolloDataKeys: data ? Object.keys(data) : [],
      directFetchDataKeys: directFetchData ? Object.keys(directFetchData) : [],
      effectiveDataKeys: effectiveData ? Object.keys(effectiveData) : [],
      effectiveHasAiRecs: !!effectiveData?.aiRecommendations,
      effectiveBuyCount: effectiveData?.aiRecommendations?.buyRecommendations?.length ?? 0,
    });
  }, [visible, loading, networkStatus, data, error, directFetchLoading, directFetchData, directFetchError, useDirectFetch, effectiveData]);

  // Debug: Log when modal visibility changes
  React.useEffect(() => {
    logger.log('👁️ NextMoveModal: Visibility changed', { visible, loading, hasData: !!data });
  }, [visible, loading, data]);

  // Direct fetch test to debug network issues
  React.useEffect(() => {
    if (visible && !data && loading) {
      // Test direct fetch after 2 seconds if still loading
      const timeoutId = setTimeout(async () => {
        logger.log('🧪 NextMoveModal: Testing direct fetch...');
        try {
          // Use the centralized API config instead of hardcoded localhost
          const { API_GRAPHQL } = await import('../config/api');
          logger.log('🧪 [NextMoveModal] Test fetch using URL:', API_GRAPHQL);
          
          const response = await fetch(API_GRAPHQL, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer dev-token-1762831885',
            },
            body: JSON.stringify({
              query: `
                query GetAIRecommendations($usingDefaults: Boolean) {
                  aiRecommendations(usingDefaults: $usingDefaults) {
                    portfolioAnalysis {
                      totalValue
                    }
                    buyRecommendations {
                      symbol
                      reasoning
                    }
                  }
                }
              `,
              variables: { usingDefaults: true },
              operationName: 'GetAIRecommendations', // Explicitly set to match query name
            }),
          });
          logger.log('🧪 Direct fetch response:', {
            status: response.status,
            ok: response.ok,
            headers: Object.fromEntries(response.headers.entries()),
          });
          const text = await response.text();
          logger.log('🧪 Direct fetch body (first 500 chars):', text.substring(0, 500));
          try {
            const json = JSON.parse(text);
            logger.log('🧪 Direct fetch parsed JSON:', {
              hasData: !!json.data,
              hasAiRecommendations: !!json.data?.aiRecommendations,
            });
          } catch (e) {
            logger.error('🧪 Failed to parse JSON:', e);
          }
        } catch (error) {
          logger.error('🧪 Direct fetch error:', {
            message: error?.message,
            name: error?.name,
            stack: error?.stack?.substring(0, 300),
          });
        }
      }, 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [visible, data, loading]);

  // Refetch when modal becomes visible and query hasn't run yet
  React.useEffect(() => {
    if (visible) {
      // If we have no data and we're not loading, trigger a refetch
      if (!data && !loading) {
        logger.log('🔄 NextMoveModal: Modal opened, triggering refetch...');
        refetch().catch((err) => {
          logger.error('❌ NextMoveModal: Refetch failed', err);
        });
      }
    }
  }, [visible, data, loading, refetch]);

  // Use direct fetch data if available, otherwise use Apollo data
  const effectiveData = useDirectFetch ? directFetchData : data;
  const effectiveLoading = useDirectFetch ? directFetchLoading : loading;
  const effectiveError = useDirectFetch ? directFetchError : error;

  const ideas: Idea[] = React.useMemo(() => {
    logger.log('💡 Ideas useMemo called:', {
      effectiveLoading,
      hasEffectiveData: !!effectiveData,
      hasAiRecs: !!effectiveData?.aiRecommendations,
      buyRecsCount: effectiveData?.aiRecommendations?.buyRecommendations?.length ?? 0,
    });

    // If we have data, use it even if loading is still true (race condition fix)
    if (!effectiveData?.aiRecommendations) {
      return [];
    }

    const recommendations = effectiveData.aiRecommendations;
    const result: Idea[] = [];

    // Transform buy recommendations
    if (recommendations.buyRecommendations) {
      recommendations.buyRecommendations.forEach((rec: any) => {
        // Map confidence to conviction: 0-0.4 = calm, 0.4-0.7 = balanced, 0.7-1.0 = bold
        let conviction: 'calm' | 'balanced' | 'bold' = 'balanced';
        if (rec.confidence >= 0.7) conviction = 'bold';
        else if (rec.confidence <= 0.4) conviction = 'calm';

        // Map allocation to sizePct (allocation is a percentage like 25.3)
        const sizePct = rec.allocation ? Math.round(rec.allocation) : 0;

        result.push({
          symbol: rec.symbol,
          action: 'BUY',
          conviction,
          sizePct,
          thesis: rec.reasoning || `Expected return: ${((rec.expectedReturn || 0) * 100).toFixed(1)}%`,
        });
      });
    }

    // Transform sell recommendations to TRIM
    if (recommendations.sellRecommendations) {
      recommendations.sellRecommendations.forEach((rec: any) => {
        result.push({
          symbol: rec.symbol,
          action: 'TRIM',
          conviction: 'balanced', // Default for sell recommendations
          sizePct: -1, // Negative indicates reduction
          thesis: rec.reasoning || 'Consider reducing position',
        });
      });
    }

    // Transform rebalance suggestions (if they indicate HOLD or adjustments)
    if (recommendations.rebalanceSuggestions) {
      recommendations.rebalanceSuggestions
        .filter((suggestion: any) => suggestion.action === 'HOLD' || suggestion.priority === 'high')
        .forEach((suggestion: any) => {
          const allocationDiff = suggestion.suggestedAllocation - suggestion.currentAllocation;
          if (Math.abs(allocationDiff) < 1) {
            // Small change, treat as HOLD
            result.push({
              symbol: suggestion.action === 'HOLD' ? 'PORTFOLIO' : 'REBALANCE',
              action: 'HOLD',
              conviction: 'calm',
              sizePct: 0,
              thesis: suggestion.reasoning || 'Maintain current allocation',
            });
          }
        });
    }

    // Limit to top 5 recommendations
    const finalIdeas = result.slice(0, 5);
    logger.log('💡 Ideas useMemo returning:', {
      count: finalIdeas.length,
      symbols: finalIdeas.map(i => i.symbol),
    });
    return finalIdeas;
  }, [effectiveData, effectiveLoading, effectiveError]);

  const displayValue = effectiveData?.aiRecommendations?.portfolioAnalysis?.totalValue || portfolioValue;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.title}>Next Move</Text>
            <TouchableOpacity onPress={onClose}><Icon name="x" size={20} color="#8E8E93" /></TouchableOpacity>
          </View>
          <Text style={styles.subtitle}>Portfolio: ${displayValue.toLocaleString()}</Text>
          
          {effectiveLoading && !effectiveData?.aiRecommendations && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#00cc99" />
              <Text style={styles.loadingText}>Loading AI recommendations...</Text>
              {useDirectFetch && <Text style={styles.loadingSubtext}>Using direct connection...</Text>}
            </View>
          )}

          {effectiveError && !effectiveData?.aiRecommendations && (
            <View style={styles.errorContainer}>
              <Icon name="alert-circle" size={20} color="#EF4444" />
              <Text style={styles.errorText}>Failed to load recommendations</Text>
              <Text style={styles.errorDetail}>{effectiveError.message || 'Unknown error occurred'}</Text>
              <TouchableOpacity 
                style={styles.retryButton}
                onPress={() => {
                  logger.log('🔄 NextMoveModal: Manual retry');
                  if (useDirectFetch) {
                    performDirectFetch(1);
                  } else {
                    refetch();
                  }
                }}
              >
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          )}

          {ideas.length === 0 && !effectiveLoading && !effectiveError && (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No recommendations available at this time.</Text>
            </View>
          )}

          {(ideas.length > 0 || effectiveData?.aiRecommendations) && (
            <FlatList
              data={ideas.length > 0 ? ideas : (() => {
                // Fallback: transform data directly if ideas array is empty
                const recs = effectiveData?.aiRecommendations?.buyRecommendations || [];
                return recs.slice(0, 5).map((rec: any) => ({
                  symbol: rec.symbol,
                  action: 'BUY' as const,
                  conviction: (rec.confidence >= 0.7 ? 'bold' : rec.confidence <= 0.4 ? 'calm' : 'balanced') as const,
                  sizePct: Math.round(rec.allocation || 0),
                  thesis: rec.reasoning || `Expected return: ${((rec.expectedReturn || 0) * 100).toFixed(1)}%`,
                }));
              })()}
              keyExtractor={(i, index) => `${i.symbol}-${index}`}
              renderItem={({ item }) => (
                <View style={styles.row}>
                  <View style={styles.left}>
                    <Text style={styles.symbol}>{item.symbol}</Text>
                    <Text style={styles.thesis}>{item.thesis}</Text>
                  </View>
                  <View style={styles.right}>
                    <Text style={[styles.action, item.action === 'BUY' ? styles.buy : item.action === 'TRIM' ? styles.trim : styles.hold]}>{item.action}</Text>
                    {item.sizePct !== 0 && <Text style={styles.size}>{item.sizePct > 0 ? '+' : ''}{item.sizePct}%</Text>}
                  </View>
                </View>
              )}
            />
          )}

          <View style={styles.footer}>
            <Icon name="alert-triangle" size={14} color="#8E8E93" />
            <Text style={styles.disclaimer}>Educational purposes only. Not investment advice.</Text>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' },
  card: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 16, maxHeight: '70%' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 16, fontWeight: '700', color: '#1C1C1E' },
  subtitle: { color: '#666', marginTop: 4, marginBottom: 8 },
  loadingContainer: { alignItems: 'center', justifyContent: 'center', padding: 20, gap: 8 },
  loadingText: { fontSize: 14, color: '#666' },
  loadingSubtext: { fontSize: 12, color: '#999', marginTop: 4 },
  errorContainer: { alignItems: 'center', justifyContent: 'center', padding: 20, gap: 8 },
  errorText: { fontSize: 14, color: '#EF4444', fontWeight: '600', textAlign: 'center' },
  errorDetail: { fontSize: 12, color: '#666', textAlign: 'center', marginTop: 4 },
  retryButton: { marginTop: 12, paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#00cc99', borderRadius: 8 },
  retryButtonText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  emptyContainer: { padding: 20, alignItems: 'center' },
  emptyText: { fontSize: 14, color: '#666', textAlign: 'center' },
  row: { flexDirection: 'row', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  left: { flex: 1 },
  right: { alignItems: 'flex-end' },
  symbol: { fontSize: 14, fontWeight: '700', color: '#1C1C1E' },
  thesis: { fontSize: 12, color: '#666', marginTop: 2 },
  action: { fontSize: 12, fontWeight: '700' },
  buy: { color: '#22C55E' },
  hold: { color: '#8E8E93' },
  trim: { color: '#EF4444' },
  size: { fontSize: 12, color: '#1C1C1E' },
  footer: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  disclaimer: { fontSize: 11, color: '#8E8E93' },
});



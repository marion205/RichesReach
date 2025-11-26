import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

interface ExecutionSuggestion {
  orderType?: string;
  priceBand?: number[];
  timeInForce?: string;
  time_in_force?: string; // Support both camelCase and snake_case
  entryStrategy?: string;
  entry_strategy?: string; // Support both camelCase and snake_case
  bracketLegs?: {
    stop?: number;
    target1?: number;
    target2?: number;
    orderStructure?: any;
  };
  bracket_legs?: {
    stop?: number;
    target1?: number;
    target2?: number;
    orderStructure?: any;
  };
  suggestedSize?: number;
  rationale?: string;
  microstructureSummary?: string;
  microstructure_summary?: string; // Support both camelCase and snake_case
}

interface ExecutionSuggestionCardProps {
  suggestion: ExecutionSuggestion | null;
  isRefreshing?: boolean;
}

const C = {
  bg: '#0A0A0A',
  card: '#1A1A1A',
  text: '#FFFFFF',
  sub: '#888888',
  primary: '#00D4FF',
  success: '#00FF88',
  danger: '#FF4444',
  warning: '#FFAA00',
};

function ExecutionSuggestionCardComponent({ suggestion, isRefreshing = false }: ExecutionSuggestionCardProps) {
  // Debug logging to see if it's remount or re-render
  useEffect(() => {
    if (__DEV__) {
      console.log(`🔄 ExecutionSuggestionCard MOUNT: ${suggestion?.orderType || 'no-suggestion'}`);
      return () => {
        console.log(`🗑️ ExecutionSuggestionCard UNMOUNT: ${suggestion?.orderType || 'no-suggestion'}`);
      };
    }
  }, []);

  if (__DEV__) {
    console.log(`📊 ExecutionSuggestionCard RENDER:`, {
      hasSuggestion: !!suggestion,
      orderType: suggestion?.orderType,
      isRefreshing,
    });
  }

  // Pure presentational component - no conditional rendering that would cause blinking
  // Only hide if we truly have no suggestion at all
  // We render even if orderType is missing - the card will show whatever data is available
  if (!suggestion) {
    if (__DEV__) {
      console.log(`⚠️ ExecutionSuggestionCard: No suggestion provided, returning null`);
    }
    return null;
  }

  const priceBand = suggestion.priceBand || [];
  const bracketLegs = suggestion.bracketLegs || suggestion.bracket_legs || {};
  
  // Parse rationale to extract structured info if fields are null
  const rationale = suggestion.rationale || '';
  let extractedTimeInForce = suggestion.timeInForce || suggestion.time_in_force;
  let extractedOrderType = suggestion.orderType;
  
  if (rationale && !extractedTimeInForce) {
    // Extract time in force from rationale
    if (rationale.includes('IOC')) extractedTimeInForce = 'IOC';
    else if (rationale.includes('GTC')) extractedTimeInForce = 'GTC';
    else if (rationale.includes('DAY')) extractedTimeInForce = 'DAY';
  }
  
  if (rationale && !extractedOrderType) {
    // Extract order type from rationale
    if (rationale.includes('LIMIT')) extractedOrderType = 'LIMIT';
    else if (rationale.includes('MARKET')) extractedOrderType = 'MARKET';
    else if (rationale.includes('STOP')) extractedOrderType = 'STOP';
  }
  
  // Extract price band from rationale if not provided
  let extractedPriceBand = priceBand;
  if (rationale && !extractedPriceBand.length) {
    const priceBandMatch = rationale.match(/Price band:\s*\$?([\d.]+)\s*-\s*\$?([\d.]+)/i);
    if (priceBandMatch) {
      extractedPriceBand = [parseFloat(priceBandMatch[1]), parseFloat(priceBandMatch[2])];
    }
  }
  
  const timeInForce = extractedTimeInForce || 'DAY';
  const entryStrategy = suggestion.entryStrategy || suggestion.entry_strategy || '';
  const microstructureSummary = suggestion.microstructureSummary || suggestion.microstructure_summary || '';

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Icon name="zap" size={16} color={C.primary} />
        <Text style={styles.title}>Smart Order Suggestion</Text>
        {extractedOrderType ? (
          <View style={[styles.orderTypeBadge, extractedOrderType === 'LIMIT' ? styles.limitBadge : styles.marketBadge]}>
            <Text style={styles.orderTypeText}>{extractedOrderType}</Text>
          </View>
        ) : null}
        {/* Subtle refreshing indicator when we have valid data but are refreshing */}
        {isRefreshing && (
          <ActivityIndicator size="small" color={C.primary} style={{ marginLeft: 8 }} />
        )}
      </View>

      <View style={styles.content}>
        {/* Price Band */}
        {extractedPriceBand.length === 2 && (
          <View style={styles.priceBandRow}>
            <Text style={styles.label}>Price Band:</Text>
            <Text style={styles.priceBand}>
              ${extractedPriceBand[0].toFixed(2)} - ${extractedPriceBand[1].toFixed(2)}
            </Text>
          </View>
        )}

        {/* Time in Force - Always show */}
        <View style={styles.row}>
          <Text style={styles.label}>Time in Force:</Text>
          <Text style={styles.value}>{timeInForce}</Text>
        </View>

        {/* Entry Strategy - Show if available */}
        {entryStrategy && (
          <View style={styles.strategyRow}>
            <Icon name="info" size={14} color={C.primary} />
            <Text style={styles.strategyText}>{entryStrategy}</Text>
          </View>
        )}

        {/* Bracket Legs */}
        {bracketLegs.stop && (
          <View style={styles.bracketSection}>
            <Text style={styles.bracketTitle}>Bracket Order:</Text>
            <View style={styles.bracketRow}>
              <View style={styles.bracketItem}>
                <Text style={styles.bracketLabel}>Stop</Text>
                <Text style={[styles.bracketValue, styles.stopValue]}>
                  ${bracketLegs.stop.toFixed(2)}
                </Text>
              </View>
              {bracketLegs.target1 && (
                <View style={styles.bracketItem}>
                  <Text style={styles.bracketLabel}>Target 1</Text>
                  <Text style={[styles.bracketValue, styles.targetValue]}>
                    ${bracketLegs.target1.toFixed(2)}
                  </Text>
                </View>
              )}
              {bracketLegs.target2 && (
                <View style={styles.bracketItem}>
                  <Text style={styles.bracketLabel}>Target 2</Text>
                  <Text style={[styles.bracketValue, styles.targetValue]}>
                    ${bracketLegs.target2.toFixed(2)}
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Microstructure Summary */}
        {microstructureSummary && (
          <View style={styles.microstructureRow}>
            <Icon name="activity" size={14} color={C.primary} />
            <Text style={styles.microstructureText}>{microstructureSummary}</Text>
          </View>
        )}

        {/* Rationale - Always show prominently since it contains the main info */}
        {suggestion.rationale && (
          <View style={styles.rationaleRow}>
            <Icon name="info" size={14} color={C.primary} />
            <Text style={styles.rationaleText}>{suggestion.rationale}</Text>
          </View>
        )}
        
        {/* Show a message if we have no structured data but rationale exists */}
        {suggestion.rationale && !suggestion.orderType && !priceBand.length && (
          <View style={[styles.rationaleRow, { marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#2A2A2A' }]}>
            <Icon name="info" size={14} color={C.primary} />
            <Text style={[styles.rationaleText, { color: C.sub, fontSize: 10 }]}>
              Detailed order parameters will be available once the suggestion is fully processed.
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

// Memoize with shallow comparison - only re-render if suggestion or isRefreshing actually changes
export const ExecutionSuggestionCard = React.memo(
  ExecutionSuggestionCardComponent,
  (prevProps, nextProps) => {
    // Only re-render if suggestion data or refreshing state actually changes
    if (prevProps.isRefreshing !== nextProps.isRefreshing) return false;
    if (!prevProps.suggestion && !nextProps.suggestion) return true;
    if (!prevProps.suggestion || !nextProps.suggestion) return false;
    
    const prev = prevProps.suggestion;
    const next = nextProps.suggestion;
    
    return (
      prev.orderType === next.orderType &&
      prev.timeInForce === next.timeInForce &&
      prev.entryStrategy === next.entryStrategy &&
      JSON.stringify(prev.priceBand) === JSON.stringify(next.priceBand) &&
      prev.bracketLegs?.stop === next.bracketLegs?.stop &&
      prev.bracketLegs?.target1 === next.bracketLegs?.target1 &&
      prev.bracketLegs?.target2 === next.bracketLegs?.target2 &&
      prev.rationale === next.rationale &&
      prev.microstructureSummary === next.microstructureSummary
    );
  }
);

const styles = StyleSheet.create({
  container: {
    backgroundColor: C.card,
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#2A2A2A',
    borderLeftWidth: 3,
    borderLeftColor: C.primary,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    gap: 8,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
    flex: 1,
  },
  orderTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  limitBadge: {
    backgroundColor: C.primary + '20',
  },
  marketBadge: {
    backgroundColor: C.warning + '20',
  },
  orderTypeText: {
    fontSize: 11,
    fontWeight: '600',
    color: C.text,
  },
  loader: {
    marginVertical: 8,
  },
  content: {
    gap: 8,
  },
  priceBandRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  label: {
    fontSize: 12,
    color: C.sub,
  },
  priceBand: {
    fontSize: 13,
    fontWeight: '600',
    color: C.primary,
  },
  value: {
    fontSize: 12,
    fontWeight: '600',
    color: C.text,
  },
  strategyRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    paddingVertical: 4,
  },
  strategyText: {
    fontSize: 11,
    color: C.sub,
    flex: 1,
    lineHeight: 16,
  },
  bracketSection: {
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
  },
  bracketTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: C.text,
    marginBottom: 6,
  },
  bracketRow: {
    flexDirection: 'row',
    gap: 12,
  },
  bracketItem: {
    flex: 1,
  },
  bracketLabel: {
    fontSize: 10,
    color: C.sub,
    marginBottom: 2,
  },
  bracketValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  stopValue: {
    color: C.danger,
  },
  targetValue: {
    color: C.success,
  },
  microstructureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
    paddingVertical: 6,
    paddingHorizontal: 8,
    backgroundColor: '#1A2A3A',
    borderRadius: 6,
  },
  microstructureText: {
    fontSize: 11,
    fontWeight: '600',
    color: C.primary,
    flex: 1,
    letterSpacing: 0.3,
  },
  rationaleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    marginTop: 4,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#2A2A2A',
  },
  rationaleText: {
    fontSize: 11,
    color: C.sub,
    flex: 1,
    fontStyle: 'italic',
    lineHeight: 16,
  },
});

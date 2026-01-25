import React, {
  useMemo,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import {
  View,
  Text,
  StyleSheet,
  PanResponder,
  LayoutChangeEvent,
  Modal,
  Pressable,
  ActivityIndicator,
} from "react-native";
import Svg, { Polyline, Circle, Line } from "react-native-svg";
import * as Haptics from "expo-haptics";
import logger from "../../utils/logger";

export type ChartPoint = {
  timestamp: string; // ISO string
  price: number;
};

export type MomentCategory =
  | "EARNINGS"
  | "NEWS"
  | "INSIDER"
  | "MACRO"
  | "SENTIMENT"
  | "OTHER";

export type StockMoment = {
  id: string;
  symbol: string;
  timestamp: string; // ISO
  category: MomentCategory;
  title: string;
  quickSummary: string;
  deepSummary: string;
};

type ChartWithMomentsProps = {
  priceSeries: ChartPoint[];
  moments: StockMoment[];
  onMomentChange?: (moment: StockMoment | null) => void;
  /**
   * When provided, ChartWithMoments will treat this as the active moment,
   * instead of using its own internal state. This lets the story player drive it.
   */
  activeMomentId?: string | null;
  /**
   * Long-press behavior: called when the user presses and holds
   * near a moment dot on the chart. Perfect for "Play from this dot".
   */
  onMomentLongPress?: (moment: StockMoment) => void;
  height?: number;
  loading?: boolean; // Optional loading prop for parent control
};

const LONG_PRESS_DURATION_MS = 500;
const LONG_PRESS_MOVE_TOLERANCE_PX = 20;

// Binary search helper for finding closest point index
const findClosestPointIndex = (
  targetTime: number,
  points: ChartPoint[],
): number => {
  if (!points.length) return -1;
  let left = 0;
  let right = points.length - 1;
  let closestIndex = 0;
  let minDiff = Math.abs(new Date(points[0].timestamp).getTime() - targetTime);

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    const midTime = new Date(points[mid].timestamp).getTime();
    const diff = Math.abs(midTime - targetTime);

    if (diff < minDiff) {
      minDiff = diff;
      closestIndex = mid;
    }

    if (midTime < targetTime) {
      left = mid + 1;
    } else if (midTime > targetTime) {
      right = mid - 1;
    } else {
      return mid; // Exact match
    }
  }

  // Check one more on each side for edge cases
  if (closestIndex > 0) {
    const prevDiff = Math.abs(
      new Date(points[closestIndex - 1].timestamp).getTime() - targetTime,
    );
    if (prevDiff < minDiff) {
      closestIndex--;
    }
  }
  if (closestIndex < points.length - 1) {
    const nextDiff = Math.abs(
      new Date(points[closestIndex + 1].timestamp).getTime() - targetTime,
    );
    if (nextDiff < minDiff) {
      closestIndex++;
    }
  }

  return closestIndex;
};

const ChartWithMoments: React.FC<ChartWithMomentsProps> = ({
  priceSeries = [],
  moments = [],
  onMomentChange,
  activeMomentId,
  onMomentLongPress,
  height = 220,
  loading = false,
}) => {
  const [width, setWidth] = useState(0);
  const [internalActiveMomentId, setInternalActiveMomentId] =
    useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  const longPressTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressStartXRef = useRef<number | null>(null);

  const sortedPoints = useMemo(
    () =>
      [...priceSeries].sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    [priceSeries],
  );

  const sortedMoments = useMemo(
    () =>
      [...moments].sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    [moments],
  );

  // Use external active id if provided, otherwise local gesture state
  const effectiveActiveMomentId =
    activeMomentId !== undefined ? activeMomentId : internalActiveMomentId;

  const timeRange = useMemo(() => {
    if (!sortedPoints.length) return null;
    const minT = new Date(sortedPoints[0].timestamp).getTime();
    const maxT =
      new Date(sortedPoints[sortedPoints.length - 1].timestamp).getTime();
    return { minT, maxT };
  }, [sortedPoints]);

  const priceRange = useMemo(() => {
    if (!sortedPoints.length) return null;
    let minP = sortedPoints[0].price;
    let maxP = sortedPoints[0].price;
    sortedPoints.forEach((p) => {
      if (p.price < minP) minP = p.price;
      if (p.price > maxP) maxP = p.price;
    });
    const pad = (maxP - minP || 1) * 0.1;
    return { minP: minP - pad, maxP: maxP + pad };
  }, [sortedPoints]);

  const activeMoment = useMemo(
    () => sortedMoments.find((m) => m.id === effectiveActiveMomentId) || null,
    [sortedMoments, effectiveActiveMomentId],
  );

  // SVG coordinate helpers (memoized to prevent recalc) - defined before use
  const toSvgX = useCallback(
    (timestamp: string): number => {
      if (!timeRange || width <= 0) return 0;
      const { minT, maxT } = timeRange;
      const t = new Date(timestamp).getTime();
      const ratio = (t - minT) / (maxT - minT || 1);
      return Math.max(0, Math.min(width, ratio * width));
    },
    [timeRange, width],
  );

  const toSvgY = useCallback((price: number): number => {
    if (!priceRange) return height / 2;
    const { minP, maxP } = priceRange;
    const ratio = (price - minP) / (maxP - minP || 1);
    return Math.max(0, Math.min(height, height - ratio * height));
  }, [priceRange, height]);

  // Precompute moment positions (x, y) for efficiency
  const momentPositions = useMemo(() => {
    if (!timeRange || !priceRange || width <= 0 || !sortedPoints.length) {
      return [];
    }

    return sortedMoments.map((m) => {
      const x = toSvgX(m.timestamp);

      const closestIndex = findClosestPointIndex(
        new Date(m.timestamp).getTime(),
        sortedPoints,
      );
      const closestPrice =
        closestIndex >= 0 ? sortedPoints[closestIndex].price : sortedPoints[0].price;
      const y = toSvgY(closestPrice);

      return { moment: m, x, y };
    });
  }, [sortedMoments, timeRange, priceRange, width, sortedPoints, toSvgX, toSvgY]);

  const handleLayout = useCallback((e: LayoutChangeEvent) => {
    setWidth(e.nativeEvent.layout.width);
  }, []);

  const findNearestMomentForX = useCallback(
    (x: number): StockMoment | null => {
      if (!timeRange || !momentPositions.length || width <= 0) return null;

      const { minT, maxT } = timeRange;
      const ratio = x / width;
      const t = minT + ratio * (maxT - minT);

      let nearest: StockMoment | null = null;
      let bestDist = Infinity;

      momentPositions.forEach(({ moment }) => {
        const mt = new Date(moment.timestamp).getTime();
        const dist = Math.abs(mt - t);
        if (dist < bestDist) {
          bestDist = dist;
          nearest = moment;
        }
      });

      const maxDist = (maxT - minT) * 0.2;
      return bestDist > maxDist ? null : nearest;
    },
    [timeRange, momentPositions, width],
  );

  const handleMomentSelectedFromGesture = useCallback(
    (moment: StockMoment | null) => {
      if (activeMomentId === undefined) {
        const prevId = internalActiveMomentId;
        const newId = moment?.id ?? null;
        if (newId !== prevId && moment) {
          // subtle tick when user hits a new moment dot
          Haptics.selectionAsync().catch((e) => logger.warn('Haptic error:', e)); // Handle potential errors
        }
        setInternalActiveMomentId(newId);
      }
      onMomentChange?.(moment);
    },
    [activeMomentId, internalActiveMomentId, onMomentChange],
  );

  // Long-press tracking
  const clearLongPressTimeout = useCallback(() => {
    if (longPressTimeoutRef.current) {
      clearTimeout(longPressTimeoutRef.current);
      longPressTimeoutRef.current = null;
    }
    longPressStartXRef.current = null;
  }, []);

  const scheduleLongPress = useCallback(
    (x: number, moment: StockMoment | null) => {
      clearLongPressTimeout();

      longPressStartXRef.current = x;

      if (!moment || !onMomentLongPress) return;

      longPressTimeoutRef.current = setTimeout(() => {
        longPressTimeoutRef.current = null;
        // Stronger haptic for "Play from this dot"
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(
          console.warn,
        );
        onMomentLongPress(moment);
      }, LONG_PRESS_DURATION_MS);
    },
    [onMomentLongPress],
  );

  const handleMoveForLongPress = useCallback((x: number) => {
    if (longPressStartXRef.current == null) return;
    const delta = Math.abs(x - longPressStartXRef.current);
    if (delta > LONG_PRESS_MOVE_TOLERANCE_PX) {
      clearLongPressTimeout();
    }
  }, []);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: (evt) => {
          const x = evt.nativeEvent.locationX;
          const m = findNearestMomentForX(x);
          handleMomentSelectedFromGesture(m);
          scheduleLongPress(x, m);
        },
        onPanResponderMove: (evt) => {
          const x = evt.nativeEvent.locationX;
          const m = findNearestMomentForX(x);
          handleMomentSelectedFromGesture(m);
          handleMoveForLongPress(x);
        },
        onPanResponderRelease: clearLongPressTimeout,
        onPanResponderTerminationRequest: () => true,
        onPanResponderTerminate: clearLongPressTimeout,
      }),
    [
      findNearestMomentForX,
      handleMomentSelectedFromGesture,
      scheduleLongPress,
      handleMoveForLongPress,
      clearLongPressTimeout,
    ],
  );


  const linePoints = useMemo(() => {
    if (!sortedPoints.length || width <= 0) return "";
    return sortedPoints
      .map((p) => `${toSvgX(p.timestamp)},${toSvgY(p.price)}`)
      .join(" ");
  }, [sortedPoints, toSvgX, toSvgY, width]);

  // Cleanup long-press timeout on unmount
  useEffect(() => {
    return () => {
      clearLongPressTimeout();
    };
  }, [clearLongPressTimeout]);

  // Loading state
  if (loading || width === 0) {
    return (
      <View
        style={[styles.chartContainer, { height }]}
        accessible={true}
        accessibilityRole="progressbar"
        accessibilityLabel="Loading chart..."
      >
        <ActivityIndicator size="small" color="#2F80ED" />
      </View>
    );
  }

  // Empty state
  if (!sortedPoints.length) {
    return (
      <View
        style={[styles.chartContainer, { height }]}
        accessible={true}
        accessibilityLabel="No price data available"
      >
        <Text style={styles.emptyText}>No price data</Text>
      </View>
    );
  }

  if (!sortedMoments.length) {
    return (
      <View
        style={[styles.chartContainer, { height }]}
        {...panResponder.panHandlers}
        accessible={true}
        accessibilityLabel="Price chart with no key moments"
      >
        <Svg width={width} height={height}>
          <Line
            x1={0}
            y1={height - 1}
            x2={width}
            y2={height - 1}
            stroke="#E0E0E0"
            strokeWidth={1}
          />
          {linePoints.length > 0 && (
            <Polyline
              points={linePoints}
              fill="none"
              stroke="#2F80ED"
              strokeWidth={2}
            />
          )}
        </Svg>
      </View>
    );
  }

  return (
    <View>
      <View
        style={[styles.chartContainer, { height }]}
        onLayout={handleLayout}
        {...panResponder.panHandlers}
        accessible={true}
        accessibilityLabel={`Interactive chart for ${sortedMoments.length} key moments`}
      >
        <Svg width={width} height={height}>
          <Line
            x1={0}
            y1={height - 1}
            x2={width}
            y2={height - 1}
            stroke="#E0E0E0"
            strokeWidth={1}
          />

          {linePoints.length > 0 && (
            <Polyline
              points={linePoints}
              fill="none"
              stroke="#2F80ED"
              strokeWidth={2}
            />
          )}

          {momentPositions.map(({ moment, x, y }) => {
            const isActive = moment.id === effectiveActiveMomentId;
            return (
              <Circle
                key={moment.id}
                cx={x}
                cy={y}
                r={isActive ? 5 : 4}
                stroke="#2F80ED"
                strokeWidth={isActive ? 2 : 1}
                fill={isActive ? "#2F80ED" : "#FFFFFF"}
                accessible={true}
                accessibilityLabel={`${moment.category} moment: ${moment.title}`}
              />
            );
          })}
        </Svg>
      </View>

      {activeMoment && (
        <Pressable
          style={styles.momentCard}
          onPress={() => setShowDetail(true)}
          accessible={true}
          accessibilityRole="button"
          accessibilityLabel={`View details for ${activeMoment.title}`}
        >
          <Text style={styles.momentCategory} aria-label={`${activeMoment.category} category`}>
            {activeMoment.category}
          </Text>
          <Text style={styles.momentTitle} numberOfLines={1}>
            {activeMoment.title}
          </Text>
          <Text style={styles.momentSummary} numberOfLines={3}>
            {activeMoment.quickSummary}
          </Text>
          <Text style={styles.momentAction}>Tap for full story</Text>
        </Pressable>
      )}

      <Modal
        visible={showDetail && !!activeMoment}
        animationType="slide"
        transparent
        onRequestClose={() => setShowDetail(false)}
        accessible={true}
        accessibilityViewIsModal={true}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            {activeMoment && (
              <>
                <Text style={styles.modalCategory}>
                  {activeMoment.category}
                </Text>
                <Text style={styles.modalTitle}>{activeMoment.title}</Text>
                <Text style={styles.modalBody}>{activeMoment.deepSummary}</Text>
                <Pressable
                  style={styles.modalButton}
                  onPress={() => setShowDetail(false)}
                  accessible={true}
                  accessibilityRole="button"
                  accessibilityLabel="Close modal"
                >
                  <Text style={styles.modalButtonText}>Close</Text>
                </Pressable>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  chartContainer: {
    width: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
  },
  momentCard: {
    marginTop: 12,
    borderRadius: 16,
    padding: 12,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000000",
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  momentCategory: {
    fontSize: 11,
    fontWeight: "600",
    letterSpacing: 0.5,
    color: "#2F80ED",
    marginBottom: 4,
  },
  momentTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  momentSummary: {
    fontSize: 13,
    color: "#4B5563",
  },
  momentAction: {
    marginTop: 6,
    fontSize: 12,
    fontWeight: "500",
    color: "#2F80ED",
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "flex-end",
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    backgroundColor: "#FFFFFF",
    maxHeight: "70%",
  },
  modalCategory: {
    fontSize: 12,
    fontWeight: "600",
    color: "#2F80ED",
    marginBottom: 6,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 10,
  },
  modalBody: {
    fontSize: 14,
    color: "#374151",
    lineHeight: 20,
  },
  modalButton: {
    marginTop: 18,
    borderRadius: 999,
    paddingVertical: 10,
    alignItems: "center",
    backgroundColor: "#111827",
  },
  modalButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});

export default ChartWithMoments;

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
  useColorScheme,
} from "react-native";
import Svg, {
  Polyline,
  Circle,
  Line,
  Path,
  Defs,
  LinearGradient,
  Stop,
  RadialGradient,
  Text as SvgText,
  G,
} from "react-native-svg";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withTiming,
  interpolate,
} from "react-native-reanimated";
import { LinearGradient as RNLinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { chartThemes, getCategoryStyle, ChartTheme } from "../../theme/chartTheme";
import type { ChartPoint, MomentCategory, StockMoment } from "./ChartWithMoments";

type ChartWithMomentsProps = {
  priceSeries: ChartPoint[];
  moments: StockMoment[];
  onMomentChange?: (moment: StockMoment | null) => void;
  activeMomentId?: string | null;
  onMomentLongPress?: (moment: StockMoment) => void;
  height?: number;
  loading?: boolean;
  theme?: ChartTheme;
};

const LONG_PRESS_DURATION_MS = 500;
const LONG_PRESS_MOVE_TOLERANCE_PX = 20;
const GRID_LINES = 5; // Number of horizontal grid lines
const GRID_LABELS_COUNT = 3; // Number of price labels

// Binary search helper
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
      return mid;
    }
  }

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

// Create smooth curve path using quadratic bezier
const createSmoothPath = (
  points: ChartPoint[],
  toSvgX: (timestamp: string) => number,
  toSvgY: (price: number) => number,
): string => {
  if (points.length < 2) return "";

  let path = `M ${toSvgX(points[0].timestamp)},${toSvgY(points[0].price)}`;

  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const next = points[i + 1] || curr;

    const x1 = toSvgX(prev.timestamp);
    const y1 = toSvgY(prev.price);
    const x2 = toSvgX(curr.timestamp);
    const y2 = toSvgY(curr.price);
    const x3 = toSvgX(next.timestamp);
    const y3 = toSvgY(next.price);

    // Control point for smooth curve
    const cp1x = x1 + (x2 - x1) * 0.5;
    const cp1y = y1;
    const cp2x = x2 - (x3 - x1) * 0.1;
    const cp2y = y2;

    path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${x2},${y2}`;
  }

  return path;
};

// Create area fill path
const createAreaPath = (
  points: ChartPoint[],
  toSvgX: (timestamp: string) => number,
  toSvgY: (price: number) => number,
  height: number,
): string => {
  if (points.length < 2) return "";

  const path = createSmoothPath(points, toSvgX, toSvgY);
  const firstX = toSvgX(points[0].timestamp);
  const lastX = toSvgX(points[points.length - 1].timestamp);

  return `${path} L ${lastX},${height} L ${firstX},${height} Z`;
};

const ChartWithMoments: React.FC<ChartWithMomentsProps> = ({
  priceSeries = [],
  moments = [],
  onMomentChange,
  activeMomentId,
  onMomentLongPress,
  height = 220,
  loading = false,
  theme: propTheme,
}) => {
  const systemTheme = useColorScheme();
  const themeName: ChartTheme = propTheme || (systemTheme === "dark" ? "dark" : "light");
  const theme = chartThemes[themeName];

  const [width, setWidth] = useState(0);
  const [internalActiveMomentId, setInternalActiveMomentId] = useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [crosshairX, setCrosshairX] = useState<number | null>(null);
  const [crosshairPrice, setCrosshairPrice] = useState<number | null>(null);

  const longPressTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressStartXRef = useRef<number | null>(null);

  // Animation values for chart entrance
  const chartOpacity = useSharedValue(0);
  const chartScale = useSharedValue(0.95);

  useEffect(() => {
    chartOpacity.value = withTiming(1, { duration: 500 });
    chartScale.value = withSpring(1, { damping: 15 });
  }, []);

  const sortedPoints = useMemo(
    () =>
      [...priceSeries].sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      ),
    [priceSeries],
  );

  const sortedMoments = useMemo(
    () => {
      const sorted = [...moments].sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      );
      console.log(`[ChartWithMoments] Rendering ${sorted.length} moments`);
      return sorted;
    },
    [moments],
  );

  const effectiveActiveMomentId =
    activeMomentId !== undefined ? activeMomentId : internalActiveMomentId;

  const timeRange = useMemo(() => {
    if (!sortedPoints.length) return null;
    const minT = new Date(sortedPoints[0].timestamp).getTime();
    const maxT = new Date(sortedPoints[sortedPoints.length - 1].timestamp).getTime();
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

  // Calculate price change direction
  const priceChange = useMemo(() => {
    if (!sortedPoints.length) return 0;
    const first = sortedPoints[0].price;
    const last = sortedPoints[sortedPoints.length - 1].price;
    return last - first;
  }, [sortedPoints]);

  const activeMoment = useMemo(
    () => sortedMoments.find((m) => m.id === effectiveActiveMomentId) || null,
  [sortedMoments, effectiveActiveMomentId]);

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

  const toSvgY = useCallback(
    (price: number): number => {
      if (!priceRange) return height / 2;
      const { minP, maxP } = priceRange;
      const ratio = (price - minP) / (maxP - minP || 1);
      return Math.max(0, Math.min(height, height - ratio * height));
    },
    [priceRange, height],
  );

  // Grid lines and labels
  const gridLines = useMemo(() => {
    if (!priceRange || !timeRange) return { lines: [], labels: [] };
    const { minP, maxP } = priceRange;
    const lines = [];
    const labels = [];

    for (let i = 0; i <= GRID_LINES; i++) {
      const ratio = i / GRID_LINES;
      const price = minP + (maxP - minP) * (1 - ratio);
      const y = height * ratio;
      lines.push({ y, price });
      if (i % Math.ceil(GRID_LINES / GRID_LABELS_COUNT) === 0) {
        labels.push({ y, price });
      }
    }

    return { lines, labels };
  }, [priceRange, height]);

  // Smooth path for price line
  const pricePath = useMemo(() => {
    if (!sortedPoints.length || width <= 0) return "";
    return createSmoothPath(sortedPoints, toSvgX, toSvgY);
  }, [sortedPoints, toSvgX, toSvgY, width]);

  // Area fill path
  const areaPath = useMemo(() => {
    if (!sortedPoints.length || width <= 0) return "";
    return createAreaPath(sortedPoints, toSvgX, toSvgY, height);
  }, [sortedPoints, toSvgX, toSvgY, height, width]);

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
        closestIndex >= 0
          ? sortedPoints[closestIndex].price
          : sortedPoints[0].price;
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

  const findPriceAtX = useCallback(
    (x: number): number | null => {
      if (!timeRange || !sortedPoints.length || width <= 0) return null;
      const { minT, maxT } = timeRange;
      const ratio = x / width;
      const t = minT + ratio * (maxT - minT);

      const closestIndex = findClosestPointIndex(t, sortedPoints);
      if (closestIndex >= 0) {
        return sortedPoints[closestIndex].price;
      }
      return null;
    },
    [timeRange, sortedPoints, width],
  );

  const handleMomentSelectedFromGesture = useCallback(
    (moment: StockMoment | null) => {
      if (activeMomentId === undefined) {
        const prevId = internalActiveMomentId;
        const newId = moment?.id ?? null;
        if (newId !== prevId && moment) {
          Haptics.selectionAsync().catch(console.warn);
        }
        setInternalActiveMomentId(newId);
      }
      onMomentChange?.(moment);
    },
    [activeMomentId, internalActiveMomentId, onMomentChange],
  );

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
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(
          console.warn,
        );
        onMomentLongPress(moment);
      }, LONG_PRESS_DURATION_MS);
    },
    [onMomentLongPress, clearLongPressTimeout],
  );

  const handleMoveForLongPress = useCallback(
    (x: number) => {
      if (longPressStartXRef.current == null) return;
      const delta = Math.abs(x - longPressStartXRef.current);
      if (delta > LONG_PRESS_MOVE_TOLERANCE_PX) {
        clearLongPressTimeout();
      }
    },
    [clearLongPressTimeout],
  );

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: (evt) => {
          const x = evt.nativeEvent.locationX;
          const m = findNearestMomentForX(x);
          const price = findPriceAtX(x);
          setCrosshairX(x);
          setCrosshairPrice(price);
          handleMomentSelectedFromGesture(m);
          scheduleLongPress(x, m);
        },
        onPanResponderMove: (evt) => {
          const x = evt.nativeEvent.locationX;
          const m = findNearestMomentForX(x);
          const price = findPriceAtX(x);
          setCrosshairX(x);
          setCrosshairPrice(price);
          handleMomentSelectedFromGesture(m);
          handleMoveForLongPress(x);
        },
        onPanResponderRelease: () => {
          clearLongPressTimeout();
          setCrosshairX(null);
          setCrosshairPrice(null);
        },
        onPanResponderTerminationRequest: () => true,
        onPanResponderTerminate: () => {
          clearLongPressTimeout();
          setCrosshairX(null);
          setCrosshairPrice(null);
        },
      }),
    [
      findNearestMomentForX,
      findPriceAtX,
      handleMomentSelectedFromGesture,
      scheduleLongPress,
      handleMoveForLongPress,
      clearLongPressTimeout,
    ],
  );

  useEffect(() => {
    return () => {
      clearLongPressTimeout();
    };
  }, [clearLongPressTimeout]);

  const chartAnimatedStyle = useAnimatedStyle(() => ({
    opacity: chartOpacity.value,
    transform: [{ scale: chartScale.value }],
  }));

  // Only show spinner if explicitly loading (not just waiting for layout)
  // Layout happens very quickly, so we can render empty chart and it will fill in
  if (loading) {
    return (
      <View
        style={[styles.chartContainer, { height, backgroundColor: theme.background }]}
        accessible={true}
        accessibilityRole="progressbar"
        accessibilityLabel="Loading chart..."
      >
        <ActivityIndicator size="small" color={theme.priceLineUp} />
      </View>
    );
  }

  // If width is 0, render empty container (layout will happen quickly)
  // This prevents spinner flash while waiting for layout
  if (width === 0) {
    return (
      <View
        style={[styles.chartContainer, { height, backgroundColor: theme.background }]}
        onLayout={handleLayout}
      />
    );
  }

  if (!sortedPoints.length) {
    return (
      <View
        style={[styles.chartContainer, { height, backgroundColor: theme.background }]}
        accessible={true}
        accessibilityRole="status"
        accessibilityLabel="No price data available"
      >
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
          No price data
        </Text>
      </View>
    );
  }

  const priceLineColor = priceChange >= 0 ? theme.priceLineUp : theme.priceLineDown;
  const areaFillColor = priceChange >= 0 ? theme.priceAreaUp : theme.priceAreaDown;

  return (
    <Animated.View style={chartAnimatedStyle}>
      <View>
        <View
          style={[styles.chartContainer, { height, backgroundColor: theme.background }]}
          onLayout={handleLayout}
          {...panResponder.panHandlers}
          accessible={true}
          accessibilityLabel={`Interactive chart for ${sortedMoments.length} key moments`}
        >
          <Svg width={width} height={height}>
            <Defs>
              {/* Price line gradient */}
              <LinearGradient id="priceGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <Stop offset="0%" stopColor={priceLineColor} stopOpacity="0.8" />
                <Stop offset="100%" stopColor={priceLineColor} stopOpacity="1" />
              </LinearGradient>
              {/* Area fill gradient */}
              <LinearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <Stop offset="0%" stopColor={priceLineColor} stopOpacity="0.2" />
                <Stop offset="100%" stopColor={priceLineColor} stopOpacity="0" />
              </LinearGradient>
            </Defs>

            {/* Grid lines */}
            {gridLines.lines.map((line, idx) => (
              <Line
                key={`grid-${idx}`}
                x1={0}
                y1={line.y}
                x2={width}
                y2={line.y}
                stroke={theme.gridLines}
                strokeWidth={1}
                strokeDasharray={idx === 0 || idx === gridLines.lines.length - 1 ? "0" : "4,4"}
              />
            ))}

            {/* Price labels */}
            {gridLines.labels.map((label, idx) => (
              <SvgText
                key={`label-${idx}`}
                x={5}
                y={label.y + 4}
                fontSize="10"
                fill={theme.textSecondary}
                fontWeight="500"
              >
                ${label.price.toFixed(2)}
              </SvgText>
            ))}

            {/* Area fill */}
            {areaPath && (
              <Path
                d={areaPath}
                fill="url(#areaGradient)"
                opacity={0.3}
              />
            )}

            {/* Price line */}
            {pricePath && (
              <Path
                d={pricePath}
                fill="none"
                stroke="url(#priceGradient)"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {/* Crosshair */}
            {crosshairX !== null && (
              <G>
                <Line
                  x1={crosshairX}
                  y1={0}
                  x2={crosshairX}
                  y2={height}
                  stroke={theme.crosshair}
                  strokeWidth={1}
                  strokeDasharray="4,4"
                  opacity={0.6}
                />
                {crosshairPrice !== null && (
                  <G>
                    <Circle
                      cx={crosshairX}
                      cy={toSvgY(crosshairPrice)}
                      r={4}
                      fill={theme.crosshair}
                      opacity={0.8}
                    />
                    <SvgText
                      x={crosshairX + 8}
                      y={toSvgY(crosshairPrice) - 8}
                      fontSize="11"
                      fill={theme.crosshairLabel}
                      fontWeight="600"
                      backgroundColor={theme.background}
                    >
                      ${crosshairPrice.toFixed(2)}
                    </SvgText>
                  </G>
                )}
              </G>
            )}

            {/* Moment dots with enhanced styling */}
            {momentPositions.map(({ moment, x, y }) => {
              const isActive = moment.id === effectiveActiveMomentId;
              const categoryStyle = getCategoryStyle(moment.category);

              return (
                <G key={moment.id}>
                  {/* Glow effect for active moments */}
                  {isActive && (
                    <Circle
                      cx={x}
                      cy={y}
                      r={8}
                      fill={categoryStyle.color}
                      opacity={0.3}
                    />
                  )}
                  {/* Moment dot */}
                  <Circle
                    cx={x}
                    cy={y}
                    r={isActive ? 6 : 5}
                    fill={isActive ? categoryStyle.color : theme.momentDot}
                    stroke={categoryStyle.color}
                    strokeWidth={isActive ? 2.5 : 1.5}
                    opacity={isActive ? 1 : 0.8}
                  />
                  {/* Category icon badge */}
                  <Circle
                    cx={x}
                    cy={y}
                    r={isActive ? 4 : 3}
                    fill="#FFFFFF"
                    opacity={0.9}
                  />
                  <SvgText
                    x={x}
                    y={y + 3}
                    fontSize="8"
                    textAnchor="middle"
                    fill={categoryStyle.color}
                    fontWeight="bold"
                  >
                    {categoryStyle.icon}
                  </SvgText>
                </G>
              );
            })}
          </Svg>
        </View>

        {/* Enhanced moment card */}
        {activeMoment && (
          <Pressable
            style={styles.momentCard}
            onPress={() => setShowDetail(true)}
            accessible={true}
            accessibilityRole="button"
            accessibilityLabel={`View details for ${activeMoment.title}`}
          >
            <RNLinearGradient
              colors={getCategoryStyle(activeMoment.category).gradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.momentCardGradient}
            >
              <View style={styles.momentCardContent}>
                <View style={styles.momentCardHeader}>
                  <Text style={styles.momentCategoryIcon}>
                    {getCategoryStyle(activeMoment.category).icon}
                  </Text>
                  <Text style={styles.momentCategory}>
                    {activeMoment.category}
                  </Text>
                </View>
                <Text style={styles.momentTitle} numberOfLines={1}>
                  {activeMoment.title}
                </Text>
                <Text style={styles.momentSummary} numberOfLines={3}>
                  {activeMoment.quickSummary}
                </Text>
                <Text style={styles.momentAction}>Tap for full story →</Text>
              </View>
            </RNLinearGradient>
          </Pressable>
        )}

        {/* Enhanced modal */}
        <Modal
          visible={showDetail && !!activeMoment}
          animationType="slide"
          transparent
          onRequestClose={() => setShowDetail(false)}
          accessible={true}
          accessibilityViewIsModal={true}
        >
          <View style={styles.modalBackdrop}>
            <View style={[styles.modalContent, { backgroundColor: theme.background }]}>
              {activeMoment && (
                <>
                  <RNLinearGradient
                    colors={getCategoryStyle(activeMoment.category).gradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={styles.modalHeader}
                  >
                    <Text style={styles.modalCategoryIcon}>
                      {getCategoryStyle(activeMoment.category).icon}
                    </Text>
                    <Text style={styles.modalCategory}>
                      {activeMoment.category}
                    </Text>
                  </RNLinearGradient>
                  <Text style={[styles.modalTitle, { color: theme.text }]}>
                    {activeMoment.title}
                  </Text>
                  <Text style={[styles.modalBody, { color: theme.textSecondary }]}>
                    {activeMoment.deepSummary}
                  </Text>
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
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  chartContainer: {
    width: "100%",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 12,
    overflow: "hidden",
  },
  emptyText: {
    fontSize: 14,
    textAlign: "center",
  },
  momentCard: {
    marginTop: 12,
    borderRadius: 16,
    overflow: "hidden",
    shadowColor: "#000000",
    shadowOpacity: 0.1,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 5,
  },
  momentCardGradient: {
    padding: 16,
  },
  momentCardContent: {
    backgroundColor: "rgba(255, 255, 255, 0.95)",
    borderRadius: 12,
    padding: 12,
  },
  momentCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  momentCategoryIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  momentCategory: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.5,
    color: "#2F80ED",
    textTransform: "uppercase",
  },
  momentTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 6,
  },
  momentSummary: {
    fontSize: 13,
    color: "#4B5563",
    lineHeight: 18,
  },
  momentAction: {
    marginTop: 8,
    fontSize: 12,
    fontWeight: "600",
    color: "#2F80ED",
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    maxHeight: "80%",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
  },
  modalCategoryIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  modalCategory: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 12,
    lineHeight: 26,
  },
  modalBody: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 20,
  },
  modalButton: {
    marginTop: 8,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    backgroundColor: "#111827",
  },
  modalButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});

// Export types for compatibility
export type { ChartPoint, MomentCategory, StockMoment } from "./ChartWithMoments";

export default ChartWithMoments;


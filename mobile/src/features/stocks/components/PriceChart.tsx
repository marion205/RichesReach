// src/features/stocks/components/PriceChart.tsx
import React, { useMemo } from 'react';
import { View, StyleSheet, LayoutChangeEvent } from 'react-native';
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

export type ChartPoint = {
  x: number;           // 0..1 normalized x
  price: number;       // demo price
  timeLabel: string;   // human label
};

type Props = {
  symbol: string;
  height?: number;
  onCrosshairMove?: (pt: ChartPoint | null) => void;  // fires as you pan
  onSelectCandle?: (pt: ChartPoint | null) => void;   // fires on release
};

export default function PriceChart({
  symbol,
  height = 240,
  onCrosshairMove,
  onSelectCandle,
}: Props) {
  const w = useSharedValue(0);
  const h = useSharedValue(height);
  const x = useSharedValue(0.5);            // normalized crosshair x (0..1)
  const scale = useSharedValue(1);          // pinch zoom scalar
  const crosshairVisible = useSharedValue(0);

  const onLayout = (e: LayoutChangeEvent) => {
    w.value = e.nativeEvent.layout.width;
    h.value = e.nativeEvent.layout.height;
  };

  // Demo: compute a fake price from x so you still get nice callbacks without data dependency
  const buildPoint = (nx: number): ChartPoint => {
    const price = 200 + Math.sin(nx * Math.PI * 2) * 20 + scale.value * 5;
    const timeLabel = `${Math.round(nx * 100)}% • ${symbol}`;
    return { x: nx, price, timeLabel };
  };

  const notifyMove = (nx: number) => {
    onCrosshairMove?.(buildPoint(nx));
  };

  const notifySelect = (nx: number) => {
    onSelectCandle?.(buildPoint(nx));
  };

  // Pan gesture (worklet) → bounce to JS
  const pan = useMemo(
    () =>
      Gesture.Pan()
        .onBegin(() => {
          'worklet';
          crosshairVisible.value = withTiming(1, { duration: 120 });
        })
        .onChange((e) => {
          'worklet';
          if (w.value <= 0) return;

          const nx = Math.min(1, Math.max(0, x.value + e.changeX / (w.value / scale.value)));

          x.value = nx;

          // ✅ JS side-effect via runOnJS
          if (onCrosshairMove) runOnJS(notifyMove)(nx);
        })
        .onEnd(() => {
          'worklet';
          if (onSelectCandle) runOnJS(notifySelect)(x.value);
          crosshairVisible.value = withTiming(0, { duration: 140 });
        }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [symbol, onCrosshairMove, onSelectCandle]
  );

  // Pinch zoom (worklet only math)
  const pinch = useMemo(
    () =>
      Gesture.Pinch()
        .onBegin(() => {
          'worklet';
        })
        .onUpdate((e) => {
          'worklet';
          const next = Math.min(5, Math.max(1, e.scale));

          scale.value = next;
        })
        .onEnd(() => {
          'worklet';
          // optional snap
          scale.value = withTiming(Math.max(1, Math.min(3, scale.value)), { duration: 200 });
        }),
    []
  );

  const gesture = useMemo(() => Gesture.Simultaneous(pan, pinch), [pan, pinch]);

  const chartStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const crosshairStyle = useAnimatedStyle(() => ({
    opacity: crosshairVisible.value,
    transform: [{ translateX: (x.value * w.value) - 0.5 }], // center 1px line
  }));

  return (
    <GestureDetector gesture={gesture}>
      <View style={[styles.wrap, { height }]} onLayout={onLayout}>
        {/* Chart drawing placeholder — replace with your real renderer if desired */}
        <Animated.View style={[styles.canvas, chartStyle]} />

        {/* Crosshair */}
        <Animated.View style={[styles.crosshair, crosshairStyle]} />
      </View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#0e0f14',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: '#1f2230',
  },
  canvas: {
    ...StyleSheet.absoluteFillObject,
  },
  crosshair: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 1,
    backgroundColor: '#7aa2ff',
  },
});


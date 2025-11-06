import React, { useMemo, useState, useEffect, useRef } from 'react';
import { View, Dimensions, Modal, Text, Pressable, TouchableOpacity, InteractionManager, Platform } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import { useSharedValue, useDerivedValue, withSpring, interpolate, withTiming, runOnJS } from 'react-native-reanimated';

// Conditionally import Skia - only available in development builds, not Expo Go
let SkiaComponents: any = null;
try {
  SkiaComponents = require('@shopify/react-native-skia');
} catch (e) {
  // Skia not available - component will return null
  console.warn('Skia chart library not available');
}

const { Canvas, Path, Skia, Rect, Circle, Line, vec } = SkiaComponents || {};

type PricePoint = { t: number | Date; price: number };
type EventPoint = { t: number | Date; title: string; summary?: string; color?: string };
type WhyDriver = {
  t: number | Date;
  driver: 'news' | 'macro' | 'flow' | 'options' | 'earnings';
  cause: string;
  relevancy: number;
};

type Palette = {
  bg: string;
  grid: string;
  price: string;
  regimeTrend: string;
  regimeChop: string;
  regimeShock: string;
  glass50: string;
  glass80: string;
  eventDot: string;
  text: string;
  card: string;
  moneyGreen: string;
  moneyRed: string;
  breakEven: string;
  whyNews: string;
  whyMacro: string;
  whyFlow: string;
  whyOptions: string;
  whyEarnings: string;
};

type Props = {
  series: PricePoint[];
  events?: EventPoint[];
  drivers?: WhyDriver[];
  costBasis?: number;
  benchmarkData?: PricePoint[];
  showMoneyView?: boolean;
  palette?: Partial<Palette>;
  height?: number;
  margin?: number;
};

const DEFAULTS: Palette = {
  bg: '#FFFFFF',
  grid: 'rgba(40,40,40,0.06)',
  price: '#0F62FE',
  regimeTrend: 'rgba(16,185,129,0.10)',
  regimeChop: 'rgba(234,179,8,0.10)',
  regimeShock: 'rgba(239,68,68,0.10)',
  glass50: 'rgba(15,98,254,0.18)',
  glass80: 'rgba(15,98,254,0.10)',
  eventDot: '#111827',
  text: '#0B0F17',
  card: '#F8FAFC',
  moneyGreen: '#10B981',
  moneyRed: '#EF4444',
  breakEven: '#F59E0B',
  whyNews: '#3B82F6',
  whyMacro: '#EF4444',
  whyFlow: '#10B981',
  whyOptions: '#F59E0B',
  whyEarnings: '#8B5CF6',
};

function toTs(x: number | Date) {
  return typeof x === 'number' ? x : x.getTime();
}

const DRIVER_COLORS = {
  news: '#3B82F6',
  macro: '#EF4444',
  flow: '#10B981',
  options: '#F59E0B',
  earnings: '#8B5CF6',
};

function InnovativeChart({
  series,
  events = [],
  drivers = [],
  costBasis,
  benchmarkData = [],
  showMoneyView = false,
  palette,
  height = 200,
  margin = 16,
}: Props) {
  // Early return if Skia is not available (e.g., in Expo Go)
  if (!SkiaComponents || !Canvas || !Path || !Skia) {
    console.warn('InnovativeChartSkia: Skia library not available, returning null');
    return null;
  }
  
  const P = { ...DEFAULTS, ...palette };
  const screenDimensions = Dimensions.get('window');
  // For now, use full screen width - the parent container should handle padding
  // If chart is in a padded container, that container should set width prop
  const width = screenDimensions.width;
  const [moneyViewVisible, setMoneyViewVisible] = useState(showMoneyView);
  const [showBenchmark, setShowBenchmark] = useState(false);
  const [showAR, setShowAR] = useState(false);
  const [selectedWhy, setSelectedWhy] = useState<{ x: number; driver: string; cause: string; relevancy: number } | null>(null);
  const [ready, setReady] = useState(false);
  const [ev, setEv] = useState<{ x: number; y: number; title: string; summary?: string } | null>(null);
  const optionKeyPressed = useRef(false);

  // CRITICAL: All hooks must be declared before any early returns or conditional logic
  // Declare shared values BEFORE useEffect that uses them
  const scaleX = useSharedValue(1);
  const translateX = useSharedValue(0);
  const savedScale = useSharedValue(1);
  const savedTranslate = useSharedValue(0);
  const isOptionPressed = useSharedValue(false); // Track Option/Alt key state
  const showBenchmarkShared = useSharedValue(showBenchmark); // For benchmarkOpacity useDerivedValue

  // Gate initial render - defer heavy chart computation until after first frame
  useEffect(() => {
    // Add a small delay to prevent blocking the UI thread
    const timeout = setTimeout(() => {
      const task = InteractionManager.runAfterInteractions(() => {
        setReady(true);
      });
      return () => task?.cancel?.();
    }, 100);
    return () => {
      clearTimeout(timeout);
    };
  }, []);

  // Update showBenchmarkShared when showBenchmark state changes
  useEffect(() => {
    showBenchmarkShared.value = showBenchmark;
  }, [showBenchmark]);

  // Handle modifier keys for web/desktop platforms and iOS Simulator
  useEffect(() => {
    // On web, we can detect modifier keys via keyboard events
    // On iOS Simulator, Option+drag is handled differently
    const handleKeyDown = (e: any) => {
      // Detect Option (Mac) or Alt (Windows/Linux) key
      if (e.altKey || e.key === 'Alt' || e.key === 'Meta' || e.keyCode === 18) {
        isOptionPressed.value = true;
        optionKeyPressed.current = true;
        if (__DEV__) {
          console.log('🔑 Option/Alt key pressed');
        }
      }
    };

    const handleKeyUp = (e: any) => {
      if (e.key === 'Alt' || e.key === 'Meta' || e.keyCode === 18 || !e.altKey) {
        isOptionPressed.value = false;
        optionKeyPressed.current = false;
        if (__DEV__) {
          console.log('🔑 Option/Alt key released');
        }
      }
    };

    // Also handle mouse events with modifier keys (for web)
    const handleMouseDown = (e: any) => {
      if (e.altKey) {
        isOptionPressed.value = true;
        optionKeyPressed.current = true;
        if (__DEV__) {
          console.log('🖱️ Mouse down with Option/Alt');
        }
      }
    };

    const handleMouseUp = () => {
      // Only reset if no longer pressed
      if (!optionKeyPressed.current) {
        isOptionPressed.value = false;
      }
    };

    // For web platforms
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyDown);
      window.addEventListener('keyup', handleKeyUp);
      window.addEventListener('mousedown', handleMouseDown);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('keydown', handleKeyDown);
        window.removeEventListener('keyup', handleKeyUp);
        window.removeEventListener('mousedown', handleMouseDown);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }

    // For iOS Simulator, we need to detect Option+drag differently
    // The gesture handler should detect this, but we can also try to detect it
    // via touch events with a modifier check
    if (Platform.OS === 'ios' && __DEV__) {
      console.log('📱 iOS detected - Option+drag may work differently');
      console.log('💡 Try: Hold Option key, then drag on the chart');
    }
  }, []);

  const sorted = useMemo(() => [...series].sort((a, b) => toTs(a.t) - toTs(b.t)), [series]);
  const times = useMemo(() => sorted.map(p => toTs(p.t)), [sorted]);
  const prices = useMemo(() => sorted.map(p => p.price), [sorted]);
  const minT = useMemo(() => Math.min(...times), [times]);
  const maxT = useMemo(() => Math.max(...times), [times]);
  const minP = useMemo(() => {
    const all = [...prices];
    if (costBasis) all.push(costBasis);
    return Math.min(...all);
  }, [prices, costBasis]);
  const maxP = useMemo(() => {
    const all = [...prices];
    if (costBasis) all.push(costBasis);
    return Math.max(...all);
  }, [prices, costBasis]);

  const w = width - margin * 2;
  const h = height - margin * 2;

  const pinchGesture = Gesture.Pinch()
    .enabled(true)
    .shouldCancelWhenOutside(true)
    .onUpdate((e) => {
      'worklet';
      scaleX.value = savedScale.value * e.scale;
    })
    .onEnd(() => {
      'worklet';
      savedScale.value = scaleX.value;
      const targetScale = Math.max(0.5, Math.min(3, scaleX.value));
      scaleX.value = withSpring(targetScale);
      savedScale.value = scaleX.value;
    });

  // Pan gesture - detect "slow/precise" drags as Option+drag
  // On iOS Simulator, Option+drag is often slower and more deliberate
  // We'll use velocity to detect this pattern
  const panGesture = Gesture.Pan()
    .minPointers(1)
    .maxPointers(1)
    .enabled(true)
    .activeOffsetX([-40, 40]) // Require significant horizontal movement to activate (navigation activates at 10px, so this won't conflict)
    .failOffsetY([-2, 2]) // Fail almost immediately on vertical movement (allows ScrollView to work)
    .shouldCancelWhenOutside(true)
    .onStart((e) => {
      'worklet';
      runOnJS(() => {
        console.log('👆 Pan START', { x: e.x, y: e.y, platform: Platform.OS });
      })();
    })
    .onBegin((e) => {
      'worklet';
      // Track gesture start time for velocity calculation
      runOnJS(() => {
        console.log('👆 Pan BEGAN', { x: e.x, y: e.y, platform: Platform.OS, state: 'BEGAN' });
      })();
    })
    .onUpdate((e) => {
      'worklet';
      // Check if Option/Alt key is pressed (works on web)
      const useOptionSensitivity = isOptionPressed.value;
      
      // For iOS Simulator: detect slow/precise drags as Option+drag
      // Option+drag is typically slower and more deliberate
      const velocity = Math.abs(e.velocityX) + Math.abs(e.velocityY);
      const totalTranslation = Math.abs(e.translationX) + Math.abs(e.translationY);
      const isSlowDrag = velocity < 800; // Slow drag = more precise
      const isPreciseDrag = totalTranslation < 300 && isSlowDrag;
      
      // Determine sensitivity multiplier
      let sensitivity = 1.0;
      if (useOptionSensitivity) {
        // Option key detected via keyboard (web/desktop)
        sensitivity = 5.0; // Very high sensitivity for Option drag
      } else if (isPreciseDrag && Platform.OS === 'ios') {
        // Slow, precise drag on iOS - likely Option key held
        sensitivity = 4.0; // High sensitivity
      }
      
      // Apply translation with sensitivity
      const deltaX = (e.translationX * sensitivity) / scaleX.value;
      translateX.value = savedTranslate.value + deltaX;
      
      // Debug logging - log updates (limit frequency to avoid spam)
      if (Math.abs(e.translationX) % 10 < 1 || sensitivity > 1.0) {
        runOnJS(() => {
          console.log('🎯 Pan UPDATE', { 
            sensitivity: sensitivity.toFixed(2), 
            translationX: e.translationX.toFixed(2),
            deltaX: deltaX.toFixed(2),
            velocity: velocity.toFixed(2),
            totalTranslation: totalTranslation.toFixed(2),
            optionPressed: useOptionSensitivity,
            isPreciseDrag,
            isSlowDrag,
            platform: Platform.OS,
            translateXValue: translateX.value.toFixed(2),
            savedTranslate: savedTranslate.value.toFixed(2)
          });
        })();
      }
    })
    .onEnd(() => {
      'worklet';
      savedTranslate.value = translateX.value;
      const targetTranslate = translateX.value;
      translateX.value = withSpring(targetTranslate);
      savedTranslate.value = translateX.value;
    });

  // Combine gestures: pan and pinch can work simultaneously
  // Note: Tap gesture is handled separately to avoid composition errors
  // For now, we'll focus on pan/pinch gestures - tap can be added back later if needed
  // Ensure gestures only work within chart bounds
  // Use Simultaneous to allow both gestures, but pan will fail on vertical movement
  // The pan gesture requires more horizontal movement (30px) than navigation (10px) to avoid conflicts
  const allGestures = Gesture.Simultaneous(
    pinchGesture.shouldCancelWhenOutside(true),
    panGesture.shouldCancelWhenOutside(true)
  );

  const timeSpan = maxT - minT;
  const baseStep = sorted.length > 0 ? w / sorted.length : 0;

  // CRITICAL: scaledData must be declared unconditionally - before any early returns
  const scaledData = useDerivedValue(() => {
    if (!sorted || sorted.length === 0) return [];
    try {
      const densityThreshold = 0.3;
      let cumulativeX = margin;
      const scaled: { t: number; price: number; x: number }[] = [];
      
      const currentScale = scaleX?.value ?? 1;
      const currentTranslate = translateX?.value ?? 0;
      
      // Validate inputs
      if (!isFinite(currentScale) || !isFinite(currentTranslate) || currentScale <= 0) {
        return [];
      }
      
      for (let i = 0; i < sorted.length; i++) {
        if (!sorted[i] || typeof sorted[i].price !== 'number' || isNaN(sorted[i].price)) continue;
        const t = toTs(sorted[i].t);
        if (!isFinite(t)) continue;
        
        const prevT = i > 0 ? toTs(sorted[i - 1].t) : t;
        const deltaT = i > 0 && timeSpan > 0 ? (t - prevT) / timeSpan : 0;
        
        if (!isFinite(deltaT)) continue;
        
        const stretch = deltaT > 0 && isFinite(deltaT) ? interpolate(
          Math.min(deltaT, 1),
          [0, densityThreshold, 1],
          [0.5, 1, 2]
        ) : 1;
        
        if (!isFinite(stretch)) continue;
        
        const segmentWidth = (baseStep * currentScale * stretch) || baseStep;
        if (!isFinite(segmentWidth) || segmentWidth <= 0) continue;
        
        const xPos = cumulativeX + currentTranslate;
        if (!isFinite(xPos)) continue;
        
        scaled.push({
          t,
          price: sorted[i].price,
          x: xPos,
        });
        cumulativeX += segmentWidth;
      }
      
      return scaled;
    } catch (e) {
      console.warn('Chart scaledData error:', e);
      return [];
    }
  });

  const xOf = useMemo(() => {
    return (t: number, useScaled = false) => {
      if (maxT === minT) return margin;
      // Don't access scaledData.value in useMemo - it's a worklet value
      // Always use simple calculation for now
      return margin + ((t - minT) / (maxT - minT || 1)) * w;
    };
  }, [maxT, minT, margin, w]);

  const yOf = (p: number) => {
    if (!isFinite(p) || isNaN(p)) return margin;
    if (maxP === minP || !isFinite(maxP) || !isFinite(minP)) return height - margin;
    const ratio = (p - minP) / (maxP - minP);
    if (!isFinite(ratio) || isNaN(ratio)) return margin;
    return margin + (1 - ratio) * h;
  };

  // Convert pricePath to a memoized path that can be used in Canvas
  const pricePath = useMemo(() => {
    if (sorted.length === 0) return Skia.Path.Make();
    try {
      const path = Skia.Path.Make();
      const maxX = width - margin;
      // Use simple linear scaling for initial render - animated scaling will be handled separately
      for (let i = 0; i < sorted.length; i++) {
        const point = sorted[i];
        if (!point || typeof point.price !== 'number' || isNaN(point.price)) continue;
        const t = toTs(point.t);
        let x = margin + ((t - minT) / (maxT - minT || 1)) * w;
        // Clamp x to chart bounds
        x = Math.max(margin, Math.min(x, maxX));
        const y = yOf(point.price);
        // Clamp y to chart bounds
        const yClamped = Math.max(margin, Math.min(y, height - margin));
        if (isNaN(x) || isNaN(yClamped) || !isFinite(x) || !isFinite(yClamped)) continue;
        if (i === 0) {
          path.moveTo(x, yClamped);
        } else {
          path.lineTo(x, yClamped);
        }
      }
      return path;
    } catch (e) {
      console.warn('Chart pricePath error:', e);
      return Skia.Path.Make();
    }
  }, [sorted, minT, maxT, minP, maxP, margin, w, h, height, width]);

  const moneyPath = useMemo(() => {
    if (!moneyViewVisible || !costBasis || sorted.length === 0) return Skia.Path.Make();
    const path = Skia.Path.Make();
    try {
      const yBasis = yOf(costBasis);
      const x0 = margin;
      path.moveTo(x0, height - margin);
      for (let i = 0; i < sorted.length; i++) {
        const point = sorted[i];
        if (!point || typeof point.price !== 'number' || isNaN(point.price)) continue;
        const t = toTs(point.t);
        const x = margin + ((t - minT) / (maxT - minT || 1)) * w;
        const yPrice = yOf(point.price);
        if (isNaN(x) || isNaN(yPrice) || !isFinite(x) || !isFinite(yPrice)) continue;
        path.lineTo(x, Math.max(yPrice, yBasis));
      }
      const xLast = margin + w;
      path.lineTo(xLast, height - margin);
      path.close();
    } catch (e) {
      console.warn('Chart moneyPath error:', e);
    }
    return path;
  }, [sorted, costBasis, moneyViewVisible, minT, maxT, minP, maxP, height, margin, w, h]);

  const breakEvenPath = useMemo(() => {
    if (!moneyViewVisible || !costBasis) return Skia.Path.Make();
    const path = Skia.Path.Make();
    const bePrice = costBasis * 1.05;
    const yBe = yOf(bePrice);
    path.moveTo(margin, yBe);
    path.lineTo(width - margin, yBe);
    return path;
  }, [costBasis, moneyViewVisible, minP, maxP, height, margin, width]);

  const alignedBenchmark = useMemo(() => {
    if (benchmarkData.length === 0) return [];
    const interpPrice = (t: number) => {
      const idx = benchmarkData.findIndex(b => toTs(b.t) <= t);
      if (idx === -1) return benchmarkData[benchmarkData.length - 1]?.price ?? 0;
      const b1 = benchmarkData[idx];
      const b2 = benchmarkData[idx + 1];
      if (!b2) return b1.price;
      const t1 = toTs(b1.t);
      const t2 = toTs(b2.t);
      return b1.price + (b2.price - b1.price) * ((t - t1) / (t2 - t1));
    };
    return sorted.map(p => ({
      t: toTs(p.t),
      price: interpPrice(toTs(p.t)),
    }));
  }, [benchmarkData, sorted]);

  // Now useDerivedValue can properly track the shared value
  const benchmarkOpacity = useDerivedValue(() => {
    return showBenchmarkShared.value ? 0.1 : 0;
  });

  const benchmarkPath = useMemo(() => {
    if (!showBenchmark || alignedBenchmark.length === 0 || sorted.length === 0) {
      return Skia.Path.Make();
    }
    const path = Skia.Path.Make();
    try {
      // Limit iterations to prevent blocking - use every Nth point for large datasets
      const step = sorted.length > 100 ? Math.ceil(sorted.length / 100) : 1;
      for (let i = 0; i < sorted.length && i < alignedBenchmark.length; i += step) {
        const point = sorted[i];
        const benchmark = alignedBenchmark[i];
        if (!point || !benchmark || typeof benchmark.price !== 'number' || isNaN(benchmark.price)) continue;
        const t = toTs(point.t);
        const x = margin + ((t - minT) / (maxT - minT || 1)) * w;
        const y = yOf(benchmark.price);
        if (isNaN(x) || isNaN(y) || !isFinite(x) || !isFinite(y)) continue;
        if (i === 0) {
          path.moveTo(x, y);
        } else {
          path.lineTo(x, y);
        }
      }
    } catch (e) {
      console.warn('Chart benchmarkPath error:', e);
    }
    return path;
  }, [showBenchmark, alignedBenchmark, sorted, minT, maxT, minP, maxP, margin, w, yOf]);

  const regimes = useMemo(() => {
    if (prices.length < 10) return [];
    const rets: number[] = [];
    for (let i = 1; i < prices.length; i++) rets.push(Math.log(prices[i] / prices[i - 1]));
    const volWin = 14;
    const slopeWin = 10;
    const R: { startIdx: number; endIdx: number; type: 'trend' | 'chop' | 'shock' }[] = [];
    let curType: 'trend' | 'chop' | 'shock' | null = null;
    let segStart = 0;
    for (let i = 1; i < prices.length; i++) {
      const j0 = Math.max(0, i - volWin);
      const slice = rets.slice(j0, i);
      const mean = slice.reduce((a, b) => a + b, 0) / Math.max(1, slice.length);
      const vol = Math.sqrt(slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / Math.max(1, slice.length));
      const k0 = Math.max(0, i - slopeWin);
      const px = prices.slice(k0, i + 1);
      const m = px.length > 1 ? (px[px.length - 1] - px[0]) / (px.length - 1) : 0;
      let t: 'trend' | 'chop' | 'shock';
      if (vol > 2 * Math.max(1e-6, mean < 0 ? -mean : mean) && vol > 0.03) t = 'shock';
      else if (Math.abs(m) > 0.5 * (maxP - minP) / prices.length) t = 'trend';
      else t = 'chop';
      if (curType === null) {
        curType = t;
        segStart = i - 1;
      } else if (t !== curType) {
        R.push({ startIdx: segStart, endIdx: i - 1, type: curType });
        curType = t;
        segStart = i - 1;
      }
    }
    if (curType) R.push({ startIdx: segStart, endIdx: prices.length - 1, type: curType });
    return R;
  }, [prices, minP, maxP]);

  const dtMedian = useMemo(() => {
    if (times.length < 2) return 24 * 3600 * 1000;
    const ds: number[] = [];
    for (let i = 1; i < times.length; i++) ds.push(times[i] - times[i - 1]);
    ds.sort((a, b) => a - b);
    return ds[Math.floor(ds.length / 2)] || 24 * 3600 * 1000;
  }, [times]);

  const glass = useMemo(() => {
    try {
      if (prices.length < 10) return { p80: Skia.Path.Make(), p50: Skia.Path.Make() };
      const rets: number[] = [];
      for (let i = 1; i < prices.length; i++) {
        if (prices[i] > 0 && prices[i-1] > 0) {
          const logRet = Math.log(prices[i] / prices[i - 1]);
          if (isFinite(logRet)) rets.push(logRet);
        }
      }
      if (rets.length === 0) return { p80: Skia.Path.Make(), p50: Skia.Path.Make() };
      const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
      const sd = Math.sqrt(rets.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / Math.max(1, rets.length));
      if (!isFinite(mean) || !isFinite(sd) || sd <= 0) return { p80: Skia.Path.Make(), p50: Skia.Path.Make() };
      const steps = 12;
      const lastT = times[times.length - 1];
      const lastP = prices[prices.length - 1];
      if (!isFinite(lastT) || !isFinite(lastP) || lastP <= 0) return { p80: Skia.Path.Make(), p50: Skia.Path.Make() };
      const z80 = 1.2815515655446004;
      const z50 = 0.6744897501960817;
      const makeBand = (z: number, bandName: string) => {
        const upper: { t: number; p: number }[] = [];
        const lower: { t: number; p: number }[] = [];
        for (let k = 1; k <= steps; k++) {
          const t = lastT + dtMedian * k;
          const mu = mean * k;
          const s = Math.sqrt(k) * sd;
          const up = lastP * Math.exp(mu + z * s);
          const lo = lastP * Math.exp(mu - z * s);
          if (isFinite(t) && isFinite(up) && isFinite(lo) && up > 0 && lo > 0) {
            upper.push({ t, p: up });
            lower.push({ t, p: lo });
          }
        }
        const path = Skia.Path.Make();
        if (upper.length === 0) {
          console.log(`Chart glass ${z === z80 ? 'p80' : 'p50'}: No upper bounds`);
          return path;
        }
        
        // Start at the last data point (end of price line)
        const lastX = xOf(lastT);
        const lastY = yOf(lastP);
        
        // Project future times into visible chart space (extend 20% to the right)
        const futureExtent = w * 0.2; // Use 20% of chart width for future predictions
        const totalFutureTime = dtMedian * steps;
        
        if (isFinite(lastX) && isFinite(lastY)) {
          // Start path at last data point
          path.moveTo(lastX, lastY);
          
          // Draw upper band - map future times to x positions extending from lastX
          for (let i = 0; i < upper.length; i++) {
            const timeOffset = upper[i].t - lastT;
            const progress = Math.min(timeOffset / totalFutureTime, 1); // 0 to 1
            const x = Math.min(lastX + (progress * futureExtent), width - margin);
            const y = yOf(upper[i].p);
            const yClamped = Math.max(margin, Math.min(y, height - margin));
            if (isFinite(x) && isFinite(yClamped) && x >= margin) {
              path.lineTo(x, yClamped);
            }
          }
          
          // Draw lower band going backwards
          for (let i = lower.length - 1; i >= 0; i--) {
            const timeOffset = lower[i].t - lastT;
            const progress = Math.min(timeOffset / totalFutureTime, 1);
            const x = Math.min(lastX + (progress * futureExtent), width - margin);
            const y = yOf(lower[i].p);
            const yClamped = Math.max(margin, Math.min(y, height - margin));
            if (isFinite(x) && isFinite(yClamped) && x >= margin) {
              path.lineTo(x, yClamped);
            }
          }
          
          path.close();
          console.log(`Chart glass ${z === z80 ? 'p80' : 'p50'}: Created band from (${lastX}, ${lastY}) with ${upper.length} points`);
        } else {
          console.log(`Chart glass ${z === z80 ? 'p80' : 'p50'}: Invalid start`, { lastX, lastY });
        }
        return path;
      };
      return { p80: makeBand(z80, 'p80'), p50: makeBand(z50, 'p50') };
    } catch (e) {
      console.warn('Chart glass error:', e);
      return { p80: Skia.Path.Make(), p50: Skia.Path.Make() };
    }
  }, [prices, times, dtMedian, minT, maxT, minP, maxP, xOf, yOf]);

  const eventPoints = useMemo(() => {
    return events.map(e => {
      const t = toTs(e.t);
      const idx = times.findIndex(x => x >= t);
      const baseIdx = idx >= 0 ? idx : times.length - 1;
      const px = prices[Math.max(0, Math.min(prices.length - 1, baseIdx))] ?? prices[prices.length - 1] ?? 0;
      const x = margin + ((t - minT) / (maxT - minT || 1)) * w;
      return { t, x, y: yOf(px), title: e.title, summary: e.summary, color: e.color || P.eventDot };
    });
  }, [events, times, prices, P.eventDot, margin, minT, maxT, w, minP, maxP, height, h]);

  const whyLines = useMemo(() => {
    return drivers.map(d => {
      const t = toTs(d.t);
      const x = margin + ((t - minT) / (maxT - minT || 1)) * w;
      return {
        x,
        driver: d.driver,
        cause: d.cause,
        relevancy: d.relevancy,
        color: DRIVER_COLORS[d.driver] || '#6B7280',
      };
    });
  }, [drivers, margin, minT, maxT, w]);

  const tapGesture = Gesture.Tap()
    .maxDuration(250) // Quick taps only
    .onEnd((e) => {
    'worklet';
    const tapX = e.x;
    const tapY = e.y;
    
    // Access memoized values directly (they're regular JS values now, not worklet values)
    const hitLine = whyLines.find((line: any) => Math.abs(line.x - tapX) < 8);
    if (hitLine) {
      runOnJS(handleWhyTap)(hitLine.x, hitLine.driver, hitLine.cause, hitLine.relevancy);
      return;
    }
    
    const hitEvent = eventPoints.find((ev: any) => {
      const dx = ev.x - tapX;
      const dy = ev.y - tapY;
      return Math.sqrt(dx * dx + dy * dy) < 10;
    });
    if (hitEvent) {
      runOnJS(setEv)({ x: hitEvent.x, y: hitEvent.y, title: hitEvent.title, summary: hitEvent.summary });
    }
  });

  const handleWhyTap = (x: number, driver: string, cause: string, relevancy: number) => {
    setSelectedWhy({ x, driver, cause, relevancy });
  };

  // Pre-compute regime positions to avoid accessing .value during render
  const regimePositions = useMemo(() => {
    return regimes.map((r) => {
      // Use fallback calculation based on base positions
      // The actual scaled positions will be applied via animated paths if needed
      const x1 = margin + ((times[r.startIdx] - minT) / (maxT - minT || 1)) * w;
      const x2 = margin + ((times[r.endIdx] - minT) / (maxT - minT || 1)) * w;
      return {
        x1,
        x2,
        type: r.type,
      };
    });
  }, [regimes, times, minT, maxT, margin, w]);

  // CRITICAL: Move useDerivedValue to top level - hooks must be called unconditionally
  // This hook creates an animated path from scaledData
  // Must be declared AFTER all useMemo hooks it depends on (pricePath, scaledData)
  // but BEFORE any early returns
  // Note: useDerivedValue automatically tracks dependencies, no array needed
  const animatedPricePath = useDerivedValue(() => {
    // Create path from scaledData if available, otherwise use static pricePath
    if (!scaledData.value || scaledData.value.length === 0) {
      return pricePath;
    }
    
    const path = Skia.Path.Make();
    const scaled = scaledData.value;
    
    if (scaled.length > 0 && scaled[0] && typeof scaled[0].price === 'number' && !isNaN(scaled[0].price)) {
      const x0 = margin + (scaled[0].x ?? 0);
      const y0 = yOf(scaled[0].price);
      if (isNaN(x0) || isNaN(y0) || !isFinite(x0) || !isFinite(y0)) {
        return pricePath;
      }
      path.moveTo(x0, y0);
      for (let i = 1; i < scaled.length; i++) {
        if (!scaled[i] || typeof scaled[i].price !== 'number' || isNaN(scaled[i].price)) continue;
        const x = margin + (scaled[i].x ?? 0);
        const y = yOf(scaled[i].price);
        if (isNaN(x) || isNaN(y) || !isFinite(x) || !isFinite(y)) continue;
        path.lineTo(x, y);
      }
    }
    return path;
  });

  if (sorted.length === 0) {
    return (
      <View style={{ width, height, backgroundColor: P.bg, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: P.text, opacity: 0.5 }}>No data</Text>
      </View>
    );
  }

  // Show skeleton until ready (defer heavy computation)
  if (!ready) {
    return (
      <View style={{ width, height, backgroundColor: P.bg, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: P.text, opacity: 0.3, fontSize: 12 }}>Loading chart...</Text>
      </View>
    );
  }

  // Render full chart with regime bands
  // Attach gestures directly to the container
  return (
    <>
      <View 
        style={{ 
          width: Math.max(0, Math.min(width, screenDimensions.width)), 
          height: Math.max(0, Math.min(height, screenDimensions.height)), 
          backgroundColor: P.bg, 
          overflow: 'hidden',
          maxWidth: screenDimensions.width,
          maxHeight: screenDimensions.height,
        }}
        collapsable={false}
      >
      <GestureDetector gesture={allGestures}>
        <View 
          style={{ 
            width: '100%',
            height: '100%',
          }}
          collapsable={false}
        >
        {/* Canvas rendered inside the gesture-detecting container */}
        {/* Canvas doesn't block touches - gestures work on the parent View */}
        <Canvas style={{ width, height }} pointerEvents="none">
          <Rect x={0} y={0} width={width} height={height} color={P.bg} />
          
          {/* Render regime bands as background rectangles */}
          {regimePositions.map((regime, idx) => {
            const color = regime.type === 'trend' 
              ? P.regimeTrend 
              : regime.type === 'chop' 
              ? P.regimeChop 
              : P.regimeShock;
            // Clamp positions to chart bounds
            const x1 = Math.max(margin, Math.min(regime.x1, width - margin));
            const x2 = Math.max(margin, Math.min(regime.x2, width - margin));
            const bandWidth = Math.max(0, x2 - x1);
            if (bandWidth <= 0) return null;
            return (
              <Rect
                key={`regime-${idx}`}
                x={x1}
                y={margin}
                width={bandWidth}
                height={h}
                color={color}
              />
            );
          })}
          
          {/* Confidence glass (p80 and p50 bands) - future prediction bands */}
          <Path
            path={glass.p80}
            color={P.glass80}
            style="fill"
          />
          <Path
            path={glass.p50}
            color={P.glass50}
            style="fill"
          />
          
          {/* Price line path - use animated path that reacts to gestures */}
          <Path
            path={animatedPricePath}
            color={P.price}
            style="stroke"
            strokeWidth={2}
          />
          
          {/* Benchmark line (if enabled) */}
          {showBenchmark && benchmarkData.length > 0 && (
            <Path
              path={benchmarkPath}
              color={P.bench || P.text}
              style="stroke"
              strokeWidth={1}
              opacity={0.5}
            />
          )}
          
          {/* Event markers */}
          {events.map((event, idx) => {
            let x = xOf(toTs(event.t));
            // Clamp x to chart bounds
            x = Math.max(margin, Math.min(x, width - margin));
            let y = yOf(sorted.find(p => toTs(p.t) === toTs(event.t))?.price || minP);
            // Clamp y to chart bounds
            y = Math.max(margin, Math.min(y, height - margin));
            return (
              <Circle key={`event-${idx}`} cx={x} cy={y} r={6} color={event.color || P.eventDot} />
            );
          })}
          
          {/* Driver lines */}
          {drivers.map((driver, idx) => {
            let x = xOf(toTs(driver.t));
            // Clamp x to chart bounds
            x = Math.max(margin, Math.min(x, width - margin));
            const color = DRIVER_COLORS[driver.driver] || P.text;
            return (
              <Line
                key={`driver-${idx}`}
                p1={vec(x, margin)}
                p2={vec(x, height - margin)}
                color={color}
                strokeWidth={2}
              />
            );
          })}
          
          {/* Cost basis line (if provided) */}
          {costBasis && (
            <Line
              p1={vec(margin, yOf(costBasis))}
              p2={vec(width - margin, yOf(costBasis))}
              color={P.breakEven}
              strokeWidth={1}
            />
          )}
        </Canvas>
        
        {/* Debug touch logging - separate View that doesn't block */}
        {__DEV__ && (
          <View 
            style={{ 
              position: 'absolute',
              left: 0,
              top: 0,
              width, 
              height, 
              backgroundColor: 'rgba(255,0,0,0.05)', // Very faint red tint
              pointerEvents: 'none', // Don't block touches
            }} 
          />
        )}
        </View>
      </GestureDetector>
      </View>

      {/* Buttons and labels OUTSIDE GestureDetector so they can be clicked */}
      <View 
        style={{ 
          position: 'absolute', 
          bottom: 10, 
          right: margin + 30, 
          flexDirection: 'column', 
          gap: 4, 
          alignItems: 'flex-end',
          zIndex: 1000,
        }}
        pointerEvents="auto"
        collapsable={false}
      >
        {costBasis && (
          <TouchableOpacity
            onPress={() => setMoneyViewVisible(!moneyViewVisible)}
            style={{
              backgroundColor: 'rgba(0,0,0,0.6)',
              paddingHorizontal: 10,
              paddingVertical: 5,
              borderRadius: 12,
            }}
          >
            <Text style={{ color: '#FFFFFF', fontSize: 11, fontWeight: '600' }}>
              {moneyViewVisible ? 'Price' : 'Money'}
            </Text>
          </TouchableOpacity>
        )}
        {benchmarkData.length > 0 && (
          <TouchableOpacity
            onPress={() => {
              setShowBenchmark(!showBenchmark);
            }}
            style={{
              backgroundColor: showBenchmark ? 'rgba(59,130,246,0.8)' : 'rgba(0,0,0,0.6)',
              paddingHorizontal: 10,
              paddingVertical: 5,
              borderRadius: 12,
            }}
            activeOpacity={0.8}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={{ color: '#FFFFFF', fontSize: 11, fontWeight: '600' }}>
              {showBenchmark ? 'Hide' : 'Bench'}
            </Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={() => {
            setShowAR(true);
          }}
          style={{
            backgroundColor: 'rgba(16,185,129,0.8)',
            paddingHorizontal: 10,
            paddingVertical: 5,
            borderRadius: 12,
          }}
          activeOpacity={0.8}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={{ color: '#FFFFFF', fontSize: 11, fontWeight: '600' }}>
            AR
          </Text>
        </TouchableOpacity>
      </View>
      
      <View 
        style={{ 
          position: 'absolute', 
          bottom: 10, 
          left: 10,
          zIndex: 1000,
        }}
        pointerEvents="none"
      >
        <Text style={{ color: P.text, fontSize: 12, opacity: 0.5 }}>
          {regimes.length > 0 ? `${regimes.length} regime${regimes.length > 1 ? 's' : ''} detected` : 'No regimes'}
        </Text>
      </View>

      {/* Modals rendered outside GestureDetector to avoid JSX parsing issues */}
      <Modal visible={!!ev} transparent onRequestClose={() => setEv(null)}>
        <Pressable style={{ flex: 1 }} onPress={() => setEv(null)}>
          {ev && (
            <View
              style={{
              position: 'absolute',
              left: Math.min(Math.max(ev.x - 120, 8), width - 240),
              top: Math.max(ev.y - 120, 24),
              width: 240,
              borderRadius: 12,
              backgroundColor: P.card,
              padding: 12,
              gap: 6,
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.25,
              shadowRadius: 8,
              elevation: 5,
            }}
          >
              <Text style={{ fontWeight: '600', fontSize: 15, color: P.text }}>{ev.title}</Text>
              {!!ev.summary && <Text style={{ fontSize: 13, color: P.text, opacity: 0.7 }}>{ev.summary}</Text>}
            </View>
          )}
        </Pressable>
      </Modal>

      <Modal visible={!!selectedWhy} transparent onRequestClose={() => setSelectedWhy(null)}>
        {selectedWhy && (
          <Pressable style={{ flex: 1 }} onPress={() => setSelectedWhy(null)}>
            <View
              style={{
              position: 'absolute',
              left: Math.min(Math.max(selectedWhy.x - 120, 8), width - 240),
              top: height / 2 - 40,
              width: 240,
              borderRadius: 12,
              backgroundColor: 'rgba(0,0,0,0.9)',
              padding: 12,
              gap: 6,
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.25,
              shadowRadius: 8,
              elevation: 5,
            }}
          >
              <Text style={{ color: '#FFFFFF', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' }}>
                {selectedWhy.driver}
              </Text>
              <Text style={{ color: '#FFFFFF', fontSize: 13 }}>{selectedWhy.cause}</Text>
              <Text style={{ color: '#FCD34D', fontSize: 11 }}>Relevancy: {selectedWhy.relevancy}%</Text>
            </View>
          </Pressable>
        )}
      </Modal>

      <Modal visible={showAR} animationType="slide" presentationStyle="fullScreen" onRequestClose={() => setShowAR(false)}>
        <View style={{ flex: 1, backgroundColor: '#000000' }}>
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
            <Text style={{ color: '#FFFFFF', fontSize: 24, fontWeight: '700', marginBottom: 20, textAlign: 'center' }}>
              AR Walk Prototype
            </Text>
            <Text style={{ color: '#9CA3AF', fontSize: 16, marginBottom: 30, textAlign: 'center', lineHeight: 24 }}>
              Place your portfolio path on your desk as a 3D walkable line.{'\n\n'}
              Events float as anchors where they happened.{'\n\n'}
              Step along 12 months to explore your journey.
            </Text>
            <View style={{ width: '100%', height: 300, backgroundColor: '#1F2937', borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: 30 }}>
              <Text style={{ color: '#6B7280', fontSize: 14 }}>AR Preview</Text>
              <Text style={{ color: '#4B5563', fontSize: 12, marginTop: 8 }}>
                Requires ARKit (iOS) or ARCore (Android)
              </Text>
              <Text style={{ color: '#4B5563', fontSize: 12, marginTop: 4 }}>
                Full AR implementation coming soon
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => {
                setShowAR(false);
              }}
              style={{
                backgroundColor: '#10B981',
                paddingHorizontal: 32,
                paddingVertical: 14,
                borderRadius: 12,
              }}
              activeOpacity={0.8}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 16, fontWeight: '600' }}>Exit AR Preview</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </>
  );
}

// Explicit default export to ensure Metro bundler recognizes it
export default InnovativeChart;

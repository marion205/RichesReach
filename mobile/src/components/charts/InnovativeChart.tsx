import React, { useEffect, useState, useMemo } from 'react';
import { InteractionManager, View, ActivityIndicator, Dimensions } from 'react-native';
// Direct import for now - we'll add lazy loading back once we verify the chart works
import SkiaChart from './InnovativeChartSkia';

type PricePoint = { t: number | Date; price: number };
type EventPoint = { t: number | Date; title: string; summary?: string; color?: string };
type WhyDriver = {
  t: number | Date;
  driver: 'news' | 'macro' | 'flow' | 'options' | 'earnings';
  cause: string;
  relevancy: number;
};

type Props = {
  series: PricePoint[];
  events?: EventPoint[];
  drivers?: WhyDriver[];
  costBasis?: number;
  benchmarkData?: PricePoint[];
  showMoneyView?: boolean;
  palette?: any;
  height?: number;
  margin?: number;
};

function Skeleton({ width, height }: { width: number; height: number }) {
  return (
    <View style={{
      width,
      height,
      borderRadius: 12,
      backgroundColor: 'rgba(0,0,0,0.06)',
      justifyContent: 'center',
      alignItems: 'center',
    }}>
      <ActivityIndicator size="small" color="#8E8E93" />
    </View>
  );
}

export default function InnovativeChart(props: Props) {
  const [ready, setReady] = useState(false);
  const { width: screenWidth } = Dimensions.get('window');
  const chartWidth = useMemo(() => {
    const margin = props.margin || 16;
    return screenWidth - margin * 2;
  }, [screenWidth, props.margin]);

  useEffect(() => {
    // Defer Skia chart mounting until after interactions are complete
    const task = InteractionManager.runAfterInteractions(() => {
      setReady(true);
    });

    return () => {
      // @ts-expect-error: cancel() method exists on InteractionManager task but may not be in all RN versions
      if (task && typeof task.cancel === 'function') {
        task.cancel();
      }
    };
  }, []);

  if (!ready) {
    return <Skeleton width={chartWidth} height={props.height || 200} />;
  }

  // Direct render - lazy loading will be added back after verifying chart works
  return <SkiaChart {...props} />;
}


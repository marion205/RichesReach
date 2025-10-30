import React, { useMemo } from 'react';
import { View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

type Point = { t: number; c: number }; // epoch ms + close
export default function SimpleLineChart({ data }: { data: Point[] }) {
  console.log('🔍 SimpleLineChart - Received data:', data);
  console.log('🔍 SimpleLineChart - Data length:', data?.length);
  console.log('🔍 SimpleLineChart - First item:', data?.[0]);
  console.log('🔍 SimpleLineChart - Last item:', data?.[data?.length - 1]);
  
  const path = useMemo(() => {
    console.log('🔍 SimpleLineChart - useMemo triggered with data:', data);
    if (!data?.length) {
      console.log('🔍 SimpleLineChart - No data, returning empty');
      return '';
    }
    const sorted = [...data].sort((a, b) => a.t - b.t);
    console.log('🔍 SimpleLineChart - Sorted data:', sorted);

    // normalize to [0,1]
    const t0 = sorted[0].t, t1 = sorted[sorted.length - 1].t || t0 + 1;
    const min = Math.min(...sorted.map(d => d.c));
    const max = Math.max(...sorted.map(d => d.c)) || min + 1;
    
    console.log('🔍 SimpleLineChart - Time range:', t0, 'to', t1);
    console.log('🔍 SimpleLineChart - Price range:', min, 'to', max);

    const W = 300, H = 200; // SVG viewport; parent View height must be >= H
    const x = (t: number) => ((t - t0) / (t1 - t0 || 1)) * W;
    const y = (v: number) => H - ((v - min) / (max - min || 1)) * H;

    const cmds = sorted
      .map((d, i) => {
        const xVal = x(d.t);
        const yVal = y(d.c);
        const cmd = `${i ? 'L' : 'M'} ${xVal.toFixed(1)} ${yVal.toFixed(1)}`;
        console.log(`🔍 SimpleLineChart - Point ${i}: t=${d.t}, c=${d.c}, x=${xVal}, y=${yVal}, cmd=${cmd}`);
        return cmd;
      })
      .join(' ');
    
    const result = { d: cmds, W, H };
    console.log('🔍 SimpleLineChart - Generated path:', result);
    return result;
  }, [data]);

  console.log('🔍 SimpleLineChart - Path result:', path);
  console.log('🔍 SimpleLineChart - Will render:', !!(path && path.d));
  
  if (!path || !path.d) {
    console.log('🔍 SimpleLineChart - Returning null (no path)');
    return null;
  }
  
  console.log('🔍 SimpleLineChart - Rendering SVG with path:', path.d);
  return (
    <View style={{ height: 220, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f0f0f0' }}>
      <Svg width={path.W} height={path.H} style={{ backgroundColor: '#e0e0e0' }}>
        <Path d={path.d} strokeWidth={2} stroke="black" fill="none" />
      </Svg>
    </View>
  );
}

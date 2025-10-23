import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';

type Props = {
  data?: number[];          // raw prices
  width?: number;           // total width
  height?: number;          // total height
  upColor?: string;
  downColor?: string;
  neutralColor?: string;
};

function hashStr(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/** Make a nice deterministic fake series when none is provided (so no network needed). */
function makeSeries(seed = 1, n = 24) {
  const out:number[] = [];
  let val = 100 + (seed % 50);
  for (let i = 0; i < n; i++) {
    // pseudo-random walk
    const step = ((seed % 7) - 3) * 0.2 + Math.sin((i + seed) * 0.45) * 0.7;
    val = Math.max(1, val + step);
    out.push(+(val || 0).toFixed(2));
    seed = (seed * 9301 + 49297) % 233280;
  }
  return out;
}

/** Normalize array 0..1; if flat, all 0.5 */
function normalize(a: number[]) {
  const min = Math.min(...a);
  const max = Math.max(...a);
  if (!isFinite(min) || !isFinite(max) || max === min) return a.map(() => 0.5);
  return a.map(v => (v - min) / (max - min));
}

export default function SparkMini({
  data,
  width = 88,
  height = 24,
  upColor = '#22C55E',
  downColor = '#EF4444',
  neutralColor = '#9CA3AF',
}: Props) {
  const series = useMemo(() => data && data.length > 1 ? data : makeSeries(hashStr(JSON.stringify(data) || 'x')), [data]);
  const norm = useMemo(() => normalize(series), [series]);
  const lastDelta = series[series.length - 1] - series[0];
  const tone = lastDelta > 0 ? upColor : lastDelta < 0 ? downColor : neutralColor;

  const barCount = Math.min(24, norm.length);
  const barW = Math.max(2, Math.floor((width - (barCount - 1) * 2) / barCount)); // 2px gaps

  return (
    <View style={[styles.container, { width, height }]}>
      {norm.slice(-barCount).map((v, i) => {
        const h = Math.max(2, Math.round(v * (height - 2)) + 2);
        return (
          <View
            key={i}
            style={{
              width: barW,
              height: h,
              backgroundColor: tone,
              borderRadius: 2,
              marginRight: i === barCount - 1 ? 0 : 2,
              opacity: 0.85,
              alignSelf: 'flex-end',
            }}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    overflow: 'hidden',
  },
});

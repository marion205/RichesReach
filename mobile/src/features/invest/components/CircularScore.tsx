/**
 * Circular score ring (0–100) for Private Markets AI Deal Score.
 * Gray track + colored progress arc; score starts from top (-90°).
 * Uses react-native-svg only; no animation libs.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';

export interface CircularScoreProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  progressColor?: string;
  trackColor?: string;
  textColor?: string;
}

export default function CircularScore({
  score,
  size = 140,
  strokeWidth = 12,
  progressColor = '#3B82F6',
  trackColor = '#E2E8F0',
  textColor = '#FFFFFF',
}: CircularScoreProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <View style={[styles.container, { width: size, height: size }]}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <Circle
          cx={cx}
          cy={cy}
          r={radius}
          stroke={trackColor}
          strokeWidth={strokeWidth}
          fill="none"
        />
        <G transform={`rotate(-90 ${cx} ${cy})`}>
          <Circle
            cx={cx}
            cy={cy}
            r={radius}
            stroke={progressColor}
            strokeWidth={strokeWidth}
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </G>
      </Svg>
      <View style={styles.textOverlay} pointerEvents="none">
        <Text style={[styles.scoreValue, { color: textColor }]}>{score}</Text>
        <Text style={[styles.scoreLabel, { color: textColor }]}>out of 100</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  textOverlay: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreValue: {
    fontSize: 48,
    fontWeight: '800',
    lineHeight: 54,
  },
  scoreLabel: {
    fontSize: 14,
    opacity: 0.85,
    marginTop: 4,
  },
});

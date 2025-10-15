import React, { memo, useMemo } from 'react';
import { View } from 'react-native';
import Svg, { Line, Rect, Path, Polyline } from 'react-native-svg';

type Candle = { open:number; high:number; low:number; close:number };
type Props = {
  data: Candle[];
  indicators?: {
    SMA20?: (number|null)[];
    SMA50?: (number|null)[];
    EMA12?: (number|null)[];
    EMA26?: (number|null)[];
    BBUpper?: (number|null)[];
    BBMiddle?: (number|null)[];
    BBLower?: (number|null)[];
  };
  width: number;
  height: number;
};

const AdvancedChart: React.FC<Props> = ({ data, indicators, width, height }) => {
  const pad = 8;
  const candleW = Math.max(2, Math.floor((width - pad*2) / data.length));
  const [min, max] = useMemo(() => {
    const vals:number[] = [];
    data.forEach(c => vals.push(c.low, c.high));
    ["SMA20","SMA50","EMA12","EMA26","BBUpper","BBLower"].forEach(k=>{
      const arr = (indicators as any)?.[k];
      if (arr && Array.isArray(arr)) arr.forEach((v:number|null)=>{ if(v!=null) vals.push(v); });
    });
    const mn = Math.min(...vals), mx = Math.max(...vals);
    return [mn, mx];
  }, [data, indicators]);

  const y = (v:number)=> pad + (height - pad*2) * (1 - (v - min)/(max - min + 1e-6));
  const x = (i:number)=> pad + i * candleW + Math.floor(candleW*0.5);

  const linePath = (arr:(number|null)[] | undefined)=>{
    if (!arr || !Array.isArray(arr)) return '';
    let d = '';
    arr.forEach((v, i) => {
      if (v==null) return;
      const cmd = (d==='' ? 'M' : 'L');
      d += `${cmd}${x(i)},${y(v)} `;
    });
    return d.trim();
  };

  return (
    <View>
      <Svg width={width} height={height}>
        {/* grid */}
        <Line x1={pad} y1={pad} x2={pad} y2={height-pad} stroke="#eee"/>
        <Line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#eee"/>

        {/* candles */}
        {data.map((c, i) => {
          const cx = x(i);
          const bodyTop = y(Math.max(c.open, c.close));
          const bodyBot = y(Math.min(c.open, c.close));
          const color = c.close >= c.open ? "#22C55E" : "#EF4444";
          return (
            <React.Fragment key={i}>
              <Line x1={cx} x2={cx} y1={y(c.high)} y2={y(c.low)} stroke={color} />
              <Rect x={cx - candleW*0.35} y={bodyTop} width={candleW*0.7}
                    height={Math.max(1, bodyBot - bodyTop)} fill={color} />
            </React.Fragment>
          );
        })}

        {/* overlays */}
        {indicators?.SMA20 && <Path d={linePath(indicators.SMA20)} stroke="#0ea5e9" fill="none" />}
        {indicators?.SMA50 && <Path d={linePath(indicators.SMA50)} stroke="#6366f1" fill="none" />}
        {indicators?.EMA12 && <Path d={linePath(indicators.EMA12)} stroke="#f59e0b" fill="none" />}
        {indicators?.EMA26 && <Path d={linePath(indicators.EMA26)} stroke="#84cc16" fill="none" />}
        {indicators?.BBUpper && <Path d={linePath(indicators.BBUpper)} stroke="#94a3b8" fill="none" />}
        {indicators?.BBMiddle && <Path d={linePath(indicators.BBMiddle)} stroke="#cbd5e1" fill="none" />}
        {indicators?.BBLower && <Path d={linePath(indicators.BBLower)} stroke="#94a3b8" fill="none" />}
      </Svg>
    </View>
  );
};
export default memo(AdvancedChart);

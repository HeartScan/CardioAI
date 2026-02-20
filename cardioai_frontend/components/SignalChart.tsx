'use client';

import { useEffect, useRef, useMemo } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

interface SignalChartProps {
  data: number[][]; // [time[], signal[]]
  title?: string;
  hideYAxis?: boolean;
  globalTimeOrigin?: number;
  selection?: { min: number, max: number };
  onSelectionChange?: (selection: { min: number, max: number }) => void;
}

export default function SignalChart({
  data,
  title,
  hideYAxis = false,
  globalTimeOrigin,
  selection,
  onSelectionChange,
}: SignalChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const uPlotInstance = useRef<uPlot | null>(null);
  const [size, setSize] = [useRef({ width: 0, height: 0 }).current, (s: {width: number, height: number}) => {}]; // Simplified for logic check
  const sizeRef = useRef({ width: 0, height: 0 });

  useEffect(() => {
    if (!chartRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        sizeRef.current = {
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        };
        if (uPlotInstance.current) {
          uPlotInstance.current.setSize(sizeRef.current);
        }
      }
    });
    observer.observe(chartRef.current);
    return () => observer.disconnect();
  }, []);

  const plotData = useMemo(() => {
    if (!data || !data[0] || !data[1]) return [[]];
    return data;
  }, [data]);

  useEffect(() => {
    if (!chartRef.current || !data || !data[0]) return;

    const origin = globalTimeOrigin !== undefined ? globalTimeOrigin : (data[0]?.[0] || 0);
    const last = data[0][data[0].length - 1];
    const totalRange = last - origin;
    const isNano = totalRange > 1e7;
    const step = isNano ? 1e9 : 1000;

    const opts: uPlot.Options = {
      title,
      width: sizeRef.current.width || 600,
      height: sizeRef.current.height || 400,
      padding: [12, 16, 12, 12],
      cursor: { 
        drag: { x: false, y: false },
        sync: { key: 'cardioai' },
      },
      select: { show: false, left: 0, top: 0, width: 0, height: 0 },
      scales: {
        x: { time: false, min: selection?.min, max: selection?.max },
        y: { range: (u, min, max) => [min - (max-min)*0.1, max + (max-min)*0.1] },
      },
      series: [
        {
          value: (u, v) => v == null ? '' : ((v - origin) / step).toFixed(3) + 's',
        },
        {
          stroke: '#2563eb',
          width: 2,
          label: 'Signal',
          points: { show: false },
          paths: uPlot.paths.linear ? uPlot.paths.linear() : undefined,
        }
      ],
      axes: [
        { 
          show: true,
          grid: { show: true, stroke: '#f1f5f9', width: 1 },
          ticks: { show: true, stroke: '#e2e8f0' },
          font: '10px sans-serif',
          values: (u: uPlot, vals: number[]) => vals.map(v => {
            const seconds = (v - origin) / step;
            return seconds.toFixed(Math.abs(seconds) < 10 ? 1 : 0) + 's';
          }),
        }, 
        { 
          show: !hideYAxis,
          grid: { show: true, stroke: '#f1f5f9', width: 1 },
          ticks: { show: true, stroke: '#e2e8f0' },
          font: '10px sans-serif',
        }
      ],
      hooks: {
        init: [
          (u) => {
            const over = u.over;
            over.addEventListener('wheel', (e: WheelEvent) => {
              e.preventDefault();
              const delta = e.deltaY > 0 ? 1.1 : 0.9;
              const { left, top } = over.getBoundingClientRect();
              const mouseY = e.clientY - top;
              const mouseX = e.clientX - left;

              // Zoom Y
              if (!e.shiftKey && !e.ctrlKey) {
                const yScale = u.scales.y;
                if (yScale.min !== undefined && yScale.max !== undefined) {
                  const valAtMouse = u.posToVal(mouseY, 'y');
                  const newRange = (yScale.max - yScale.min) * delta;
                  const ratio = (yScale.max - valAtMouse) / (yScale.max - yScale.min);
                  u.setScale('y', { min: valAtMouse - newRange * (1 - ratio), max: valAtMouse + newRange * ratio });
                }
              }

              // Zoom X
              if (e.ctrlKey) {
                const xScale = u.scales.x;
                if (xScale.min !== undefined && xScale.max !== undefined) {
                  const valAtMouse = u.posToVal(mouseX, 'x');
                  const newRange = (xScale.max - xScale.min) * delta;
                  const ratio = (valAtMouse - xScale.min) / (xScale.max - xScale.min);
                  const newMin = valAtMouse - newRange * ratio;
                  const newMax = valAtMouse + newRange * (1 - ratio);
                  
                  if (onSelectionChange) {
                    onSelectionChange({ min: newMin, max: newMax });
                  } else {
                    u.setScale('x', { min: newMin, max: newMax });
                  }
                }
              }
            }, { passive: false });
          },
        ],
      },
    };

    uPlotInstance.current = new uPlot(opts, plotData as uPlot.AlignedData, chartRef.current);
    return () => {
      uPlotInstance.current?.destroy();
      uPlotInstance.current = null;
    };
  }, [plotData, hideYAxis, globalTimeOrigin, title]);

  useEffect(() => {
    if (selection && uPlotInstance.current) {
      uPlotInstance.current.setScale('x', { min: selection.min, max: selection.max });
    }
  }, [selection]);

  return (
    <div 
      ref={chartRef} 
      className="w-full h-full overflow-hidden" 
    />
  );
}

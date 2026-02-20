'use client';

import { useState, useMemo } from 'react';
import SignalChart from './SignalChart';
import OverviewChart from './OverviewChart';

interface ChartWorkspaceProps {
  displayMode: 'high' | 'low';
  chartData: number[][] | null;
}

export default function ChartWorkspace({
  displayMode,
  chartData,
}: ChartWorkspaceProps) {
  const globalTimeOrigin = chartData?.[0]?.[0] || 0;

  const initialSelection = useMemo(() => {
    if (!chartData || chartData[0].length === 0) return undefined;
    const start = chartData[0][0];
    const last = chartData[0][chartData[0].length - 1];
    const diff = last - start;
    
    const isNano = diff > 1e7; 
    const step = isNano ? 1e9 : 1000;
    
    const end = start + 10 * step; 
    return { min: start, max: Math.min(last, end) };
  }, [chartData]);

  const [lastDataId, setLastDataId] = useState<number[][] | null>(null);
  const [internalSelection, setInternalSelection] = useState<{ min: number; max: number } | undefined>(undefined);

  if (chartData !== lastDataId) {
    setLastDataId(chartData);
    setInternalSelection(undefined);
  }

  const selection = internalSelection || initialSelection;

  if (!chartData || chartData[0].length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-300 font-bold uppercase text-[11px] tracking-widest italic">
        Awaiting signal data...
      </div>
    );
  }

  const segments = useMemo(() => {
    if (displayMode !== 'high') return null;
    const totalPoints = chartData[0].length;
    const segmentSize = Math.floor(totalPoints / 3);
    
    return [0, 1, 2].map(i => {
      const start = i * segmentSize;
      const end = i === 2 ? totalPoints : (i + 1) * segmentSize;
      return [
        chartData[0].slice(start, end),
        chartData[1].slice(start, end)
      ];
    });
  }, [chartData, displayMode]);

  return (
    <div className="w-full h-full flex flex-col bg-white overflow-hidden m-0 p-0 gap-1">
      {displayMode === 'high' ? (
        segments?.map((seg, idx) => (
          <div key={idx} className="flex-1 w-full relative m-0 p-0 overflow-hidden bg-white border-b border-slate-100 last:border-b-0">
            <SignalChart
              data={seg}
              hideYAxis={false}
              globalTimeOrigin={globalTimeOrigin}
              title={`Segment ${idx + 1}`}
            />
          </div>
        ))
      ) : (
        <div className="w-full h-full flex flex-col m-0 p-0 overflow-hidden bg-white">
          <div className="flex-[4] min-h-0 w-full relative m-0 p-0 overflow-hidden bg-white">
            <SignalChart
              data={chartData}
              title="Zoomed region"
              globalTimeOrigin={globalTimeOrigin}
              selection={selection}
              onSelectionChange={setInternalSelection}
            />
          </div>
          <div className="flex-1 min-h-[100px] max-h-[120px] w-full shrink-0 border-t border-slate-200 bg-slate-50/30 m-0 p-0 flex items-center overflow-hidden relative">
            <OverviewChart 
              data={chartData}
              selection={selection!}
              onSelectionChange={setInternalSelection}
              globalTimeOrigin={globalTimeOrigin}
            />
          </div>
        </div>
      )}
    </div>
  );
}

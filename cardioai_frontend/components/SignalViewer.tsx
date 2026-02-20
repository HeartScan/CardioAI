'use client';

import { useState } from 'react';
import ChartWorkspace from './ChartWorkspace';
import { X, LayoutGrid, Activity } from 'lucide-react';

interface SignalViewerProps {
  data: number[][]; // [time[], signal[]]
  title?: string;
  onClose?: () => void;
}

export default function SignalViewer({ data, title, onClose }: SignalViewerProps) {
  const [displayMode, setDisplayMode] = useState<'high' | 'low'>('low');

  if (!data || data[0].length === 0) return null;

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Viewer Header */}
      <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4 border-b border-slate-100 shrink-0 bg-white z-10">
        <div className="flex items-center gap-3 md:gap-4 min-w-0">
          <div className="hidden sm:flex w-8 h-8 bg-blue-50 rounded-lg items-center justify-center text-blue-600 shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div className="min-w-0">
             <h3 className="text-sm md:text-lg font-bold text-slate-800 truncate">
               {title || 'Signal Analysis'}
             </h3>
             <p className="text-[10px] text-slate-400 font-medium uppercase tracking-tight hidden sm:block">Accelerometer AZ • {data[0].length} Samples</p>
          </div>
          
          {/* Mode switch - hidden on mobile small screens */}
          <div className="hidden md:flex items-center gap-1 bg-slate-100 p-1 rounded-lg ml-2">
            <button
              onClick={() => setDisplayMode('low')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                displayMode === 'low' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Standard
            </button>
            <button
              onClick={() => setDisplayMode('high')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                displayMode === 'high' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Split View
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Mobile mode toggle (simplified) */}
          <button 
            onClick={() => setDisplayMode(displayMode === 'low' ? 'high' : 'low')}
            className="md:hidden p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
          
          {onClose && (
            <button 
              onClick={onClose}
              className="p-2 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-500 transition-colors"
              title="Close viewer"
            >
              <X className="w-6 h-6" />
            </button>
          )}
        </div>
      </div>

      {/* Main Chart Area */}
      <div className="flex-1 min-h-0 relative">
        <ChartWorkspace 
          chartData={data}
          displayMode={displayMode}
        />
      </div>
    </div>
  );
}

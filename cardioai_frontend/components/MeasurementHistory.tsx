'use client';

import { useEffect, useState } from 'react';
import { storage, MeasurementEntry } from '@/lib/utils/storage';
import { Activity, Trash2, ChevronRight, Clock } from 'lucide-react';

interface MeasurementHistoryProps {
  onSelect: (entry: MeasurementEntry) => void;
  activeId?: string;
}

export default function MeasurementHistory({ onSelect, activeId }: MeasurementHistoryProps) {
  const [items, setItems] = useState<MeasurementEntry[]>([]);

  const refresh = () => {
    setItems(storage.getMeasurements());
  };

  useEffect(() => {
    refresh();
    // Listen for storage changes in other tabs
    window.addEventListener('storage', refresh);
    // Poll for changes in this tab (since we don't have a shared state manager)
    const interval = setInterval(refresh, 2000);
    return () => {
      window.removeEventListener('storage', refresh);
      clearInterval(interval);
    };
  }, []);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    storage.deleteMeasurement(id);
    refresh();
  };

  if (items.length === 0) {
    return (
      <div className="text-center py-8 px-4 border-2 border-dashed border-slate-200 rounded-xl">
        <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-xs font-medium text-slate-400">No recent measurements found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">
      {items.map((item) => (
        <div
          key={item.id}
          onClick={() => onSelect(item)}
          className={`
            group relative p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3
            ${activeId === item.id 
              ? 'bg-blue-50 border-blue-200 ring-1 ring-blue-100' 
              : 'bg-white border-slate-100 hover:border-blue-200 hover:shadow-md hover:shadow-blue-50/50'}
          `}
        >
          <div className={`
            w-8 h-8 rounded-lg flex items-center justify-center shrink-0
            ${activeId === item.id ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-400 group-hover:bg-blue-100 group-hover:text-blue-500'}
          `}>
            <Activity className="w-4 h-4" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">
                {new Date(item.timestamp).toLocaleDateString()}
              </span>
              <button
                onClick={(e) => handleDelete(e, item.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-red-500 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-sm font-bold text-slate-700 truncate leading-none mb-1">
              {item.source.replace('Test data: ', '').replace('Real-time clinical measurement', 'Measurement')}
            </p>
            <p className="text-[10px] font-medium text-slate-500">
              {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {item.data[0].length} samples
            </p>
          </div>

          <ChevronRight className={`w-4 h-4 transition-transform ${activeId === item.id ? 'text-blue-400' : 'text-slate-300 group-hover:translate-x-0.5'}`} />
        </div>
      ))}
    </div>
  );
}

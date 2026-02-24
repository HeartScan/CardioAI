'use client';

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useIsMobile } from "@/components/ui/use-mobile";
import MobileOnlyError from "@/components/MobileOnlyError";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Activity, Send, Trash2, Menu, X, ChevronRight, History, BarChart3 } from "lucide-react";
import { storage, MeasurementEntry } from "@/lib/utils/storage";
import MeasurementHistory from "@/components/MeasurementHistory";
import SignalViewer from "@/components/SignalViewer";

// Dynamically import the measurement component to avoid SSR issues
const ProHeartRateMeasurement = dynamic(() => import('@/components/ProHeartRateMeasurement'), {
  loading: () => <div className="p-8 text-center text-slate-400">Initializing Clinical Tool...</div>,
  ssr: false
});

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface MeasurementMetadata {
  source_file: string;
  expected_bpm: number;
  expected_episodes: number;
  expected_anomalies: string[];
}

interface MeasurementPayload {
  metadata: MeasurementMetadata;
  request_body: Record<string, unknown>;
}

export default function App() {
  const [history, setHistory] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [activeMeasurement, setActiveMeasurement] = useState<MeasurementEntry | null>(null);
  const [isMeasurementOpen, setIsMeasurementOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [showDeviceError, setShowDeviceError] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const isMobile = useIsMobile();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  useEffect(() => {
    if (isMeasurementOpen) {
      document.body.classList.add('scroll-lock');
    } else {
      document.body.classList.remove('scroll-lock');
    }
    return () => document.body.classList.remove('scroll-lock');
  }, [isMeasurementOpen]);

  // Unified function to send messages or data
  async function callApi(userMessage: string | null, observation: Record<string, unknown> | null) {
    if (busy) return;
    try {
      setBusy(true);
      
      if (userMessage) {
        setHistory(prev => [...prev, { role: "user", content: userMessage }]);
        setMessage("");
      }

      // Helper for retries (handles cold starts)
      const fetchWithRetry = async (url: string, options: RequestInit, retries = 3, backoff = 2000) => {
        for (let i = 0; i < retries; i++) {
          try {
            const res = await fetch(url, options);
            
            if (res.ok) return res;

            // If it's a server error or gateway issue (502, 503, 504), definitely retry
            const shouldRetry = res.status >= 500 || res.status === 429;
            
            if (shouldRetry && i < retries - 1) {
              console.warn(`API attempt ${i + 1} failed with status ${res.status}, retrying in ${backoff}ms...`);
              await new Promise(resolve => setTimeout(resolve, backoff));
              backoff *= 2;
              continue;
            }
            return res;
          } catch (err) {
            if (i < retries - 1) {
              await new Promise(resolve => setTimeout(resolve, backoff));
              backoff *= 2;
              continue;
            }
            throw err;
          }
        }
        return fetch(url, options);
      };

      const res = await fetchWithRetry("/api/cardio-ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: userMessage, 
            history: history,
            observation: observation 
        }),
      });

      if (!res.ok) {
        let errorMessage = `API failed: ${res.status}`;
        try {
          const errorData = await res.json();
          errorMessage = errorData.error || errorMessage;
          // If the error is still JSON stringified (common in our proxy), parse it
          if (typeof errorMessage === 'string' && errorMessage.startsWith('{')) {
            try {
              const parsed = JSON.parse(errorMessage);
              errorMessage = parsed.detail || parsed.error || errorMessage;
            } catch {}
          }
        } catch {
          // If not JSON, maybe it's HTML error page
          const text = await res.text();
          if (text.includes('<title>502')) errorMessage = "Service is warming up (502 Bad Gateway). Please try again in a moment.";
          else if (text.includes('<title>504')) errorMessage = "Service timeout (504 Gateway Timeout). Backend is taking too long.";
          else errorMessage = text.slice(0, 100); // Show first 100 chars of whatever it is
        }
        throw new Error(errorMessage);
      }
      
      const data = await res.json();
      setHistory(data.history);
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert("Error: " + err.message);
      } else {
        alert("An unknown error occurred");
      }
    } finally {
      setBusy(false);
    }
  }

  const processMeasurementData = async (rawData: any, sourceName: string) => {
    if (!rawData || !Array.isArray(rawData)) {
      alert("Invalid measurement data received");
      return;
    }

    setActiveFile(sourceName);

    // Save to local storage
    const newEntry: MeasurementEntry = {
      id: Math.random().toString(36).substring(7),
      timestamp: new Date().toISOString(),
      source: sourceName,
      data: rawData
    };
    // Convert to chart format [time[], signal[]] for local storage
    const chartData = [
      rawData.map((d: any) => d.timestamp),
      rawData.map((d: any) => d.az)
    ];

    storage.saveMeasurement({
      ...newEntry,
      data: chartData
    });
    setActiveMeasurement({
      ...newEntry,
      data: chartData
    });
    
    const observation = {
      sensor_data: rawData
    };
    
    // Log the payload to console for verification (Vercel compatible)
    console.log('[Clinical Telemetry Capture]', {
      source: sourceName,
      timestamp: new Date().toISOString(),
      dataPoints: rawData.length
    });
    
    await callApi(null, observation);
  };

  const sendRandomMeasurement = async () => {
    setIsSidebarOpen(false);
    const randomIndex = Math.floor(Math.random() * 10);
    const filename = `measurement_${randomIndex}.json`;
    
    try {
        setBusy(true);
        const res = await fetch(`/measurements/${filename}`);
        if (!res.ok) throw new Error(`Failed to fetch ${filename}`);
        const item: MeasurementPayload = await res.json();
        
        const data = item.request_body?.sensor_data;
        if (!data) throw new Error("sensor_data not found in test file");

        setBusy(false);
        await processMeasurementData(data, `Test data: ${item.metadata.source_file}`);
    } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        alert("Failed to send measurement: " + msg);
        setBusy(false);
    }
  };

  const handleRealMeasurementComplete = async (heartRate: number, rawData?: any) => {
    setIsMeasurementOpen(false);
    await processMeasurementData(rawData, "Real-time clinical measurement");
  };

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (message.trim()) callApi(message, null);
    }
  }

  return (
    <div className="flex flex-col h-[100dvh] bg-[#F8FAFC] font-sans text-slate-900 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-4 md:px-8 py-4 bg-white border-b border-slate-200 shadow-sm shrink-0 z-30">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="md:hidden p-2 -ml-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-md shadow-blue-100">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 tracking-tight leading-none">Cardio<span className="text-blue-600">AI</span></h1>
              <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mt-1">Clinical Support System</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-full border border-green-100 text-[11px] font-bold">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            Active
          </div>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden relative">
        {/* Sidebar */}
        <aside className={`
          fixed inset-y-0 left-0 w-80 bg-white border-r border-slate-200 z-40 transform transition-transform duration-300 ease-in-out flex flex-col p-4 md:p-6 gap-6
          md:relative md:translate-x-0
          ${isSidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'}
        `}>
          <div className="space-y-4">
            <div className="flex items-center justify-between md:hidden mb-2">
               <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Menu</h3>
               <button onClick={() => setIsSidebarOpen(false)} className="p-1 text-slate-400"><X className="w-5 h-5" /></button>
            </div>
            
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Patient Data</h3>
            
            <button 
              onClick={() => {
                setIsSidebarOpen(false);
                if (isMobile) {
                  setIsMeasurementOpen(true);
                } else {
                  setShowDeviceError(true);
                }
              }}
              disabled={busy}
              className="w-full py-4 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white rounded-xl font-bold transition-all shadow-lg shadow-blue-100 flex items-center justify-center gap-2"
            >
              <Activity className="w-5 h-5" />
              Start Measurement
            </button>

            <button 
              onClick={sendRandomMeasurement}
              disabled={busy}
              className="w-full py-3 px-4 bg-white hover:bg-slate-50 disabled:bg-slate-100 text-slate-600 border border-slate-200 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              Send Test Data
            </button>
          </div>

          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            <div className="flex items-center justify-between mb-4">
               <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recent History</h3>
               <button 
                onClick={() => storage.clearAll()}
                className="text-[10px] font-bold text-slate-400 hover:text-red-500 transition-colors uppercase tracking-tight"
               >
                Clear All
               </button>
            </div>
            <MeasurementHistory 
              activeId={activeMeasurement?.id}
              onSelect={(entry) => {
                setActiveMeasurement(entry);
                setActiveFile(entry.source);
                setIsHistoryOpen(false);
              }}
            />
          </div>

          {activeFile && (
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <h4 className="text-xs font-bold text-slate-400 uppercase mb-2 tracking-tight">Active Source</h4>
              <p className="text-sm font-mono text-slate-600 break-all leading-relaxed">{activeFile}</p>
            </div>
          )}

          <div className="mt-auto pt-4 border-t border-slate-100">
            <button 
              onClick={() => { 
                setHistory([]); 
                setActiveFile(null); 
                setActiveMeasurement(null);
                setIsSidebarOpen(false); 
              }}
              disabled={busy}
              className="w-full py-2 px-4 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Clear Session
            </button>
          </div>
        </aside>

        {/* Backdrop for mobile sidebar */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-slate-900/20 backdrop-blur-sm z-30 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          ></div>
        )}

        {/* Chat Area */}
        <section className="flex-1 flex flex-col bg-[#F1F5F9] relative overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 transition-all">
            {history.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4 py-12">
                <div className="w-16 h-16 md:w-20 md:h-20 bg-white rounded-[2rem] shadow-xl flex items-center justify-center mb-4">
                   <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.040L3 6.241V11c0 5.523 4.477 10 10 10s10-4.477 10-10V6.241l-1.382-.257z" />
                   </svg>
                </div>
                <h2 className="text-xl md:text-2xl font-bold text-slate-800">CardioAI Assistant</h2>
                <p className="text-sm md:text-base text-slate-500 leading-relaxed px-4">Initialize diagnostic analysis by performing a real-time measurement or sending sample data.</p>
              </div>
            ) : (
              history
                .filter(m => m.role !== "system")
                .map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[90%] md:max-w-[80%] rounded-2xl p-4 md:p-5 shadow-sm border ${
                      m.role === 'user' 
                        ? 'bg-blue-600 text-white border-blue-500 rounded-tr-none' 
                        : 'bg-white text-slate-700 border-slate-200 rounded-tl-none'
                    }`}>
                      <div className={`text-[10px] uppercase font-bold tracking-widest mb-1.5 ${
                        m.role === 'user' ? 'text-blue-200' : 'text-slate-400'
                      }`}>
                        {m.role === 'user' ? 'Practitioner' : 'AI Arrhythmologist'}
                      </div>
                      <div className="text-sm md:text-[15px] leading-relaxed whitespace-pre-wrap font-medium">
                        {m.content}
                      </div>
                    </div>
                  </div>
                ))
            )}
            {busy && (
              <div className="flex justify-start animate-pulse">
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 md:p-5 shadow-sm">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:-.3s]"></div>
                    <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:-.5s]"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} className="h-4" />
          </div>

          {/* Input Bar */}
          <div className="p-4 md:p-8 bg-gradient-to-t from-[#F1F5F9] via-[#F1F5F9] to-transparent shrink-0">
            <form 
              onSubmit={(e) => { e.preventDefault(); if (message.trim()) callApi(message, null); }}
              className="max-w-4xl mx-auto flex items-end gap-2 md:gap-3 bg-white p-2 md:p-3 rounded-2xl shadow-lg border border-slate-200 focus-within:shadow-xl transition-shadow"
            >
              <textarea
                placeholder="Request diagnostic clarification..."
                value={message}
                disabled={busy}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKey}
                rows={1}
                className="flex-1 bg-transparent border-none focus:ring-0 text-slate-700 placeholder-slate-400 resize-none py-2 px-2 md:px-3 min-h-[44px] max-h-32 text-sm font-medium"
              />
              <button 
                type="submit" 
                disabled={busy || !message.trim()}
                className="w-10 h-10 md:w-11 md:h-11 flex items-center justify-center bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white rounded-xl transition-all shadow-md shadow-blue-100 shrink-0"
              >
                <Send className="w-4 h-4 md:w-5 md:h-5" />
              </button>
            </form>
          </div>
        </section>
      </main>

      {/* Measurement Dialog */}
      <Dialog open={isMeasurementOpen} onOpenChange={setIsMeasurementOpen}>
        <DialogContent className="sm:max-w-2xl bg-white border-slate-200 text-slate-900 overflow-hidden p-0 flex flex-col h-full sm:h-auto max-h-screen rounded-none sm:rounded-2xl">
          <DialogHeader className="p-6 md:p-8 pb-0 shrink-0 bg-slate-50 border-b border-slate-100">
            <DialogTitle className="text-xl md:text-2xl font-bold flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-md shadow-blue-100">
                <Activity className="w-6 h-6 text-white" />
              </div>
              Clinical Data Capture
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-10 pt-6">
             <ProHeartRateMeasurement 
                durationMs={60000}
                onComplete={handleRealMeasurementComplete}
                onError={(err) => {
                   console.error(err);
                   setIsMeasurementOpen(false);
                   alert("Analysis Error: " + err);
                }}
                className="bg-slate-50 border border-slate-200 w-full"
             />
          </div>
        </DialogContent>
      </Dialog>

      {/* Signal Viewer Dialog */}
      <Dialog open={!!activeMeasurement} onOpenChange={(open) => !open && setActiveMeasurement(null)}>
        <DialogContent className="max-w-[95vw] w-[1400px] h-[90vh] bg-white border-slate-200 text-slate-900 overflow-hidden p-0 flex flex-col rounded-2xl shadow-2xl transition-all">
          <DialogHeader className="sr-only">
            <DialogTitle>Signal Analysis Viewer</DialogTitle>
            <DialogDescription>Detailed visualization of recorded heart vibrations signal</DialogDescription>
          </DialogHeader>
          {activeMeasurement && (
            <SignalViewer 
              data={activeMeasurement.data}
              title={activeMeasurement.source}
              onClose={() => setActiveMeasurement(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Error Dialog */}
      <Dialog open={showDeviceError} onOpenChange={setShowDeviceError}>
        <DialogContent className="sm:max-w-md bg-white border-slate-200 text-slate-900 overflow-hidden p-6 rounded-2xl shadow-xl">
          <DialogHeader className="sr-only">
            <DialogTitle>Device Compatibility Error</DialogTitle>
            <DialogDescription>Information about required sensors for measurement</DialogDescription>
          </DialogHeader>
          <MobileOnlyError onClose={() => setShowDeviceError(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

/**
 * IMPORTANT: THIS COMPONENT MUST ONLY USE REAL DEVICE DATA
 */
import React, {useState, useEffect, useRef, useCallback} from 'react';
import {Heart, Activity, CheckCircle, AlertCircle} from 'lucide-react';
import {Button} from '@/components/ui/button';
import Image from "next/image"
import {useIsMobile} from "@/components/ui/use-mobile"
import {useAnalytics} from "@/lib/analytics/AnalyticsProvider"
import {AccelerometerDataPoint} from "@/app/service/apiService";
import {useMotionSensor} from "@/hooks/useMotionSensor";

export interface HeartRateMeasurementProps {
    onComplete?: (heartRate: number, rawData?: AccelerometerDataPoint[]) => void;
    onStart?: () => void;
    onError?: (error: string) => void;
    className?: string;
    onDesktopClick?: () => void;
    durationMs?: number;
}


const ProHeartRateMeasurement: React.FC<HeartRateMeasurementProps> = (
    {
        onComplete,
        onStart,
        onError,
        className = '',
        onDesktopClick,
        durationMs = 60000,
    }) => {
    const isMobile = useIsMobile();
    // State variables
    const [stage, setStage] = useState<'ready' | 'countdown' | 'measuring' | 'complete' | 'error'>('ready');
    const stageRef = useRef(stage); 
    useEffect(() => {
        stageRef.current = stage;
    }, [stage]);

    const [countdown, setCountdown] = useState(3);
    const [isCounting, setIsCounting] = useState(false);
    const [measurementProgress, setMeasurementProgress] = useState(0);
    const [errorMessage, setErrorMessage] = useState('');
    const [chartData, setChartData] = useState<number[]>([]);

    // Refs for measurement data
    const dataBufferRef = useRef<AccelerometerDataPoint[]>([]);
    const lastPeakTimeRef = useRef(0);
    const heartbeatCountRef = useRef(0);
    const chartCanvasRef = useRef<HTMLCanvasElement>(null);
    const animationFrameRef = useRef<number | null>(null);
    const updateChartTimerRef = useRef<NodeJS.Timeout | null>(null);
    const motionDataReceivedRef = useRef(false);
    const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);
    const analytics = useAnalytics();
    
    // Refs for the MATLAB-style peak detection algorithm
    const quarterPeriod = 20;
    const zValuesRef = useRef<number[]>([]);
    const deviationAbsSumsRef = useRef<number[]>([]);
    const meanDeviationsRef = useRef<number[]>([]);
    const maxMeanDeviationsLongRef = useRef<number[]>([]);

    // Buffer for handling duplicate timestamps intelligently
    const duplicateTimestampBuffer = useRef<AccelerometerDataPoint[]>([]);
    const lastUniqueTimestamp = useRef<number>(0);

    // Very simple beep sound function using a single audio context
    const audioContextRef = useRef<AudioContext | null>(null);

    const playBeep = async (frequency = 800, duration = 0.1) => {
        try {
            if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
                const contextOptions = { latencyHint: 'playback' as AudioContextLatencyCategory };
                audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)(contextOptions);
            }
            const ctx = audioContextRef.current;
            if (ctx.state === 'suspended') {
                await ctx.resume();
            }
            if (ctx.state !== 'running') return;

            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);

            // ANALYTIC ENVELOPE
            const attackTime = 0.02;
            gainNode.gain.setValueAtTime(0.001, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.2, ctx.currentTime + attackTime);
            gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            oscillator.start();
            oscillator.stop(ctx.currentTime + duration);
        } catch (err: unknown) {
            console.error('Error playing beep:', err);
        }
    };

    const cleanupMeasurement = () => {
        if (animationFrameRef.current !== null) cancelAnimationFrame(animationFrameRef.current);
        if (updateChartTimerRef.current) clearInterval(updateChartTimerRef.current);
        if (countdownTimerRef.current) clearTimeout(countdownTimerRef.current);
    };

    const drawChart = () => {
        const canvas = chartCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        const width = canvas.width;
        const height = canvas.height;
        ctx.clearRect(0, 0, width, height);
        const dataToUse = dataBufferRef.current.length > 0
            ? dataBufferRef.current.slice(-150).map(data => data.az)
            : chartData;
        ctx.fillStyle = 'rgba(10, 10, 20, 0.05)';
        ctx.fillRect(0, 0, width, height);
        let maxVal = Math.max(...dataToUse) * 1.1;
        let minVal = Math.min(...dataToUse) * 0.9;
        const range = maxVal - minVal;
        if (range < 0.5) {
            const avg = (maxVal + minVal) / 2;
            maxVal = avg + 0.5; minVal = avg - 0.5;
        }
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < dataToUse.length; i++) {
            const x = (i / (dataToUse.length - 1)) * width;
            const y = height - ((dataToUse[i] - minVal) / (maxVal - minVal)) * height;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
    };

    const completeMeasurement = useCallback(async () => {
        cleanupMeasurement();
        setStage('complete');
        if (onComplete) {
            const formattedData = dataBufferRef.current.map(point => ({
                ax: point.ax, ay: point.ay, az: point.az,
                timestamp: Math.round(point.timestamp)
            }));
            onComplete(0, formattedData);
        }
        playBeep(1200, 0.15);
    }, [onComplete]);

    const startMeasurement = () => {
        setStage('measuring');
        heartbeatCountRef.current = 0;
        zValuesRef.current = [];
        deviationAbsSumsRef.current = [];
        meanDeviationsRef.current = [];
        maxMeanDeviationsLongRef.current = [];
        dataBufferRef.current = [];
        const measurementStartTime = Date.now();

        const animate = () => {
            drawChart();
            animationFrameRef.current = requestAnimationFrame(animate);
        };
        animationFrameRef.current = requestAnimationFrame(animate);

        updateChartTimerRef.current = setInterval(() => {
            if (dataBufferRef.current.length > 0) {
                setChartData(dataBufferRef.current.slice(-150).map(data => data.az));
            }
            const progress = Math.min(100, ((Date.now() - measurementStartTime) / durationMs) * 100);
            setMeasurementProgress(progress);
        }, 50);

        setTimeout(() => {
            if (stageRef.current === 'measuring') completeMeasurement();
        }, durationMs);
    };

    const detectPeaks = useCallback((currentValue: number, currentTime: number) => {
        const noSearchFlagDuration = 400; 
        zValuesRef.current.push(currentValue);
        if (zValuesRef.current.length > 160) zValuesRef.current.shift();
        if (zValuesRef.current.length < 80) {
            deviationAbsSumsRef.current.push(0);
            meanDeviationsRef.current.push(0);
            maxMeanDeviationsLongRef.current.push(0);
            return;
        }
        if (lastPeakTimeRef.current === 0) lastPeakTimeRef.current = currentTime;
        const timeSinceLastPeak = currentTime - lastPeakTimeRef.current;
        if (timeSinceLastPeak < noSearchFlagDuration) return;

        const meanWindow = zValuesRef.current.slice(-40);
        const windowMean = meanWindow.reduce((a, b) => a + b, 0) / meanWindow.length;
        const deviationWindow = zValuesRef.current.slice(-20);
        let deviationAbsSum = deviationWindow.reduce((sum, val) => sum + Math.abs(val - windowMean), 0);
        
        const tempSums = [...deviationAbsSumsRef.current, deviationAbsSum];
        const smoothedDeviation = tempSums.slice(-60).reduce((a,b)=>a+b,0) / 60;
        deviationAbsSumsRef.current.push(smoothedDeviation);

        const meanDeviation = deviationAbsSumsRef.current.slice(-36).reduce((a,b)=>a+b,0) / 36;
        meanDeviationsRef.current.push(meanDeviation);

        const maxMeanDeviationLong = Math.max(...meanDeviationsRef.current.slice(-80));
        maxMeanDeviationsLongRef.current.push(maxMeanDeviationLong);

        const currentSignal = deviationAbsSumsRef.current[deviationAbsSumsRef.current.length - 1];
        const prevSignal = deviationAbsSumsRef.current[deviationAbsSumsRef.current.length - 3];
        const currentThreshold = maxMeanDeviationsLongRef.current[maxMeanDeviationsLongRef.current.length - 1];
        const prevThreshold = maxMeanDeviationsLongRef.current[maxMeanDeviationsLongRef.current.length - 3];

        if (currentSignal > currentThreshold && prevSignal < prevThreshold) {
            lastPeakTimeRef.current = currentTime;
            heartbeatCountRef.current++;
            playBeep(1000, 0.1);
        }
    }, []);

    const handleDeviceMotion = useCallback((event: DeviceMotionEvent) => {
        if (stageRef.current !== 'measuring' || !event.accelerationIncludingGravity) return;
        const accel = event.accelerationIncludingGravity;
        const timestamp = event.timeStamp;
        const dataPoint: AccelerometerDataPoint = {ax: accel.x || 0, ay: accel.y || 0, az: accel.z || 0, timestamp};

        if (!motionDataReceivedRef.current) motionDataReceivedRef.current = true;

        if (timestamp === lastUniqueTimestamp.current) {
            duplicateTimestampBuffer.current.push(dataPoint);
        } else {
            if (duplicateTimestampBuffer.current.length > 0) {
                const startTime = lastUniqueTimestamp.current;
                const timeSpan = timestamp - startTime;
                duplicateTimestampBuffer.current.forEach((point, index) => {
                    const ratio = (index + 1) / (duplicateTimestampBuffer.current.length + 1);
                    point.timestamp = startTime + (timeSpan * ratio);
                    dataBufferRef.current.push(point);
                    detectPeaks(point.az, point.timestamp);
                });
                duplicateTimestampBuffer.current = [];
            }
            lastUniqueTimestamp.current = timestamp;
            dataBufferRef.current.push(dataPoint);
            detectPeaks(dataPoint.az, timestamp);
        }
        if (dataBufferRef.current.length > 2000) dataBufferRef.current.shift();
    }, [detectPeaks]);

    const { requestPermission } = useMotionSensor(handleDeviceMotion);

    const beginCountdown = async () => {
        // Explicitly request permission
        const granted = await requestPermission();
        if (!granted) {
            alert("Motion sensor permission is required.");
            return;
        }

        if (onStart) onStart();
        setStage('countdown');
        setCountdown(3);
        setIsCounting(true);
    };

    useEffect(() => {
        if (isCounting && countdown > 0) {
            countdownTimerRef.current = setTimeout(() => {
                setCountdown(prev => prev - 1);
                playBeep(800, 0.1);
            }, 1000);
        } else if (isCounting && countdown === 0) {
            setIsCounting(false);
            startMeasurement();
        }
        return () => { if (countdownTimerRef.current) clearTimeout(countdownTimerRef.current); };
    }, [countdown, isCounting]);

    useEffect(() => {
        return () => {
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close().catch(console.error);
            }
        };
    }, []);

    return (
        <div className={`flex flex-col items-center justify-center w-full max-w-lg mx-auto rounded-xl p-6 ${className}`}>
            {stage === 'ready' && (
                <div className="flex flex-col items-center space-y-6 text-center">
                    <div className="relative w-24 h-24 mb-4">
                        <Heart className="w-24 h-24 text-red-500 animate-pulse"/>
                        <Activity className="absolute inset-0 w-12 h-12 m-auto text-blue-600"/>
                    </div>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">Clinical Heart Measurement</h3>
            <p className="text-slate-500 mb-4">Place your phone firmly on your chest to measure heart vibrations for AI analysis.</p>
            <Button onClick={() => { playBeep(1, 0.001); if (isMobile) beginCountdown(); else if (onDesktopClick) onDesktopClick(); }} size="lg" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-14 rounded-xl shadow-md shadow-blue-100">Start 60s Session</Button>
        </div>
            )}
            {stage === 'countdown' && (
                <div className="relative flex flex-col items-center justify-center py-12">
                    <Image src="/images/boy.webp" alt="" width={300} height={300} className="absolute opacity-10" />
                    <p className="text-lg font-bold text-slate-400 mb-6 z-10 uppercase tracking-widest">Get Ready</p>
                    <div className="text-8xl font-black text-blue-600 mb-4 z-10 tabular-nums">{countdown}</div>
                    <p className="text-slate-500 z-10 font-medium">Position phone now</p>
                </div>
            )}
            {stage === 'measuring' && (
                <div className="flex flex-col items-center space-y-6 w-full">
                    <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-600 rounded-full border border-blue-100 text-xs font-bold uppercase tracking-wider">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                        Measuring...
                    </div>
                    <div className="w-full h-44 bg-slate-50 rounded-2xl overflow-hidden border border-slate-200 relative">
                        <canvas ref={chartCanvasRef} className="w-full h-full absolute inset-0 opacity-70" />
                        {dataBufferRef.current.length <= 1 && (
                            <div className="absolute inset-0 flex items-center justify-center text-slate-400 font-medium text-sm">Awaiting motion data...</div>
                        )}
                    </div>
                    <div className="w-full space-y-2">
                        <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                            <span>Capture Progress</span>
                            <span>{Math.round(measurementProgress)}%</span>
                        </div>
                        <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                            <div className="h-full bg-blue-600 transition-all duration-300 ease-out" style={{width: `${measurementProgress}%`}}></div>
                        </div>
                    </div>
                    <p className="text-slate-400 text-xs font-medium uppercase tracking-widest">Stay Still and Breathe Normally</p>
                </div>
            )}
            {stage === 'complete' && (
                <div className="flex flex-col items-center space-y-6 text-center py-4">
                    <CheckCircle className="w-16 h-16 text-green-500 mb-2"/>
                    <h3 className="text-xl font-bold text-slate-800 uppercase tracking-tight">Capture Verified</h3>
                    <p className="text-slate-500 text-sm">Data has been recorded and sent for clinical AI analysis.</p>
                    <Button onClick={() => setStage('ready')} variant="outline" className="mt-4 border-slate-200 text-slate-400 hover:text-blue-600">New Measurement</Button>
                </div>
            )}
            {stage === 'error' && (
                <div className="flex flex-col items-center space-y-6 text-center py-4">
                    <AlertCircle className="w-16 h-16 text-red-500 mb-2"/>
                    <h3 className="text-xl font-bold text-slate-800">Telemetry Error</h3>
                    <p className="text-slate-500 text-sm px-4">{errorMessage}</p>
                    <Button onClick={() => setStage('ready')} className="bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 px-8 rounded-xl mt-4 shadow-md shadow-blue-100">Retry Capture</Button>
                </div>
            )}
        </div>
    );
};

export default ProHeartRateMeasurement;

"use client";

import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * Hook to manage device motion sensors and permissions.
 */
export const useMotionSensor = (onMotion: (event: DeviceMotionEvent) => void) => {
  const [permissionStatus, setPermissionStatus] = useState<'default' | 'granted' | 'denied'>('default');
  const onMotionRef = useRef(onMotion);

  // Update ref when callback changes to avoid re-subscribing in useEffect
  useEffect(() => {
    onMotionRef.current = onMotion;
  }, [onMotion]);

  const requestPermission = useCallback(async () => {
    if (typeof DeviceMotionEvent !== 'undefined' && 'requestPermission' in DeviceMotionEvent && typeof (DeviceMotionEvent as any).requestPermission === 'function') {
      try {
        const response = await (DeviceMotionEvent as unknown as { requestPermission: () => Promise<'granted' | 'denied' | 'default'> }).requestPermission();
        setPermissionStatus(response);
        return response === 'granted';
      } catch (error) {
        console.error('Error requesting motion permission:', error);
        setPermissionStatus('denied');
        return false;
      }
    } else {
      // Non-iOS devices or devices that don't require explicit permission
      setPermissionStatus('granted');
      return true;
    }
  }, []);

  useEffect(() => {
    const handleMotion = (event: DeviceMotionEvent) => {
      onMotionRef.current(event);
    };

    if (permissionStatus === 'granted') {
      window.addEventListener('devicemotion', handleMotion);
    }

    return () => {
      window.removeEventListener('devicemotion', handleMotion);
    };
  }, [permissionStatus]);

  return {
    permissionStatus,
    requestPermission,
    isSupported: typeof window !== 'undefined' && 'DeviceMotionEvent' in window
  };
};

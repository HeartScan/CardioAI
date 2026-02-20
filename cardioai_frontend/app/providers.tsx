"use client";

import React from 'react';
import { ThemeProvider } from './theme-provider';
import { ErrorBoundary } from '@/app/error-boundary';
import { AnalyticsInit } from '@/app/analytics-init';
import { AnalyticsProvider } from '@/lib/analytics/AnalyticsProvider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
        <AnalyticsInit />
        <AnalyticsProvider>
          {children}
        </AnalyticsProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

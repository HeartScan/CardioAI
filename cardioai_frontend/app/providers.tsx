"use client";

import React, { Suspense, lazy } from 'react';
import { ThemeProvider } from 'next-themes';
import { ErrorBoundary } from './error-boundary';
import { AnalyticsInit } from './analytics-init';

// Lazy load AnalyticsProvider to reduce initial bundle size
const AnalyticsProvider = lazy(() => 
  import('@/lib/analytics/AnalyticsProvider').then(mod => ({
    default: mod.AnalyticsProvider
  }))
);

// Simple fallback component while analytics loads
const AnalyticsFallback = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>;
};

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
        <AnalyticsInit />
        <Suspense fallback={<AnalyticsFallback>{children}</AnalyticsFallback>}>
          <AnalyticsProvider>
            {children}
          </AnalyticsProvider>
        </Suspense>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

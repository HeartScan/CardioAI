export const getPlatform = () => {
  if (typeof window === 'undefined') return 'other';
  
  const userAgent = window.navigator.userAgent.toLowerCase();
  const platform = (window.navigator as any).platform?.toLowerCase() || '';
  
  if (/android/.test(userAgent) || /android/.test(platform)) {
    return 'android';
  } else if (/iphone|ipad|ipod/.test(userAgent) || /iphone|ipad|ipod/.test(platform)) {
    return 'ios';
  }
  
  return 'other';
};

export const getAppDownloadLink = (forceMobileFallback?: boolean) => {
  const platform = getPlatform();
  
  // DO NOT CHANGE THESE LINKS - Official app store URLs
  if (platform === 'android') {
    return "https://play.google.com/store/apps/details?id=heart.rate.monitor.ecg.scg.pulse.app";
  } else if (platform === 'ios') {
    return "https://apps.apple.com/us/app/heartscan-heart-rate-monitor/id1639306601";
  }
  
  if (forceMobileFallback) {
    // If we're on a mobile device but detection failed, default to Play Store as it's more likely 
    // to handle the redirect gracefully than a Branch link on a failing detector.
    return "https://play.google.com/store/apps/details?id=heart.rate.monitor.ecg.scg.pulse.app";
  }
  
  return "https://heartscan.app.link";
};

import { Linking } from 'react-native';

export class DeepLinkHandler {
  private static instance: DeepLinkHandler;
  private listeners: ((url: string) => void)[] = [];

  public static getInstance(): DeepLinkHandler {
    if (!DeepLinkHandler.instance) {
      DeepLinkHandler.instance = new DeepLinkHandler();
    }
    return DeepLinkHandler.instance;
  }

  constructor() {
    this.initialize();
  }

  private initialize() {
    // Handle app launch from deep link
    Linking.getInitialURL().then((url) => {
      if (url) {
        console.log('🔗 App launched with deep link:', url);
        this.handleDeepLink(url);
      }
    });

    // Handle deep links when app is already running
    Linking.addEventListener('url', (event) => {
      console.log('🔗 Deep link received:', event.url);
      this.handleDeepLink(event.url);
    });
  }

  private handleDeepLink(url: string) {
    console.log('🔗 Processing deep link:', url);

    // Parse the URL
    const parsedUrl = this.parseDeepLink(url);

    if (parsedUrl) {
      // Notify all listeners
      this.listeners.forEach(listener => {
        try {
          listener(url);
        } catch (error) {
          console.error('❌ Error in deep link listener:', error);
        }
      });
    }
  }

  private parseDeepLink(url: string): { scheme: string; path: string; params: Record<string, string> } | null {
    try {
      const urlObj = new URL(url);

      if (urlObj.protocol !== 'payvo:') {
        console.warn('⚠️ Unsupported deep link scheme:', urlObj.protocol);
        return null;
      }

      const params: Record<string, string> = {};
      urlObj.searchParams.forEach((value, key) => {
        params[key] = value;
      });

      return {
        scheme: urlObj.protocol.replace(':', ''),
        path: urlObj.pathname,
        params,
      };
    } catch (error) {
      console.error('❌ Failed to parse deep link:', url, error);
      return null;
    }
  }

  public addListener(listener: (url: string) => void) {
    this.listeners.push(listener);
  }

  public removeListener(listener: (url: string) => void) {
    const index = this.listeners.indexOf(listener);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  public removeAllListeners() {
    this.listeners = [];
  }

  // Helper method to handle auth-related deep links
  public handleAuthDeepLink(url: string): boolean {
    if (url.startsWith('payvo://auth') || 
        url.startsWith('payvo://reset-password') ||
        url.startsWith('ai.payvo.middleware://auth') || 
        url.startsWith('ai.payvo.middleware://reset-password')) {
      console.log('🔐 Auth deep link detected:', url);
      // The Supabase client will automatically handle these URLs
      return true;
    }
    return false;
  }
}

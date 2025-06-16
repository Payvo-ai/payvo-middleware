import { DeepLinkHandler } from './DeepLinkHandler';

export const initializeApp = () => {
  console.log('🚀 Initializing Payvo Middleware App...');
  
  // Initialize deep link handler
  console.log('🔗 Setting up deep link handler...');
  DeepLinkHandler.getInstance();
  
  console.log('✅ App initialization complete');
};

// Auto-initialize when this module is imported
initializeApp(); 
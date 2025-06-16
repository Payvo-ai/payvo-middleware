import AsyncStorage from '@react-native-async-storage/async-storage';
import {LocationData} from './LocationService';

export interface RoutingInitiateRequest {
  user_id: string;
  platform?: string;
  wallet_type?: string;
  device_id?: string;
  transaction_amount?: number;
  location?: LocationData;
}

export interface RoutingSessionResponse {
  success: boolean;
  data?: {
    session_id: string;
    predicted_mcc?: string;
    confidence?: number;
    prediction_method?: string;
    recommended_card?: {
      card_id: string;
      card_type: string;
      rewards_rate: number;
      estimated_savings: number;
    };
    analysis_details?: {
      location_analysis?: {
        predicted_mcc?: {
          mcc: string;
          confidence: number;
          source: string;
          details?: {
            nearby_stores?: Array<{
              name: string;
              types?: string[];
              rating?: number;
              distance?: number;
              source?: string;
              store_dimensions?: {
                width_meters?: number;
                length_meters?: number;
                area_sqm?: number;
                bounds?: {
                  northeast: {
                    lat: number;
                    lng: number;
                  };
                  southwest: {
                    lat: number;
                    lng: number;
                  };
                };
              };
            }>;
            detected_merchant?: {
              name: string;
              types?: string[];
              confidence?: number;
              store_dimensions?: {
                width_meters?: number;
                length_meters?: number;
                area_sqm?: number;
                bounds?: {
                  northeast: {
                    lat: number;
                    lng: number;
                  };
                  southwest: {
                    lat: number;
                    lng: number;
                  };
                };
              };
            };
          };
        };
      };
    };
    message?: string;
    timestamp?: string;
  };
  // Keep backward compatibility
  session_id?: string;
  predicted_mcc?: string;
  confidence?: number;
  prediction_method?: string;
  recommended_card?: {
    card_id: string;
    card_type: string;
    rewards_rate: number;
    estimated_savings: number;
  };
  analysis_details?: {
    location_analysis?: {
      predicted_mcc?: {
        mcc: string;
        confidence: number;
        source: string;
        details?: {
          nearby_stores?: Array<{
            name: string;
            types?: string[];
            rating?: number;
            distance?: number;
            source?: string;
            store_dimensions?: {
              width_meters?: number;
              length_meters?: number;
              area_sqm?: number;
              bounds?: {
                northeast: {
                  lat: number;
                  lng: number;
                };
                southwest: {
                  lat: number;
                  lng: number;
                };
              };
            };
          }>;
          detected_merchant?: {
            name: string;
            types?: string[];
            confidence?: number;
            store_dimensions?: {
              width_meters?: number;
              length_meters?: number;
              area_sqm?: number;
              bounds?: {
                northeast: {
                  lat: number;
                  lng: number;
                };
                southwest: {
                  lat: number;
                  lng: number;
                };
              };
            };
          };
        };
      };
    };
  };
  message?: string;
  timestamp?: string;
}

export interface RoutingStatusResponse {
  session_id: string;
  status: string;
  mcc_prediction?: {
    predicted_mcc: string;
    confidence: number;
    merchant_category: string;
  };
  selected_card?: {
    card_id: string;
    card_type: string;
    rewards_rate: number;
  };
  transaction_amount?: number;
  created_at: string;
  updated_at: string;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  timestamp: string;
  components: {
    routing_orchestrator: string;
    database: string;
    supabase: string;
  };
  cache_stats: {
    mcc_cache_size: number;
    location_cache_size: number;
    terminal_cache_size: number;
    wifi_cache_size: number;
    ble_cache_size: number;
  };
  system_info: {
    active_sessions: number;
    background_tasks: number;
  };
}

export interface HealthCheckAPIResponse {
  success: boolean;
  data: HealthCheckResponse;
  message: string;
}

export interface PaymentRequest {
  user_id: string;
  amount: number;
  platform: 'ios' | 'android';
  wallet_type: 'apple_pay' | 'google_pay';
  location?: LocationData;
  merchant_name?: string;
  terminal_id?: string;
  wifi_networks?: string[];
  ble_beacons?: string[];
}

export interface PaymentResponse {
  success: boolean;
  message: string;
  session_id: string;
  predicted_mcc?: string;
  merchant_category?: string;
  confidence?: number;
  error?: string;
  prediction_method?: string;
  recommended_cards?: string[];
  expires_at?: string;
  analysis_details?: {
    location_analysis?: {
      predicted_mcc?: {
        mcc: string;
        confidence: number;
        source: string;
        details?: {
          nearby_stores?: Array<{
            name: string;
            types?: string[];
            rating?: number;
            distance?: number;
            source?: string;
            store_dimensions?: {
              width_meters?: number;
              length_meters?: number;
              area_sqm?: number;
              bounds?: {
                northeast: {
                  lat: number;
                  lng: number;
                };
                southwest: {
                  lat: number;
                  lng: number;
                };
              };
            };
          }>;
          detected_merchant?: {
            name: string;
            types?: string[];
            confidence?: number;
            store_dimensions?: {
              width_meters?: number;
              length_meters?: number;
              area_sqm?: number;
              bounds?: {
                northeast: {
                  lat: number;
                  lng: number;
                };
                southwest: {
                  lat: number;
                  lng: number;
                };
              };
            };
          };
        };
      };
    };
  };
}

export interface MCCPredictionRequest {
  latitude: number;
  longitude: number;
  radius?: number;
  include_alternatives?: boolean;
  use_llm_enhancement?: boolean;
}

export interface MCCPredictionResponse {
  predicted_mcc: string;
  confidence: number;
  method: string;
  alternatives?: Array<{
    mcc: string;
    confidence: number;
    reason: string;
  }>;
  analysis_details?: any;
}

export interface BackgroundLocationUpdate {
  sessionId: string;
  userId: string;
  location: LocationData;
  mccPrediction?: {
    mcc: string;
    confidence: number;
    method: string;
    timestamp: number;
  };
  timestamp: number;
}

export interface StartBackgroundTrackingRequest {
  user_id: string;
  session_duration_minutes?: number;
  update_interval_seconds?: number;
  min_distance_filter_meters?: number;
}

export interface BackgroundTrackingResponse {
  session_id: string;
  user_id: string;
  start_time: string;
  expires_at: string;
  status: string;
  message: string;
}

export interface OptimalMCCResponse {
  mcc: string;
  confidence: number;
  method: string;
  location_count: number;
  session_age_minutes: number;
  last_prediction_minutes_ago: number;
}

export interface RoutingActivateRequest {
  location?: LocationData;
  terminal_id?: string;
  merchant_name?: string;
  wifi_networks?: Array<{
    ssid: string;
    bssid: string;
    signal_strength: number;
  }>;
  ble_beacons?: Array<{
    uuid: string;
    major: number;
    minor: number;
    rssi: number;
  }>;
  amount?: number;
  context_info?: any;
}

export interface TransactionHistoryItem {
  id: string;
  session_id: string;
  merchant_name?: string;
  predicted_mcc?: string;
  actual_mcc?: string;
  transaction_amount?: number;
  transaction_success?: boolean;
  prediction_confidence?: number;
  network_used?: string;
  terminal_id?: string;
  location_hash?: string;
  created_at: string;
  transaction_timestamp?: string;
  location?: {
    latitude?: number;
    longitude?: number;
    address?: string;
    city?: string;
    state?: string;
    country?: string;
    postal_code?: string;
  };
}

export interface TransactionHistoryResponse {
  success: boolean;
  data: {
    transactions: TransactionHistoryItem[];
    total_count: number;
    limit: number;
    offset: number;
    user_id: string;
  };
  error?: string;
}

class PayvoAPIService {
  private baseURL: string;
  private apiKey?: string;
  private currentSessionId: string | null = null;

  constructor() {
    // Use production URL by default, can be overridden
    this.baseURL = 'https://payvo-middleware-production.up.railway.app/api/v1';
    this.loadApiKey();
  }

  private async loadApiKey(): Promise<void> {
    try {
      const storedKey = await AsyncStorage.getItem('payvo_api_key');
      this.apiKey = storedKey || undefined;
    } catch (error) {
      console.error('Failed to load API key:', error);
    }
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseURL}${endpoint}`;
    await this.loadApiKey();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    try {
      // Create AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      console.error(`API Request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Routing API Methods
  async initiateRouting(params: RoutingInitiateRequest): Promise<RoutingSessionResponse> {
    const response = await this.makeRequest('/routing/initiate', {
      method: 'POST',
      body: JSON.stringify(params),
    });

    this.currentSessionId = response.session_id;
    return response as RoutingSessionResponse;
  }

  async activateRouting(sessionId: string, location: LocationData): Promise<RoutingSessionResponse> {
    const response = await this.makeRequest(`/routing/${sessionId}/activate`, {
      method: 'POST',
      body: JSON.stringify({ location }),
    });

    return response as RoutingSessionResponse;
  }

  async completeRouting(sessionId: string): Promise<RoutingSessionResponse> {
    const response = await this.makeRequest(`/routing/${sessionId}/complete`, {
      method: 'POST',
    });

    return response as RoutingSessionResponse;
  }

  async getRoutingStatus(sessionId: string): Promise<RoutingStatusResponse> {
    const response = await this.makeRequest(`/routing/${sessionId}/status`);
    return response as RoutingStatusResponse;
  }

  async cancelRouting(sessionId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.makeRequest(`/routing/${sessionId}/cancel`, {
      method: 'POST',
    });

    return response as { success: boolean; message: string };
  }

  // MCC Prediction API Methods
  async predictMCC(params: MCCPredictionRequest): Promise<MCCPredictionResponse> {
    const response = await this.makeRequest('/mcc/predict', {
      method: 'POST',
      body: JSON.stringify(params),
    });

    return response as MCCPredictionResponse;
  }

  // Background Location API Methods
  async startBackgroundTracking(params: StartBackgroundTrackingRequest): Promise<BackgroundTrackingResponse> {
    const response = await this.makeRequest('/background-location/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });

    return response as BackgroundTrackingResponse;
  }

  async updateBackgroundLocation(update: BackgroundLocationUpdate): Promise<any> {
    const response = await this.makeRequest('/background-location/update', {
      method: 'POST',
      body: JSON.stringify(update),
    });
    return response;
  }

  async getBackgroundSessionStatus(sessionId: string): Promise<any> {
    const response = await this.makeRequest(`/background-location/session/${sessionId}/status`);
    return response;
  }

  async getOptimalMCC(sessionId: string, latitude: number, longitude: number, radius: number): Promise<OptimalMCCResponse> {
    const response = await this.makeRequest(`/background-location/session/${sessionId}/optimal-mcc`, {
      method: 'POST',
      body: JSON.stringify({
        latitude,
        longitude,
        radius,
      }),
    });

    return response as OptimalMCCResponse;
  }

  async extendBackgroundSession(sessionId: string, additionalMinutes: number = 30): Promise<any> {
    const response = await this.makeRequest(`/background-location/session/${sessionId}/extend`, {
      method: 'POST',
      body: JSON.stringify({ additional_minutes: additionalMinutes }),
    });
    return response;
  }

  async stopBackgroundTracking(sessionId: string): Promise<any> {
    const response = await this.makeRequest(`/background-location/session/${sessionId}`, {
      method: 'DELETE',
    });
    return response;
  }

  async getUserBackgroundSessions(userId: string, activeOnly: boolean = false): Promise<any> {
    const params = new URLSearchParams();
    if (activeOnly) {
      params.append('active_only', 'true');
    }

    const queryString = params.toString();
    const endpoint = `/background-location/sessions/user/${userId}${queryString ? `?${queryString}` : ''}`;

    const response = await this.makeRequest(endpoint);
    return response;
  }

  // Test API Methods
  async testPaymentWithGPS(request: {
    user_id: string;
    latitude: number;
    longitude: number;
    platform?: string;
    wallet_type?: string;
    amount?: number;
    merchant_name?: string;
    accuracy?: number;
    altitude?: number;
    speed?: number;
    heading?: number;
  }): Promise<any> {
    const response = await this.makeRequest('/test/gps-payment', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response;
  }

  // Utility Methods
  async getHealthCheck(): Promise<HealthCheckAPIResponse> {
    const response = await this.makeRequest('/health');
    return response as HealthCheckAPIResponse;
  }

  async getMetrics(): Promise<any> {
    const response = await this.makeRequest('/metrics');
    return response;
  }

  async getMCCInfo(mccCode: string): Promise<any> {
    const response = await this.makeRequest(`/mcc/${mccCode}/info`);
    return response;
  }

  async getNetworkAcceptanceRates(): Promise<any> {
    const response = await this.makeRequest('/networks/acceptance');
    return response;
  }

  // Configuration Methods
  setBaseURL(url: string): void {
    this.baseURL = url;
    console.log('🔧 PayvoAPI base URL updated:', url);
  }

  async setAPIKey(key: string): Promise<void> {
    this.apiKey = key;
    try {
      await AsyncStorage.setItem('payvo_api_key', key);
      console.log('🔑 API key saved');
    } catch (error) {
      console.error('❌ Failed to save API key:', error);
    }
  }

  async clearAPIKey(): Promise<void> {
    this.apiKey = undefined;
    try {
      await AsyncStorage.removeItem('payvo_api_key');
      console.log('🗑️ API key cleared');
    } catch (error) {
      console.error('❌ Failed to clear API key:', error);
    }
  }

  getBaseURL(): string {
    return this.baseURL;
  }

  hasAPIKey(): boolean {
    return !!this.apiKey;
  }

  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }

  async getUserTransactionHistory(
    userId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<TransactionHistoryResponse> {
    try {
      const response = await this.makeRequest(
        `/users/${encodeURIComponent(userId)}/transactions?limit=${limit}&offset=${offset}`,
        {
          method: 'GET',
        }
      );

      return response;
    } catch (error) {
      console.error('❌ Get user transaction history failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const PayvoAPI = new PayvoAPIService();
export default PayvoAPI;


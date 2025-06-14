import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from 'react-native';
import {
  Button,
  ActivityIndicator,
  Chip,
  TextInput,
} from 'react-native-paper';
import {PayvoAPI, RoutingSessionResponse} from '../services/PayvoAPI';
import {useLocation} from '../hooks/useLocation';
import { useNotification } from '../components/NotificationProvider';

const TransactionScreen: React.FC = () => {
  const [userId, setUserId] = useState('test_user_001');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<RoutingSessionResponse | null>(null);
  const [status, setStatus] = useState<'idle' | 'pending' | 'activated' | 'completed' | 'failed'>('idle');
  const [error, setError] = useState<string | null>(null);

  const walletTypes = ['apple_pay', 'google_pay', 'samsung_pay'];
  const [selectedWallet, setSelectedWallet] = useState('apple_pay');

  const {
    location,
    error: locationError,
    isLoading: isLocationLoading,
    requestPermission,
    getCurrentLocation,
  } = useLocation();

  const { showNotification } = useNotification();

  // Helper functions to safely access session data
  const getPredictedMcc = (): string | undefined => {
    if (!sessionData) {
      return undefined;
    }

    // Log the complete response structure first
    console.log('🔍 COMPLETE sessionData:', JSON.stringify(sessionData, null, 2));

    // Based on backend response structure, the MCC is directly at root level
    const mcc = sessionData?.predicted_mcc ||
                sessionData?.data?.predicted_mcc;

    console.log('🔍 getPredictedMcc() - Final MCC value:', mcc);

    return mcc;
  };

  const getConfidence = (): number | undefined => {
    if (!sessionData) {
      return undefined;
    }

    // Backend returns confidence directly at root level
    const confidence = sessionData?.confidence ||
                      sessionData?.data?.confidence;

    console.log('🔍 getConfidence() - Final confidence value:', confidence);
    return confidence;
  };

  const getRecommendedCard = () => {
    if (!sessionData) {
      return undefined;
    }

    // Backend returns recommended_card directly at root level
    const card = sessionData?.recommended_card ||
                sessionData?.data?.recommended_card;

    console.log('🔍 getRecommendedCard() - Final card value:', card);
    return card;
  };

  const getMerchantInfo = () => {
    if (!sessionData) {
      return null;
    }

    // Try to get merchant info from analysis_details
    const merchantInfo =
      sessionData?.analysis_details?.location_analysis?.predicted_mcc?.details?.detected_merchant ||
      sessionData?.data?.analysis_details?.location_analysis?.predicted_mcc?.details?.detected_merchant;

    console.log('🔍 getMerchantInfo() - Final merchant info:', merchantInfo);

    return merchantInfo;
  };

  const getAnalysisDetails = () => {
    if (!sessionData) {
      return undefined;
    }

    // Backend returns analysis_details directly at root level
    const details = sessionData?.analysis_details ||
                   sessionData?.data?.analysis_details;

    console.log('🔍 getAnalysisDetails() - Final analysis details:', details);

    return details;
  };

  // Debug function to log complete structure
  const logCompleteStructure = (data: any, label: string) => {
    console.log(`🔍 ${label} - Complete structure:`);
    console.log(`🔍 ${label} - JSON:`, JSON.stringify(data, null, 2));
    if (data && typeof data === 'object') {
      console.log(`🔍 ${label} - Keys:`, Object.keys(data));
      if (data.data && typeof data.data === 'object') {
        console.log(`🔍 ${label}.data - Keys:`, Object.keys(data.data));
      }
    }
  };

  // Debug effect to log sessionData changes
  useEffect(() => {
    if (sessionData) {
      logCompleteStructure(sessionData, 'SessionData');
    }
  }, [sessionData]);

  useEffect(() => {
    // Request location permission when component mounts
    const requestLocation = async () => {
      try {
        const granted = await requestPermission();
        if (granted) {
          // Get initial location
          await getCurrentLocation();
        }
      } catch (err) {
        console.error('Error requesting location:', err);
      }
    };

    requestLocation();
  }, [requestPermission, getCurrentLocation]);

  const handleInitiatePayment = async () => {
    console.log('🚀 Starting payment session...');
    console.log('User ID:', userId);
    console.log('Amount:', amount);
    console.log('Selected wallet:', selectedWallet);
    console.log('Location available:', !!location);

    try {
      setLoading(true);
      setError(null);

      // Get current location
      const currentLocation = await getCurrentLocation();
      console.log('📍 Current location:', currentLocation);

      if (!currentLocation) {
        throw new Error('Location is required for payment');
      }

      console.log('📡 Making API call to initiate routing...');

      // Validate and format amount
      const numericAmount = parseFloat(amount);
      if (isNaN(numericAmount) || numericAmount <= 0) {
        throw new Error('Please enter a valid transaction amount');
      }

      console.log('💰 Formatted amount:', numericAmount.toFixed(2));

      const response = await PayvoAPI.initiateRouting({
        user_id: userId,
        platform: 'ios',
        wallet_type: selectedWallet,
        device_id: 'iphone_test_001',
        transaction_amount: parseFloat(numericAmount.toFixed(2)),
        location: currentLocation,
      });

      console.log('✅ API Response received:', response);
      console.log('Session ID from response:', response.session_id);
      console.log('Response data:', response.data);
      console.log('Session ID from data:', response.data?.session_id);

      const sessionId = response.session_id || response.data?.session_id;
      console.log('Final session ID to use:', sessionId);

      setCurrentSession(sessionId || null);
      setSessionData(response);
      setStatus('pending');

      console.log('✅ Session state updated successfully');
    } catch (err) {
      console.error('❌ Payment initiation failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to initiate payment');
      setStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const handleActivatePayment = async () => {
    console.log('🔥 Tap to Pay button clicked!');
    console.log('Current session:', currentSession);
    console.log('Loading state:', loading);
    console.log('Location available:', !!location);
    console.log('Status:', status);

    // Show notification instead of alert
    showNotification('Tap to Pay button clicked!', 'info', 2000);

    if (!currentSession) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Get current location
      const currentLocation = await getCurrentLocation();
      if (!currentLocation) {
        throw new Error('Location is required for payment');
      }

      const response = await PayvoAPI.activateRouting(currentSession, currentLocation);
      console.log('🔍 Activate Payment Response:', JSON.stringify(response, null, 2));
      console.log('🔍 Response predicted_mcc:', response.predicted_mcc);
      console.log('🔍 Response confidence:', response.confidence);
      console.log('🔍 Response recommended_card:', response.recommended_card);
      console.log('🔍 Response analysis_details:', response.analysis_details);
      console.log('🔍 Response data:', response.data);
      console.log('🔍 Response data predicted_mcc:', response.data?.predicted_mcc);
      console.log('🔍 Response data analysis_details:', response.data?.analysis_details);

      setSessionData(response);
      setStatus('activated'); // Changed from 'pending' to 'activated'

      // Add a small delay to ensure state is updated, then log helper function results
      setTimeout(() => {
        console.log('🔍 After setState - getPredictedMcc():', getPredictedMcc());
        console.log('🔍 After setState - getConfidence():', getConfidence());
        console.log('🔍 After setState - getRecommendedCard():', getRecommendedCard());
        console.log('🔍 After setState - getAnalysisDetails():', getAnalysisDetails());
        console.log('🔍 After setState - sessionData:', sessionData);
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate payment');
      setStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCompletePayment = async () => {
    if (!currentSession) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await PayvoAPI.completeRouting(currentSession);
      setSessionData(response);
      setStatus('completed');

      // Show success notification instead of popup
      showNotification('Transaction completed successfully!', 'success', 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to complete payment');
      setStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelPayment = async () => {
    console.log('🚫 Cancel button clicked!');
    console.log('Current session:', currentSession);
    console.log('Loading state:', loading);

    // Show notification instead of alert
    showNotification('Cancel button clicked!', 'info', 2000);

    if (!currentSession) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await PayvoAPI.cancelRouting(currentSession);
      setCurrentSession(null);
      setSessionData(null);
      setStatus('idle');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel payment');
    } finally {
      setLoading(false);
    }
  };

  const clearSession = () => {
    setCurrentSession(null);
    setSessionData(null);
    setAmount('');
  };

  if (isLocationLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" />
        <Text style={styles.text}>Getting your location...</Text>
      </View>
    );
  }

  if (locationError) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{locationError.message}</Text>
        <Button mode="contained" onPress={requestPermission} style={styles.button}>
          Enable Location
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* Transaction Setup Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>New Transaction</Text>
          </View>

          <View style={styles.cardContent}>
            <View style={styles.amountSection}>
              <Text style={styles.inputLabel}>Amount</Text>
              <View style={styles.amountInputContainer}>
                <Text style={styles.currencySymbol}>$</Text>
                <TextInput
                  value={amount}
                  onChangeText={setAmount}
                  style={styles.amountInput}
                  mode="flat"
                  keyboardType="numeric"
                  placeholder="0.00"
                  underlineColor="transparent"
                  activeUnderlineColor="transparent"
                />
              </View>
            </View>

            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>User ID</Text>
              <TextInput
                value={userId}
                onChangeText={setUserId}
                style={styles.textInput}
                mode="flat"
                placeholder="Enter user ID"
                underlineColor="transparent"
                activeUnderlineColor="transparent"
              />
            </View>

            <View style={styles.walletSection}>
              <Text style={styles.inputLabel}>Payment Method</Text>
              <View style={styles.walletGrid}>
                {walletTypes.map((type) => (
                  <View
                    key={type}
                    style={[
                      styles.walletOption,
                      selectedWallet === type && styles.walletOptionSelected,
                    ]}
                    onTouchEnd={() => setSelectedWallet(type)}>
                    <Text style={[
                      styles.walletText,
                      selectedWallet === type && styles.walletTextSelected,
                    ]}>
                      {type.replace('_', ' ').toUpperCase()}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
        </View>

        {/* Payment Actions Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Payment Flow</Text>
          </View>

          <View style={styles.cardContent}>
            {status === 'idle' && (
              <Button
                mode="contained"
                onPress={handleInitiatePayment}
                loading={loading}
                disabled={loading || !location}
                style={styles.primaryButton}
                labelStyle={styles.primaryButtonText}>
                Initialize Payment Session
              </Button>
            )}

            {status === 'pending' && (
              <View style={styles.actionGroup}>
                <Button
                  mode="contained"
                  onPress={handleActivatePayment}
                  loading={loading}
                  disabled={loading || !location}
                  style={styles.primaryButton}
                  labelStyle={styles.primaryButtonText}>
                  🚀 Tap to Pay
                </Button>
                <Button
                  mode="outlined"
                  onPress={handleCancelPayment}
                  disabled={loading}
                  style={styles.secondaryButton}
                  labelStyle={styles.secondaryButtonText}>
                  Cancel Transaction
                </Button>
              </View>
            )}

            {status === 'activated' && (
              <View style={styles.actionGroup}>
                <View style={styles.successIndicator}>
                  <View style={styles.successIcon}>
                    <Text style={styles.successIconText}>✓</Text>
                  </View>
                  <Text style={styles.successText}>Payment Activated</Text>
                </View>
                <Button
                  mode="outlined"
                  onPress={handleCancelPayment}
                  disabled={loading}
                  style={styles.secondaryButton}
                  labelStyle={styles.secondaryButtonText}>
                  Cancel Transaction
                </Button>
              </View>
            )}

            <Button
              mode="contained"
              onPress={handleCompletePayment}
              loading={loading}
              disabled={!currentSession || status === 'idle'}
              style={[styles.primaryButton, (!currentSession || status === 'idle') && styles.disabledButton]}
              labelStyle={styles.primaryButtonText}>
              Complete Transaction
            </Button>
          </View>
        </View>

        {/* Session Details Card */}
        {currentSession && (status === 'activated' || status === 'completed') && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Session Information</Text>
            </View>

            <View style={styles.cardContent}>
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Session ID</Text>
                <Text style={styles.detailValue}>{currentSession}</Text>
              </View>

              {/* MCC Display - Show actual data */}
              {sessionData && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>MCC (Merchant Category Code)</Text>
                  {getPredictedMcc() ? (
                    <Chip style={styles.detailChip} textStyle={styles.detailChipText}>
                      {getPredictedMcc()}
                    </Chip>
                  ) : (
                    <Text style={styles.detailValue}>Not available</Text>
                  )}
                </View>
              )}

              {/* Merchant Information - Show actual data */}
              {sessionData && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Merchant Information</Text>
                  <View style={styles.merchantInfoContainer}>
                    {(() => {
                      const merchantInfo = getMerchantInfo();
                      if (merchantInfo) {
                        return (
                          <>
                            <Text style={styles.merchantInfoName}>
                              {merchantInfo.name}
                            </Text>
                            {merchantInfo.types && (
                              <Text style={styles.merchantInfoTypes}>
                                {merchantInfo.types.join(' • ')}
                              </Text>
                            )}
                            {merchantInfo.confidence && (
                              <Text style={styles.merchantInfoConfidence}>
                                Confidence: {(merchantInfo.confidence * 100).toFixed(1)}%
                              </Text>
                            )}
                          </>
                        );
                      } else {
                        return <Text style={styles.detailValue}>Not available</Text>;
                      }
                    })()}
                  </View>
                </View>
              )}

              {/* Prediction Confidence */}
              {sessionData && getConfidence() && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Prediction Confidence</Text>
                  <Text style={styles.detailValue}>
                    {((getConfidence() || 0) * 100).toFixed(1)}%
                  </Text>
                </View>
              )}

              {/* Recommended Card */}
              {sessionData && getRecommendedCard() && (
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>Recommended Card</Text>
                  <Text style={styles.detailValue}>{getRecommendedCard()?.card_type || 'Unknown'}</Text>
                </View>
              )}

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Transaction Status</Text>
                <Chip
                  style={[styles.statusChip, status === 'completed' ? styles.statusChipCompleted : styles.statusChipActivated]}
                  textStyle={styles.statusChipText}>
                  {status.toUpperCase()}
                </Chip>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Amount</Text>
                <Text style={styles.detailValueAmount}>${amount}</Text>
              </View>

              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Payment Method</Text>
                <Text style={styles.detailValue}>{selectedWallet.replace('_', ' ').toUpperCase()}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Debug Card - Show raw API response */}
        {sessionData && (status === 'activated' || status === 'completed') && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Debug: Raw API Response</Text>
            </View>
            <View style={styles.cardContent}>
              <Text style={styles.debugText}>
                {JSON.stringify(sessionData, null, 2)}
              </Text>
            </View>
          </View>
        )}

        {/* Info Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>How It Works</Text>
          </View>
          <View style={styles.cardContent}>
            <View style={styles.infoItem}>
              <Text style={styles.infoNumber}>1</Text>
              <Text style={styles.infoText}>Initialize payment session with transaction details</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoNumber}>2</Text>
              <Text style={styles.infoText}>AI detects merchant location and category in real-time</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoNumber}>3</Text>
              <Text style={styles.infoText}>System selects optimal card for maximum rewards</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoNumber}>4</Text>
              <Text style={styles.infoText}>Complete transaction with intelligent routing</Text>
            </View>
          </View>
        </View>
      </ScrollView>

      {/* Loading Overlay */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingCard}>
            <ActivityIndicator size="large" color="#2742d5" />
            <Text style={styles.loadingText}>Processing Transaction...</Text>
          </View>
        </View>
      )}

      {/* Error Overlay */}
      {error && (
        <View style={styles.errorOverlay}>
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>Transaction Error</Text>
            <Text style={styles.errorMessage}>{error}</Text>
            <Button
              mode="contained"
              onPress={clearSession}
              style={styles.errorButton}
              labelStyle={styles.errorButtonText}>
              Try Again
            </Button>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e293b',
  },
  cardContent: {
    gap: 16,
  },
  amountSection: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  amountInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    paddingHorizontal: 16,
  },
  currencySymbol: {
    fontSize: 18,
    fontWeight: '600',
    color: '#64748b',
    marginRight: 8,
  },
  amountInput: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    backgroundColor: 'transparent',
  },
  inputSection: {
    marginBottom: 20,
  },
  textInput: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
  },
  walletSection: {
    marginBottom: 20,
  },
  walletGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  walletOption: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f8fafc',
    borderWidth: 2,
    borderColor: '#e2e8f0',
    borderRadius: 12,
  },
  walletOptionSelected: {
    backgroundColor: '#eff6ff',
    borderColor: '#3b82f6',
  },
  walletText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748b',
    textAlign: 'center',
  },
  walletTextSelected: {
    color: '#3b82f6',
  },
  actionGroup: {
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#2742d5',
    borderRadius: 12,
    paddingVertical: 4,
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderColor: '#e2e8f0',
    borderWidth: 2,
    borderRadius: 12,
    paddingVertical: 4,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#64748b',
  },
  disabledButton: {
    backgroundColor: '#94a3b8',
  },
  successIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#f0fdf4',
    borderRadius: 12,
    marginBottom: 16,
  },
  successIcon: {
    backgroundColor: '#22c55e',
    width: 24,
    height: 24,
    borderRadius: 12,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  successIconText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#ffffff',
  },
  successText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#22c55e',
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
    flex: 1,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
    textAlign: 'right',
  },
  detailValueAmount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#22c55e',
    textAlign: 'right',
  },
  detailChip: {
    backgroundColor: '#3b82f6',
  },
  detailChipText: {
    color: '#ffffff',
    fontSize: 12,
  },
  merchantInfoContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  merchantInfoName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3b82f6',
    textAlign: 'right',
    marginBottom: 4,
  },
  merchantInfoTypes: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'right',
    marginBottom: 4,
  },
  merchantInfoConfidence: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'right',
  },
  statusChip: {
    alignSelf: 'flex-end',
  },
  statusChipActivated: {
    backgroundColor: '#f59e0b',
  },
  statusChipCompleted: {
    backgroundColor: '#22c55e',
  },
  statusChipText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  debugText: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#64748b',
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 8,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  infoNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#3b82f6',
    backgroundColor: '#eff6ff',
    width: 32,
    height: 32,
    borderRadius: 16,
    textAlign: 'center',
    lineHeight: 32,
    marginRight: 16,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingCard: {
    backgroundColor: '#ffffff',
    padding: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748b',
    fontWeight: '600',
  },
  errorOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorCard: {
    backgroundColor: '#ffffff',
    padding: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    margin: 20,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ef4444',
    marginBottom: 12,
    textAlign: 'center',
  },
  errorMessage: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  errorButton: {
    backgroundColor: '#ef4444',
    borderRadius: 12,
  },
  errorButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  text: {
    fontSize: 16,
    color: '#64748b',
  },
  errorText: {
    fontSize: 16,
    color: '#ef4444',
    textAlign: 'center',
    marginBottom: 20,
  },
  button: {
    borderRadius: 12,
  },
});

export default TransactionScreen;

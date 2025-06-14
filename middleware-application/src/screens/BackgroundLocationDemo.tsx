import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Switch,
  TextInput,
} from 'react-native';
import { useBackgroundLocation } from '../hooks/useBackgroundLocation';
import { PayvoAPI } from '../services/PayvoAPI';
import { useAuth } from '../contexts/AuthContext';

const BackgroundLocationDemo: React.FC = () => {
  const [userId, setUserId] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [config, setConfig] = useState({
    updateInterval: 4000, // 4 seconds
    minDistanceFilter: 5, // 5 meters
    sessionDuration: 30, // 30 minutes
    enableWhenClosed: true,
  });

  const { getUserId } = useAuth();

  const {
    currentSession,
    recentPredictions,
    startTracking,
    stopTracking,
    getOptimalMCC,
    extendSession,
    refreshSessionStatus,
    isSessionValid,
    isTracking,
    hasActiveSession,
    sessionId,
    locationsCount,
    lastUpdate,
    error,
  } = useBackgroundLocation(userId, config);

  const [optimalMCC, setOptimalMCC] = useState<{
    mcc: string;
    confidence: number;
    method: string;
  } | null>(null);

  const [userSessions, setUserSessions] = useState<any[]>([]);

  // Initialize user ID from authenticated user
  useEffect(() => {
    const initializeUserId = async () => {
      try {
        const authenticatedUserId = await getUserId();
        setUserId(authenticatedUserId);
        console.log('🔐 Background Location - Initialized user ID from auth:', authenticatedUserId);
      } catch (initError) {
        console.error('❌ Background Location - Failed to get authenticated user ID:', initError);
      }
    };

    initializeUserId();
  }, [getUserId]);

  // Load user sessions on mount
  const loadUserSessions = useCallback(async () => {
    try {
      const response = await PayvoAPI.getUserBackgroundSessions(userId, false);
      setUserSessions(response.sessions || []);
    } catch (loadError) {
      console.error('Failed to load user sessions:', loadError);
    }
  }, [userId]);

  useEffect(() => {
    loadUserSessions();
  }, [loadUserSessions]);

  const handleStartTracking = async () => {
    try {
      const newSessionId = await startTracking();
      if (newSessionId) {
        Alert.alert('Success', `Background tracking started!\nSession ID: ${newSessionId}`);
        await loadUserSessions();
      } else {
        Alert.alert('Error', 'Failed to start background tracking');
      }
    } catch (startError) {
      Alert.alert('Error', startError instanceof Error ? startError.message : 'Unknown error');
    }
  };

  const handleStopTracking = async () => {
    try {
      await stopTracking();
      Alert.alert('Success', 'Background tracking stopped');
      await loadUserSessions();
    } catch (stopError) {
      Alert.alert('Error', stopError instanceof Error ? stopError.message : 'Unknown error');
    }
  };

  const handleGetOptimalMCC = async () => {
    try {
      const result = await getOptimalMCC();
      setOptimalMCC(result);
      if (result) {
        Alert.alert(
          'Optimal MCC Found',
          `MCC: ${result.mcc}\nConfidence: ${(result.confidence * 100).toFixed(1)}%\nMethod: ${result.method}`
        );
      } else {
        Alert.alert('No Data', 'No optimal MCC available yet');
      }
    } catch (mccError) {
      Alert.alert('Error', mccError instanceof Error ? mccError.message : 'Unknown error');
    }
  };

  const handleExtendSession = async () => {
    try {
      const success = await extendSession(30);
      if (success) {
        Alert.alert('Success', 'Session extended by 30 minutes');
      } else {
        Alert.alert('Error', 'Failed to extend session');
      }
    } catch (extendError) {
      Alert.alert('Error', extendError instanceof Error ? extendError.message : 'Unknown error');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshSessionStatus();
      await loadUserSessions();
    } catch (refreshError) {
      console.error('Refresh failed:', refreshError);
    } finally {
      setRefreshing(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000 / 60); // minutes
    return `${duration} min`;
  };

  const getMCCDescription = (mcc: string) => {
    const mccMap: { [key: string]: string } = {
      '5411': 'Grocery Stores',
      '5812': 'Eating Places/Restaurants',
      '5541': 'Service Stations',
      '5999': 'Miscellaneous Retail',
      '8021': 'Dentists',
      '7011': 'Hotels/Motels',
      '5311': 'Department Stores',
      '4111': 'Transportation/Taxi',
    };
    return mccMap[mcc] || `MCC ${mcc}`;
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      <Text style={styles.title}>Background Location Tracking</Text>
      <Text style={styles.subtitle}>Continuous MCC Prediction & Session Management</Text>

      {/* Configuration Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Configuration</Text>

        <View style={styles.configRow}>
          <Text style={styles.configLabel}>User ID:</Text>
          <TextInput
            style={[styles.configInput, styles.readOnlyInput]}
            value={userId}
            onChangeText={() => {}} // No-op function to prevent changes
            placeholder="Loading username..."
            editable={false}
          />
          <Text style={styles.configHelper}>✓ Auto-set</Text>
        </View>

        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Update Interval:</Text>
          <TextInput
            style={styles.configInput}
            value={config.updateInterval.toString()}
            onChangeText={(text) => setConfig(prev => ({ ...prev, updateInterval: parseInt(text, 10) || 4000 }))}
            placeholder="4000"
            keyboardType="numeric"
          />
          <Text style={styles.configUnit}>ms</Text>
        </View>

        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Min Distance Filter:</Text>
          <TextInput
            style={styles.configInput}
            value={config.minDistanceFilter.toString()}
            onChangeText={(text) => setConfig(prev => ({ ...prev, minDistanceFilter: parseInt(text, 10) || 5 }))}
            placeholder="5"
            keyboardType="numeric"
          />
          <Text style={styles.configUnit}>m</Text>
        </View>

        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Session Duration:</Text>
          <TextInput
            style={styles.configInput}
            value={config.sessionDuration.toString()}
            onChangeText={(text) => setConfig(prev => ({ ...prev, sessionDuration: parseInt(text, 10) || 30 }))}
            placeholder="30"
            keyboardType="numeric"
          />
          <Text style={styles.configUnit}>min</Text>
        </View>

        <View style={styles.configRow}>
          <Text style={styles.configLabel}>Enable When Closed:</Text>
          <Switch
            value={config.enableWhenClosed}
            onValueChange={(value) => setConfig(prev => ({ ...prev, enableWhenClosed: value }))}
          />
        </View>
      </View>

      {/* Status Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Current Status</Text>

        <View style={styles.statusGrid}>
          <View style={[styles.statusCard, isTracking ? styles.statusActive : styles.statusInactive]}>
            <Text style={styles.statusLabel}>Tracking</Text>
            <Text style={styles.statusValue}>{isTracking ? 'Active' : 'Inactive'}</Text>
          </View>

          <View style={[styles.statusCard, hasActiveSession ? styles.statusActive : styles.statusInactive]}>
            <Text style={styles.statusLabel}>Session</Text>
            <Text style={styles.statusValue}>{hasActiveSession ? 'Active' : 'None'}</Text>
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Locations</Text>
            <Text style={styles.statusValue}>{locationsCount}</Text>
          </View>

          <View style={styles.statusCard}>
            <Text style={styles.statusLabel}>Valid</Text>
            <Text style={styles.statusValue}>{isSessionValid ? 'Yes' : 'No'}</Text>
          </View>
        </View>

        {sessionId && (
          <View style={styles.sessionInfo}>
            <Text style={styles.sessionLabel}>Session ID:</Text>
            <Text style={styles.sessionValue}>{sessionId}</Text>
          </View>
        )}

        {lastUpdate && (
          <View style={styles.sessionInfo}>
            <Text style={styles.sessionLabel}>Last Update:</Text>
            <Text style={styles.sessionValue}>{lastUpdate.toLocaleTimeString()}</Text>
          </View>
        )}

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>Error: {error}</Text>
          </View>
        )}
      </View>

      {/* Controls Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Controls</Text>

        <View style={styles.buttonGrid}>
          <TouchableOpacity
            style={[styles.button, isTracking ? styles.buttonDanger : styles.buttonPrimary]}
            onPress={isTracking ? handleStopTracking : handleStartTracking}
          >
            <Text style={styles.buttonText}>
              {isTracking ? 'Stop Tracking' : 'Start Tracking'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={handleGetOptimalMCC}
            disabled={!hasActiveSession}
          >
            <Text style={styles.buttonText}>Get Optimal MCC</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={handleExtendSession}
            disabled={!hasActiveSession}
          >
            <Text style={styles.buttonText}>Extend Session</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={handleRefresh}
          >
            <Text style={styles.buttonText}>Refresh Status</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Current Session Details */}
      {currentSession && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Current Session Details</Text>

          <View style={styles.sessionDetails}>
            <Text style={styles.detailRow}>
              <Text style={styles.detailLabel}>Start Time: </Text>
              <Text style={styles.detailValue}>{currentSession.startTime.toLocaleString()}</Text>
            </Text>

            <Text style={styles.detailRow}>
              <Text style={styles.detailLabel}>Expires At: </Text>
              <Text style={styles.detailValue}>{currentSession.expiresAt.toLocaleString()}</Text>
            </Text>

            <Text style={styles.detailRow}>
              <Text style={styles.detailLabel}>Duration: </Text>
              <Text style={styles.detailValue}>
                {formatDuration(currentSession.startTime.toISOString())}
              </Text>
            </Text>

            <Text style={styles.detailRow}>
              <Text style={styles.detailLabel}>Location Count: </Text>
              <Text style={styles.detailValue}>{currentSession.locationCount}</Text>
            </Text>
          </View>
        </View>
      )}

      {/* Optimal MCC */}
      {optimalMCC && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Optimal MCC Prediction</Text>

          <View style={styles.mccCard}>
            <Text style={styles.mccCode}>{optimalMCC.mcc}</Text>
            <Text style={styles.mccDescription}>{getMCCDescription(optimalMCC.mcc)}</Text>
            <Text style={styles.mccConfidence}>
              Confidence: {(optimalMCC.confidence * 100).toFixed(1)}%
            </Text>
            <Text style={styles.mccMethod}>Method: {optimalMCC.method}</Text>
          </View>
        </View>
      )}

      {/* Recent Predictions */}
      {recentPredictions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Predictions ({recentPredictions.length})</Text>

          {recentPredictions.slice(-5).reverse().map((prediction, index) => (
            <View key={index} style={styles.predictionCard}>
              <View style={styles.predictionHeader}>
                <Text style={styles.predictionTime}>
                  {new Date(prediction.timestamp).toLocaleTimeString()}
                </Text>
                <Text style={styles.predictionAccuracy}>
                  ±{prediction.accuracy.toFixed(1)}m
                </Text>
              </View>

              <Text style={styles.predictionLocation}>
                {prediction.location.latitude.toFixed(6)}, {prediction.location.longitude.toFixed(6)}
              </Text>

              {prediction.mccPrediction && (
                <View style={styles.predictionMCC}>
                  <Text style={styles.predictionMCCCode}>
                    MCC: {prediction.mccPrediction.mcc}
                  </Text>
                  <Text style={styles.predictionMCCConfidence}>
                    {(prediction.mccPrediction.confidence * 100).toFixed(1)}%
                  </Text>
                </View>
              )}
            </View>
          ))}
        </View>
      )}

      {/* User Sessions History */}
      {userSessions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Session History ({userSessions.length})</Text>

          {userSessions.slice(0, 5).map((session, index) => (
            <View key={index} style={styles.sessionCard}>
              <View style={styles.sessionCardHeader}>
                <Text style={styles.sessionCardId}>
                  {session.session_id.substring(0, 16)}...
                </Text>
                <Text style={[
                  styles.sessionCardStatus,
                  session.is_active ? styles.sessionActive : styles.sessionInactive,
                ]}>
                  {session.is_active ? 'Active' : 'Inactive'}
                </Text>
              </View>

              <Text style={styles.sessionCardDetail}>
                Started: {formatDate(session.start_time)}
              </Text>

              <Text style={styles.sessionCardDetail}>
                Duration: {formatDuration(session.start_time, session.expires_at)}
              </Text>

              <Text style={styles.sessionCardDetail}>
                Locations: {session.location_count}
              </Text>
            </View>
          ))}
        </View>
      )}

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Background location tracking enables continuous MCC prediction
        </Text>
        <Text style={styles.footerText}>
          Perfect for tap-to-pay optimization and merchant detection
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 5,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    color: '#666',
  },
  section: {
    backgroundColor: 'white',
    margin: 10,
    padding: 15,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  configRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  configLabel: {
    flex: 1,
    fontSize: 14,
    color: '#666',
  },
  configInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    padding: 8,
    fontSize: 14,
  },
  configUnit: {
    marginLeft: 5,
    fontSize: 14,
    color: '#666',
  },
  configHelper: {
    marginLeft: 5,
    fontSize: 12,
    color: '#999',
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statusCard: {
    width: '48%',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
  },
  statusActive: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4caf50',
    borderWidth: 1,
  },
  statusInactive: {
    backgroundColor: '#ffeaea',
    borderColor: '#f44336',
    borderWidth: 1,
  },
  statusLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  sessionInfo: {
    flexDirection: 'row',
    marginTop: 10,
  },
  sessionLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 10,
  },
  sessionValue: {
    fontSize: 14,
    color: '#333',
    fontFamily: 'monospace',
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    padding: 10,
    borderRadius: 5,
    marginTop: 10,
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 14,
  },
  buttonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  button: {
    width: '48%',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  buttonPrimary: {
    backgroundColor: '#2196f3',
  },
  buttonSecondary: {
    backgroundColor: '#757575',
  },
  buttonDanger: {
    backgroundColor: '#f44336',
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  sessionDetails: {
    backgroundColor: '#f9f9f9',
    padding: 10,
    borderRadius: 5,
  },
  detailRow: {
    marginBottom: 5,
  },
  detailLabel: {
    fontWeight: 'bold',
    color: '#666',
  },
  detailValue: {
    color: '#333',
  },
  mccCard: {
    backgroundColor: '#e3f2fd',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
  },
  mccCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1976d2',
    marginBottom: 5,
  },
  mccDescription: {
    fontSize: 16,
    color: '#333',
    marginBottom: 5,
  },
  mccConfidence: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  mccMethod: {
    fontSize: 12,
    color: '#999',
  },
  predictionCard: {
    backgroundColor: '#f9f9f9',
    padding: 10,
    borderRadius: 5,
    marginBottom: 8,
  },
  predictionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  predictionTime: {
    fontSize: 12,
    color: '#666',
  },
  predictionAccuracy: {
    fontSize: 12,
    color: '#999',
  },
  predictionLocation: {
    fontSize: 11,
    color: '#333',
    fontFamily: 'monospace',
    marginBottom: 5,
  },
  predictionMCC: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  predictionMCCCode: {
    fontSize: 12,
    color: '#1976d2',
    fontWeight: 'bold',
  },
  predictionMCCConfidence: {
    fontSize: 12,
    color: '#4caf50',
  },
  sessionCard: {
    backgroundColor: '#f9f9f9',
    padding: 10,
    borderRadius: 5,
    marginBottom: 8,
  },
  sessionCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  sessionCardId: {
    fontSize: 12,
    color: '#333',
    fontFamily: 'monospace',
  },
  sessionCardStatus: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  sessionActive: {
    color: '#4caf50',
  },
  sessionInactive: {
    color: '#f44336',
  },
  sessionCardDetail: {
    fontSize: 11,
    color: '#666',
    marginBottom: 2,
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
    marginBottom: 5,
  },
  readOnlyInput: {
    backgroundColor: '#f9f9f9',
  },
});

export default BackgroundLocationDemo;

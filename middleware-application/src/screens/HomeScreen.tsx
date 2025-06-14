import React, {useState, useEffect} from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
} from 'react-native';
import {
  Button,
  Chip,
  Text,
  ActivityIndicator,
} from 'react-native-paper';
import {PayvoAPI, HealthCheckResponse} from '../services/PayvoAPI';
import { useNotification } from '../components/NotificationProvider';

const HomeScreen: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const { showNotification } = useNotification();

  const loadHealthData = React.useCallback(async () => {
    try {
      setConnectionStatus('checking');
      const healthData = await PayvoAPI.getHealthCheck();

      if (healthData) {
        setHealth(healthData);
        setConnectionStatus('connected');
      } else {
        // Create a mock health response for error state
        setHealth({
          status: 'error',
          version: 'unknown',
          timestamp: new Date().toISOString(),
          components: {
            database: 'down',
            routing_orchestrator: 'down',
            supabase: 'down',
          },
          cache_stats: {
            mcc_cache_size: 0,
            location_cache_size: 0,
            terminal_cache_size: 0,
            wifi_cache_size: 0,
            ble_cache_size: 0,
          },
          system_info: {
            active_sessions: 0,
            background_tasks: 0,
          },
        });
        setConnectionStatus('disconnected');
      }
    } catch (error) {
      console.error('Health check failed:', error);
      // Create a mock health response for error state with proper structure
      setHealth({
        status: 'error',
        version: 'unknown',
        timestamp: new Date().toISOString(),
        components: {
          database: 'down',
          routing_orchestrator: 'down',
          supabase: 'down',
        },
        cache_stats: {
          mcc_cache_size: 0,
          location_cache_size: 0,
          terminal_cache_size: 0,
          wifi_cache_size: 0,
          ble_cache_size: 0,
        },
        system_info: {
          active_sessions: 0,
          background_tasks: 0,
        },
      });
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  }, []);

  const testConnection = async () => {
    try {
      setLoading(true);
      // Test connection by calling health check
      await PayvoAPI.getHealthCheck();
      setConnectionStatus('connected');
      showNotification('✅ Connection successful!', 'success', 2000);
    } catch (error) {
      setConnectionStatus('disconnected');
      showNotification('❌ Connection failed', 'error', 3000);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealthData();
  }, [loadHealthData]);

  const getStatusColor = (status: string | { status: string }) => {
    const statusValue = typeof status === 'object' ? status.status : status;
    switch (statusValue?.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'up':
        return '#4CAF50';
      case 'unhealthy':
      case 'disconnected':
      case 'down':
        return '#F44336';
      default:
        return '#FF9800';
    }
  };

  const getConnectionChipColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return '#4CAF50';
      case 'disconnected':
        return '#F44336';
      default:
        return '#FF9800';
    }
  };

  if (loading && !health) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2742d5" />
        <Text style={styles.loadingText}>Connecting to Payvo Middleware...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* System Status Card */}
      <View style={styles.card}>
        {/* Stats Section */}
        <View style={styles.statsSection}>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statValue}>
                  {connectionStatus === 'connected' ? '✓' : '✗'}
                </Text>
              </View>
              <Text style={styles.statLabel}>Connection</Text>
            </View>

            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statValue}>
                  {health ? health.status === 'healthy' ? '100%' : '0%' : '...'}
                </Text>
              </View>
              <Text style={styles.statLabel}>Health</Text>
            </View>

            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statValue}>
                  {health ? health.version : '...'}
                </Text>
              </View>
              <Text style={styles.statLabel}>Version</Text>
            </View>
          </View>
        </View>

        {/* Connection Status Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Connection Status</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.statusContainer}>
                <Chip
                  style={[styles.statusChip, {backgroundColor: getConnectionChipColor()}]}
                  textStyle={styles.chipText}>
                  {connectionStatus === 'connected' ? 'Connected' :
                   connectionStatus === 'disconnected' ? 'Disconnected' : 'Unknown'}
                </Chip>
              </View>
              <Button
                mode="contained"
                onPress={testConnection}
                style={styles.primaryButton}
                labelStyle={styles.buttonText}
                loading={loading}>
                Test Connection
              </Button>
            </View>
          </View>
        </View>

        {/* Health Status Card */}
        {health && (
          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>System Health</Text>
                <Text style={styles.cardSubtitle}>Middleware Status: v{health.version}</Text>
              </View>
              <View style={styles.cardContent}>
                <View style={styles.healthGrid}>
                  <View style={styles.healthItem}>
                    <Text style={styles.healthLabel}>Overall Status</Text>
                    <Chip
                      style={[styles.healthChip, {backgroundColor: getStatusColor(health.status)}]}
                      textStyle={styles.chipText}>
                      {health.status}
                    </Chip>
                  </View>

                  <View style={styles.healthItem}>
                    <Text style={styles.healthLabel}>Database</Text>
                    <Chip
                      style={[styles.healthChip, {backgroundColor: getStatusColor(health.components?.database || 'unknown')}]}
                      textStyle={styles.chipText}>
                      {health.components?.database || 'unknown'}
                    </Chip>
                  </View>

                  <View style={styles.healthItem}>
                    <Text style={styles.healthLabel}>Routing Service</Text>
                    <Chip
                      style={[styles.healthChip, {backgroundColor: getStatusColor(health.components?.routing_orchestrator || 'unknown')}]}
                      textStyle={styles.chipText}>
                      {health.components?.routing_orchestrator || 'unknown'}
                    </Chip>
                  </View>

                  <View style={styles.healthItem}>
                    <Text style={styles.healthLabel}>Supabase</Text>
                    <Chip
                      style={[styles.healthChip, {backgroundColor: getStatusColor(health.components?.supabase || 'unknown')}]}
                      textStyle={styles.chipText}>
                      {health.components?.supabase || 'unknown'}
                    </Chip>
                  </View>
                </View>

                <Text style={styles.timestamp}>
                  Last updated: {new Date(health.timestamp).toLocaleString()}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Service Information Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Service Information</Text>
              <Text style={styles.cardSubtitle}>Available Features & Capabilities</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.featureList}>
                <Text style={styles.featureItem}>• MCC Prediction Engine</Text>
                <Text style={styles.featureItem}>• Card Routing Optimization</Text>
                <Text style={styles.featureItem}>• Transaction Analytics</Text>
                <Text style={styles.featureItem}>• Real-time Performance Monitoring</Text>
              </View>

              <Button
                mode="outlined"
                onPress={() => showNotification('Visit http://localhost:8000/docs for complete API documentation', 'info', 4000)}
                style={styles.secondaryButton}
                labelStyle={styles.secondaryButtonText}>
                View API Docs
              </Button>
            </View>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#64748b',
    fontFamily: 'Inter',
  },
  statsSection: {
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#afafaf',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  statIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2742d5',
    fontFamily: 'Inter',
  },
  statLabel: {
    fontSize: 14,
    color: '#676767',
    fontFamily: 'Inter',
    textAlign: 'center',
  },
  cardContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    shadowColor: '#afafaf',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  cardHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    fontFamily: 'Inter',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#676767',
    fontFamily: 'Inter',
  },
  cardContent: {
    padding: 20,
  },
  statusContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  statusChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  chipText: {
    color: '#ffffff',
    fontWeight: '500',
    fontFamily: 'Inter',
  },
  healthGrid: {
    gap: 16,
    marginBottom: 20,
  },
  healthItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
  },
  healthLabel: {
    fontSize: 14,
    color: '#333333',
    fontFamily: 'Inter',
    fontWeight: '500',
  },
  healthChip: {
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  timestamp: {
    fontSize: 12,
    color: '#999999',
    fontFamily: 'Inter',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  featureList: {
    marginBottom: 20,
  },
  featureItem: {
    fontSize: 14,
    color: '#333333',
    fontFamily: 'Inter',
    marginBottom: 8,
    lineHeight: 20,
  },
  primaryButton: {
    backgroundColor: '#2742d5',
    borderRadius: 12,
    paddingVertical: 4,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'Inter',
  },
  secondaryButton: {
    borderColor: '#2742d5',
    borderRadius: 12,
    paddingVertical: 4,
  },
  secondaryButtonText: {
    color: '#2742d5',
    fontSize: 16,
    fontWeight: '500',
    fontFamily: 'Inter',
  },
});

export default HomeScreen;

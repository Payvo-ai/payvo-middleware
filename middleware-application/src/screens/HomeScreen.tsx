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
  Card,
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
      console.log('🔍 Attempting to connect to middleware...');

      const response = await PayvoAPI.getHealthCheck();
      console.log('✅ Health check successful:', response);

      // Handle the wrapped response format: {success: true, data: {...}, message: "..."}
      if (response && response.success && response.data) {
        setHealth(response.data);
        setConnectionStatus('connected');
        showNotification('✅ Connected to middleware', 'success', 2000);
      } else if (response && (response as any).status) {
        // Handle direct response format (fallback)
        setHealth(response as any);
        setConnectionStatus('connected');
        showNotification('✅ Connected to middleware', 'success', 2000);
      } else {
        throw new Error('Invalid health response format');
      }
    } catch (error) {
      console.error('❌ Health check failed:', error);

      // Determine error type for better user feedback
      let errorMessage = '⚠️ Middleware offline - using demo mode';
      if (error instanceof Error) {
        if (error.message.includes('Network request failed') || error.message.includes('fetch')) {
          errorMessage = '🌐 Network error - check your connection';
        } else if (error.message.includes('timeout') || error.message.includes('AbortError')) {
          errorMessage = '⏱️ Connection timeout - server may be slow';
        } else if (error.message.includes('HTTP 404')) {
          errorMessage = '🔍 API endpoint not found';
        } else if (error.message.includes('HTTP 500')) {
          errorMessage = '🔧 Server error - try again later';
        }
      }

      // Create a realistic mock health response for demo mode
      setHealth({
        status: 'error',
        version: 'v1.0.0',
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
      showNotification(errorMessage, 'warning', 4000);
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  const testConnection = async () => {
    try {
      setLoading(true);
      setConnectionStatus('checking');
      console.log('🔄 Testing connection...');

      // Test connection by calling health check
      const response = await PayvoAPI.getHealthCheck();
      console.log('✅ Connection test successful:', response);

      // Handle the wrapped response format: {success: true, data: {...}, message: "..."}
      if (response && response.success && response.data) {
        setHealth(response.data);
        setConnectionStatus('connected');
        showNotification('✅ Connection successful!', 'success', 2000);
      } else if (response && (response as any).status) {
        // Handle direct response format (fallback)
        setHealth(response as any);
        setConnectionStatus('connected');
        showNotification('✅ Connection successful!', 'success', 2000);
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('❌ Connection test failed:', error);
      setConnectionStatus('disconnected');

      let errorMessage = '❌ Connection failed';
      if (error instanceof Error) {
        if (error.message.includes('Network request failed')) {
          errorMessage = '🌐 Network error - check internet connection';
        } else if (error.message.includes('timeout') || error.message.includes('AbortError')) {
          errorMessage = '⏱️ Connection timeout - server unreachable';
        } else if (error.message.includes('HTTP')) {
          errorMessage = `🔧 Server error: ${error.message}`;
        }
      }

      showNotification(errorMessage, 'error', 4000);
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

  const getHealthPercentage = () => {
    if (!health) {return '0%';}
    if (health.status === 'healthy') {return '100%';}
    if (health.status === 'error') {return '0%';}
    return '50%';
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
    <View style={styles.container}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}>

        {/* Stats Section */}
        <View style={styles.statsSection}>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <View style={[styles.statIconContainer, { backgroundColor: getConnectionChipColor() + '20' }]}>
                <Text style={[styles.statIcon, { color: getConnectionChipColor() }]}>
                  {connectionStatus === 'connected' ? '✓' : connectionStatus === 'disconnected' ? '✗' : '?'}
                </Text>
              </View>
              <Text style={styles.statLabel}>Connection</Text>
            </View>

            <View style={styles.statCard}>
              <View style={[styles.statIconContainer, { backgroundColor: getStatusColor(health?.status || 'unknown') + '20' }]}>
                <Text style={[styles.statValue, { color: getStatusColor(health?.status || 'unknown') }]}>
                  {getHealthPercentage()}
                </Text>
              </View>
              <Text style={styles.statLabel}>Health</Text>
            </View>

            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statValue}>
                  {health?.version || 'v1.0'}
                </Text>
              </View>
              <Text style={styles.statLabel}>Version</Text>
            </View>
          </View>
        </View>

        {/* Connection Status Card */}
        <Card style={styles.card}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardTitle}>Connection Status</Text>
            <View style={styles.statusContainer}>
              <Chip
                style={[styles.statusChip, {backgroundColor: getConnectionChipColor()}]}
                textStyle={styles.chipText}>
                {connectionStatus === 'connected' ? 'Connected' :
                 connectionStatus === 'disconnected' ? 'Disconnected' : 'Checking...'}
              </Chip>
            </View>
            <Button
              mode="contained"
              onPress={testConnection}
              style={styles.primaryButton}
              labelStyle={styles.buttonText}
              loading={loading && connectionStatus === 'checking'}>
              Test Connection
            </Button>
          </Card.Content>
        </Card>

        {/* Health Status Card */}
        {health && (
          <Card style={styles.card}>
            <Card.Content style={styles.cardContent}>
              <Text style={styles.cardTitle}>System Health</Text>
              <Text style={styles.cardSubtitle}>Status: {health.version}</Text>

              <View style={styles.healthGrid}>
                <View style={styles.healthItem}>
                  <Text style={styles.healthLabel}>Overall</Text>
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
                  <Text style={styles.healthLabel}>Routing</Text>
                  <Chip
                    style={[styles.healthChip, {backgroundColor: getStatusColor(health.components?.routing_orchestrator || 'unknown')}]}
                    textStyle={styles.chipText}>
                    {health.components?.routing_orchestrator || 'unknown'}
                  </Chip>
                </View>
              </View>

              <Text style={styles.timestamp}>
                Updated: {health.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'Just now'}
              </Text>
            </Card.Content>
          </Card>
        )}

        {/* System Components Information */}
        <Card style={styles.card}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardTitle}>System Components</Text>
            <Text style={styles.cardSubtitle}>Understanding your middleware health</Text>

            <View style={styles.infoSection}>
              <Text style={styles.infoSectionTitle}>Components</Text>

              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Database</Text>
                <Text style={styles.infoDescription}>
                  Core data storage for transactions, user data, and system configuration
                </Text>
              </View>

              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Routing Orchestrator</Text>
                <Text style={styles.infoDescription}>
                  Manages payment routing logic and transaction flow between processors
                </Text>
              </View>

              <View style={styles.infoItem}>
                <Text style={styles.infoLabel}>Supabase</Text>
                <Text style={styles.infoDescription}>
                  Authentication and real-time data synchronization service
                </Text>
              </View>
            </View>

            <View style={styles.infoSection}>
              <Text style={styles.infoSectionTitle}>Health Status</Text>

              <View style={styles.statusExplanation}>
                <View style={styles.statusRow}>
                  <View style={[styles.statusDot, styles.statusDotGreen]} />
                  <Text style={styles.statusText}>
                    <Text style={styles.statusLabel}>Healthy/Up:</Text> Component is running normally
                  </Text>
                </View>

                <View style={styles.statusRow}>
                  <View style={[styles.statusDot, styles.statusDotRed]} />
                  <Text style={styles.statusText}>
                    <Text style={styles.statusLabel}>Error/Down:</Text> Component is offline or failing
                  </Text>
                </View>

                <View style={styles.statusRow}>
                  <View style={[styles.statusDot, styles.statusDotOrange]} />
                  <Text style={styles.statusText}>
                    <Text style={styles.statusLabel}>Unknown:</Text> Status cannot be determined
                  </Text>
                </View>
              </View>
            </View>
          </Card.Content>
        </Card>

      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContent: {
    paddingBottom: 20,
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
    textAlign: 'center',
  },
  statsSection: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
    minHeight: 85,
  },
  statIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f1f5f9',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  statIcon: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  statValue: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2742d5',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748b',
    textAlign: 'center',
    fontWeight: '500',
  },
  card: {
    marginHorizontal: 16,
    marginBottom: 12,
    borderRadius: 12,
    elevation: 2,
  },
  cardContent: {
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 16,
  },
  statusContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  statusChip: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 16,
  },
  chipText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 13,
  },
  healthGrid: {
    marginTop: 12,
    marginBottom: 16,
  },
  healthItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    marginBottom: 6,
  },
  healthLabel: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
    flex: 1,
  },
  healthChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  timestamp: {
    fontSize: 11,
    color: '#9ca3af',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  primaryButton: {
    backgroundColor: '#2742d5',
    borderRadius: 8,
    paddingVertical: 4,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
  infoSection: {
    marginBottom: 16,
  },
  infoSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 8,
  },
  infoItem: {
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  infoDescription: {
    fontSize: 12,
    color: '#64748b',
  },
  statusExplanation: {
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 10,
  },
  statusDotGreen: {
    backgroundColor: '#4CAF50',
  },
  statusDotRed: {
    backgroundColor: '#F44336',
  },
  statusDotOrange: {
    backgroundColor: '#FF9800',
  },
  statusText: {
    fontSize: 13,
    color: '#374151',
    flex: 1,
  },
  statusLabel: {
    fontWeight: '600',
  },
});

export default HomeScreen;

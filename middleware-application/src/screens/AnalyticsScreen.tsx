import React, {useState, useEffect, useCallback} from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
} from 'react-native';
import {
  Button,
  Text,
  ActivityIndicator,
  Chip,
  ProgressBar,
} from 'react-native-paper';
import {PayvoAPI} from '../services/PayvoAPI';
import { useNotification } from '../components/NotificationProvider';

const AnalyticsScreen: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [networkAcceptance, setNetworkAcceptance] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'disconnected'>('unknown');
  const { showNotification } = useNotification();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [metricsData, networkData] = await Promise.all([
        PayvoAPI.getMetrics(),
        PayvoAPI.getNetworkAcceptanceRates(),
      ]);

      setMetrics(metricsData);
      setNetworkAcceptance(networkData);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      setConnectionStatus('disconnected');
      showNotification(
        'Unable to fetch analytics data. Please check if the service is running.',
        'error',
        4000
      );
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getMCCInfo = async (mccCode: string) => {
    try {
      const mccInfo = await PayvoAPI.getMCCInfo(mccCode);
      showNotification(
        `MCC ${mccCode}: ${JSON.stringify(mccInfo)}`,
        'info',
        5000
      );
    } catch (error) {
      showNotification('Failed to fetch MCC information', 'error', 3000);
    }
  };

  const formatMetricValue = (value: any): string => {
    if (typeof value === 'number') {
      if (value > 1000000) {return `${(value / 1000000).toFixed(1)}M`;}
      if (value > 1000) {return `${(value / 1000).toFixed(1)}K`;}
      return value.toString();
    }
    if (typeof value === 'boolean') {return value ? 'Active' : 'Inactive';}
    if (typeof value === 'string') {return value;}
    return 'N/A';
  };

  const getProgressValue = (value: any): number => {
    if (typeof value === 'number') {
      if (value > 100) {return Math.min(value / 1000, 1);}
      return Math.min(value / 100, 1);
    }
    if (typeof value === 'boolean') {return value ? 1 : 0;}
    return 0.5;
  };

  const renderMetricCard = (title: string, value: any, icon: string, color: string = '#2742d5') => (
    <View style={styles.metricCard} key={title}>
      <View style={styles.metricHeader}>
        <Text style={styles.metricIcon}>{icon}</Text>
        <Text style={styles.metricTitle}>{title}</Text>
      </View>
      <Text style={[styles.metricValue, { color }]}>{formatMetricValue(value)}</Text>
      <ProgressBar
        progress={getProgressValue(value)}
        color={color}
        style={styles.progressBar}
      />
    </View>
  );

  const renderNetworkCard = (network: string, acceptance: any, icon: string) => (
    <View style={styles.networkCard} key={network}>
      <View style={styles.networkHeader}>
        <Text style={styles.networkIcon}>{icon}</Text>
        <View style={styles.networkInfo}>
          <Text style={styles.networkName}>{network}</Text>
          <Text style={styles.networkStatus}>
            {typeof acceptance === 'object' ? 'Available' : formatMetricValue(acceptance)}
          </Text>
        </View>
      </View>
      <View style={styles.networkDetails}>
        {typeof acceptance === 'object' && acceptance !== null ? (
          Object.entries(acceptance).slice(0, 3).map(([key, value]) => (
            <View style={styles.networkDetailItem} key={key}>
              <Text style={styles.networkDetailLabel}>{key.replace(/_/g, ' ').toUpperCase()}</Text>
              <Text style={styles.networkDetailValue}>{formatMetricValue(value)}</Text>
            </View>
          ))
        ) : (
          <View style={styles.networkDetailItem}>
            <Text style={styles.networkDetailLabel}>ACCEPTANCE RATE</Text>
            <Text style={styles.networkDetailValue}>{formatMetricValue(acceptance)}</Text>
          </View>
        )}
      </View>
    </View>
  );

  if (loading && !metrics) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2742d5" />
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Performance Metrics Card */}
      <View style={styles.card}>
        {/* Stats Overview */}
        <View style={styles.statsSection}>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statIcon}>📊</Text>
              </View>
              <Text style={styles.statValue}>
                {metrics ? 'Active' : 'Loading...'}
              </Text>
              <Text style={styles.statLabel}>System Status</Text>
            </View>

            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statIcon}>🌐</Text>
              </View>
              <Text style={styles.statValue}>
                {connectionStatus === 'connected' ? 'Online' : 'Checking...'}
              </Text>
              <Text style={styles.statLabel}>Network</Text>
            </View>

            <View style={styles.statCard}>
              <View style={styles.statIconContainer}>
                <Text style={styles.statIcon}>⚡</Text>
              </View>
              <Text style={styles.statValue}>Real-time</Text>
              <Text style={styles.statLabel}>Updates</Text>
            </View>
          </View>
        </View>

        {/* System Metrics Card */}
        {metrics && (
          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>System Metrics</Text>
                <Text style={styles.cardSubtitle}>Real-time performance indicators</Text>
              </View>
              <View style={styles.cardContent}>
                <View style={styles.metricsGrid}>
                  {Object.entries(metrics).slice(0, 6).map(([key, value], index) => {
                    const icons = ['⚡', '💾', '🔄', '📈', '⏱️', '🎯'];
                    const colors = ['#2742d5', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#20c997'];
                    return renderMetricCard(
                      key.replace(/_/g, ' ').toUpperCase(),
                      value,
                      icons[index % icons.length],
                      colors[index % colors.length]
                    );
                  })}
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Network Acceptance Card */}
        {networkAcceptance && (
          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Network Acceptance</Text>
                <Text style={styles.cardSubtitle}>Payment network coverage and acceptance rates</Text>
              </View>
              <View style={styles.cardContent}>
                <View style={styles.networksContainer}>
                  {Object.entries(networkAcceptance).slice(0, 4).map(([network, acceptance], index) => {
                    const icons = ['💳', '🏦', '📱', '💰'];
                    return renderNetworkCard(
                      network.replace(/_/g, ' ').toUpperCase(),
                      acceptance,
                      icons[index % icons.length]
                    );
                  })}
                </View>
              </View>
            </View>
          </View>
        )}

        {/* MCC Lookup Tool Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>MCC Information</Text>
              <Text style={styles.cardSubtitle}>Get detailed information about merchant category codes</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.mccContainer}>
                {['5411', '5812', '5541', '5732', '4121'].map((mcc) => (
                  <Chip
                    key={mcc}
                    mode="outlined"
                    onPress={() => getMCCInfo(mcc)}
                    style={styles.mccChip}
                    textStyle={styles.chipTextStyle}>
                    MCC {mcc}
                  </Chip>
                ))}
              </View>
            </View>
          </View>
        </View>

        {/* Real-Time Features Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Real-Time Features</Text>
              <Text style={styles.cardSubtitle}>Live monitoring and analysis capabilities</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.featureList}>
                <Text style={styles.featureItem}>• Live system performance metrics</Text>
                <Text style={styles.featureItem}>• Network acceptance monitoring</Text>
                <Text style={styles.featureItem}>• MCC category information lookup</Text>
                <Text style={styles.featureItem}>• Payment routing effectiveness</Text>
              </View>

              <Button
                mode="contained"
                onPress={fetchData}
                style={styles.primaryButton}
                labelStyle={styles.buttonText}
                loading={loading}>
                Refresh Data
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
    backgroundColor: '#f0eff2',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0eff2',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#676767',
    fontFamily: 'Inter',
  },
  headerSection: {
    backgroundColor: '#2742d5',
    paddingHorizontal: 16,
    paddingTop: 40,
    paddingBottom: 20,
    alignItems: 'center',
  },
  headerLogoContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  headerLogo: {
    width: 80,
    height: 80,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#ffffff',
    fontFamily: 'Inter',
    marginBottom: 4,
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#ffffff',
    fontFamily: 'Inter',
    textAlign: 'center',
  },
  scrollContainer: {
    flex: 1,
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
  statIcon: {
    fontSize: 24,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2742d5',
    fontFamily: 'Inter',
    marginBottom: 4,
    textAlign: 'center',
  },
  statLabel: {
    fontSize: 12,
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
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  metricTitle: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
    fontWeight: '500',
    flex: 1,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '600',
    fontFamily: 'Inter',
    marginBottom: 8,
  },
  progressBar: {
    height: 4,
    borderRadius: 2,
    backgroundColor: '#e0e0e0',
  },
  networksContainer: {
    gap: 16,
  },
  networkCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  networkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  networkIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  networkInfo: {
    flex: 1,
  },
  networkName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    fontFamily: 'Inter',
    marginBottom: 2,
  },
  networkStatus: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
  },
  networkDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  networkDetailItem: {
    flex: 1,
    minWidth: '30%',
  },
  networkDetailLabel: {
    fontSize: 10,
    color: '#676767',
    fontFamily: 'Inter',
    fontWeight: '500',
    marginBottom: 2,
  },
  networkDetailValue: {
    fontSize: 14,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
  },
  mccContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  mccChip: {
    borderColor: '#2742d5',
    backgroundColor: '#ffffff',
  },
  chipTextStyle: {
    color: '#2742d5',
    fontFamily: 'Inter',
    fontSize: 14,
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
});

export default AnalyticsScreen;

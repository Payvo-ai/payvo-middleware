import React, {useState, useEffect, useCallback} from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import {
  Text,
  ActivityIndicator,
  Chip,
} from 'react-native-paper';
import {PayvoAPI, TransactionHistoryItem} from '../services/PayvoAPI';
import { useNotification } from '../components/NotificationProvider';
import { useAuth } from '../contexts/AuthContext';

const AnalyticsScreen: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { showNotification } = useNotification();
  const { getUserId } = useAuth();

  const fetchTransactionHistory = useCallback(async () => {
    try {
      setLoading(true);
      const userId = await getUserId();
      const response = await PayvoAPI.getUserTransactionHistory(userId, 20, 0);

      if (response.success && response.data) {
        setTransactions(response.data.transactions);
      } else {
        console.warn('Failed to fetch transaction history:', response.error);
        showNotification(
          'Unable to fetch transaction history. Please try again.',
          'error',
          4000,
        );
      }
    } catch (error) {
      console.error('Failed to fetch transaction history:', error);
      showNotification(
        'Unable to fetch transaction history. Please check your connection.',
        'error',
        4000,
      );
    } finally {
      setLoading(false);
    }
  }, [getUserId, showNotification]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchTransactionHistory();
    setRefreshing(false);
  }, [fetchTransactionHistory]);

  useEffect(() => {
    fetchTransactionHistory();
  }, [fetchTransactionHistory]);

  const formatTransactionDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Unknown';
    }
  };

  const formatLocation = (location?: TransactionHistoryItem['location']): string => {
    if (!location) {
      return 'Location not available';
    }
    
    const parts = [];
    if (location.address) {
      parts.push(location.address);
    }
    if (location.city) {
      parts.push(location.city);
    }
    if (location.state) {
      parts.push(location.state);
    }
    if (location.postal_code) {
      parts.push(location.postal_code);
    }
    
    return parts.length > 0 ? parts.join(', ') : 'Location not available';
  };

  const getMCCDescription = (mcc?: string): string => {
    if (!mcc) {
      return 'Unknown Category';
    }

    // Common MCC codes and their descriptions
    const mccDescriptions: { [key: string]: string } = {
      '5411': 'Grocery Stores',
      '5812': 'Eating Places/Restaurants',
      '5541': 'Service Stations',
      '5732': 'Electronics Stores',
      '4121': 'Taxicabs/Limousines',
      '5311': 'Department Stores',
      '5912': 'Drug Stores',
      '5999': 'Miscellaneous Retail',
      '7011': 'Hotels/Motels',
      '4111': 'Transportation',
    };

    return mccDescriptions[mcc] || `MCC ${mcc}`;
  };

  const formatAmount = (amount: number | undefined): string => {
    if (typeof amount !== 'number') {
      return 'N/A';
    }
    return `$${amount.toFixed(2)}`;
  };

  const getTransactionStatusColor = (success: boolean | undefined): string => {
    if (success === undefined) {
      return '#6c757d';
    }
    return success ? '#28a745' : '#dc3545';
  };

  const getTransactionStatusText = (success: boolean | undefined): string => {
    if (success === undefined) {
      return 'Unknown';
    }
    return success ? 'Success' : 'Failed';
  };

  if (loading && !transactions.length) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2742d5" />
        <Text style={styles.loadingText}>Loading transaction history...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      {/* Transaction History Card */}
      <View style={styles.cardContainer}>
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Transaction History</Text>
            <Text style={styles.cardSubtitle}>Your recent transactions with MCC, merchant, amount, and location details</Text>
          </View>
          <View style={styles.cardContent}>
            {transactions.length > 0 ? (
              transactions.map((transaction, index) => (
                <View key={transaction.id || index} style={styles.transactionItem}>
                  <View style={styles.transactionHeader}>
                    <View style={styles.transactionMerchant}>
                      <Text style={styles.merchantName}>
                        {transaction.merchant_name || 'Unknown Merchant'}
                      </Text>
                      <Text style={styles.transactionDate}>
                        {formatTransactionDate(transaction.created_at)}
                      </Text>
                    </View>
                    <View style={styles.transactionAmount}>
                      <Text style={styles.amountText}>
                        {formatAmount(transaction.transaction_amount)}
                      </Text>
                      <Chip
                        style={[
                          styles.statusChip,
                          { backgroundColor: getTransactionStatusColor(transaction.transaction_success) }
                        ]}
                        textStyle={styles.statusChipText}
                        compact>
                        {getTransactionStatusText(transaction.transaction_success)}
                      </Chip>
                    </View>
                  </View>
                  
                  <View style={styles.transactionDetails}>
                    {/* MCC Information */}
                    <View style={styles.transactionDetailRow}>
                      <View style={styles.transactionDetailItem}>
                        <Text style={styles.detailLabel}>Category:</Text>
                        <Text style={styles.detailValue}>
                          {getMCCDescription(transaction.predicted_mcc || transaction.actual_mcc)}
                        </Text>
                      </View>
                      {(transaction.predicted_mcc || transaction.actual_mcc) && (
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>MCC:</Text>
                          <Text style={styles.detailValue}>
                            {transaction.predicted_mcc || transaction.actual_mcc}
                          </Text>
                        </View>
                      )}
                    </View>

                    {/* Location Information */}
                    <View style={styles.transactionDetailRow}>
                      <View style={styles.transactionDetailItem}>
                        <Text style={styles.detailLabel}>📍 Location:</Text>
                        <Text style={styles.detailValue}>
                          {formatLocation(transaction.location)}
                        </Text>
                      </View>
                    </View>

                    {/* Additional Details */}
                    <View style={styles.transactionDetailRow}>
                      {transaction.prediction_confidence && (
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>Confidence:</Text>
                          <Text style={styles.detailValue}>
                            {(transaction.prediction_confidence * 100).toFixed(1)}%
                          </Text>
                        </View>
                      )}
                      {transaction.network_used && (
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>Network:</Text>
                          <Text style={styles.detailValue}>{transaction.network_used}</Text>
                        </View>
                      )}
                    </View>

                    {transaction.terminal_id && (
                      <View style={styles.transactionDetailRow}>
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>Terminal ID:</Text>
                          <Text style={styles.detailValue}>{transaction.terminal_id}</Text>
                        </View>
                      </View>
                    )}
                  </View>
                </View>
              ))
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>No transactions found</Text>
                <Text style={styles.emptyStateSubtext}>
                  Transaction history will appear here once you start using the app
                </Text>
              </View>
            )}
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
    paddingTop: 16,
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
  transactionItem: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  transactionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  transactionMerchant: {
    flex: 1,
  },
  merchantName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    fontFamily: 'Inter',
    marginBottom: 2,
  },
  transactionDate: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
  },
  transactionAmount: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  amountText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2742d5',
    fontFamily: 'Inter',
    marginRight: 8,
  },
  transactionDetails: {
    marginTop: 8,
  },
  transactionDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  transactionDetailItem: {
    flex: 1,
  },
  detailLabel: {
    fontSize: 10,
    color: '#676767',
    fontFamily: 'Inter',
    fontWeight: '500',
    marginRight: 8,
  },
  detailValue: {
    fontSize: 14,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
  },
  statusChip: {
    borderColor: '#2742d5',
    backgroundColor: '#ffffff',
    borderWidth: 1,
  },
  statusChipText: {
    color: '#2742d5',
    fontFamily: 'Inter',
    fontSize: 14,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    color: '#676767',
    fontFamily: 'Inter',
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#676767',
    fontFamily: 'Inter',
  },
});

export default AnalyticsScreen;

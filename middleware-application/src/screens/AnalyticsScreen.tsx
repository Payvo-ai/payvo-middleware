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
  ProgressBar,
} from 'react-native-paper';
import {PayvoAPI, TransactionHistoryItem} from '../services/PayvoAPI';
import { useNotification } from '../components/NotificationProvider';
import { useAuth } from '../contexts/AuthContext';

interface AnalyticsData {
  totalTransactions: number;
  successRate: number;
  averageAmount: number;
  totalRewards: number;
  mccAccuracy: number;
  averageConfidence: number;
  topMccCategories: Array<{mcc: string, count: number, description: string}>;
  networkPerformance: Array<{network: string, count: number, successRate: number}>;
  monthlyTrends: Array<{month: string, transactions: number, rewards: number}>;
}

const AnalyticsScreen: React.FC = () => {
  const [transactions, setTransactions] = useState<TransactionHistoryItem[]>([]);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { showNotification } = useNotification();
  const { getUserId } = useAuth();

  const getMCCDescription = (mcc?: string): string => {
    if (!mcc) {
      return 'Unknown Category';
    }

    // Common MCC codes and their descriptions
    const mccDescriptions: { [key: string]: string } = {
      '5411': 'Grocery Stores',
      '5812': 'Eating Places/Restaurants',
      '5541': 'Service Stations',
      '5542': 'Automated Fuel Dispensers',
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

  const calculateAnalytics = useCallback((transactionList: TransactionHistoryItem[]): AnalyticsData => {
    if (transactionList.length === 0) {
      return {
        totalTransactions: 0,
        successRate: 0,
        averageAmount: 0,
        totalRewards: 0,
        mccAccuracy: 0,
        averageConfidence: 0,
        topMccCategories: [],
        networkPerformance: [],
        monthlyTrends: [],
      };
    }

    // Basic metrics
    const totalTransactions = transactionList.length;
    const successfulTransactions = transactionList.filter(t => t.transaction_success === true).length;
    const successRate = successfulTransactions / totalTransactions;

    const validAmounts = transactionList.filter(t => t.transaction_amount).map(t => t.transaction_amount!);
    const averageAmount = validAmounts.length > 0 ? validAmounts.reduce((a, b) => a + b, 0) / validAmounts.length : 0;

    const totalRewards = transactionList.reduce((sum, t) => sum + (t.prediction_confidence || 0), 0);

    // MCC Accuracy
    const transactionsWithBothMccs = transactionList.filter(t => t.predicted_mcc && t.actual_mcc);
    const correctPredictions = transactionsWithBothMccs.filter(t => t.predicted_mcc === t.actual_mcc).length;
    const mccAccuracy = transactionsWithBothMccs.length > 0 ? correctPredictions / transactionsWithBothMccs.length : 0;

    // Average Confidence
    const confidenceValues = transactionList.filter(t => t.prediction_confidence).map(t => t.prediction_confidence!);
    const averageConfidence = confidenceValues.length > 0 ? confidenceValues.reduce((a, b) => a + b, 0) / confidenceValues.length : 0;

    // Top MCC Categories
    const mccCounts: {[key: string]: number} = {};
    transactionList.forEach(t => {
      const mcc = t.actual_mcc || t.predicted_mcc;
      if (mcc) {
        mccCounts[mcc] = (mccCounts[mcc] || 0) + 1;
      }
    });

    const topMccCategories = Object.entries(mccCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([mcc, count]) => ({
        mcc,
        count,
        description: getMCCDescription(mcc),
      }));

    // Network Performance
    const networkStats: {[key: string]: {count: number, successful: number}} = {};
    transactionList.forEach(t => {
      if (t.network_used) {
        if (!networkStats[t.network_used]) {
          networkStats[t.network_used] = {count: 0, successful: 0};
        }
        networkStats[t.network_used].count++;
        if (t.transaction_success) {
          networkStats[t.network_used].successful++;
        }
      }
    });

    const networkPerformance = Object.entries(networkStats).map(([network, stats]) => ({
      network,
      count: stats.count,
      successRate: stats.count > 0 ? stats.successful / stats.count : 0,
    }));

    // Monthly Trends (last 6 months)
    const monthlyData: {[key: string]: {transactions: number, rewards: number}} = {};
    transactionList.forEach(t => {
      const month = new Date(t.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
      if (!monthlyData[month]) {
        monthlyData[month] = {transactions: 0, rewards: 0};
      }
      monthlyData[month].transactions++;
      monthlyData[month].rewards += t.prediction_confidence || 0;
    });

    const monthlyTrends = Object.entries(monthlyData)
      .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
      .slice(-6)
      .map(([month, data]) => ({
        month,
        transactions: data.transactions,
        rewards: data.rewards,
      }));

    return {
      totalTransactions,
      successRate,
      averageAmount,
      totalRewards,
      mccAccuracy,
      averageConfidence,
      topMccCategories,
      networkPerformance,
      monthlyTrends,
    };
  }, []);

  const fetchTransactionHistory = useCallback(async () => {
    try {
      setLoading(true);
      const userId = await getUserId();
      const response = await PayvoAPI.getUserTransactionHistory(userId, 100, 0);

      if (response.success && response.data) {
        setTransactions(response.data.transactions);
        setAnalyticsData(calculateAnalytics(response.data.transactions));
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
  }, [getUserId, showNotification, calculateAnalytics]);

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

  const formatAmount = (amount: number | undefined): string => {
    if (typeof amount !== 'number') {
      return 'N/A';
    }
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
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
        <Text style={styles.loadingText}>Loading analytics...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {analyticsData && (
        <>
          {/* Overview Cards */}
          <View style={styles.overviewContainer}>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewNumber}>{analyticsData.totalTransactions}</Text>
              <Text style={styles.overviewLabel}>Total Transactions</Text>
            </View>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewNumber}>{formatPercentage(analyticsData.successRate)}</Text>
              <Text style={styles.overviewLabel}>Success Rate</Text>
            </View>
          </View>

          <View style={styles.overviewContainer}>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewNumber}>{formatAmount(analyticsData.averageAmount)}</Text>
              <Text style={styles.overviewLabel}>Avg Amount</Text>
            </View>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewNumber}>{formatPercentage(analyticsData.mccAccuracy)}</Text>
              <Text style={styles.overviewLabel}>MCC Accuracy</Text>
            </View>
          </View>

          {/* MCC Prediction Analytics */}
          <View style={styles.cardContainer}>
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>🎯 MCC Prediction Performance</Text>
                <Text style={styles.cardSubtitle}>Machine learning prediction accuracy and confidence metrics</Text>
              </View>
              <View style={styles.cardContent}>
                <View style={styles.metricRow}>
                  <Text style={styles.metricLabel}>Prediction Accuracy</Text>
                  <View style={styles.metricValueContainer}>
                    <Text style={styles.metricValue}>{formatPercentage(analyticsData.mccAccuracy)}</Text>
                    <ProgressBar
                      progress={analyticsData.mccAccuracy}
                      color="#28a745"
                      style={styles.progressBar}
                    />
                  </View>
                </View>
                <View style={styles.metricRow}>
                  <Text style={styles.metricLabel}>Average Confidence</Text>
                  <View style={styles.metricValueContainer}>
                    <Text style={styles.metricValue}>{formatPercentage(analyticsData.averageConfidence)}</Text>
                    <ProgressBar
                      progress={analyticsData.averageConfidence}
                      color="#2742d5"
                      style={styles.progressBar}
                    />
                  </View>
                </View>
                <View style={styles.metricRow}>
                  <Text style={styles.metricLabel}>Transactions with Predictions</Text>
                  <Text style={styles.metricValue}>
                    {transactions.filter(t => t.predicted_mcc || t.actual_mcc).length} of {analyticsData.totalTransactions}
                  </Text>
                </View>
              </View>
            </View>
          </View>

          {/* Top MCC Categories */}
          {analyticsData.topMccCategories.length > 0 && (
            <View style={styles.cardContainer}>
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>🏪 Top Merchant Categories</Text>
                  <Text style={styles.cardSubtitle}>Your most frequent transaction categories</Text>
                </View>
                <View style={styles.cardContent}>
                  {analyticsData.topMccCategories.map((category) => (
                    <View key={category.mcc} style={styles.categoryRow}>
                      <View style={styles.categoryInfo}>
                        <Text style={styles.categoryDescription}>{category.description}</Text>
                        <Text style={styles.categoryMcc}>MCC {category.mcc}</Text>
                      </View>
                      <View style={styles.categoryStats}>
                        <Text style={styles.categoryCount}>{category.count} transactions</Text>
                        <ProgressBar
                          progress={category.count / analyticsData.totalTransactions}
                          color="#2742d5"
                          style={styles.categoryProgressBar}
                        />
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            </View>
          )}

          {/* Network Performance */}
          {analyticsData.networkPerformance.length > 0 && (
            <View style={styles.cardContainer}>
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>💳 Payment Network Performance</Text>
                  <Text style={styles.cardSubtitle}>Success rates by payment network</Text>
                </View>
                <View style={styles.cardContent}>
                  {analyticsData.networkPerformance.map((network) => (
                    <View key={network.network} style={styles.networkRow}>
                      <View style={styles.networkInfo}>
                        <Text style={styles.networkName}>{network.network.toUpperCase()}</Text>
                        <Text style={styles.networkCount}>{network.count} transactions</Text>
                      </View>
                      <View style={styles.networkPerformanceStats}>
                        <Text style={styles.networkSuccessRate}>{formatPercentage(network.successRate)}</Text>
                        <ProgressBar
                          progress={network.successRate}
                          color={network.successRate > 0.9 ? '#28a745' : network.successRate > 0.7 ? '#ffc107' : '#dc3545'}
                          style={styles.networkProgressBar}
                        />
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            </View>
          )}

          {/* Monthly Trends */}
          {analyticsData.monthlyTrends.length > 0 && (
            <View style={styles.cardContainer}>
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>📈 Monthly Trends</Text>
                  <Text style={styles.cardSubtitle}>Transaction volume over time</Text>
                </View>
                <View style={styles.cardContent}>
                  {analyticsData.monthlyTrends.map((month) => (
                    <View key={month.month} style={styles.trendRow}>
                      <Text style={styles.trendMonth}>{month.month}</Text>
                      <View style={styles.trendStats}>
                        <Text style={styles.trendTransactions}>{month.transactions} transactions</Text>
                        <ProgressBar
                          progress={month.transactions / Math.max(...analyticsData.monthlyTrends.map(m => m.transactions))}
                          color="#2742d5"
                          style={styles.trendProgressBar}
                        />
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            </View>
          )}
        </>
      )}

      {/* Transaction History */}
      <View style={styles.cardContainer}>
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>📊 Recent Transaction Details</Text>
            <Text style={styles.cardSubtitle}>Detailed transaction history with feedback data</Text>
          </View>
          <View style={styles.cardContent}>
            {transactions.length > 0 ? (
              transactions.slice(0, 10).map((transaction, index) => (
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
                          { backgroundColor: getTransactionStatusColor(transaction.transaction_success) },
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

                    {/* Prediction vs Actual */}
                    {transaction.predicted_mcc && transaction.actual_mcc && (
                      <View style={styles.transactionDetailRow}>
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>Predicted:</Text>
                          <Text style={[styles.detailValue, transaction.predicted_mcc === transaction.actual_mcc ? styles.correctPrediction : styles.incorrectPrediction]}>
                            {transaction.predicted_mcc}
                          </Text>
                        </View>
                        <View style={styles.transactionDetailItem}>
                          <Text style={styles.detailLabel}>Actual:</Text>
                          <Text style={styles.detailValue}>{transaction.actual_mcc}</Text>
                        </View>
                      </View>
                    )}

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
                  Transaction analytics will appear here once you start using the app
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
    fontSize: 14,
    fontWeight: '600',
    color: '#2742d5',
    fontFamily: 'Inter',
    marginRight: 8,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
    marginLeft: 8,
    flex: 1,
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
    fontSize: 14,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
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
  overviewContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
  },
  overviewCard: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  overviewNumber: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2742d5',
    fontFamily: 'Inter',
    marginBottom: 4,
  },
  overviewLabel: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  metricLabel: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
    fontWeight: '500',
    marginRight: 8,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryDescription: {
    fontSize: 14,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
  },
  categoryMcc: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
    marginTop: 2,
  },
  categoryStats: {
    flex: 1,
    alignItems: 'flex-end',
  },
  categoryCount: {
    fontSize: 12,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
    marginBottom: 4,
  },
  categoryProgressBar: {
    width: 80,
    height: 4,
    borderRadius: 2,
  },
  networkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  networkCount: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
    marginTop: 2,
  },
  networkPerformanceStats: {
    flex: 1,
    alignItems: 'flex-end',
  },
  networkSuccessRate: {
    fontSize: 12,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
    marginBottom: 4,
  },
  networkProgressBar: {
    width: 80,
    height: 4,
    borderRadius: 2,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  trendMonth: {
    fontSize: 14,
    color: '#2742d5',
    fontFamily: 'Inter',
    fontWeight: '600',
    width: 60,
  },
  trendStats: {
    flex: 1,
    alignItems: 'flex-end',
  },
  trendTransactions: {
    fontSize: 12,
    color: '#676767',
    fontFamily: 'Inter',
    marginBottom: 4,
  },
  trendProgressBar: {
    width: 100,
    height: 4,
    borderRadius: 2,
  },
  correctPrediction: {
    color: '#28a745',
  },
  incorrectPrediction: {
    color: '#dc3545',
  },
});

export default AnalyticsScreen;

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRealtime } from '../hooks/useRealtime';
import { TransactionUpdate, UserSessionUpdate, LocationSessionUpdate, UserProfileUpdate } from '../services/RealtimeService';

interface RealtimeExampleProps {
  userId: string;
}

export const RealtimeExample: React.FC<RealtimeExampleProps> = ({ userId }) => {
  const [transactions, setTransactions] = useState<TransactionUpdate[]>([]);
  const [sessionStatus, setSessionStatus] = useState<string>('Unknown');
  const [locationStatus, setLocationStatus] = useState<string>('Inactive');
  const [profileInfo, setProfileInfo] = useState<string>('Loading...');

  // Handle new transactions
  const handleNewTransaction = useCallback((transaction: TransactionUpdate) => {
    setTransactions(prev => [transaction, ...prev.slice(0, 9)]); // Keep last 10
    Alert.alert(
      'New Transaction!',
      `${transaction.merchant_name}: $${transaction.transaction_amount}`,
      [{ text: 'OK' }]
    );
  }, []);

  // Handle session changes
  const handleSessionChange = useCallback((session: UserSessionUpdate) => {
    setSessionStatus(session.is_active ? 'Active' : 'Inactive');
  }, []);

  // Handle location updates
  const handleLocationUpdate = useCallback((session: LocationSessionUpdate) => {
    setLocationStatus(`${session.status} - ${session.location_count} locations`);
  }, []);

  // Handle profile updates
  const handleProfileUpdate = useCallback((profile: UserProfileUpdate) => {
    setProfileInfo(`${profile.full_name} (${profile.username || 'No username'})`);
  }, []);

  // Use the comprehensive realtime hook
  const { activeChannels } = useRealtime({
    userId,
    onTransaction: handleNewTransaction,
    onSession: handleSessionChange,
    onLocation: handleLocationUpdate,
    onProfile: handleProfileUpdate,
    enabled: true,
  });

  // Alternative: Use specific hooks for more control
  // const { channelName: transactionChannel } = useTransactionUpdates(
  //   userId,
  //   handleNewTransaction,
  //   handleTransactionUpdate,
  //   true
  // );

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🔴 Live Updates</Text>

      {/* Connection Status */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Connection Status</Text>
        <Text style={styles.info}>
          Active Channels: {activeChannels.length}
        </Text>
        <Text style={styles.info}>
          User ID: {userId}
        </Text>
      </View>

      {/* Profile Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>👤 Profile</Text>
        <Text style={styles.info}>{profileInfo}</Text>
      </View>

      {/* Session Status */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔐 Session</Text>
        <Text style={styles.info}>Status: {sessionStatus}</Text>
      </View>

      {/* Location Status */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📍 Location Tracking</Text>
        <Text style={styles.info}>{locationStatus}</Text>
      </View>

      {/* Recent Transactions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💳 Recent Transactions</Text>
        {transactions.length === 0 ? (
          <Text style={styles.info}>No transactions yet...</Text>
        ) : (
          transactions.map((transaction, _index) => (
            <View key={transaction.id} style={styles.transactionItem}>
              <Text style={styles.merchantName}>
                {transaction.merchant_name || 'Unknown Merchant'}
              </Text>
              <Text style={styles.transactionDetails}>
                ${transaction.transaction_amount} • MCC: {transaction.actual_mcc}
              </Text>
              <Text style={styles.transactionStatus}>
                {transaction.transaction_success ? '✅ Success' : '❌ Failed'}
              </Text>
              <Text style={styles.timestamp}>
                {new Date(transaction.created_at).toLocaleTimeString()}
              </Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
  },
  section: {
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  info: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  transactionItem: {
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    paddingVertical: 8,
    marginBottom: 8,
  },
  merchantName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  transactionDetails: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  transactionStatus: {
    fontSize: 14,
    marginTop: 2,
  },
  timestamp: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
});

import React, {useState} from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
} from 'react-native';
import {
  Button,
  Switch,
  TextInput,
  Divider,
  Chip,
  Text,
} from 'react-native-paper';
import {PayvoAPI} from '../services/PayvoAPI';
import { useNotification } from '../components/NotificationProvider';

// Separate components to avoid nested component warnings
const NotificationSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const DebugModeSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const MockDataSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const AutoRefreshSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const SettingsScreen: React.FC = () => {
  const [apiUrl, setApiUrl] = useState('https://payvo-middleware-production.up.railway.app');
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [enableDebugMode, setEnableDebugMode] = useState(false);
  const [enableMockData, setEnableMockData] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState('30');
  const { showNotification } = useNotification();

  const handleSaveSettings = () => {
    // Update API base URL
    PayvoAPI.updateBaseURL(apiUrl);

    showNotification(
      'Your configuration has been updated successfully.',
      'success',
      3000
    );
  };

  const handleResetSettings = () => {
    setApiUrl('https://payvo-middleware-production.up.railway.app');
    setEnableNotifications(true);
    setEnableDebugMode(false);
    setEnableMockData(true);
    setAutoRefresh(true);
    setRefreshInterval('30');
    PayvoAPI.updateBaseURL('https://payvo-middleware-production.up.railway.app');

    showNotification(
      'All settings have been reset to default values.',
      'info',
      3000
    );
  };

  const handleTestConnection = async () => {
    try {
      showNotification('Checking API connectivity...', 'info', 2000);
      PayvoAPI.updateBaseURL(apiUrl);
      const isConnected = await PayvoAPI.testConnection();

      setTimeout(() => {
        showNotification(
          isConnected
            ? 'Successfully connected to Payvo Middleware!'
            : 'Connection failed. Please check your middleware service.',
          isConnected ? 'success' : 'error',
          4000
        );
      }, 1000);
    } catch (error) {
      showNotification(
        'Could not connect to the middleware. Please check your settings.',
        'error',
        4000
      );
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* API Configuration Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>API Configuration</Text>
              <Text style={styles.cardSubtitle}>Configure connection to Payvo Middleware</Text>
            </View>
            <View style={styles.cardContent}>
              <TextInput
                label="API Base URL"
                value={apiUrl}
                onChangeText={setApiUrl}
                style={styles.input}
                mode="outlined"
                placeholder="http://localhost:8000"
                outlineColor="#e0e0e0"
                activeOutlineColor="#2742d5"
              />

              <View style={styles.buttonRow}>
                <Button
                  mode="outlined"
                  onPress={handleTestConnection}
                  style={styles.secondaryButton}
                  labelStyle={styles.secondaryButtonText}>
                  Test Connection
                </Button>
              </View>
            </View>
          </View>
        </View>

        {/* App Preferences Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>App Preferences</Text>
              <Text style={styles.cardSubtitle}>Customize your app behavior</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.settingItem}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingTitle}>Enable Notifications</Text>
                  <Text style={styles.settingDescription}>Receive alerts for transaction updates</Text>
                </View>
                <NotificationSwitch value={enableNotifications} onValueChange={setEnableNotifications} />
              </View>

              <Divider style={styles.divider} />

              <View style={styles.settingItem}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingTitle}>Debug Mode</Text>
                  <Text style={styles.settingDescription}>Show detailed logs and debug information</Text>
                </View>
                <DebugModeSwitch value={enableDebugMode} onValueChange={setEnableDebugMode} />
              </View>

              <Divider style={styles.divider} />

              <View style={styles.settingItem}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingTitle}>Use Mock Data</Text>
                  <Text style={styles.settingDescription}>Use sample data when API is unavailable</Text>
                </View>
                <MockDataSwitch value={enableMockData} onValueChange={setEnableMockData} />
              </View>

              <Divider style={styles.divider} />

              <View style={styles.settingItem}>
                <View style={styles.settingInfo}>
                  <Text style={styles.settingTitle}>Auto Refresh</Text>
                  <Text style={styles.settingDescription}>Automatically refresh data</Text>
                </View>
                <AutoRefreshSwitch value={autoRefresh} onValueChange={setAutoRefresh} />
              </View>

              {autoRefresh && (
                <View style={styles.intervalContainer}>
                  <Text style={styles.intervalLabel}>Refresh Interval (seconds):</Text>
                  <TextInput
                    value={refreshInterval}
                    onChangeText={setRefreshInterval}
                    style={styles.intervalInput}
                    mode="outlined"
                    keyboardType="numeric"
                    placeholder="30"
                    outlineColor="#e0e0e0"
                    activeOutlineColor="#2742d5"
                  />
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Testing Tools Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Testing Tools</Text>
              <Text style={styles.cardSubtitle}>Quick access to testing utilities</Text>
            </View>
            <View style={styles.cardContent}>
              <View style={styles.chipContainer}>
                <Chip
                  mode="outlined"
                  onPress={() => showNotification('Clear all cached data', 'info', 2000)}
                  style={styles.toolChip}
                  textStyle={styles.chipTextStyle}>
                  Clear Cache
                </Chip>
                <Chip
                  mode="outlined"
                  onPress={() => showNotification('Reset all preferences', 'info', 2000)}
                  style={styles.toolChip}
                  textStyle={styles.chipTextStyle}>
                  Reset Preferences
                </Chip>
                <Chip
                  mode="outlined"
                  onPress={() => showNotification('Export configuration', 'info', 2000)}
                  style={styles.toolChip}
                  textStyle={styles.chipTextStyle}>
                  Export Config
                </Chip>
                <Chip
                  mode="outlined"
                  onPress={() => showNotification('Import configuration', 'info', 2000)}
                  style={styles.toolChip}
                  textStyle={styles.chipTextStyle}>
                  Import Config
                </Chip>
              </View>
            </View>
          </View>
        </View>

        {/* Action Buttons Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardContent}>
              <View style={styles.actionButtons}>
                <Button
                  mode="contained"
                  onPress={handleSaveSettings}
                  style={styles.primaryButton}
                  labelStyle={styles.buttonText}>
                  Save Settings
                </Button>
                <Button
                  mode="outlined"
                  onPress={handleResetSettings}
                  style={styles.secondaryButton}
                  labelStyle={styles.secondaryButtonText}>
                  Reset to Defaults
                </Button>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
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
  input: {
    marginBottom: 16,
    backgroundColor: '#ffffff',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#000000',
    fontFamily: 'Inter',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#676767',
    fontFamily: 'Inter',
  },
  divider: {
    marginVertical: 8,
    backgroundColor: '#f0f0f0',
  },
  intervalContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  intervalLabel: {
    fontSize: 14,
    color: '#333333',
    fontFamily: 'Inter',
    marginBottom: 8,
    fontWeight: '500',
  },
  intervalInput: {
    backgroundColor: '#ffffff',
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  toolChip: {
    borderColor: '#2742d5',
    backgroundColor: '#ffffff',
  },
  chipTextStyle: {
    color: '#2742d5',
    fontFamily: 'Inter',
  },
  actionButtons: {
    gap: 12,
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

export default SettingsScreen;

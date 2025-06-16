import React, {useState, useEffect} from 'react';
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
  Text,
} from 'react-native-paper';
import { useNotification } from '../components/NotificationProvider';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AuthService from '../services/AuthService';

// Separate components to avoid nested component warnings
const NotificationSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const DebugModeSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const AutoRefreshSwitch: React.FC<{value: boolean; onValueChange: (value: boolean) => void}> = ({value, onValueChange}) => (
  <Switch value={value} onValueChange={onValueChange} />
);

const SettingsScreen: React.FC = () => {
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [enableDebugMode, setEnableDebugMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState('30');
  const { showNotification } = useNotification();

  // Auto-save settings when they change
  useEffect(() => {
    const saveSettings = async () => {
      try {
        await AsyncStorage.setItem('enableNotifications', JSON.stringify(enableNotifications));
        await AsyncStorage.setItem('enableDebugMode', JSON.stringify(enableDebugMode));
        await AsyncStorage.setItem('autoRefresh', JSON.stringify(autoRefresh));
        await AsyncStorage.setItem('refreshInterval', refreshInterval);
      } catch (error) {
        console.error('Failed to save settings:', error);
      }
    };
    saveSettings();
  }, [enableNotifications, enableDebugMode, autoRefresh, refreshInterval]);

  // Load settings on component mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const savedNotifications = await AsyncStorage.getItem('enableNotifications');
        const savedDebugMode = await AsyncStorage.getItem('enableDebugMode');
        const savedAutoRefresh = await AsyncStorage.getItem('autoRefresh');
        const savedRefreshInterval = await AsyncStorage.getItem('refreshInterval');

        if (savedNotifications !== null) {
          setEnableNotifications(JSON.parse(savedNotifications));
        }
        if (savedDebugMode !== null) {
          setEnableDebugMode(JSON.parse(savedDebugMode));
        }
        if (savedAutoRefresh !== null) {
          setAutoRefresh(JSON.parse(savedAutoRefresh));
        }
        if (savedRefreshInterval !== null) {
          setRefreshInterval(savedRefreshInterval);
        }
      } catch (error) {
        console.error('Failed to load settings:', error);
      }
    };
    loadSettings();
  }, []);

  const handleLogout = async () => {
    try {
      await AuthService.signOut();
      showNotification('Logged out successfully', 'success', 2000);
    } catch (error) {
      console.error('Logout error:', error);
      showNotification('Failed to logout', 'error', 2000);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* App Preferences Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>App Preferences</Text>
              <Text style={styles.cardSubtitle}>Settings are saved automatically</Text>
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

        {/* Action Buttons Card */}
        <View style={styles.cardContainer}>
          <View style={styles.card}>
            <View style={styles.cardContent}>
              <View style={styles.actionButtons}>
                <Button
                  mode="outlined"
                  onPress={handleLogout}
                  style={styles.secondaryButton}
                  labelStyle={styles.secondaryButtonText}>
                  Logout
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
    paddingTop: 16,
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

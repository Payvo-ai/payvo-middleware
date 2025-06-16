/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {createStackNavigator} from '@react-navigation/stack';
import {MD3LightTheme, PaperProvider} from 'react-native-paper';
import {SafeAreaProvider, useSafeAreaInsets} from 'react-native-safe-area-context';
import {StatusBar, View, Text, StyleSheet, Image, ActivityIndicator} from 'react-native';
import { HomeIcon, CreditCardIcon, AnalyticsIcon, SettingsIcon } from './src/components/TabIcons';
import { NotificationProvider } from './src/components/NotificationProvider';
import { AuthProvider, useAuth } from './src/contexts/AuthContext';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import TransactionScreen from './src/screens/TransactionScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import SignInScreen from './src/screens/SignInScreen';

// Custom theme with Payvo primary blue
const PayvoTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#2742d5',
    primaryContainer: '#e8eaff',
    onPrimary: '#ffffff',
    onPrimaryContainer: '#001258',
    secondary: '#5a5d72',
    secondaryContainer: '#dfe1f9',
    onSecondary: '#ffffff',
    onSecondaryContainer: '#171b2c',
  },
};

// Loading Screen Component
const LoadingScreen: React.FC = () => {
  return (
    <View style={styles.loadingContainer}>
      <Image
        source={require('./images/logo.png')}
        style={styles.loadingLogo}
        resizeMode="contain"
      />
      <ActivityIndicator size="large" color="#ffffff" style={styles.loadingSpinner} />
      <Text style={styles.loadingText}>Loading Payvo...</Text>
    </View>
  );
};

// Tab Navigator
const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Tab Navigator with Safe Area handling
const SafeTabNavigator: React.FC = () => {
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      id={undefined}
      screenOptions={{
        tabBarActiveTintColor: '#2742d5',
        tabBarInactiveTintColor: '#64748b',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopColor: '#e2e8f0',
          borderTopWidth: 1,
          paddingTop: 4,
          paddingBottom: Math.max(insets.bottom, 4),
          height: 48 + Math.max(insets.bottom, 4),
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
          marginTop: 1,
          marginBottom: 2,
        },
        tabBarIconStyle: {
          marginTop: 2,
        },
        headerShown: true,
        headerStyle: {
          backgroundColor: '#2742d5',
          borderBottomColor: '#1e40af',
          borderBottomWidth: 1,
          elevation: 4,
          shadowOpacity: 0.1,
          shadowOffset: { width: 0, height: 2 },
          shadowRadius: 4,
        },
        headerTitleStyle: {
          fontSize: 18,
          fontWeight: '600',
          color: '#ffffff',
        },
        headerTitleAlign: 'left',
        headerLeft: () => (
          <View style={styles.headerLeft}>
            <Image
              source={require('./images/logo.png')}
              style={styles.headerLogo}
              resizeMode="contain"
            />
          </View>
        ),
        headerRight: () => null,
        headerTitle: () => null,
      }}>
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: 'Dashboard',
          tabBarIcon: ({color, size}) => <HomeIcon color={color} size={size} />,
          headerRight: () => (
            <View style={styles.headerRight}>
              <Text style={styles.headerTitle}>Dashboard</Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Transaction"
        component={TransactionScreen}
        options={{
          title: 'Transactions',
          tabBarIcon: ({color, size}) => <CreditCardIcon color={color} size={size} />,
          headerRight: () => (
            <View style={styles.headerRight}>
              <Text style={styles.headerTitle}>Transactions</Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{
          title: 'Analytics',
          tabBarIcon: ({color, size}) => <AnalyticsIcon color={color} size={size} />,
          headerRight: () => (
            <View style={styles.headerRight}>
              <Text style={styles.headerTitle}>Analytics</Text>
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          tabBarIcon: ({color, size}) => <SettingsIcon color={color} size={size} />,
          headerRight: () => (
            <View style={styles.headerRight}>
              <Text style={styles.headerTitle}>Settings</Text>
            </View>
          ),
        }}
      />
    </Tab.Navigator>
  );
};

const MainAppTabs: React.FC = () => {
  return <SafeTabNavigator />;
};

// Auth Stack Navigator
const AuthStack: React.FC = () => {
  return (
    <Stack.Navigator
      id={undefined}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="SignIn" component={SignInScreen} />
    </Stack.Navigator>
  );
};

// App Navigator (handles authentication flow)
const AppNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <AuthStack />;
  }

  return <MainAppTabs />;
};

// Main App Component
const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={PayvoTheme}>
        <StatusBar
          barStyle="dark-content"
          backgroundColor="#ffffff"
          translucent={false}
        />
        <AuthProvider>
          <NotificationProvider>
            <NavigationContainer>
              <AppNavigator />
            </NavigationContainer>
          </NotificationProvider>
        </AuthProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

const styles = StyleSheet.create({
  headerLeft: {
    paddingLeft: 16,
  },
  headerLogo: {
    width: 60,
    height: 60,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#2742d5',
  },
  loadingLogo: {
    width: 100,
    height: 100,
    marginBottom: 32,
  },
  loadingSpinner: {
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '500',
  },
  headerRight: {
    paddingRight: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
});

export default App;

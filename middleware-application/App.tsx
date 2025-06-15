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
import {SafeAreaProvider} from 'react-native-safe-area-context';
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
import PasswordChangeScreen from './src/screens/PasswordChangeScreen';

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

const MainAppTabs: React.FC = () => {
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
          paddingTop: 8,
          paddingBottom: 8,
          height: 70,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
          marginTop: 4,
        },
        header: () => null,
      }}>
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({color, size}) => <HomeIcon color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Transaction"
        component={TransactionScreen}
        options={{
          tabBarIcon: ({color, size}) => <CreditCardIcon color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{
          tabBarIcon: ({color, size}) => <AnalyticsIcon color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({color, size}) => <SettingsIcon color={color} size={size} />,
        }}
      />
    </Tab.Navigator>
  );
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
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <AuthStack />;
  }

  // Check if user needs to change password
  if (user?.password_change_required) {
    return (
      <Stack.Navigator
        id={undefined}
        screenOptions={{
          headerShown: true,
          header: () => (
            <View style={styles.headerContainer}>
              <View style={styles.headerContent}>
                <Image
                  source={require('./images/logo.png')}
                  style={styles.headerLogo}
                  resizeMode="contain"
                />
                <Text style={styles.logoSubtitle}>Payvo Middleware</Text>
              </View>
            </View>
          ),
        }}
      >
        <Stack.Screen name="PasswordChange" component={PasswordChangeScreen} />
      </Stack.Navigator>
    );
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
  headerContainer: {
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    paddingTop: 12,
    paddingBottom: 12,
    paddingHorizontal: 16,
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerLogo: {
    width: 32,
    height: 32,
    marginRight: 12,
  },
  logoSubtitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
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
    fontFamily: 'Inter',
  },
});

export default App;

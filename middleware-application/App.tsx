/**
 * Sample React Native App
 * https://github.com/facebook/react-native
 *
 * @format
 */

import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createBottomTabNavigator} from '@react-navigation/bottom-tabs';
import {MD3LightTheme, PaperProvider} from 'react-native-paper';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {StatusBar, View, Text, StyleSheet, Image} from 'react-native';
import { HomeIcon, CreditCardIcon, AnalyticsIcon, SettingsIcon } from './src/components/TabIcons';
import { NotificationProvider } from './src/components/NotificationProvider';

// Import screens
import HomeScreen from './src/screens/HomeScreen';
import TransactionScreen from './src/screens/TransactionScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Custom Header Component
const CustomHeader: React.FC<{title: string}> = ({title}) => {
  return (
    <View style={styles.headerContainer}>
      <View style={styles.headerContent}>
        <Image
          source={require('./images/logo.png')}
          style={styles.headerLogo}
          resizeMode="contain"
        />
        <Text style={styles.logoSubtitle}>{title}</Text>
      </View>
    </View>
  );
};

// Theme configuration using MD3LightTheme as base
const theme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#3b82f6',
    secondary: '#03DAC6',
    background: '#f8fafc',
    surface: '#FFFFFF',
    error: '#B00020',
    onPrimary: '#FFFFFF',
    onSecondary: '#000000',
    onBackground: '#000000',
    onSurface: '#000000',
    disabled: '#C7C7C7',
    placeholder: '#757575',
    backdrop: '#000000',
    notification: '#FF5722',
  },
};

const Tab = createBottomTabNavigator();

const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <NotificationProvider>
          <NavigationContainer>
            <StatusBar
              barStyle="light-content"
              backgroundColor={theme.colors.primary}
            />
            <Tab.Navigator
              screenOptions={({route}) => ({
                tabBarIcon: ({color, size}) => {
                  switch (route.name) {
                    case 'Home':
                      return <HomeIcon size={size} color={color} />;
                    case 'Transaction':
                      return <CreditCardIcon size={size} color={color} />;
                    case 'Analytics':
                      return <AnalyticsIcon size={size} color={color} />;
                    case 'Settings':
                      return <SettingsIcon size={size} color={color} />;
                    default:
                      return <HomeIcon size={size} color={color} />;
                  }
                },
                tabBarActiveTintColor: theme.colors.primary,
                tabBarInactiveTintColor: 'gray',
                headerStyle: {
                  backgroundColor: '#2742d5',
                  height: 80,
                  shadowColor: '#000',
                  shadowOffset: {
                    width: 0,
                    height: 2,
                  },
                  shadowOpacity: 0.1,
                  shadowRadius: 8,
                  elevation: 4,
                },
                headerTintColor: '#ffffff',
                headerTitleStyle: {
                  fontWeight: 'bold',
                },
              })}>
              <Tab.Screen
                name="Home"
                component={HomeScreen}
                options={{
                  headerTitle: () => <CustomHeader title="System Dashboard" />,
                }}
              />
              <Tab.Screen
                name="Transaction"
                component={TransactionScreen}
                options={{
                  headerTitle: () => <CustomHeader title="Smart Payment Intelligence" />,
                }}
              />
              <Tab.Screen
                name="Analytics"
                component={AnalyticsScreen}
                options={{
                  headerTitle: () => <CustomHeader title="Analytics Dashboard" />,
                }}
              />
              <Tab.Screen
                name="Settings"
                component={SettingsScreen}
                options={{
                  headerTitle: () => <CustomHeader title="Settings & Configuration" />,
                }}
              />
            </Tab.Navigator>
          </NavigationContainer>
        </NotificationProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 0,
    paddingHorizontal: 20,
  },
  headerContent: {
    alignItems: 'center',
  },
  headerLogo: {
    width: 50,
    height: 50,
  },
  logoSubtitle: {
    fontSize: 12,
    color: '#e2e8f0',
    marginTop: 0,
    textAlign: 'center',
  },
});

export default App;

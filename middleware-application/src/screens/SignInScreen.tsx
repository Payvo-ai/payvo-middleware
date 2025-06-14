import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Image,
} from 'react-native';
import {
  TextInput,
  Button,
  Card,
  Snackbar,
} from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';

const SignInScreen: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
  const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false);
  const [forgotPasswordSuccess, setForgotPasswordSuccess] = useState(false);

  const { signIn, forgotPassword } = useAuth();

  const handleSignIn = async () => {
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      await signIn({
        email: email.trim(),
        password: password.trim(),
      });

    } catch (err: any) {
      console.error('Sign in error:', err);
      setError(err.message || 'Sign in failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotPasswordEmail.trim()) {
      setError('Please enter your email address.');
      return;
    }

    try {
      setForgotPasswordLoading(true);
      setError('');

      await forgotPassword({
        email: forgotPasswordEmail.trim(),
      });

      setForgotPasswordSuccess(true);
      setShowForgotPassword(false);
      setForgotPasswordEmail('');

    } catch (err: any) {
      console.error('Forgot password error:', err);
      setError(err.message || 'Failed to send reset email. Please try again.');
    } finally {
      setForgotPasswordLoading(false);
    }
  };

  const resetForgotPassword = () => {
    setShowForgotPassword(false);
    setForgotPasswordEmail('');
    setError('');
  };

  if (showForgotPassword) {
    return (
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer}>
          <View style={styles.logoContainer}>
            <Image
              source={require('../../images/logo.png')}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.title}>Reset Password</Text>
            <Text style={styles.subtitle}>
              Enter your email address and we'll send you a link to reset your password.
            </Text>
          </View>

          <Card style={styles.card}>
            <Card.Content>
              <TextInput
                label="Email Address"
                value={forgotPasswordEmail}
                onChangeText={setForgotPasswordEmail}
                mode="outlined"
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                style={styles.input}
                disabled={forgotPasswordLoading}
              />

              <Button
                mode="contained"
                onPress={handleForgotPassword}
                style={styles.button}
                disabled={forgotPasswordLoading}
                loading={forgotPasswordLoading}
              >
                Send Reset Email
              </Button>

              <Button
                mode="text"
                onPress={resetForgotPassword}
                style={styles.linkButton}
                disabled={forgotPasswordLoading}
              >
                Back to Sign In
              </Button>
            </Card.Content>
          </Card>
        </ScrollView>

        <Snackbar
          visible={!!error}
          onDismiss={() => setError('')}
          duration={4000}
          style={styles.errorSnackbar}
        >
          {error}
        </Snackbar>
      </KeyboardAvoidingView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.logoContainer}>
          <Image
            source={require('../../images/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.title}>Payvo Employee Portal</Text>
          <Text style={styles.subtitle}>
            Sign in to access the Payvo Middleware Platform
          </Text>
        </View>

        <Card style={styles.card}>
          <Card.Content>
            <TextInput
              label="Email Address"
              value={email}
              onChangeText={setEmail}
              mode="outlined"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              style={styles.input}
              disabled={isLoading}
            />

            <TextInput
              label="Password"
              value={password}
              onChangeText={setPassword}
              mode="outlined"
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              autoComplete="password"
              style={styles.input}
              disabled={isLoading}
              right={
                <TextInput.Icon
                  icon={showPassword ? 'eye-off' : 'eye'}
                  onPress={() => setShowPassword(!showPassword)}
                />
              }
            />

            <Button
              mode="contained"
              onPress={handleSignIn}
              style={styles.button}
              disabled={isLoading}
              loading={isLoading}
            >
              Sign In
            </Button>

            <Button
              mode="text"
              onPress={() => setShowForgotPassword(true)}
              style={styles.linkButton}
              disabled={isLoading}
            >
              Forgot Password?
            </Button>
          </Card.Content>
        </Card>

        <View style={styles.footer}>
          <Text style={styles.footerText}>
            This app is restricted to Payvo AI employees only.
          </Text>
          <Text style={styles.footerText}>
            Contact your administrator for access.
          </Text>
        </View>
      </ScrollView>

      <Snackbar
        visible={!!error}
        onDismiss={() => setError('')}
        duration={4000}
        style={styles.errorSnackbar}
      >
        {error}
      </Snackbar>

      <Snackbar
        visible={forgotPasswordSuccess}
        onDismiss={() => setForgotPasswordSuccess(false)}
        duration={6000}
        style={styles.successSnackbar}
      >
        Password reset email sent! Check your inbox.
      </Snackbar>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2742d5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
    textAlign: 'center',
    fontFamily: 'Inter',
  },
  subtitle: {
    fontSize: 16,
    color: '#e2e8f0',
    textAlign: 'center',
    lineHeight: 24,
    fontFamily: 'Inter',
    fontWeight: '400',
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 12,
    marginBottom: 32,
    paddingVertical: 8,
  },
  input: {
    marginBottom: 20,
    backgroundColor: '#ffffff',
  },
  button: {
    marginTop: 8,
    marginBottom: 20,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#2742d5',
  },
  linkButton: {
    marginTop: 8,
  },
  footer: {
    alignItems: 'center',
    marginTop: 24,
    paddingHorizontal: 16,
  },
  footerText: {
    fontSize: 14,
    color: '#e2e8f0',
    textAlign: 'center',
    marginBottom: 6,
    fontFamily: 'Inter',
    fontWeight: '400',
    lineHeight: 20,
  },
  errorSnackbar: {
    backgroundColor: '#ef4444',
  },
  successSnackbar: {
    backgroundColor: '#10b981',
  },
});

export default SignInScreen;

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
  HelperText,
} from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';

const UsernameSetupScreen: React.FC = () => {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const { setUsername: setAuthUsername, user } = useAuth();

  const validateUsername = (value: string): string | null => {
    const trimmed = value.trim();

    if (trimmed.length < 2) {
      return 'Username must be at least 2 characters long.';
    }

    if (trimmed.length > 20) {
      return 'Username must be 20 characters or less.';
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
      return 'Username can only contain letters, numbers, hyphens, and underscores.';
    }

    return null;
  };

  const handleSetUsername = async () => {
    const validationError = validateUsername(username);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsLoading(true);
      setError('');

      await setAuthUsername(username.trim());

    } catch (err: any) {
      console.error('Set username error:', err);
      setError(err.message || 'Failed to set username. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const usernameError = username.length > 0 ? validateUsername(username) : null;

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
          <Text style={styles.title}>Welcome to Payvo!</Text>
          <Text style={styles.subtitle}>
            Hi {user?.email?.split('@')[0]}, let's set up your testing username.
          </Text>
        </View>

        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.cardTitle}>Choose Your Username</Text>
            <Text style={styles.cardDescription}>
              This username will identify all your test transactions and background location sessions.
              Choose something memorable and professional.
            </Text>

            <TextInput
              label="Username"
              value={username}
              onChangeText={setUsername}
              mode="outlined"
              autoCapitalize="none"
              autoComplete="username"
              style={styles.input}
              disabled={isLoading}
              error={!!usernameError}
              placeholder="e.g., john_doe, test_user_1"
            />

            <HelperText type={usernameError ? 'error' : 'info'} visible={true}>
              {usernameError || 'Letters, numbers, hyphens, and underscores only (2-20 characters)'}
            </HelperText>

            <View style={styles.exampleContainer}>
              <Text style={styles.exampleTitle}>Examples:</Text>
              <Text style={styles.exampleText}>• john_payvo</Text>
              <Text style={styles.exampleText}>• test-user-1</Text>
              <Text style={styles.exampleText}>• demo_employee</Text>
            </View>

            <Button
              mode="contained"
              onPress={handleSetUsername}
              style={styles.button}
              disabled={isLoading || !!usernameError || !username.trim()}
              loading={isLoading}
            >
              Set Username & Continue
            </Button>
          </Card.Content>
        </Card>

        <View style={styles.infoContainer}>
          <Text style={styles.infoTitle}>Important Notes:</Text>
          <Text style={styles.infoText}>
            • Your username will appear on all transaction records
          </Text>
          <Text style={styles.infoText}>
            • It will be used to identify your background location sessions
          </Text>
          <Text style={styles.infoText}>
            • You can only set this once, so choose carefully
          </Text>
          <Text style={styles.infoText}>
            • Contact your administrator if you need to change it later
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
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    width: 80,
    height: 80,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 22,
  },
  card: {
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1e293b',
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 20,
    lineHeight: 20,
  },
  input: {
    marginBottom: 4,
  },
  exampleContainer: {
    backgroundColor: '#f1f5f9',
    padding: 16,
    borderRadius: 8,
    marginTop: 8,
    marginBottom: 20,
  },
  exampleTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  exampleText: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 4,
  },
  button: {
    marginTop: 8,
    paddingVertical: 4,
  },
  infoContainer: {
    backgroundColor: '#eff6ff',
    padding: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1e40af',
    marginBottom: 4,
    lineHeight: 18,
  },
  errorSnackbar: {
    backgroundColor: '#dc2626',
  },
});

export default UsernameSetupScreen;

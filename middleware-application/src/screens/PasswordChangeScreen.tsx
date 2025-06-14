import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from 'react-native';
import {
  TextInput,
  Button,
  Card,
  Snackbar,
} from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';

const PasswordChangeScreen: React.FC = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const { changePassword, user } = useAuth();

  const validatePassword = (password: string): boolean => {
    if (password.length < 8) {
      setErrors(prev => ({...prev, newPassword: 'Password must be at least 8 characters long'}));
      return false;
    }
    if (!/(?=.*[a-z])/.test(password)) {
      setErrors(prev => ({...prev, newPassword: 'Password must contain at least one lowercase letter'}));
      return false;
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      setErrors(prev => ({...prev, newPassword: 'Password must contain at least one uppercase letter'}));
      return false;
    }
    if (!/(?=.*\d)/.test(password)) {
      setErrors(prev => ({...prev, newPassword: 'Password must contain at least one number'}));
      return false;
    }
    return true;
  };

  const handleChangePassword = async () => {
    try {
      setIsLoading(true);
      setErrors({});

      // Validate inputs
      if (!currentPassword) {
        setErrors(prev => ({...prev, currentPassword: 'Current password is required'}));
        return;
      }

      if (!newPassword) {
        setErrors(prev => ({...prev, newPassword: 'New password is required'}));
        return;
      }

      if (!confirmPassword) {
        setErrors(prev => ({...prev, confirmPassword: 'Please confirm your new password'}));
        return;
      }

      if (newPassword !== confirmPassword) {
        setErrors(prev => ({...prev, confirmPassword: 'Passwords do not match'}));
        return;
      }

      if (!validatePassword(newPassword)) {
        return;
      }

      if (currentPassword === newPassword) {
        setErrors(prev => ({...prev, newPassword: 'New password must be different from current password'}));
        return;
      }

      // Change password
      await changePassword({
        currentPassword,
        newPassword,
      });

      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      setSuccessMessage('Your password has been changed successfully!');

    } catch (error) {
      console.error('Password change error:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Failed to change password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContainer}
      showsVerticalScrollIndicator={false}
    >
      <Card style={styles.card}>
        <Card.Content>
          <Text style={styles.title}>Change Password</Text>
          <Text style={styles.subtitle}>
            Update your password for {user?.email}
          </Text>

          <View style={styles.form}>
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Current Password</Text>
              <TextInput
                value={currentPassword}
                onChangeText={setCurrentPassword}
                secureTextEntry
                mode="outlined"
                style={styles.textInput}
                disabled={isLoading}
                error={!!errors.currentPassword}
              />
              {errors.currentPassword && (
                <Text style={styles.errorText}>{errors.currentPassword}</Text>
              )}
            </View>

            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>New Password</Text>
              <TextInput
                value={newPassword}
                onChangeText={setNewPassword}
                secureTextEntry
                mode="outlined"
                style={styles.textInput}
                disabled={isLoading}
                error={!!errors.newPassword}
              />
              {errors.newPassword && (
                <Text style={styles.errorText}>{errors.newPassword}</Text>
              )}
            </View>

            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Confirm New Password</Text>
              <TextInput
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
                mode="outlined"
                style={styles.textInput}
                disabled={isLoading}
                error={!!errors.confirmPassword}
              />
              {errors.confirmPassword && (
                <Text style={styles.errorText}>{errors.confirmPassword}</Text>
              )}
            </View>

            <Button
              mode="contained"
              onPress={handleChangePassword}
              style={styles.changeButton}
              disabled={isLoading}
              loading={isLoading}
            >
              Change Password
            </Button>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.infoCard}>
        <Card.Content>
          <Text style={styles.infoTitle}>Password Requirements</Text>
          <View style={styles.requirementsList}>
            <Text style={styles.requirement}>• At least 8 characters long</Text>
            <Text style={styles.requirement}>• Contains uppercase and lowercase letters</Text>
            <Text style={styles.requirement}>• Contains at least one number</Text>
            <Text style={styles.requirement}>• Contains at least one special character</Text>
          </View>
        </Card.Content>
      </Card>

      <Snackbar
        visible={!!successMessage}
        onDismiss={() => setSuccessMessage('')}
        duration={4000}
        style={styles.successSnackbar}
      >
        {successMessage}
      </Snackbar>

      <Snackbar
        visible={!!errorMessage}
        onDismiss={() => setErrorMessage('')}
        duration={4000}
        style={styles.errorSnackbar}
      >
        {errorMessage}
      </Snackbar>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#2742d5',
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 24,
    paddingTop: 60,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    marginBottom: 24,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 12,
    paddingVertical: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
    fontFamily: 'Inter',
  },
  subtitle: {
    fontSize: 16,
    color: '#e2e8f0',
    marginBottom: 32,
    fontFamily: 'Inter',
    fontWeight: '400',
    lineHeight: 24,
  },
  form: {
    gap: 24,
  },
  inputSection: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
    fontFamily: 'Inter',
  },
  textInput: {
    backgroundColor: '#ffffff',
  },
  errorText: {
    fontSize: 13,
    color: '#ef4444',
    marginTop: 8,
    fontFamily: 'Inter',
    fontWeight: '500',
  },
  changeButton: {
    backgroundColor: '#2742d5',
    borderRadius: 16,
    paddingVertical: 6,
    marginTop: 16,
  },
  infoCard: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 12,
    paddingVertical: 8,
  },
  infoTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 20,
    fontFamily: 'Inter',
  },
  requirementsList: {
    gap: 12,
  },
  requirement: {
    fontSize: 15,
    color: '#64748b',
    lineHeight: 22,
    fontFamily: 'Inter',
    fontWeight: '400',
  },
  successSnackbar: {
    backgroundColor: '#10b981',
  },
  errorSnackbar: {
    backgroundColor: '#ef4444',
  },
});

export default PasswordChangeScreen;

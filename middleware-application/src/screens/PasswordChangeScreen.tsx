import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  TextInput,
  Button,
  Card,
  Title,
  Paragraph,
} from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';

const PasswordChangeScreen: React.FC = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

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
      setLoading(true);
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

      Alert.alert(
        'Success',
        'Your password has been changed successfully!',
        [{ text: 'OK' }]
      );

    } catch (error) {
      console.error('Password change error:', error);
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to change password. Please try again.',
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.title}>Change Password</Title>
          <Paragraph style={styles.subtitle}>
            Update your password for {user?.email}
          </Paragraph>

          <View style={styles.form}>
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Current Password</Text>
              <TextInput
                value={currentPassword}
                onChangeText={setCurrentPassword}
                style={styles.textInput}
                mode="outlined"
                secureTextEntry
                placeholder="Enter your current password"
                error={!!errors.currentPassword}
                disabled={loading}
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
                style={styles.textInput}
                mode="outlined"
                secureTextEntry
                placeholder="Enter your new password"
                error={!!errors.newPassword}
                disabled={loading}
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
                style={styles.textInput}
                mode="outlined"
                secureTextEntry
                placeholder="Confirm your new password"
                error={!!errors.confirmPassword}
                disabled={loading}
              />
              {errors.confirmPassword && (
                <Text style={styles.errorText}>{errors.confirmPassword}</Text>
              )}
            </View>

            <Button
              mode="contained"
              onPress={handleChangePassword}
              loading={loading}
              disabled={loading || !currentPassword || !newPassword || !confirmPassword}
              style={styles.changeButton}
              labelStyle={styles.changeButtonText}>
              Change Password
            </Button>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.infoCard}>
        <Card.Content>
          <Title style={styles.infoTitle}>Password Requirements</Title>
          <View style={styles.requirementsList}>
            <Text style={styles.requirement}>• At least 8 characters long</Text>
            <Text style={styles.requirement}>• Contains at least one lowercase letter</Text>
            <Text style={styles.requirement}>• Contains at least one uppercase letter</Text>
            <Text style={styles.requirement}>• Contains at least one number</Text>
            <Text style={styles.requirement}>• Different from your current password</Text>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    padding: 16,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    marginBottom: 16,
    shadowColor: '#afafaf',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 8,
    fontFamily: 'Inter',
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    marginBottom: 24,
    fontFamily: 'Inter',
  },
  form: {
    gap: 20,
  },
  inputSection: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    fontFamily: 'Inter',
  },
  textInput: {
    backgroundColor: '#ffffff',
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    marginTop: 4,
    fontFamily: 'Inter',
  },
  changeButton: {
    backgroundColor: '#2742d5',
    borderRadius: 12,
    paddingVertical: 4,
    marginTop: 8,
  },
  changeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    fontFamily: 'Inter',
  },
  infoCard: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    shadowColor: '#afafaf',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 4,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 16,
    fontFamily: 'Inter',
  },
  requirementsList: {
    gap: 8,
  },
  requirement: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
    fontFamily: 'Inter',
  },
});

export default PasswordChangeScreen;

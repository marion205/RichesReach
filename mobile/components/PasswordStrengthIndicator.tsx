import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface PasswordStrengthIndicatorProps {
  password: string;
}

interface PasswordStrength {
  score: number;
  label: string;
  color: string;
  requirements: {
    minLength: boolean;
    hasUpperCase: boolean;
    hasLowerCase: boolean;
    hasNumbers: boolean;
    hasSpecialChar: boolean;
  };
}

const PasswordStrengthIndicator: React.FC<PasswordStrengthIndicatorProps> = ({ password }) => {
  const calculateStrength = (password: string): PasswordStrength => {
    const requirements = {
      minLength: password.length >= 8,
      hasUpperCase: /[A-Z]/.test(password),
      hasLowerCase: /[a-z]/.test(password),
      hasNumbers: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const score = Object.values(requirements).filter(Boolean).length;
    
    let label = '';
    let color = '';
    
    if (score === 0) {
      label = '';
      color = '#e5e7eb';
    } else if (score <= 2) {
      label = 'Weak';
      color = '#ef4444';
    } else if (score <= 3) {
      label = 'Fair';
      color = '#f59e0b';
    } else if (score <= 4) {
      label = 'Good';
      color = '#3b82f6';
    } else {
      label = 'Strong';
      color = '#10b981';
    }

    return { score, label, color, requirements };
  };

  const strength = calculateStrength(password);

  if (!password) {
    return null;
  }

  return (
    <View style={styles.container}>
      {/* Strength Bar */}
      <View style={styles.strengthBarContainer}>
        <View style={styles.strengthBar}>
          <View 
            style={[
              styles.strengthBarFill, 
              { 
                width: `${(strength.score / 5) * 100}%`,
                backgroundColor: strength.color 
              }
            ]} 
          />
        </View>
        {strength.label && (
          <Text style={[styles.strengthLabel, { color: strength.color }]}>
            {strength.label}
          </Text>
        )}
      </View>

      {/* Requirements */}
      <View style={styles.requirementsContainer}>
        <Text style={styles.requirementsTitle}>Password Requirements:</Text>
        {Object.entries(strength.requirements).map(([key, met]) => (
          <View key={key} style={styles.requirementRow}>
            <View style={[
              styles.requirementDot, 
              { backgroundColor: met ? '#10b981' : '#e5e7eb' }
            ]} />
            <Text style={[
              styles.requirementText,
              { color: met ? '#10b981' : '#6b7280' }
            ]}>
              {getRequirementText(key)}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
};

const getRequirementText = (key: string): string => {
  switch (key) {
    case 'minLength':
      return 'At least 8 characters';
    case 'hasUpperCase':
      return 'One uppercase letter';
    case 'hasLowerCase':
      return 'One lowercase letter';
    case 'hasNumbers':
      return 'One number';
    case 'hasSpecialChar':
      return 'One special character';
    default:
      return '';
  }
};

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
  },
  strengthBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  strengthBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    marginRight: 12,
  },
  strengthBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthLabel: {
    fontSize: 14,
    fontWeight: '600',
    minWidth: 50,
  },
  requirementsContainer: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 12,
  },
  requirementsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  requirementDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 8,
  },
  requirementText: {
    fontSize: 12,
    flex: 1,
  },
});

export default PasswordStrengthIndicator;

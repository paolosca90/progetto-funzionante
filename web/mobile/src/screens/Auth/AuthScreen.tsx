import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Dimensions,
} from 'react-native';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import ThemedButton from '../../components/common/ThemedButton';
import ThemedText from '../../components/common/ThemedText';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { authService } from '../../services/authService';

const { width: screenWidth } = Dimensions.get('window');

WebBrowser.maybeCompleteAuthSession();

const AuthScreen: React.FC = () => {
  const { theme } = useTheme();
  const { state, login, register, googleLogin } = useAuth();

  const [mode, setMode] = useState<'login' | 'register' | 'forgotPassword'>('login');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Google Auth configuration
  const [request, response, promptAsync] = Google.useAuthRequest({
    androidClientId: '', // Configure in app.json
    iosClientId: '', // Configure in app.json
    webClientId: '', // Configure in app.json
  });

  useEffect(() => {
    if (response?.type === 'success') {
      const { authentication } = response;
      handleGoogleAuth(authentication?.accessToken);
    }
  }, [response]);

  const handleGoogleAuth = async (accessToken?: string) => {
    if (!accessToken) return;

    setIsSubmitting(true);
    try {
      // In a real implementation, you'd exchange the Google token
      // for user info and authenticate with your backend
      // For now, this is a placeholder

      await googleLogin(
        'google-user-id', // Would come from Google
        'user@example.com', // Would come from Google
        'John', // Would come from Google
        'Doe', // Would come from Google
      );

    } catch (error: any) {
      Alert.alert('Errore', error.message || 'Errore nell\'autenticazione Google');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async () => {
    if (mode === 'forgotPassword') {
      await handleForgotPassword();
      return;
    }

    // Validate form
    if (!formData.email || !formData.password) {
      Alert.alert('Errore', 'Email e password sono obbligatori');
      return;
    }

    if (mode === 'register') {
      if (!formData.confirmPassword || formData.password !== formData.confirmPassword) {
        Alert.alert('Errore', 'Le password non coincidono');
        return;
      }
      if (formData.password.length < 8) {
        Alert.alert('Errore', 'La password deve essere di almeno 8 caratteri');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (mode === 'login') {
        await login(formData.email.trim().toLowerCase(), formData.password);
      } else {
        await register({
          email: formData.email.trim().toLowerCase(),
          password: formData.password,
          firstName: formData.firstName.trim(),
          lastName: formData.lastName.trim(),
        });
      }
    } catch (error: any) {
      Alert.alert('Errore', error.message || 'Errore nell\'autenticazione');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!formData.email) {
      Alert.alert('Errore', 'Inserisci il tuo indirizzo email');
      return;
    }

    setIsSubmitting(true);
    try {
      await authService.forgotPassword(formData.email.trim().toLowerCase());
      Alert.alert(
        'Email Inviata',
        'Se l\'email è registrata, riceverai le istruzioni per il reset della password'
      );
      setMode('login');
    } catch (error: any) {
      Alert.alert('Errore', error.message || 'Errore nell\'invio dell\'email');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderForm = () => (
    <View style={styles.form}>
      {/* Email Input */}
      <View style={styles.inputContainer}>
        <ThemedText variant="mono" style={styles.label}>
          EMAIL
        </ThemedText>
        <View style={[styles.input, { borderColor: theme.colors.primary }]}>
          <ThemedText
            style={styles.inputText}
            onPress={() => {
              // In a real app, you'd show a text input overlay or similar
              Alert.prompt('Email', 'Inserisci il tuo indirizzo email', (email) => {
                setFormData(prev => ({ ...prev, email }));
              });
            }}
          >
            {formData.email || 'user@example.com'}
          </ThemedText>
        </View>
      </View>

      {/* Password Input (conditionally rendered) */}
      {(mode === 'login' || mode === 'register') && (
        <View style={styles.inputContainer}>
          <ThemedText variant="mono" style={styles.label}>
            PASSWORD
          </ThemedText>
          <View style={[styles.input, { borderColor: theme.colors.primary }]}>
            <ThemedText style={styles.inputText}>
              {'••••••••'}
            </ThemedText>
          </View>
        </View>
      )}

      {/* Confirm Password for Registration */}
      {mode === 'register' && (
        <View style={styles.inputContainer}>
          <ThemedText variant="mono" style={styles.label}>
            CONFERMA PASSWORD
          </ThemedText>
          <View style={[styles.input, { borderColor: theme.colors.primary }]}>
            <ThemedText style={styles.inputText}>
              {'••••••••'}
            </ThemedText>
          </View>
        </View>
      )}

      {/* Name fields for Registration */}
      {mode === 'register' && (
        <>
          <View style={styles.inputContainer}>
            <ThemedText variant="mono" style={styles.label}>
              NOME
            </ThemedText>
            <View style={[styles.input, { borderColor: theme.colors.primary }]}>
              <ThemedText style={styles.inputText}>
                {formData.firstName || 'Nome'}
              </ThemedText>
            </View>
          </View>

          <View style={styles.inputContainer}>
            <ThemedText variant="mono" style={styles.label}>
              COGNOME
            </ThemedText>
            <View style={[styles.input, { borderColor: theme.colors.primary }]}>
              <ThemedText style={styles.inputText}>
                {formData.lastName || 'Cognome'}
              </ThemedText>
            </View>
          </View>
        </>
      )}

      {/* Submit Button */}
      <ThemedButton
        title={
          mode === 'login' ? 'ACCEDI' :
          mode === 'register' ? 'REGISTRATI' :
          'INVIA EMAIL RESET'
        }
        onPress={handleSubmit}
        loading={isSubmitting}
        style={styles.submitButton}
      />
    </View>
  );

  const renderModeToggle = () => (
    <View style={styles.modeToggle}>
      <ThemedButton
        title="ACCEDI"
        variant={mode === 'login' ? 'primary' : 'secondary'}
        onPress={() => setMode('login')}
        style={styles.modeButton}
      />
      <ThemedButton
        title="REGISTRATI"
        variant={mode === 'register' ? 'primary' : 'secondary'}
        onPress={() => setMode('register')}
        style={styles.modeButton}
      />
      <ThemedButton
        title="PASSWORD PERSA"
        variant={mode === 'forgotPassword' ? 'primary' : 'secondary'}
        onPress={() => setMode('forgotPassword')}
        style={styles.modeButton}
      />
    </View>
  );

  if (state.isLoading) {
    return <LoadingSpinner fullScreen text="Inizializzazione..." />;
  }

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Logo/Title */}
        <View style={styles.header}>
          <ThemedText variant="title" weight="bold" style={{ color: theme.colors.primary }}>
            AI CASH REVOLUTION
          </ThemedText>
          <ThemedText variant="mono" style={styles.subtitle}>
            INTELLIGENZA ARTIFICIALE PER TRADING PROFESSIONALE
          </ThemedText>
        </View>

        {/* Mode Toggle */}
        {renderModeToggle()}

        {/* Form */}
        {renderForm()}

        {/* Google Auth Button */}
        {(mode === 'login' || mode === 'register') && (
          <View style={styles.googleSection}>
            <ThemedText variant="caption" style={styles.orText}>OPPURE</ThemedText>
            <ThemedButton
              title="CONTINUA CON GOOGLE"
              variant="secondary"
              onPress={() => promptAsync()}
              disabled={!request}
              loading={isSubmitting}
              style={styles.googleButton}
            />
          </View>
        )}

        {/* Footer */}
        <View style={styles.footer}>
          <ThemedText variant="mono" style={{ color: theme.colors.textSecondary, fontSize: 10 }}>
            POWERED BY MATRIX AI • V1.0.0 • SECURE & ENCRYPTED
          </ThemedText>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    marginTop: 60,
    marginBottom: 40,
  },
  subtitle: {
    marginTop: 10,
    textAlign: 'center',
    fontSize: 12,
    textTransform: 'uppercase',
    opacity: 0.8,
  },
  modeToggle: {
    flexDirection: 'row',
    marginBottom: 40,
    gap: 8,
  },
  modeButton: {
    flex: 1,
    minHeight: 40,
  },
  form: {
    marginBottom: 30,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 12,
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    justifyContent: 'center',
    paddingHorizontal: 16,
    backgroundColor: '#141414',
  },
  inputText: {
    fontSize: 16,
    color: '#ffffff',
  },
  submitButton: {
    marginTop: 20,
    minHeight: 50,
  },
  googleSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  orText: {
    marginVertical: 20,
    opacity: 0.6,
  },
  googleButton: {
    width: '100%',
    minHeight: 50,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footer: {
    alignItems: 'center',
    marginTop: 20,
  },
});

export default AuthScreen;
import React, { useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
  Alert,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import ThemedButton from '../../components/common/ThemedButton';
import ThemedText from '../../components/common/ThemedText';
import ThemedCard from '../../components/common/ThemedCard';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import TradingViewWidget from '../../components/charts/TradingViewWidget';
import SignalCard from '../../components/signals/SignalCard';
import { useAuth } from '../../context/AuthContext';
import { useSignals } from '../../context/SignalContext';
import { useTheme } from '../../context/ThemeContext';
import { instrumentService } from '../../services/instrumentService';

interface Instrument {
  id: string;
  symbol: string;
  name: string;
  type: string;
  category: string;
}

const DashboardScreen: React.FC = () => {
  const navigation = useNavigation();
  const { theme } = useTheme();
  const { state: authState, logout } = useAuth();
  const { state: signalState, generateSignal, fetchActiveSignals, selectInstrument } = useSignals();

  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedInstrument, setSelectedInstrument] = useState<string>('EURUSD');
  const [isLoadingInstruments, setIsLoadingInstruments] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoadingInstruments(true);

      // Load instruments
      const instrumentsResponse = await instrumentService.getInstruments();
      setInstruments(instrumentsResponse.data.instruments);

      // Load active signals
      await fetchActiveSignals();

    } catch (error: any) {
      console.error('Failed to load dashboard data:', error);
      Alert.alert('Errore', 'Impossibile caricare i dati del dashboard');
    } finally {
      setIsLoadingInstruments(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      loadDashboardData(),
    ]);
    setRefreshing(false);
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Sei sicuro di voler uscire?',
      [
        { text: 'Annulla', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              await logout();
            } catch (error: any) {
              Alert.alert('Errore', error.message || 'Errore durante il logout');
            }
          }
        }
      ]
    );
  };

  const handleInstrumentSelect = (instrumentId: string) => {
    setSelectedInstrument(instrumentId);
    selectInstrument(instrumentId);
  };

  const handleGenerateSignal = async () => {
    try {
      navigation.navigate('SignalGeneration' as never);
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };

  const handleSignalPress = (signal: any) => {
    navigation.navigate('SignalDetail' as never, { signal } as never);
  };

  const renderInstrumentItem = ({ item }: { item: Instrument }) => (
    <TouchableOpacity
      style={[
        styles.instrumentItem,
        {
          borderColor: selectedInstrument === item.id ? theme.colors.primary : theme.colors.border,
          backgroundColor: selectedInstrument === item.id ? '#00ff8810' : 'transparent',
        },
      ]}
      onPress={() => handleInstrumentSelect(item.id)}
    >
      <View style={styles.instrumentInfo}>
        <ThemedText variant="mono" weight="bold" style={{ color: theme.colors.primary }}>
          {item.symbol}
        </ThemedText>
        <ThemedText variant="caption" style={{ color: theme.colors.textSecondary }}>
          {item.name}
        </ThemedText>
        <View style={styles.categoryBadge}>
          <ThemedText variant="mono" style={{ color: theme.colors.secondary, fontSize: 8 }}>
            {item.category.toUpperCase()}
          </ThemedText>
        </View>
      </View>
      {selectedInstrument === item.id && (
        <Ionicons name="checkmark-circle" size={20} color={theme.colors.primary} />
      )}
    </TouchableOpacity>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.headerTop}>
        <View style={styles.userInfo}>
          <ThemedText variant="subtitle" weight="bold">
            BENEDICTO, {authState.user?.firstName?.toUpperCase() || 'USER'}
          </ThemedText>
          <View style={[styles.subscriptionBadge, { borderColor: theme.colors.primary }]}>
            <ThemedText variant="mono" style={{ color: theme.colors.primary, fontSize: 10 }}>
              {authState.user?.subscriptionStatus?.toUpperCase() || 'TRIAL'}
            </ThemedText>
          </View>
        </View>

        <TouchableOpacity
          style={styles.profileButton}
          onPress={() => navigation.navigate('Profile' as never)}
        >
          <Ionicons name="person-circle" size={32} color={theme.colors.primary} />
        </TouchableOpacity>
      </View>

      {/* TradingView Chart */}
      <View style={styles.chartContainer}>
        <TradingViewWidget
          symbol={selectedInstrument}
          theme="dark"
          height={200}
        />
      </View>

      {/* Instruments List */}
      <View style={styles.instrumentsSection}>
        <ThemedText variant="subtitle" weight="bold" style={styles.sectionTitle}>
          STRUMENTI DISPONIBILI
        </ThemedText>

        {isLoadingInstruments ? (
          <LoadingSpinner text="Caricamento strumenti..." />
        ) : (
          <FlatList
            data={instruments.slice(0, 6)} // Show first 6 instruments
            horizontal
            showsHorizontalScrollIndicator={false}
            keyExtractor={(item) => item.id}
            renderItem={renderInstrumentItem}
            contentContainerStyle={styles.instrumentsList}
          />
        )}
      </View>
    </View>
  );

  const renderActiveSignals = () => (
    <View style={styles.signalsSection}>
      <View style={styles.signalsHeader}>
        <ThemedText variant="subtitle" weight="bold">SEGNALI ATTIVI</ThemedText>
        <ThemedButton
          title="GENERA SEGNALE"
          onPress={handleGenerateSignal}
          variant="primary"
          size="small"
          loading={signalState.isGeneratingSignal}
        />
      </View>

      {signalState.isGeneratingSignal ? (
        <ThemedCard style={styles.generatingCard}>
          <LoadingSpinner text="Analisi in corso..." />
          <ThemedText variant="mono" style={{ color: theme.colors.secondary, marginTop: 10 }}>
            INTERROGAZIONE DEI MODULI DI ANALISI...
          </ThemedText>
        </ThemedCard>
      ) : signalState.activeSignals.length > 0 ? (
        signalState.activeSignals.slice(0, 3).map((signal) => (
          <SignalCard
            key={signal.id}
            signal={signal}
            onPress={() => handleSignalPress(signal)}
          />
        ))
      ) : (
        <ThemedCard>
          <View style={styles.emptySignals}>
            <Ionicons name="trending-up" size={48} color={theme.colors.disabled} />
            <ThemedText variant="subtitle" style={{ color: theme.colors.textSecondary, marginTop: 10 }}>
              NESSUN SEGNALE ATTIVO
            </ThemedText>
            <ThemedText variant="caption" style={{ color: theme.colors.disabled, marginTop: 5 }}>
              Genera il tuo primo segnale per iniziare
            </ThemedText>
            <ThemedButton
              title="GENERA ORA"
              onPress={handleGenerateSignal}
              variant="secondary"
              size="small"
              style={{ marginTop: 15 }}
            />
          </View>
        </ThemedCard>
      )}
    </View>
  );

  const renderQuickActions = () => (
    <View style={styles.quickActions}>
      <ThemedText variant="subtitle" weight="bold" style={styles.sectionTitle}>
        AZIONI RAPIDE
      </ThemedText>

      <View style={styles.actionGrid}>
        <TouchableOpacity
          style={styles.actionCard}
          onPress={handleGenerateSignal}
        >
          <Ionicons name="flash" size={24} color={theme.colors.primary} />
          <ThemedText variant="mono" style={{ color: theme.colors.primary, marginTop: 8 }}>
            SEGNALE RAPIDO
          </ThemedText>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Profile' as never)}
        >
          <Ionicons name="person" size={24} color={theme.colors.primary} />
          <ThemedText variant="mono" style={{ color: theme.colors.primary, marginTop: 8 }}>
            PROFILO
          </ThemedText>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={() => navigation.navigate('Settings' as never)}
        >
          <Ionicons name="settings" size={24} color={theme.colors.primary} />
          <ThemedText variant="mono" style={{ color: theme.colors.primary, marginTop: 8 }}>
            IMPOSTAZIONI
          </ThemedText>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionCard}
          onPress={handleLogout}
        >
          <Ionicons name="log-out" size={24} color={theme.colors.error} />
          <ThemedText variant="mono" style={{ color: theme.colors.error, marginTop: 8 }}>
            LOGOUT
          </ThemedText>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (authState.isLoading) {
    return <LoadingSpinner fullScreen text="Caricamento dashboard..." />;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={theme.colors.primary}
            colors={[theme.colors.primary]}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {renderHeader()}
        {renderActiveSignals()}
        {renderQuickActions()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  userInfo: {
    flex: 1,
  },
  subscriptionBadge: {
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginTop: 4,
    alignSelf: 'flex-start',
  },
  profileButton: {
    marginLeft: 16,
  },
  chartContainer: {
    marginBottom: 20,
  },
  instrumentsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    marginBottom: 16,
  },
  instrumentsList: {
    paddingHorizontal: 4,
  },
  instrumentItem: {
    width: 120,
    height: 80,
    borderWidth: 1,
    borderRadius: 8,
    marginRight: 8,
    padding: 8,
    justifyContent: 'space-between',
  },
  instrumentInfo: {
    flex: 1,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    marginTop: 4,
    paddingHorizontal: 4,
    paddingVertical: 1,
    backgroundColor: 'rgba(0, 255, 136, 0.1)',
    borderRadius: 3,
  },
  signalsSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  signalsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  generatingCard: {
    padding: 20,
    alignItems: 'center',
  },
  emptySignals: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  quickActions: {
    paddingHorizontal: 16,
    marginBottom: 40,
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  actionCard: {
    width: '48%',
    aspectRatio: 1,
    backgroundColor: '#141414',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#00ff88',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    padding: 16,
  },
});

export default DashboardScreen;
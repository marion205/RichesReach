import React, { useMemo, useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Linking,
  Alert,
  ActivityIndicator,
  TextInput,
  Platform,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Bank = {
  id: string;
  name: string;
  logoUrl?: string | null;
  minApr: number | null;   // decimal (0.065 => 6.5%)
  maxApr: number | null;
  minLtv: number | null;   // decimal (0.5 => 50%)
  maxLtv: number | null;
  notes?: string | null;
  regions?: string[] | null; // e.g. ["US","EU","CA"]
  minLoanUsd?: number | null;
};

type BanksQueryData = { sblocBanks: Bank[] };
type CreateSessionVars = { bankId: string; amountUsd: number };
type CreateSessionPayload = {
  success: boolean;
  applicationUrl?: string | null;
  sessionId?: string | null;
  error?: string | null;
};
type CreateSessionData = { createSblocSession: CreateSessionPayload };

const SBLOC_BANKS = gql`
  query SblocBanks {
    sblocBanks {
      id
      name
      logoUrl
      minApr
      maxApr
      minLtv
      maxLtv
      notes
      regions
      minLoanUsd
    }
  }
`;

const CREATE_SBLOC_SESSION = gql`
  mutation CreateSblocSession($bankId: ID!, $amountUsd: Int!) {
    createSblocSession(bankId: $bankId, amountUsd: $amountUsd) {
      success
      applicationUrl
      sessionId
      error
    }
  }
`;

function pct(v?: number | null, digits: number = 0) {
  if (v == null || Number.isNaN(v)) return '—';
  return `${(v * 100).toFixed(digits)}%`;
}
function usd(n: number) {
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
  } catch {
    return `$${Math.round(n).toLocaleString()}`;
  }
}

const REGION_ALL = 'ALL';

// Storage keys
const K_AMOUNT = 'sbloc.amount';
const K_REGION = 'sbloc.region';
const K_ONLY_ELIG = 'sbloc.onlyEligible';

// Analytics tracking
const track = (event: string, props?: Record<string, any>) => {
  // plug in Segment/Amplitude later
  console.log('[analytics]', event, props || {});
};

export default function SblocBankSelectionScreen({ route, navigation }: any) {
  const initialAmount = route?.params?.amountUsd ?? 25000;
  const [amount, setAmount] = useState<string>(String(initialAmount));
  const [region, setRegion] = useState<string>(REGION_ALL);
  const [onlyEligible, setOnlyEligible] = useState<boolean>(false);
  const [creatingById, setCreatingById] = useState<Record<string, boolean>>({});

  // normalize amount → integer USD with clamping
  const amountUsd = useMemo(() => {
    const n = parseInt((amount || '').replace(/[^\d]/g, ''), 10);
    return Number.isFinite(n) ? Math.max(0, Math.min(50_000_000, n)) : 0;
  }, [amount]);

  const { data, loading, error, refetch } = useQuery<BanksQueryData>(SBLOC_BANKS, {
    fetchPolicy: 'cache-and-network',
  });

  const [createSession, { loading: creatingGlobal }] =
    useMutation<CreateSessionData, CreateSessionVars>(CREATE_SBLOC_SESSION);

  const banks = data?.sblocBanks ?? [];

  // build region choices from data
  const regionOptions = useMemo(() => {
    const set = new Set<string>();
    banks.forEach(b => (b.regions ?? []).forEach(r => set.add(r)));
    return [REGION_ALL, ...Array.from(set).sort()];
  }, [banks]);

  // filter by region + eligibility + sort by APR, then min loan
  const filteredSorted = useMemo(() => {
    const list = banks
      .filter(b => region === REGION_ALL ? true : (b.regions ?? []).includes(region))
      .filter(b => !onlyEligible ? true : (b.minLoanUsd == null || amountUsd >= b.minLoanUsd!));
    return list.sort((a, b) => {
      const aApr = a.minApr ?? Number.POSITIVE_INFINITY;
      const bApr = b.minApr ?? Number.POSITIVE_INFINITY;
      if (aApr !== bApr) return aApr - bApr;
      const aMin = a.minLoanUsd ?? Number.POSITIVE_INFINITY;
      const bMin = b.minLoanUsd ?? Number.POSITIVE_INFINITY;
      return aMin - bMin;
    });
  }, [banks, region, amountUsd, onlyEligible]);

  const startApp = useCallback(
    async (bankId: string) => {
      if (creatingById[bankId]) return; // debounce per-item
      setCreatingById(s => ({ ...s, [bankId]: true }));
      try {
        track('sbloc_start_app', { bankId, amountUsd });
        const res = await createSession({ variables: { bankId, amountUsd } });
        const payload = res.data?.createSblocSession;
        if (!payload?.success || !payload?.applicationUrl) {
          Alert.alert('Unable to continue', payload?.error || 'Please try again in a moment.');
          return;
        }
        const canOpen = await Linking.canOpenURL(payload.applicationUrl);
        if (!canOpen) {
          Alert.alert('Invalid link', 'We could not open the application URL from the provider.');
          return;
        }
        await Linking.openURL(payload.applicationUrl);
        navigation.navigate('SblocStatus', { sessionId: payload.sessionId });
      } catch (e: any) {
        Alert.alert('Error', e?.message || 'Something went wrong while starting the application.');
      } finally {
        setCreatingById(s => ({ ...s, [bankId]: false }));
      }
    },
    [amountUsd, createSession, creatingById, navigation]
  );

  // hydrate from AsyncStorage on mount
  useEffect(() => {
    (async () => {
      const [a, r, e] = await Promise.all([
        AsyncStorage.getItem(K_AMOUNT),
        AsyncStorage.getItem(K_REGION),
        AsyncStorage.getItem(K_ONLY_ELIG),
      ]);
      if (a) setAmount(a);
      if (r) setRegion(r);
      if (e) setOnlyEligible(e === '1');
    })();
  }, []);

  // persist to AsyncStorage on change
  useEffect(() => { AsyncStorage.setItem(K_AMOUNT, amount || ''); }, [amount]);
  useEffect(() => { AsyncStorage.setItem(K_REGION, region); }, [region]);
  useEffect(() => { AsyncStorage.setItem(K_ONLY_ELIG, onlyEligible ? '1' : '0'); }, [onlyEligible]);

  // small UX polish: auto-select region if only one exists (besides ALL)
  useEffect(() => {
    if (regionOptions.length === 2 && region === REGION_ALL) {
      setRegion(regionOptions[1]);
    }
  }, [regionOptions, region]);

  // analytics tracking
  useEffect(() => {
    track('sbloc_banks_view', { region, amountUsd, onlyEligible });
  }, [region, amountUsd, onlyEligible]);

  if (loading && !data) {
    return (
      <View style={{ flex: 1, padding: 16, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8 }}>Loading providers…</Text>
      </View>
    );
  }
  if (error) {
    return (
      <View style={{ flex: 1, padding: 16, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ marginBottom: 12 }}>Couldn't load providers.</Text>
        <TouchableOpacity
          onPress={() => refetch()}
          style={{ backgroundColor: '#111', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 8 }}
        >
          <Text style={{ color: '#fff', fontWeight: '600' }}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, padding: 16 }}>
      {/* Filters */}
      <View style={{ marginBottom: 12 }}>
        <Text style={{ fontSize: 18, fontWeight: '700' }} accessibilityRole="header">
          SBLOC Request
        </Text>
        <Text style={{ color: '#666', marginBottom: 8 }}>
          Compare providers. Continue to a secure, hosted application.
        </Text>

        <View style={{ flexDirection: 'row', gap: 8 }}>
          {/* Amount input */}
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Amount</Text>
            <TextInput
              value={amount}
              onChangeText={setAmount}
              keyboardType={Platform.select({ ios: 'number-pad', android: 'numeric', default: 'numeric' })}
              placeholder="25000"
              inputMode="numeric"
              style={{
                borderWidth: 1,
                borderColor: '#ddd',
                paddingVertical: 8,
                paddingHorizontal: 10,
                borderRadius: 8,
                backgroundColor: '#fff',
              }}
            />
          </View>

          {/* Region select (simple chips) */}
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>Region</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
              {regionOptions.map(r => {
                const selected = r === region;
                return (
                  <TouchableOpacity
                    key={r}
                    onPress={() => setRegion(r)}
                    style={{
                      paddingHorizontal: 10,
                      paddingVertical: 6,
                      borderRadius: 16,
                      borderWidth: 1,
                      borderColor: selected ? '#111' : '#ccc',
                      backgroundColor: selected ? '#111' : '#fff',
                    }}
                  >
                    <Text style={{ color: selected ? '#fff' : '#111', fontSize: 12 }}>
                      {r === REGION_ALL ? 'All' : r}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        </View>

        <Text style={{ marginTop: 6, color: '#888', fontSize: 12 }}>
          Request • {usd(amountUsd)}
        </Text>

        <TouchableOpacity
          onPress={() => setOnlyEligible(v => !v)}
          style={{ 
            marginTop: 8, 
            alignSelf: 'flex-start', 
            paddingHorizontal: 10, 
            paddingVertical: 6, 
            borderRadius: 16, 
            borderWidth: 1, 
            borderColor: '#ccc', 
            backgroundColor: onlyEligible ? '#111' : '#fff' 
          }}
        >
          <Text style={{ color: onlyEligible ? '#fff' : '#111', fontSize: 12 }}>
            Show only eligible
          </Text>
        </TouchableOpacity>
      </View>

      {/* List */}
      {filteredSorted.length === 0 ? (
        <Text style={{ color: '#666' }}>No providers available{region !== REGION_ALL ? ` for ${region}` : ''}.</Text>
      ) : (
        <FlatList
          data={filteredSorted}
          keyExtractor={(b) => b.id}
          contentContainerStyle={{ paddingBottom: 24 }}
          renderItem={({ item }) => {
            const creating = !!creatingById[item.id] || creatingGlobal;

            const aprRange =
              item.minApr == null && item.maxApr == null
                ? 'APR —'
                : `APR ${pct(item.minApr, 2)}–${pct(item.maxApr, 2)}`;
            const ltvRange =
              item.minLtv == null && item.maxLtv == null
                ? 'LTV —'
                : `LTV ${pct(item.minLtv)}–${pct(item.maxLtv)}`;
            const minLoan = item.minLoanUsd ?? null;

            const belowMin = minLoan != null && amountUsd > 0 && amountUsd < minLoan;
            const disabled = creating || belowMin || amountUsd <= 0;

            return (
              <View
                style={{
                  backgroundColor: '#fff',
                  padding: 14,
                  borderRadius: 12,
                  marginBottom: 12,
                  borderWidth: 1,
                  borderColor: '#eee',
                }}
              >
                <Text style={{ fontWeight: '700' }}>{item.name}</Text>
                <Text style={{ color: '#444', marginTop: 4 }}>
                  {ltvRange} • {aprRange}
                  {minLoan ? ` • Min ${usd(minLoan)}` : ''}
                </Text>
                {!!item.notes && (
                  <Text style={{ color: '#666', marginTop: 6 }} numberOfLines={2}>
                    {item.notes}
                  </Text>
                )}
                {!!item.regions?.length && (
                  <Text style={{ color: '#888', marginTop: 4, fontSize: 12 }}>
                    Regions: {item.regions.join(', ')}
                  </Text>
                )}

                {belowMin && (
                  <Text style={{ color: '#B00020', marginTop: 8, fontSize: 12 }}>
                    Minimum loan for {item.name} is {usd(minLoan!)}. Increase the amount to continue.
                  </Text>
                )}

                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel={`Continue to application for ${item.name}`}
                  disabled={disabled}
                  onPress={() => startApp(item.id)}
                  style={{
                    marginTop: 10,
                    backgroundColor: disabled ? '#777' : '#111',
                    padding: 12,
                    borderRadius: 8,
                    opacity: disabled ? 0.8 : 1,
                  }}
                >
                  {creating ? (
                    <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 }}>
                      <ActivityIndicator />
                      <Text style={{ color: '#fff', fontWeight: '600' }}>Opening…</Text>
                    </View>
                  ) : (
                    <Text style={{ color: '#fff', textAlign: 'center', fontWeight: '600' }}>
                      Continue to application
                    </Text>
                  )}
                </TouchableOpacity>

                <Text style={{ marginTop: 8, fontSize: 11, color: '#888' }}>
                  You'll complete KYC and agree to terms with {item.name}. We do not make credit decisions.
                </Text>
              </View>
            );
          }}
          ListFooterComponent={<View style={{ height: 8 }} />}
        />
      )}
    </View>
  );
}
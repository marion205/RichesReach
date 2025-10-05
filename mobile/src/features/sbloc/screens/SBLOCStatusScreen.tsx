import React, { useMemo, useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, Linking, Alert } from 'react-native';
import { useQuery, gql } from '@apollo/client';
import { safeFormatDateTime } from '../../../utils/dateUtils';

type SessionStatus =
  | 'CREATED'
  | 'APPLICATION_STARTED'
  | 'KYC_PENDING'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'CONDITIONAL_APPROVAL'
  | 'DECLINED'
  | 'CANCELLED'
  | 'EXPIRED';

type Session = {
  sessionId: string;
  status: SessionStatus;
  applicationUrl?: string | null;
  lastUpdatedIso?: string | null;
  lenderName?: string | null;
  requestedAmountUsd?: number | null;
  message?: string | null; // optional backend message/tips
};

type SessionQueryData = { sblocSession: Session };
type SessionQueryVars = { sessionId: string };

const GET_SBLOC_SESSION = gql`
  query GetSblocSession($sessionId: ID!) {
    sblocSession(sessionId: $sessionId) {
      sessionId
      status
      applicationUrl
      lastUpdatedIso
      lenderName
      requestedAmountUsd
      message
    }
  }
`;

function statusText(s: SessionStatus) {
  switch (s) {
    case 'CREATED': return 'Created';
    case 'APPLICATION_STARTED': return 'Application in progress';
    case 'KYC_PENDING': return 'KYC pending';
    case 'UNDER_REVIEW': return 'Under review';
    case 'APPROVED': return 'Approved';
    case 'CONDITIONAL_APPROVAL': return 'Conditional approval';
    case 'DECLINED': return 'Declined';
    case 'CANCELLED': return 'Cancelled';
    case 'EXPIRED': return 'Expired';
    default: return s;
  }
}

function usd(n?: number | null) {
  if (!n) return '—';
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);
  } catch { return `$${Math.round(n).toLocaleString()}`; }
}

// Analytics tracking
const track = (event: string, props?: Record<string, any>) => {
  // plug in Segment/Amplitude later
  console.log('[analytics]', event, props || {});
};

export default function SblocStatusScreen({ route, navigation }: any) {
  const sessionId: string = route?.params?.sessionId;

  const { data, loading, error, refetch, startPolling, stopPolling } = useQuery<SessionQueryData, SessionQueryVars>(
    GET_SBLOC_SESSION,
    {
      variables: { sessionId },
      pollInterval: 5000, // 5s polling
      fetchPolicy: 'cache-and-network',
    }
  );

  const session = data?.sblocSession;

  // Stop polling on terminal states
  const terminal = new Set(['APPROVED', 'DECLINED', 'CANCELLED', 'EXPIRED']);
  useEffect(() => {
    if (session && terminal.has(session.status)) {
      stopPolling();
    }
  }, [session, stopPolling]);

  // Analytics tracking
  useEffect(() => {
    if (session) {
      track('sbloc_status_view', { sessionId, status: session.status });
    }
  }, [sessionId, session]);

  const cta = useMemo(() => {
    if (!session) return null;

    // CTA logic: resume application if not finished; show offer if approved
    if (['CREATED', 'APPLICATION_STARTED', 'KYC_PENDING'].includes(session.status)) {
      return {
        label: 'Resume application',
        action: async () => {
          const url = session.applicationUrl;
          if (!url) { Alert.alert('Link unavailable', 'Try again later.'); return; }
          const can = await Linking.canOpenURL(url);
          if (!can) { Alert.alert('Invalid link', 'We could not open the application URL.'); return; }
          await Linking.openURL(url);
        },
      };
    }
    if (['UNDER_REVIEW', 'CONDITIONAL_APPROVAL'].includes(session.status)) {
      return { label: 'Refresh status', action: () => refetch() };
    }
    if (session.status === 'APPROVED') {
      return { label: 'View next steps', action: () => Alert.alert('Next steps', 'Your lender will contact you to finalize docs and funding.') };
    }
    return null;
  }, [session, refetch]);

  if (!sessionId) {
    return (
      <View style={{ flex: 1, padding: 16, justifyContent: 'center', alignItems: 'center' }}>
        <Text>Missing session ID.</Text>
      </View>
    );
  }

  if (loading && !data) {
    return (
      <View style={{ flex: 1, padding: 16, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 8 }}>Checking status…</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={{ flex: 1, padding: 16, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ marginBottom: 12 }}>Unable to fetch status.</Text>
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
      <Text style={{ fontSize: 18, fontWeight: '700' }}>SBLOC Application Status</Text>

      {session ? (
        <View style={{ marginTop: 12, backgroundColor: '#fff', padding: 14, borderRadius: 12, borderWidth: 1, borderColor: '#eee' }}>
          {!!session.lenderName && <Text style={{ fontWeight: '700' }}>{session.lenderName}</Text>}
          <Text style={{ marginTop: 4, color: '#444' }}>
            Status: {statusText(session.status)}
          </Text>
          {!!session.requestedAmountUsd && (
            <Text style={{ marginTop: 2, color: '#444' }}>Amount: {usd(session.requestedAmountUsd)}</Text>
          )}
          {!!session.lastUpdatedIso && (
            <Text style={{ marginTop: 2, color: '#888', fontSize: 12 }}>
              Updated: {safeFormatDateTime(session.lastUpdatedIso)}
            </Text>
          )}
          {!!session.message && (
            <Text style={{ marginTop: 8, color: '#666' }}>{session.message}</Text>
          )}

          {!!cta && (
            <TouchableOpacity
              onPress={cta.action}
              style={{ marginTop: 12, backgroundColor: '#111', padding: 12, borderRadius: 8 }}
            >
              <Text style={{ color: '#fff', textAlign: 'center', fontWeight: '600' }}>{cta.label}</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        <Text style={{ color: '#666', marginTop: 10 }}>No session found.</Text>
      )}

      <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginTop: 16 }}>
        <Text style={{ color: '#111', textAlign: 'center' }}>Back</Text>
      </TouchableOpacity>
    </View>
  );
}

/**
 * WalletConnect v2 Sign Client integration with session persistence.
 * Sessions are saved to AsyncStorage and restored on app relaunch.
 */
import SignClient from '@walletconnect/sign-client';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'wc_session_v2';
let client: SignClient | null = null;

export async function initWC() {
  if (client) return client;
  client = await SignClient.init({
    projectId: '42421cf8-2df7-45c6-9475-df4f4b115ffc',
    relayUrl: 'wss://relay.walletconnect.com',
    metadata: {
      name: 'RichesReach',
      description: 'AI-powered investing',
      url: 'https://richesreach.ai',
      icons: ['https://yourcdn/logo.png'],
    },
  });
  return client;
}

export type WcSession = Awaited<ReturnType<typeof connectWallet>>['session'];

/**
 * Connect to a wallet via WalletConnect.
 * Saves the session to AsyncStorage for persistence.
 */
export async function connectWallet(chainIdWC: string) {
  const c = await initWC();
  const { uri, approval } = await c.connect({
    requiredNamespaces: {
      eip155: {
        methods: ['eth_sendTransaction', 'eth_signTypedData', 'personal_sign'],
        chains: [chainIdWC],
        events: ['accountsChanged', 'chainChanged'],
      },
    },
  });

  // Present QR / deep-link mobile wallet with `uri` in your UI
  const session = await approval();
  const account = session.namespaces.eip155.accounts[0]; // eip155:137:0xabc...
  const address = account.split(':')[2];

  // Persist session for app relaunch
  await saveSession(session);

  return { client: c, session, address };
}

/**
 * Restore a previously saved WalletConnect session.
 * Returns null if no session exists or it has expired.
 */
export async function restoreSession(): Promise<{
  client: SignClient;
  session: WcSession;
  address: string;
} | null> {
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    if (!stored) return null;

    const { topic } = JSON.parse(stored);
    if (!topic) return null;

    const c = await initWC();

    // Check if the session still exists in the client
    const activeSessions = c.session.getAll();
    const session = activeSessions.find((s: any) => s.topic === topic);

    if (!session) {
      // Session expired or was killed from the wallet side
      await clearSession();
      return null;
    }

    // Check if session has expired
    if (session.expiry && session.expiry * 1000 < Date.now()) {
      await clearSession();
      return null;
    }

    const account = session.namespaces?.eip155?.accounts?.[0];
    if (!account) {
      await clearSession();
      return null;
    }

    const address = account.split(':')[2];
    return { client: c, session, address };
  } catch (error) {
    // If anything goes wrong, clear stale data
    await clearSession();
    return null;
  }
}

/**
 * Disconnect wallet and clear persisted session.
 */
export async function disconnectWallet() {
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    if (stored) {
      const { topic } = JSON.parse(stored);
      if (topic && client) {
        try {
          await client.disconnect({
            topic,
            reason: { code: 6000, message: 'User disconnected' },
          });
        } catch (e) {
          // Session may already be dead on the relay
        }
      }
    }
  } catch (e) {
    // Best effort
  }
  await clearSession();
}

/**
 * Send a transaction via WalletConnect.
 */
export async function sendTx(params: {
  client: SignClient;
  session: WcSession;
  chainIdWC: string;
  tx: { from: string; to: string; data: string; value?: string };
}) {
  const { client: c, session, chainIdWC, tx } = params;
  const hash = (await c.request({
    topic: session.topic,
    chainId: chainIdWC,
    request: { method: 'eth_sendTransaction', params: [tx] },
  })) as string;
  return hash;
}

// ---- Internal helpers ----

async function saveSession(session: WcSession) {
  try {
    await AsyncStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        topic: session.topic,
        expiry: session.expiry,
        savedAt: Date.now(),
      })
    );
  } catch (e) {
    // Non-critical — wallet will work but won't persist
  }
}

async function clearSession() {
  try {
    await AsyncStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    // Best effort
  }
}

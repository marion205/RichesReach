import SignClient from '@walletconnect/sign-client';

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
      icons: ['https://yourcdn/logo.png']
    }
  });
  return client;
}

export type WcSession = Awaited<ReturnType<typeof connectWallet>>['session'];

export async function connectWallet(chainIdWC: string) {
  const c = await initWC();
  const { uri, approval } = await c.connect({
    requiredNamespaces: {
      eip155: {
        methods: ['eth_sendTransaction','eth_signTypedData','personal_sign'],
        chains: [chainIdWC],
        events: ['accountsChanged','chainChanged'],
      }
    }
  });

  // Present QR / deep-link mobile wallet with `uri` in your UI
  const session = await approval();
  const account = session.namespaces.eip155.accounts[0]; // eip155:137:0xabc...
  const address = account.split(':')[2];
  return { client: c, session, address };
}

export async function sendTx(params: {
  client: SignClient,
  session: WcSession,
  chainIdWC: string,
  tx: { from: string; to: string; data: string; value?: string }
}) {
  const { client, session, chainIdWC, tx } = params;
  const hash = await client.request({
    topic: session.topic,
    chainId: chainIdWC,
    request: { method: 'eth_sendTransaction', params: [tx] }
  }) as string;
  return hash;
}

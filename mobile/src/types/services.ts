/**
 * Shared types for service-related functionality
 */

import type { ApolloClient } from '@apollo/client';

export interface WebSocketMessage {
  ev?: string;
  status?: string;
  sym?: string;
  p?: number;
  t?: number;
  bp?: number;
  ap?: number;
  data?: string;
  [key: string]: unknown;
}

export interface PolygonWebSocket extends WebSocket {
  send(data: string | ArrayBuffer): void;
  onopen: ((event: Event) => void) | null;
  onmessage: ((event: MessageEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onclose: ((event: CloseEvent) => void) | null;
  readyState: number;
}

export type ApolloClientType = ApolloClient<unknown>;

export interface NewsArticle {
  id: string;
  title: string;
  description: string;
  url: string;
  publishedAt: string;
  source: string;
  imageUrl?: string;
  category?: string;
}

export interface GraphQLError {
  message: string;
  extensions?: Record<string, unknown>;
  [key: string]: unknown;
}

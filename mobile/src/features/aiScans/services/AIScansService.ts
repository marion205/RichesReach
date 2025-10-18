/**
 * AIScansService - Hedge-Fund Edition
 * Advanced, production-grade AI market scanning client
 */

import { httpFetch, TokenProvider } from './http';
import type {
  AIScan, ScanResult, Playbook, CreateScanRequest, RunScanRequest, ClonePlaybookRequest, AIScanFilters
} from '../types/AIScansTypes';

class AIScansService {
  private baseUrl: string;
  private tokenProvider: TokenProvider;

  constructor(tokenProvider?: TokenProvider) {
    this.baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    this.tokenProvider = tokenProvider ?? (async () => 'your-auth-token');
  }

  private async authHeaders(extra?: Record<string, string>) {
    const tok = await this.tokenProvider();
    return {
      'Content-Type': 'application/json',
      ...(tok ? { 'Authorization': `Bearer ${tok}` } : {}),
      ...extra,
    };
  }

  async getScans(filters?: AIScanFilters): Promise<AIScan[]> {
    const qs = new URLSearchParams();
    if (filters?.category) qs.append('category', filters.category);
    if (filters?.riskLevel) qs.append('riskLevel', filters.riskLevel);
    if (filters?.timeHorizon) qs.append('timeHorizon', filters.timeHorizon);
    if (filters?.isActive !== undefined) qs.append('isActive', String(filters.isActive));
    if (filters?.tags?.length) qs.append('tags', filters.tags.join(','));

    const res = await httpFetch(`${this.baseUrl}/api/ai-scans?${qs.toString()}`, {
      method: 'GET',
      headers: await this.authHeaders(),
      timeoutMs: 8000,
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to fetch scans');
    return res.json();
  }

  async getScan(scanId: string): Promise<AIScan> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/${scanId}`, {
      method: 'GET',
      headers: await this.authHeaders(),
      timeoutMs: 8000,
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to fetch scan');
    return res.json();
  }

  async runScan(request: RunScanRequest): Promise<ScanResult[]> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/${request.scanId}/run`, {
      method: 'POST',
      headers: await this.authHeaders({ 'X-Client-Feature': 'ai-scans.run' }),
      timeoutMs: 20_000,
      idempotencyKey: `scan-run-${request.scanId}-${Date.now()}`,
      body: JSON.stringify(request),
    }, 1);
    if (!res.ok) throw await this.toApiError(res, 'Failed to run scan');
    return res.json();
  }

  async createScan(request: CreateScanRequest): Promise<AIScan> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans`, {
      method: 'POST',
      headers: await this.authHeaders(),
      timeoutMs: 10_000,
      idempotencyKey: `scan-create-${Date.now()}`,
      body: JSON.stringify(request),
    }, 1);
    if (!res.ok) throw await this.toApiError(res, 'Failed to create scan');
    return res.json();
  }

  async getPlaybooks(): Promise<Playbook[]> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/playbooks`, {
      method: 'GET',
      headers: await this.authHeaders(),
      timeoutMs: 8000,
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to fetch playbooks');
    return res.json();
  }

  async clonePlaybook(request: ClonePlaybookRequest): Promise<AIScan> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/playbooks/${request.playbookId}/clone`, {
      method: 'POST',
      headers: await this.authHeaders(),
      timeoutMs: 12_000,
      idempotencyKey: `playbook-clone-${request.playbookId}-${Date.now()}`,
      body: JSON.stringify(request),
    }, 1);
    if (!res.ok) throw await this.toApiError(res, 'Failed to clone playbook');
    return res.json();
  }

  async getScanHistory(scanId: string, limit = 10): Promise<ScanResult[][]> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/${scanId}/history?limit=${limit}`, {
      method: 'GET',
      headers: await this.authHeaders(),
      timeoutMs: 8000,
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to fetch scan history');
    return res.json();
  }

  async updateScan(scanId: string, updates: Partial<AIScan>): Promise<AIScan> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/${scanId}`, {
      method: 'PUT',
      headers: await this.authHeaders(),
      timeoutMs: 10_000,
      idempotencyKey: `scan-update-${scanId}-${Date.now()}`,
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to update scan');
    return res.json();
  }

  async deleteScan(scanId: string): Promise<void> {
    const res = await httpFetch(`${this.baseUrl}/api/ai-scans/${scanId}`, {
      method: 'DELETE',
      headers: await this.authHeaders(),
      timeoutMs: 10_000,
      idempotencyKey: `scan-delete-${scanId}-${Date.now()}`,
    });
    if (!res.ok) throw await this.toApiError(res, 'Failed to delete scan');
  }

  private async toApiError(res: Response, message: string) {
    const detail = await safeJson(res);
    const err = new Error(`${message} (${res.status})`);
    (err as any).status = res.status;
    (err as any).detail = detail;
    return err;
  }
}

async function safeJson(res: Response) {
  try { return await res.json(); } catch { return undefined; }
}

export default new AIScansService();
import { raiseForStatus } from "./exceptions";
import type {
  AnnotateResponse,
  AuditRecord,
  Entity,
  HealthResponse,
  IngestResponse,
  ReportExportResponse,
  TransactionListResponse,
  TravelRuleCheckResponse,
  TravelRuleTransmitResponse,
  WalletVerifyResponse,
} from "./models";
import { VERSION } from "./version";

const DEFAULT_BASE_URL = "https://api.getradius.com";

/** Options for creating a RadiusClient. */
export interface RadiusClientOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

// ── Resource classes ─────────────────────────────────────────────────────

class Transactions {
  constructor(private client: RadiusClient) {}

  /** Ingest a transaction for compliance checking. */
  async ingest(params: {
    direction: "outbound" | "inbound";
    from_entity: Entity;
    to_entity: Entity;
    amount: string;
    asset: string;
    chain: string;
    business_id?: string;
    external_id?: string;
    purpose?: string;
    metadata?: Record<string, unknown>;
  }): Promise<IngestResponse> {
    return this.client._request<IngestResponse>("POST", "/v1/transactions/ingest", {
      body: {
        direction: params.direction,
        from_entity: params.from_entity,
        to_entity: params.to_entity,
        amount: params.amount,
        asset: params.asset,
        chain: params.chain,
        business_id: params.business_id ?? "",
        ...(params.external_id !== undefined && { external_id: params.external_id }),
        ...(params.purpose !== undefined && { purpose: params.purpose }),
        ...(params.metadata !== undefined && { metadata: params.metadata }),
      },
    });
  }

  /** List transactions with optional filtering. */
  async list(params?: {
    status?: string;
    risk_level?: string;
    limit?: number;
    offset?: number;
  }): Promise<TransactionListResponse> {
    const query: Record<string, string> = {};
    if (params?.status) query.status = params.status;
    if (params?.risk_level) query.risk_level = params.risk_level;
    query.limit = String(params?.limit ?? 50);
    query.offset = String(params?.offset ?? 0);

    return this.client._request<TransactionListResponse>("GET", "/v1/transactions", { query });
  }

  /** Get the audit record for a specific transaction. */
  async getAudit(transactionId: string): Promise<AuditRecord> {
    return this.client._request<AuditRecord>("GET", `/v1/transactions/${transactionId}/audit`);
  }
}

class Payments {
  constructor(private client: RadiusClient) {}

  /** Annotate a transaction with on-chain execution data. */
  async annotate(params: {
    transaction_id: string;
    tx_hash: string;
    executed_at: string;
    provider_refs?: Record<string, string>;
  }): Promise<AnnotateResponse> {
    return this.client._request<AnnotateResponse>("POST", "/v1/payments/annotate", {
      body: {
        transaction_id: params.transaction_id,
        tx_hash: params.tx_hash,
        executed_at: params.executed_at,
        ...(params.provider_refs !== undefined && { provider_refs: params.provider_refs }),
      },
    });
  }
}

class Wallets {
  constructor(private client: RadiusClient) {}

  /** Verify wallet ownership via signed message. */
  async verify(params: {
    wallet: string;
    entity_type: "user" | "business";
    entity_id: string;
    proof_message: string;
    proof_signature: string;
  }): Promise<WalletVerifyResponse> {
    return this.client._request<WalletVerifyResponse>("POST", "/v1/wallets/verify", {
      body: {
        wallet: params.wallet,
        entity_type: params.entity_type,
        entity_id: params.entity_id,
        proof: {
          type: "signed_message",
          message: params.proof_message,
          signature: params.proof_signature,
        },
      },
    });
  }
}

class TravelRule {
  constructor(private client: RadiusClient) {}

  /** Pre-flight check of Travel Rule requirements. */
  async check(params: {
    amount: string;
    originator_jurisdiction?: string;
    beneficiary_jurisdiction?: string;
    originator_entity_type?: string;
    beneficiary_entity_type?: string;
    involves_self_hosted?: boolean;
  }): Promise<TravelRuleCheckResponse> {
    const query: Record<string, string> = { amount: params.amount };
    if (params.originator_jurisdiction) query.originator_jurisdiction = params.originator_jurisdiction;
    if (params.beneficiary_jurisdiction) query.beneficiary_jurisdiction = params.beneficiary_jurisdiction;
    query.originator_entity_type = params.originator_entity_type ?? "user";
    query.beneficiary_entity_type = params.beneficiary_entity_type ?? "user";
    if (params.involves_self_hosted) query.involves_self_hosted = "true";

    return this.client._request<TravelRuleCheckResponse>("GET", "/v1/travel-rule/check", { query });
  }

  /** Transmit Travel Rule data to counterparty VASP. */
  async transmit(params: {
    transaction_id: string;
    originator: Record<string, unknown>;
    beneficiary: Record<string, unknown>;
    beneficiary_vasp: Record<string, unknown>;
  }): Promise<TravelRuleTransmitResponse> {
    return this.client._request<TravelRuleTransmitResponse>("POST", "/v1/travel-rule/transmit", {
      body: params,
    });
  }

  /** List all supported jurisdictions with their Travel Rule requirements. */
  async jurisdictions(): Promise<Record<string, unknown>> {
    return this.client._request<Record<string, unknown>>("GET", "/v1/travel-rule/jurisdictions");
  }
}

class Reports {
  constructor(private client: RadiusClient) {}

  /** Export audit records as typed JSON. */
  async exportJson(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<ReportExportResponse> {
    const query: Record<string, string> = { format: "json" };
    if (params?.from_date) query.from_date = params.from_date;
    if (params?.to_date) query.to_date = params.to_date;

    return this.client._request<ReportExportResponse>("GET", "/v1/reports/export", { query });
  }

  /** Export audit records as raw CSV. */
  async exportCsv(params?: {
    from_date?: string;
    to_date?: string;
  }): Promise<ArrayBuffer> {
    const query: Record<string, string> = { format: "csv" };
    if (params?.from_date) query.from_date = params.from_date;
    if (params?.to_date) query.to_date = params.to_date;

    const response = await this.client._rawRequest("GET", "/v1/reports/export", { query });
    await raiseForStatus(response);
    return response.arrayBuffer();
  }
}

// ── Client ───────────────────────────────────────────────────────────────

export class RadiusClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  readonly transactions: Transactions;
  readonly payments: Payments;
  readonly wallets: Wallets;
  readonly travelRule: TravelRule;
  readonly reports: Reports;

  constructor(options: RadiusClientOptions) {
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeout = options.timeout ?? 30_000;

    this.transactions = new Transactions(this);
    this.payments = new Payments(this);
    this.wallets = new Wallets(this);
    this.travelRule = new TravelRule(this);
    this.reports = new Reports(this);
  }

  /** Check API health status (no auth required). */
  async health(): Promise<HealthResponse> {
    return this._request<HealthResponse>("GET", "/v1/health");
  }

  /** @internal Send a request and return the raw Response. */
  async _rawRequest(
    method: string,
    path: string,
    options?: { query?: Record<string, string>; body?: unknown },
  ): Promise<Response> {
    let url = `${this.baseUrl}${path}`;

    if (options?.query) {
      const qs = new URLSearchParams(options.query).toString();
      if (qs) url += `?${qs}`;
    }

    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      "User-Agent": `getradius-ts/${VERSION}`,
      Accept: "application/json",
    };

    const init: RequestInit = { method, headers };

    if (options?.body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(options.body);
    }

    if (typeof AbortSignal.timeout === "function") {
      init.signal = AbortSignal.timeout(this.timeout);
    }

    return fetch(url, init);
  }

  /** @internal Send a request, raise on error, return parsed JSON. */
  async _request<T>(
    method: string,
    path: string,
    options?: { query?: Record<string, string>; body?: unknown },
  ): Promise<T> {
    const response = await this._rawRequest(method, path, options);
    await raiseForStatus(response);
    return (await response.json()) as T;
  }
}

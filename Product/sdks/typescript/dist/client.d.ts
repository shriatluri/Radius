import type { AnnotateResponse, AuditRecord, Entity, HealthResponse, IngestResponse, ReportExportResponse, TransactionListResponse, TravelRuleCheckResponse, TravelRuleTransmitResponse, WalletVerifyResponse } from "./models";
/** Options for creating a RadiusClient. */
export interface RadiusClientOptions {
    apiKey: string;
    baseUrl?: string;
    timeout?: number;
}
declare class Transactions {
    private client;
    constructor(client: RadiusClient);
    /** Ingest a transaction for compliance checking. */
    ingest(params: {
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
    }): Promise<IngestResponse>;
    /** List transactions with optional filtering. */
    list(params?: {
        status?: string;
        risk_level?: string;
        limit?: number;
        offset?: number;
    }): Promise<TransactionListResponse>;
    /** Get the audit record for a specific transaction. */
    getAudit(transactionId: string): Promise<AuditRecord>;
}
declare class Payments {
    private client;
    constructor(client: RadiusClient);
    /** Annotate a transaction with on-chain execution data. */
    annotate(params: {
        transaction_id: string;
        tx_hash: string;
        executed_at: string;
        provider_refs?: Record<string, string>;
    }): Promise<AnnotateResponse>;
}
declare class Wallets {
    private client;
    constructor(client: RadiusClient);
    /** Verify wallet ownership via signed message. */
    verify(params: {
        wallet: string;
        entity_type: "user" | "business";
        entity_id: string;
        proof_message: string;
        proof_signature: string;
    }): Promise<WalletVerifyResponse>;
}
declare class TravelRule {
    private client;
    constructor(client: RadiusClient);
    /** Pre-flight check of Travel Rule requirements. */
    check(params: {
        amount: string;
        originator_jurisdiction?: string;
        beneficiary_jurisdiction?: string;
        originator_entity_type?: string;
        beneficiary_entity_type?: string;
        involves_self_hosted?: boolean;
    }): Promise<TravelRuleCheckResponse>;
    /** Transmit Travel Rule data to counterparty VASP. */
    transmit(params: {
        transaction_id: string;
        originator: Record<string, unknown>;
        beneficiary: Record<string, unknown>;
        beneficiary_vasp: Record<string, unknown>;
    }): Promise<TravelRuleTransmitResponse>;
    /** List all supported jurisdictions with their Travel Rule requirements. */
    jurisdictions(): Promise<Record<string, unknown>>;
}
declare class Reports {
    private client;
    constructor(client: RadiusClient);
    /** Export audit records as typed JSON. */
    exportJson(params?: {
        from_date?: string;
        to_date?: string;
    }): Promise<ReportExportResponse>;
    /** Export audit records as raw CSV. */
    exportCsv(params?: {
        from_date?: string;
        to_date?: string;
    }): Promise<ArrayBuffer>;
}
export declare class RadiusClient {
    private baseUrl;
    private apiKey;
    private timeout;
    readonly transactions: Transactions;
    readonly payments: Payments;
    readonly wallets: Wallets;
    readonly travelRule: TravelRule;
    readonly reports: Reports;
    constructor(options: RadiusClientOptions);
    /** Check API health status (no auth required). */
    health(): Promise<HealthResponse>;
    /** @internal Send a request and return the raw Response. */
    _rawRequest(method: string, path: string, options?: {
        query?: Record<string, string>;
        body?: unknown;
    }): Promise<Response>;
    /** @internal Send a request, raise on error, return parsed JSON. */
    _request<T>(method: string, path: string, options?: {
        query?: Record<string, string>;
        body?: unknown;
    }): Promise<T>;
}
export {};
//# sourceMappingURL=client.d.ts.map
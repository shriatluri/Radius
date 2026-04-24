/** An entity involved in a transaction (sender or receiver). */
export interface Entity {
    type: "business" | "user" | "vasp" | "unknown";
    entity_id: string;
    wallet?: string;
    jurisdiction?: string;
}
/** Travel Rule compliance information. */
export interface TravelRuleInfo {
    status: string;
    threshold_exceeded: boolean;
    applicable_threshold: string;
    threshold_currency: string;
    jurisdiction: string;
    self_hosted_verification_needed: boolean;
    notes?: string | null;
}
/** Response from transaction ingestion. */
export interface IngestResponse {
    transaction_id: string;
    status: string;
    risk_score: number;
    risk_level: string;
    sanctions_result: string;
    travel_rule: TravelRuleInfo;
    required_actions: string[];
    audit_record_id: string;
}
/** Response from payment annotation. */
export interface AnnotateResponse {
    transaction_id: string;
    status: string;
    audit_record_id: string;
}
/** An approval decision in an audit record. */
export interface AuditApproval {
    type: string;
    result: string;
    rule_id: string;
}
/** Full audit record for compliance reporting. */
export interface AuditRecord {
    transaction_id: string;
    business_id: string;
    from_entity: string;
    to_entity: string;
    wallets: Record<string, string | null>;
    amount: string;
    asset: string;
    purpose?: string | null;
    risk_score: number;
    risk_level: string;
    sanctions_result: string;
    travel_rule_status: string;
    tx_hash?: string | null;
    timestamp: string;
    approvals: AuditApproval[];
    reconciliation_status: string;
}
/** Summary of a transaction for list views. */
export interface TransactionSummary {
    transaction_id: string;
    external_id?: string | null;
    status: string;
    business_id: string;
    amount: string;
    asset: string;
    chain: string;
    risk_level: string;
    created_at: string;
}
/** Paginated list of transactions. */
export interface TransactionListResponse {
    transactions: TransactionSummary[];
    total: number;
    limit: number;
    offset: number;
}
/** Response from wallet verification. */
export interface WalletVerifyResponse {
    wallet_id: string;
    verification_status: string;
    verified_at?: string | null;
    expires_at?: string | null;
    error?: string | null;
}
/** Response from Travel Rule pre-flight check. */
export interface TravelRuleCheckResponse {
    status: string;
    threshold_exceeded: boolean;
    applicable_threshold: string;
    threshold_currency: string;
    jurisdiction: string;
    required_actions: string[];
    self_hosted_verification_needed: boolean;
    notes?: string | null;
    required_data_fields?: string[] | null;
}
/** Response from Travel Rule transmission. */
export interface TravelRuleTransmitResponse {
    transaction_id: string;
    travel_rule_status: string;
    proof_id?: string | null;
}
/** Response from JSON report export. */
export interface ReportExportResponse {
    records: Record<string, unknown>[];
    count: number;
}
/** Response from health check endpoint. */
export interface HealthResponse {
    status: string;
    version: string;
    environment: string;
    db_connected: boolean;
    sanctions_screening: Record<string, unknown>;
}
//# sourceMappingURL=models.d.ts.map
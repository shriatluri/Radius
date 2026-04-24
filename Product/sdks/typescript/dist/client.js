import { raiseForStatus } from "./exceptions";
import { VERSION } from "./version";
const DEFAULT_BASE_URL = "https://api.getradius.com";
// ── Resource classes ─────────────────────────────────────────────────────
class Transactions {
    client;
    constructor(client) {
        this.client = client;
    }
    /** Ingest a transaction for compliance checking. */
    async ingest(params) {
        return this.client._request("POST", "/v1/transactions/ingest", {
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
    async list(params) {
        const query = {};
        if (params?.status)
            query.status = params.status;
        if (params?.risk_level)
            query.risk_level = params.risk_level;
        query.limit = String(params?.limit ?? 50);
        query.offset = String(params?.offset ?? 0);
        return this.client._request("GET", "/v1/transactions", { query });
    }
    /** Get the audit record for a specific transaction. */
    async getAudit(transactionId) {
        return this.client._request("GET", `/v1/transactions/${transactionId}/audit`);
    }
}
class Payments {
    client;
    constructor(client) {
        this.client = client;
    }
    /** Annotate a transaction with on-chain execution data. */
    async annotate(params) {
        return this.client._request("POST", "/v1/payments/annotate", {
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
    client;
    constructor(client) {
        this.client = client;
    }
    /** Verify wallet ownership via signed message. */
    async verify(params) {
        return this.client._request("POST", "/v1/wallets/verify", {
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
    client;
    constructor(client) {
        this.client = client;
    }
    /** Pre-flight check of Travel Rule requirements. */
    async check(params) {
        const query = { amount: params.amount };
        if (params.originator_jurisdiction)
            query.originator_jurisdiction = params.originator_jurisdiction;
        if (params.beneficiary_jurisdiction)
            query.beneficiary_jurisdiction = params.beneficiary_jurisdiction;
        query.originator_entity_type = params.originator_entity_type ?? "user";
        query.beneficiary_entity_type = params.beneficiary_entity_type ?? "user";
        if (params.involves_self_hosted)
            query.involves_self_hosted = "true";
        return this.client._request("GET", "/v1/travel-rule/check", { query });
    }
    /** Transmit Travel Rule data to counterparty VASP. */
    async transmit(params) {
        return this.client._request("POST", "/v1/travel-rule/transmit", {
            body: params,
        });
    }
    /** List all supported jurisdictions with their Travel Rule requirements. */
    async jurisdictions() {
        return this.client._request("GET", "/v1/travel-rule/jurisdictions");
    }
}
class Reports {
    client;
    constructor(client) {
        this.client = client;
    }
    /** Export audit records as typed JSON. */
    async exportJson(params) {
        const query = { format: "json" };
        if (params?.from_date)
            query.from_date = params.from_date;
        if (params?.to_date)
            query.to_date = params.to_date;
        return this.client._request("GET", "/v1/reports/export", { query });
    }
    /** Export audit records as raw CSV. */
    async exportCsv(params) {
        const query = { format: "csv" };
        if (params?.from_date)
            query.from_date = params.from_date;
        if (params?.to_date)
            query.to_date = params.to_date;
        const response = await this.client._rawRequest("GET", "/v1/reports/export", { query });
        await raiseForStatus(response);
        return response.arrayBuffer();
    }
}
// ── Client ───────────────────────────────────────────────────────────────
export class RadiusClient {
    baseUrl;
    apiKey;
    timeout;
    transactions;
    payments;
    wallets;
    travelRule;
    reports;
    constructor(options) {
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
    async health() {
        return this._request("GET", "/v1/health");
    }
    /** @internal Send a request and return the raw Response. */
    async _rawRequest(method, path, options) {
        let url = `${this.baseUrl}${path}`;
        if (options?.query) {
            const qs = new URLSearchParams(options.query).toString();
            if (qs)
                url += `?${qs}`;
        }
        const headers = {
            Authorization: `Bearer ${this.apiKey}`,
            "User-Agent": `getradius-ts/${VERSION}`,
            Accept: "application/json",
        };
        const init = { method, headers };
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
    async _request(method, path, options) {
        const response = await this._rawRequest(method, path, options);
        await raiseForStatus(response);
        return (await response.json());
    }
}
//# sourceMappingURL=client.js.map
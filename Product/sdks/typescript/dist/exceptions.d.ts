/** Structured error body returned by the Radius API. */
export interface RadiusErrorBody {
    error: {
        code: string;
        message: string;
    };
}
/** Base class for all Radius API errors. */
export declare class RadiusError extends Error {
    readonly code: string;
    readonly statusCode: number;
    readonly body?: RadiusErrorBody;
    constructor(code: string, message: string, statusCode: number, body?: RadiusErrorBody);
}
/** 400 — invalid request parameters. */
export declare class BadRequestError extends RadiusError {
    constructor(code: string, message: string, body?: RadiusErrorBody);
}
/** 401 — missing or invalid API key. */
export declare class AuthenticationError extends RadiusError {
    constructor(code: string, message: string, body?: RadiusErrorBody);
}
/** 403 — valid key but insufficient scopes. */
export declare class ForbiddenError extends RadiusError {
    constructor(code: string, message: string, body?: RadiusErrorBody);
}
/** 404 — resource does not exist. */
export declare class NotFoundError extends RadiusError {
    constructor(code: string, message: string, body?: RadiusErrorBody);
}
/** 429 — too many requests. */
export declare class RateLimitError extends RadiusError {
    readonly retryAfter?: string;
    constructor(code: string, message: string, body?: RadiusErrorBody, retryAfter?: string);
}
/** 5xx — something went wrong on the server. */
export declare class ServerError extends RadiusError {
    constructor(code: string, message: string, statusCode: number, body?: RadiusErrorBody);
}
/** Throw a typed RadiusError if the response is not 2xx. */
export declare function raiseForStatus(response: Response): Promise<void>;
//# sourceMappingURL=exceptions.d.ts.map
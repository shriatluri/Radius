/** Base class for all Radius API errors. */
export class RadiusError extends Error {
    code;
    statusCode;
    body;
    constructor(code, message, statusCode, body) {
        super(`[${statusCode}] ${code}: ${message}`);
        this.name = "RadiusError";
        this.code = code;
        this.statusCode = statusCode;
        this.body = body;
    }
}
/** 400 — invalid request parameters. */
export class BadRequestError extends RadiusError {
    constructor(code, message, body) {
        super(code, message, 400, body);
        this.name = "BadRequestError";
    }
}
/** 401 — missing or invalid API key. */
export class AuthenticationError extends RadiusError {
    constructor(code, message, body) {
        super(code, message, 401, body);
        this.name = "AuthenticationError";
    }
}
/** 403 — valid key but insufficient scopes. */
export class ForbiddenError extends RadiusError {
    constructor(code, message, body) {
        super(code, message, 403, body);
        this.name = "ForbiddenError";
    }
}
/** 404 — resource does not exist. */
export class NotFoundError extends RadiusError {
    constructor(code, message, body) {
        super(code, message, 404, body);
        this.name = "NotFoundError";
    }
}
/** 429 — too many requests. */
export class RateLimitError extends RadiusError {
    retryAfter;
    constructor(code, message, body, retryAfter) {
        super(code, message, 429, body);
        this.name = "RateLimitError";
        this.retryAfter = retryAfter;
    }
}
/** 5xx — something went wrong on the server. */
export class ServerError extends RadiusError {
    constructor(code, message, statusCode, body) {
        super(code, message, statusCode, body);
        this.name = "ServerError";
    }
}
const STATUS_MAP = {
    400: BadRequestError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
};
/** Throw a typed RadiusError if the response is not 2xx. */
export async function raiseForStatus(response) {
    if (response.ok)
        return;
    let code = "api_error";
    let message = response.statusText;
    let body;
    try {
        body = (await response.json());
        code = body.error?.code ?? code;
        message = body.error?.message ?? message;
    }
    catch {
        // Response wasn't JSON — keep defaults
    }
    const status = response.status;
    if (status === 429) {
        const retryAfter = response.headers.get("Retry-After") ?? undefined;
        throw new RateLimitError(code, message, body, retryAfter);
    }
    const ErrorCls = STATUS_MAP[status];
    if (ErrorCls) {
        throw new ErrorCls(code, message, body);
    }
    if (status >= 500) {
        throw new ServerError(code, message, status, body);
    }
    throw new RadiusError(code, message, status, body);
}
//# sourceMappingURL=exceptions.js.map
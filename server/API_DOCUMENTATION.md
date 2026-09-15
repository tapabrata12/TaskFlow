# TaskFlow API Reference

**Version:** `0.0.1`

**Service:** TaskFlow backend

**API format:** JSON over HTTPS (production)
**Interactive documentation:** `GET /docs` (Swagger UI) and `GET /redoc` when the FastAPI service is running.

## 1. Overview

This document describes the authentication API currently implemented by TaskFlow. The service uses stateless JSON Web Tokens (JWTs) for authentication and MongoDB for user storage and refresh-token revocation records.

All request and response bodies use `application/json`, unless stated otherwise. Dates and MongoDB internals are not exposed through the current public API.

### Base URL

Use the deployment-specific URL supplied by your environment:

```text
https://api.example.com
```

For local development, FastAPI commonly runs at:

```text
http://127.0.0.1:8000
```

Do not hard-code the example production domain in application code.

## 2. API conventions

### Headers

Protected endpoints require an access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

`Content-Type: application/json` is required whenever a JSON request body is sent.

### Authentication model

| Token | Lifetime | Purpose | Where to send it |
| --- | --- | --- | --- |
| Access token | 15 minutes | Authorizes protected API calls | `Authorization: Bearer …` |
| Refresh token | 7 days | Obtains a new access token; identifies a logout revocation record | JSON request body only |

JWTs contain a subject (`sub`, the user email) and a token type (`access` or `refresh`). Refresh JWTs also contain a unique identifier (`jti`). Token signing algorithm and signing secret are environment-configured and must never be returned by or embedded in clients.

### HTTP status codes

| Status | Meaning |
| --- | --- |
| `200 OK` | Request completed successfully. |
| `201 Created` | User account created successfully. |
| `400 Bad Request` | Request is valid JSON but violates a business rule, such as a duplicate email. |
| `401 Unauthorized` | Missing, expired, malformed, invalid, incorrectly typed, or unrecognized credential. |
| `422 Unprocessable Entity` | Request validation failed (missing field, malformed email, or length constraint). FastAPI returns its standard validation-error body. |
| `500 Internal Server Error` | An unexpected server-side failure occurred. Clients should not rely on its message. |

Business/authentication errors use this envelope:

```json
{
  "detail": "Human-readable error description"
}
```

## 3. Data contracts

### Signup request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `user_name` | string | Yes | 3–100 characters |
| `email` | string | Yes | Valid email format |
| `password` | string | Yes | 6–20 characters |

### Login request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `email` | string | Yes | Valid email format |
| `password` | string | Yes | 6–20 characters |

### Refresh request

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| `refresh_token` | string | Yes | At least 3 characters; must be a valid, unexpired refresh JWT |

### Token object

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer"
}
```

## 4. Endpoints

### `GET /`

Returns a basic service response. This endpoint is public.

**Success — `200 OK`**

```json
{
  "message": "Hello world"
}
```

---

### `POST /auth/signup`

Creates a user account, stores a password hash, and issues an access/refresh-token pair. Email comparison and persistence are normalized to lowercase.

**Authentication:** Not required

**Success:** `201 Created`

**Request**

```json
{
  "user_name": "Ada Lovelace",
  "email": "ada@example.com",
  "password": "strong-password"
}
```

**Success response**

```json
{
  "message": "User successfully signed up",
  "email": "ada@example.com",
  "token": {
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "token_type": "bearer"
  }
}
```

**Error responses**

| Status | `detail` | When |
| --- | --- | --- |
| `400` | `User already registered` | An account already exists for the normalized email address. |
| `422` | FastAPI validation details | A required field is missing or a field violates the documented constraints. |
| `500` | `Internal server error` | User creation, database, or token issuance failed unexpectedly. |

---

### `POST /auth/login`

Authenticates an existing user using their email and password, then issues a new access/refresh-token pair.

**Authentication:** Not required

**Success:** `200 OK`

**Request**

```json
{
  "email": "ada@example.com",
  "password": "strong-password"
}
```

**Success response**

```json
{
  "message": "User successfully Logged in",
  "email": "ada@example.com",
  "token": {
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "token_type": "bearer"
  }
}
```

**Error responses**

| Status | `detail` | When |
| --- | --- | --- |
| `401` | `Invalid email or password` | The account does not exist or the password does not match. |
| `422` | FastAPI validation details | Input does not conform to the login contract. |
| `500` | `Internal server error` | An unexpected server-side error occurred. |

---

### `GET /auth/profile`

Returns the authenticated user’s public profile.

**Authentication:** Required — access token only

**Success:** `200 OK`

**Example request**

```bash
curl --request GET "https://api.example.com/auth/profile" \
  --header "Authorization: Bearer <access_token>"
```

**Success response**

```json
{
  "user_name": "Ada Lovelace",
  "email": "ada@example.com"
}
```

**Error responses**

| Status | `detail` | When |
| --- | --- | --- |
| `401` | `Not authenticated` | The `Authorization` header is missing or not Bearer authentication. |
| `401` | `Invalid access token` | A refresh token is presented where an access token is required. |
| `401` | `Invalid token` | The JWT does not contain a subject claim. |
| `401` | `Token has expired` | The access JWT has expired. |
| `401` | `Invalid token` | The token signature or token format is invalid. |
| `401` | `User not found` | The JWT subject no longer has a corresponding user record. |

---

### `POST /auth/refresh`

Issues a new access token from a valid refresh token. The submitted refresh token is returned unchanged; this endpoint does not currently rotate refresh tokens.

**Authentication:** Refresh token in JSON body

**Success:** `200 OK`

**Request**

```json
{
  "refresh_token": "<refresh_jwt>"
}
```

**Success response**

```json
{
  "access_token": "<new_access_jwt>",
  "refresh_token": "<refresh_jwt>",
  "token_type": "bearer"
}
```

**Error responses**

| Status | `detail` | When |
| --- | --- | --- |
| `401` | `Invalid refresh token` | The JWT is not a refresh token, or has no `jti` when its subject is absent. |
| `401` | `Refresh token has expired` | The refresh JWT has expired. |
| `401` | `User not found` | The refresh-token subject is absent or no longer has a corresponding user record. |
| `422` | FastAPI validation details | `refresh_token` is missing or shorter than three characters. |
| `500` | `Internal server error` | An unexpected server-side error occurred. |

---

### `POST /auth/logout`

Records the supplied refresh token’s JWT ID (`jti`) in the `revoked_tokens` MongoDB collection. The record stores the token’s expiration as `expires_at`.

**Authentication:** Refresh token in JSON body

**Success:** `200 OK`

**Request**

```json
{
  "refresh_token": "<refresh_jwt>"
}
```

**Success response**

```json
{
  "message": "User successfully logged out"
}
```

**Error responses**

| Status | `detail` | When |
| --- | --- | --- |
| `401` | `Invalid refresh token` | The JWT is not a refresh token or does not contain a `jti`. |
| `401` | `Refresh token has expired` | The refresh JWT has expired. |
| `422` | FastAPI validation details | `refresh_token` is missing or shorter than three characters. |
| `500` | `Internal server error` | An unexpected server-side error occurred. |

## 5. Client integration flow

1. Call `POST /auth/signup` or `POST /auth/login` and retain the returned token pair.
2. Send the access token as a Bearer credential for `GET /auth/profile` and future protected endpoints.
3. When the access token expires, call `POST /auth/refresh` with the refresh token, then replace the access token with the returned value.
4. On sign-out, call `POST /auth/logout` with the refresh token and remove both tokens from client storage.

## 6. Security and production integration guidance

- Use TLS for every environment that handles real credentials or tokens. Never send JWTs over plaintext HTTP in production.
- Treat access and refresh tokens as secrets. Do not place them in URLs, logs, analytics events, crash reports, or error messages.
- Prefer an HttpOnly, Secure, SameSite cookie strategy for browser refresh tokens; if tokens are held by a non-browser client, use its platform-provided secure storage.
- Keep access tokens short-lived. The current implementation uses 15 minutes; refresh tokens expire after 7 days.
- Restrict CORS origins at deployment time and apply rate limiting/abuse controls to signup, login, refresh, and logout endpoints.
- Use a strong, rotated `JWT_SECRET_KEY` and a deliberately selected `ALGORITHM` in the runtime environment. Do not commit `.env` files or secrets.
- Configure a MongoDB TTL index on `revoked_tokens.expires_at` so expired revocation records are automatically removed. MongoDB TTL indexes require a BSON datetime value; confirm the stored `expires_at` type meets that requirement.
- Return generic authentication failures to clients as implemented, and retain detailed exceptions only in secure server logs.

## 7. Current implementation notes

These notes document the behavior of the current codebase so client teams can integrate safely:

- Refresh-token rotation is not implemented: `/auth/refresh` returns the same refresh JWT that was submitted.
- Logout stores refresh-token revocations, but the current `/auth/refresh` implementation checks the revocation collection only when the refresh token has no `sub` claim. Normal issued refresh tokens include `sub`, so a logged-out token may still be accepted by `/auth/refresh` until it expires. Clients should still clear tokens locally after logout; server-side enforcement needs a small implementation fix before it can be relied on as a revocation guarantee.
- Logout requires possession of a refresh token but does not require an access-token `Authorization` header.
- Access tokens are not individually revocable in the current implementation; they remain usable until expiry, unless the referenced user no longer exists.
- The root endpoint is a simple service response, not a readiness/liveness contract. Add dedicated health checks before relying on it for production orchestration.

## 8. Example error: validation failure

FastAPI validation failures return `422 Unprocessable Entity` with a `detail` array. The exact `msg` and `type` fields are framework-generated and may vary by FastAPI/Pydantic version.

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 6 characters",
      "input": "abc",
      "ctx": { "min_length": 6 }
    }
  ]
}
```

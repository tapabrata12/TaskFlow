# TaskFlow API Reference

**Version:** `0.0.1`

**Service:** TaskFlow backend

**API format:** JSON over HTTPS (production)
**Interactive documentation:** `GET /docs` (Swagger UI) and `GET /redoc` when the FastAPI service is running.

## 1. Overview

This document describes the API currently implemented by TaskFlow: authentication, projects, project memberships, and tasks. The service uses stateless JSON Web Tokens (JWTs) for authentication and MongoDB for persistence.

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

## 9. Projects

All endpoints in this section require an access token. Creating a project also creates an `owner` membership for the caller. Project and user IDs are MongoDB ObjectId strings (24 hexadecimal characters). Project timestamps are ISO 8601 strings.

### Project response

```json
{
  "id": "65f000000000000000000001",
  "name": "Website refresh",
  "description": "Q2 work",
  "created_by": "65f000000000000000000002",
  "created_at": "2026-09-17T10:00:00+00:00",
  "updated_at": "2026-09-17T10:00:00+00:00"
}
```

### `POST /projects`

Creates a project and returns `201 Created` with a project response.

```json
{ "name": "Website refresh", "description": "Q2 work" }
```

`name` is required (1-100 characters). `description` is optional, defaults to an empty string, and is limited to 500 characters. An unexpected persistence failure returns `500` / `Failed to create project`.

### `GET /projects`

Returns `200 OK` and an array of project responses for every project in which the caller has a membership. Returns an empty array when none exists.

### `GET /projects/{project_id}`

Returns the specified project to a project member. Invalid IDs return `400` / `Invalid project ID`; a non-member receives `403` / `You are not a member of this project`; absent projects return `404` / `Project not found`.

### `PATCH /projects/{project_id}`

Owner-only partial update. Both fields are optional and retain the create constraints.

```json
{ "name": "Website redesign", "description": "Updated scope" }
```

An empty body returns the existing project without changing it. A non-owner receives `403` / `Only the project owner can update the project`.

### `DELETE /projects/{project_id}`

Owner-only deletion. Returns `204 No Content`; removes the project and its memberships. It does **not** delete the project's tasks, so task records can remain after deletion. A non-owner receives `403` / `Only the project owner can delete the project`.

## 10. Project memberships

All membership endpoints require an access token. A membership response has this shape:

```json
{
  "user_id": "65f000000000000000000003",
  "user_name": "Grace Hopper",
  "email": "grace@example.com",
  "role": "member",
  "joined_at": "2026-09-17T10:00:00+00:00"
}
```

### `POST /projects/{project_id}/members`

Owner-only. Adds a registered user by email and returns `201 Created` with a membership response.

```json
{ "email": "grace@example.com" }
```

Returns `404` when the project is missing or the email is unregistered; returns `409` / `User is already a member of this project` for an existing membership. Non-owners receive `403` / `Only the project owner can perform this action`.

### `GET /projects/{project_id}/members`

Available to any project member. Returns `200 OK`:

```json
{ "members": [/* membership responses */] }
```

### `DELETE /projects/{project_id}/members/{user_id}`

Owner-only. Returns `204 No Content`. Invalid IDs return `400`; a missing membership returns `404` / `User is not a member of this project`. The owner cannot be removed (`400` / `Project owner cannot be removed`).

## 11. Tasks

All task endpoints require a project membership. Valid statuses are `to-do`, `progress`, and `done`; valid priorities are `low`, `medium`, and `high`. A supplied due date may not be in the past. If assigned, a user must exist and be a member of the same project.

### Task response

```json
{
  "id": "65f000000000000000000010",
  "project_id": "65f000000000000000000001",
  "title": "Design homepage",
  "description": "Prepare the first draft",
  "status": "to-do",
  "priority": "high",
  "due_date": "2026-10-01T09:00:00+00:00",
  "assignee_id": "65f000000000000000000003",
  "created_by": "65f000000000000000000002",
  "completed_at": null,
  "created_at": "2026-09-17T10:00:00+00:00",
  "updated_at": "2026-09-17T10:00:00+00:00"
}
```

### `GET /projects/{project_id}/tasks`

Returns the paginated task contract below. All query parameters are optional.

| Parameter | Default | Valid values / behavior |
| --- | --- | --- |
| `page` | `1` | Integer >= 1 |
| `limit` | `10` | Integer from 1 through 100 |
| `assignee_id` | none | A valid user ObjectId |
| `priority` | none | `low`, `medium`, or `high` |
| `search` | none | Case-insensitive regular-expression search of titles |
| `sort_by` | `created_at` | `created_at`, `due_date`, or `priority` |
| `sort_order` | `desc` | `asc` or `desc` |

```json
{
  "tasks": [/* task responses */],
  "page": 1,
  "limit": 10,
  "total": 1,
  "total_pages": 1
}
```

Invalid filtering/sorting values return `400` with `Invalid user ID`, `Invalid priority`, `Invalid sort field`, or `Invalid sort order`.

### `POST /projects/{project_id}/tasks`

Creates a task and returns `201 Created` with a task response.

```json
{
  "title": "Design homepage",
  "description": "Prepare the first draft",
  "status": "to-do",
  "priority": "high",
  "due_date": "2026-10-01T09:00:00Z",
  "assignee_id": "65f000000000000000000003"
}
```

`title` is required (1-200 characters). `description` defaults to `""` (maximum 2,000 characters); `status` defaults to `to-do`; `priority` defaults to `medium`; `due_date` and `assignee_id` are optional. Creating a task with status `done` sets `completed_at` to the creation timestamp.

### `PUT /projects/{project_id}/tasks/{task_id}`

Partially updates a task; every task input property is optional. Send `null` for `due_date` or `assignee_id` to clear it. A status change to `done` sets `completed_at`; changing a completed task to another status clears it. Even an empty body updates `updated_at`.

```json
{ "status": "done", "priority": "high" }
```

Whitespace-only titles return `400` / `Task title cannot be empty`. A missing task returns `404` / `Task not found`.

### `DELETE /projects/{project_id}/tasks/{task_id}`

Deletes a task and returns `200 OK`:

```json
{ "message": "Task deleted successfully" }
```

Invalid task IDs return `400` / `Invalid task ID`; tasks not in the project return `404` / `Task not found`.

## 12. Additional implementation notes

- All project members may create, update, and delete tasks; task creator/assignee ownership is not enforced.
- `src/routes/task.py` declares `GET /projects/{project_id}/tasks` twice. Runtime routing reaches the first declaration (the paginated response documented above); the duplicate should be removed to avoid ambiguity in generated OpenAPI documentation.
- As described in section 7, logout records a refresh-token revocation but normally issued refresh tokens contain `sub`, bypassing the current revocation check during refresh. Logout therefore does not yet guarantee server-side refresh-token invalidation.

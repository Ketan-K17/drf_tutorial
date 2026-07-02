# CORS & CSRF in Django: The Complete Guide

A deep, practical guide to two of the most important web-security concepts you'll deal with every day as a Django developer: **CORS** (Cross-Origin Resource Sharing) and **CSRF** (Cross-Site Request Forgery). This document covers what they are, why they exist, how attackers exploit their absence, and exactly how to configure them properly in a Django (and Django REST Framework) project.

---

## Table of Contents

1. [Foundations: The Same-Origin Policy](#1-foundations-the-same-origin-policy)
2. [CORS — Cross-Origin Resource Sharing](#2-cors--cross-origin-resource-sharing)
   - [2.1 What is CORS?](#21-what-is-cors)
   - [2.2 Why do we need CORS?](#22-why-do-we-need-cors)
   - [2.3 What problem does CORS solve?](#23-what-problem-does-cors-solve)
   - [2.4 How CORS works (the protocol)](#24-how-cors-works-the-protocol)
   - [2.5 CORS request types](#25-cors-request-types)
   - [2.6 The complete list of CORS headers](#26-the-complete-list-of-cors-headers)
   - [2.7 A worked example](#27-a-worked-example)
   - [2.8 Enforcing CORS in Django](#28-enforcing-cors-in-django)
   - [2.9 DRF + CORS: the JWT/token gotcha](#29-drf--cors-the-jwttoken-gotcha)
   - [2.10 CORS in production: do's and don'ts](#210-cors-in-production-dos-and-donts)
3. [CSRF — Cross-Site Request Forgery](#3-csrf--cross-site-request-forgery)
   - [3.1 What is CSRF?](#31-what-is-csrf)
   - [3.2 A real-world attack scenario](#32-a-real-world-attack-scenario)
   - [3.3 Why browsers can't stop this alone](#33-why-browsers-cant-stop-this-alone)
   - [3.4 The defense: synchronizer token pattern](#34-the-defense-synchronizer-token-pattern)
   - [3.5 How Django's CSRF protection works](#35-how-djangos-csrf-protection-works)
   - [3.6 Enforcing CSRF in Django](#36-enforcing-csrf-in-django)
   - [3.7 CSRF in templates (server-rendered)](#37-csrf-in-templates-server-rendered)
   - [3.8 CSRF with AJAX / fetch / Axios](#38-csrf-with-ajax--fetch--axios)
   - [3.9 CSRF with Django REST Framework](#39-csrf-with-django-rest-framework)
   - [3.10 Disabling CSRF (and when it's actually safe)](#310-disabling-csrf-and-when-its-actually-safe)
   - [3.11 Cookie configuration that affects CSRF](#311-cookie-configuration-that-affects-csrf)
4. [CORS vs CSRF: don't confuse them](#4-cors-vs-csrf-dont-confuse-them)
5. [A production-ready Django settings.py example](#5-a-production-ready-django-settingspy-example)
6. [Testing & debugging](#6-testing--debugging)
7. [Common mistakes checklist](#7-common-mistakes-checklist)
8. [Quick reference card](#8-quick-reference-card)

---

## 1. Foundations: The Same-Origin Policy

Before either CORS or CSRF makes sense, you have to understand the **Same-Origin Policy (SOP)**.

An **origin** is the triple `(scheme, host, port)`. For example:

| URL                              | Scheme | Host          | Port | Origin                  |
|----------------------------------|--------|---------------|------|-------------------------|
| `https://example.com/page1`      | https  | example.com   | 443  | `https://example.com`   |
| `https://example.com:8080/page1` | https  | example.com   | 8080 | `https://example.com:8080` |
| `http://example.com/page1`       | http   | example.com   | 80   | `http://example.com`    |
| `https://api.example.com/x`      | https  | api.example.com| 443  | `https://api.example.com` |

The Same-Origin Policy says: **a page loaded from one origin may not read responses from a different origin.** This is the cornerstone of browser security. It prevents `evil.com` from reading your `bank.com` data via JavaScript.

But SOP is also inconvenient. It is *too strict* in the modern world, where:

- Your React/Vue/Svelte frontend lives at `app.example.com`.
- Your API lives at `api.example.com`.
- These are *different origins* even though they're the same company.

That's where **CORS** comes in: it's an *opt-in relaxation* of the SOP that the server uses to tell the browser "yes, I trust this other origin."

And **CSRF** is the *complement*: even when CORS allows a cross-origin request, browsers will still automatically send cookies/credentials with it under certain conditions — which is exactly the hole CSRF attacks exploit.

---

## 2. CORS — Cross-Origin Resource Sharing

### 2.1 What is CORS?

**CORS (Cross-Origin Resource Sharing)** is a **browser-enforced mechanism** that lets a server declare *which* external origins are allowed to read its responses, and under what conditions.

Key facts:

- CORS is enforced by the **browser**, not by your server. The server simply *advertises* a policy; the browser *enforces* it.
- CORS only affects **browser-initiated** requests from JavaScript. `curl`, Postman, mobile apps, and server-to-server calls are not subject to CORS at all.
- CORS does **not** stop requests from being sent. It stops the browser from *exposing the response* to JavaScript.

### 2.2 Why do we need CORS?

Without CORS, a browser at `https://app.example.com` running JavaScript cannot fetch data from `https://api.example.com`. The browser blocks the response even though the request went out.

This is a problem because:

- **Modern SPAs** are typically split: a static frontend (often on a CDN) and a JSON API.
- **Microservices** live on different subdomains/ports.
- **Third-party integrations** need controlled cross-origin access.

CORS is the protocol by which the API says "browser, you can let `app.example.com` read my responses."

### 2.3 What problem does CORS solve?

It solves the *relaxation* problem of the Same-Origin Policy in a controlled way. Without CORS, you had two bad options:

1. **Disable SOP** (don't do this — opens up massive security holes).
2. **JSONP / proxies** (hacks that predate the modern web).

CORS gives a clean, header-driven way to say: "Origin X may call me with methods Y and headers Z."

### 2.4 How CORS works (the protocol)

Two flavors of requests:

#### Simple requests

If the request uses only "safe" methods (`GET`, `HEAD`, `POST`) and "safe" headers (`Accept`, `Content-Type` of `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain`), the browser just sends it with an `Origin` header. The server responds with `Access-Control-Allow-Origin` to opt-in.

```
GET /api/users/ HTTP/1.1
Origin: https://app.example.com
...
```

```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.example.com
Content-Type: application/json
...
```

#### Preflighted requests

Anything fancier — custom headers like `Authorization`, content types like `application/json`, methods like `PUT`/`DELETE`/`PATCH` — triggers a **preflight**: an `OPTIONS` request sent first to ask permission.

```
OPTIONS /api/users/ HTTP/1.1
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type, authorization
```

The server must respond to the preflight with what it allows:

```
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: content-type, authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 600
```

Only if the preflight succeeds does the browser send the real request.

### 2.5 CORS request types

- **Simple request** — `GET`/`HEAD`/`POST` with simple headers and content types. No preflight.
- **Preflighted request** — anything else. Browser sends `OPTIONS` first.
- **Credentialed request** — includes cookies / HTTP auth. Requires `Access-Control-Allow-Credentials: true` and the `Allow-Origin` header **cannot be `*`** (it must echo the specific origin).
- **Preflight cache** — `Access-Control-Max-Age` lets you cache the preflight result so the browser doesn't OPTIONS every single request.

### 2.6 The complete list of CORS headers

**Request headers (browser → server):**

| Header                          | Purpose                                                                  |
|---------------------------------|--------------------------------------------------------------------------|
| `Origin`                        | Where the request is coming from. Always sent on cross-origin requests. |
| `Access-Control-Request-Method` | In preflight: the HTTP method the real request will use.                |
| `Access-Control-Request-Headers`| In preflight: custom headers the real request will use.                 |

**Response headers (server → browser):**

| Header                              | Purpose                                                                              |
|-------------------------------------|--------------------------------------------------------------------------------------|
| `Access-Control-Allow-Origin`       | The allowed origin, or `*`. Cannot be `*` when credentials are used.                 |
| `Access-Control-Allow-Methods`      | Comma-separated methods allowed (in response to preflight).                          |
| `Access-Control-Allow-Headers`      | Comma-separated headers allowed (in response to preflight).                          |
| `Access-Control-Allow-Credentials`  | `true` to allow cookies/auth. Requires a specific origin.                            |
| `Access-Control-Expose-Headers`     | Which response headers JS is allowed to read (others are hidden).                   |
| `Access-Control-Max-Age`            | How long (seconds) the preflight result can be cached.                               |

### 2.7 A worked example

Imagine:

- Frontend SPA at `https://app.acme.com`
- API at `https://api.acme.com`
- SPA needs to call `POST https://api.acme.com/orders` with `Authorization: Bearer <jwt>` and `Content-Type: application/json`.

**Step 1** — Browser sees a cross-origin POST with a non-simple content type and a custom header. It triggers a **preflight**.

**Step 2** — Browser sends:

```
OPTIONS /orders HTTP/1.1
Host: api.acme.com
Origin: https://app.acme.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: authorization, content-type
```

**Step 3** — API responds:

```
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.acme.com
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Max-Age: 600
```

**Step 4** — Browser is satisfied. It sends the real request.

**Step 5** — API responds to the real request, also with CORS headers attached so the browser exposes the response body to JS.

If any header is missing or wrong, the browser blocks the response. From the JavaScript side, the request "fails" with a `TypeError: Failed to fetch` and a console message that often mentions CORS.

### 2.8 Enforcing CORS in Django

Django itself does **not** ship a CORS implementation. You must install `django-cors-headers`.

#### Installation

```bash
pip install django-cors-headers
```

Add to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "corsheaders",
    # ...
]
```

Add the middleware. **Order matters** — it must be as high as possible, especially before any middleware that can generate responses (e.g., `CommonMiddleware`, `WhiteNoiseMiddleware`):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # <-- here
    "django.middleware.common.CommonMiddleware",
    # ...
]
```

#### The key settings

```python
# settings.py

# Option A: allow specific origins (RECOMMENDED for production)
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]

# Option B: allow any origin via regex (looser, but useful in dev)
# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^https://\w+\.example\.com$",
# ]

# Option C: allow ALL origins (NEVER do this in production unless the API is fully public)
# CORS_ALLOW_ALL_ORIGINS = True   # django-cors-headers >= 3.0
```

**Common supporting settings:**

```python
# Allow cookies / Authorization headers cross-origin
CORS_ALLOW_CREDENTIALS = True

# Which HTTP methods the browser is allowed to use
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Which request headers the browser is allowed to send
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    # Add any custom headers your frontend uses, e.g.:
    # "x-tenant-id",
]

# Which response headers JS is allowed to read
CORS_EXPOSE_HEADERS = [
    "content-disposition",
    "x-request-id",
]

# How long to cache the preflight (seconds)
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# Apply CORS only to specific URL patterns (URL prefixes)
# CORS_URLS_REGEX = r"^/api/.*$"
```

**Important rule:** if you set `CORS_ALLOW_CREDENTIALS = True`, you **cannot** use `*` for `Access-Control-Allow-Origin`. The browser will reject it. `django-cors-headers` handles this for you automatically as long as you use `CORS_ALLOWED_ORIGINS` (a list) and don't set `CORS_ALLOW_ALL_ORIGINS = True`.

### 2.9 DRF + CORS: the JWT/token gotcha

This is the single most common Django CORS problem: **the browser silently drops the `Authorization` header** on cross-origin requests unless you whitelist it.

**Symptoms:**
- Local dev works (same origin).
- In production, frontend gets 401.
- `OPTIONS` preflight succeeds, but the real request never sends `Authorization`.
- Server logs show the request coming in with no auth header.

**Fix:** make sure `authorization` is in `CORS_ALLOW_HEADERS` (or use the default list, which includes it). Also, for JWTs in cookies, set `CORS_ALLOW_CREDENTIALS = True` and use `CORS_ALLOWED_ORIGINS` (not `*`).

For the classic session-cookie case with DRF, see the CSRF section below — you also need to handle CSRF tokens there.

### 2.10 CORS in production: do's and don'ts

**Do:**
- Use `CORS_ALLOWED_ORIGINS` with an explicit list of origins.
- Set `CORS_ALLOW_CREDENTIALS = True` *only if* you actually need cookies/auth cross-origin.
- Cache preflights with `CORS_PREFLIGHT_MAX_AGE` to reduce `OPTIONS` chatter.
- Use HTTPS everywhere in production. Mixed HTTP/HTTPS and CORS is a nightmare.
- Treat your CORS list like a firewall allow-list: review it.

**Don't:**
- Don't set `CORS_ALLOW_ALL_ORIGINS = True` in production unless the API is intentionally public and has no auth.
- Don't set `Access-Control-Allow-Origin: *` by hand — `django-cors-headers` does the right thing.
- Don't rely on CORS as your only security. CORS is *not* a replacement for authn/authz.

---

## 3. CSRF — Cross-Site Request Forgery

### 3.1 What is CSRF?

**CSRF (Cross-Site Request Forgery)** is an attack where a malicious site causes a victim's browser to make an unwanted request to a target site where the victim is authenticated.

The key insight: **browsers automatically attach cookies to requests that match a target domain, regardless of who initiated the request.** This means if you're logged into `bank.com` and you visit `evil.com`, JavaScript on `evil.com` can cause your browser to issue a `POST` to `bank.com/transfer` with your session cookie attached — and `bank.com` has no way to know the request didn't come from you.

### 3.2 A real-world attack scenario

Setup:

1. You log into `https://bank.com`. The bank sets a `sessionid` cookie.
2. You visit `https://evil.com` (in another tab).
3. `evil.com` serves this HTML:

```html
<form action="https://bank.com/transfer" method="POST" id="x">
  <input type="hidden" name="to" value="attacker">
  <input type="hidden" name="amount" value="10000">
</form>
<script>document.getElementById('x').submit();</script>
```

4. Your browser submits the form. Because the request goes to `bank.com`, your `sessionid` cookie is automatically attached.
5. `bank.com` sees a valid session and a valid request, and processes the transfer.

The attack works because:
- The browser **automatically** sends cookies for `bank.com` regardless of where the request originates.
- The server has no easy way to distinguish "request initiated by the user on `bank.com`" from "request initiated by JavaScript on `evil.com`."
- The Same-Origin Policy does **not** prevent `evil.com` from *sending* the request — it only prevents `evil.com` from *reading the response*. By the time SOP kicks in, the damage is done.

### 3.3 Why browsers can't stop this alone

The browser could in theory require an explicit "I want to send a cross-origin request" gesture, but:

- Legitimate cross-origin form submissions (e.g., a payment gateway redirecting back) are too common to block.
- Some HTTP methods (`GET`) are designed to be initiated by links/images/etc., not by forms alone.
- HTML forms and `<img>`/`<script>` tags are the historical foundation of the web.

So the burden falls on the server to add a defense that **a third-party site cannot forge**. That's where the **synchronizer token pattern** comes in.

### 3.4 The defense: synchronizer token pattern

The defense is conceptually simple:

1. When the server renders a page for a logged-in user, it includes a **secret, unpredictable token** in the page (e.g., a hidden form field or a meta tag).
2. The server also stores a copy of this token in the user's session (or signs it and stuffs it in a cookie).
3. Every state-changing request (POST, PUT, PATCH, DELETE) must include this token.
4. The server validates that the submitted token matches the one it stored.

A third-party site like `evil.com` cannot read the token (it would need to read the response from `bank.com`, which SOP blocks), so it can't include a valid token in its forged form. The attack fails.

Django uses exactly this pattern. By default it stores the token in the session and renders it into templates via `{% csrf_token %}`.

### 3.5 How Django's CSRF protection works

When `django.middleware.csrf.CsrfViewMiddleware` is active:

1. **On a `GET` request** for an authenticated user, Django sets a `csrftoken` cookie (if not already set). It also includes the token in the response context so `{% csrf_token %}` can render it.
2. **On a state-changing request** (`POST`, `PUT`, `PATCH`, `DELETE`), Django requires one of:
   - A form field named `csrfmiddlewaretoken` whose value matches the session's CSRF token.
   - A header named `X-CSRFToken` whose value matches.
   - A header named `X-CSRF-Token` (alias).
3. Django compares the submitted token against the one stored in the session.
4. If they don't match (or no token is present), Django returns **403 Forbidden**.
5. The `csrftoken` cookie is **not** the secret — the secret is in the session. The cookie is sent automatically by the browser (so JS on the same origin can read it via `document.cookie` and put it in a header), but a cross-origin site cannot read it because of SOP.

This works because:

- `evil.com` can't read the `csrftoken` cookie (different origin, SOP blocks `document.cookie` access).
- `evil.com` can't read the rendered `csrfmiddlewaretoken` hidden field (different origin, SOP blocks reading the response).
- So `evil.com` cannot include a valid token in its forged form.

### 3.6 Enforcing CSRF in Django

Django ships CSRF protection out of the box. You just need to:

#### 1. Make sure the middleware is in `MIDDLEWARE`

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.session.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # <-- usually already there
    # ...
]
```

The default `startproject` template includes this for you. If you use `django-admin startproject`, you should already have it.

#### 2. Understand the relevant settings

```python
# settings.py

# Use HTTPS-only CSRF cookie (recommended in production)
CSRF_COOKIE_SECURE = True

# JS-readable CSRF cookie (so frontend JS can read it to put in headers)
CSRF_COOKIE_HTTPONLY = False   # default; do not change this unless you know why

# Cookie name
CSRF_COOKIE_NAME = "csrftoken"   # default

# Path the cookie is valid for
CSRF_COOKIE_PATH = "/"           # default

# Cookie SameSite policy. The default in modern Django is "Lax", which is a good balance.
CSRF_COOKIE_SAMESITE = "Lax"     # "Strict" | "Lax" | "None"

# Seconds before the CSRF cookie expires. None = session cookie.
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7  # example: 1 week

# Trusted origins for CSRF (cross-site POSTs from these are allowed if they have a token)
# In Django 4.0+
CSRF_TRUSTED_ORIGINS = [
    "https://app.example.com",
]

# Whether to enforce CSRF on the logout view
CSRF_USE_SESSIONS = False  # default; if True, token is stored in session not cookie
```

The default settings are sensible. The most common production tweaks are:

- `CSRF_COOKIE_SECURE = True` (HTTPS only)
- `CSRF_COOKIE_SAMESITE = "Lax"` (already default in modern Django; this is a strong CSRF defense on its own for many cases)
- `CSRF_TRUSTED_ORIGINS` if your frontend and API are on different subdomains of the same eTLD+1

### 3.7 CSRF in templates (server-rendered)

In any form that uses `method="POST"`, include `{% csrf_token %}`:

```html
<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Save</button>
</form>
```

`{% csrf_token %}` renders as:

```html
<input type="hidden" name="csrfmiddlewaretoken" value="abc123randomtokenxyz">
```

If you forget this, Django will return 403 on POST. The error page will say "CSRF verification failed."

You can also use the `csrf_token` tag with the `{% csrf_token % as csrf_token %}` syntax if you need to render the token in a non-standard way.

### 3.8 CSRF with AJAX / fetch / Axios

For a JS frontend that POSTs to a same-origin Django backend, you need to read the CSRF cookie and put its value in an `X-CSRFToken` header.

**Plain fetch:**

```javascript
function getCookie(name) {
  const v = `; ${document.cookie}`;
  const parts = v.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

fetch("/api/orders/", {
  method: "POST",
  credentials: "same-origin",   // required to send cookies
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
  },
  body: JSON.stringify({ item: "book" }),
});
```

**Axios:** Axios is smart enough to do this automatically in many cases, but only if certain conditions are met.

By default, Axios reads `XSRF-TOKEN` (note the hyphen) from `document.cookie` and sends it back as `X-XSRF-TOKEN`. Django's cookie is named `csrftoken` (no hyphen), so you need to bridge:

```javascript
// In your JS entrypoint
import axios from "axios";

// Tell Axios which cookie holds the token
axios.defaults.xsrfCookieName = "csrftoken";

// Tell Axios which header to put it in
axios.defaults.xsrfHeaderName = "X-CSRFToken";

// Tell Axios to send cookies on cross-origin requests if you really need that
axios.defaults.withCredentials = true;
```

Or with `fetch` you can simply set `credentials: "include"` if the API is on a different origin and you need cookies to be sent.

### 3.9 CSRF with Django REST Framework

By default, DRF uses **session authentication** and **enforces CSRF** for any session-authenticated request. This is correct and safe.

If you use **token authentication** (`Authorization: Token ...`) or **JWT**, DRF's `SessionAuthentication` is *not* used for those credentials, and CSRF is bypassed for token-auth requests — which is fine, because:

- The attacker on `evil.com` cannot read your JWT from your `localStorage` or from a non-`HttpOnly` cookie on a different origin.
- The token isn't sent automatically by the browser; the frontend code must explicitly put it in the `Authorization` header.
- SOP already prevents `evil.com`'s JS from reading responses, so it can't extract the token.

**Practical DRF settings:**

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",   # uses CSRF
        "rest_framework.authentication.TokenAuthentication",     # skips CSRF
    ],
}

# Tell DRF where your frontend lives (for CSRF allowed origins)
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
]
CSRF_TRUSTED_ORIGINS = [
    "https://app.example.com",
]
```

**Per-view CSRF override:** if you want to disable CSRF on a specific view (e.g., a webhook receiver that authenticates by signature), use:

```python
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([])
@csrf_exempt
def my_webhook(request):
    # verify request signature, not session
    ...
```

Or in CBVs:

```python
from rest_framework.views import APIView

class MyWebhook(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = []
    @csrf_exempt
    def post(self, request):
        ...
```

Or, more idiomatically with DRF, subclass and override `get_authenticators` and set `csrf_exempt = True`:

```python
class WebhookView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = []
    csrf_exempt = True
```

### 3.10 Disabling CSRF (and when it's actually safe)

`@csrf_exempt` is a code smell until proven otherwise. There are a few legitimate use cases:

- **Webhooks** from third parties (Stripe, GitHub, etc.) that authenticate via HMAC signatures.
- **Stateless token-based APIs** where the client never uses session cookies.
- **Mobile clients** that don't use cookies.

**The rule of thumb:** if the client authenticates with something **not stored in a cookie** (e.g., `Authorization: Bearer ...` header), CSRF is not exploitable, and you can disable it. If the client authenticates with a cookie (session cookie), CSRF protection must stay on.

Don't globally set `CSRF_USE_SESSIONS = False` and call it a day — that's just turning off a defense.

### 3.11 Cookie configuration that affects CSRF

The **`SameSite`** cookie attribute is a powerful, modern CSRF defense:

- **`SameSite=Strict`** — the cookie is *never* sent on cross-origin requests. Maximum CSRF protection, but breaks links from external sites into your app.
- **`SameSite=Lax`** — the cookie is sent on top-level navigation `GET` requests but not on cross-origin POST or sub-requests. **This is the modern default and is sufficient to block most CSRF for state-changing endpoints.**
- **`SameSite=None`** — the cookie is always sent. Requires `Secure`. Don't use unless you have a real cross-site cookie need.

Modern Django sets the session cookie and CSRF cookie to `SameSite=Lax` by default. In a cross-site scenario (e.g., SPA at `app.example.com`, API at `api.example.com` with session cookies), you need to:

```python
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

And you **must** have HTTPS, because `SameSite=None` requires `Secure`.

Then in JS:

```javascript
fetch("https://api.example.com/...", {
  credentials: "include",
  headers: { "X-CSRFToken": getCookie("csrftoken") },
});
```

CORS settings must include `CORS_ALLOW_CREDENTIALS = True` and the `api.example.com` CORS list must include `https://app.example.com`.

---

## 4. CORS vs CSRF: don't confuse them

| Aspect                    | CORS                                                            | CSRF                                                              |
|---------------------------|-----------------------------------------------------------------|-------------------------------------------------------------------|
| **What it is**            | Server says "browser, let origin X read my responses."         | Server says "browser, prove this request really came from my UI." |
| **Defends against**       | Cross-origin data leakage via JS                               | Forged state-changing requests from malicious sites               |
| **Who enforces it**       | Browser                                                         | Server                                                            |
| **Stops requests?**       | No — stops browser from *exposing the response* to JS.          | Yes — server returns 403 if token is missing/wrong.               |
| **Default in Django?**    | No — need `django-cors-headers` package.                       | Yes — middleware enabled by default.                              |
| **Applies to**            | Any cross-origin request that JS would read.                    | Any state-changing request (POST, PUT, PATCH, DELETE).            |
| **Affects cookies?**      | Can allow/disallow them being read across origins.             | Verifies that the caller has access to a per-session secret.      |
| **Works without HTTPS?**  | Technically yes, but please don't.                             | Same.                                                             |

**Mnemonic:**
- **CORS = "Can I read this?"** The browser asks the server.
- **CSRF = "Did you really mean to send this?"** The server asks the browser/page.

---

## 5. A production-ready Django settings.py example

```python
# settings.py

# ----------------------------------------------------------------------
# Apps & middleware
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",

    # your apps
    "myapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # CORS first
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",      # CSRF
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ----------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization", "content-type",
    "dnt", "origin", "user-agent", "x-csrftoken", "x-requested-with",
]
CORS_EXPOSE_HEADERS = ["content-disposition", "x-request-id"]
CORS_PREFLIGHT_MAX_AGE = 86400

# ----------------------------------------------------------------------
# CSRF
# ----------------------------------------------------------------------
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False   # JS on the same origin must read it
CSRF_COOKIE_SAMESITE = "Lax"   # default in modern Django; explicit for clarity
CSRF_TRUSTED_ORIGINS = [
    "https://app.example.com",
]

# ----------------------------------------------------------------------
# Session cookies (if using session auth cross-origin)
# ----------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ----------------------------------------------------------------------
# Django REST Framework
# ----------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ----------------------------------------------------------------------
# Security (recommended)
# ----------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

---

## 6. Testing & debugging

### 6.1 Test CORS from the command line

A `curl` request with `Origin` will show you what the server returns:

```bash
curl -i -X OPTIONS https://api.example.com/orders/ \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type, authorization"
```

You should see `Access-Control-Allow-Origin: https://app.example.com` (or similar) in the response.

For a simple request:

```bash
curl -i https://api.example.com/orders/ -H "Origin: https://app.example.com"
```

### 6.2 Test CORS in the browser

Open DevTools → Network tab → look for the `OPTIONS` request (preflight). Check:

- Is it returning 2xx?
- Are the `Access-Control-*` headers present and correct?
- Is the JS request being made at all?

In the Console you'll see messages like:
> Access to XMLHttpRequest at '...' from origin '...' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

### 6.3 Test CSRF

- For server-rendered forms: just submit a form. If you forget `{% csrf_token %}`, you get 403 with a clear message.
- For AJAX: open DevTools, look at the request headers, confirm `X-CSRFToken` is present. Look at cookies, confirm `csrftoken` is set. If you POST without it, you get 403.
- Use the Django shell to inspect `request.session.get('_csrftoken')` to see what the server expects.

### 6.4 Common error messages

- `403 Forbidden — CSRF verification failed. Request aborted.` — missing/invalid CSRF token. Add `{% csrf_token %}` or send `X-CSRFToken` header.
- `Reason: CORS header 'Access-Control-Allow-Origin' does not match '...'` — your origin isn't whitelisted, or you mixed `*` with credentials.
- `Reason: Credential is not supported if the CORS header 'Access-Control-Allow-Origin' is '*'` — you set `CORS_ALLOW_ALL_ORIGINS = True` AND `CORS_ALLOW_CREDENTIALS = True`. The browser will reject this. Use `CORS_ALLOWED_ORIGINS` instead.

---

## 7. Common mistakes checklist

### CORS

- [ ] Forgot to add `corsheaders` to `INSTALLED_APPS`.
- [ ] Placed `CorsMiddleware` too low in `MIDDLEWARE` (after middleware that short-circuits).
- [ ] Set `CORS_ALLOW_ALL_ORIGINS = True` in production.
- [ ] Set `CORS_ALLOW_CREDENTIALS = True` but kept `Access-Control-Allow-Origin: *` (browser will reject).
- [ ] Frontend sends `Authorization` header but `authorization` isn't in `CORS_ALLOW_HEADERS`.
- [ ] Forgot to handle `OPTIONS` preflight; Django returns 405 because no view handles it. (The `CorsMiddleware` should handle this, but custom middleware can interfere.)
- [ ] Deployed with HTTP in production; `SameSite=None` cookies don't work without `Secure`.

### CSRF

- [ ] Used `{% csrf_form_input %}` (no such thing) instead of `{% csrf_token %}`.
- [ ] Form uses `method="post"` but doesn't include `{% csrf_token %}`.
- [ ] AJAX POST without `X-CSRFToken` header.
- [ ] Axios default config doesn't bridge Django's `csrftoken` cookie.
- [ ] Disabled CSRF globally with `csrf_exempt` on a session-authenticated view.
- [ ] Set `CSRF_COOKIE_HTTPONLY = True` (JS can no longer read the cookie, breaking AJAX).
- [ ] Frontend on `app.example.com`, API on `api.example.com`, but `CSRF_TRUSTED_ORIGINS` not set.
- [ ] Mobile/web app uses session cookies over HTTP, no `Secure` flag.

---

## 8. Quick reference card

### CORS — server says "I allow this origin"

```python
# settings.py
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]

CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["authorization", "content-type", "x-csrftoken", ...]
CORS_PREFLIGHT_MAX_AGE = 86400
```

### CSRF — client proves "I rendered the form"

```html
<!-- In every POST form -->
<form method="post">{% csrf_token %} ...</form>
```

```javascript
// For fetch / AJAX
fetch("/api/x/", {
  method: "POST",
  credentials: "same-origin",
  headers: { "X-CSRFToken": getCookie("csrftoken") },
  body: JSON.stringify(...),
});
```

```python
# settings.py — modern defaults
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = ["https://app.example.com"]  # if cross-site
```

### DRF cheat sheet

| Authentication                | CSRF needed? | Why                                                          |
|-------------------------------|--------------|--------------------------------------------------------------|
| `SessionAuthentication`       | **Yes**      | Browser auto-attaches the session cookie cross-origin.       |
| `TokenAuthentication`         | No           | Attacker can't read the token (it's not auto-sent).          |
| `JWTAuthentication`           | No           | Same as token — header is set explicitly by your JS.         |
| HMAC / signature (webhooks)   | No           | Authentication is by signature, not session.                 |

---

## Closing thoughts

- **CORS** is about *who is allowed to read responses*, decided by the *server*, enforced by the *browser*.
- **CSRF** is about *whether the request was actually initiated by the user*, decided by the *server*, using a *secret token*.
- They address different threats. A correct Django app needs **both** (or appropriate alternatives like token auth + CORS allow-list).
- When in doubt, prefer **explicit allow-lists**, **HTTPS**, **`SameSite=Lax` cookies**, and **token/JWT auth for cross-origin APIs**. Those four choices eliminate most of the common CORS/CSRF pitfalls.

Stay paranoid. Validate everything. Never trust the client.

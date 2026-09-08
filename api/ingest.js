// Public telemetry ingest for the 3-phone fleet (#61).
//
// Deployed at:
//   https://hop-ultrasonic-1digital-design.vercel.app/api/ingest
//
// Vercel Project env (names only; values in 1Password / Secret Manager — never commit):
//   IOT_ASP_GCS_BUCKET   — private fleet bucket name
//   GCP_SA_JSON          — service-account JSON with storage.objectUser on that bucket
//
// Invariants: no Vertex/Gemini keys; never log SA JSON, tokens, or raw PII payloads.
// CORS open for Safari sendBeacon from the static PWA (same-site preferred).

import { createSign, randomUUID } from 'node:crypto';

export const config = { runtime: 'nodejs', maxDuration: 15 };

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
  'Cache-Control': 'no-store',
};

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, 'content-type': 'application/json; charset=utf-8' },
  });
}

function b64url(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function loadSa() {
  const raw = process.env.GCP_SA_JSON;
  if (!raw || typeof raw !== 'string') return null;
  try {
    const sa = JSON.parse(raw);
    if (!sa.client_email || !sa.private_key) return null;
    return sa;
  } catch {
    return null;
  }
}

async function googleAccessToken(sa) {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = b64url(
    JSON.stringify({
      iss: sa.client_email,
      scope: 'https://www.googleapis.com/auth/devstorage.read_write',
      aud: 'https://oauth2.googleapis.com/token',
      iat: now,
      exp: now + 3600,
    }),
  );
  const unsigned = `${header}.${claim}`;
  const signer = createSign('RSA-SHA256');
  signer.update(unsigned);
  const sig = signer.sign(sa.private_key, 'base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = `${unsigned}.${sig}`;
  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }),
  });
  if (!res.ok) {
    return { ok: false, error: `token_http_${res.status}` };
  }
  const data = await res.json();
  if (!data.access_token) return { ok: false, error: 'token_missing' };
  return { ok: true, token: data.access_token };
}

function safeNode(tel) {
  const raw = String(tel.deviceId || tel.nodeId || 'node1');
  const cleaned = raw.replace(/[^A-Za-z0-9._-]/g, '').slice(0, 64);
  return cleaned || 'node1';
}

function safeTs(tel) {
  let ts = tel.ts || tel.t;
  if (typeof ts === 'number') {
    const ms = ts > 1e12 ? ts : ts * 1000;
    ts = new Date(ms).toISOString();
  }
  if (typeof ts !== 'string' || !ts) ts = new Date().toISOString();
  return ts.replace(/:/g, '-');
}

function scrub(tel) {
  // Drop obvious PII / oversized tails before GCS write (mirrors fleet_log intent).
  const out = { ...tel, schemaVersion: Number(tel.schemaVersion) || 1 };
  for (const k of ['userAgent', 'geolocation', 'address', 'email', 'name', 'phone']) {
    delete out[k];
  }
  if (typeof out.logTail === 'string' && out.logTail.length > 4000) {
    out.logTail = out.logTail.slice(-4000);
  }
  return out;
}

async function writeGcs(bucket, objectName, payload, token) {
  const url =
    `https://storage.googleapis.com/upload/storage/v1/b/${encodeURIComponent(bucket)}` +
    `/o?uploadType=media&name=${encodeURIComponent(objectName)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json; charset=utf-8',
    },
    body: JSON.stringify(payload, null, 2) + '\n',
  });
  if (!res.ok) {
    return { ok: false, error: `gcs_http_${res.status}` };
  }
  return { ok: true, uri: `gs://${bucket}/${objectName}` };
}

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response('', { status: 204, headers: CORS });
    }
    if (request.method !== 'POST') {
      return json(405, { ok: false, error: 'method not allowed' });
    }

    const bucket = process.env.IOT_ASP_GCS_BUCKET;
    const sa = loadSa();
    if (!bucket || !sa) {
      return json(503, {
        ok: false,
        error: 'ingest not configured',
        hint: 'Set IOT_ASP_GCS_BUCKET + GCP_SA_JSON on the Vercel project',
      });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json(400, { ok: false, error: 'invalid JSON' });
    }
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
      return json(400, { ok: false, error: 'JSON object required' });
    }

    const tel = scrub(body);
    const node = safeNode(tel);
    const ts = safeTs(tel);
    const path = `meta/telemetry/${node}/${ts}-${randomUUID().slice(0, 8)}.json`;

    const tok = await googleAccessToken(sa);
    if (!tok.ok) return json(502, { ok: false, error: tok.error });

    const written = await writeGcs(bucket, path, tel, tok.token);
    if (!written.ok) return json(502, { ok: false, error: written.error });

    return json(200, {
      ok: true,
      path,
      uri: written.uri,
      schemaVersion: tel.schemaVersion,
    });
  },
};

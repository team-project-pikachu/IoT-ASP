// Vercel webhook receiver → GitHub repository_dispatch (issue #37).
//
// Deployed as a Vercel Function at:
//   https://hop-ultrasonic-1digital-design.vercel.app/api/vercel-webhook
// Web Fetch handler: RAW body via `request.text()` so HMAC covers signed bytes.
//
// Vercel Project env vars (names only; values in 1Password vault `dev`):
//   VERCEL_WEBHOOK_SECRET     op://dev/VERCEL_WEBHOOK_SECRET/credential
//   GITHUB_DISPATCH_TOKEN or GITHUB_TOKEN  — Contents write on this repo only
//
// Invariants: never log secret, token, signature, or raw body.
// client_payload is { type, url, id } only. See docs/vercel-webhooks.md.
import { createHmac, timingSafeEqual } from 'node:crypto';

const DISPATCH_URL = 'https://api.github.com/repos/team-project-pikachu/IoT-ASP/dispatches';
const EVENT_TYPE = 'vercel-deployment';
const USER_AGENT = 'IoT-ASP-vercel-webhook-receiver';
const SIGNATURE_HEADER = 'x-vercel-signature';

export const config = { runtime: 'nodejs', maxDuration: 15 };

function reply(status, text) {
  return new Response(text, {
    status,
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

function signatureMatches(secret, rawBody, headerSig) {
  if (typeof headerSig !== 'string' || headerSig.length === 0) return false;
  const expected = createHmac('sha1', secret).update(rawBody).digest('hex');
  const a = Buffer.from(expected, 'utf8');
  const b = Buffer.from(headerSig.trim().toLowerCase(), 'utf8');
  if (a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}

function publicHttpsUrl(val) {
  if (typeof val !== 'string') return '';
  const s = val.trim();
  if (!s) return '';
  const lower = s.toLowerCase();
  // Reject non-https schemes (CodeQL incomplete-url-scheme / XSS vectors).
  if (
    lower.startsWith('http://') ||
    lower.startsWith('javascript:') ||
    lower.startsWith('data:') ||
    lower.startsWith('vbscript:') ||
    lower.startsWith('file:')
  ) {
    return '';
  }
  const beforeSlash = s.split('/')[0];
  if (beforeSlash.includes(':') && !lower.startsWith('https:')) return '';
  if (s.startsWith('https://')) return s;
  if (s.startsWith('//')) return `https:${s}`;
  if (s.includes('.') && !s.includes(' ') && !s.startsWith('.')) return `https://${s}`;
  return '';
}

function pickString(value, fallback) {
  return typeof value === 'string' && value.length > 0 ? value : fallback;
}

export default {
  async fetch(request) {
    if (request.method !== 'POST') return reply(405, 'method not allowed');

    const secret = process.env.VERCEL_WEBHOOK_SECRET;
    const token = process.env.GITHUB_DISPATCH_TOKEN || process.env.GITHUB_TOKEN;
    if (!secret || !token) return reply(500, 'receiver not configured');

    const rawText = await request.text();
    const rawBody = Buffer.from(rawText, 'utf8');
    if (!signatureMatches(secret, rawBody, request.headers.get(SIGNATURE_HEADER))) {
      return reply(403, 'invalid signature');
    }

    let event;
    try {
      event = JSON.parse(rawText);
    } catch {
      return reply(400, 'invalid json');
    }

    const type = pickString(event?.type, 'unknown');
    const url =
      publicHttpsUrl(event?.payload?.deployment?.url) ||
      publicHttpsUrl(event?.payload?.url) ||
      publicHttpsUrl(event?.payload?.deploymentUrl) ||
      '';
    const id = pickString(event?.id, '');

    let res;
    try {
      res = await fetch(DISPATCH_URL, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': USER_AGENT,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: EVENT_TYPE,
          client_payload: { type, url, id },
        }),
      });
    } catch {
      return reply(502, 'dispatch failed');
    }
    if (res.status !== 204) return reply(502, 'dispatch failed');

    return new Response(null, { status: 204 });
  },
};

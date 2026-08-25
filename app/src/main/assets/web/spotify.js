const AUTH = 'https://accounts.spotify.com/authorize';
const TOKEN = 'https://accounts.spotify.com/api/token';
const API = 'https://api.spotify.com/v1';

export const SCOPES = [
  'streaming',
  'user-read-email',
  'user-read-private',
  'user-top-read',
  'user-read-recently-played',
  'playlist-read-private',
  'playlist-read-collaborative',
  'user-read-playback-state',
  'user-modify-playback-state',
  'user-library-read'
].join(' ');

const base64url = bytes => btoa(String.fromCharCode(...new Uint8Array(bytes)))
  .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

async function sha256(text) {
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
}

export function isNativeAndroid() {
  try { return Boolean(window.AndroidMusikplay?.isNative?.()); } catch { return false; }
}

export function getRedirectUri() {
  try {
    const nativeUri = window.AndroidMusikplay?.getRedirectUri?.();
    if (nativeUri) return nativeUri;
  } catch {}
  return `${window.location.origin}${window.location.pathname}`;
}

export function getClientId() {
  const saved = localStorage.getItem('musikplay_client_id');
  if (saved) return saved;
  try { return window.AndroidMusikplay?.getClientId?.() || ''; } catch { return ''; }
}
export function setClientId(v) { localStorage.setItem('musikplay_client_id', v.trim()); }

export async function loginSpotify() {
  const clientId = getClientId();
  if (!clientId) throw new Error('Primero agrega tu Client ID de Spotify.');
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(64)));
  const challenge = base64url(await sha256(verifier));
  const state = base64url(crypto.getRandomValues(new Uint8Array(18)));
  localStorage.setItem('musikplay_verifier', verifier);
  localStorage.setItem('musikplay_state', state);
  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'code',
    redirect_uri: getRedirectUri(),
    scope: SCOPES,
    code_challenge_method: 'S256',
    code_challenge: challenge,
    state,
    show_dialog: 'false'
  });
  window.location.assign(`${AUTH}?${params}`);
}

function saveTokens(data) {
  const prev = JSON.parse(localStorage.getItem('musikplay_tokens') || '{}');
  localStorage.setItem('musikplay_tokens', JSON.stringify({
    access_token: data.access_token,
    refresh_token: data.refresh_token || prev.refresh_token,
    expires_at: Date.now() + (data.expires_in || 3600) * 1000 - 30000
  }));
}

export function logoutSpotify() {
  localStorage.removeItem('musikplay_tokens');
  localStorage.removeItem('musikplay_verifier');
}

export async function handleCallback() {
  const url = new URL(window.location.href);
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');
  if (error) {
    history.replaceState({}, '', `${window.location.origin}${window.location.pathname}`);
    throw new Error(`Spotify: ${error}`);
  }
  if (!code) return false;
  const state = url.searchParams.get('state');
  if (state !== localStorage.getItem('musikplay_state')) throw new Error('La validación de seguridad de Spotify no coincide.');
  const verifier = localStorage.getItem('musikplay_verifier');
  const clientId = getClientId();
  const body = new URLSearchParams({
    client_id: clientId,
    grant_type: 'authorization_code',
    code,
    redirect_uri: getRedirectUri(),
    code_verifier: verifier
  });
  const r = await fetch(TOKEN, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
  if (!r.ok) throw new Error('No fue posible completar el inicio de sesión con Spotify.');
  saveTokens(await r.json());
  history.replaceState({}, '', `${window.location.origin}${window.location.pathname}`);
  return true;
}

async function refresh() {
  const t = JSON.parse(localStorage.getItem('musikplay_tokens') || '{}');
  if (!t.refresh_token) return null;
  const body = new URLSearchParams({
    client_id: getClientId(),
    grant_type: 'refresh_token',
    refresh_token: t.refresh_token
  });
  const r = await fetch(TOKEN, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body });
  if (!r.ok) { logoutSpotify(); return null; }
  const data = await r.json();
  saveTokens(data);
  return data.access_token;
}

export async function getAccessToken() {
  const t = JSON.parse(localStorage.getItem('musikplay_tokens') || '{}');
  if (!t.access_token) return null;
  if (Date.now() >= (t.expires_at || 0)) return refresh();
  return t.access_token;
}

export async function api(path, options = {}) {
  let token = await getAccessToken();
  if (!token) throw new Error('NOT_CONNECTED');
  const doFetch = tk => fetch(`${API}${path}`, {
    ...options,
    headers: { 'Authorization': `Bearer ${tk}`, 'Content-Type': 'application/json', ...(options.headers || {}) }
  });
  let r = await doFetch(token);
  if (r.status === 401) {
    token = await refresh();
    if (!token) throw new Error('NOT_CONNECTED');
    r = await doFetch(token);
  }
  if (r.status === 204) return null;
  if (r.status === 429) throw new Error('Spotify alcanzó el límite temporal de solicitudes. Intenta nuevamente en un momento.');
  if (!r.ok) {
    const body = await r.text();
    throw new Error(`Spotify ${r.status}: ${body.slice(0, 180)}`);
  }
  return r.json();
}

export async function loadSpotifyHome() {
  const [profile, top, recent, playlists] = await Promise.all([
    api('/me'),
    api('/me/top/tracks?limit=10&time_range=short_term'),
    api('/me/player/recently-played?limit=12'),
    api('/me/playlists?limit=12')
  ]);
  return {
    profile,
    topTracks: top?.items || [],
    recentTracks: (recent?.items || []).map(x => x.track).filter(Boolean),
    playlists: playlists?.items || []
  };
}

export async function searchTracks(query) {
  if (!query.trim()) return [];
  const d = await api(`/search?${new URLSearchParams({ q: query.trim(), type: 'track', limit: '10' })}`);
  return d?.tracks?.items || [];
}

export async function loadSavedTracks() {
  const d = await api('/me/tracks?limit=20');
  return (d?.items || []).map(x => x.track || x.item).filter(Boolean);
}

export async function getDevices() {
  const d = await api('/me/player/devices');
  return d?.devices || [];
}

export async function getPlaybackState() {
  return api('/me/player');
}

export async function getQueue() {
  const d = await api('/me/player/queue');
  return d || { queue: [] };
}

export async function controlPlayer(action, deviceId, extra = {}) {
  const suffix = deviceId ? `?device_id=${encodeURIComponent(deviceId)}` : '';
  if (action === 'playTrack') return api(`/me/player/play${suffix}`, { method: 'PUT', body: JSON.stringify({ uris: [extra.uri] }) });
  if (action === 'playContext') return api(`/me/player/play${suffix}`, { method: 'PUT', body: JSON.stringify({ context_uri: extra.uri }) });
  if (action === 'resume') return api(`/me/player/play${suffix}`, { method: 'PUT' });
  if (action === 'pause') return api(`/me/player/pause${suffix}`, { method: 'PUT' });
  if (action === 'next') return api(`/me/player/next${suffix}`, { method: 'POST' });
  if (action === 'previous') return api(`/me/player/previous${suffix}`, { method: 'POST' });
  if (action === 'transfer') return api('/me/player', { method: 'PUT', body: JSON.stringify({ device_ids: [deviceId], play: Boolean(extra.play) }) });
}

export function youtubeMusicUrl(track) {
  const title = track?.name || '';
  const artist = track?.artists?.map(a => a.name).join(' ') || '';
  return `https://music.youtube.com/search?q=${encodeURIComponent(`${title} ${artist}`.trim())}`;
}

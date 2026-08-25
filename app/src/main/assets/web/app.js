import {
  controlPlayer, getAccessToken, getClientId, getDevices, getPlaybackState, getQueue,
  getRedirectUri, handleCallback, loadSavedTracks, loadSpotifyHome, loginSpotify,
  logoutSpotify, searchTracks, setClientId, youtubeMusicUrl, isNativeAndroid
} from './spotify.js';

const $app = document.getElementById('app');
const nativeAndroid = isNativeAndroid();
if (nativeAndroid) document.documentElement.classList.add('native-app');
const demo = {
  profile: { display_name: 'Musiklover' },
  topTracks: [
    ['Neon Drive','Nova Avenue'],['Midnight Pulse','Lunar Echo'],['City Lights','Astra Lane'],
    ['Afterglow','Milo North'],['Velvet Sky','Sienna Ray'],['Electric Bloom','Kairo West'],
    ['Nocturne 22','Lume'],['Golden Hour','June Atlas'],['Night Runner','Sonic Vale'],['Cloud Nine','Ari Flux']
  ].map((x,i)=>({id:`d${i}`,uri:`demo:${i}`,name:x[0],artists:[{name:x[1]}],album:{name:'Musikplay Demo',images:[]},demo:true})),
  recentTracks: [
    ['Horizons','Ivy North'],['Parallel','Eon'],['Low Gravity','Monarch'],['Warm Static','Riva'],['Blue Motion','Lina Ford'],['Daybreak','Solace']
  ].map((x,i)=>({id:`r${i}`,uri:`demo:r${i}`,name:x[0],artists:[{name:x[1]}],album:{name:'Recently played',images:[]},demo:true})),
  playlists: [
    {id:'p1',uri:'demo:p1',name:'Mix diario',description:'Lo que encaja contigo hoy',images:[],demo:true},
    {id:'p2',uri:'demo:p2',name:'Modo noche',description:'Suave, profundo y sin prisa',images:[],demo:true},
    {id:'p3',uri:'demo:p3',name:'Para conducir',description:'Energía constante para la ruta',images:[],demo:true},
    {id:'p4',uri:'demo:p4',name:'Sube el ánimo',description:'Un empujón de energía',images:[],demo:true}
  ]
};
const mixThemes=[['Mix Diario','Tus canciones más repetidas'],['Night Flow','Para escuchar de noche'],['Ruta Musikplay','Energía para conducir'],['Descubrimiento','Un giro a lo que sueles escuchar']];
const storedMode = localStorage.getItem('musikplay_playback_mode');
const state={
  tab:'home',data:demo,connected:false,loading:true,notice:'',search:'',results:[],saved:[],
  clientId:getClientId(),showSetup:false,copied:false,sdkReady:false,deviceId:'',playerState:null,
  playerError:'',installEvent:null,playbackMode:nativeAndroid?'background':(storedMode==='web'?'web':'background'),devices:[],
  selectedDeviceId:localStorage.getItem('musikplay_device_id')||'',remotePlayback:null,queue:[],
  showPlayer:false,deviceBusy:false,lastDeviceSync:0,
  nativeRemoteReady:nativeAndroid?Boolean(window.AndroidMusikplay?.isSpotifyRemoteReady?.()):false,
  nativeRemoteMessage:nativeAndroid?'Conectando con Spotify…':'',nativeTrack:null
};
let player=null, searchTimer=null, pollTimer=null;

function esc(s=''){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function artists(t){return t?.artists?.map(a=>a.name).join(', ')||''}
function current(){return state.remotePlayback?.item||state.playerState?.track_window?.current_track||null}
function isPaused(){return state.remotePlayback? !state.remotePlayback.is_playing : (state.playerState?.paused??true)}
function greeting(){const h=new Date().getHours();return h<12?'Buenos días':h<19?'Buenas tardes':'Buenas noches'}
function isWebDevice(d){return Boolean(d?.id&&state.deviceId&&d.id===state.deviceId)||d?.name==='Musikplay'}
function externalDevices(){return state.devices.filter(d=>d?.id&&!d.is_restricted&&!isWebDevice(d))}
function activeDevice(){return state.devices.find(d=>d.is_active)||state.remotePlayback?.device||null}
function selectedExternal(){return externalDevices().find(d=>d.id===state.selectedDeviceId)||externalDevices().find(d=>d.is_active)||externalDevices()[0]||null}
function targetDevice(){return state.playbackMode==='web'?state.deviceId:(selectedExternal()?.id||'')}
function deviceIcon(type=''){const t=String(type).toLowerCase();return t.includes('smartphone')||t.includes('phone')?'▯':t.includes('computer')?'▰':t.includes('speaker')?'◖':'◉'}
function playbackLabel(){if(nativeAndroid)return state.nativeRemoteReady?'ESTE CELULAR':'ANDROID';if(state.playbackMode==='web')return 'WEB';const d=selectedExternal()||activeDevice();return d?.name?String(d.name).slice(0,18):'2º PLANO'}
function nativeBridge(){return nativeAndroid?window.AndroidMusikplay:null}
function nativeConnect(){try{nativeBridge()?.connectSpotifyRemote?.()}catch{}}
function nativeRequestState(){try{nativeBridge()?.requestSpotifyPlayerState?.()}catch{}}
function nativePlay(uri){try{return Boolean(nativeBridge()?.playSpotifyUri?.(uri))}catch{return false}}
function nativeTransport(action){
  try{
    const b=nativeBridge();
    if(action==='pause')b?.pauseSpotify?.();
    else if(action==='resume')b?.resumeSpotify?.();
    else if(action==='next')b?.nextSpotify?.();
    else if(action==='previous')b?.previousSpotify?.();
    else return false;
    return true;
  }catch{return false}
}
function art(item,index=0,extra=''){
  const src=item?.album?.images?.[0]?.url||item?.images?.[0]?.url;
  if(src)return `<img class="artwork ${extra}" src="${esc(src)}" alt="">`;
  return `<div class="artwork fallback art-${index%6} ${extra}"><span class="disc-symbol">♫</span></div>`;
}
function trackRow(t,i){const active=current()?.id===t.id;return `<button class="track-row ${active?'active':''}" data-action="play" data-uri="${esc(t.uri)}"><div class="track-index">${active?'<span class="bars"><i></i><i></i><i></i></span>':i+1}</div>${art(t,i)}<div class="track-copy"><strong>${esc(t.name)}</strong><span>${esc(artists(t))}</span></div><div class="track-action">▶</div></button>`}
function nav(){return `<nav class="bottom-nav">${[['⌂','home','Inicio'],['⌕','search','Buscar'],['♫','library','Biblioteca'],['⚙','settings','Ajustes']].map(([ic,id,label])=>`<button class="${state.tab===id?'on':''}" data-action="tab" data-tab="${id}"><span class="nav-symbol">${ic}</span><span>${label}</span></button>`).join('')}</nav>`}
function topbar(){return `<header class="topbar"><button class="brand" data-action="tab" data-tab="home"><span class="brand-mark"><span class="brand-symbol">♫</span></span><span class="brand-word">MUSIK<span>PLAY</span></span></button><div class="top-actions"><span class="status-pill ${state.connected?'connected':''}">${state.connected?(nativeAndroid?(state.nativeRemoteReady?'● Listo':'● Spotify'):'● Spotify'):'○ Demo'}</span>${nativeAndroid?'':`<button class="icon-btn" data-action="tab" data-tab="settings">◉</button>`}</div></header>`}

function home(){const tracks=state.data.topTracks?.length?state.data.topTracks:demo.topTracks;const recent=state.data.recentTracks?.length?state.data.recentTracks:demo.recentTracks;return `
<section class="hero"><div><span class="eyebrow">${greeting()}</span><h1>${esc((state.data.profile?.display_name||'Musiklover').split(' ')[0])}<span>.</span></h1><p>Tu música, sin ruido alrededor.</p></div><button class="surprise" data-action="surprise"><span class="spark">✦</span> Sorpréndeme</button></section>
${!state.connected?`<section class="connect-card"><div class="connect-icon">♫</div><div><span class="mini-tag">ACTIVA TU MÚSICA</span><h3>Conecta Spotify Premium</h3><p>Trae tus favoritos, historial, playlists y reproduce desde Musikplay.</p></div><button data-action="connect">Conectar</button></section>`:`<section class="background-banner"><span class="bg-icon">${state.playbackMode==='background'?'◉':'♫'}</span><div><b>${state.playbackMode==='background'?(nativeAndroid?'Musikplay Android activo':'Segundo plano activo'):'Reproductor web activo'}</b><span>${state.playbackMode==='background'?(nativeAndroid?'La interfaz queda en Musikplay y Spotify mantiene el audio al bloquear o cambiar de app.':'Spotify oficial mantiene el audio aunque bloquees el celular.'):'Puedes cambiar al modo de máxima estabilidad desde Ajustes.'}</span></div><button data-action="tab" data-tab="settings">${state.playbackMode==='background'?'VER':'CAMBIAR'}</button></section>`}
<section><div class="section-head"><div><span class="eyebrow">MUSIK AI</span><h2>Hecho para ti</h2></div><button data-action="surprise">✦ Afinar</button></div><div class="mix-grid">${mixThemes.map((m,i)=>`<button class="mix-card mix-${i}" data-action="play" data-uri="${esc(tracks[(i*2)%tracks.length].uri)}"><span class="mix-orb">◉</span><span class="mix-index">0${i+1}</span><div><h3>${m[0]}</h3><p>${m[1]}</p></div><span class="mix-play">▶</span></button>`).join('')}</div></section>
<section><div class="section-head"><div><span class="eyebrow">TU MOMENTO</span><h2>${state.connected?'Lo que más escuchas':'Así se verá con Spotify'}</h2></div></div><div class="horizontal-cards">${tracks.slice(0,8).map((t,i)=>`<button class="album-card" data-action="play" data-uri="${esc(t.uri)}">${art(t,i)}<strong>${esc(t.name)}</strong><span>${esc(t.artists?.[0]?.name||'')}</span><i class="float-play">▶</i></button>`).join('')}</div></section>
<section><div class="section-head"><div><span class="eyebrow">RECIENTE</span><h2>Vuelve a escuchar</h2></div><button data-action="tab" data-tab="library">Ver todo ›</button></div><div class="track-list">${recent.slice(0,6).map(trackRow).join('')}</div></section>`}

function searchPage(){return `<section class="page-section"><span class="eyebrow">ENCUENTRA TU SONIDO</span><h1>Buscar</h1><div class="searchbox"><span class="search-symbol">⌕</span><input id="searchInput" value="${esc(state.search)}" placeholder="Canción o artista..." autocomplete="off"><button data-action="clear-search">${state.search?'×':''}</button></div>${searchBody()}</section>`}
function searchBody(){if(!state.connected)return `<div class="empty-state"><span style="font-size:40px">⌕</span><h3>Conecta Spotify para buscar</h3><p>Musikplay buscará directamente en el catálogo de Spotify.</p><button class="primary" data-action="connect">Conectar Spotify</button></div>`;if(state.searching)return `<div class="skeleton-list">${[1,2,3,4,5].map(()=>'<i></i>').join('')}</div>`;if(state.results.length)return `<div class="result-head"><span>${state.results.length} resultados</span><a href="https://music.youtube.com/search?q=${encodeURIComponent(state.search)}" target="_blank" rel="noopener">Buscar en YouTube Music ↗</a></div><div class="track-list">${state.results.map((t,i)=>`<div class="result-wrap">${trackRow(t,i)}<a class="yt-mini" href="${youtubeMusicUrl(t)}" target="_blank" rel="noopener" title="Abrir en YouTube Music">▶</a></div>`).join('')}</div>`;return `<div class="discover-grid">${['Pop para hoy','Reggaetón','Rock','Electrónica','Para entrenar','Relax'].map((x,i)=>`<button class="discover d${i}" data-action="preset-search" data-query="${esc(x)}">${x}<span class="disc-symbol">♫</span></button>`).join('')}</div>`}

function libraryPage(){return `<section class="page-section"><span class="eyebrow">TU ESPACIO</span><h1>Biblioteca</h1><div class="library-tabs"><button class="selected">Canciones</button><button>Playlists</button><button>Artistas</button></div>${!state.connected?`<div class="empty-state"><span style="font-size:36px">♫</span><h3>Tu biblioteca aparecerá aquí</h3><p>Conecta Spotify y Musikplay cargará tus canciones y playlists.</p><button class="primary" data-action="connect">Conectar Spotify</button></div>`:`<div class="library-summary"><div><span class="line-symbol">♥</span><span><b>${state.saved.length||'—'}</b> favoritas cargadas</span></div><div><span class="line-symbol">☷</span><span><b>${state.data.playlists?.length||0}</b> playlists</span></div></div><div class="track-list">${state.saved.length?state.saved.map(trackRow).join(''):'<p class="muted">No se pudieron cargar canciones guardadas o aún no tienes favoritas.</p>'}</div><h2 class="subheading">Tus playlists</h2><div class="playlist-grid">${(state.data.playlists||[]).map((p,i)=>`<button class="playlist-card" data-action="play-context" data-uri="${esc(p.uri||'')}">${art(p,i)}<strong>${esc(p.name)}</strong><span>${esc(p.description||'Playlist de Spotify')}</span><i class="playlist-play">▶</i></button>`).join('')}</div>`}</section>`}

function deviceRows(){
  if(nativeAndroid){
    return `<div class="native-engine ${state.nativeRemoteReady?'ready':''}">
      <span class="native-engine-icon">${state.nativeRemoteReady?'✓':'↻'}</span>
      <div><b>${state.nativeRemoteReady?'Motor Android conectado':'Motor Android pendiente'}</b><span>${esc(state.nativeRemoteMessage||'Musikplay se conecta directamente al servicio de Spotify del celular.')}</span></div>
      <button data-action="native-connect">${state.nativeRemoteReady?'Reconectar':'Autorizar'}</button>
    </div>`;
  }
  const ext=externalDevices();
  if(!ext.length)return `<div class="no-device"><b>No veo otro dispositivo Spotify todavía</b><span>Abre Spotify oficial en el celular, reproduce o pausa cualquier canción una vez y vuelve a tocar “Actualizar”.</span><a href="https://open.spotify.com" target="_blank" rel="noopener">Abrir Spotify ↗</a></div>`;
  return `<div class="device-list">${ext.map(d=>`<button class="device-row ${d.id===state.selectedDeviceId?'selected':''}" data-action="select-device" data-device="${esc(d.id)}"><span class="device-ico">${deviceIcon(d.type)}</span><span><b>${esc(d.name)}</b><small>${esc(d.type||'Spotify Connect')}${d.is_active?' · Reproduciendo':''}</small></span><i>${d.id===state.selectedDeviceId?'✓':d.is_active?'●':'○'}</i></button>`).join('')}</div>`;
}
function settingsPage(){return `<section class="page-section settings-page"><span class="eyebrow">PERSONALIZA MUSIKPLAY</span><h1>Ajustes</h1>
<div class="settings-card profile-card"><div class="avatar">${state.connected?esc(state.data.profile?.display_name?.[0]||'M'):'M'}</div><div><h3>${state.connected?esc(state.data.profile?.display_name||'Spotify'):'Modo demostración'}</h3><p>${state.connected?'Spotify conectado':'Conecta tu cuenta Premium para activar la música real.'}</p></div><span class="connection-dot ${state.connected?'on':''}"></span></div>
<div class="settings-card"><div class="setting-line"><div class="setting-icon">♫</div><div><h3>Cuenta de Spotify</h3><p>${getClientId()?'Client ID configurado':'Falta configurar el Client ID'}</p></div>${nativeAndroid?'':`<button data-action="setup">Configurar</button>`}</div>${state.connected?`<button class="danger-line" data-action="disconnect">↪ Desconectar Spotify</button>`:`<button class="primary full" data-action="connect">Conectar Spotify</button>`}</div>
${state.connected?`<div class="settings-card hifi-card"><span class="eyebrow">REPRODUCCIÓN</span><h3 class="card-title">${nativeAndroid?'Musikplay Android':'Motor de reproducción'}</h3>${nativeAndroid?`<p class="engine-copy">Musikplay controla la reproducción desde su propia interfaz. Spotify permanece como servicio de audio autorizado para mantener la música al bloquear la pantalla.</p>${deviceRows()}<div class="native-actions"><button class="primary full" data-action="native-connect">${state.nativeRemoteReady?'Reconectar motor':'Autorizar control de Spotify'}</button><button class="secondary full" data-action="open-spotify-native">Abrir Spotify oficial</button></div>`:`<div class="mode-switch"><button class="${state.playbackMode==='background'?'on':''}" data-action="mode" data-mode="background"><b>◉ Spotify oficial</b><span>Segundo plano</span></button><button class="${state.playbackMode==='web'?'on':''}" data-action="mode" data-mode="web"><b>♫ Musikplay Web</b><span>Respaldo</span></button></div><div class="mode-explain">${state.playbackMode==='background'?`<b>Segundo plano + máxima calidad disponible</b><p>El audio queda en Spotify oficial/Spotify Connect. Puedes bloquear el celular o cambiar de app sin cortar la música.</p><div class="device-head"><span>Dispositivo de audio</span><button data-action="refresh-devices">↻ Actualizar</button></div>${deviceRows()}`:`<b>Reproductor dentro de Musikplay</b><p>Usa Spotify Web Playback SDK y Media Session.</p><div class="web-status"><span class="connection-dot ${state.sdkReady?'on':''}"></span>${state.sdkReady?'Musikplay Web listo':'Activando reproductor web…'}</div>`}</div>`}</div>`:''}
<div class="settings-card"><div class="setting-line"><div class="setting-icon">◉</div><div><h3>Estado del reproductor</h3><p>${state.connected?(nativeAndroid?(state.nativeRemoteReady?'Listo para reproducir desde Musikplay':(state.nativeRemoteMessage||'Autoriza el motor Android')):(state.playbackMode==='background'?(selectedExternal()?`Listo en ${esc(selectedExternal().name)}`:'Abre Spotify oficial para detectar tu celular'):(state.sdkReady?'Musikplay Web está activo':'Iniciando reproductor…'))):'Disponible al conectar Spotify'}</p></div><span class="quality ${state.connected&&(!nativeAndroid||state.nativeRemoteReady)?'on':''}">${nativeAndroid?'APP':state.playbackMode==='background'?'BG':'WEB'}</span></div><p class="muted quality-note">Musikplay no recomprime el audio. La calidad final depende de la configuración de Spotify y del dispositivo de salida.</p>${state.playerError?`<p class="error-copy">${esc(state.playerError)}</p>`:''}</div>
<div class="settings-card"><div class="setting-line"><div class="setting-icon">▶</div><div><h3>YouTube Premium</h3><p>Musikplay abre la búsqueda en YouTube Music sin extraer ni convertir el audio.</p></div></div></div>
${state.installEvent?`<div class="settings-card"><div class="setting-line"><div class="setting-icon">▣</div><div><h3>Instalar Musikplay</h3><p>Úsala como una app desde la pantalla de inicio.</p></div><button data-action="install">Instalar</button></div></div>`:''}<div class="about"><span>Musikplay Android V2.1</span><span>App Remote + segundo plano</span></div></section>`}

function miniPlayer(){const c=current();if(!state.connected&&!c)return '';if(c)return `<div class="mini-player visible"><button class="mini-art-btn" data-action="open-player">${art(c,2)}</button><div class="mini-copy" data-action="open-player"><strong>${esc(c.name)}</strong><span>${esc(artists(c))}</span><small>${nativeAndroid?(state.nativeRemoteReady?'● ESTE CELULAR':'○ CONECTANDO'):(state.playbackMode==='background'?'◉':'♫')+' '+esc(playbackLabel())}</small></div><button class="mini-skip" data-action="previous" aria-label="Anterior">⏮</button><button class="mini-toggle" data-action="toggle" aria-label="Reproducir o pausar">${isPaused()?'▶':'Ⅱ'}</button><button class="mini-skip" data-action="next" aria-label="Siguiente">⏭</button></div>`;return `<div class="mini-player waiting"><div class="waiting-disc">♫</div><div class="mini-copy"><strong>${nativeAndroid?'Motor de reproducción':'Musikplay listo'}</strong><span>${nativeAndroid?(state.nativeRemoteReady?'Toca una canción para empezar':esc(state.nativeRemoteMessage||'Conectando con Spotify…')):(state.playbackMode==='background'?'Abre Spotify oficial si no aparece tu celular':'Activando Spotify Player…')}</span></div>${nativeAndroid&&!state.nativeRemoteReady?`<button class="mini-connect" data-action="native-connect">Conectar</button>`:''}</div>`}
function playerSheet(){if(!state.showPlayer)return '';const c=current();if(!c)return '';const d=activeDevice()||selectedExternal();return `<div class="player-sheet-backdrop" data-action="close-player"><section class="player-sheet" data-action="sheet"><button class="sheet-close" data-action="close-player">⌄</button><span class="eyebrow">REPRODUCIENDO AHORA</span><div class="sheet-art">${art(c,3)}</div><div class="sheet-copy"><h2>${esc(c.name)}</h2><p>${esc(artists(c))}</p></div><div class="sheet-device"><span>${deviceIcon(d?.type)}</span><div><b>${esc(d?.name||playbackLabel())}</b><small>${state.playbackMode==='background'?'Spotify Connect · segundo plano':'Musikplay Web'}</small></div></div><div class="sheet-controls"><button data-action="previous">⏮</button><button class="main" data-action="toggle">${isPaused()?'▶':'Ⅱ'}</button><button data-action="next">⏭</button></div>${state.queue?.length?`<div class="queue"><div class="queue-title"><b>Siguiente</b><span>${state.queue.length} en cola</span></div>${state.queue.slice(0,4).map((t,i)=>`<div class="queue-row">${art(t,i)}<span><b>${esc(t.name)}</b><small>${esc(artists(t))}</small></span></div>`).join('')}</div>`:''}</section></div>`}
function modal(){if(!state.showSetup)return '';return `<div class="modal-backdrop" data-action="backdrop"><div class="modal"><button class="modal-close" data-action="close-setup">×</button><span class="modal-icon">♫</span><span class="eyebrow">SPOTIFY FOR DEVELOPERS</span><h2>Conectar Musikplay</h2><p>Musikplay usa OAuth con PKCE. En Android el Client ID viene preconfigurado en la app; nunca se guarda un Client Secret.</p><label>Client ID<input id="clientIdInput" value="${esc(state.clientId)}" placeholder="Ej. 4f8c..."></label><label>Redirect URI que debes registrar<div class="copy-field"><code>${esc(getRedirectUri())}</code><button data-action="copy-redirect">${state.copied?'✓':'▣'}</button></div></label><div class="setup-steps"><b>En Spotify Developer Dashboard:</b><span>1. Crea una app llamada Musikplay.</span><span>2. Agrega exactamente el Redirect URI mostrado arriba.</span><span>3. Guarda y copia el Client ID aquí.</span><a class="dashboard-link" href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener noreferrer">Abrir Spotify Developer Dashboard ↗</a></div><button class="primary full" data-action="save-config">Guardar configuración</button><button class="text-btn" data-action="save-connect">Guardar y conectar Spotify</button></div></div>`}
function loading(){return `<div class="loading"><div class="pulse-logo">♫</div><strong>Cargando Musikplay</strong></div>`}
function render(){const focused=document.activeElement?.id;const sel=focused==='searchInput'?document.activeElement?.selectionStart:null;const body=state.loading?loading():state.tab==='home'?home():state.tab==='search'?searchPage():state.tab==='library'?libraryPage():settingsPage();$app.innerHTML=`<div class="app-shell"><div class="ambient ambient-a"></div><div class="ambient ambient-b"></div>${state.notice?`<div class="toast" data-action="dismiss">${esc(state.notice)}<b>×</b></div>`:''}${topbar()}<main class="content ${current()?'with-player':''}">${body}</main>${miniPlayer()}${nav()}${modal()}${playerSheet()}</div>`;if(focused==='searchInput'){const i=document.getElementById('searchInput');if(i){i.focus();const p=Math.min(sel??i.value.length,i.value.length);i.setSelectionRange(p,p)}}}
function findTrackByUri(uri){return [...(state.data.topTracks||[]),...(state.data.recentTracks||[]),...(state.results||[]),...(state.saved||[]),...demo.topTracks,...demo.recentTracks].find(t=>t.uri===uri)}
function notify(msg){state.notice=msg;render();setTimeout(()=>{if(state.notice===msg){state.notice='';render()}},4600)}

async function connect(){if(!getClientId()){state.showSetup=true;render();return}try{await loginSpotify()}catch(e){notify(e.message)}}
async function refreshDevices(renderAfter=true){if(!state.connected)return;state.deviceBusy=true;try{state.devices=await getDevices();state.lastDeviceSync=Date.now();const ext=externalDevices();if(state.selectedDeviceId&&!ext.some(d=>d.id===state.selectedDeviceId))state.selectedDeviceId='';if(!state.selectedDeviceId&&ext.length){const pick=ext.find(d=>d.is_active)||ext.find(d=>String(d.type).toLowerCase().includes('smartphone'))||ext[0];state.selectedDeviceId=pick.id;localStorage.setItem('musikplay_device_id',pick.id)}}catch(e){if(!String(e.message).includes('204'))state.playerError=e.message}state.deviceBusy=false;if(renderAfter)render()}
async function syncPlayback(full=false){
  if(!state.connected)return;
  if(nativeAndroid){
    nativeRequestState();
    if(state.showPlayer){try{const q=await getQueue();state.queue=q?.queue||[]}catch{}}
    if(full)render();
    return;
  }
  try{const pb=await getPlaybackState();state.remotePlayback=pb||null;if(full||Date.now()-state.lastDeviceSync>18000)await refreshDevices(false);if(state.showPlayer){try{const q=await getQueue();state.queue=q?.queue||[]}catch{}}render()}catch(e){if(e.message!=='NOT_CONNECTED')state.playerError=e.message}
}
async function requireTarget(){
  if(nativeAndroid){
    if(!state.nativeRemoteReady)nativeConnect();
    return 'native';
  }
  if(state.playbackMode==='web'){await player?.activateElement?.();if(!state.deviceId)throw new Error('Musikplay Web todavía se está activando.');return state.deviceId}
  await refreshDevices(false);const d=selectedExternal();if(!d)throw new Error('Abre Spotify oficial en tu celular, reproduce o pausa una canción una vez y luego vuelve a Musikplay.');state.selectedDeviceId=d.id;localStorage.setItem('musikplay_device_id',d.id);return d.id
}
async function playUri(uri){
  const t=findTrackByUri(uri);
  if(t?.demo){state.showSetup=true;notify('Conecta Spotify para reproducir música real.');return}
  try{
    if(nativeAndroid){
      if(t) state.remotePlayback={is_playing:true,item:t,device:{id:'native',name:'Este celular',type:'Smartphone'}};
      render();
      nativePlay(uri);
      setTimeout(nativeRequestState,700);
      return;
    }
    const id=await requireTarget();await controlPlayer('playTrack',id,{uri});setTimeout(()=>syncPlayback(true),650)
  }catch(e){notify(e.message)}
}
async function playContext(uri){
  if(!uri||uri.startsWith('demo:')){notify('Conecta Spotify para abrir tus playlists reales.');return}
  try{
    if(nativeAndroid){nativePlay(uri);setTimeout(nativeRequestState,700);return}
    const id=await requireTarget();await controlPlayer('playContext',id,{uri});setTimeout(()=>syncPlayback(true),650)
  }catch(e){notify(e.message)}
}
async function transport(action){
  try{
    if(nativeAndroid){
      const cmd=action==='toggle'?(isPaused()?'resume':'pause'):action;
      nativeTransport(cmd);
      if(state.remotePlayback&&action==='toggle')state.remotePlayback.is_playing=isPaused();
      render();setTimeout(nativeRequestState,400);return;
    }
    const id=await requireTarget();if(action==='toggle')await controlPlayer(isPaused()?'resume':'pause',id);else await controlPlayer(action,id);setTimeout(()=>syncPlayback(false),450)
  }catch(e){notify(e.message)}
}
async function switchMode(mode){if(nativeAndroid)mode='background';if(!['background','web'].includes(mode)||mode===state.playbackMode)return;state.playbackMode=mode;localStorage.setItem('musikplay_playback_mode',mode);try{if(mode==='background'){await refreshDevices(false);const d=selectedExternal();if(d){const wasPlaying=!isPaused();await controlPlayer('transfer',d.id,{play:wasPlaying});state.selectedDeviceId=d.id;localStorage.setItem('musikplay_device_id',d.id);notify(`Segundo plano activo en ${d.name}.`)}else notify('Modo segundo plano activado. Abre Spotify oficial para detectar tu celular.')}else{await player?.activateElement?.();if(!state.deviceId)throw new Error('Musikplay Web todavía se está activando.');await controlPlayer('transfer',state.deviceId,{play:!isPaused()});notify('Reproducción transferida a Musikplay Web.')}setTimeout(()=>syncPlayback(true),600)}catch(e){notify(e.message)}render()}
async function initPlayer(){if(player||!state.connected||!window.Spotify)return;const token=await getAccessToken();if(!token)return;player=new window.Spotify.Player({name:'Musikplay',getOAuthToken:async cb=>cb(await getAccessToken()),volume:.85,enableMediaSession:true});player.addListener('ready',({device_id})=>{state.deviceId=device_id;state.sdkReady=true;refreshDevices(false).finally(()=>render())});player.addListener('not_ready',()=>{state.sdkReady=false;render()});player.addListener('player_state_changed',s=>{if(s){state.playerState=s;if(state.playbackMode==='web')state.remotePlayback={is_playing:!s.paused,item:s.track_window?.current_track,device:{id:state.deviceId,name:'Musikplay',type:'Computer'}};render()}});['initialization_error','authentication_error','account_error','playback_error'].forEach(ev=>player.addListener(ev,({message})=>{state.playerError=message;render()}));await player.connect()}
async function boot(){try{await handleCallback()}catch(e){state.notice=e.message}const token=await getAccessToken();if(token){try{state.data=await loadSpotifyHome();state.connected=true;loadSavedTracks().then(x=>{state.saved=x;render()}).catch(()=>{});loadSdk();if(nativeAndroid)nativeConnect();await syncPlayback(true);pollTimer=setInterval(()=>syncPlayback(false),7000)}catch(e){state.notice=e.message}}state.loading=false;render();if(nativeAndroid&&state.connected)setTimeout(nativeConnect,450)}
function loadSdk(){if(nativeAndroid)return;if(window.Spotify){initPlayer();return}if(document.querySelector('script[data-spotify-sdk]'))return;const s=document.createElement('script');s.src='https://sdk.scdn.co/spotify-player.js';s.async=true;s.dataset.spotifySdk='1';document.body.appendChild(s);window.onSpotifyWebPlaybackSDKReady=initPlayer}

window.onMusikplayNativeRemoteState=(ready,message)=>{
  if(!nativeAndroid)return;
  state.nativeRemoteReady=Boolean(ready);
  state.nativeRemoteMessage=message||'';
  if(ready)state.playerError='';
  render();
};
window.onMusikplayNativeRemoteError=(message)=>{
  if(!nativeAndroid)return;
  state.nativeRemoteReady=false;
  state.nativeRemoteMessage=message||'No se pudo conectar con Spotify';
  state.playerError=state.nativeRemoteMessage;
  notify(state.nativeRemoteMessage);
};
window.onMusikplayNativePlayerState=(payload)=>{
  if(!nativeAndroid||!payload)return;
  const existing=findTrackByUri(payload.uri);
  const item=existing||{
    id:payload.uri||payload.name||'native',
    uri:payload.uri||'',
    name:payload.name||'Spotify',
    artists:[{name:payload.artist||''}],
    album:{name:'Spotify',images:[]}
  };
  state.nativeTrack=item;
  state.remotePlayback={
    is_playing:!payload.paused,
    item,
    progress_ms:Number(payload.position||0),
    device:{id:'native',name:'Este celular',type:'Smartphone'}
  };
  state.nativeRemoteReady=true;
  state.nativeRemoteMessage='Musikplay controla Spotify en este celular';
  render();
};

window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();state.installEvent=e;render()});
window.addEventListener('visibilitychange',()=>{if(!document.hidden&&state.connected)syncPlayback(true)});
window.addEventListener('focus',()=>{if(state.connected)syncPlayback(true)});
if('serviceWorker'in navigator&&!nativeAndroid)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));
$app.addEventListener('click',async e=>{const b=e.target.closest('[data-action]');if(!b)return;const a=b.dataset.action;if(a==='sheet'){e.stopPropagation();return}if(a==='tab'){state.tab=b.dataset.tab;render();window.scrollTo({top:0,behavior:'smooth'})}else if(a==='dismiss')state.notice='',render();else if(a==='connect')connect();else if(a==='setup')state.showSetup=true,render();else if(a==='close-setup')state.showSetup=false,render();else if(a==='backdrop'&&e.target===b)state.showSetup=false,render();else if(a==='save-config'){state.clientId=document.getElementById('clientIdInput')?.value||state.clientId;setClientId(state.clientId);state.showSetup=false;notify('Client ID guardado. Ahora pulsa “Conectar Spotify”.')}else if(a==='save-connect'){state.clientId=document.getElementById('clientIdInput')?.value||state.clientId;setClientId(state.clientId);state.showSetup=false;render();connect()}else if(a==='copy-redirect'){await navigator.clipboard.writeText(getRedirectUri());state.copied=true;render();setTimeout(()=>{state.copied=false;render()},1200)}else if(a==='disconnect'){logoutSpotify();clearInterval(pollTimer);state.connected=false;state.data=demo;state.saved=[];state.deviceId='';state.devices=[];state.remotePlayback=null;state.sdkReady=false;player?.disconnect();player=null;render()}else if(a==='play')playUri(b.dataset.uri);else if(a==='play-context')playContext(b.dataset.uri);else if(a==='surprise'){const tracks=state.data.topTracks?.length?state.data.topTracks:demo.topTracks;playUri(tracks[Math.floor(Math.random()*tracks.length)].uri)}else if(a==='toggle')transport('toggle');else if(a==='next')transport('next');else if(a==='previous')transport('previous');else if(a==='mode')switchMode(b.dataset.mode);else if(a==='refresh-devices')refreshDevices(true);else if(a==='native-connect'){nativeConnect();notify('Conectando Musikplay con Spotify…')}else if(a==='open-spotify-native'){try{window.AndroidMusikplay?.openSpotify?.()}catch{}}else if(a==='select-device'){state.selectedDeviceId=b.dataset.device;localStorage.setItem('musikplay_device_id',state.selectedDeviceId);render();notify('Dispositivo seleccionado. La próxima reproducción irá allí.')}else if(a==='open-player'){state.showPlayer=true;syncPlayback(true)}else if(a==='close-player'){state.showPlayer=false;render()}else if(a==='clear-search'){state.search='';state.results=[];render()}else if(a==='preset-search'){state.search=b.dataset.query;render();doSearch()}else if(a==='install'&&state.installEvent){await state.installEvent.prompt();state.installEvent=null;render()}});
$app.addEventListener('input',e=>{if(e.target.id==='clientIdInput'){state.clientId=e.target.value;return}if(e.target.id==='searchInput'){state.search=e.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(doSearch,350)}});
async function doSearch(){if(!state.connected||state.search.trim().length<2){state.results=[];render();return}state.searching=true;render();try{state.results=await searchTracks(state.search)}catch(e){state.notice=e.message}state.searching=false;render()}

boot();

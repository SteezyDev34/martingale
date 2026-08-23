const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');

chrome.runtime.sendMessage({ action: 'get_ws_status' }, (res) => {
  const connected = res?.connected || false;
  statusEl.textContent = connected ? '🟢 Python connecté' : '⚫ Python déconnecté';
  statusEl.className = connected ? 'connected' : 'disconnected';
});

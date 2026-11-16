const $ = (s) => document.getElementById(s);

async function getCurrentHost() {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (!tab?.url) return null;
  try { return new URL(tab.url).hostname.replace(/^www\./, ''); } catch { return null; }
}

async function getBlockedSites() {
  const r = await chrome.storage.local.get({blockedSites: []});
  return r.blockedSites;
}

async function setBlockedSites(sites) {
  await chrome.storage.local.set({blockedSites: sites});
}

function renderToggle(host, isBlocked, onChange) {
  const label = document.createElement('label');
  label.className = 'toggle';
  label.title = isBlocked ? 'Blocked (original restrictions)' : 'Allowed (unblocked)';
  const input = document.createElement('input');
  input.type = 'checkbox';
  input.checked = !isBlocked;
  input.addEventListener('change', () => onChange(!input.checked));
  const slider = document.createElement('span');
  slider.className = 'slider';
  label.append(input, slider);
  return label;
}

async function render() {
  const host = await getCurrentHost();
  const blocked = await getBlockedSites();
  const isBlocked = host && blocked.includes(host);

  const current = $('current-site');
  if (host) {
    current.innerHTML = `
      <div class="current-label">Current site</div>
      <div class="current-host">${host}</div>
      <span class="status ${isBlocked ? 'blocked' : 'allowed'}">
        ${isBlocked ? 'Blocked' : 'Allowed'}
      </span>
    `;
    const toggle = renderToggle(host, isBlocked, async (block) => {
      const sites = await getBlockedSites();
      const set = new Set(sites);
      block ? set.add(host) : set.delete(host);
      await setBlockedSites([...set].sort());
      render();
    });
    current.querySelector('.current-host').after(toggle);
    current.querySelector('.current-host').style.display = 'inline';
    current.style.display = 'flex';
    current.style.alignItems = 'center';
    current.style.justifyContent = 'space-between';
    current.style.flexWrap = 'wrap';
  } else {
    current.innerHTML = '<div class="current-label">No active site</div>';
  }

  const list = $('blocked-list');
  list.innerHTML = '';
  if (blocked.length === 0) {
    list.innerHTML = '<div class="empty">No sites blocked. All sites are allowed.</div>';
    return;
  }
  for (const site of blocked.sort()) {
    const row = document.createElement('div');
    row.className = 'site-row';
    const name = document.createElement('span');
    name.className = 'site-name';
    name.textContent = site;
    const btn = document.createElement('button');
    btn.className = 'remove-btn';
    btn.title = 'Unblock';
    btn.textContent = '✕';
    btn.addEventListener('click', async () => {
      const sites = await getBlockedSites();
      await setBlockedSites(sites.filter(s => s !== site));
      render();
    });
    row.append(name, btn);
    list.append(row);
  }
}

$('open-panel').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (tab) chrome.sidePanel.open({tabId: tab.id});
  window.close();
});

render();

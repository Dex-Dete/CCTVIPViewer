// Hikvision DVR Viewer

let scanning = false;
let currentDvr = null;
let refreshTimers = [];

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btnScan').addEventListener('click', scanDvrs);
    document.getElementById('connectBtn').addEventListener('click', connectDvr);
    document.getElementById('dvrIpInput').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') connectDvr();
    });
    loadSavedDvrs();
});

async function loadSavedDvrs() {
    try {
        const response = await fetch('/api/dvrs', { cache: 'no-cache' });
        if (!response.ok) throw new Error('Server returned ' + response.status);
        renderDvrList(await response.json(), 'Saved DVRs');
    } catch (error) {
        setStatus('Start the local server with start.bat or python scripts/server.py.');
        console.error(error);
    }
}

async function scanDvrs() {
    if (scanning) return;
    scanning = true;
    setScanControls(true);
    setStatus('Scanning for Hikvision DVR/NVR devices...');
    setProgress(35);

    try {
        const response = await fetch('/api/scan', { cache: 'no-cache' });
        if (!response.ok) throw new Error('Scan failed with status ' + response.status);
        const dvrs = await response.json();
        setProgress(100);
        setStatus(dvrs.length ? 'Found ' + dvrs.length + ' Hikvision DVR/NVR device(s).' : 'No Hikvision DVR found. Type the DVR IP manually.');
        renderDvrList(dvrs, 'Detected DVRs');
    } catch (error) {
        setStatus('Scan failed: ' + error.message);
        console.error(error);
    } finally {
        scanning = false;
        setScanControls(false);
    }
}

async function connectDvr() {
    const payload = {
        ip: document.getElementById('dvrIpInput').value.trim(),
        port: document.getElementById('dvrPortInput').value || '80',
        username: document.getElementById('usernameInput').value.trim() || 'admin',
        password: document.getElementById('passwordInput').value
    };

    if (!isValidIp(payload.ip)) {
        alert('Please enter a valid DVR IP address, for example 192.168.1.4');
        return;
    }

    setStatus('Connecting to DVR ' + payload.ip + '...');
    document.getElementById('connectBtn').disabled = true;

    try {
        const response = await fetch('/api/dvr/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Login failed');

        currentDvr = result.dvr;
        renderChannels(result.channels || []);
        setStatus('Connected to ' + (currentDvr.device_name || currentDvr.ip) + '.');
    } catch (error) {
        setStatus('DVR connection failed: ' + error.message);
        console.error(error);
    } finally {
        document.getElementById('connectBtn').disabled = false;
    }
}

function renderDvrList(dvrs, title) {
    const container = document.getElementById('dvrList');
    if (!dvrs.length) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = `<h3>${escapeHtml(title)}</h3>`;
    dvrs.forEach((dvr) => {
        const button = document.createElement('button');
        button.className = 'dvr-chip';
        button.type = 'button';
        button.innerHTML = `
            <strong>${escapeHtml(dvr.ip)}:${escapeHtml(dvr.port || '80')}</strong>
            <span>${escapeHtml(dvr.device_name || dvr.model || 'Hikvision DVR/NVR')}</span>
        `;
        button.addEventListener('click', () => {
            document.getElementById('dvrIpInput').value = dvr.ip;
            document.getElementById('dvrPortInput').value = dvr.port || '80';
            setStatus('Selected DVR ' + dvr.ip + '. Enter password if the default does not work.');
        });
        container.appendChild(button);
    });
}

function renderChannels(channels) {
    clearRefreshTimers();
    const grid = document.getElementById('channelsGrid');
    const title = document.getElementById('dvrTitle');
    title.textContent = currentDvr.device_name ? currentDvr.device_name + ' Channels' : 'DVR Channels';
    grid.innerHTML = '';

    if (!channels.length) {
        grid.innerHTML = '<div class="no-cameras">Connected, but no channels were returned by the DVR.</div>';
        return;
    }

    channels.forEach((channel, index) => {
        const card = document.createElement('article');
        card.className = 'camera-card';
        const imageUrl = '/api/dvr/snapshot?ip=' + encodeURIComponent(currentDvr.ip) + '&channel=' + encodeURIComponent(channel.id);
        card.innerHTML = `
            <div class="camera-header">
                <span>${escapeHtml(channel.name || 'Camera ' + (index + 1))}</span>
                <span>CH ${escapeHtml(channel.id)}</span>
            </div>
            <div class="camera-container">
                <img class="camera-frame" id="channel${index}" alt="${escapeHtml(channel.name || 'Camera')}" src="">
                <div class="camera-status" id="status${index}">Loading</div>
            </div>
            <div class="controls">
                <span class="camera-url">${escapeHtml(currentDvr.ip)} / ${escapeHtml(channel.id)}</span>
                <button class="link-button" type="button" data-index="${index}">Refresh</button>
            </div>
        `;
        grid.appendChild(card);
        startChannelRefresh(index, imageUrl);
    });

    grid.querySelectorAll('.link-button').forEach((button) => {
        button.addEventListener('click', () => refreshChannel(Number(button.dataset.index)));
    });
}

function startChannelRefresh(index, imageUrl) {
    const image = document.getElementById('channel' + index);
    const status = document.getElementById('status' + index);

    image.dataset.baseUrl = imageUrl;
    image.addEventListener('load', () => {
        status.textContent = 'Live';
    });
    image.addEventListener('error', () => {
        status.textContent = 'No snapshot';
    });

    refreshChannel(index);
    refreshTimers.push(window.setInterval(() => refreshChannel(index), 2000));
}

function refreshChannel(index) {
    const image = document.getElementById('channel' + index);
    const status = document.getElementById('status' + index);
    if (!image) return;
    status.textContent = 'Refreshing';
    image.src = image.dataset.baseUrl + '&t=' + Date.now();
}

function setStatus(text) {
    document.getElementById('status').textContent = text;
}

function setProgress(percent) {
    document.getElementById('progressBar').style.width = percent + '%';
}

function setScanControls(active) {
    const scanBtn = document.getElementById('btnScan');
    const progress = document.querySelector('.progress-bar');
    scanBtn.disabled = active;
    scanBtn.textContent = active ? 'Scanning...' : 'Scan Hikvision DVRs';
    progress.style.display = active ? 'block' : 'none';
    if (!active) window.setTimeout(() => setProgress(0), 800);
}

function clearRefreshTimers() {
    refreshTimers.forEach((timer) => window.clearInterval(timer));
    refreshTimers = [];
}

function isValidIp(value) {
    const parts = value.split('.');
    if (parts.length !== 4) return false;
    return parts.every((part) => {
        if (!/^\d+$/.test(part)) return false;
        const number = Number(part);
        return number >= 0 && number <= 255;
    });
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[char]));
}

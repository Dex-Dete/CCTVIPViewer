const IP_RANGE_START = 1;
const IP_RANGE_END = 255;
const LOCAL_NETWORK_PREFIX = '';

let scanning = false;
let cameras = [];
let streamIntervals = {};

document.getElementById('btnScan').addEventListener('click', initScan);

async function initScan() {
    const btn = document.getElementById('btnScan');
    const progressBar = document.getElementById('progressBar');
    const status = document.querySelector('.status-idle');
    const camerasSection = document.getElementById('camerasSection');
    const camerasGrid = document.getElementById('camerasGrid');

    scanning = true;
    btn.disabled = true;
    btn.textContent = 'Scanning...';
    progressBar.style.display = 'block';
    status.textContent = 'Scanning local network...';
    camerasGrid.innerHTML = '';

    cameras = [];
    Object.values(streamIntervals).forEach(clearInterval);
    streamIntervals = {};

    // Get local network prefix (assume 192.168.1.x, will adapt)
    const netInfo = await getLocalNetworkInfo();
    LOCAL_NETWORK_PREFIX = netInfo.prefix;

    // Show scanning progress
    for (let i = 1; i <= IP_RANGE_END; i++) {
        if (!scanning) break;
        const ip = `${LOCAL_NETWORK_PREFIX}${i}`;
        await checkCamera(ip);
        progressBar.style.width = `${(i / IP_RANGE_END) * 100}%`;
    }

    scanning = false;
    btn.disabled = false;
    btn.textContent = 'Scan Network';

    if (cameras.length === 0) {
        status.textContent = 'No cameras found. Enter IP manually:';
        camerasSection.style.display = 'none';
        return;
    }

    status.textContent = `Found ${cameras.length} camera(s)`;
    camerasSection.style.display = 'block';

    renderCameras(camerasGrid);
}

async function getLocalNetworkInfo() {
    // Try to determine local network prefix
    // First try using a simple approach - get the first non-loopback IP
    let prefix = '192.168.1'; // Default assumption
    
    try {
        // Use fetch to get network info via a simple approach
        // We'll assume 192.168.1.x but detect the actual prefix
        const response = await fetch('https://ifconfig.me/json', { 
            method: 'GET', 
            timeout: 3000 
        });
        if (response.ok) {
            const data = await response.json();
            const ip = data.ip;
            if (ip && ip.startsWith('192.168.')) {
                const parts = ip.split('.');
                return { prefix: `${parts[0]}.${parts[1]}.${parts[2]}` };
            }
        }
    } catch (e) {
        // Fall back to default
    }
    
    return { prefix: '192.168.1' };
}

async function checkCamera(ip) {
    try {
        // Quick port 80/8080/554 check for camera HTTP/RTP
        const httpResponses = await Promise.race([
            fetch(`http://${ip}/`, { method: 'GET', timeout: 500, mode: 'no-cors' }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 500))
        ]);
        
        // If we get here without timeout, camera might be there
        // But let's also try a simple GET to common camera paths
        try {
            await fetch(`http://${ip}:8080/video`, { method: 'GET', timeout: 300, mode: 'no-cors' });
        } catch (e) {
            // Ignore - camera might not respond to this
        }
        
        // Try common camera URLs
        const urls = [
            `http://${ip}:80/stream`,
            `http://${ip}:80/mjpeg/1`, 
            `http://${ip}:80/video`,
            `http://${ip}:8080/stream`,
            `http://${ip}:8080/mjpg`,
            `http://${ip}:554/stream`
        ];
        
        for (const url of urls) {
            if (!scanning) break;
            try {
                const resp = await fetch(url, { method: 'GET', timeout: 300, mode: 'no-cors' });
                // Even if it fails, if we get a response, consider it a camera
                cameras.push({ ip, url, name: `Camera ${cameras.length + 1}` });
                break;
            } catch (e) {
                // Continue to next URL
            }
        }
    } catch (e) {
        // Camera not responding - skip
    }
}

function renderCameras(grid) {
    if (cameras.length === 0) {
        grid.innerHTML = '<div class="no-cameras">No cameras detected</div>';
        return;
    }

    grid.innerHTML = '';

    cameras.forEach((cam, index) => {
        const card = document.createElement('div');
        card.className = 'camera-card';
        card.innerHTML = `
            <div class="camera-header">${cam.name}</div>
            <div class="camera-container">
                <video class="camera-feed" id="video${index}" autoplay playsinline></video>
                <div class="camera-status" id="status${index}">Connecting...</div>
            </div>
            <div class="controls">
                <span class="camera-name">${cam.name}</span>
                <span class="stream-status" id="streamStatus${index}">Offline</span>
            </div>
        `;
        grid.appendChild(card);

        // Start streaming
        startCameraStream(index, cam.url);
    });
}

function startCameraStream(index, url) {
    const video = document.getElementById(`video${index}`);
    const statusDiv = document.getElementById(`status${index}`);
    const streamStatus = document.getElementById(`streamStatus${index}`);
    
    // Stop any existing interval for this camera
    if (streamIntervals[index]) {
        clearInterval(streamIntervals[index]);
    }
    
    // Create new video stream
    const videoSrc = new URL(url);
    video.src = url + '?t=' + Date.now();
    
    video.oncanplaythrough = () => {
        statusDiv.textContent = 'Live';
        streamStatus.textContent = 'Online';
        video.play();
        
        // Start keep-alive interval - refresh every 3 minutes to prevent disconnect
        streamIntervals[index] = setInterval(() => {
            video.src = url + '?t=' + Date.now();
        }, 180000); // 3 minutes
    };
    
    video.onerror = () => {
        statusDiv.textContent = 'Error';
        streamStatus.textContent = 'Offline';
    };
    
    video.onabort = () => {
        // Stream was aborted, try to reconnect
        video.src = url + '?t=' + Date.now();
        video.play();
    };
}

// Auto-reconnect handling - keep streams alive
setInterval(() => {
    cameras.forEach((cam, index) => {
        const video = document.getElementById(`video${index}`);
        if (video && video.readyState < 2) {
            video.src = cam.url + '?t=' + Date.now();
            video.play();
        }
    });
}, 15000); // Check every 15 seconds
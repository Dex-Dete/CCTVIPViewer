// CCTV IP Viewer - Simple Sequential Scan & Manual IP
// Scans 192.168.1.1 through 192.168.1.255

let scanning = false;
let cameras = [];
let streamIntervals = {};
let scannedIps = [];

document.addEventListener('DOMContentLoaded', function() {
    const scanBtn = document.getElementById('btnScan');
    const progressBar = document.getElementById('progressBar');
    const statusDiv = document.getElementById('status');
    const camerasSection = document.getElementById('camerasSection');
    const camerasGrid = document.getElementById('camerasGrid');
    const manualSection = document.getElementById('manualSection');
    const manualIpInput = document.getElementById('manualIpInput');
    const addManualBtn = document.getElementById('addManualBtn');

    if (!scanBtn) return;

    scanBtn.addEventListener('click', startScan);
    if (addManualBtn) addManualBtn.addEventListener('click', addManualCamera);

    // Show manual section after 20s if no cameras found
    setTimeout(function() {
        if (isScanning && cameras.length === 0) {
            statusDiv.textContent = 'No cameras detected scanning automatically';
            manualSection.style.display = 'block';
            scanBtn.style.display = 'none';
        }
    }, 20000);

    function startScan() {
        if (scanning) return;
        scanning = true;
        scanBtn.disabled = true;
        scanBtn.textContent = 'Scanning...';
        progressBar.style.display = 'block';
        statusDiv.textContent = 'Scanning network...';
        camerasGrid.innerHTML = '';
        cameras = [];
        Object.values(streamIntervals).forEach(c => clearInterval(c));
        streamIntervals = {};
        scannedIps = [];

        scanIP(1);
    }

    function scanIP(ipNum) {
        if (ipNum > 255) {
            // Scan complete
            scanning = false;
            scanBtn.disabled = false;
            scanBtn.textContent = 'Scan Network';
            statusDiv.textContent = 'Scan complete - found ' + cameras.length + ' camera(s)';
            camerasSection.style.display = 'block';
            return;
        }

        const ip = '192.168.1.' + ipNum;
        scannedIps.push(ip);
        progressBar.style.width = ((ipNum / 255) * 100) + '%';
        statusDiv.textContent = 'Checking ' + ip + '...';

        // Quick check this IP
        checkIP(ip, ipNum);
    }

    function checkIP(ip, ipNum) {
        // Try common camera URLs
        const testUrls = [
            'http://' + ip + '/',
            'http://' + ip + ':8080/',
            'http://' + ip + ':80/',
            'http://' + ip + '/video',
            'http://' + ip + ':8080/video'
        ];

        let urlIndex = 0;
        function tryNextUrl() {
            if (urlIndex >= testUrls.length) {
                // Done with this IP, move to next
                setTimeout(function() { scanIP(ipNum + 1); }, 30);
                return;
            }

            const url = testUrls[urlIndex];
            urlIndex++;

            // Quick fetch with 300ms timeout
            fetch(url, { method: 'GET', mode: 'no-cors', cache: 'no-cache', signal: AbortSignal.timeout(300) })
                .then(function(resp) {
                    // Even 404 means server is responding, could be camera
                    if (resp.status === 404 || resp.ok) {
                        // Found potential camera
                        const cameraName = 'Camera ' + (cameras.length + 1) + ' (' + ip + ')';
                        cameras.push({
                            ip: ip,
                            url: url,
                            name: cameraName
                        });

                        // Start streaming immediately
                        startStream(cameras.length - 1, url);

                        // Show in UI
                        addCameraToUI(cameras.length - 1);
                    }

                    // Continue to next URL or next IP
                    setTimeout(tryNextUrl, 100);
                })
                .catch(function(e) {
                    // Timeout/error, try next URL
                    setTimeout(tryNextUrl, 100);
                });
        }

        tryNextUrl();
    }

    function startStream(index, url) {
        const video = document.getElementById('video' + index);
        const statusDiv = document.getElementById('status' + index);

        if (streamIntervals[index]) {
            clearInterval(streamIntervals[index]);
        }

        video.src = url + '?rand=' + Date.now();

        video.oncanplaythrough = function() {
            statusDiv.textContent = 'Live';
            video.play();

            // Keep-alive every 3 minutes to prevent disconnection
            streamIntervals[index] = setInterval(function() {
                video.src = url + '?rand=' + Date.now();
            }, 180000);
        };

        video.onerror = function() {
            statusDiv.textContent = 'Connecting...';
        };

        video.onabort = function() {
            video.src = url + '?rand=' + Date.now();
            video.play();
        };
    }

    function addCameraToUI(index) {
        const cam = cameras[index];
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
                <span class="stream-status">Offline</span>
            </div>
        `;
        camerasGrid.appendChild(card);

        // Start stream
        setTimeout(function() {
            startStream(index, cam.url);
        }, 200);
    }

    // Add manual camera
    function addManualCamera() {
        const ip = manualIpInput.value.trim();

        if (ip && ip.match(/^192\.168\.\d+$/)) {
            const url = 'http://' + ip + '/';
            const cameraName = 'Manual Camera ' + (cameras.length + 1);

            cameras.push({
                ip: ip,
                url: url,
                name: cameraName
            });

            startStream(cameras.length - 1, url);
            addCameraToUI(cameras.length - 1);

            manualIpInput.value = '';
            manualSection.style.display = 'none';
            scanBtn.style.display = 'inline-block';

            statusDiv.textContent = 'Added manual camera: ' + ip;
        } else {
            alert('Please enter valid IP: 192.168.1.xxx');
        }
    }
});
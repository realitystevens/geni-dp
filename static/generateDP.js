export const designImg = document.getElementById('__design-image');
export const errorMessage = document.getElementById('error-message');
const userImage = document.getElementById('user-image');
const loadingSpinner = document.querySelector('.loading-spinner');

const wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/generate';
let ws;

function connectWebSocket() {
    ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    ws.onmessage = function(event) {
        const arrayBuffer = event.data;
        const blob = new Blob([arrayBuffer], { type: 'image/png' });
        const url = URL.createObjectURL(blob);
        
        designImg.src = url;
        loadingSpinner.style.display = 'none';
        window.designImageEdited = true;
    };
    ws.onclose = function() {
        console.log('WebSocket connection closed. Reconnecting...');

        if (typeof wsReconnectAttempts === 'undefined') {
            window.wsReconnectAttempts = 1;
        } else {
            window.wsReconnectAttempts++;
        }

        if (window.wsReconnectAttempts <= 3) {
            setTimeout(connectWebSocket, 1000);
        } else {
            console.error("WebSocket connection failed after 3 attempts. Please check the server or reload the page.");
            errorMessage.textContent = 'WebSocket connection failed. Please check the server or reload the page.';
            errorMessage.style.display = 'block';
            loadingSpinner.style.display = 'none';
            window.wsReconnectAttempts = undefined; // Reset attempts after failure
        }
    };
}

connectWebSocket();

userImage.addEventListener('change', function(e) {
    loadingSpinner.style.display = 'block';
    errorMessage.style.display = 'none';
    if (!userImage.files || !userImage.files[0]) {
        errorMessage.textContent = 'Please select an image file (PNG or JPEG).';
        errorMessage.style.display = 'block';
        loadingSpinner.style.display = 'none';
        return;
    }
    const file = userImage.files[0];
    const reader = new FileReader();
    reader.onload = function(evt) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(evt.target.result);
        } else {
            errorMessage.textContent = 'WebSocket not connected. Please refresh the page.';
            errorMessage.style.display = 'block';
            loadingSpinner.style.display = 'none';
        }
    };
    reader.readAsArrayBuffer(file);
    reader.onerror = function() {
        errorMessage.textContent = 'Error reading file. Please try again.';
        errorMessage.style.display = 'block';
        loadingSpinner.style.display = 'none';
    };
});

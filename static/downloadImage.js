import { designImg, errorMessage } from './generateDP.js';
const downloadBtn = document.getElementById('download-btn');


downloadBtn.addEventListener('click', function(e) {
    e.preventDefault();

    if (window.designImageEdited) {
        const link = document.createElement('a');
        link.href = designImg.src;
        link.download = 'geni-dp.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        errorMessage.textContent = 'No DP available to download yet. Upload an image first.';
        errorMessage.style.display = 'block';
    }
});
document.addEventListener("DOMContentLoaded", () => {
    
    // --- DASHBOARD: ELEMENTS ---
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileStatus = document.getElementById("file-status");
    const fileNameDisplay = document.getElementById("filename");
    const removeBtn = document.getElementById("remove-file");
    const form = document.getElementById("upload-form");
    const loader = document.getElementById("loader-overlay");
    const loadingText = document.getElementById("loading-text");

    // --- DASHBOARD: SCROLL REVEAL ---
    if (typeof ScrollReveal !== 'undefined') {
        ScrollReveal().reveal('.hero-text', { distance: '50px', origin: 'bottom', duration: 1000 });
        ScrollReveal().reveal('.bento-card', { interval: 150, scale: 0.9, delay: 300 });
    }

    // --- DASHBOARD: RADAR ANIMATION ---
    const radar = document.getElementById("radar-area");
    if (radar) {
        setInterval(() => {
            const dot = document.createElement("div");
            dot.classList.add("radar-dot");
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * 45; 
            const x = 50 + radius * Math.cos(angle); 
            const y = 50 + radius * Math.sin(angle);
            dot.style.left = x + "%";
            dot.style.top = y + "%";
            radar.appendChild(dot);
            setTimeout(() => dot.remove(), 2500);
        }, 800);
    }

    // --- DASHBOARD: DRAG & DROP ---
    if (dropZone) {
        dropZone.addEventListener("click", () => fileInput.click());
        dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
        dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("drag-over"); });
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            if(e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", () => { if(fileInput.files.length) handleFile(fileInput.files[0]); });
    }

    function handleFile(file) {
        fileNameDisplay.innerText = file.name;
        dropZone.style.display = 'none'; 
        fileStatus.classList.remove("hidden");
        fileStatus.style.display = "flex";
        if (fileInput.files[0] !== file) {
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
        }
    }

    if (removeBtn) {
        removeBtn.addEventListener("click", (e) => {
            e.stopPropagation(); 
            fileInput.value = ""; 
            fileStatus.classList.add("hidden");
            fileStatus.style.display = "none";
            dropZone.style.display = 'block'; 
            dropZone.classList.remove("drag-over");
        });
    }

    // --- FIX: SUBMIT WITH DELAY (AI THINKING) ---
   if (form) {
        form.addEventListener("submit", (e) => {
            // Prevent default submission to show animation first
            e.preventDefault(); 
            
            if(fileInput.files.length === 0) {
                alert("⚠️ Please upload a document first.");
                return;
            }
            
            loader.classList.add("active");
            
            const steps = [
                "Tokenizing Input Text...", 
                "Engaging Transformer Model...", 
                "Vectorizing Document Math...", 
                "Querying Knowledge Base...", 
                "Calculating Cosine Similarities...", 
                "Generating PDF Report..."
            ];
            
            let i = 0;
            let progress = 5;
            loadingText.innerText = steps[0];
            const progBar = document.getElementById('progress-bar');
            progBar.style.width = progress + '%';
            
            const intervalId = setInterval(() => {
                i++;
                if (i < steps.length) { 
                    loadingText.innerText = steps[i]; 
                }
                
                // Increment progress bar up to 95% (holds there until server replies)
                progress += 18;
                if(progress > 95) progress = 95;
                progBar.style.width = progress + '%';
                
            }, 800);

            // Give the animation 4 seconds, then actually submit the file to Python
            setTimeout(() => {
                clearInterval(intervalId);
                progBar.style.width = '100%';
                form.submit(); 
            }, 4000);
        });
    }

    // --- REPORT PAGE: ANIMATION & COLORING ---
    const circle = document.querySelector('.score-path');
    const resultText = document.getElementById('result-text');
    const wrapper = document.querySelector('.score-circle-wrapper');

    if (circle && wrapper) {
        const score = parseInt(wrapper.getAttribute('data-score'));
        const radius = circle.r.baseVal.value;
        const circumference = radius * 2 * Math.PI;
        const offset = circumference - (score / 100) * circumference;
        
        // 1. Set Color based on Score (Red if > 50, Green if <= 50)
        const color = score > 50 ? '#ef4444' : '#10b981';
        circle.style.stroke = color;
        if(resultText) resultText.style.color = color;
        
        // 2. Animate Circle
        setTimeout(() => { circle.style.strokeDashoffset = offset; }, 300);
    }

    // --- SIGNUP: PASSWORD STRENGTH ---
    const passInput = document.getElementById('password');
    const strengthFill = document.getElementById('strength-fill');
    if (passInput && strengthFill) {
        passInput.addEventListener('input', (e) => {
            const val = e.target.value;
            let strength = 0;
            if(val.length > 5) strength += 30;
            if(val.match(/[0-9]/)) strength += 30;
            if(val.match(/[^a-zA-Z0-9]/)) strength += 40;
            
            strengthFill.style.width = strength + '%';
            if(strength < 40) strengthFill.style.background = '#ef4444';
            else if(strength < 80) strengthFill.style.background = '#f59e0b';
            else strengthFill.style.background = '#10b981';
        });
    }
    // --- LIVE STATS COUNTER ANIMATION ---
    const counters = document.querySelectorAll('.stat-num');
    const speed = 200; // The lower the slower

    counters.forEach(counter => {
        const updateCount = () => {
            const target = +counter.getAttribute('data-target');
            const count = +counter.innerText;
            
            // Calculate increment step
            const inc = target / speed;

            if (count < target) {
                // If it's a decimal (like 98.7), keep 1 decimal place. Otherwise round up.
                if(target % 1 !== 0) {
                    counter.innerText = (count + inc).toFixed(1);
                } else {
                    counter.innerText = Math.ceil(count + inc);
                }
                setTimeout(updateCount, 15);
            } else {
                counter.innerText = target;
            }
        };
        updateCount();
    });
});
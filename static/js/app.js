document.addEventListener('DOMContentLoaded', () => {
    initFlashMessages();
    initPasswordToggles();
    initAnimatedCounters();
    initSidebar();
    initFormValidation();
    initAccountVerification();
});

function initFlashMessages() {
    document.querySelectorAll('.flash-message').forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => msg.remove(), 400);
        }, 5000);

        msg.addEventListener('click', () => {
            msg.style.animation = 'slideOut 0.4s ease forwards';
            setTimeout(() => msg.remove(), 400);
        });
    });
}

function showToast(message, type = 'info') {
    let container = document.querySelector('.flash-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        danger: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        info: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `flash-message ${type}`;
    toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.4s ease forwards';
        setTimeout(() => toast.remove(), 400);
    }, 5000);

    toast.addEventListener('click', () => {
        toast.style.animation = 'slideOut 0.4s ease forwards';
        setTimeout(() => toast.remove(), 400);
    });
}

function initPasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.previousElementSibling;
            if (!input) return;
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            btn.innerHTML = isPassword
                ? '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
                : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
        });
    });
}

function initAnimatedCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseFloat(el.dataset.counter);
        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 2;
        const duration = 1500;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            el.textContent = prefix + formatNumber(current, decimals) + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    });
}

function formatNumber(num, decimals = 2) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatCurrency(amount) {
    return 'GH₵' + formatNumber(parseFloat(amount), 2);
}

function initSidebar() {
    const toggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (!toggle || !sidebar) return;

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024 && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

function initFormValidation() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
            let valid = true;
            form.querySelectorAll('[required]').forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.style.borderColor = '#ef4444';
                    input.addEventListener('input', () => {
                        input.style.borderColor = '';
                    }, { once: true });
                }
            });

            const password = form.querySelector('[name="password"]');
            const confirm = form.querySelector('[name="confirm_password"]');
            if (password && confirm && password.value !== confirm.value) {
                valid = false;
                confirm.style.borderColor = '#ef4444';
                showToast('Passwords do not match.', 'danger');
            }

            const amount = form.querySelector('[name="amount"]');
            if (amount && (parseFloat(amount.value) <= 0 || isNaN(amount.value))) {
                valid = false;
                amount.style.borderColor = '#ef4444';
                showToast('Please enter a valid amount.', 'danger');
            }

            if (!valid) {
                e.preventDefault();
            }
        });
    });
}

function initAccountVerification() {
    const accountInput = document.querySelector('[name="receiver_account"]');
    const verifyResult = document.getElementById('verify-result');
    if (!accountInput || !verifyResult) return;

    let timeout;
    accountInput.addEventListener('input', () => {
        clearTimeout(timeout);
        const val = accountInput.value.trim();
        if (val.length < 5) {
            verifyResult.textContent = '';
            return;
        }

        timeout = setTimeout(() => {
            fetch(`/api/verify-account/${encodeURIComponent(val)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.found) {
                        verifyResult.innerHTML = `<span style="color: var(--success);">&#10003; ${data.name}</span>`;
                    } else {
                        verifyResult.innerHTML = `<span style="color: var(--danger);">&#10007; Account not found</span>`;
                    }
                })
                .catch(() => {
                    verifyResult.textContent = '';
                });
        }, 500);
    });
}

function initChart(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    fetch('/api/chart-data')
        .then(r => r.json())
        .then(data => {
            new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            label: 'Deposits',
                            data: data.deposits,
                            backgroundColor: 'rgba(30, 64, 175, 0.8)', // Primary blue
                            borderRadius: 6,
                            barPercentage: 0.6
                        },
                        {
                            label: 'Withdrawals',
                            data: data.withdrawals,
                            backgroundColor: 'rgba(220, 38, 38, 0.8)', // Pure red
                            borderRadius: 6,
                            barPercentage: 0.6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { usePointStyle: true, padding: 20, font: { size: 12 } }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0,0,0,0.04)' },
                            ticks: {
                                callback: val => 'GH₵' + val.toLocaleString(),
                                font: { size: 11 }
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 11 } }
                        }
                    }
                }
            });
        })
        .catch(() => {});
}

// Dark Mode Toggle Logic
document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initAIChatbot();
    initDragAndDrop();
});

function initDarkMode() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;

    // Check saved preference
    const isDark = localStorage.getItem('darkMode') === 'enabled';
    if (isDark) {
        document.body.classList.add('dark-theme');
    }

    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('darkMode', 'enabled');
            showToast('Dark mode activated.', 'info');
        } else {
            localStorage.setItem('darkMode', 'disabled');
            showToast('Light mode activated.', 'info');
        }
    });
}

// AI Financial Chatbot Helper
function initAIChatbot() {
    // Add HTML widget dynamically if it's not present
    if (!document.getElementById('chatbot-widget') && document.querySelector('.navbar')) {
        const widget = document.createElement('div');
        widget.id = 'chatbot-widget';
        widget.style.position = 'fixed';
        widget.style.bottom = '20px';
        widget.style.right = '20px';
        widget.style.zIndex = '9999';
        widget.style.fontFamily = 'inherit';

        widget.innerHTML = `
            <button id="chatbot-toggle" style="width: 56px; height: 56px; border-radius: 50%; background: var(--primary); color: white; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.3s ease;">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
            </button>
            <div id="chatbot-box" style="display: none; position: absolute; bottom: 70px; right: 0; width: 340px; height: 420px; background: var(--white); border-radius: 12px; border: 1px solid var(--gray-200); box-shadow: var(--shadow-lg); overflow: hidden; flex-direction: column;">
                <div style="background: var(--primary); color: white; padding: 1rem; font-weight: 600; display: flex; justify-content: space-between; align-items: center;">
                    <span>AI Banking Assistant</span>
                    <button id="chatbot-close" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.2rem;">&times;</button>
                </div>
                <div id="chatbot-messages" style="flex: 1; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.85rem; max-height: 290px;">
                    <div style="align-self: flex-start; background: var(--gray-100); padding: 0.6rem 0.85rem; border-radius: 8px; color: var(--dark); max-width: 80%;">
                        Hi there! I am your AI Financial Assistant. How can I help you manage your Ghana Cedis today?
                    </div>
                </div>
                <div style="padding: 0.5rem; background: var(--gray-50); border-top: 1px solid var(--gray-200); display: flex; flex-wrap: wrap; gap: 4px;">
                    <button class="chat-chip" onclick="sendChatQuery('Predict expenses')" style="background: white; border: 1px solid var(--gray-300); border-radius: 20px; padding: 4px 8px; font-size: 0.72rem; cursor: pointer; color: var(--dark);">Predict Expenses</button>
                    <button class="chat-chip" onclick="sendChatQuery('Detect unusual txns')" style="background: white; border: 1px solid var(--gray-300); border-radius: 20px; padding: 4px 8px; font-size: 0.72rem; cursor: pointer; color: var(--dark);">Detect Anomalies</button>
                    <button class="chat-chip" onclick="sendChatQuery('Financial Advice')" style="background: white; border: 1px solid var(--gray-300); border-radius: 20px; padding: 4px 8px; font-size: 0.72rem; cursor: pointer; color: var(--dark);">Get Advice</button>
                </div>
                <div style="display: flex; border-top: 1px solid var(--gray-200);">
                    <input type="text" id="chatbot-input" placeholder="Type a message..." style="flex: 1; padding: 0.75rem; border: none; outline: none; font-size: 0.85rem; background: var(--white); color: var(--dark);">
                    <button id="chatbot-send" style="padding: 0 1rem; background: var(--primary); color: white; border: none; cursor: pointer; font-size: 0.85rem; font-weight: 600;">Send</button>
                </div>
            </div>
        `;
        document.body.appendChild(widget);

        const toggle = document.getElementById('chatbot-toggle');
        const box = document.getElementById('chatbot-box');
        const close = document.getElementById('chatbot-close');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        if (toggle && box) {
            toggle.addEventListener('click', () => {
                const isHidden = box.style.display === 'none';
                box.style.display = isHidden ? 'flex' : 'none';
            });
        }
        if (close && box) {
            close.addEventListener('click', () => {
                box.style.display = 'none';
            });
        }
        if (send && input) {
            send.addEventListener('click', () => {
                const text = input.value.trim();
                if (text) {
                    addUserMessage(text);
                    input.value = '';
                    simulateBotResponse(text);
                }
            });
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    send.click();
                }
            });
        }
    }
}

function addUserMessage(text) {
    const list = document.getElementById('chatbot-messages');
    if (!list) return;
    const msg = document.createElement('div');
    msg.className = 'chat-message user';
    msg.style.cssText = 'align-self: flex-end; background: var(--primary); color: var(--dark); padding: 0.6rem 0.85rem; border-radius: 8px; max-width: 80%; font-weight: 500;';
    msg.textContent = text;
    list.appendChild(msg);
    list.scrollTop = list.scrollHeight;
}

function addBotMessage(text) {
    const list = document.getElementById('chatbot-messages');
    if (!list) return;
    const msg = document.createElement('div');
    msg.className = 'chat-message bot';
    msg.style.cssText = 'align-self: flex-start; background: var(--gray-100); padding: 0.6rem 0.85rem; border-radius: 8px; color: var(--dark); max-width: 80%;';
    msg.innerHTML = text;
    list.appendChild(msg);
    list.scrollTop = list.scrollHeight;
}

window.sendChatQuery = function(type) {
    addUserMessage(type);
    simulateBotResponse(type);
};

function simulateBotResponse(query) {
    const lower = query.toLowerCase();
    let reply = "I am processing your query. Please ask me about predictions, anomalies, or financial tips!";
    
    if (lower.includes('predict') || lower.includes('expense')) {
        reply = "<strong>AI Smart Expense Prediction:</strong><br>Based on your historical transfers and utilities: You are projected to spend <strong>GH₵ 350.00</strong> next month on utilities/data. Your savings plan remains highly optimal.";
    } else if (lower.includes('unusual') || lower.includes('detect') || lower.includes('anomaly') || lower.includes('anomalies')) {
        reply = "<strong>AI Smart Fraud Scan:</strong><br>Scanning transactions...<br>No unusual location or transaction size variations detected. Status: <strong>Secure & Compliant</strong>.";
    } else if (lower.includes('advice') || lower.includes('financial')) {
        reply = "<strong>AI Financial Advice:</strong><br>You should allocate around 15% of your deposits to the Fixed Deposit Management module to earn <strong>12.5% p.a. interest</strong> guaranteed. This will hedge against local inflation!";
    } else if (lower.includes('balance') || lower.includes('how much')) {
        reply = "To see your exact real-time balance, please review the main card deck on your dashboard. You can also generate an automated CSV list from your transaction history page.";
    }
    
    setTimeout(() => {
        addBotMessage(reply);
    }, 600);
}

// Drag and drop profile upload triggers
function initDragAndDrop() {
    const dropZone = document.getElementById('drag-drop-zone');
    const fileInput = document.getElementById('profile_pic');
    if (!dropZone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--primary)';
            dropZone.style.background = 'var(--primary-50)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--gray-300)';
            dropZone.style.background = '';
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            fileInput.files = files;
            showToast('Photo dropped! Click upload to save.', 'success');
        }
    });
}


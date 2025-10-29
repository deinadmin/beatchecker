// Configuration
const API_BASE_URL = 'http://127.0.0.1:8765';

// DOM elements
let serviceIndicator, serviceStatus, loadingView, licenseView;
let licenseStatusEl, licenseTitle, licenseMessage, licenseBadge;
let licenseDetails, refreshContainer, refreshBtn, removeBtn, activationForm, messageContainer;
let licenseKeyInput, activateBtn;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    serviceIndicator = document.getElementById('serviceIndicator');
    serviceStatus = document.getElementById('serviceStatus');
    loadingView = document.getElementById('loadingView');
    licenseView = document.getElementById('licenseView');
    licenseStatusEl = document.getElementById('licenseStatus');
    licenseTitle = document.getElementById('licenseTitle');
    licenseMessage = document.getElementById('licenseMessage');
    licenseBadge = document.getElementById('licenseBadge');
    licenseDetails = document.getElementById('licenseDetails');
    refreshContainer = document.getElementById('refreshContainer');
    refreshBtn = document.getElementById('refreshBtn');
    removeBtn = document.getElementById('removeBtn');
    activationForm = document.getElementById('activationForm');
    messageContainer = document.getElementById('messageContainer');
    licenseKeyInput = document.getElementById('licenseKeyInput');
    activateBtn = document.getElementById('activateBtn');

    activateBtn.addEventListener('click', handleActivate);
    refreshBtn.addEventListener('click', handleRefresh);
    removeBtn.addEventListener('click', handleRemove);
    licenseKeyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleActivate();
        }
    });

    loadStatus();
});

async function loadStatus() {
    try {
        const serviceRunning = await checkService();
        updateServiceStatus(serviceRunning);

        if (!serviceRunning) {
            showLicenseView(false, 'Please open the BeatCheckerService helper app.', null);
            return;
        }

        const status = await fetchLicenseStatus();
        showLicenseView(serviceRunning, null, status);
    } catch (error) {
        console.error('Failed to load status:', error);
        updateServiceStatus(false);
        showLicenseView(false, 'Failed to connect to service', null);
    }
}

async function checkService() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        return response.ok;
    } catch (error) {
        return false;
    }
}

async function fetchLicenseStatus() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    try {
        const response = await fetch(`${API_BASE_URL}/license/status`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error('Failed to fetch license status');
        }
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

async function activateLicense(key) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch(`${API_BASE_URL}/license/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: key }),
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Activation failed');
        }
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

function updateServiceStatus(running) {
    if (running) {
        serviceIndicator.classList.add('running');
        serviceStatus.textContent = 'Service running';
    } else {
        serviceIndicator.classList.remove('running');
        serviceStatus.textContent = 'Service not running';
    }
}

function showLicenseView(serviceRunning, errorMessage, status) {
    loadingView.classList.add('hidden');
    licenseView.classList.remove('hidden');

    if (refreshContainer) {
        refreshContainer.classList.add('hidden');
    }
    if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.textContent = 'Refresh';
    }
    if (removeBtn) {
        removeBtn.disabled = false;
        removeBtn.textContent = 'Remove';
    }

    if (!serviceRunning || errorMessage) {
        licenseStatusEl.className = 'license-status inactive';
        licenseTitle.textContent = 'Service Unavailable';
        licenseMessage.textContent = errorMessage || 'BeatCheckerService is not running.';
        licenseBadge.className = 'license-badge inactive';
        licenseBadge.textContent = 'Offline';
        licenseDetails.classList.add('hidden');
        activationForm.classList.add('hidden');
        if (refreshContainer) {
            refreshContainer.classList.add('hidden');
        }
        return;
    }

    if (status.active) {
        licenseStatusEl.className = 'license-status active';
        licenseTitle.textContent = 'License Active';
        licenseMessage.textContent = status.message || 'Your BeatChecker license is active.';
        licenseBadge.className = 'license-badge active';
        licenseBadge.textContent = 'Active';
        renderLicenseDetails(status);
        refreshContainer.classList.remove('hidden');
        activationForm.classList.add('hidden');
    } else if (status.license_key) {
        // License exists but is inactive (blocked, expired, etc.)
        licenseStatusEl.className = 'license-status inactive';
        
        if (status.blocked) {
            licenseTitle.textContent = 'License Blocked';
            licenseBadge.className = 'license-badge inactive';
            licenseBadge.textContent = 'Blocked';
        } else if (status.expires_at && new Date(status.expires_at) < new Date()) {
            licenseTitle.textContent = 'License Expired';
            licenseBadge.className = 'license-badge inactive';
            licenseBadge.textContent = 'Expired';
        } else {
            licenseTitle.textContent = 'License Inactive';
            licenseBadge.className = 'license-badge inactive';
            licenseBadge.textContent = 'Inactive';
        }
        
        licenseMessage.textContent = status.message || 'This license cannot be used.';
        renderLicenseDetails(status);
        refreshContainer.classList.remove('hidden');
        activationForm.classList.add('hidden');
    } else {
        // No license activated
        licenseStatusEl.className = 'license-status inactive';
        licenseTitle.textContent = 'License Required';
        licenseMessage.textContent = status.message || 'Please activate BeatChecker with a license key.';
        licenseBadge.className = 'license-badge inactive';
        licenseBadge.textContent = 'INACTIVE';
        licenseDetails.classList.add('hidden');
        refreshContainer.classList.add('hidden');
        activationForm.classList.remove('hidden');
    }
}

async function refreshLicense() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch(`${API_BASE_URL}/license/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Refresh failed');
        }
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

async function handleRefresh() {
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Refreshing...';
    clearMessage();

    try {
        await refreshLicense();
        // Reload status immediately to show updated state
        const status = await fetchLicenseStatus();
        showLicenseView(true, null, status);
        
        if (status.blocked) {
            showMessage('License is blocked. Contact support for assistance.', 'error');
        } else if (!status.active) {
            showMessage('License updated but is not active.', 'error');
        } else {
            showMessage('License refreshed successfully!', 'success');
            setTimeout(clearMessage, 3000);
        }
    } catch (error) {
        showMessage(error.message || 'Refresh failed. Please try again.', 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.textContent = 'Refresh';
    }
}

async function removeLicense() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
        const response = await fetch(`${API_BASE_URL}/license/deactivate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Removal failed');
        }
        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

async function handleRemove() {
    const confirmed = confirm('Remove this license from this device?');
    
    if (!confirmed) {
        return;
    }

    removeBtn.disabled = true;
    refreshBtn.disabled = true;
    removeBtn.textContent = 'Removing...';
    clearMessage();

    try {
        await removeLicense();
        showMessage('License removed successfully.', 'success');
        setTimeout(() => {
            loadStatus();
        }, 1500);
    } catch (error) {
        showMessage(error.message || 'Removal failed. Please try again.', 'error');
        removeBtn.disabled = false;
        refreshBtn.disabled = false;
        removeBtn.textContent = 'Remove';
    }
}

function renderLicenseDetails(status) {
    licenseDetails.classList.remove('hidden');
    const rows = [];

    if (status.license_key) {
        rows.push({ label: 'License Key', value: status.license_key });
    }

    if (status.customer_name) {
        rows.push({ label: 'Customer', value: status.customer_name });
    }

    // Show status if not active
    if (!status.active) {
        let statusText = 'Inactive';
        if (status.blocked) {
            statusText = 'Blocked';
        } else if (status.expires_at && new Date(status.expires_at) < new Date()) {
            statusText = 'Expired';
        }
        rows.push({ label: 'Status', value: statusText, highlight: true });
    }

    if (status.expires_at) {
        const expiresDate = new Date(status.expires_at);
        const formatted = expiresDate.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
        rows.push({ label: 'Expires', value: formatted });
    }

    if (status.activated_machines !== null && status.max_machines !== null) {
        rows.push({
            label: 'Devices',
            value: `${status.activated_machines} / ${status.max_machines}`,
        });
    }

    licenseDetails.innerHTML = rows
        .map(
            (row) => `
        <div class="license-detail-row">
            <span class="license-detail-label">${row.label}</span>
            <span class="license-detail-value${row.highlight ? ' error-text' : ''}">${row.value}</span>
        </div>
    `
        )
        .join('');
}

async function handleActivate() {
    const key = licenseKeyInput.value.trim();
    if (!key) {
        showMessage('Please enter a license key.', 'error');
        return;
    }

    activateBtn.disabled = true;
    activateBtn.textContent = 'Activating...';
    clearMessage();

    try {
        const result = await activateLicense(key);
        showMessage(result.message || 'License activated successfully!', 'success');
        licenseKeyInput.value = '';
        setTimeout(() => {
            loadStatus();
        }, 1500);
    } catch (error) {
        showMessage(error.message || 'Activation failed. Please try again.', 'error');
        activateBtn.disabled = false;
        activateBtn.textContent = 'Activate License';
    }
}

function showMessage(text, type) {
    messageContainer.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function clearMessage() {
    messageContainer.innerHTML = '';
}

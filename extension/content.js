// Configuration
const API_BASE_URL = 'http://127.0.0.1:8765';
const HEALTH_URL = `${API_BASE_URL}/health`;
const ANALYZE_URL = `${API_BASE_URL}/analyze`;
const DOWNLOAD_URL = `${API_BASE_URL}/download`;

// Helper to get current video ID
function getVideoId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('v');
}

function createLicenseRequiredModal() {
    const modal = document.createElement('div');
    modal.className = 'yt-analyze-modal';
    modal.innerHTML = `
        <div class="yt-analyze-modal-content">
            <div class="yt-analyze-modal-header">
                <h2>License Required</h2>
                <button class="yt-analyze-modal-close">×</button>
            </div>
            <div class="yt-analyze-modal-body">
                <div class="yt-analyze-results">
                    <p class="confirmation-text">BeatChecker requires an active license. Click the BeatChecker extension icon to activate your license.</p>
                </div>
            </div>
            <div class="yt-analyze-modal-footer">
                <button class="yt-confirm-primary">Okay</button>
            </div>
        </div>
    `;

    const closeModal = () => {
        modal.classList.remove('visible');
    };

    const primaryButton = modal.querySelector('.yt-confirm-primary');
    const closeButton = modal.querySelector('.yt-analyze-modal-close');

    let resolveFn = null;

    const handleResolve = () => {
        if (resolveFn) {
            resolveFn();
            resolveFn = null;
        }
        closeModal();
    };

    primaryButton.addEventListener('click', handleResolve);
    closeButton.addEventListener('click', handleResolve);
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            handleResolve();
        }
    });

    const show = () => {
        modal.classList.add('visible');
        return new Promise((resolve) => {
            resolveFn = resolve;
        });
    };

    return {
        element: modal,
        show,
    };
}

function createServiceMissingModal() {
    const modal = document.createElement('div');
    modal.className = 'yt-analyze-modal';
    modal.innerHTML = `
        <div class="yt-analyze-modal-content">
            <div class="yt-analyze-modal-header">
                <h2>Service Required</h2>
                <button class="yt-analyze-modal-close">×</button>
            </div>
            <div class="yt-analyze-modal-body">
                <div class="yt-analyze-results">
                    <p class="confirmation-text">BeatCheckerService is not running. The helper app is required to run in the background for this extension to work.</p>
                </div>
            </div>
            <div class="yt-analyze-modal-footer">
                <button class="yt-confirm-primary">Okay</button>
            </div>
        </div>
    `;

    const closeModal = () => {
        modal.classList.remove('visible');
    };

    const primaryButton = modal.querySelector('.yt-confirm-primary');
    const closeButton = modal.querySelector('.yt-analyze-modal-close');

    let resolveFn = null;

    const handleResolve = () => {
        if (resolveFn) {
            resolveFn();
            resolveFn = null;
        }
        closeModal();
    };

    primaryButton.addEventListener('click', handleResolve);
    closeButton.addEventListener('click', handleResolve);
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            handleResolve();
        }
    });

    const show = () => {
        modal.classList.add('visible');
        return new Promise((resolve) => {
            resolveFn = resolve;
        });
    };

    return {
        element: modal,
        show,
    };
}

function createConfirmationModal() {
    const modal = document.createElement('div');
    modal.className = 'yt-analyze-modal';
    modal.innerHTML = `
        <div class="yt-analyze-modal-content">
            <div class="yt-analyze-modal-header">
                <h2>Confirm Analysis</h2>
                <button class="yt-analyze-modal-close">×</button>
            </div>
            <div class="yt-analyze-modal-body">
                <div class="yt-analyze-results">
                    <p class="confirmation-text">This video is longer than 5 minutes. Are you sure this is a beat and you want to analyze it?</p>
                </div>
            </div>
            <div class="yt-analyze-modal-footer">
                <button class="yt-confirm-cancel">Cancel</button>
                <button class="yt-confirm-primary">Analyze</button>
            </div>
        </div>
    `;

    const closeModal = () => {
        modal.classList.remove('visible');
    };

    const primaryButton = modal.querySelector('.yt-confirm-primary');
    const cancelButton = modal.querySelector('.yt-confirm-cancel');
    const closeButton = modal.querySelector('.yt-analyze-modal-close');

    let resolveFn = null;

    const handleResolve = (value) => {
        if (resolveFn) {
            resolveFn(value);
            resolveFn = null;
        }
        closeModal();
    };

    primaryButton.addEventListener('click', () => handleResolve(true));
    cancelButton.addEventListener('click', () => handleResolve(false));
    closeButton.addEventListener('click', () => handleResolve(false));
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            handleResolve(false);
        }
    });

    const show = () => {
        modal.classList.add('visible');
        return new Promise((resolve) => {
            resolveFn = resolve;
        });
    };

    return {
        element: modal,
        show,
    };
}

// Helper to get full YouTube URL
function getVideoUrl() {
    return window.location.href;
}

function closeYouTubeMenu() {
    const escapeEvent = new KeyboardEvent('keydown', {
        key: 'Escape',
        code: 'Escape',
        keyCode: 27,
        which: 27,
        bubbles: true,
    });
    document.dispatchEvent(escapeEvent);

    const openMenu = document.querySelector('ytd-menu-popup-renderer[opened]');
    if (openMenu) {
        openMenu.removeAttribute('opened');
        openMenu.removeAttribute('active');
    }
}

function getVideoDurationText() {
    const durationElement = document.querySelector('.ytp-time-duration');
    return durationElement ? durationElement.textContent.trim() : null;
}

function getVideoTitle() {
    const primaryTitle = document.querySelector('h1.ytd-watch-metadata yt-formatted-string');
    if (primaryTitle && primaryTitle.textContent.trim()) {
        return primaryTitle.textContent.trim();
    }

    const metaTitle = document.querySelector('meta[name="title"]');
    if (metaTitle && metaTitle.getAttribute('content')) {
        return metaTitle.getAttribute('content').trim();
    }

    return 'BeatChecker Track';
}

function parseDurationToSeconds(durationText) {
    if (!durationText) {
        return null;
    }

    const parts = durationText.split(':').map((part) => parseInt(part.trim(), 10));
    if (parts.some((value) => Number.isNaN(value))) {
        return null;
    }

    let multiplier = 1;
    let seconds = 0;
    for (let index = parts.length - 1; index >= 0; index -= 1) {
        seconds += parts[index] * multiplier;
        multiplier *= 60;
    }

    return seconds;
}

function getVideoDurationInSeconds() {
    return parseDurationToSeconds(getVideoDurationText());
}

let confirmationModalController = null;
let serviceModalController = null;
let licenseModalController = null;

function getConfirmationModal() {
    if (!confirmationModalController) {
        confirmationModalController = createConfirmationModal();
        document.body.appendChild(confirmationModalController.element);
    }
    return confirmationModalController;
}

function getServiceModal() {
    if (!serviceModalController) {
        serviceModalController = createServiceMissingModal();
        document.body.appendChild(serviceModalController.element);
    }
    return serviceModalController;
}

function getLicenseModal() {
    if (!licenseModalController) {
        licenseModalController = createLicenseRequiredModal();
        document.body.appendChild(licenseModalController.element);
    }
    return licenseModalController;
}

const INVALID_FILENAME_CHARS = /[\\/:*?"<>|]+/g;
const LEADING_TAG_PATTERN = /^(\s*(?:\(|\[)\s*(free(?: for profit)?|sold)\s*(?:\)|\]))\s*/i;

function sanitizeFilename(value) {
    return value
        .replace(INVALID_FILENAME_CHARS, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function stripLeadingTags(value) {
    let result = value || '';
    while (true) {
        const match = result.match(LEADING_TAG_PATTERN);
        if (!match) break;
        result = result.slice(match[0].length);
    }
    return result.trim().length ? result.trim() : value.trim();
}

function buildDownloadFilename(rawTitle, analysisData) {
    const title = rawTitle || 'BeatChecker Track';
    const cleanedTitle = stripLeadingTags(title);
    const safeTitle = sanitizeFilename(cleanedTitle) || 'BeatChecker Track';
    const lowerTitle = safeTitle.toLowerCase();

    if (lowerTitle.includes('type beat') && analysisData?.key && analysisData?.bpm) {
        const index = lowerTitle.indexOf('type beat');
        const baseSegment = safeTitle.slice(0, index).trim();
        const base = baseSegment ? baseSegment : safeTitle;
        const key = `${analysisData.key}`.toLowerCase().replace(/\s+/g, ' ').trim();
        const bpmValue = `${analysisData.bpm}`.toLowerCase();
        const normalized = `${base} type beat ${key} ${bpmValue}bpm`.toLowerCase().replace(/\s+/g, ' ').trim();
        const sanitized = sanitizeFilename(normalized) || 'beatchecker type beat';
        return `${sanitized}.mp3`;
    }

    const defaultTitle = safeTitle || 'BeatChecker Track';
    if (analysisData?.key && analysisData?.bpm) {
        const keyValue = `${analysisData.key}`.toLowerCase().replace(/\s+/g, ' ').trim();
        const bpmValue = `${analysisData.bpm}`.toLowerCase();
        const normalized = `${defaultTitle} ${keyValue} ${bpmValue}bpm`.replace(/\s+/g, ' ').trim();
        return `${sanitizeFilename(normalized)}.mp3`;
    }

    if (analysisData?.bpm) {
        return `${defaultTitle} ${analysisData.bpm}bpm.mp3`;
    }

    return `${defaultTitle}.mp3`;
}

// Create analyze button
function createAnalyzeButton() {
    const button = document.createElement('button');
    button.className = 'yt-analyze-button';
    button.innerHTML = `
        <svg style="margin-left: 8px;" viewBox="0 0 24 24" width="24" height="24">
            <path fill="currentColor" d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
        </svg>
        <span style="margin-left: 12px; padding-right: 6px;">BeatChecker</span>
    `;
    
    button.style.cssText = `
        display: flex;
        align-items: center;
        background: transparent;
        border: none;
        color: var(--yt-spec-text-primary);
        cursor: pointer;
        padding: 0 8px;
        font-size: 1.4rem;
        font-family: Roboto, sans-serif;
        height: 36px;
        line-height: 2rem;
        font-weight: 400;
        width: 100%;
        border-radius: 8px;
    `;
    
    button.onmouseover = () => button.style.backgroundColor = 'var(--yt-spec-additive-background)';
    button.onmouseout = () => button.style.backgroundColor = 'transparent';
    
    return button;
}

// Create results modal
function createResultsModal() {
    const modal = document.createElement('div');
    modal.className = 'yt-analyze-modal';
    modal.innerHTML = `
        <div class="yt-analyze-modal-content">
            <div class="yt-analyze-modal-header">
                <h2>BeatChecker</h2>
                <button class="yt-analyze-modal-close">×</button>
            </div>
            <div class="yt-analyze-modal-body">
                <div class="yt-analyze-results">
                    <div class="result-item">
                        <label>BPM:</label>
                        <span class="result-bpm">--</span>
                    </div>
                    <div class="result-item">
                        <label>Key:</label>
                        <span class="result-key">--</span>
                    </div>
                </div>
            </div>
            <div class="yt-analyze-modal-footer">
                <button class="yt-analyze-close">Close</button>
                <button class="yt-analyze-save" disabled>Download</button>
            </div>
        </div>
    `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .yt-analyze-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .yt-analyze-modal.visible {
            display: flex;
            opacity: 1;
        }
        .yt-analyze-modal-content {
            background: var(--yt-spec-base-background);
            border-radius: 12px;
            width: 450px;
            max-width: 90vw;
            color: var(--yt-spec-text-primary);
        }
        .yt-analyze-modal.visible .yt-analyze-modal-content {
            animation: fadeInUp 0.28s ease forwards;
        }
        .yt-analyze-modal-header {
            padding: 20px;
            border-bottom: 1px solid var(--yt-spec-10-percent-layer);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .yt-analyze-modal-header h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 500;
        }
        .yt-analyze-modal-close {
            background: none;
            border: none;
            color: var(--yt-spec-text-secondary);
            font-size: 32px;
            cursor: pointer;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }
        .yt-analyze-modal-close:hover {
            background: var(--yt-spec-10-percent-layer);
            border-radius: 50%;
        }
        .yt-analyze-modal-body {
            padding: 32px 20px;
        }
        .yt-analyze-results {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .confirmation-text {
            font-size: 16px;
            line-height: 1.6;
            color: var(--yt-spec-text-primary);
            margin: 0;
            text-align: left;
        }
        .result-item {
            text-align: left;
        }
        .result-item label {
            display: block;
            margin-bottom: 4px;
            font-size: 13px;
            color: var(--yt-spec-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }
        .result-item span {
            font-size: 42px;
            font-weight: 700;
            color: var(--yt-spec-text-primary);
            display: block;
        }
        .yt-analyze-modal-footer {
            padding: 16px 20px;
            border-top: 1px solid var(--yt-spec-10-percent-layer);
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        .yt-analyze-modal-footer button {
            padding: 10px 20px;
            border-radius: 18px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .yt-analyze-close {
            background: transparent;
            color: var(--yt-spec-text-primary);
        }
        .yt-confirm-cancel {
            background: transparent;
            color: var(--yt-spec-text-primary);
        }
        .yt-confirm-cancel:hover {
            background: var(--yt-spec-10-percent-layer);
        }
        .yt-analyze-close:hover {
            background: var(--yt-spec-10-percent-layer);
        }
        .yt-analyze-save {
            background: #3ea6ff;
            color: #000;
        }
        .yt-confirm-primary {
            background: #3ea6ff;
            color: #000;
        }
        .yt-confirm-primary:hover {
            background: #65b8ff;
        }
        .yt-analyze-save:hover:not(:disabled) {
            background: #65b8ff;
        }
        .yt-analyze-save:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .yt-analyze-loading {
            position: fixed;
            bottom: 24px;
            right: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px 24px;
            border-radius: 12px;
            color: var(--yt-spec-text-primary);
            background:
                linear-gradient(135deg, rgba(20, 24, 36, 0.68), rgba(14, 18, 30, 0.65)) padding-box,
                linear-gradient(135deg, rgba(104, 169, 255, 0.78), rgba(173, 112, 255, 0.78)) border-box;
            border: 1px solid transparent;
            box-shadow:
                0 10px 24px rgba(58, 123, 213, 0.25),
                0 4px 14px rgba(173, 112, 255, 0.22);
            background-size: 100% 100%, 160% 160%;
            animation: slideIn 0.3s ease-out, borderGlow 8s linear infinite;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            z-index: 10000;
        }
        .loading-spinner {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid rgba(104, 169, 255, 0.8);
            border-top: 3px solid transparent;
            animation: spin 1s linear infinite;
            box-shadow: 0 0 10px rgba(104, 169, 255, 0.45);
        }
        .loading-text {
            font-size: 14px;
            font-weight: 500;
            letter-spacing: 0.3px;
            color: rgba(226, 232, 255, 0.92);
        }
        @keyframes borderGlow {
            0% { background-position: center, 0% 50%; }
            50% { background-position: center, 100% 50%; }
            100% { background-position: center, 0% 50%; }
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes fadeInUp {
            0% {
                opacity: 0;
                transform: translateY(24px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @keyframes slideIn {
            from { transform: translateX(120%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .yt-notification {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 16px 24px;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease-out;
        }
        .yt-notification.success {
            background: #43a047;
        }
        .yt-notification.error {
            background: #d32f2f;
        }
        .yt-notification.info {
            background: #1976d2;
        }
    `;
    document.head.appendChild(style);

    return modal;
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `yt-notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
}

// Show loading indicator
function showLoading(message) {
    const loading = document.createElement('div');
    loading.className = 'yt-analyze-loading';
    loading.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-text">${message}</div>
    `;
    document.body.appendChild(loading);
    return loading;
}

// Check if service is available
async function checkService() {
    try {
        const response = await fetch(HEALTH_URL);
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Analyze video
async function analyzeVideo(url) {
    const response = await fetch(ANALYZE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
        const error = await response.json();
        if (response.status === 403) {
            const licenseError = new Error(error.detail || 'License required');
            licenseError.isLicenseError = true;
            throw licenseError;
        }
        throw new Error(error.detail || 'Analysis failed');
    }
    
    return await response.json();
}

// Trigger download via backend endpoint
async function downloadFile(filePath, preferredFilename) {
    try {
        const response = await fetch(`${DOWNLOAD_URL}?file=${encodeURIComponent(filePath)}`);
        if (!response.ok) {
            const error = await response
                .json()
                .catch(() => ({ detail: 'Download failed' }));
            throw new Error(error.detail || 'Download failed');
        }

        const blob = await response.blob();
        const filename = preferredFilename || 'beatchecker.mp3';

        const blobUrl = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(blobUrl);
    } catch (error) {
        if (error instanceof Error && error.message.includes('Failed to fetch')) {
            throw new Error('BeatCheckerService has been closed. Please reopen it to download.');
        }
        throw error;
    }
}

// Insert analyze button
function insertAnalyzeButton() {
    const menuContainer = document.querySelector('.ytd-menu-popup-renderer');
    if (!menuContainer || menuContainer.querySelector('.yt-analyze-button')) return;

    const analyzeButton = createAnalyzeButton();
    const resultsModal = createResultsModal();
    document.body.appendChild(resultsModal);

    let currentAnalysisData = null;

    analyzeButton.addEventListener('click', async () => {
        closeYouTubeMenu();

        const videoUrl = getVideoUrl();
        if (!videoUrl) {
            showNotification('Could not get video URL', 'error');
            return;
        }

        const durationSeconds = getVideoDurationInSeconds();
        const requiresConfirmation = durationSeconds !== null && durationSeconds > 5 * 60;

        if (requiresConfirmation) {
            const confirmation = await getConfirmationModal().show();
            if (!confirmation) {
                return;
            }
        }

        // Check if service is running
        const serviceAvailable = await checkService();
        if (!serviceAvailable) {
            await getServiceModal().show();
            return;
        }

        // Show loading
        const loading = showLoading('Analyzing beat...');

        try {
            const result = await analyzeVideo(videoUrl);
            currentAnalysisData = result;

            resultsModal.querySelector('.result-bpm').textContent = result.bpm;
            resultsModal.querySelector('.result-key').textContent = result.key;
            resultsModal.querySelector('.yt-analyze-save').disabled = false;
            resultsModal.classList.add('visible');
        } catch (error) {
            console.error('Analysis error:', error);
            if (error.isLicenseError) {
                // Remove loading before showing license modal
                if (loading && loading.parentNode) {
                    loading.remove();
                }
                await getLicenseModal().show();
            } else {
                showNotification(error.message || 'Analysis failed', 'error');
            }
        } finally {
            if (loading && loading.parentNode) {
                loading.remove();
            }
        }
    });

    // Modal close handlers
    const closeModal = () => {
        resultsModal.classList.remove('visible');
        currentAnalysisData = null;
    };

    resultsModal.querySelector('.yt-analyze-modal-close').addEventListener('click', closeModal);
    resultsModal.querySelector('.yt-analyze-close').addEventListener('click', closeModal);
    resultsModal.addEventListener('click', (e) => {
        if (e.target === resultsModal) closeModal();
    });

    // Save button handler
    resultsModal.querySelector('.yt-analyze-save').addEventListener('click', async () => {
        if (!currentAnalysisData) return;

        const saveButton = resultsModal.querySelector('.yt-analyze-save');
        saveButton.disabled = true;
        const originalText = saveButton.textContent;
        saveButton.textContent = 'Saving...';

        try {
            const title = getVideoTitle();
            const filename = buildDownloadFilename(title, currentAnalysisData);
            await downloadFile(currentAnalysisData.file_path, filename);
            showNotification('Downloaded successfully!', 'success');
        } catch (error) {
            console.error('Save error:', error);
            showNotification(error.message || 'Download failed!', 'error');
        } finally {
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        }
    });

    menuContainer.appendChild(analyzeButton);
}

// Observe page changes
function isWatchPage() {
    return window.location.pathname === '/watch';
}

function observePageChanges() {
    const observer = new MutationObserver(() => {
        if (!isWatchPage()) {
            return;
        }

        const menuContainer = document.querySelector('.ytd-menu-popup-renderer');
        if (menuContainer && !menuContainer.querySelector('.yt-analyze-button')) {
            insertAnalyzeButton();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

function scheduleInjection(delay = 0) {
    setTimeout(() => {
        if (!isWatchPage()) {
            return;
        }
        insertAnalyzeButton();
    }, delay);
}

function initialize() {
    observePageChanges();
    scheduleInjection(0);

    const navigationHandler = () => {
        // Allow the DOM to settle before trying to insert the button
        scheduleInjection(100);
    };

    window.addEventListener('yt-navigate-finish', navigationHandler);
    window.addEventListener('yt-page-data-updated', navigationHandler);
    window.addEventListener('popstate', navigationHandler);
    window.addEventListener('load', navigationHandler);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

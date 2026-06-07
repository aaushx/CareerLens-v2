/**
 * CareerLens — Main Application Logic & Micro-Interactions
 */

// Global Chart References to allow redraws
window.radarChartInstance = null;
window.donutChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {



    /* =============================================
       0. MOBILE SIDEBAR TOGGLE
       ============================================= */
    const sidebarMobileToggle = document.getElementById('sidebar-mobile-toggle');
    const sidebar = document.getElementById('sidebar');
    const tabLinks = document.querySelectorAll('.sidebar-link-lens');

    if (sidebarMobileToggle && sidebar) {
        // Toggle sidebar on mobile/tablet
        sidebarMobileToggle.addEventListener('click', () => {
            if (window.innerWidth >= 768 && window.innerWidth < 1024) {
                sidebar.classList.toggle('collapsed');
                // Trigger chart resize after collapse animation finishes
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 300);
            } else {
                sidebar.classList.toggle('show');
                sidebarMobileToggle.setAttribute('aria-expanded', 
                    sidebar.classList.contains('show') ? 'true' : 'false');
            }
        });

        // Close sidebar when a tab link is clicked (on mobile)
        tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth < 768) {
                    sidebar.classList.remove('show');
                    sidebarMobileToggle.setAttribute('aria-expanded', 'false');
                }
            });
        });

        // Close sidebar when clicking outside of it
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 768 && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && !sidebarMobileToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                    sidebarMobileToggle.setAttribute('aria-expanded', 'false');
                }
            }
        });

        // Close sidebar on window resize to desktop
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 1024) {
                sidebar.classList.remove('show');
                sidebar.classList.remove('collapsed');
                sidebarMobileToggle.setAttribute('aria-expanded', 'false');
            } else if (window.innerWidth >= 768 && window.innerWidth < 1024) {
                sidebar.classList.remove('show');
            }
        });
    }

    /* =============================================
       0.1 SCROLL REVEAL INITIALIZATION
       ============================================= */
    initScrollReveal();

    /* =============================================
       1. ROUTING & TAB SWITCHING
       ============================================= */
    const tabViews = document.querySelectorAll('.tab-view-lens');

    if (tabLinks.length > 0) {
        tabLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const targetTab = link.getAttribute('data-tab');
                if (!targetTab) return; // Allow normal navigation for "/"

                e.preventDefault();

                // Set active link style
                tabLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                if (window.innerWidth < 768) {
                    // Smooth-scroll to target section on mobile
                    let targetEl = null;
                    if (targetTab === 'overview') targetEl = document.querySelector('.widget-ats-score');
                    else if (targetTab === 'analysis') targetEl = document.querySelector('.widget-checklist-suggestions');
                    else if (targetTab === 'skills') targetEl = document.querySelector('.widget-skill-gap');
                    else if (targetTab === 'analytics') targetEl = document.querySelector('.widget-analytics-categories');
                    else if (targetTab === 'history') targetEl = document.querySelector('.widget-history');

                    if (targetEl) {
                        const yOffset = -90; 
                        const y = targetEl.getBoundingClientRect().top + window.pageYOffset + yOffset;
                        window.scrollTo({ top: y, behavior: 'smooth' });
                    }
                } else {
                    // Toggle views on desktop/tablet
                    tabViews.forEach(view => {
                        if (view.id === `${targetTab}-tab-view`) {
                            view.classList.add('active');
                        } else {
                            view.classList.remove('active');
                        }
                    });

                    // Trigger chart resize
                    window.dispatchEvent(new Event('resize'));
                }
            });
        });
    }

    /* =============================================
       2. SLIDING UPLOAD DRAWER (LANDING PAGE)
       ============================================= */
    const triggerUploadBtn = document.getElementById('analyze-trigger-btn');
    const uploadDrawer = document.getElementById('upload-drawer');

    if (triggerUploadBtn && uploadDrawer) {
        triggerUploadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            uploadDrawer.classList.remove('d-none');
            uploadDrawer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    /* =============================================
       3. DRAG & DROP FILE UPLOAD
       ============================================= */
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileNameBadge = document.getElementById('file-name-badge');
    const fileDisplayName = document.getElementById('file-display-name');
    
    // AJAX Progress Bar elements
    const uploadProgressContainer = document.getElementById('upload-progress-container');
    const uploadProgressBar = document.getElementById('upload-progress-bar');
    const uploadPercentage = document.getElementById('upload-percentage');
    const uploadSize = document.getElementById('upload-size');
    const cancelUploadBtn = document.getElementById('cancel-upload-btn');
    const changeFileBtn = document.getElementById('change-file-btn');
    const submitBtn = document.getElementById('submit-btn');
    const tempFilenameInput = document.getElementById('temp-filename');

    let uploadXHR = null;

    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                displaySelectedFile();
            }
        });

        fileInput.addEventListener('change', displaySelectedFile);
    }

    function displaySelectedFile() {
        if (fileInput && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            // Client-side file size validation (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                alert('File size exceeds the 5MB limit. Please upload a smaller PDF resume.');
                resetUploadUI();
                return;
            }

            // Client-side extension validation (PDF only)
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Only PDF files are allowed.');
                resetUploadUI();
                return;
            }

            // Trigger the AJAX file upload
            uploadFileToServer(file);
        } else {
            resetUploadUI();
        }
    }

    function uploadFileToServer(file) {
        // Abort any active upload
        if (uploadXHR) {
            uploadXHR.abort();
        }

        // Show progress UI and reset states
        fileNameBadge.classList.add('d-none');
        uploadProgressContainer.classList.remove('d-none');
        uploadProgressBar.style.width = '0%';
        uploadProgressBar.setAttribute('aria-valuenow', 0);
        uploadPercentage.textContent = '0%';
        uploadSize.textContent = `0.00 MB / ${(file.size / (1024 * 1024)).toFixed(2)} MB`;

        // Disable submit button during upload
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading Resume...';
        }

        const formData = new FormData();
        formData.append('resume', file);

        uploadXHR = new XMLHttpRequest();
        uploadXHR.open('POST', '/upload_temp_resume', true);

        // Track progress
        uploadXHR.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                uploadProgressBar.style.width = `${percent}%`;
                uploadProgressBar.setAttribute('aria-valuenow', percent);
                uploadPercentage.textContent = `${percent}%`;
                uploadSize.textContent = `${(e.loaded / (1024 * 1024)).toFixed(2)} MB / ${(e.total / (1024 * 1024)).toFixed(2)} MB`;
            }
        };

        // Finish load
        uploadXHR.onload = () => {
            if (uploadXHR.status === 200) {
                try {
                    const response = JSON.parse(uploadXHR.responseText);
                    if (response.success) {
                        tempFilenameInput.value = response.filename;
                        fileDisplayName.textContent = `${response.original_filename} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
                        
                        // Show success state
                        uploadProgressContainer.classList.add('d-none');
                        fileNameBadge.classList.remove('d-none');

                        // Enable analysis button
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Analyze Resume Match';
                        }
                    } else {
                        alert(`Upload failed: ${response.error || 'Unknown error'}`);
                        resetUploadUI();
                    }
                } catch (err) {
                    alert('Invalid server response during upload.');
                    resetUploadUI();
                }
            } else {
                let errorMsg = 'Upload failed.';
                try {
                    const response = JSON.parse(uploadXHR.responseText);
                    errorMsg = response.error || errorMsg;
                } catch(e) {}
                alert(errorMsg);
                resetUploadUI();
            }
            uploadXHR = null;
        };

        uploadXHR.onerror = () => {
            alert('An error occurred during file upload.');
            resetUploadUI();
            uploadXHR = null;
        };

        uploadXHR.send(formData);
    }

    function resetUploadUI() {
        if (uploadXHR) {
            uploadXHR.abort();
            uploadXHR = null;
        }
        if (fileInput) fileInput.value = '';
        if (tempFilenameInput) tempFilenameInput.value = '';
        if (fileNameBadge) fileNameBadge.classList.add('d-none');
        if (uploadProgressContainer) uploadProgressContainer.classList.add('d-none');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analyze Resume Match';
        }
    }

    if (cancelUploadBtn) {
        cancelUploadBtn.addEventListener('click', resetUploadUI);
    }

    if (changeFileBtn) {
        changeFileBtn.addEventListener('click', resetUploadUI);
    }

    /* =============================================
       4. DYNAMIC LOADER SCREEN (IMAGE 4)
       ============================================= */
    const form = document.getElementById('analyzer-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const cancelAnalysisBtn = document.getElementById('cancel-analysis');

    if (form && loadingOverlay) {
        form.addEventListener('submit', (e) => {
            const tempVal = tempFilenameInput ? tempFilenameInput.value.trim() : '';
            if (!tempVal) {
                alert('Please upload a PDF resume file first.');
                e.preventDefault();
                return;
            }

            const jdVal = document.getElementById('job-description').value.trim();
            if (jdVal.length < 20) {
                alert('Please enter a target job description of at least 20 characters.');
                e.preventDefault();
                return;
            }

            // Clear file input value before submission to prevent double upload of bytes
            if (fileInput) {
                fileInput.value = '';
            }

            // Trigger normal upload progress
            runProgressAnimation();
        });
    }

    if (cancelAnalysisBtn && loadingOverlay) {
        cancelAnalysisBtn.addEventListener('click', () => {
            loadingOverlay.style.display = 'none';
            document.body.style.overflow = 'auto';
            window.location.reload();
        });
    }

    /* =============================================
       5. INITIALIZE DASHBOARD WITH SERVER DATA
       ============================================= */
    if (window.CL_INITIAL_DATA && window.CL_INITIAL_DATA.success) {
        // Render the current server-provided payload
        renderDashboardState(window.CL_INITIAL_DATA);
    }

    // Render history records log
    renderHistoryTab();

});

/* =============================================
   6. DYNAMIC PROGRESS BAR LOADER CORE
   ============================================= */
function runProgressAnimation(onComplete = null) {
    const loadingOverlay = document.getElementById('loading-overlay');
    const loaderPct = document.getElementById('loader-pct');
    const loaderFillCircle = document.getElementById('loader-fill-circle');
    
    if (!loadingOverlay) return;

    loadingOverlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    let progress = 0;
    const circumference = 439.82; // 2 * Math.PI * 70
    
    const steps = [
        { limit: 20, elementId: 'step-extract' },
        { limit: 40, elementId: 'step-ocr' },
        { limit: 65, elementId: 'step-skills' },
        { limit: 85, elementId: 'step-ats' },
        { limit: 100, elementId: 'step-report' }
    ];

    let currentStepIdx = 0;

    const interval = setInterval(() => {
        if (progress >= 100) {
            clearInterval(interval);
            if (onComplete) {
                onComplete();
            }
            return;
        }

        progress += 1;
        loaderPct.textContent = `${progress}%`;

        const offset = circumference - (progress / 100) * circumference;
        if (loaderFillCircle) {
            loaderFillCircle.style.strokeDashoffset = offset;
        }

        const currentStep = steps[currentStepIdx];
        if (currentStep && progress >= currentStep.limit) {
            const stepItem = document.getElementById(currentStep.elementId);
            if (stepItem) {
                stepItem.classList.remove('active');
                stepItem.classList.add('completed');
                stepItem.querySelector('i').className = 'fas fa-circle-check';
            }

            currentStepIdx += 1;
            const nextStep = steps[currentStepIdx];
            if (nextStep) {
                const nextItem = document.getElementById(nextStep.elementId);
                if (nextItem) {
                    nextItem.classList.add('active');
                    nextItem.querySelector('i').className = 'fas fa-spinner fa-spin';
                }
            }
        }
    }, 45); // ~4.5 seconds animation
}

/* =============================================
   7. TRY DEMO SCAN FUNCTION
   ============================================= */
function runDemoScan() {
    const form = document.getElementById('analyzer-form');
    const fileInput = document.getElementById('file-input');
    const jdField = document.getElementById('job-description');
    const tempFilenameInput = document.getElementById('temp-filename');

    if (!form) return;

    // Pre-fill demo job description if empty
    if (!jdField.value || jdField.value.trim().length < 20) {
        useSample('frontend');
    }

    // Bypass required file validation dynamically
    if (fileInput) {
        fileInput.removeAttribute('required');
    }

    // Clear temporary filename input to avoid submitting old data
    if (tempFilenameInput) {
        tempFilenameInput.value = '';
    }

    // Run loaders, set endpoint to /demo, and submit
    runProgressAnimation(() => {
        form.action = '/demo';
        form.submit();
    });
}

/* =============================================
   8. CENTRAL STATE SYNCHRONIZATION ENGINE
   ============================================= */
function renderDashboardState(data) {
    if (!data) return;

    // Cache current active payload for theme change redraws
    window.currentActiveScanPayload = data;

    // ── Update Filename ──
    const filenameLabel = document.getElementById('overview-filename-label');
    if (filenameLabel) {
        filenameLabel.textContent = data.filename || "Alexander_Davis_Lead_Dev.pdf";
    }

    // ── Update Core Metrics ──
    const maxOffset = 263.89; // 2 * Math.PI * 42
    
    // Animate Circular Gauges
    const gauges = [
        { id: 'gauge-final', score: data.metrics.final_score },
        { id: 'gauge-skill', score: data.metrics.skill_match },
        { id: 'gauge-semantic', score: data.metrics.semantic_match }
    ];
    
    gauges.forEach(g => {
        const el = document.getElementById(g.id);
        if (el) {
            const offset = maxOffset - (g.score / 100) * maxOffset;
            el.style.strokeDashoffset = offset;
        }
    });

    // Update Text Values inside Gauges
    document.getElementById('text-gauge-final').textContent = `${Math.round(data.metrics.final_score)}%`;
    document.getElementById('text-gauge-skill').textContent = `${Math.round(data.metrics.skill_match)}%`;
    document.getElementById('text-gauge-semantic').textContent = `${Math.round(data.metrics.semantic_match)}%`;

    // Strength Badge
    document.getElementById('text-badge-strength').textContent = data.metrics.badge;
    const strengthIcon = document.getElementById('badge-strength-icon');
    if (strengthIcon) {
        let iconHtml = '<i class="fas fa-circle-check"></i>';
        if (data.metrics.badge === 'Beginner') iconHtml = '<i class="fas fa-triangle-exclamation text-danger"></i>';
        else if (data.metrics.badge === 'Intermediate') iconHtml = '<i class="fas fa-bars-progress text-warning"></i>';
        strengthIcon.innerHTML = iconHtml;
    }

    // ── Update AI Verdict ──
    let verdictTitle = "Strong candidate profile, but lacking measurable impacts.";
    if (data.metrics.final_score >= 80) {
        verdictTitle = "Strong candidate profile, demonstrating great domain fundamentals.";
    } else if (data.metrics.final_score >= 60) {
        verdictTitle = "Moderate compliance, but lacking key target impact metrics.";
    } else {
        verdictTitle = "Weak resume alignment, significant keywords optimization required.";
    }
    document.getElementById('verdict-title-label').textContent = verdictTitle;

    // Strengths list
    const strengthsWrapper = document.getElementById('verdict-strengths-list');
    let strengthsHtml = '<li>Demonstrates clear baseline structural parsed sections.</li>';
    if (data.checklist.projects) strengthsHtml += '<li>Detailed projects layout highlighting software architecture.</li>';
    if (data.checklist.experience) strengthsHtml += '<li>Professional work history details successfully cataloged.</li>';
    if (data.checklist.contact_info) strengthsHtml += '<li>Header contact coordinates &amp; socials successfully mapped.</li>';
    strengthsWrapper.innerHTML = strengthsHtml;

    // Weaknesses list
    const weaknessesWrapper = document.getElementById('verdict-weaknesses-list');
    let weaknessesHtml = '';
    if (data.details.metric_count < 3) weaknessesHtml += '<li>Under-quantified achievements. Try to add more metrics (e.g. %, $) to show impact.</li>';
    if (data.details.action_verb_count < 5) weaknessesHtml += '<li>Passive voice detected. Revise bullets to start with active verbs (e.g. Spearheaded).</li>';
    if (data.skills.missing_flat_count > 0) weaknessesHtml += `<li>Target keyword gaps. Integrate missing ${data.skills.missing_flat_count} competencies from report.</li>`;
    if (!weaknessesHtml) weaknessesHtml = '<li>None! Excellent compliance levels.</li>';
    weaknessesWrapper.innerHTML = weaknessesHtml;

    // ── Update Quick Wins ──
    const quickWinsWrapper = document.getElementById('quick-wins-list-wrapper');
    let winsHtml = '';
    data.quick_wins.forEach(win => {
        winsHtml += `
            <div class="win-card-lens">
                <div class="win-header-lens">
                    <span class="win-title-lens text-white">${win.title}</span>
                    <span class="win-points-lens text-success">${win.points}</span>
                </div>
                <p class="win-desc-lens">${win.description}</p>
            </div>
        `;
    });
    quickWinsWrapper.innerHTML = winsHtml;

    // ── Update Suggestions (Detailed Tab) ──
    const suggestionsWrapper = document.getElementById('suggestions-list-wrapper');
    let suggestionsHtml = '';
    data.suggestions.forEach(sugg => {
        suggestionsHtml += `
            <div class="win-card-lens m-0" style="border-left: 3px solid ${sugg.priority === 'High' ? 'var(--danger)' : (sugg.priority === 'Medium' ? 'var(--warning)' : 'var(--accent-indigo)')};">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="win-title-lens text-white font-bold">${sugg.title}</span>
                    <span class="small font-bold" style="font-size: 0.65rem; text-transform: uppercase; color: var(--text-muted);">${sugg.priority}</span>
                </div>
                <p class="win-desc-lens" style="font-size: 0.8rem;">${sugg.description}</p>
            </div>
        `;
    });
    if (!suggestionsHtml) suggestionsHtml = '<div class="text-center py-5 text-muted small">No suggestions generated. Structure is optimal.</div>';
    suggestionsWrapper.innerHTML = suggestionsHtml;

    // ── Update ATS Compliance Checks ──
    const complianceWrapper = document.getElementById('compliance-checklist-wrapper');
    let complianceHtml = `
        <div class="compliance-row-lens">
            <span class="compliance-label-lens"><i class="fas fa-circle-check text-success"></i> Keyword Density</span>
            <span class="compliance-status-lens">${data.compliance.keyword_density.status}</span>
        </div>
        <div class="compliance-row-lens">
            <span class="compliance-label-lens"><i class="fas fa-circle-check text-success"></i> File Format</span>
            <span class="compliance-status-lens">${data.compliance.file_format.status}</span>
        </div>
        <div class="compliance-row-lens">
            <span class="compliance-label-lens">
                ${data.compliance.complex_formatting.status === 'Review' ? '<i class="fas fa-triangle-exclamation text-warning"></i>' : '<i class="fas fa-circle-check text-success"></i>'}
                Complex Formatting
            </span>
            <span class="compliance-status-lens ${data.compliance.complex_formatting.status === 'Review' ? 'caution' : ''}">${data.compliance.complex_formatting.status}</span>
        </div>
    `;
    complianceWrapper.innerHTML = complianceHtml;

    // ── Update Parsing details ──
    document.getElementById('parse-method-label').textContent = data.extraction_method;
    document.getElementById('action-verbs-count-label').textContent = data.details.action_verb_count;
    document.getElementById('quantifiers-count-label').textContent = data.details.metric_count;

    // ── Update Missing Skills Detail ──
    document.getElementById('skills-gap-badge-count').textContent = `${data.skills.missing_flat_count} Critical Gaps`;
    
    const missingWrapper = document.getElementById('skills-missing-wrapper');
    let missingHtml = '';
    let flatIdx = 1;
    
    for (const [category, skillList] of Object.entries(data.skills.missing)) {
        skillList.forEach(skill => {
            missingHtml += `
                <div class="skill-expand-card-lens">
                    <div class="skill-expand-header-lens" onclick="toggleSkillCollapse(this)">
                        <div>
                            <span class="skill-expand-title-lens text-white">${skill.name}</span>
                            <span class="small text-muted ms-2" style="font-size: 0.75rem;">(${category})</span>
                        </div>
                        <div class="d-flex align-items-center gap-3">
                            <span class="skill-expand-badge-lens">${skill.difficulty}</span>
                            <span class="collapse-icon-lens"><i class="fas fa-chevron-down text-muted"></i></span>
                        </div>
                    </div>
                    
                    <div class="skill-expand-body-lens ${flatIdx > 1 ? 'd-none' : ''}">
                        <h6 class="small font-bold text-uppercase text-muted" style="letter-spacing: 0.05em; font-size: 0.65rem;">Why it Matters</h6>
                        <p class="small text-secondary mb-3" style="line-height: 1.6;">
                            This skill was explicitly required in the target Job Description. Including it directly improves your ATS keyword matching score.
                        </p>

                        <h6 class="small font-bold text-uppercase text-muted" style="letter-spacing: 0.05em; font-size: 0.65rem; margin-top: 1rem;">Importance</h6>
                        <div class="importance-bar-wrap-lens d-flex align-items-center gap-3">
                            <div class="importance-bar-lens flex-grow-1">
                                <div class="importance-bar-fill-lens" style="width: 85%;"></div>
                            </div>
                            <span class="small font-bold text-white">High (85%)</span>
                        </div>
                    </div>
                </div>
            `;
            flatIdx++;
        });
    }
    if (!missingHtml) {
        missingHtml = `
            <div class="text-center py-5 text-muted small">
                <i class="fas fa-circle-check text-success fs-1 mb-2"></i>
                <p class="mb-0">No missing skills detected! Perfect keywords match.</p>
            </div>
        `;
    }
    missingWrapper.innerHTML = missingHtml;

    // ── Update Timeline Roadmap ──
    const roadmapWrapper = document.getElementById('skills-roadmap-timeline-wrapper');
    let roadmapHtml = '';
    data.roadmap_timeline.forEach((step, idx) => {
        roadmapHtml += `
            <div class="timeline-step-lens">
                <div class="timeline-dot-lens ${idx > 0 ? 'empty' : ''}"></div>
                <div class="timeline-day-lens">${step.days}</div>
                <h6 class="timeline-title-lens text-white">${step.title}</h6>
                <p class="timeline-desc-lens">${step.description}</p>
            </div>
        `;
    });
    roadmapWrapper.innerHTML = roadmapHtml;

    // ── Update Analytics Match Summary Pills ──
    const matchedPillsWrapper = document.getElementById('analytics-matched-skills-pills');
    let matchedPills = '';
    for (const [cat, skillList] of Object.entries(data.skills.matching)) {
        skillList.forEach(s => {
            matchedPills += `<span class="skill-pill-lens match"><i class="fas fa-check"></i> ${s}</span>`;
        });
    }
    if (!matchedPills) matchedPills = '<span class="small text-muted">No keywords matched.</span>';
    matchedPillsWrapper.innerHTML = matchedPills;

    const missingPillsWrapper = document.getElementById('analytics-missing-skills-pills');
    let missingPills = '';
    for (const [cat, skillList] of Object.entries(data.skills.missing)) {
        skillList.forEach(s => {
            missingPills += `<span class="skill-pill-lens miss"><i class="fas fa-xmark"></i> ${s.name}</span>`;
        });
    }
    if (!missingPills) missingPills = '<span class="small text-success">No keywords missing! Perfect match.</span>';
    missingPillsWrapper.innerHTML = missingPills;

    // ── Update Analytics Progress Bars ──
    const analyticsCategoriesWrapper = document.getElementById('analytics-categories-wrapper');
    let categoriesHtml = '';
    data.skills.category_progress.forEach(cat => {
        categoriesHtml += `
            <div>
                <div class="d-flex justify-content-between mb-2 small font-bold">
                    <span class="text-white">${cat.category}</span>
                    <span class="text-muted">${cat.matched}/${cat.total} (${Math.round(cat.coverage)}%)</span>
                </div>
                <div class="importance-bar-lens">
                    <div class="importance-bar-fill-lens" style="width: ${cat.coverage}%; background: linear-gradient(90deg, var(--accent-purple), var(--accent-indigo));"></div>
                </div>
            </div>
        `;
    });
    if (!categoriesHtml) categoriesHtml = '<div class="text-center py-5 text-muted small">No category matches available.</div>';
    analyticsCategoriesWrapper.innerHTML = categoriesHtml;

    // ── Update Charts (Chart.js instance rebuilds) ──
    rebuildCharts(data);
}

/**
 * Destroys existing charts if present and constructs the Radar/Donut models.
 */
function rebuildCharts(data) {
    const chartFontColor = '#4b5563';
    const chartGridColor = 'rgba(0, 0, 0, 0.06)';

    const radarStroke = '#111827';
    const radarFill = 'rgba(17, 24, 39, 0.08)';
    const radarTargetStroke = 'rgba(0, 0, 0, 0.12)';

    const donutBorder = '#ffffff';

    // 1. Rebuild Radar Skill Coverage
    const radarCanvas = document.getElementById('radar-chart-lens');
    if (radarCanvas) {
        if (window.radarChartInstance) {
            window.radarChartInstance.destroy();
        }

        const categories = [];
        const coverageData = [];
        const targetData = [];

        data.skills.category_progress.forEach(cat => {
            categories.push(cat.category);
            coverageData.push(cat.coverage || 0);
            targetData.push(100);
        });

        window.radarChartInstance = new Chart(radarCanvas, {
            type: 'radar',
            data: {
                labels: categories,
                datasets: [
                    {
                        label: 'Current Skills',
                        data: coverageData,
                        backgroundColor: radarFill,
                        borderColor: radarStroke,
                        borderWidth: 2,
                        pointBackgroundColor: radarStroke,
                        pointBorderColor: '#ffffff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: radarStroke,
                        pointRadius: 4
                    },
                    {
                        label: 'Target Role',
                        data: targetData,
                        backgroundColor: 'rgba(0, 0, 0, 0.01)',
                        borderColor: radarTargetStroke,
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: chartGridColor },
                        grid: { color: chartGridColor },
                        ticks: { display: false },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        pointLabels: {
                            color: chartFontColor,
                            font: { family: 'Inter', size: 10, weight: '600' }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: chartFontColor,
                            font: { family: 'Inter', size: 10 },
                            boxWidth: 12
                        }
                    }
                }
            }
        });
    }

    // 2. Rebuild Donut Chart
    const donutCanvas = document.getElementById('donut-chart-lens');
    if (donutCanvas) {
        if (window.donutChartInstance) {
            window.donutChartInstance.destroy();
        }

        const matchedCount = data.skills.matching_flat_count || 0;
        const missingCount = data.skills.missing_flat_count || 0;

        window.donutChartInstance = new Chart(donutCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Matched Skills', 'Missing Skills'],
                datasets: [{
                    data: [matchedCount, missingCount],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.75)',
                        'rgba(239, 68, 68, 0.75)'
                    ],
                    borderColor: donutBorder,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: chartFontColor,
                            font: { family: 'Inter', size: 10 },
                            boxWidth: 12
                        }
                    }
                }
            }
        });
    }
}

/**
 * Event-bindable function to toggle skill card expansion.
 */
function toggleSkillCollapse(header) {
    const body = header.nextElementSibling;
    const icon = header.querySelector('.collapse-icon-lens i');
    
    if (body.classList.contains('d-none')) {
        body.classList.remove('d-none');
        if (icon) icon.className = 'fas fa-chevron-up';
    } else {
        body.classList.add('d-none');
        if (icon) icon.className = 'fas fa-chevron-down';
    }
}

/* =============================================
   9. DATABASE-BACKED HISTORY MANAGEMENT
   ============================================= */

function renderHistoryTab() {
    const listWrapper = document.getElementById('history-list-wrapper');
    if (!listWrapper) return;

    fetch('/api/history')
    .then(response => response.json())
    .then(history => {
        if (history.length === 0) {
            listWrapper.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-history mb-3 fs-1" style="opacity: 0.3;"></i>
                    <p class="mb-0">No previous scan reports found. Run a new scan first!</p>
                </div>
            `;
            return;
        }

        let html = '<div class="table-responsive"><table class="table table-dark table-hover border-0 align-middle">';
        html += `
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.06); font-size: 0.8rem; color: #64748b;">
                    <th scope="col" class="py-3">DATE / FILE</th>
                    <th scope="col" class="py-3">PARSING METHOD</th>
                    <th scope="col" class="py-3">SKILL MATCH</th>
                    <th scope="col" class="py-3">SEMANTIC</th>
                    <th scope="col" class="py-3">STRENGTH</th>
                    <th scope="col" class="py-3">SCORE</th>
                    <th scope="col" class="py-3 text-end">ACTIONS</th>
                </tr>
            </thead>
            <tbody>
        `;

        history.forEach((run, idx) => {
            const formattedDate = new Date(run.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            html += `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.03); font-size: 0.9rem;">
                    <td class="py-3" data-label="Date / File">
                        <div class="fw-semibold text-white d-inline-block d-md-block">${formattedDate}</div>
                        <div class="text-muted small d-inline-block d-md-block ms-2 ms-md-0">${run.filename}</div>
                    </td>
                    <td class="py-3" data-label="Parsing Method"><span class="badge bg-dark border border-secondary border-opacity-10 rounded-pill px-3 py-1 font-monospace">${run.extraction_method}</span></td>
                    <td class="py-3" data-label="Skill Match">${run.skill_match.toFixed(1)}%</td>
                    <td class="py-3" data-label="Semantic">${run.semantic_match.toFixed(1)}%</td>
                    <td class="py-3" data-label="Strength">${run.resume_strength.toFixed(1)}% (${run.badge})</td>
                    <td class="py-3 fw-bold text-white" data-label="Score">${run.final_score.toFixed(1)}%</td>
                    <td class="py-3 text-end" data-label="Actions">
                        <button class="btn btn-sm btn-pill btn-pill-primary py-1 px-3" onclick="reloadHistoricalScan(${run.id})">Reload</button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        listWrapper.innerHTML = html;
    })
    .catch(err => {
        console.error("Error fetching history:", err);
        listWrapper.innerHTML = `<div class="text-center py-5 text-danger">Error loading scan history from server.</div>`;
    });
}

/**
 * Reloads a historical scan from the database, updates session results, and redraws gauges/charts.
 */
function reloadHistoricalScan(scanId) {
    fetch(`/api/history/${scanId}`)
    .then(response => response.json())
    .then(data => {
        if (!data.success || !data.results) {
            alert("Could not load report logs.");
            return;
        }

        // Synchronize all UI metrics, timelines, lists, charts
        renderDashboardState(data.results);

        // Smooth transition to Overview tab
        const overviewLink = document.querySelector('.sidebar-link-lens[data-tab="overview"]');
        if (overviewLink) {
            overviewLink.click();
        }
    })
    .catch(err => {
        console.error("Error loading scan:", err);
        alert("Failed to connect to the database to reload scan.");
    });
}

/**
 * Clears all scan history for the current visitor in the database.
 */
function clearDatabaseHistory() {
    if (confirm("Are you sure you want to permanently erase your scan history logs?")) {
        fetch('/api/history/clear', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert("Failed to clear database logs.");
            }
        })
        .catch(err => {
            console.error("Error clearing logs:", err);
            alert("Error connecting to server to clear logs.");
        });
    }
}

/**
 * Fill a sample role requirements description into the textarea.
 */
function useSample(role) {
    const jdField = document.getElementById('job-description');

    const SAMPLE_JDS = {
        swe: `Software Engineer\nResponsibilities:\n- Design and develop scalable backend applications in Python and Java.\n- Write clean, maintainable, and efficient SQL queries.\n- Build web interfaces and integrate REST APIs.\n- Collaborate using Git/GitHub.\nRequirements:\n- Strong knowledge of Python, Java, and SQL.\n- Experience with Flask, Django, and PostgreSQL.\n- Understanding of Docker, CI/CD, and Cloud (AWS/GCP).\n- Excellent communication and software engineering principles.`,

        frontend: `Frontend Developer\nResponsibilities:\n- Build responsive, beautiful, and interactive web applications.\n- Collaborate with designers to translate wireframes into high-quality code.\n- Optimize frontend components for maximum speed and scalability.\nRequirements:\n- Expert level HTML, CSS, JavaScript, and Tailwind CSS.\n- Extensive experience with React, Next.js, and TypeScript.\n- Strong familiarity with Git, npm, Webpack, and version control.\n- Good knowledge of UI/UX design patterns.`,

        backend: `Backend Developer\nResponsibilities:\n- Develop secure and high-performance server-side APIs.\n- Manage and design relational and non-relational database schemas.\n- Implement containerized deployments using Docker and Kubernetes.\nRequirements:\n- Proficient in Node.js, Express, and FastAPI.\n- Hands-on experience with SQL, PostgreSQL, MongoDB, and Redis.\n- Deep understanding of REST APIs, GraphQL, and security protocols.\n- Familiarity with CI/CD pipelines, Docker, Kubernetes, and AWS.`,

        data: `Data Analyst\nResponsibilities:\n- Collect, clean, and analyze complex datasets to drive business decisions.\n- Create automated reports and interactive dashboards.\n- Write complex database queries to extract insight.\nRequirements:\n- Strong programming skills in Python and SQL.\n- Mastery of Pandas, NumPy, and Scikit-Learn for analysis.\n- Experience with Postgres, MySQL, and Excel.\n- Excellent data visualization skills and statistical background.`,

        ml: `Machine Learning Engineer\nResponsibilities:\n- Build, train, and deploy production-grade machine learning models.\n- Optimize neural network architectures for computer vision and NLP.\n- Create data processing pipelines and train models at scale.\nRequirements:\n- Strong background in Python, PyTorch, and TensorFlow.\n- Experience with Machine Learning, Deep Learning, NLP, and Computer Vision.\n- Good knowledge of Pandas, NumPy, Keras, and Scikit-Learn.\n- Familiarity with Docker, AWS, and model deployment APIs.`
    };

    if (jdField && SAMPLE_JDS[role]) {
        jdField.value = SAMPLE_JDS[role];
        jdField.style.transition = 'box-shadow 0.3s ease';
        jdField.style.boxShadow = '0 0 0 3px rgba(255, 255, 255, 0.15)';
        setTimeout(() => {
            jdField.style.boxShadow = 'none';
        }, 1500);
    }
}

/**
 * Initializes IntersectionObserver to reveal elements as the user scrolls.
 */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    if ('IntersectionObserver' in window && revealElements.length > 0) {
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        revealElements.forEach(el => observer.observe(el));
    } else {
        revealElements.forEach(el => el.classList.add('revealed'));
    }
}

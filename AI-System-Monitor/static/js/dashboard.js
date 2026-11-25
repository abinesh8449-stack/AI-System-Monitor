/**
 * Dashboard Live Telemetry & AI Diagnostic Controller
 */

let previousOverallStatus = null;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize live charts
    initCharts();

    // 2. Initial fetch
    fetchMetrics();
    fetchSummary();

    // 3. Set polling loops
    setInterval(fetchMetrics, 1500); // 1.5s real-time telemetry
    setInterval(fetchSummary, 5000); // 5s summary & count aggregation
});

async function fetchMetrics() {
    try {
        const response = await fetch('/api/metrics');
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        renderDashboard(data);
    } catch (err) {
        console.warn('Telemetry fetch error:', err.message);
        const liveDot = document.getElementById('globalLiveDot');
        if (liveDot) liveDot.style.backgroundColor = '#ef4444';
        const liveStatus = document.getElementById('globalLiveStatus');
        if (liveStatus) liveStatus.textContent = 'DISCONNECTED';
    }
}

async function fetchSummary() {
    try {
        const response = await fetch('/api/summary');
        if (response.ok) {
            const data = await response.json();
            if (data.alert_counts) {
                document.getElementById('metaTotalAlerts').textContent = data.alert_counts.total_alerts || '0';
                document.getElementById('statRecoveredCount').textContent = data.alert_counts.recovered_events || '0';
                
                const navBadge = document.getElementById('navAlertBadge');
                if (navBadge) {
                    const unrecovered = (data.alert_counts.total_alerts || 0) - (data.alert_counts.recovered_events || 0);
                    if (unrecovered > 0) {
                        navBadge.textContent = unrecovered;
                        navBadge.style.display = 'inline-block';
                    } else {
                        navBadge.style.display = 'none';
                    }
                }
            }
            if (data.system_info) {
                document.getElementById('metaHostname').textContent = data.system_info.hostname || 'Local Host';
                document.getElementById('metaUptime').textContent = data.system_info.uptime || '--:--:--';
            }
        }
    } catch (err) {
        // Silently tolerate summary polling hiccup
    }
}

function renderDashboard(data) {
    const timeLabel = new Date().toLocaleTimeString('en-US', { hour12: false });
    document.getElementById('lastUpdatedTime').textContent = timeLabel;

    // Reset live indicator to online
    const liveDot = document.getElementById('globalLiveDot');
    if (liveDot) liveDot.style.backgroundColor = '#10b981';
    const liveStatus = document.getElementById('globalLiveStatus');
    if (liveStatus) liveStatus.textContent = 'ONLINE';

    // 1. Overall System Health Banner
    const health = data.health || {};
    const overallStatus = (health.overall_status || 'HEALTHY').toUpperCase();
    const bannerCard = document.getElementById('healthBannerCard');
    const healthText = document.getElementById('overallHealthText');
    const healthBadge = document.getElementById('overallHealthBadge');
    const healthIcon = document.getElementById('overallHealthIcon');
    const iconWrapper = document.getElementById('overallHealthIconWrapper');

    healthText.textContent = `SYSTEM ${overallStatus}`;
    healthBadge.textContent = overallStatus;

    if (overallStatus === 'CRITICAL') {
        bannerCard.style.borderLeftColor = 'var(--color-critical)';
        healthBadge.className = 'badge rounded-pill px-3 py-2 fs-6 bg-danger';
        healthIcon.className = 'bi bi-x-octagon-fill';
        iconWrapper.style.color = 'var(--color-critical)';
        iconWrapper.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
        if (previousOverallStatus !== 'CRITICAL') {
            playAlertBeep();
        }
    } else if (overallStatus === 'WARNING') {
        bannerCard.style.borderLeftColor = 'var(--color-warning)';
        healthBadge.className = 'badge rounded-pill px-3 py-2 fs-6 bg-warning text-dark';
        healthIcon.className = 'bi bi-exclamation-triangle-fill';
        iconWrapper.style.color = 'var(--color-warning)';
        iconWrapper.style.backgroundColor = 'rgba(245, 158, 11, 0.15)';
    } else {
        bannerCard.style.borderLeftColor = 'var(--color-healthy)';
        healthBadge.className = 'badge rounded-pill px-3 py-2 fs-6 bg-success';
        healthIcon.className = 'bi bi-shield-check';
        iconWrapper.style.color = 'var(--color-healthy)';
        iconWrapper.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
    }
    previousOverallStatus = overallStatus;

    // Health counts
    if (health.counts) {
        document.getElementById('statHealthyCount').textContent = health.counts.healthy;
        document.getElementById('statWarningCount').textContent = health.counts.warning;
        document.getElementById('statCriticalCount').textContent = health.counts.critical;
    }

    // 2. CPU Card
    const cpu = data.cpu || {};
    const cpuVal = formatDecimals(cpu.cpu_percent, 1);
    document.getElementById('cpuPercent').textContent = cpuVal;
    document.getElementById('cpuProgressBar').style.width = `${cpuVal}%`;
    document.getElementById('cpuCores').textContent = cpu.logical_cores || '--';
    document.getElementById('cpuFreq').textContent = cpu.frequency_current_mhz ? `${cpu.frequency_current_mhz} MHz` : 'Dynamic';

    const cpuBadge = document.getElementById('cpuStatusBadge');
    cpuBadge.textContent = health.cpu_status || 'HEALTHY';
    cpuBadge.className = `badge status-pill ${getStatusClass(health.cpu_status)}`;

    // 3. RAM Card
    const ram = data.ram || {};
    const ramVal = formatDecimals(ram.ram_percent, 1);
    document.getElementById('ramPercent').textContent = ramVal;
    document.getElementById('ramProgressBar').style.width = `${ramVal}%`;
    document.getElementById('ramUsed').textContent = ram.used_ram_gb || '0.0';
    document.getElementById('ramTotal').textContent = ram.total_ram_gb || '0.0';
    document.getElementById('ramAvail').textContent = `${ram.available_ram_gb || '0.0'} GB Avail`;

    const ramBadge = document.getElementById('ramStatusBadge');
    ramBadge.textContent = health.ram_status || 'HEALTHY';
    ramBadge.className = `badge status-pill ${getStatusClass(health.ram_status)}`;

    // 4. Disk Card
    const disk = data.disk || {};
    const diskVal = formatDecimals(disk.disk_percent, 1);
    document.getElementById('diskPercent').textContent = diskVal;
    document.getElementById('diskProgressBar').style.width = `${diskVal}%`;
    document.getElementById('diskUsed').textContent = disk.used_disk_gb || '0.0';
    document.getElementById('diskTotal').textContent = disk.total_disk_gb || '0.0';
    document.getElementById('diskFree').textContent = `${disk.free_disk_gb || '0.0'} GB Free`;

    const diskBadge = document.getElementById('diskStatusBadge');
    diskBadge.textContent = health.disk_status || 'HEALTHY';
    diskBadge.className = `badge status-pill ${getStatusClass(health.disk_status)}`;

    // 5. Network Card
    const net = data.network || {};
    document.getElementById('netUpload').innerHTML = `${net.rates?.upload_speed_kb || 0.0} <span class="small text-muted fs-6">KB/s</span>`;
    document.getElementById('netDownload').innerHTML = `${net.rates?.download_speed_kb || 0.0} <span class="small text-muted fs-6">KB/s</span>`;
    document.getElementById('netStatusText').textContent = net.status_text || 'Connected';
    document.getElementById('netIpAddress').textContent = net.primary_ip || '127.0.0.1';

    const netBadge = document.getElementById('netStatusBadge');
    netBadge.textContent = health.network_status || 'HEALTHY';
    netBadge.className = `badge status-pill ${getStatusClass(health.network_status)}`;

    // 6. AI Recommendation Card
    const ai = data.ai_recommendation || {};
    document.getElementById('aiProblem').textContent = ai.problem || 'Evaluating operational workloads...';
    document.getElementById('aiPossibleCause').textContent = ai.possible_cause || 'Workload profile is standard.';
    document.getElementById('aiRecommendedAction').textContent = ai.recommended_action || 'No action needed.';
    document.getElementById('aiPreventiveAction').textContent = ai.preventive_action || 'Maintain standard routine.';
    document.getElementById('aiTimestamp').textContent = ai.timestamp || timeLabel;

    const aiSeverity = document.getElementById('aiSeverityBadge');
    aiSeverity.textContent = ai.severity || 'NORMAL';
    if (ai.severity === 'CRITICAL') {
        aiSeverity.className = 'badge rounded-pill bg-danger px-3 py-1 font-monospace';
    } else if (ai.severity === 'WARNING') {
        aiSeverity.className = 'badge rounded-pill bg-warning text-dark px-3 py-1 font-monospace';
    } else {
        aiSeverity.className = 'badge rounded-pill bg-success-subtle text-success border border-success-subtle px-3 py-1 font-monospace';
    }

    // Sync AI Self-Healing Controls
    if (data.remediation) {
        const autoSwitch = document.getElementById('autoHealSwitch');
        if (autoSwitch && document.activeElement !== autoSwitch) {
            autoSwitch.checked = !!data.remediation.auto_heal_enabled;
        }
    }

    // Highlight AI Fix button when system is CRITICAL
    const fixBtn = document.getElementById('btnExecuteAiFix');
    if (fixBtn) {
        if (overallStatus === 'CRITICAL') {
            fixBtn.className = 'btn btn-danger btn-sm fw-semibold d-flex align-items-center gap-2 px-3 shadow pulse-badge';
            fixBtn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i> CRITICAL: Execute AI Self-Healing Now';
        } else {
            fixBtn.className = 'btn btn-success btn-sm fw-semibold d-flex align-items-center gap-2 px-3 shadow-sm';
            fixBtn.innerHTML = '<i class="bi bi-wrench-adjustable-circle-fill"></i> Execute AI Self-Healing Now';
        }
    }

    // If Autonomous AI Self-Healing just executed, show the log banner
    if (data.auto_healed_event) {
        showRemediationLog(data.auto_healed_event);
        fetchSummary();
    }

    // 7. Update Charts
    updateChartSeries(cpuChart, timeLabel, parseFloat(cpuVal));
    updateChartSeries(ramChart, timeLabel, parseFloat(ramVal));
    updateChartSeries(diskChart, timeLabel, parseFloat(diskVal));
    updateNetworkChartSeries(timeLabel, net.rates?.upload_speed_kb || 0.0, net.rates?.download_speed_kb || 0.0);

    // 8. Update Top Processes (skip DOM rebuild while user is hovering to prevent mid-click cancellation)
    if (data.top_processes && (!window.isHoveringProcessTable || window.forceProcessTableRefresh)) {
        window.forceProcessTableRefresh = false;
        renderProcesses(data.top_processes);
    }
}

function renderProcesses(processes) {
    const topCpu = processes.top_cpu_processes || [];
    const topRam = processes.top_ram_processes || [];

    const cpuBody = document.getElementById('topCpuTableBody');
    if (cpuBody && topCpu.length > 0) {
        cpuBody.innerHTML = topCpu.map(p => `
            <tr class="${p.pid === 99412 ? 'table-danger' : ''}" data-pid-row="${p.pid}">
                <td class="ps-4 font-monospace text-muted">${p.pid}</td>
                <td class="fw-semibold text-truncate" style="max-width: 140px;">${p.name}</td>
                <td><span class="badge ${p.cpu_percent >= 80 ? 'bg-danger' : 'bg-primary-subtle text-primary border border-primary-subtle'}">${p.cpu_percent}%</span></td>
                <td class="text-muted">${p.memory_percent}%</td>
                <td class="pe-4 text-end">
                    <button type="button" class="btn btn-danger btn-sm py-0 px-2 fw-semibold" onmousedown="killProcessPid(${p.pid}, this, event)" title="Terminate / Isolate Process PID ${p.pid}">
                        <i class="bi bi-x-octagon-fill me-1"></i>Kill
                    </button>
                </td>
            </tr>
        `).join('');
    }

    const ramBody = document.getElementById('topRamTableBody');
    if (ramBody && topRam.length > 0) {
        ramBody.innerHTML = topRam.map(p => `
            <tr class="${p.pid === 99412 ? 'table-danger' : ''}" data-pid-row="${p.pid}">
                <td class="ps-4 font-monospace text-muted">${p.pid}</td>
                <td class="fw-semibold text-truncate" style="max-width: 140px;">${p.name}</td>
                <td><span class="badge ${p.memory_percent >= 50 ? 'bg-danger' : 'bg-info-subtle text-info border border-info-subtle'}">${p.memory_percent}%</span></td>
                <td class="text-muted">${p.cpu_percent}%</td>
                <td class="pe-4 text-end">
                    <button type="button" class="btn btn-danger btn-sm py-0 px-2 fw-semibold" onmousedown="killProcessPid(${p.pid}, this, event)" title="Terminate / Isolate Process PID ${p.pid}">
                        <i class="bi bi-x-octagon-fill me-1"></i>Kill
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// ---------------- Active AI Self-Healing & Simulation Actions ----------------

async function executeAiRemediation(actionType = 'auto_heal', pid = null) {
    try {
        const response = await fetch('/api/remediate/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_type: actionType, pid: pid })
        });
        if (response.ok) {
            const data = await response.json();
            if (data.remediation_result) {
                showRemediationLog(data.remediation_result);
                showActionToast('AI Remediation Executed', data.remediation_result.summary, 'success');
            }
            window.forceProcessTableRefresh = true;
            await fetchMetrics();
            fetchSummary();
        }
    } catch (err) {
        console.error('Remediation error:', err);
        showActionToast('Action Error', 'Could not complete remediation action.', 'danger');
    }
}

async function triggerSimulation(simType) {
    try {
        const response = await fetch('/api/remediate/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: simType })
        });
        if (response.ok) {
            const data = await response.json();
            showActionToast(
                'Critical Incident Simulated',
                data.simulation?.description || 'Simulated critical resource spike active.',
                'danger'
            );
            window.forceProcessTableRefresh = true;
            await fetchMetrics();
            fetchSummary();
        }
    } catch (err) {
        console.error('Simulation error:', err);
    }
}

async function toggleAutoHeal(enabled) {
    try {
        await fetch('/api/remediate/toggle-auto', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enabled })
        });
        showActionToast(
            'Autonomous AI Healing',
            enabled ? 'Auto-Heal Mode ENABLED. Critical incidents will be resolved automatically.' : 'Auto-Heal Mode DISABLED.',
            enabled ? 'info' : 'secondary'
        );
    } catch (err) {
        console.error('Toggle Auto-Heal error:', err);
    }
}

function killProcessPid(pid, btnEl, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Killed';
    }
    // Immediately fade out and remove matching PID rows from both tables for instant visual removal
    document.querySelectorAll(`tr[data-pid-row="${pid}"]`).forEach(row => {
        row.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(12px)';
        setTimeout(() => {
            if (row && row.parentNode) {
                row.remove();
            }
        }, 150);
    });

    executeAiRemediation('kill_process', pid);
}

function showRemediationLog(record) {
    const container = document.getElementById('aiRemediationLogContainer');
    const titleEl = document.getElementById('aiRemediationTitle');
    const timeEl = document.getElementById('aiRemediationTime');
    const stepsEl = document.getElementById('aiRemediationSteps');

    if (!container) return;

    titleEl.textContent = `AI Self-Healing Executed (${record.triggered_by || 'System'})`;
    timeEl.textContent = record.timestamp || '';
    const steps = record.steps || [record.summary];
    stepsEl.innerHTML = steps.map(s => `<div>&bull; ${s}</div>`).join('');
    container.style.display = 'block';
}

function showActionToast(title, message, variant = 'success') {
    const container = document.getElementById('aiToastContainer');
    if (!container) return;

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${variant} border-0 show shadow-lg mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body small">
                <strong class="d-block mb-1"><i class="bi bi-robot me-1"></i>${title}</strong>
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;
    container.appendChild(toastEl);
    setTimeout(() => {
        if (toastEl && toastEl.parentNode) {
            toastEl.remove();
        }
    }, 4500);
}



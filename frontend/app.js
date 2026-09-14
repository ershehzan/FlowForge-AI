/* ═══════════════════════════════════════════════════════════
   FlowForge — Dashboard Application
   State management, API integration, Gantt rendering,
   disruption flows, and deterministic AI explanations.
   ═══════════════════════════════════════════════════════════ */

// ── API Base ──
const API = '';

// ── Application State ──
let state = {
  factory: null,
  baselineMetrics: null,
  disruptedMetrics: null,
  recoveryMetrics: null,
  baselineResilience: null,
  recoveryResilience: null,
  baselineSchedule: null,
  disruptedSchedule: null,
  recoverySchedule: null,
  currentSchedule: null,
  lastDisruption: null,
  failedMachines: new Set(),
  selectorMode: null, // 'failure' or 'recovery'
  selectedExcelFile: null,
};

// ── Job Color Map ──
const JOB_COLORS = [
  '#4F6D8E', '#5B7BA5', '#6B89B0', '#5A7493', '#4E6C88',
  '#577A9C', '#6589A8', '#4A6F92', '#5E82A0', '#527696',
  '#6090B0', '#4D7090',
];

// ═══════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
  setupDropzone();
  await initializeFactory();
}

async function initializeFactory() {
  setFactoryStatus('OPERATIONAL');
  try {
    const res = await fetch(`${API}/factory/initialize`, { method: 'POST' });
    const data = await res.json();

    state.baselineSchedule = data.baseline_schedule;
    state.currentSchedule = data.baseline_schedule;
    state.baselineMetrics = data.metrics;
    state.baselineResilience = data.resilience;
    state.disruptedMetrics = null;
    state.recoveryMetrics = null;
    state.recoveryResilience = null;
    state.lastDisruption = null;
    state.failedMachines = new Set();

    // Fetch full factory state for machine data
    const stateRes = await fetch(`${API}/factory/state`);
    state.factory = await stateRes.json();

    updateDataSourceBadge(state.factory ? state.factory.data_source : 'Demo Factory Data');
    updateKPIs(data.metrics, data.resilience);
    renderMachineStatusBar();
    renderGantt(data.baseline_schedule, 'baseline');
    resetPanels();
    hideExplanation();
    updateSimButtons();

  } catch (err) {
    console.error('Failed to initialize:', err);
  }
}


// ═══════════════════════════════════════════════════════════
// FACTORY STATUS
// ═══════════════════════════════════════════════════════════

function setFactoryStatus(status) {
  const el = document.getElementById('factoryStatus');
  const txt = document.getElementById('factoryStatusText');
  el.setAttribute('data-status', status);
  txt.textContent = status;
}

// ═══════════════════════════════════════════════════════════
// KPI UPDATES
// ═══════════════════════════════════════════════════════════

function updateKPIs(metrics, resilience, prevMetrics = null) {
  // Resilience
  const resEl = document.getElementById('kpiResilience');
  const resLabel = document.getElementById('kpiResilienceLabel');
  animateValue(resEl, resilience ? resilience.score : 0, '/100');
  resLabel.textContent = resilience ? resilience.label : '';

  // Machines
  const available = state.factory
    ? Object.values(state.factory.machines).filter(m => m.status === 'available').length
    : 6;
  const total = state.factory ? Object.keys(state.factory.machines).length : 6;
  document.getElementById('kpiMachines').textContent = `${available}/${total}`;

  // Late jobs
  const lateCard = document.getElementById('kpiLateCard');
  document.getElementById('kpiLateJobs').textContent = metrics ? metrics.late_jobs : '—';
  if (metrics && metrics.late_jobs === 0) {
    lateCard.classList.add('good');
  } else {
    lateCard.classList.remove('good');
  }
  if (prevMetrics && metrics) {
    showChange('kpiLateChange', prevMetrics.late_jobs, metrics.late_jobs, true);
  } else {
    document.getElementById('kpiLateChange').textContent = '';
  }

  // Makespan
  document.getElementById('kpiMakespan').textContent = metrics ? `${metrics.makespan}` : '—';
  document.getElementById('kpiMakespan').title = metrics ? `${metrics.makespan} min` : '';
  if (prevMetrics && metrics) {
    showChange('kpiMakespanChange', prevMetrics.makespan, metrics.makespan, true, ' min');
  } else {
    document.getElementById('kpiMakespanChange').textContent = metrics ? 'min' : '';
  }

  // Energy
  document.getElementById('kpiEnergy').textContent = metrics ? `${metrics.energy_kwh}` : '—';
  if (prevMetrics && metrics) {
    showChange('kpiEnergyChange', prevMetrics.energy_kwh, metrics.energy_kwh, true, ' kWh');
  } else {
    document.getElementById('kpiEnergyChange').textContent = metrics ? 'kWh' : '';
  }
}

function showChange(elementId, oldVal, newVal, lowerIsBetter, suffix = '') {
  const el = document.getElementById(elementId);
  if (oldVal === newVal) {
    el.textContent = `→ ${newVal}${suffix}`;
    el.className = 'kpi-change';
    return;
  }
  const diff = newVal - oldVal;
  const improved = lowerIsBetter ? diff < 0 : diff > 0;
  const sign = diff > 0 ? '+' : '';
  el.textContent = `${sign}${diff}${suffix} vs baseline`;
  el.className = `kpi-change ${improved ? 'improved' : 'worsened'}`;
}

function animateValue(el, target, suffix = '') {
  const start = parseInt(el.textContent) || 0;
  const diff = target - start;
  const duration = 600;
  const startTime = performance.now();

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + diff * eased);
    el.textContent = `${current}${suffix}`;
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

// ═══════════════════════════════════════════════════════════
// MACHINE STATUS BAR
// ═══════════════════════════════════════════════════════════

function renderMachineStatusBar() {
  const bar = document.getElementById('machineStatusBar');
  if (!state.factory) { bar.innerHTML = ''; return; }

  const machines = state.factory.machines;
  const schedule = state.currentSchedule || [];
  const makespan = schedule.length > 0
    ? Math.max(...schedule.map(a => a.start + a.duration))
    : 1;

  // Calculate utilization per machine
  const busy = {};
  schedule.forEach(a => {
    busy[a.machine] = (busy[a.machine] || 0) + a.duration;
  });

  let html = '';
  Object.entries(machines).forEach(([id, m]) => {
    const status = m.status === 'available' ? 'available' : 'failed';
    const util = m.status === 'available' && makespan > 0
      ? Math.round((busy[id] || 0) / makespan * 100)
      : 0;
    const utilStr = m.status === 'available' ? `<span class="chip-util">${util}%</span>` : '';
    html += `<div class="machine-status-chip ${status}">
      <span class="chip-dot"></span>${id}${utilStr}
    </div>`;
  });

  bar.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════
// GANTT CHART
// ═══════════════════════════════════════════════════════════

function renderGantt(schedule, mode = 'baseline', reassignedJobs = []) {
  const container = document.getElementById('ganttChart');
  if (!schedule || schedule.length === 0) {
    container.innerHTML = '<div class="panel-empty"><div class="icon">📋</div><div class="text">No schedule to display</div></div>';
    return;
  }

  const machines = state.factory
    ? Object.keys(state.factory.machines)
    : [...new Set(schedule.map(a => a.machine))].sort();

  const makespan = Math.max(...schedule.map(a => a.start + a.duration));
  const trackWidth = container.offsetWidth - 80;
  const pxPerUnit = trackWidth / Math.max(1, makespan);

  const reassignedSet = new Set(reassignedJobs);

  let html = '';

  machines.forEach(machineId => {
    const isFailed = state.failedMachines.has(machineId);
    const machineJobs = schedule.filter(a => a.machine === machineId);

    html += `<div class="gantt-row">
      <div class="gantt-machine-label ${isFailed ? 'failed' : ''}">
        <span class="machine-dot"></span>${machineId}
      </div>
      <div class="gantt-track">`;

    machineJobs.forEach(job => {
      const left = (job.start / makespan * 100).toFixed(2);
      const width = (job.duration / makespan * 100).toFixed(2);
      const completion = job.start + job.duration;
      const due = job.due || job.deadline || 999;
      const isLate = completion > due;
      const isReassigned = reassignedSet.has(job.job_id);
      const isAtRisk = !isLate && completion > due * 0.85;

      let cls = 'normal';
      if (isReassigned) cls = 'reassigned';
      else if (isLate) cls = 'late';
      else if (isAtRisk) cls = 'at-risk';

      const jobIdx = parseInt(job.job_id.replace('J', '')) - 1;
      const bg = isReassigned ? '' : isLate ? '' : isAtRisk ? '' : `background:${JOB_COLORS[jobIdx % JOB_COLORS.length]};border-color:${JOB_COLORS[jobIdx % JOB_COLORS.length]}88;`;

      html += `<div class="gantt-job ${cls}" style="left:${left}%;width:${width}%;${bg}"
        onmouseenter="showTooltip(event, '${job.job_id}', '${machineId}', ${job.start}, ${job.duration}, ${due}, ${completion}, '${cls}')"
        onmouseleave="hideTooltip()"
        >${job.job_id}</div>`;
    });

    // If machine is failed, show indicator
    if (isFailed && machineJobs.length === 0) {
      html += `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--color-danger);font-size:0.75rem;font-weight:600;gap:6px;opacity:0.7">
        🔴 FAILED
      </div>`;
    }

    html += `</div></div>`;
  });

  // Time axis
  html += `<div class="gantt-time-axis" style="position:relative;height:20px;">`;
  const steps = Math.min(8, Math.ceil(makespan / 10));
  for (let i = 0; i <= steps; i++) {
    const t = Math.round(makespan * i / steps);
    const pct = (i / steps * 100).toFixed(1);
    html += `<span class="gantt-time-label" style="left:${pct}%">${t}</span>`;
  }
  html += `</div>`;

  container.innerHTML = html;
  container.classList.add('animate-in');
}

function showTooltip(event, jobId, machine, start, duration, due, completion, cls) {
  const tip = document.getElementById('ganttTooltip');
  const title = document.getElementById('tooltipTitle');
  const body = document.getElementById('tooltipBody');

  title.textContent = `Job ${jobId}`;

  const status = cls === 'reassigned' ? '🔵 Reassigned' :
                 cls === 'late' ? '🔴 Late' :
                 cls === 'at-risk' ? '🟡 At Risk' : '✅ On Time';

  body.innerHTML = `
    <div class="gantt-tooltip-row"><span>Machine</span><span>${machine}</span></div>
    <div class="gantt-tooltip-row"><span>Start</span><span>${start} min</span></div>
    <div class="gantt-tooltip-row"><span>Duration</span><span>${duration} min</span></div>
    <div class="gantt-tooltip-row"><span>Deadline</span><span>${due} min</span></div>
    <div class="gantt-tooltip-row"><span>Completes</span><span>${completion} min</span></div>
    <div class="gantt-tooltip-row"><span>Status</span><span>${status}</span></div>
  `;

  tip.style.left = (event.clientX + 16) + 'px';
  tip.style.top = (event.clientY - 8) + 'px';
  tip.classList.add('visible');
}

function hideTooltip() {
  document.getElementById('ganttTooltip').classList.remove('visible');
}

// ═══════════════════════════════════════════════════════════
// DISRUPTION FLOWS
// ═══════════════════════════════════════════════════════════

// ── Machine Selector ──
function showMachineSelector(mode) {
  state.selectorMode = mode;
  const selector = document.getElementById('machineSelector');
  const grid = document.getElementById('machineGrid');
  const title = document.getElementById('machineSelectorTitle');

  title.textContent = mode === 'failure' ? 'Select Machine to Fail' : 'Select Machine to Recover';

  const machines = state.factory ? Object.entries(state.factory.machines) : [];
  let html = '';
  machines.forEach(([id, m]) => {
    const isAvailable = m.status === 'available';
    if (mode === 'failure') {
      html += `<button class="machine-btn ${isAvailable ? '' : 'disabled'}" onclick="executeMachineAction('${id}')">${id}</button>`;
    } else {
      html += `<button class="machine-btn ${!isAvailable ? '' : 'disabled'}" onclick="executeMachineAction('${id}')">${id}</button>`;
    }
  });
  grid.innerHTML = html;
  selector.classList.add('visible');
}

function hideMachineSelector() {
  document.getElementById('machineSelector').classList.remove('visible');
}

async function executeMachineAction(machineId) {
  hideMachineSelector();

  if (state.selectorMode === 'failure') {
    await triggerDisruption({ type: 'machine_failure', machine_id: machineId });
  } else {
    await triggerDisruption({ type: 'machine_recovery', machine_id: machineId });
  }
}

// ── Disruption Triggers ──
async function triggerUrgentJob() {
  const existingIds = state.factory
    ? state.factory.jobs.map(j => parseInt(j.job_id.replace('J', '')))
    : [12];
  const nextId = Math.max(...existingIds) + 1;

  await triggerDisruption({
    type: 'urgent_job',
    job_id: `J${nextId}`,
    duration: 35 + Math.floor(Math.random() * 20),
    deadline: 100 + Math.floor(Math.random() * 60),
    priority: 5,
  });
}

async function triggerDeadlineChange() {
  // Pick a random active job and tighten its deadline
  const jobs = state.factory ? state.factory.jobs.filter(j => j.status !== 'cancelled') : [];
  if (jobs.length === 0) return;
  const job = jobs[Math.floor(Math.random() * jobs.length)];
  const newDeadline = Math.max(20, Math.floor(job.deadline * 0.5));

  await triggerDisruption({
    type: 'deadline_change',
    job_id: job.job_id,
    new_deadline: newDeadline,
  });
}

async function triggerJobCancellation() {
  const jobs = state.factory ? state.factory.jobs.filter(j => j.status !== 'cancelled') : [];
  if (jobs.length === 0) return;
  const job = jobs[Math.floor(Math.random() * jobs.length)];

  await triggerDisruption({
    type: 'job_cancellation',
    job_id: job.job_id,
  });
}

async function triggerMultipleFailures() {
  const available = state.factory
    ? Object.entries(state.factory.machines).filter(([_, m]) => m.status === 'available').map(([id]) => id)
    : [];
  if (available.length < 2) return;

  // Fail two random machines
  const shuffled = available.sort(() => Math.random() - 0.5);
  await triggerDisruption({ type: 'machine_failure', machine_id: shuffled[0] });
  // Small delay for visual effect
  await new Promise(r => setTimeout(r, 300));
  await triggerDisruption({ type: 'machine_failure', machine_id: shuffled[1] });
}

// ── Central Disruption Handler ──
async function triggerDisruption(disruption) {
  setFactoryStatus('DISRUPTED');
  disableSimButtons(true);

  try {
    const res = await fetch(`${API}/disruptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(disruption),
    });
    const data = await res.json();

    if (data.error) {
      console.error('Disruption error:', data.error);
      setFactoryStatus('OPERATIONAL');
      disableSimButtons(false);
      return;
    }

    state.lastDisruption = data;

    // Track failed machines
    if (disruption.type === 'machine_failure') {
      state.failedMachines.add(disruption.machine_id);
    } else if (disruption.type === 'machine_recovery') {
      state.failedMachines.delete(disruption.machine_id);
    }

    // Show DISRUPTED status briefly
    setFactoryStatus('DISRUPTED');
    updateWhatChanged(data);

    // Animate to RECOVERING
    await sleep(400);
    setFactoryStatus('RECOVERING');

    // Update state
    await sleep(400);

    // Refresh full factory state
    const stateRes = await fetch(`${API}/factory/state`);
    state.factory = await stateRes.json();

    state.disruptedMetrics = data.metrics.disrupted;
    state.recoveryMetrics = data.metrics.recovery;
    state.recoveryResilience = data.resilience.recovery;
    state.recoverySchedule = data.schedules.recovery;
    state.currentSchedule = data.schedules.recovery;

    // Find reassigned jobs (jobs that moved machines)
    const reassigned = findReassignedJobs(
      state.baselineSchedule, data.schedules.recovery
    );

    // Update everything
    setFactoryStatus('RECOVERED');
    updateKPIs(data.metrics.recovery, data.resilience.recovery, state.baselineMetrics);
    renderMachineStatusBar();
    renderGantt(data.schedules.recovery, 'recovery', reassigned);
    updateComparison(data.metrics.baseline, data.metrics.disrupted, data.metrics.recovery, data.resilience);
    generateExplanation(data, disruption, reassigned);
    updateSimButtons();
    updateRecoveryStatus(data);

  } catch (err) {
    console.error('Disruption failed:', err);
    setFactoryStatus('OPERATIONAL');
  }

  disableSimButtons(false);
}

function findReassignedJobs(baseline, recovery) {
  if (!baseline || !recovery) return [];
  const baseMap = {};
  baseline.forEach(a => { baseMap[a.job_id] = a.machine; });

  return recovery
    .filter(a => baseMap[a.job_id] && baseMap[a.job_id] !== a.machine)
    .map(a => a.job_id);
}

// ═══════════════════════════════════════════════════════════
// WHAT CHANGED PANEL
// ═══════════════════════════════════════════════════════════

function updateWhatChanged(data) {
  const empty = document.getElementById('whatChangedEmpty');
  const content = document.getElementById('whatChangedContent');
  empty.style.display = 'none';
  content.style.display = 'block';

  const d = data.disruption;
  const impact = data.impact;

  let iconClass = 'failure';
  let icon = '🔴';
  let title = 'DISRUPTION';

  switch (d.type) {
    case 'machine_failure':
      title = `MACHINE FAILURE — ${d.machine_id}`;
      break;
    case 'machine_recovery':
      icon = '🟢'; iconClass = 'recovery';
      title = `MACHINE RECOVERED — ${d.machine_id}`;
      break;
    case 'urgent_job':
      icon = '⚡'; iconClass = 'urgent';
      title = `URGENT ORDER — ${d.job_id}`;
      break;
    case 'job_cancellation':
      icon = '❌'; iconClass = 'failure';
      title = `JOB CANCELLED — ${d.job_id}`;
      break;
    case 'deadline_change':
      icon = '⏰'; iconClass = 'urgent';
      title = `DEADLINE CHANGED — ${d.job_id}`;
      break;
  }

  let impactHtml = '';
  if (impact.affected_job_count !== undefined) {
    impactHtml += `<li class="impact-item"><span class="dot"></span>${impact.affected_job_count} jobs affected</li>`;
  }
  if (impact.deadline_risks !== undefined && impact.deadline_risks > 0) {
    impactHtml += `<li class="impact-item"><span class="dot"></span>${impact.deadline_risks} deadline risks</li>`;
  }
  if (impact.description) {
    impactHtml += `<li class="impact-item"><span class="dot"></span>${impact.description}</li>`;
  }
  if (data.affected_jobs && data.affected_jobs.length > 0) {
    impactHtml += `<li class="impact-item"><span class="dot"></span>Affected: ${data.affected_jobs.join(', ')}</li>`;
  }

  content.innerHTML = `
    <div class="disruption-header ${iconClass}">${icon} ${title}</div>
    <ul class="impact-list">${impactHtml}</ul>
    <div class="recovery-status processing" id="recoveryIndicator">
      <span class="spinner"></span> Generating recovery schedule...
    </div>
  `;

  content.classList.add('animate-in');
}

function updateRecoveryStatus(data) {
  const indicator = document.getElementById('recoveryIndicator');
  if (!indicator) return;

  const recoveryJobs = data.schedules.recovery ? data.schedules.recovery.length : 0;
  const time = data.recovery_time_seconds ? `${(data.recovery_time_seconds * 1000).toFixed(0)}ms` : '';

  indicator.className = 'recovery-status complete';
  indicator.innerHTML = `✓ Recovery complete · ${recoveryJobs} jobs scheduled · ${time}`;
}

// ═══════════════════════════════════════════════════════════
// BEFORE vs AFTER COMPARISON
// ═══════════════════════════════════════════════════════════

function updateComparison(baseline, disrupted, recovery, resilience) {
  const empty = document.getElementById('comparisonEmpty');
  const content = document.getElementById('comparisonContent');
  empty.style.display = 'none';
  content.style.display = 'block';

  const baseRes = resilience.baseline ? resilience.baseline.score : '—';
  const recRes = resilience.recovery ? resilience.recovery.score : '—';

  const rows = [
    { label: 'Makespan', base: baseline.makespan + ' min', dis: (disrupted.makespan || '—') + ' min', rec: recovery.makespan + ' min' },
    { label: 'Late Jobs', base: baseline.late_jobs, dis: disrupted.late_jobs !== undefined ? disrupted.late_jobs : '—', rec: recovery.late_jobs },
    { label: 'Energy', base: baseline.energy_kwh + ' kWh', dis: (disrupted.energy_kwh || '—') + ' kWh', rec: recovery.energy_kwh + ' kWh' },
    { label: 'Utilization', base: baseline.average_utilization + '%', dis: (disrupted.average_utilization || '—') + '%', rec: recovery.average_utilization + '%' },
    { label: 'Resilience', base: baseRes, dis: '—', rec: recRes },
  ];

  let html = `<table class="comparison-table">
    <thead><tr>
      <th>Metric</th>
      <th>Baseline</th>
      <th>Disrupted</th>
      <th>FlowForge</th>
    </tr></thead><tbody>`;

  rows.forEach(r => {
    html += `<tr>
      <td>${r.label}</td>
      <td class="value-baseline">${r.base}</td>
      <td class="value-disrupted">${r.dis}</td>
      <td class="value-recovery">${r.rec}</td>
    </tr>`;
  });

  html += `</tbody></table>`;
  content.innerHTML = html;
  content.classList.add('animate-in');
}

// ═══════════════════════════════════════════════════════════
// AI EXPLANATION (Deterministic template-based)
// ═══════════════════════════════════════════════════════════

function generateExplanation(data, disruption, reassignedJobs) {
  const panel = document.getElementById('explanationPanel');
  const contentEl = document.getElementById('explanationContent');
  const factsEl = document.getElementById('explanationFacts');
  panel.style.display = 'block';

  const baseline = data.metrics.baseline;
  const recovery = data.metrics.recovery;

  let explanation = '';
  let facts = '';

  switch (disruption.type) {
    case 'machine_failure': {
      const mid = disruption.machine_id;
      const affected = data.affected_jobs || [];
      const energyMap = state.factory ? state.factory.machines : {};
      const machineEnergy = energyMap[mid] ? energyMap[mid].energy_kwh_per_hour : '?';

      // Find where jobs were reassigned to
      const movements = [];
      if (state.baselineSchedule && data.schedules.recovery) {
        const baseMap = {};
        state.baselineSchedule.forEach(a => { baseMap[a.job_id] = a.machine; });
        data.schedules.recovery.forEach(a => {
          if (baseMap[a.job_id] && baseMap[a.job_id] !== a.machine) {
            movements.push({ job: a.job_id, from: baseMap[a.job_id], to: a.machine });
          }
        });
      }

      explanation = `<strong>${mid}</strong> became unavailable (${machineEnergy} kWh/hr capacity removed). `;

      if (movements.length > 0) {
        const mainMove = movements[0];
        explanation += `<strong>${mainMove.job}</strong> was reassigned from <strong>${mainMove.from}</strong> to <strong>${mainMove.to}</strong>. `;

        if (movements.length > 1) {
          explanation += `${movements.length - 1} additional job${movements.length > 2 ? 's were' : ' was'} redistributed across available machines. `;
        }
      }

      const makespanDiff = recovery.makespan - baseline.makespan;
      const energyDiff = recovery.energy_kwh - baseline.energy_kwh;
      const energyPct = baseline.energy_kwh > 0 ? ((energyDiff / baseline.energy_kwh) * 100).toFixed(1) : 0;

      if (recovery.late_jobs === 0) {
        explanation += `All deadlines are protected in the recovery schedule. `;
      }
      if (energyDiff < 0) {
        explanation += `Energy consumption decreased by ${Math.abs(energyPct)}% as jobs shifted to more efficient machines.`;
      } else if (energyDiff > 0) {
        explanation += `Energy consumption increased by ${energyPct}% as a trade-off for deadline protection.`;
      }

      // Facts
      if (movements.length > 0) {
        facts = movements.slice(0, 3).map(m =>
          `<div class="explanation-fact">
            <span class="explanation-fact-label">${m.job}</span>
            <span class="explanation-fact-value">${m.from} → ${m.to}</span>
          </div>`
        ).join('');
      }

      facts += `<div class="explanation-fact">
        <span class="explanation-fact-label">Makespan Δ</span>
        <span class="explanation-fact-value">${makespanDiff > 0 ? '+' : ''}${makespanDiff} min</span>
      </div>`;
      facts += `<div class="explanation-fact">
        <span class="explanation-fact-label">Energy Δ</span>
        <span class="explanation-fact-value">${energyDiff > 0 ? '+' : ''}${energyDiff.toFixed(1)} kWh (${energyPct}%)</span>
      </div>`;
      break;
    }

    case 'urgent_job': {
      const jid = disruption.job_id;
      explanation = `Urgent job <strong>${jid}</strong> (duration: ${disruption.duration} min, deadline: ${disruption.deadline} min) `;
      explanation += `was inserted into the production schedule. FlowForge re-optimized all job assignments to accommodate the new job while protecting existing deadlines.`;

      facts = `<div class="explanation-fact">
        <span class="explanation-fact-label">New Job</span>
        <span class="explanation-fact-value">${jid}</span>
      </div>
      <div class="explanation-fact">
        <span class="explanation-fact-label">Duration</span>
        <span class="explanation-fact-value">${disruption.duration} min</span>
      </div>
      <div class="explanation-fact">
        <span class="explanation-fact-label">Deadline</span>
        <span class="explanation-fact-value">${disruption.deadline} min</span>
      </div>`;
      break;
    }

    case 'job_cancellation': {
      explanation = `Job <strong>${disruption.job_id}</strong> was cancelled, releasing capacity. FlowForge re-optimized the schedule to take advantage of the freed capacity, potentially improving makespan and energy consumption.`;

      const energyDiff = recovery.energy_kwh - baseline.energy_kwh;
      facts = `<div class="explanation-fact">
        <span class="explanation-fact-label">Cancelled</span>
        <span class="explanation-fact-value">${disruption.job_id}</span>
      </div>
      <div class="explanation-fact">
        <span class="explanation-fact-label">Energy Δ</span>
        <span class="explanation-fact-value">${energyDiff > 0 ? '+' : ''}${energyDiff.toFixed(1)} kWh</span>
      </div>`;
      break;
    }

    case 'deadline_change': {
      explanation = `The deadline for <strong>${disruption.job_id}</strong> was changed to <strong>${disruption.new_deadline} min</strong>. FlowForge re-prioritized the schedule to protect this tighter constraint.`;

      facts = `<div class="explanation-fact">
        <span class="explanation-fact-label">Job</span>
        <span class="explanation-fact-value">${disruption.job_id}</span>
      </div>
      <div class="explanation-fact">
        <span class="explanation-fact-label">New Deadline</span>
        <span class="explanation-fact-value">${disruption.new_deadline} min</span>
      </div>`;
      break;
    }

    case 'machine_recovery': {
      explanation = `Machine <strong>${disruption.machine_id}</strong> has been restored. FlowForge re-optimized the schedule to take advantage of the restored capacity, potentially improving performance.`;

      facts = `<div class="explanation-fact">
        <span class="explanation-fact-label">Recovered</span>
        <span class="explanation-fact-value">${disruption.machine_id}</span>
      </div>`;
      break;
    }

    default:
      explanation = 'FlowForge automatically generated a recovery schedule.';
  }

  contentEl.innerHTML = explanation;
  factsEl.innerHTML = facts;
  panel.classList.add('animate-in');
}

function hideExplanation() {
  document.getElementById('explanationPanel').style.display = 'none';
}

// ═══════════════════════════════════════════════════════════
// RESET & PANEL MANAGEMENT
// ═══════════════════════════════════════════════════════════

async function resetFactory() {
  try {
    await fetch(`${API}/factory/reset`, { method: 'POST' });
    state.failedMachines = new Set();
    await initializeFactory();
  } catch (err) {
    console.error('Reset failed:', err);
  }
}

function resetPanels() {
  document.getElementById('whatChangedEmpty').style.display = '';
  document.getElementById('whatChangedContent').style.display = 'none';
  document.getElementById('comparisonEmpty').style.display = '';
  document.getElementById('comparisonContent').style.display = 'none';
}

// ═══════════════════════════════════════════════════════════
// SIMULATOR CONTROLS
// ═══════════════════════════════════════════════════════════

function updateSimButtons() {
  const hasFailed = state.failedMachines.size > 0;
  const recoverBtn = document.getElementById('btnRecoverMachine');
  recoverBtn.style.display = hasFailed ? '' : 'none';
}

function disableSimButtons(disabled) {
  document.querySelectorAll('.sim-btn').forEach(btn => {
    btn.disabled = disabled;
  });
}

// ── Utility ──
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ═══════════════════════════════════════════════════════════
// DATA SOURCE & EXCEL UPLOADER
// ═══════════════════════════════════════════════════════════

function updateDataSourceBadge(dataSource) {
  const badgeText = document.getElementById('dataSourceText');
  const demoBtn = document.getElementById('btnUseDemoData');

  const text = dataSource || 'Demo Factory Data';
  badgeText.textContent = text.replace('uploaded/', '').replace('examples/', '');

  if (text.toLowerCase().includes('demo')) {
    demoBtn.style.display = 'none';
  } else {
    demoBtn.style.display = 'inline-block';
  }
}

function openExcelModal() {
  document.getElementById('excelModalOverlay').style.display = 'flex';
  resetExcelModalState();
}

function closeExcelModal() {
  document.getElementById('excelModalOverlay').style.display = 'none';
}

function resetExcelModalState() {
  state.selectedExcelFile = null;
  document.getElementById('excelFileInput').value = '';
  document.getElementById('fileSelectedInfo').style.display = 'none';
  document.getElementById('excelErrorBox').style.display = 'none';
  document.getElementById('excelPreviewBox').style.display = 'none';
  document.getElementById('uploadLoading').style.display = 'none';
  document.getElementById('btnConfirmExcel').disabled = true;
}

function setupDropzone() {
  const dropzone = document.getElementById('dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      processSelectedFile(files[0]);
    }
  });
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    processSelectedFile(files[0]);
  }
}

function processSelectedFile(file) {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
  if (ext !== '.xlsx' && ext !== '.xls') {
    showExcelErrors(['• Unsupported file format. Please upload an Excel workbook (.xlsx or .xls).']);
    return;
  }

  state.selectedExcelFile = file;
  document.getElementById('selectedFileName').textContent = file.name;
  document.getElementById('selectedFileSize').textContent = (file.size / 1024).toFixed(1) + ' KB';
  document.getElementById('fileSelectedInfo').style.display = 'block';
  document.getElementById('excelErrorBox').style.display = 'none';
  document.getElementById('btnConfirmExcel').disabled = false;
}

function showExcelErrors(errorMessages) {
  const box = document.getElementById('excelErrorBox');
  const list = document.getElementById('excelErrorList');
  list.innerHTML = errorMessages.map(msg => `<div>${msg}</div>`).join('');
  box.style.display = 'block';
  document.getElementById('excelPreviewBox').style.display = 'none';
  document.getElementById('btnConfirmExcel').disabled = true;
}

async function uploadAndOptimize() {
  if (!state.selectedExcelFile) return;

  const loadingEl = document.getElementById('uploadLoading');
  const confirmBtn = document.getElementById('btnConfirmExcel');

  loadingEl.style.display = 'flex';
  confirmBtn.disabled = true;
  document.getElementById('excelErrorBox').style.display = 'none';

  const formData = new FormData();
  formData.append('file', state.selectedExcelFile);

  try {
    const res = await fetch(`${API}/factory/upload`, {
      method: 'POST',
      body: formData,
    });

    const data = await res.json();
    loadingEl.style.display = 'none';

    if (!res.ok || !data.success) {
      showExcelErrors(data.error_messages || ['• Validation error processing Excel workbook.']);
      return;
    }

    // Success! Update Application State
    state.baselineSchedule = data.baseline_schedule;
    state.currentSchedule = data.baseline_schedule;
    state.baselineMetrics = data.metrics;
    state.baselineResilience = data.resilience;
    state.disruptedMetrics = null;
    state.recoveryMetrics = null;
    state.recoveryResilience = null;
    state.lastDisruption = null;
    state.failedMachines = new Set();
    state.factory = data.factory_state;

    // Show Preview Card brief moment before closing
    document.getElementById('prevMachines').textContent = data.summary.machines_count;
    document.getElementById('prevJobs').textContent = data.summary.jobs_count;
    document.getElementById('prevHighPriority').textContent = data.summary.high_priority_jobs;
    document.getElementById('prevEnergy').textContent = data.summary.total_energy_capacity_kwh + ' kWh';
    document.getElementById('excelPreviewBox').style.display = 'block';

    updateDataSourceBadge(data.data_source);
    updateKPIs(data.metrics, data.resilience);
    renderMachineStatusBar();
    renderGantt(data.baseline_schedule, 'baseline');
    resetPanels();
    hideExplanation();
    updateSimButtons();

    await sleep(800);
    closeExcelModal();

  } catch (err) {
    loadingEl.style.display = 'none';
    showExcelErrors([`• Connection error: ${err.message}`]);
  }
}

async function useDemoData() {
  await initializeFactory();
}


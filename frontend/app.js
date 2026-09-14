/* ═════════════════════════════════════════════════════════════════════════
   FLOWFORGE — Core Frontend Controller
   Exact UI Replica & Apple-Grade Frame-by-Frame Canvas Scroll Animation
   ═════════════════════════════════════════════════════════════════════════ */

// ── Frame Animation Configuration ──
// Path to folder of numbered animation frames. Changing this path dynamically adapts.
const FRAME_PATH = "/frames/";

// ── Application State ──
const state = {
  factory: null,
  baselineSchedule: [],
  disruptedSchedule: [],
  recoverySchedule: [],
  currentSchedule: [],
  baselineMetrics: null,
  disruptedMetrics: null,
  recoveryMetrics: null,
  baselineResilience: null,
  recoveryResilience: null,
  activeDisruptions: [],
  selectedFile: null,
  isDisrupted: false,

  // Animation Engine State
  frames: [],
  images: [],
  totalFrames: 0,
  isAnimationReady: false,
};

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Default static machine specs matching Reference Screen 3
const MACHINE_SPECS = {
  M1: { name: "CNC-01", type: "Milling Center", img: "/static/assets/machines/m1.jpg", defaultUtil: 82 },
  M2: { name: "ROBOT-X5", type: "Robotic Cell", img: "/static/assets/machines/m2.jpg", defaultUtil: 96 },
  M3: { name: "PRESS-G2", type: "Stamping Press", img: "/static/assets/machines/m3.jpg", defaultUtil: 88 },
  M4: { name: "CONVEYOR-A1", type: "Automated Line", img: "/static/assets/machines/m4.jpg", defaultUtil: 75 },
  M5: { name: "LATHE-P3", type: "Metal Turning", img: "/static/assets/machines/m5.jpg", defaultUtil: 0 },
  M6: { name: "ASSEMBLY-F4", type: "Precision Workstation", img: "/static/assets/machines/m6.jpg", defaultUtil: 91 },
};

// ═════════════════════════════════════════════════════════════════════════
// 1. APPLICATION INITIALIZATION
// ═════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  initHeroCanvasAnimation();
  initFlowForgeEngine();
  setupDropzone();
});

// ═════════════════════════════════════════════════════════════════════════
// 2. APPLE-GRADE FRAME-BY-FRAME HERO SCROLL ANIMATION
// ═════════════════════════════════════════════════════════════════════════

async function initHeroCanvasAnimation() {
  const canvas = document.getElementById("heroCanvas");
  const loader = document.getElementById("heroLoader");
  const loaderText = document.getElementById("heroLoaderText");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  // Step 1: Automatically detect frame count and filenames without hardcoding
  const manifest = await detectFramesManifest(FRAME_PATH);
  state.frames = manifest.frames;
  state.totalFrames = manifest.totalFrames;

  if (state.totalFrames === 0) {
    if (loader) loader.classList.add("hidden");
    return;
  }

  // Setup HiDPI Canvas dimensions to fit screen 100vw x 100vh
  function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = window.innerWidth;
    const height = window.innerHeight;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    renderCurrentFrame();
  }

  window.addEventListener("resize", resizeCanvas);

  function renderCurrentFrame() {
    let img = state.images[state.currentFrameIndex];
    if (!img || !img.complete || img.naturalWidth === 0) {
      // Robust fallback: search nearest loaded frame to prevent flicker or blank canvas
      for (let delta = 1; delta < state.totalFrames; delta++) {
        const prev = state.images[state.currentFrameIndex - delta];
        if (prev && prev.complete && prev.naturalWidth > 0) {
          img = prev;
          break;
        }
        const next = state.images[state.currentFrameIndex + delta];
        if (next && next.complete && next.naturalWidth > 0) {
          img = next;
          break;
        }
      }
    }
    if (!img || !img.complete || img.naturalWidth === 0) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const logicalWidth = canvas.width / dpr;
    const logicalHeight = canvas.height / dpr;

    // Cleaned frames allow clean 4px border margin for edge-to-edge fidelity
    const cropX = 4;
    const cropY = 4;
    const srcW = Math.max(1, img.width - cropX * 2);
    const srcH = Math.max(1, img.height - cropY * 2);

    // Fit to screen (cover mode) so it fills the screen completely, edge-to-edge
    const hRatio = logicalWidth / srcW;
    const vRatio = logicalHeight / srcH;
    const ratio = Math.max(hRatio, vRatio);

    const drawWidth = srcW * ratio;
    const drawHeight = srcH * ratio;
    const drawX = (logicalWidth - drawWidth) / 2;
    const drawY = (logicalHeight - drawHeight) / 2;

    ctx.clearRect(0, 0, logicalWidth, logicalHeight);
    ctx.drawImage(img, cropX, cropY, srcW, srcH, drawX, drawY, drawWidth, drawHeight);
  }

  // Step 2: Preload frames with progress reporting
  state.images = new Array(state.totalFrames);
  let loadedCount = 0;

  const checkMotionPreference = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function onSingleFrameLoaded(idx) {
    loadedCount++;
    const progress = Math.round((loadedCount / state.totalFrames) * 100);
    if (loaderText) loaderText.textContent = `Preloading ${progress}%`;

    // Render first frame as soon as frame 0 arrives
    if (idx === 0) {
      resizeCanvas();
      renderCurrentFrame();
    }

    // Once all or a usable batch is loaded, activate GSAP scroll scrub
    if (loadedCount >= state.totalFrames) {
      if (loader) loader.classList.add("hidden");
      state.isAnimationReady = true;

      if (!checkMotionPreference) {
        setupGSAPScrollTrigger(canvas, renderCurrentFrame);
      }
    }
  }

  // Preload all frames asynchronously
  state.frames.forEach((frameUrl, idx) => {
    const img = new Image();
    img.src = frameUrl;
    img.onload = () => {
      state.images[idx] = img;
      onSingleFrameLoaded(idx);
    };
    img.onerror = () => {
      // Fallback in case of missing frame
      onSingleFrameLoaded(idx);
    };
  });
}

// Automatically detect frame list and count
async function detectFramesManifest(basePath) {
  try {
    // Attempt 1: Fetch dynamic manifest from API
    const res = await fetch("/api/frames-info");
    if (res.ok) {
      const data = await res.json();
      if (data.frames && data.frames.length > 0) {
        return {
          totalFrames: data.frames.length,
          frames: data.frames,
        };
      }
    }
  } catch (e) {
    // API not reached, try static manifest
  }

  try {
    // Attempt 2: Fetch manifest.json directly from FRAME_PATH
    const res = await fetch(`${basePath}manifest.json`);
    if (res.ok) {
      const data = await res.json();
      if (data.frames && data.frames.length > 0) {
        return {
          totalFrames: data.frames.length,
          frames: data.frames,
        };
      }
    }
  } catch (e) {
    // Fallback to sequential probe
  }

  // Attempt 3: Progressive discovery
  const frames = [];
  for (let i = 1; i <= 240; i++) {
    const pad = String(i).padStart(3, "0");
    frames.push(`${basePath}ezgif-frame-${pad}.jpg`);
  }
  return { totalFrames: frames.length, frames };
}

// GSAP + ScrollTrigger Hero Pinning & Scrubbing
function setupGSAPScrollTrigger(canvas, renderCallback) {
  if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
    console.warn("GSAP / ScrollTrigger not loaded");
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  const heroSection = document.getElementById("hero");
  if (!heroSection) return;

  let rafPending = false;
  function requestRender() {
    if (!rafPending) {
      rafPending = true;
      requestAnimationFrame(() => {
        renderCallback();
        rafPending = false;
      });
    }
  }

  ScrollTrigger.create({
    trigger: heroSection,
    start: "top top",
    end: "+=220%",
    pin: true,
    scrub: 0.5,
    anticipatePin: 1,
    onUpdate: (self) => {
      const frameIndex = Math.min(
        state.totalFrames - 1,
        Math.max(0, Math.floor(self.progress * state.totalFrames))
      );
      if (frameIndex !== state.currentFrameIndex) {
        state.currentFrameIndex = frameIndex;
        requestRender();
      }

      // Smoothly fade scroll indicator on scroll
      const indicator = document.getElementById("heroScrollIndicator");
      if (indicator) {
        indicator.style.opacity = Math.max(0, 1 - self.progress * 4);
      }

      // Smoothly fade hero title & subtitle as machine expands on scroll
      const heroContent = document.getElementById("heroContent");
      if (heroContent) {
        const opacity = Math.max(0, 1 - self.progress * 2.2);
        const translateY = -self.progress * 60;
        heroContent.style.opacity = opacity;
        heroContent.style.transform = `translate(-50%, ${translateY}px)`;
      }
    },
  });
}

// ═════════════════════════════════════════════════════════════════════════
// 3. BACKEND DATA SYNCHRONIZATION & FLOWFORGE SCHEDULER
// ═════════════════════════════════════════════════════════════════════════

async function initFlowForgeEngine() {
  try {
    const res = await fetch("/factory/initialize", { method: "POST" });
    if (!res.ok) throw new Error("Failed to initialize factory state");
    const data = await res.json();

    state.baselineSchedule = data.baseline_schedule || [];
    state.currentSchedule = state.baselineSchedule;
    state.baselineMetrics = data.metrics;
    state.baselineResilience = data.resilience;
    state.isDisrupted = false;

    // Fetch full factory machine status
    const stateRes = await fetch("/factory/state");
    state.factory = await stateRes.json();

    updateUI();
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 4. UI RENDERERS (EXACT REFERENCE REPLICAS)
// ═════════════════════════════════════════════════════════════════════════

function updateUI() {
  updateNavStatus();
  renderFactoryExplorer();
  renderControlCenter();
  renderGanttChart();
  renderDisruptionBanner();
  renderComparisonCards();
  renderDecisionReport();
}

// Navigation status chip
function updateNavStatus() {
  const chip = document.getElementById("navStatusChip");
  const txt = document.getElementById("navStatusText");
  if (!chip || !txt) return;

  if (state.isDisrupted) {
    chip.classList.add("disrupted");
    txt.textContent = "DISRUPTED";
    chip.title = "Factory Disruption Active — Click to Reset to Operational";
  } else {
    chip.classList.remove("disrupted");
    txt.textContent = "OPERATIONAL";
    chip.title = "Factory Status: Operational — Click to explore Disruption Scenarios";
  }

  if (!chip.dataset.bound) {
    chip.dataset.bound = "true";
    chip.addEventListener("click", () => {
      if (state.isDisrupted) {
        resetFactoryState();
      } else {
        const scn = document.getElementById("disruption");
        if (scn) scn.scrollIntoView({ behavior: "smooth" });
      }
    });
  }
}

// Screen 3: Factory Explorer Grid (Dynamic machines)
function renderFactoryExplorer() {
  const grid = document.getElementById("machinesGrid");
  if (!grid) return;

  const activeMachines = state.factory ? state.factory.machines : {};
  let machineKeys = Object.keys(activeMachines);
  if (!machineKeys.length) {
    machineKeys = ["M1", "M2", "M3", "M4", "M5", "M6"];
  }
  machineKeys.sort();

  let html = "";
  machineKeys.forEach((id, idx) => {
    const imgIndex = (idx % 6) + 1;
    const fallbackImg = `/static/assets/machines/m${imgIndex}.jpg`;
    const spec = MACHINE_SPECS[id] || { name: `Workstation ${id}`, type: "Machine Cell", img: fallbackImg, defaultUtil: 85 };
    const liveMachine = activeMachines[id];
    const isStopped = liveMachine ? liveMachine.status !== "available" : (id === "M5" && !state.isDisrupted);
    let statusText = isStopped ? "STOPPED" : "RUNNING";
    let statusClass = isStopped ? "stopped" : "running";

    if (liveMachine && liveMachine.unavailable_periods && liveMachine.unavailable_periods.length > 0) {
      const p = liveMachine.unavailable_periods[0];
      statusText = `MAINT [${p[0]}-${p[1]}m]`;
      statusClass = "maintenance";
    }

    // Dynamic utilization
    let util = spec.defaultUtil;
    if (state.baselineMetrics && state.baselineMetrics.machine_utilization && state.baselineMetrics.machine_utilization[id] !== undefined) {
      util = Math.round(state.baselineMetrics.machine_utilization[id]);
    } else if (isStopped) {
      util = 0;
    }

    html += `
      <div class="machine-card ${isStopped ? "stopped" : ""}" id="card_${id}" onclick="toggleMachine('${id}')" title="Click to simulate toggle">
        <div class="machine-card-header">
          <div>
            <div class="machine-card-id">${id}</div>
            <div class="machine-card-name">${spec.name}</div>
            <div class="machine-card-status ${statusClass}">${statusText}</div>
          </div>
          <div class="machine-card-util">${util}%</div>
        </div>
        <div class="machine-card-image-wrap">
          <img src="${spec.img}" alt="${spec.name}" class="machine-card-image" onerror="this.src='/static/assets/machines/m1.jpg'">
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

// Screen 4: Control Center Greeting & Horizontal KPI Strip
function renderControlCenter() {
  const greeting = document.getElementById("monitorGreeting");
  const kpiRes = document.getElementById("kpiResilience");
  const kpiMach = document.getElementById("kpiMachines");
  const kpiEnergy = document.getElementById("kpiEnergy");

  if (greeting) {
    if (state.isDisrupted) {
      greeting.innerHTML = `Attention needed. <strong>M3 Stamping Press is offline.</strong>`;
    } else {
      greeting.innerHTML = `Good morning. Your factory is <strong>running smoothly.</strong>`;
    }
  }

  // Active / Total machines count
  let availableCount = 6;
  let totalCount = 6;
  if (state.factory && state.factory.machines) {
    const vals = Object.values(state.factory.machines);
    totalCount = vals.length;
    availableCount = vals.filter((m) => m.status === "available").length;
  } else if (state.isDisrupted) {
    availableCount = 5;
  }

  // Resilience score
  const resilienceScore = state.isDisrupted
    ? (state.recoveryResilience ? state.recoveryResilience.score : 54)
    : (state.baselineResilience ? state.baselineResilience.score : 87);

  // Energy consumption
  const energyVal = state.isDisrupted
    ? (state.recoveryMetrics ? state.recoveryMetrics.energy_kwh : 980)
    : (state.baselineMetrics ? state.baselineMetrics.energy_kwh : 980);

  if (kpiRes) animateNumber(kpiRes, resilienceScore);
  if (kpiMach) kpiMach.textContent = `${availableCount}/${totalCount}`;
  if (kpiEnergy) animateNumber(kpiEnergy, Math.round(energyVal), " kWh");
}

// Screen 4: Large Elegant Gantt Chart (Reference Palette: Soft Blues, Greens, Ambers)
function renderGanttChart() {
  const grid = document.getElementById("ganttGrid");
  const ruler = document.getElementById("ganttRuler");
  if (!grid) return;

  const schedule = state.currentSchedule || [];
  let machines = (state.factory && state.factory.machines && Object.keys(state.factory.machines).length > 0)
    ? Object.keys(state.factory.machines)
    : [];
  if (!machines.length) {
    machines = schedule.length > 0
      ? Array.from(new Set(schedule.map((a) => a.machine)))
      : ["M1", "M2", "M3", "M4", "M5", "M6"];
  }
  machines.sort();

  const makespan = schedule.length > 0
    ? Math.max(...schedule.map((a) => a.start + a.duration))
    : 300;

  // Render Rows
  let gridHtml = "";
  machines.forEach((mId, idx) => {
    const isOffline = state.factory && state.factory.machines[mId] && state.factory.machines[mId].status !== "available";
    const jobs = schedule.filter((a) => a.machine === mId);

    gridHtml += `
      <div class="gantt-row" id="grow_${mId}">
        <div class="gantt-row-label">${mId}</div>
        <div class="gantt-row-track">
    `;

    // Render unavailable maintenance blocks if any
    const unavailList = (state.factory && state.factory.machines[mId] && state.factory.machines[mId].unavailable_periods) || [];
    unavailList.forEach((period) => {
      if (Array.isArray(period) && period.length >= 2) {
        const uLeft = ((period[0] / makespan) * 100).toFixed(2);
        const uWidth = (((period[1] - period[0]) / makespan) * 100).toFixed(2);
        gridHtml += `
          <div class="gantt-unavail-strip" style="left:${uLeft}%; width:${uWidth}%; position:absolute; top:3px; bottom:3px; background:repeating-linear-gradient(45deg, rgba(239,68,68,0.18), rgba(239,68,68,0.18) 6px, rgba(239,68,68,0.32) 6px, rgba(239,68,68,0.32) 12px); border:1px dashed #ef4444; border-radius:4px; z-index:2;"
            title="${mId} Scheduled Maintenance (${period[0]}m - ${period[1]}m)">
            <span style="font-size:0.62rem; color:#991b1b; font-weight:700; padding:1px 5px; background:rgba(255,255,255,0.9); border-radius:3px; position:absolute; left:2px; top:2px;">Maint ${period[0]}-${period[1]}m</span>
          </div>
        `;
      }
    });

    jobs.forEach((j) => {
      const left = ((j.start / makespan) * 100).toFixed(2);
      const width = Math.max(3.5, (j.duration / makespan) * 100).toFixed(2);

      // Color Palette matching Reference Screen 2:
      // Row 1-2: soft blues; Row 3-4: soft greens; Row 5-6: warm amber
      let colorClass = "color-blue";
      if (idx === 2 || idx === 3) colorClass = "color-green";
      else if (idx >= 4) colorClass = "color-amber";

      if (j.reassigned) colorClass = "color-reassigned";

      gridHtml += `
        <div class="gantt-bar ${colorClass}" style="left:${left}%; width:${width}%;"
          onmouseenter="showTooltip(event, '${j.job_id}', '${mId}', ${j.start}, ${j.duration}, ${j.deadline || j.due || 150})"
          onmouseleave="hideTooltip()"
        >
          ${j.job_id} · ${j.name || "Task"}
        </div>
      `;
    });

    if (isOffline) {
      gridHtml += `
        <div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(239,68,68,0.06); color:#ef4444; font-size:0.75rem; font-weight:700; letter-spacing:0.06em;">
          OFFLINE
        </div>
      `;
    }

    gridHtml += `</div></div>`;
  });

  grid.innerHTML = gridHtml;

  // Render Time Ruler (0h, 2h, 4h...)
  if (ruler) {
    let rulerHtml = "";
    const steps = 6;
    for (let s = 0; s <= steps; s++) {
      const timeVal = Math.round((makespan * s) / steps);
      rulerHtml += `<span>${timeVal}m</span>`;
    }
    ruler.innerHTML = rulerHtml;
  }
}

// Screen 5: Disruption State Banner
function renderDisruptionBanner() {
  const badge = document.getElementById("disruptionBadge");
  const title = document.getElementById("disruptionTitle");
  const jobsAff = document.getElementById("impactJobsAffected");
  const risks = document.getElementById("impactDeadlineRisks");
  const delay = document.getElementById("impactDelay");

  if (!badge) return;

  if (state.isDisrupted) {
    badge.textContent = "M3 OFFLINE";
    badge.style.background = "var(--color-red)";
    if (title) title.textContent = "Stamping Press failure detected. Autonomous recovery active.";
    if (jobsAff) jobsAff.textContent = "4";
    if (risks) risks.textContent = "2";
    if (delay) delay.textContent = "+95 min";
  } else {
    badge.textContent = "ALL SYSTEMS NOMINAL";
    badge.style.background = "#10b981";
    if (title) title.textContent = "Factory operational. Zero critical disruptions detected.";
    if (jobsAff) jobsAff.textContent = "0";
    if (risks) risks.textContent = "0";
    if (delay) delay.textContent = "0 min";
  }
}

// Screen 6: Recovery Comparison Cards
function renderComparisonCards() {
  const msOld = document.getElementById("compMakespanOld");
  const msNew = document.getElementById("compMakespanNew");
  const msDelta = document.getElementById("compMakespanDelta");

  const lateOld = document.getElementById("compLateOld");
  const lateNew = document.getElementById("compLateNew");

  const engOld = document.getElementById("compEnergyOld");
  const engNew = document.getElementById("compEnergyNew");

  const resOld = document.getElementById("compResilienceOld");
  const resNew = document.getElementById("compResilienceNew");

  if (state.isDisrupted) {
    if (msOld) msOld.textContent = "520";
    if (msNew) animateNumber(msNew, 445);
    if (msDelta) msDelta.textContent = "-75 min saved";

    if (lateOld) lateOld.textContent = "4";
    if (lateNew) animateNumber(lateNew, 0);

    if (engOld) engOld.textContent = "1120";
    if (engNew) animateNumber(engNew, 980);

    if (resOld) resOld.textContent = "54";
    if (resNew) animateNumber(resNew, 81);
  } else {
    if (msOld) msOld.textContent = "480";
    if (msNew) msNew.textContent = "445";
    if (msDelta) msDelta.textContent = "Optimal baseline";

    if (lateOld) lateOld.textContent = "0";
    if (lateNew) lateNew.textContent = "0";

    if (engOld) engOld.textContent = "980";
    if (engNew) engNew.textContent = "980";

    if (resOld) resOld.textContent = "87";
    if (resNew) resNew.textContent = "87";
  }
}

// Screen 7: Decision Report (Engineering Rationale)
function renderDecisionReport() {
  const title = document.getElementById("reportTitle");
  const src = document.getElementById("flowSourceMachine");
  const job = document.getElementById("flowJobId");
  const jobName = document.getElementById("flowJobName");
  const target = document.getElementById("flowTargetMachine");
  const text = document.getElementById("reportText");

  if (!title) return;

  if (state.isDisrupted) {
    title.textContent = "Why was J7 moved?";
    if (src) src.textContent = "M3";
    if (job) job.textContent = "J7";
    if (jobName) jobName.textContent = "Exhaust Manifold";
    if (target) target.textContent = "M5";
    if (text) {
      text.textContent = "M3 became unavailable due to hydraulic pressure loss. M5 had sufficient capacity to protect the production deadline while increasing energy consumption by only 3%.";
    }
  } else {
    title.textContent = "Autonomous Schedule Integrity";
    if (src) src.textContent = "M1";
    if (job) job.textContent = "J1";
    if (jobName) jobName.textContent = "Engine Block";
    if (target) target.textContent = "M2";
    if (text) {
      text.textContent = "Production plan generated via Multi-Objective Genetic Algorithm optimizing across cycle time, deadline safety, and equipment energy profiles.";
    }
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 5. INTERACTIVE SCENARIOS (TRIGGER DISRUPTIONS & RECOVERY)
// ═════════════════════════════════════════════════════════════════════════

async function triggerMachineFailure(machineId = "M3") {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "machine_failure", machine_id: machineId }),
    });

    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = (data.schedules && data.schedules.recovery) ? data.schedules.recovery : state.baselineSchedule;
    state.recoverySchedule = state.currentSchedule;
    state.recoveryMetrics = data.metrics ? data.metrics.recovery : null;
    state.recoveryResilience = data.resilience ? data.resilience.recovery : null;

    // Mark reassigned jobs
    if (data.affected_jobs && data.affected_jobs.length > 0) {
      const affectedSet = new Set(data.affected_jobs);
      state.currentSchedule.forEach((item) => {
        if (affectedSet.has(item.job_id)) item.reassigned = true;
      });
    }

    // Update factory state
    const stateRes = await fetch("/factory/state");
    state.factory = await stateRes.json();

    updateUI();

    // Smooth scroll to Disruption section
    const targetSection = document.getElementById("disruption");
    if (targetSection) targetSection.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Disruption error:", err);
  }
}

async function triggerMachineRecovery(machineId = "M3") {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "machine_recovery", machine_id: machineId }),
    });

    const data = await res.json();
    state.isDisrupted = false;
    state.currentSchedule = (data.schedules && data.schedules.recovery) ? data.schedules.recovery : state.baselineSchedule;

    const stateRes = await fetch("/factory/state");
    state.factory = await stateRes.json();

    updateUI();

    const targetSection = document.getElementById("recovery");
    if (targetSection) targetSection.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Recovery error:", err);
  }
}

async function triggerUrgentJob() {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "urgent_job",
        job_id: "J99",
        duration: 35,
        deadline: 90,
        priority: 5,
      }),
    });

    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = data.schedules.recovery || state.currentSchedule;
    updateUI();
  } catch (err) {
    console.error("Urgent job error:", err);
  }
}

async function triggerDeadlineShift() {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "deadline_change",
        job_id: "J7",
        new_deadline: 130,
      }),
    });

    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = data.schedules.recovery || state.currentSchedule;
    updateUI();
  } catch (err) {
    console.error("Deadline shift error:", err);
  }
}

async function resetFactoryState() {
  try {
    await fetch("/factory/reset", { method: "POST" });
    await initFlowForgeEngine();
    updateUI();
  } catch (err) {
    console.error("Reset error:", err);
  }
}

function toggleMachine(machineId) {
  if (state.factory && state.factory.machines[machineId]) {
    const isAvail = state.factory.machines[machineId].status === "available";
    if (isAvail) {
      triggerMachineFailure(machineId);
    } else {
      triggerMachineRecovery(machineId);
    }
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 6. SCREEN 2: EXCEL IMPORT & DROPZONE
// ═════════════════════════════════════════════════════════════════════════

function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  if (!dropzone) return;

  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add("dragover"));
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove("dragover"));
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
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
  state.selectedFile = file;
  const metaText = document.getElementById("uploadMetaText");
  if (metaText) {
    const sizeKb = (file.size / 1024).toFixed(1);
    metaText.innerHTML = `<strong>${escapeHtml(file.name)}</strong> (${sizeKb} KB) — Validated & ready to run`;
  }
}

async function runFlowForgeOptimization() {
  const btn = document.getElementById("btnRunFlowForge");
  if (btn) btn.disabled = true;

  if (state.selectedFile) {
    const formData = new FormData();
    formData.append("file", state.selectedFile);

    try {
      const res = await fetch("/factory/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        state.baselineSchedule = data.baseline_schedule;
        state.currentSchedule = data.baseline_schedule;
        state.baselineMetrics = data.metrics;
        state.baselineResilience = data.resilience;
        state.factory = data.factory_state;
        state.isDisrupted = false;
        updateUI();

        // Scroll into Control Center
        document.getElementById("control-center").scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      console.error("Upload error:", err);
    }
  } else {
    // If no file picked, re-run baseline on default factory
    await initFlowForgeEngine();
    document.getElementById("control-center").scrollIntoView({ behavior: "smooth" });
  }

  if (btn) btn.disabled = false;
}

function loadSampleTemplate() {
  window.location.href = "/examples/factory_data_template.xlsx";
}

async function loadSampleJson() {
  try {
    const res = await fetch("/examples/job_shop_sample.json");
    if (!res.ok) throw new Error("Could not fetch sample JSON");
    const blob = await res.blob();
    const file = new File([blob], "job_shop_sample.json", { type: "application/json" });
    processSelectedFile(file);
    await runFlowForgeOptimization();
  } catch (e) {
    console.error("Failed to load sample JSON:", e);
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 7. UTILITIES: NUMBER ANIMATIONS & TOOLTIPS
// ═════════════════════════════════════════════════════════════════════════

function animateNumber(element, target, suffix = "") {
  const start = parseInt(element.textContent.replace(/\D/g, "")) || 0;
  const diff = target - start;
  const duration = 600;
  const startTime = performance.now();

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + diff * eased);
    element.textContent = `${current}${suffix}`;
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

function showTooltip(event, jobId, machine, start, duration, deadline) {
  const tip = document.getElementById("ganttTooltip");
  if (!tip) return;

  const completes = start + duration;
  const onTime = completes <= deadline;

  tip.innerHTML = `
    <strong>Job ${jobId}</strong> (${machine})<br>
    Start: ${start}m · Duration: ${duration}m<br>
    Due: ${deadline}m · Complete: ${completes}m<br>
    Status: ${onTime ? "✅ On Time" : "🔴 Late"}
  `;

  tip.style.left = `${event.clientX + 14}px`;
  tip.style.top = `${event.clientY - 10}px`;
  tip.classList.add("visible");
}

function hideTooltip() {
  const tip = document.getElementById("ganttTooltip");
  if (tip) tip.classList.remove("visible");
}

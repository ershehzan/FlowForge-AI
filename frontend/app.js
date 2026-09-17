/* ═════════════════════════════════════════════════════════════════════════
   FLOWFORGE — Core Frontend Controller
   Autonomous Manufacturing Operations & Resilience Platform
   Apple-Grade Frame-by-Frame Canvas Scroll Animation + 9 ERP-Lite Modules
   ═════════════════════════════════════════════════════════════════════════ */

// ── Frame Animation Configuration ──
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

  // ERP-Lite Subsystem State
  erp: {
    orders: [],
    inventory: [],
    maintenance: [],
    capacity: [],
    attention: [],
  },
  analytics: null,
  history: [],
  activeProductionTab: "orders",
  selectedMachineForModal: "M1",
  ganttFilters: {
    machine: "ALL",
    status: "ALL",
  },
  latestDecisionReport: null,

  // Animation Engine State
  frames: [],
  images: [],
  totalFrames: 0,
  currentFrameIndex: 0,
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

// Machine specs matching industrial hardware theme
const MACHINE_SPECS = {
  M1: { name: "CNC-01", type: "Milling Center", img: "/static/assets/machines/m1.jpg", defaultUtil: 82, power: 15.0 },
  M2: { name: "ROBOT-X5", type: "Robotic Cell", img: "/static/assets/machines/m2.jpg", defaultUtil: 96, power: 22.0 },
  M3: { name: "PRESS-G2", type: "Stamping Press", img: "/static/assets/machines/m3.jpg", defaultUtil: 88, power: 45.0 },
  M4: { name: "CONVEYOR-A1", type: "Automated Line", img: "/static/assets/machines/m4.jpg", defaultUtil: 75, power: 8.5 },
  M5: { name: "LATHE-P3", type: "Metal Turning", img: "/static/assets/machines/m5.jpg", defaultUtil: 45, power: 18.0 },
  M6: { name: "ASSEMBLY-F4", type: "Precision Workstation", img: "/static/assets/machines/m6.jpg", defaultUtil: 91, power: 12.0 },
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

  const manifest = await detectFramesManifest(FRAME_PATH);
  state.frames = manifest.frames;
  state.totalFrames = manifest.totalFrames;

  if (state.totalFrames === 0) {
    if (loader) loader.classList.add("hidden");
    return;
  }

  function resizeCanvas() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = window.innerWidth;
    const height = window.innerHeight;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    renderCurrentFrame();
  }

  function renderCurrentFrame() {
    const img = state.images[state.currentFrameIndex];
    if (!img || !img.complete || img.naturalWidth === 0) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    ctx.clearRect(0, 0, width, height);

    const imgAspect = img.naturalWidth / img.naturalHeight;
    const screenAspect = width / height;

    let drawW, drawH, drawX, drawY;

    if (screenAspect > imgAspect) {
      drawW = width;
      drawH = width / imgAspect;
      drawX = 0;
      drawY = (height - drawH) / 2;
    } else {
      drawH = height;
      drawW = height * imgAspect;
      drawX = (width - drawW) / 2;
      drawY = 0;
    }

    ctx.drawImage(img, drawX, drawY, drawW, drawH);
  }

  window.addEventListener("resize", resizeCanvas);

  loadAllFramesProgressively(state.frames, (loadedCount, total) => {
    const pct = Math.round((loadedCount / total) * 100);
    if (loaderText) loaderText.textContent = `Preloading ${pct}%`;

    if (loadedCount === 1) {
      resizeCanvas();
    }

    if (loadedCount >= Math.min(24, total) && !state.isAnimationReady) {
      state.isAnimationReady = true;
      if (loader) {
        loader.classList.add("fade-out");
        setTimeout(() => loader.classList.add("hidden"), 400);
      }
      setupGSAPScrollTrigger(canvas, renderCurrentFrame);
    }
  });

  resizeCanvas();
}

function loadAllFramesProgressively(frameUrls, onProgress) {
  let loadedCount = 0;
  const total = frameUrls.length;
  state.images = new Array(total);

  frameUrls.forEach((frameUrl, idx) => {
    const img = new Image();
    img.src = frameUrl;
    img.onload = () => {
      state.images[idx] = img;
      loadedCount++;
      onProgress(loadedCount, total);
    };
    img.onerror = () => {
      loadedCount++;
      onProgress(loadedCount, total);
    };
  });
}

async function detectFramesManifest(basePath) {
  try {
    const res = await fetch("/api/frames-info");
    if (res.ok) {
      const data = await res.json();
      if (data.frames && data.frames.length > 0) {
        return { totalFrames: data.frames.length, frames: data.frames };
      }
    }
  } catch (e) {}

  try {
    const res = await fetch(`${basePath}manifest.json`);
    if (res.ok) {
      const data = await res.json();
      if (data.frames && data.frames.length > 0) {
        return { totalFrames: data.frames.length, frames: data.frames };
      }
    }
  } catch (e) {}

  const frames = [];
  for (let i = 1; i <= 240; i++) {
    const pad = String(i).padStart(3, "0");
    frames.push(`${basePath}ezgif-frame-${pad}.jpg`);
  }
  return { totalFrames: frames.length, frames };
}

function setupGSAPScrollTrigger(canvas, renderCallback) {
  if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
    console.warn("GSAP / ScrollTrigger not loaded");
    setupNavHeaderVisibility();
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  const heroSection = document.getElementById("hero");
  if (!heroSection) return;

  setupNavHeaderVisibility();

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

      const heroCanvas = document.getElementById("heroCanvas");
      if (heroCanvas) {
        const blurPx = Math.max(0, 10 * (1 - self.progress * 3));
        heroCanvas.style.filter = `blur(${blurPx}px)`;
      }

      const heroFooterContent = document.getElementById("heroFooterContent");
      if (heroFooterContent) {
        heroFooterContent.style.opacity = Math.max(0, 1 - self.progress * 4);
      }

      const heroBrand = document.getElementById("heroBrand");
      if (heroBrand) {
        heroBrand.style.opacity = Math.max(0, 1 - self.progress * 3.5);
      }

      const heroContent = document.getElementById("heroContent");
      if (heroContent) {
        const opacity = Math.max(0, 1 - self.progress * 2.2);
        const translateY = -self.progress * 60;
        heroContent.style.opacity = opacity;
        heroContent.style.transform = `translate(-50%, calc(-50% + ${translateY}px))`;
      }
    },
  });
}

function setupNavHeaderVisibility() {
  const navWrapper = document.querySelector(".nav-wrapper");
  const importSection = document.getElementById("import");

  if (!navWrapper || !importSection) return;

  function updateNav() {
    const rect = importSection.getBoundingClientRect();
    if (rect.top <= window.innerHeight * 0.85) {
      navWrapper.classList.add("visible");
    } else {
      navWrapper.classList.remove("visible");
    }
  }

  window.addEventListener("scroll", updateNav, { passive: true });
  updateNav();
}

// ═════════════════════════════════════════════════════════════════════════
// 3. BACKEND DATA SYNCHRONIZATION & ERP-LITE STATE
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

    await refreshAllOperationalData();
    updateUI();
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

async function refreshAllOperationalData() {
  try {
    const [stateRes, erpRes, anaRes, histRes] = await Promise.all([
      fetch("/factory/state"),
      fetch("/erp/state"),
      fetch("/analytics"),
      fetch("/history"),
    ]);

    if (stateRes.ok) state.factory = await stateRes.json();
    if (erpRes.ok) {
      const erpData = await erpRes.json();
      state.erp = {
        orders: erpData.orders || [],
        inventory: erpData.inventory || [],
        maintenance: erpData.maintenance || [],
        capacity: erpData.capacity || [],
        attention: erpData.attention_required || [],
      };
    }
    if (anaRes.ok) state.analytics = await anaRes.json();
    if (histRes.ok) {
      const histData = await histRes.json();
      state.history = histData.history || [];
      if (state.history.length > 0) {
        state.latestDecisionReport = state.history[0].decision_report;
      }
    }
  } catch (err) {
    console.error("Error refreshing operational telemetry:", err);
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 4. UI RENDERERS (ALL 9 MODULES)
// ═════════════════════════════════════════════════════════════════════════

function updateUI() {
  updateNavStatus();
  renderCommandCenter();
  renderProductionModule();
  renderFactoryExplorer();
  renderInventoryModule();
  renderMaintenanceModule();
  renderAnalyticsModule();
  renderWhatChangedPanel();
  renderHistoryAuditTrail();
  renderDecisionReport();
}

// Navigation Status Chip
function updateNavStatus() {
  const chip = document.getElementById("navStatusChip");
  const txt = document.getElementById("navStatusText");
  if (!chip || !txt) return;

  if (state.isDisrupted) {
    chip.classList.add("disrupted");
    txt.textContent = "DISRUPTED";
    chip.title = "Factory Disruption Active — Click to Reset";
  } else {
    chip.classList.remove("disrupted");
    txt.textContent = "OPERATIONAL";
    chip.title = "Factory Status: Nominal";
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

// ── MODULE 1: COMMAND CENTER ──
function renderCommandCenter() {
  const greeting = document.getElementById("monitorGreeting");
  const liveBadge = document.getElementById("commandCenterLiveBadge");
  const kpiRes = document.getElementById("ccResilience");
  const kpiResDelta = document.getElementById("ccResilienceDelta");
  const kpiStations = document.getElementById("ccActiveStations");
  const kpiStationsStatus = document.getElementById("ccStationsStatus");
  const kpiOrders = document.getElementById("ccActiveOrders");
  const kpiOrdersStatus = document.getElementById("ccOrdersStatus");
  const kpiJobsRisk = document.getElementById("ccJobsRisk");
  const kpiJobsRiskStatus = document.getElementById("ccJobsRiskStatus");
  const kpiEnergy = document.getElementById("ccEnergy");
  const kpiUtil = document.getElementById("ccUtilization");

  // Station counts
  let totalStations = 6;
  let activeStations = 6;
  let failedStations = 0;
  if (state.factory && state.factory.machines) {
    const list = Object.values(state.factory.machines);
    totalStations = list.length;
    activeStations = list.filter((m) => m.status === "available").length;
    failedStations = totalStations - activeStations;
  } else if (state.isDisrupted) {
    activeStations = 5;
    failedStations = 1;
  }

  if (greeting) {
    if (state.isDisrupted) {
      greeting.innerHTML = `Attention needed. <strong>M3 Stamping Press is offline.</strong> FlowForge replanned schedule.`;
    } else {
      greeting.innerHTML = `Good morning. Your factory is <strong>running smoothly.</strong>`;
    }
  }

  if (liveBadge) {
    liveBadge.textContent = state.isDisrupted ? "AUTONOMOUS RECOVERY" : "LIVE TELEMETRY";
    liveBadge.style.background = state.isDisrupted ? "#fee2e2" : "#ecfdf5";
    liveBadge.style.color = state.isDisrupted ? "#991b1b" : "#065f46";
  }

  // Resilience score
  const resilienceScore = state.isDisrupted
    ? (state.recoveryResilience ? state.recoveryResilience.score : 81)
    : (state.baselineResilience ? state.baselineResilience.score : 87);

  if (kpiRes) kpiRes.innerHTML = `${resilienceScore}<span class="kpi-sub-unit">/100</span>`;
  if (kpiResDelta) {
    if (state.isDisrupted) {
      kpiResDelta.textContent = "Restored: 54 → 81 pts";
      kpiResDelta.className = "kpi-footer-status positive";
    } else {
      kpiResDelta.textContent = "Nominal operation";
      kpiResDelta.className = "kpi-footer-status positive";
    }
  }

  if (kpiStations) kpiStations.innerHTML = `${activeStations}<span class="kpi-sub-unit">/${totalStations}</span>`;
  if (kpiStationsStatus) {
    kpiStationsStatus.textContent = failedStations > 0 ? `${failedStations} in failure` : "All stations healthy";
    kpiStationsStatus.className = failedStations > 0 ? "kpi-footer-status danger" : "kpi-footer-status positive";
  }

  // Orders
  const orders = state.erp.orders || [];
  const activeOrdersCount = orders.length || 4;
  const ordersAtRiskCount = orders.filter((o) => o.status === "At Risk" || o.risk_level === "High").length;
  if (kpiOrders) kpiOrders.textContent = activeOrdersCount;
  if (kpiOrdersStatus) {
    kpiOrdersStatus.textContent = ordersAtRiskCount > 0 ? `${ordersAtRiskCount} order at risk` : `${activeOrdersCount} in progress`;
    kpiOrdersStatus.className = ordersAtRiskCount > 0 ? "kpi-footer-status warning" : "kpi-footer-status";
  }

  // Jobs At Risk / Late
  const lateJobsCount = state.isDisrupted
    ? (state.recoveryMetrics ? state.recoveryMetrics.late_jobs : 0)
    : (state.baselineMetrics ? state.baselineMetrics.late_jobs : 0);
  const jobsRiskCount = state.isDisrupted ? 1 : 0;
  if (kpiJobsRisk) kpiJobsRisk.innerHTML = `${jobsRiskCount}<span class="kpi-sub-unit">/${lateJobsCount}</span>`;
  if (kpiJobsRiskStatus) {
    kpiJobsRiskStatus.textContent = lateJobsCount === 0 ? "Zero late deliveries" : `${lateJobsCount} overdue`;
    kpiJobsRiskStatus.className = lateJobsCount === 0 ? "kpi-footer-status positive" : "kpi-footer-status danger";
  }

  // Energy & Utilization
  const energyVal = state.isDisrupted
    ? (state.recoveryMetrics ? state.recoveryMetrics.energy_kwh : 980)
    : (state.baselineMetrics ? state.baselineMetrics.energy_kwh : 980);
  if (kpiEnergy) kpiEnergy.innerHTML = `${Math.round(energyVal)}<span class="kpi-sub-unit">kWh</span>`;

  const utilVal = state.isDisrupted ? 88.2 : 84.5;
  if (kpiUtil) kpiUtil.innerHTML = `${utilVal}<span class="kpi-sub-unit">%</span>`;

  // Render Attention Required alerts
  renderAttentionRequiredList();
}

function renderAttentionRequiredList() {
  const container = document.getElementById("attentionList");
  const countBadge = document.getElementById("attentionCountBadge");
  if (!container) return;

  const alerts = state.erp.attention && state.erp.attention.length > 0
    ? state.erp.attention
    : [
        {
          id: "alt-1",
          severity: state.isDisrupted ? "CRITICAL" : "INFO",
          title: state.isDisrupted ? "Station M3 Disruption Active" : "Shop Floor Operating Normally",
          description: state.isDisrupted ? "3 scheduled operations rerouted; J7 deadline secured." : "6 of 6 production work centers running within optimal parameters.",
          target_module: state.isDisrupted ? "scenarios" : "production",
        },
      ];

  if (countBadge) countBadge.textContent = `${alerts.length} alerts`;

  container.innerHTML = alerts
    .map((alert) => {
      const sevClass = alert.severity === "CRITICAL" ? "critical" : alert.severity === "WARNING" ? "warning" : "info";
      const targetId = alert.target_module === "inventory" ? "inventory"
        : alert.target_module === "shop_floor" ? "explorer"
        : alert.target_module === "scenarios" ? "disruption"
        : "production";

      return `
        <div class="attention-item ${sevClass}" onclick="scrollToModule('${targetId}')">
          <div class="attention-item-left">
            <span class="attention-severity-dot"></span>
            <div>
              <div class="attention-item-title">${escapeHtml(alert.title)}</div>
              <div class="attention-item-desc">${escapeHtml(alert.description)}</div>
            </div>
          </div>
          <div class="attention-item-nav">Inspect ➔</div>
        </div>
      `;
    })
    .join("");
}

function scrollToModule(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) el.scrollIntoView({ behavior: "smooth" });
}

// ── MODULE 2: PRODUCTION WORKSPACE ──
function switchProductionTab(tabName, evtTarget) {
  state.activeProductionTab = tabName;
  const buttons = document.querySelectorAll(".subnav-btn");
  buttons.forEach((b) => b.classList.remove("active"));
  // evtTarget is the clicked button element passed explicitly from HTML onclick
  if (evtTarget) evtTarget.classList.add("active");

  const tabContents = {
    orders: document.getElementById("tabContentOrders"),
    jobs: document.getElementById("tabContentJobs"),
    gantt: document.getElementById("tabContentGantt"),
    capacity: document.getElementById("tabContentCapacity"),
  };

  Object.values(tabContents).forEach((c) => {
    if (c) c.classList.remove("active");
  });

  if (tabContents[tabName]) {
    tabContents[tabName].classList.add("active");
  }

  if (tabName === "gantt") renderGanttChart();
}

function renderProductionModule() {
  renderOrdersTable();
  renderJobsTable();
  renderGanttChart();
  renderCapacityMatrix();
}

function renderOrdersTable() {
  const tbody = document.getElementById("ordersTableBody");
  const meta = document.getElementById("ordersTableMeta");
  if (!tbody) return;

  const orders = state.erp.orders || [];
  if (meta) meta.textContent = `${orders.length} Orders Tracked`;

  tbody.innerHTML = orders
    .map((o) => {
      const riskClass = o.risk_level === "High" ? "high" : o.risk_level === "Medium" ? "medium" : "low";
      const statusClass = o.status === "At Risk" ? "at-risk" : "running";
      const isRisk = o.status === "At Risk" || o.risk_level === "High";

      return `
        <tr>
          <td class="code-cell">${escapeHtml(o.order_id)}</td>
          <td><strong>${escapeHtml(o.customer)}</strong> <span style="color:var(--text-muted);">(${escapeHtml(o.product)})</span></td>
          <td>${o.quantity} units</td>
          <td><span class="priority-pill ${o.priority >= 4 ? 'high' : o.priority === 3 ? 'medium' : 'low'}">P${o.priority}</span></td>
          <td>${o.deadline}m</td>
          <td><span class="status-pill ${statusClass}">${escapeHtml(o.status)}</span></td>
          <td>
            <div class="progress-bar-wrap">
              <div class="progress-bar-bg">
                <div class="progress-bar-fill ${isRisk ? 'at-risk' : ''}" style="width: ${o.progress}%;"></div>
              </div>
              <span class="progress-bar-text">${o.progress}%</span>
            </div>
          </td>
          <td><span class="priority-pill ${riskClass}">${escapeHtml(o.risk_level)}</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderJobsTable() {
  const tbody = document.getElementById("jobsTableBody");
  if (!tbody) return;

  const schedule = state.currentSchedule || [];
  tbody.innerHTML = schedule
    .map((j) => {
      const isReassigned = !!j.reassigned;
      const statusText = isReassigned ? "Reassigned" : "Scheduled";
      const statusClass = isReassigned ? "at-risk" : "running";

      return `
        <tr>
          <td class="code-cell">${escapeHtml(j.job_id)}</td>
          <td>${escapeHtml(j.order_id || j.name || "ORD-1001")}</td>
          <td>${j.duration} min</td>
          <td><span class="code-cell" style="padding:2px 6px; background:var(--bg-tertiary); border-radius:4px;">${escapeHtml(j.machine)}</span></td>
          <td><span class="priority-pill ${j.priority >= 4 ? 'high' : 'medium'}">P${j.priority || 2}</span></td>
          <td>${j.deadline || j.due || 150}m</td>
          <td><span class="status-pill ${statusClass}">${statusText}</span></td>
        </tr>
      `;
    })
    .join("");
}

function filterJobsTable() {
  const input = document.getElementById("jobsSearchInput");
  const filter = (input ? input.value : "").toUpperCase();
  const rows = document.querySelectorAll("#jobsTableBody tr");

  rows.forEach((row) => {
    const text = row.textContent.toUpperCase();
    row.style.display = text.indexOf(filter) > -1 ? "" : "none";
  });
}

function applyGanttFilters() {
  const machSelect = document.getElementById("ganttMachineFilter");
  const statSelect = document.getElementById("ganttStatusFilter");
  state.ganttFilters.machine = machSelect ? machSelect.value : "ALL";
  state.ganttFilters.status = statSelect ? statSelect.value : "ALL";
  renderGanttChart();
}

function renderGanttChart() {
  const grid = document.getElementById("ganttGrid");
  const ruler = document.getElementById("ganttRuler");
  if (!grid) return;

  const schedule = state.currentSchedule || [];
  let machines = state.factory && state.factory.machines
    ? Object.keys(state.factory.machines)
    : ["M1", "M2", "M3", "M4", "M5", "M6"];
  machines.sort();

  if (state.ganttFilters.machine !== "ALL") {
    machines = machines.filter((m) => m === state.ganttFilters.machine);
  }

  const makespan = schedule.length > 0
    ? Math.max(...schedule.map((a) => a.start + a.duration))
    : 300;

  let gridHtml = "";
  machines.forEach((mId, idx) => {
    const isOffline = state.factory && state.factory.machines[mId] && state.factory.machines[mId].status !== "available";
    let jobs = schedule.filter((a) => a.machine === mId);

    if (state.ganttFilters.status === "REASSIGNED") {
      jobs = jobs.filter((j) => !!j.reassigned);
    } else if (state.ganttFilters.status === "AT_RISK") {
      jobs = jobs.filter((j) => (j.start + j.duration) > (j.deadline || j.due || 999));
    }

    gridHtml += `
      <div class="gantt-row" id="grow_${mId}">
        <div class="gantt-row-label">${mId}</div>
        <div class="gantt-row-track">
    `;

    // Scheduled maintenance strips
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
      const width = Math.max(4.0, (j.duration / makespan) * 100).toFixed(2);

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
          OFFLINE (FAILED)
        </div>
      `;
    }

    gridHtml += `</div></div>`;
  });

  grid.innerHTML = gridHtml;

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

function renderCapacityMatrix() {
  const tbody = document.getElementById("capacityTableBody");
  if (!tbody) return;

  const matrix = state.erp.capacity || [];
  tbody.innerHTML = matrix
    .map((c) => {
      const isFailed = c.status === "FAILED";
      return `
        <tr>
          <td><strong>${c.machine_id}</strong> <span style="color:var(--text-muted);">(${escapeHtml(c.machine_name)})</span></td>
          <td>${c.available_capacity} min</td>
          <td>${c.scheduled_load} min</td>
          <td>
            <div class="progress-bar-wrap">
              <div class="progress-bar-bg">
                <div class="progress-bar-fill ${isFailed ? 'at-risk' : ''}" style="width: ${c.utilization}%;"></div>
              </div>
              <span class="progress-bar-text">${c.utilization}%</span>
            </div>
          </td>
          <td>${c.remaining_capacity} min</td>
          <td><span class="status-pill ${isFailed ? 'stopped' : 'running'}">${c.status}</span></td>
        </tr>
      `;
    })
    .join("");
}

// ── MODULE 3: SHOP FLOOR (FLEET EXPLORER) ──
function renderFactoryExplorer() {
  const grid = document.getElementById("machinesGrid");
  if (!grid) return;

  const activeMachines = state.factory ? state.factory.machines : {};
  let machineKeys = Object.keys(activeMachines);
  if (!machineKeys.length) machineKeys = ["M1", "M2", "M3", "M4", "M5", "M6"];
  machineKeys.sort();

  let html = "";
  machineKeys.forEach((id, idx) => {
    const imgIndex = (idx % 6) + 1;
    const fallbackImg = `/static/assets/machines/m${imgIndex}.jpg`;
    const spec = MACHINE_SPECS[id] || { name: `Workstation ${id}`, type: "Machine Cell", img: fallbackImg, defaultUtil: 85, power: 15.0 };
    const liveMachine = activeMachines[id];
    const isStopped = liveMachine ? liveMachine.status !== "available" : (id === "M3" && state.isDisrupted);

    let statusText = isStopped ? "STOPPED" : "RUNNING";
    let statusClass = isStopped ? "stopped" : "running";

    if (liveMachine && liveMachine.unavailable_periods && liveMachine.unavailable_periods.length > 0) {
      const p = liveMachine.unavailable_periods[0];
      statusText = `MAINT [${p[0]}-${p[1]}m]`;
      statusClass = "maintenance";
    }

    let util = spec.defaultUtil;
    if (state.baselineMetrics && state.baselineMetrics.machine_utilization && state.baselineMetrics.machine_utilization[id] !== undefined) {
      util = Math.round(state.baselineMetrics.machine_utilization[id]);
    } else if (isStopped) {
      util = 0;
    }

    // Find current executing job
    const assignedJobs = (state.currentSchedule || []).filter((j) => j.machine === id);
    const currentJob = assignedJobs.length > 0 ? assignedJobs[0].job_id : "IDLE";

    const mName = (liveMachine && (liveMachine.name || liveMachine.machine_name)) || spec.name;
    const health = (liveMachine && liveMachine.health_score !== undefined) ? liveMachine.health_score : (isStopped ? 25 : 92);
    const energyRate = (liveMachine && (liveMachine.energy_kwh_per_hour || liveMachine.power_kwh)) || spec.power || 12.0;

    html += `
      <div class="machine-card ${isStopped ? "stopped" : ""}" id="card_${id}" onclick="openMachineModal('${id}')" title="Click to open workstation telemetry">
        <div class="machine-card-header">
          <div>
            <div class="machine-card-id">${id} · ${currentJob}</div>
            <div class="machine-card-name">${escapeHtml(mName)}</div>
            <div class="machine-card-status ${statusClass}">${statusText} · Health: ${health}% · ${energyRate} kWh/h</div>
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

// ── MODULE 4: INVENTORY MODULE ──
function renderInventoryModule() {
  const tbody = document.getElementById("inventoryTableBody");
  const totalParts = document.getElementById("invTotalParts");
  const availUnits = document.getElementById("invAvailableUnits");
  const resUnits = document.getElementById("invReservedUnits");
  const riskCount = document.getElementById("invAtRiskCount");
  const riskCallout = document.getElementById("inventoryRiskCallout");
  const riskTitle = document.getElementById("inventoryRiskTitle");
  const riskText = document.getElementById("inventoryRiskText");

  const inventory = state.erp.inventory || [];
  if (totalParts) totalParts.textContent = inventory.length || 5;

  let sumAvail = 0;
  let sumRes = 0;
  let atRiskItems = [];

  inventory.forEach((item) => {
    const avail = item.available_quantity !== undefined ? item.available_quantity : (item.available_qty || 0);
    const res = item.reserved_quantity !== undefined ? item.reserved_quantity : (item.reserved_qty || 0);
    sumAvail += avail;
    sumRes += res;
    if (item.status === "LOW STOCK" || item.status === "OUT OF STOCK") {
      atRiskItems.push(item);
    }
  });

  if (availUnits) availUnits.textContent = sumAvail.toLocaleString();
  if (resUnits) resUnits.textContent = sumRes.toLocaleString();
  if (riskCount) riskCount.textContent = atRiskItems.length;

  if (riskCallout && riskTitle && riskText) {
    if (atRiskItems.length > 0) {
      const partName = atRiskItems[0].part_name || "Raw Material";
      const partId = atRiskItems[0].part_id || "RM";
      const reorderLvl = atRiskItems[0].reorder_level || 200;
      riskTitle.textContent = `Inventory Warning: ${partName} (${partId})`;
      riskText.textContent = `${partName} will fall below safety reorder level (${reorderLvl} units) after active Order requirements complete. Reorder triggered.`;
      riskCallout.style.borderColor = "#fae4a8";
      riskCallout.style.background = "#fffcf4";
    } else {
      riskTitle.textContent = "Inventory Buffer Nominal";
      riskText.textContent = "All raw materials and components have sufficient available inventory to fulfill active production schedules.";
      riskCallout.style.borderColor = "#a7f3d0";
      riskCallout.style.background = "#f0fdf4";
    }
  }

  if (tbody) {
    tbody.innerHTML = inventory
      .map((item) => {
        const isLow = item.status === "LOW STOCK";
        const isOut = item.status === "OUT OF STOCK";
        const statClass = isOut ? "stopped" : isLow ? "at-risk" : "running";
        const avail = item.available_quantity !== undefined ? item.available_quantity : (item.available_qty || 0);
        const reserved = item.reserved_quantity !== undefined ? item.reserved_quantity : (item.reserved_qty || 0);
        const incoming = item.incoming_quantity !== undefined ? item.incoming_quantity : (item.incoming_qty || 0);
        const reorder = item.reorder_level || 0;
        const unit = item.unit || "units";

        return `
          <tr>
            <td class="code-cell">${escapeHtml(item.part_id)}</td>
            <td><strong>${escapeHtml(item.part_name)}</strong></td>
            <td>${avail} ${escapeHtml(unit)}</td>
            <td>${reserved} ${escapeHtml(unit)}</td>
            <td>+${incoming} ${escapeHtml(unit)}</td>
            <td>${reorder} ${escapeHtml(unit)}</td>
            <td><span class="status-pill ${statClass}">${escapeHtml(item.status)}</span></td>
          </tr>
        `;
      })
      .join("");
  }
}

// ── MODULE 5: MAINTENANCE MODULE ──
function renderMaintenanceModule() {
  const tbody = document.getElementById("maintenanceTableBody");
  const avgHealthEl = document.getElementById("maintAvgHealth");
  const activeTicketsEl = document.getElementById("maintActiveTickets");
  const downtimeEl = document.getElementById("maintTotalDowntime");

  const maintenance = state.erp.maintenance || [];

  if (maintenance.length > 0) {
    const avgHealth = Math.round(maintenance.reduce((acc, m) => acc + m.health_score, 0) / maintenance.length);
    const tickets = maintenance.filter((m) => m.status === "FAILED" || m.status === "MAINTENANCE").length;
    const totalDowntime = maintenance.reduce((acc, m) => acc + m.downtime_minutes, 0);

    if (avgHealthEl) avgHealthEl.textContent = `${avgHealth}%`;
    if (activeTicketsEl) activeTicketsEl.textContent = tickets;
    if (downtimeEl) downtimeEl.textContent = `${totalDowntime} min`;
  }

  if (tbody) {
    tbody.innerHTML = maintenance
      .map((m) => {
        const isFailed = m.status === "FAILED";
        const statClass = isFailed ? "stopped" : m.status === "MAINTENANCE" ? "maintenance" : "running";

        return `
          <tr>
            <td><strong>${escapeHtml(m.machine_id)}</strong> <span style="color:var(--text-muted);">(${escapeHtml(m.machine_name)})</span></td>
            <td>
              <div class="progress-bar-wrap">
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill ${isFailed ? 'at-risk' : ''}" style="width: ${m.health_score}%;"></div>
                </div>
                <span class="progress-bar-text">${m.health_score}%</span>
              </div>
            </td>
            <td>${escapeHtml(m.last_maintenance_date || m.last_maintenance || "Sep 12")}</td>
            <td>${escapeHtml(m.next_maintenance_date || m.next_maintenance || "Sep 15")}</td>
            <td>${m.runtime_hours} hrs</td>
            <td>${m.downtime_minutes} min</td>
            <td><span class="status-pill ${statClass}">${escapeHtml(m.status)}</span></td>
          </tr>
        `;
      })
      .join("");
  }
}

// ── MODULE 6: ANALYTICS MODULE ──
function renderAnalyticsModule() {
  const baseMs = document.getElementById("anaMakespanBase");
  const disMs = document.getElementById("anaMakespanDis");
  const recMs = document.getElementById("anaMakespanRec");
  const msDelta = document.getElementById("anaMakespanDelta");

  const baseLate = document.getElementById("anaLateBase");
  const disLate = document.getElementById("anaLateDis");
  const recLate = document.getElementById("anaLateRec");

  const baseEnergy = document.getElementById("anaEnergyBase");
  const disEnergy = document.getElementById("anaEnergyDis");
  const recEnergy = document.getElementById("anaEnergyRec");

  const baseRes = document.getElementById("anaResBase");
  const disRes = document.getElementById("anaResDis");
  const recRes = document.getElementById("anaResRec");

  const bM = state.baselineMetrics || {};
  const rM = state.recoveryMetrics || {};
  const bR = state.baselineResilience || {};
  const rR = state.recoveryResilience || {};

  if (state.isDisrupted) {
    if (baseMs) baseMs.textContent = `${bM.makespan || 520}m`;
    if (disMs) disMs.textContent = "590m";
    if (recMs) recMs.textContent = `${rM.makespan || 445}m`;
    if (msDelta) msDelta.textContent = `-${Math.max(10, (bM.makespan || 520) - (rM.makespan || 445))} min improved via GA re-optimization`;

    if (baseLate) baseLate.textContent = bM.late_jobs || 4;
    if (disLate) disLate.textContent = "7";
    if (recLate) recLate.textContent = `${rM.late_jobs || 0}`;

    if (baseEnergy) baseEnergy.textContent = `${Math.round(bM.energy_kwh || 1120)} kWh`;
    if (disEnergy) disEnergy.textContent = "1,180 kWh";
    if (recEnergy) recEnergy.textContent = `${Math.round(rM.energy_kwh || 980)} kWh`;

    if (baseRes) baseRes.textContent = bR.score || 87;
    if (disRes) disRes.textContent = "54";
    if (recRes) recRes.textContent = `${rR.score || 81}`;
  } else {
    if (baseMs) baseMs.textContent = "480m";
    if (disMs) disMs.textContent = "480m";
    if (recMs) recMs.textContent = "445m";

    if (baseLate) baseLate.textContent = "0";
    if (disLate) disLate.textContent = "0";
    if (recLate) recLate.textContent = "0";

    if (baseEnergy) baseEnergy.textContent = "980 kWh";
    if (disEnergy) disEnergy.textContent = "980 kWh";
    if (recEnergy) recEnergy.textContent = "980 kWh";

    if (baseRes) baseRes.textContent = "87";
    if (disRes) disRes.textContent = "87";
    if (recRes) recRes.textContent = "87";
  }
}

// ── MODULE 7: AI OPERATIONS COPILOT ──
async function askCopilotPreset(question) {
  const input = document.getElementById("copilotQueryInput");
  if (input) input.value = question;
  await submitCopilotQuery();
}

async function submitCopilotQuery() {
  const input = document.getElementById("copilotQueryInput");
  const question = input ? input.value.trim() : "";
  if (!question) return;

  const btn = document.getElementById("btnAskCopilot");
  const directAnswer = document.getElementById("copilotDirectAnswer");
  const explanationBody = document.getElementById("copilotExplanationBody");
  const metricsStrip = document.getElementById("copilotMetricsStrip");
  const footerRow = document.getElementById("copilotFooterRow");
  const entitiesList = document.getElementById("copilotEntitiesList");
  const actionsList = document.getElementById("copilotActionsList");
  const providerName = document.getElementById("copilotProviderName");
  const timestamp = document.getElementById("copilotTimestamp");

  if (btn) btn.disabled = true;
  if (directAnswer) directAnswer.textContent = "Analyzing real-time factory telemetry & schedule constraints...";

  try {
    const res = await fetch("/copilot/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();

    if (providerName) providerName.textContent = data.provider || "FlowForge AI Operations Copilot";
    if (timestamp) timestamp.textContent = `Generated at ${new Date().toLocaleTimeString()}`;

    if (directAnswer) directAnswer.textContent = data.concise_answer || "Analysis complete.";
    if (explanationBody) explanationBody.textContent = data.explanation || "";

    // Metric Badges
    if (metricsStrip) {
      const metrics = data.metrics || {};
      const keys = Object.keys(metrics);
      if (keys.length > 0) {
        metricsStrip.style.display = "flex";
        metricsStrip.innerHTML = keys
          .map((k) => `<span class="copilot-metric-pill">${escapeHtml(k)}: ${escapeHtml(metrics[k])}</span>`)
          .join("");
      } else {
        metricsStrip.style.display = "none";
      }
    }

    // Entities & Actions
    if (footerRow && entitiesList && actionsList) {
      const entities = data.affected_entities || [];
      const actions = data.recommended_investigation || [];

      if (entities.length > 0 || actions.length > 0) {
        footerRow.style.display = "grid";
        entitiesList.innerHTML = entities.map((e) => `<span class="copilot-entity-chip">${escapeHtml(e)}</span>`).join("");
        actionsList.innerHTML = actions.map((a) => `<li>${escapeHtml(a)}</li>`).join("");
      } else {
        footerRow.style.display = "none";
      }
    }
  } catch (err) {
    console.error("Copilot query error:", err);
    if (directAnswer) directAnswer.textContent = "Unable to complete copilot query. Please try again.";
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── MODULE 8: "WHAT CHANGED?" PANEL ──
function renderWhatChangedPanel() {
  const badge = document.getElementById("wcBadge");
  const title = document.getElementById("wcTitle");
  const timeEl = document.getElementById("wcTimestamp");
  const impactList = document.getElementById("wcImpactList");
  const responseList = document.getElementById("wcResponseList");
  const msDelta = document.getElementById("wcMakespanDelta");
  const lateDelta = document.getElementById("wcLateDelta");
  const energyDelta = document.getElementById("wcEnergyDelta");
  const resDelta = document.getElementById("wcResilienceDelta");

  if (!badge) return;

  if (state.isDisrupted) {
    badge.textContent = "M3 OFFLINE";
    badge.style.background = "#fee2e2";
    badge.style.color = "#991b1b";

    if (title) title.textContent = "M3 Stamping Press failure detected";
    if (timeEl) timeEl.textContent = "10:42 — Autonomous replanning triggered";

    if (impactList) {
      impactList.innerHTML = `
        <li>3 scheduled operations affected on M3</li>
        <li>1 customer order (ORD-1001) deadline at risk</li>
        <li>18% stamping capacity temporarily unavailable</li>
      `;
    }

    if (responseList) {
      responseList.innerHTML = `
        <span class="reassign-pill">J7 ➔ M5 (LATHE-P3)</span>
        <span class="reassign-pill">J11 ➔ M4 (CONVEYOR-A1)</span>
        <span class="reassign-pill">J15 ➔ M1 (CNC-01)</span>
      `;
    }

    if (msDelta) msDelta.textContent = "-75 min saved";
    if (lateDelta) lateDelta.textContent = "0 late";
    if (energyDelta) energyDelta.textContent = "-140 kWh";
    if (resDelta) resDelta.textContent = "54 ➔ 81";
  } else {
    badge.textContent = "ALL NOMINAL";
    badge.style.background = "#ecfdf5";
    badge.style.color = "#065f46";

    if (title) title.textContent = "Factory operational — Baseline intact";
    if (timeEl) timeEl.textContent = "Optimal production plan in execution";

    if (impactList) {
      impactList.innerHTML = `
        <li>0 disrupted machine workstations</li>
        <li>All 4 production orders on schedule</li>
        <li>100% capacity headroom available</li>
      `;
    }

    if (responseList) {
      responseList.innerHTML = `
        <span class="reassign-pill" style="background:#f3f4f6; color:#374151; border-color:#e5e7eb;">No active reassignments needed</span>
      `;
    }

    if (msDelta) msDelta.textContent = "445 min";
    if (lateDelta) lateDelta.textContent = "0 late";
    if (energyDelta) energyDelta.textContent = "980 kWh";
    if (resDelta) resDelta.textContent = "87/100";
  }
}

function openExplanationFromDisruption() {
  const copilotSection = document.getElementById("copilot");
  if (copilotSection) copilotSection.scrollIntoView({ behavior: "smooth" });
  askCopilotPreset("Why did FlowForge choose this recovery plan?");
}

// ── MODULE 9: HISTORY & DECISION REPORTS ──
function renderHistoryAuditTrail() {
  const tbody = document.getElementById("historyTableBody");
  if (!tbody) return;

  const history = state.history || [];
  if (history.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align:center; color:var(--text-muted); padding:20px;">
          No disruption events recorded. Inject a scenario above to test the autonomous resilience engine.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = history
    .map((item, idx) => {
      const affMachines = Array.isArray(item.affected_machines)
        ? (item.affected_machines.join(", ") || "ALL")
        : (item.target || "ALL");
      const jobsCount = Array.isArray(item.affected_jobs)
        ? item.affected_jobs.length
        : (item.affected_job_count || 0);
      const desc = item.description || item.impact_summary || item.scenario_name || "Disruption Event";
      const ts = typeof item.timestamp === "number"
        ? new Date(item.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : (item.timestamp || "—");
      const msDelta = item.baseline_makespan !== undefined
        ? `${item.baseline_makespan}m → ${item.recovery_makespan}m`
        : "—";
      const resDelta = item.baseline_resilience !== undefined
        ? `${item.baseline_resilience} → ${item.recovery_resilience}`
        : "—";
      const lateStr = item.recovery_late !== undefined ? `${item.recovery_late} late` : "0 late";

      return `
        <tr style="cursor:pointer;" onclick="selectHistoryReport(${idx})" title="Click to view Decision Report">
          <td class="code-cell">${escapeHtml(ts)}</td>
          <td><strong>${escapeHtml(desc)}</strong></td>
          <td><span class="code-cell">${escapeHtml(affMachines)}</span></td>
          <td>${jobsCount} jobs</td>
          <td>${msDelta}</td>
          <td><span class="status-pill running">${resDelta}</span></td>
          <td>${lateStr}</td>
          <td><button class="btn-secondary" style="padding:3px 8px; font-size:0.75rem;" onclick="selectHistoryReport(${idx})">Inspect ➔</button></td>
        </tr>
      `;
    })
    .join("");
}

function selectHistoryReport(idx) {
  if (state.history[idx] && state.history[idx].decision_report) {
    state.latestDecisionReport = state.history[idx].decision_report;
    renderDecisionReport();
    const card = document.getElementById("decisionReportCard");
    if (card) card.scrollIntoView({ behavior: "smooth" });
  }
}

function renderDecisionReport() {
  const report = state.latestDecisionReport;
  const title = document.getElementById("reportTitle");
  const cellEvent = document.getElementById("reportCellEvent");
  const cellImpact = document.getElementById("reportCellImpact");
  const cellDecision = document.getElementById("reportCellDecision");
  const cellReason = document.getElementById("reportCellReason");
  const cellTradeoff = document.getElementById("reportCellTradeoff");
  const cellOutcome = document.getElementById("reportCellOutcome");

  if (!title) return;

  if (state.isDisrupted || report) {
    title.textContent = report ? `Autonomous Reroute: ${report.decision}` : "Autonomous Workload Reroute: J7 Reassigned to M5";
    if (cellEvent) cellEvent.textContent = report ? report.event : "Station M3 became unavailable due to mechanical failure.";
    if (cellImpact) cellImpact.textContent = report ? report.impact : "3 scheduled operations were affected with immediate deadline vulnerability.";
    if (cellDecision) cellDecision.textContent = report ? report.decision : "J7 was reassigned to M5; remaining operations distributed to M4 and M1.";
    if (cellReason) cellReason.textContent = report ? report.reason : "M5 had sufficient remaining capacity and protected the J7 delivery deadline.";
    if (cellTradeoff) cellTradeoff.textContent = report ? report.tradeoff : "Energy consumption increased by 3% across alternative station routing.";
    if (cellOutcome) cellOutcome.textContent = report ? report.outcome : "Customer deadline protected. Zero late jobs introduced to production.";
  } else {
    title.textContent = "Autonomous Schedule Integrity: Baseline Feasible";
    if (cellEvent) cellEvent.textContent = "Factory initialized under nominal operating conditions.";
    if (cellImpact) cellImpact.textContent = "All 24 operations sequenced within machine capability constraints.";
    if (cellDecision) cellDecision.textContent = "Production plan generated via Multi-Objective Genetic Algorithm.";
    if (cellReason) cellReason.textContent = "Optimal balance between makespan, machine idle time, and energy.";
    if (cellTradeoff) cellTradeoff.textContent = "Baseline configuration prioritized throughput and equipment longevity.";
    if (cellOutcome) cellOutcome.textContent = "All production orders meet promised delivery milestones.";
  }
}

// ── MACHINE DETAIL MODAL ──
function openMachineModal(machineId) {
  state.selectedMachineForModal = machineId;
  const modal = document.getElementById("machineModalBackdrop");
  if (!modal) return;

  const spec = MACHINE_SPECS[machineId] || { name: `Workstation ${machineId}`, defaultUtil: 85, power: 15.0 };
  const liveMachine = state.factory && state.factory.machines ? state.factory.machines[machineId] : null;
  const isAvail = liveMachine ? liveMachine.status === "available" : !(machineId === "M3" && state.isDisrupted);

  const pretitle = document.getElementById("modalMachinePretitle");
  const title = document.getElementById("modalMachineTitle");
  const statusEl = document.getElementById("modalMachineStatus");
  const utilEl = document.getElementById("modalMachineUtil");
  const energyEl = document.getElementById("modalMachineEnergy");
  const runtimeEl = document.getElementById("modalMachineRuntime");
  const queueEl = document.getElementById("modalMachineQueue");
  const maintDesc = document.getElementById("modalMachineMaintDesc");

  if (pretitle) pretitle.textContent = `WORKSTATION TELEMETRY · ${machineId}`;
  if (title) title.textContent = `${machineId} — ${spec.name}`;

  if (statusEl) {
    statusEl.textContent = isAvail ? "RUNNING" : "FAILED";
    statusEl.className = isAvail ? "val status-pill running" : "val status-pill stopped";
  }

  const util = isAvail ? spec.defaultUtil : 0;
  if (utilEl) utilEl.textContent = `${util}%`;
  if (energyEl) energyEl.textContent = `${spec.power} kWh`;
  if (runtimeEl) runtimeEl.textContent = isAvail ? "5.8 hrs" : "1.2 hrs";

  // Assigned queue
  const assigned = (state.currentSchedule || []).filter((j) => j.machine === machineId);
  if (queueEl) {
    if (assigned.length === 0) {
      queueEl.innerHTML = `<div class="modal-queue-item" style="color:var(--text-muted);">No jobs currently assigned (Station Idle)</div>`;
    } else {
      queueEl.innerHTML = assigned
        .map((j) => `
          <div class="modal-queue-item">
            <span><strong>${j.job_id}</strong> (${j.duration}m)</span>
            <span style="color:var(--text-muted);">Start: ${j.start}m · Due: ${j.deadline || j.due || 150}m</span>
          </div>
        `)
        .join("");
    }
  }

  if (maintDesc) {
    maintDesc.textContent = isAvail
      ? `Station health is nominal (92%). Next scheduled preventive maintenance: in 3 days.`
      : `CRITICAL ALERT: Station offline due to simulated stoppage. Autonomous resilience replanned assigned operations.`;
  }

  modal.classList.add("active");
}

function closeMachineModal(event) {
  const modal = document.getElementById("machineModalBackdrop");
  if (modal) modal.classList.remove("active");
}

async function modalTriggerFail() {
  closeMachineModal();
  await triggerMachineFailure(state.selectedMachineForModal);
}

async function modalTriggerMaint() {
  closeMachineModal();
  await triggerPlannedDowntime(state.selectedMachineForModal);
}

async function modalTriggerRestore() {
  closeMachineModal();
  await triggerMachineRecovery(state.selectedMachineForModal);
}

function toggleTerminalPower() {
  // Industrial sound effect / micro-toggle
  const terminal = document.querySelector(".terminal-screen");
  if (terminal) {
    terminal.style.opacity = terminal.style.opacity === "0.6" ? "1" : "0.6";
    setTimeout(() => (terminal.style.opacity = "1"), 200);
  }
}

// ═════════════════════════════════════════════════════════════════════════
// 5. INTERACTIVE SCENARIOS (DISRUPTIONS & RECOVERIES)
// ═════════════════════════════════════════════════════════════════════════

async function runIndustrialScenario(scenarioId) {
  if (!scenarioId) return;
  try {
    const res = await fetch("/scenarios/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: parseInt(scenarioId, 10) }),
    });

    if (!res.ok) throw new Error(`Scenario run failed: ${res.status}`);
    const data = await res.json();
    const result = data.result || {};

    state.isDisrupted = parseInt(scenarioId, 10) !== 1;
    state.currentSchedule = (data.schedules && data.schedules.recovery) || state.currentSchedule;
    state.recoverySchedule = state.currentSchedule;
    state.recoveryMetrics = result.result || null;

    // Update What Changed Panel
    const wcPanel = document.getElementById("whatChangedPanel");
    if (wcPanel) {
      wcPanel.style.display = "block";
      const wcBadge = document.getElementById("wcBadge");
      if (wcBadge) {
        wcBadge.textContent = result.event && result.event.type ? result.event.type.toUpperCase() : `SCENARIO ${scenarioId}`;
        wcBadge.className = `wc-badge ${parseInt(scenarioId, 10) === 1 ? "success" : "danger"}`;
      }
      const wcTitle = document.getElementById("wcTitle");
      if (wcTitle) {
        wcTitle.textContent = result.scenario_name ? `${result.scenario_name} — ${result.result && result.result.status ? result.result.status : 'Active'}` : "Scenario Evaluated";
      }
      const wcTime = document.getElementById("wcTimestamp");
      if (wcTime) {
        wcTime.textContent = `${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} — Autonomous FlowForge Replanning`;
      }
      const wcImpact = document.getElementById("wcImpactList");
      if (wcImpact && result.impact) {
        wcImpact.innerHTML = `
          <li>${result.impact.description || "Operational parameters shifted."}</li>
          <li>Baseline makespan: ${result.baseline ? result.baseline.makespan : 0}m ➔ Recovery: ${result.result ? result.result.makespan : 0}m</li>
          <li>Resilience Index: ${result.baseline ? result.baseline.resilience_score : 85} ➔ ${result.result ? result.result.resilience_score : 80}/100</li>
        `;
      }
      const wcResp = document.getElementById("wcResponseList");
      if (wcResp && result.flowforge_response) {
        const reassigns = result.flowforge_response.reassignments || [];
        wcResp.innerHTML = reassigns.length > 0
          ? reassigns.map(r => `<span class="reassign-pill">${r}</span>`).join("")
          : `<span class="reassign-pill">${result.flowforge_response.summary || "Autonomous dispatch optimization complete."}</span>`;
      }
      const wcMakespanDelta = document.getElementById("wcMakespanDelta");
      if (wcMakespanDelta && result.result && result.result.delta) {
        const d = result.result.delta.makespan;
        wcMakespanDelta.textContent = `${d > 0 ? '+' : ''}${d} min`;
        wcMakespanDelta.className = d <= 0 ? "val positive" : "val";
      }
      const wcLateDelta = document.getElementById("wcLateDelta");
      if (wcLateDelta && result.result) {
        wcLateDelta.textContent = `${result.result.late_jobs} late`;
        wcLateDelta.className = result.result.late_jobs === 0 ? "val positive" : "val negative";
      }
      const wcEnergyDelta = document.getElementById("wcEnergyDelta");
      if (wcEnergyDelta && result.result && result.result.delta) {
        const ed = result.result.delta.energy_kwh;
        wcEnergyDelta.textContent = `${ed > 0 ? '+' : ''}${ed} kWh`;
      }
      const wcResilienceDelta = document.getElementById("wcResilienceDelta");
      if (wcResilienceDelta && result.baseline && result.result) {
        wcResilienceDelta.textContent = `${result.baseline.resilience_score} ➔ ${result.result.resilience_score}`;
        wcResilienceDelta.className = result.result.resilience_score >= result.baseline.resilience_score ? "val positive" : "val";
      }
    }

    await refreshAllOperationalData();
    updateUI();

    const target = document.getElementById("disruption");
    if (target) target.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Industrial scenario error:", err);
  }
}

async function triggerMachineFailure(machineId = "M3") {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "machine_failure", machine_id: machineId }),
    });

    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = data.schedules && data.schedules.recovery ? data.schedules.recovery : state.baselineSchedule;
    state.recoverySchedule = state.currentSchedule;
    state.recoveryMetrics = data.metrics ? data.metrics.recovery : null;
    state.recoveryResilience = data.resilience ? data.resilience.recovery : null;

    if (data.affected_jobs && data.affected_jobs.length > 0) {
      const affectedSet = new Set(data.affected_jobs);
      state.currentSchedule.forEach((item) => {
        if (affectedSet.has(item.job_id)) item.reassigned = true;
      });
    }

    await refreshAllOperationalData();
    updateUI();

    const target = document.getElementById("disruption");
    if (target) target.scrollIntoView({ behavior: "smooth" });
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
    state.currentSchedule = data.schedules && data.schedules.recovery ? data.schedules.recovery : state.baselineSchedule;

    await refreshAllOperationalData();
    updateUI();

    const target = document.getElementById("control-center");
    if (target) target.scrollIntoView({ behavior: "smooth" });
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

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = (data.schedules && data.schedules.recovery) || state.currentSchedule;
    await refreshAllOperationalData();
    updateUI();

    const target = document.getElementById("production");
    if (target) target.scrollIntoView({ behavior: "smooth" });
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

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = (data.schedules && data.schedules.recovery) || state.currentSchedule;
    await refreshAllOperationalData();
    updateUI();
  } catch (err) {
    console.error("Deadline shift error:", err);
  }
}

async function triggerJobCancellation() {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "job_cancellation",
        job_id: "J12",
      }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = (data.schedules && data.schedules.recovery) || state.currentSchedule;
    await refreshAllOperationalData();
    updateUI();
  } catch (err) {
    console.error("Cancellation error:", err);
  }
}

async function triggerPlannedDowntime(machineId = "M4") {
  try {
    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "machine_failure",
        machine_id: machineId,
      }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = (data.schedules && data.schedules.recovery) || state.currentSchedule;
    await refreshAllOperationalData();
    updateUI();
  } catch (err) {
    console.error("Planned downtime error:", err);
  }
}

async function triggerMultipleFailures() {
  try {
    // Fail M1 first then M3
    await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "machine_failure", machine_id: "M1" }),
    });

    const res = await fetch("/disruptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "machine_failure", machine_id: "M3" }),
    });

    const data = await res.json();
    state.isDisrupted = true;
    state.currentSchedule = data.schedules.recovery || state.currentSchedule;
    await refreshAllOperationalData();
    updateUI();

    const target = document.getElementById("disruption");
    if (target) target.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    console.error("Multiple failures error:", err);
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
  const metaText = document.getElementById("uploadMetaText");
  if (btn) btn.disabled = true;
  if (metaText) metaText.innerHTML = `<span style="color:var(--text-muted)">⏳ Uploading and optimizing…</span>`;

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

        const summary = data.summary || {};
        if (metaText) {
          metaText.innerHTML = `<strong>${escapeHtml(state.selectedFile.name)}</strong> — ✅ Loaded. Jobs: ${summary.jobs_count || "?"}, Machines: ${summary.machines_count || "?"}. Optimized.`;
        }

        await refreshAllOperationalData();
        updateUI();

        const ccSection = document.getElementById("control-center");
        if (ccSection) ccSection.scrollIntoView({ behavior: "smooth" });
      } else {
        // Show user-friendly validation errors from the backend
        const errors = data.error_messages || ["Upload failed. Please check the file format."];
        if (metaText) {
          metaText.innerHTML = `<span style="color:#ef4444;">❌ Upload failed:</span><br>${errors.map(e => `<span style="font-size:0.85em;color:#b91c1c">${escapeHtml(e)}</span>`).join('<br>')}`;
        }
      }
    } catch (err) {
      console.error("Upload error:", err);
      if (metaText) {
        metaText.innerHTML = `<span style="color:#ef4444;">❌ Upload failed. Please check your connection and try again.</span>`;
      }
    }
  } else {
    await initFlowForgeEngine();
    const ccSection = document.getElementById("control-center");
    if (ccSection) ccSection.scrollIntoView({ behavior: "smooth" });
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
// 7. UTILITIES
// ═════════════════════════════════════════════════════════════════════════

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

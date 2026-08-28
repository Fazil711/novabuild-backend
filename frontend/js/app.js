import { ApiClient, BACKEND_URL } from "./api.js";
import { AuthManager } from "./auth.js";
import { renderBlueprint } from "./blueprint.js";
import { CodeViewer } from "./code-viewer.js";
import { IterationManager } from "./iterate.js";

// Global Application State
let currentPlan = null;
let activeProjectId = null;

// Initialize components
const authManager = new AuthManager(onAuthStateChanged);
const codeViewer = new CodeViewer("file-tree-container", "code-view-container", "active-filename", "copy-code-btn", "download-zip-btn");
const iterationManager = new IterationManager("iterate-project-select", "iterate-prompt-input", "iterate-submit-btn", "iterate-diff-output", onIterateDone);

// DOM Elements
const backendStatusBadge = document.getElementById("backend-status-badge");
const authBtn = document.getElementById("auth-toggle-btn");
const authModal = document.getElementById("auth-modal");
const authModalClose = document.getElementById("auth-modal-close");
const authForm = document.getElementById("auth-form");
const authToggleLink = document.getElementById("auth-toggle-link");
const authModalTitle = document.getElementById("auth-modal-title");
const authFullNameContainer = document.getElementById("auth-fullname-container");
const authSubmitBtn = document.getElementById("auth-submit-btn");

const promptInput = document.getElementById("prompt-input");
const generatePlanBtn = document.getElementById("generate-plan-btn");
const streamProgressContainer = document.getElementById("stream-progress-container");
const streamProgressBar = document.getElementById("stream-progress-bar");
const streamProgressText = document.getElementById("stream-progress-text");
const streamPercentText = document.getElementById("stream-percent-text");
const blueprintContainer = document.getElementById("blueprint-container");

const navTabs = document.querySelectorAll(".nav-tab");
const viewSections = document.querySelectorAll(".view-section");

let isSignUpMode = false;

// ---- Lifecycle & Initialization ----
document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  initTabNavigation();
  initAuthModal();
  initPromptPresets();
  initPlanGeneration();
});

// Toast notification helper
export function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  const bg = type === "error" ? "bg-red-600 text-white" : type === "success" ? "bg-emerald-600 text-white" : "bg-indigo-600 text-white";
  toast.className = `p-4 rounded-xl shadow-xl flex items-center gap-3 text-xs font-medium toast-animate ${bg}`;
  toast.innerHTML = `<span>✦</span> <span>${message}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Health check poller
async function initHealthCheck() {
  async function check() {
    const health = await ApiClient.checkHealth();
    if (health && health.status === "ok") {
      backendStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> <span class="text-emerald-400 font-medium">Backend Live</span>`;
    } else {
      backendStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500"></span> <span class="text-rose-400 font-medium">Backend Offline</span>`;
    }
  }
  check();
  setInterval(check, 10000);
}

// Tab Switching
function initTabNavigation() {
  navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetView = tab.dataset.view;
      switchView(targetView);
    });
  });
}

export function switchView(targetView) {
  navTabs.forEach(t => {
    if (t.dataset.view === targetView) {
      t.classList.add("bg-indigo-600/20", "text-indigo-400", "border-indigo-500/50");
      t.classList.remove("text-gray-400", "border-transparent");
    } else {
      t.classList.remove("bg-indigo-600/20", "text-indigo-400", "border-indigo-500/50");
      t.classList.add("text-gray-400", "border-transparent");
    }
  });

  viewSections.forEach(sec => {
    if (sec.id === `view-${targetView}`) {
      sec.classList.remove("hidden");
    } else {
      sec.classList.add("hidden");
    }
  });

  if (targetView === "projects") {
    loadProjectsList();
  } else if (targetView === "iterate") {
    iterationManager.populateProjects(activeProjectId);
  }
}

// ---- Auth Modal & Flow ----
function initAuthModal() {
  authBtn.addEventListener("click", () => {
    if (authManager.currentUser) {
      if (confirm(`Logged in as ${authManager.currentUser.email}. Do you want to logout?`)) {
        authManager.logout();
        showToast("Logged out successfully", "info");
      }
    } else {
      authModal.classList.remove("hidden");
    }
  });

  authModalClose.addEventListener("click", () => authModal.classList.add("hidden"));

  authToggleLink.addEventListener("click", (e) => {
    e.preventDefault();
    isSignUpMode = !isSignUpMode;
    authModalTitle.textContent = isSignUpMode ? "Create an Account" : "Sign In to NovaBuild";
    authFullNameContainer.classList.toggle("hidden", !isSignUpMode);
    authSubmitBtn.textContent = isSignUpMode ? "Sign Up" : "Sign In";
    authToggleLink.textContent = isSignUpMode ? "Already have an account? Sign In" : "Need an account? Sign Up";
  });

  authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    const fullName = document.getElementById("auth-fullname").value.trim();

    authSubmitBtn.disabled = true;
    try {
      if (isSignUpMode) {
        await authManager.register(email, password, fullName);
        showToast("Account created successfully!", "success");
      } else {
        await authManager.login(email, password);
        showToast("Welcome back!", "success");
      }
      authModal.classList.add("hidden");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      authSubmitBtn.disabled = false;
    }
  });
}

function onAuthStateChanged(user) {
  if (user) {
    authBtn.innerHTML = `
      <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
      <span class="font-medium truncate max-w-[120px]">${user.email}</span>
    `;
    authBtn.classList.add("border-emerald-500/30", "bg-emerald-950/20");
  } else {
    authBtn.innerHTML = `<span>Sign In</span>`;
    authBtn.classList.remove("border-emerald-500/30", "bg-emerald-950/20");
  }
}

// ---- Prompt Presets ----
function initPromptPresets() {
  const presets = document.querySelectorAll(".prompt-preset-chip");
  presets.forEach(chip => {
    chip.addEventListener("click", () => {
      promptInput.value = chip.dataset.prompt;
      promptInput.focus();
    });
  });
}

// ---- Plan Generation & SSE Streaming ----
function initPlanGeneration() {
  generatePlanBtn.addEventListener("click", () => {
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showToast("Please enter an application idea", "error");
      return;
    }

    generatePlanBtn.disabled = true;
    generatePlanBtn.innerHTML = `<span>⏳ Synthesizing Blueprint...</span>`;
    streamProgressContainer.classList.remove("hidden");
    streamProgressBar.style.width = "5%";
    streamProgressText.textContent = "Connecting to NovaBuild Blueprint Engine...";
    streamPercentText.textContent = "5%";

    ApiClient.generatePlanStream(
      prompt,
      (event) => {
        streamProgressBar.style.width = `${event.percent}%`;
        streamProgressText.textContent = event.message || "Synthesizing...";
        streamPercentText.textContent = `${event.percent}%`;
      },
      (error) => {
        showToast(`Generation error: ${error}`, "error");
        generatePlanBtn.disabled = false;
        generatePlanBtn.innerHTML = `<span>✨ Generate Blueprint</span>`;
      },
      (blueprint) => {
        currentPlan = blueprint;
        renderBlueprint(blueprint, blueprintContainer);
        showToast("Blueprint synthesized successfully!", "success");
        generatePlanBtn.disabled = false;
        generatePlanBtn.innerHTML = `<span>✨ Generate Blueprint</span>`;

        // Attach event listener to "Approve & Generate Code"
        const approveBtn = document.getElementById("approve-build-btn");
        if (approveBtn) {
          approveBtn.addEventListener("click", handleApproveAndBuild);
        }
      }
    );
  });
}

// ---- Approve & Build Handler ----
async function handleApproveAndBuild() {
  if (!currentPlan) return;
  const btn = document.getElementById("approve-build-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳ Generating Next.js Codebase & Supabase Schema...</span>`;
  }

  try {
    const result = await ApiClient.buildProject(currentPlan);
    activeProjectId = result.project_id;
    showToast("Application generated successfully!", "success");

    // Open Code Viewer tab with the generated project
    switchView("code");
    codeViewer.loadProject(result.project_id);
  } catch (err) {
    showToast(`Build error: ${err.message}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>🚀 Approve & Generate Code</span>`;
    }
  }
}

// ---- Projects List Renderer ----
async function loadProjectsList() {
  const container = document.getElementById("projects-grid");
  if (!container) return;
  container.innerHTML = `<div class="col-span-full p-8 text-center text-gray-500">Loading projects...</div>`;

  try {
    const projects = await ApiClient.listProjects();
    if (!projects.length) {
      container.innerHTML = `
        <div class="col-span-full p-12 text-center glass-card rounded-2xl border border-slate-800">
          <p class="text-gray-400 mb-4">No projects generated yet.</p>
          <button onclick="window.novabuildSwitchView('studio')" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold">
            Create Your First App
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = projects.map(p => `
      <div class="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col justify-between hover:border-indigo-500/40 transition-all">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${p.type}</span>
            <span class="text-[11px] font-mono text-gray-400">v${p.version || 1}</span>
          </div>
          <h3 class="text-base font-bold text-white mb-1 truncate">${p.app_name}</h3>
          <p class="text-xs font-mono text-gray-500 mb-3 truncate">ID: ${p.project_id}</p>
          <p class="text-xs text-gray-400 mb-4">${(p.created_files || []).length} generated files (Next.js + SQL)</p>
        </div>

        <div class="flex items-center gap-2 pt-3 border-t border-slate-800/80">
          <button class="open-project-btn flex-1 py-1.5 px-3 rounded-lg bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 hover:text-white text-xs font-bold transition-colors" data-id="${p.project_id}">
            Code View
          </button>
          <button class="iterate-project-btn py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors" data-id="${p.project_id}">
            Iterate
          </button>
          <a href="${ApiClient.getDownloadUrl(p.project_id)}" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors" title="Download ZIP">
            📦
          </a>
        </div>
      </div>
    `).join("");

    // Bind card buttons
    container.querySelectorAll(".open-project-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        activeProjectId = btn.dataset.id;
        switchView("code");
        codeViewer.loadProject(btn.dataset.id);
      });
    });

    container.querySelectorAll(".iterate-project-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        activeProjectId = btn.dataset.id;
        switchView("iterate");
      });
    });
  } catch (err) {
    container.innerHTML = `<div class="col-span-full p-8 text-center text-red-400">Failed to load projects: ${err.message}</div>`;
  }
}

function onIterateDone(res) {
  showToast(`Project updated to v${res.version}!`, "success");
  activeProjectId = res.project_id;
}

// Expose switch view globally for inline button handlers
window.novabuildSwitchView = switchView;

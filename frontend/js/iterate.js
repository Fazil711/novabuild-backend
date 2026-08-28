import { ApiClient } from "./api.js";

export class IterationManager {
  constructor(selectId, promptInputId, submitBtnId, diffOutputId, onIterateComplete) {
    this.projectSelect = document.getElementById(selectId);
    this.promptInput = document.getElementById(promptInputId);
    this.submitBtn = document.getElementById(submitBtnId);
    this.diffOutput = document.getElementById(diffOutputId);
    this.onIterateComplete = onIterateComplete;

    if (this.submitBtn) {
      this.submitBtn.addEventListener("click", () => this.handleIterate());
    }
  }

  async populateProjects(selectedId = null) {
    if (!this.projectSelect) return;
    try {
      const projects = await ApiClient.listProjects();
      this.projectSelect.innerHTML = projects.map(p => `
        <option value="${p.project_id}" ${p.project_id === selectedId ? "selected" : ""}>
          ${p.app_name} (v${p.version || 1}) - ${p.project_id.slice(0, 8)}
        </option>
      `).join("");
    } catch (err) {
      console.error("Failed to populate iteration projects:", err);
    }
  }

  async handleIterate() {
    const projectId = this.projectSelect ? this.projectSelect.value : null;
    const instruction = this.promptInput ? this.promptInput.value.trim() : "";

    if (!projectId) {
      alert("Please select a project to iterate on.");
      return;
    }
    if (!instruction) {
      alert("Please enter a modification instruction.");
      return;
    }

    this.submitBtn.disabled = true;
    this.submitBtn.innerHTML = `<span>⏳ Applying Changes...</span>`;
    this.diffOutput.innerHTML = `<div class="p-6 text-center text-indigo-400">Analyzing instruction and computing incremental diffs...</div>`;

    try {
      const res = await ApiClient.iterateProject(projectId, instruction);
      this.renderDiffResult(res);
      this.promptInput.value = "";
      if (this.onIterateComplete) {
        this.onIterateComplete(res);
      }
    } catch (err) {
      this.diffOutput.innerHTML = `<div class="p-4 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-xs">${err.message}</div>`;
    } finally {
      this.submitBtn.disabled = false;
      this.submitBtn.innerHTML = `<span>Apply Update</span>`;
    }
  }

  renderDiffResult(res) {
    const opsHtml = (res.operations || []).map(op => {
      let badge = "bg-blue-900/40 text-blue-300 border-blue-700";
      if (op.op.startsWith("add")) badge = "bg-emerald-900/40 text-emerald-300 border-emerald-700";
      if (op.op.startsWith("remove")) badge = "bg-rose-900/40 text-rose-300 border-rose-700";

      return `
        <div class="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs font-mono">
          <span class="px-2 py-0.5 rounded text-[11px] border ${badge}">${op.op}</span>
          <span class="text-slate-300">${op.entity ? op.entity.name : op.entity_name || op.feature || op.app_name || "-"}</span>
        </div>
      `;
    }).join("");

    const changedHtml = (res.changed_files || []).map(f => `<span class="px-2 py-1 rounded bg-slate-800 text-indigo-300 text-xs font-mono">✎ ${f}</span>`).join(" ");
    const removedHtml = (res.removed_files || []).map(f => `<span class="px-2 py-1 rounded bg-rose-950 text-rose-400 text-xs font-mono">🗑 ${f}</span>`).join(" ");

    this.diffOutput.innerHTML = `
      <div class="space-y-4 p-5 rounded-xl bg-slate-900 border border-indigo-500/30">
        <div class="flex items-center justify-between">
          <h4 class="font-bold text-white text-sm">✓ Project Bumped to v${res.version}</h4>
          <span class="text-xs text-gray-400 font-mono">${res.project_id.slice(0, 8)}</span>
        </div>

        <div>
          <p class="text-xs font-bold uppercase text-gray-400 mb-2">Applied Operations</p>
          <div class="space-y-1.5">${opsHtml}</div>
        </div>

        <div class="pt-3 border-t border-slate-800 space-y-2">
          ${changedHtml ? `<div><p class="text-xs text-gray-400 mb-1">Updated Files:</p><div class="flex flex-wrap gap-1.5">${changedHtml}</div></div>` : ""}
          ${removedHtml ? `<div><p class="text-xs text-gray-400 mb-1">Removed Files:</p><div class="flex flex-wrap gap-1.5">${removedHtml}</div></div>` : ""}
        </div>
      </div>
    `;
  }
}

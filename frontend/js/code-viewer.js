import { ApiClient } from "./api.js";

export class CodeViewer {
  constructor(treeContainerId, codeContainerId, filenameHeaderId, copyBtnId, downloadBtnId) {
    this.treeContainer = document.getElementById(treeContainerId);
    this.codeContainer = document.getElementById(codeContainerId);
    this.filenameHeader = document.getElementById(filenameHeaderId);
    this.copyBtn = document.getElementById(copyBtnId);
    this.downloadBtn = document.getElementById(downloadBtnId);

    this.currentProjectId = null;
    this.currentFilePath = null;
    this.currentCode = "";

    if (this.copyBtn) {
      this.copyBtn.addEventListener("click", () => this.copyCurrentCode());
    }
  }

  async loadProject(projectId) {
    this.currentProjectId = projectId;
    if (this.downloadBtn) {
      this.downloadBtn.href = ApiClient.getDownloadUrl(projectId);
      this.downloadBtn.classList.remove("hidden");
    }

    try {
      const project = await ApiClient.getProject(projectId);
      const files = Object.keys(project.files || {}).sort();
      this.renderFileTree(files);

      // Default select first meaningful file
      const defaultFile = files.find(f => f.includes("layout.tsx")) || files.find(f => f.includes("schema.sql")) || files[0];
      if (defaultFile) {
        this.loadFile(defaultFile);
      }
    } catch (err) {
      this.codeContainer.innerHTML = `<div class="p-8 text-center text-red-400">Failed to load project files: ${err.message}</div>`;
    }
  }

  renderFileTree(files) {
    if (!this.treeContainer) return;
    this.treeContainer.innerHTML = "";

    const ul = document.createElement("ul");
    ul.className = "space-y-1 text-xs font-mono";

    files.forEach(file => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.className = "w-full text-left px-3 py-1.5 rounded-lg text-slate-300 hover:bg-slate-800/80 hover:text-white flex items-center gap-2 transition-colors";
      button.dataset.filepath = file;

      let icon = "📄";
      if (file.endsWith(".tsx") || file.endsWith(".ts")) icon = "⚛️";
      else if (file.endsWith(".json")) icon = "📦";
      else if (file.endsWith(".sql")) icon = "🗄️";
      else if (file.endsWith(".css")) icon = "🎨";
      else if (file.endsWith(".md")) icon = "📝";

      button.innerHTML = `<span class="text-xs">${icon}</span> <span class="truncate">${file}</span>`;
      button.addEventListener("click", () => {
        this.treeContainer.querySelectorAll("button").forEach(b => b.classList.remove("bg-indigo-600/30", "text-indigo-300", "font-bold"));
        button.classList.add("bg-indigo-600/30", "text-indigo-300", "font-bold");
        this.loadFile(file);
      });

      li.appendChild(button);
      ul.appendChild(li);
    });

    this.treeContainer.appendChild(ul);
  }

  async loadFile(filePath) {
    this.currentFilePath = filePath;
    if (this.filenameHeader) {
      this.filenameHeader.textContent = filePath;
    }

    try {
      const code = await ApiClient.getProjectFile(this.currentProjectId, filePath);
      this.currentCode = code;
      this.renderCode(code);
    } catch (err) {
      this.codeContainer.innerHTML = `<div class="p-8 text-center text-red-400">Failed to load file: ${err.message}</div>`;
    }
  }

  renderCode(code) {
    if (!this.codeContainer) return;
    const lines = code.split("\n");
    const escapedLines = lines.map(line => {
      const safe = line
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      return `<div>${safe || " "}</div>`;
    }).join("");

    this.codeContainer.innerHTML = `
      <pre class="line-numbers text-slate-200"><code class="block font-mono text-xs">${escapedLines}</code></pre>
    `;
  }

  copyCurrentCode() {
    if (!this.currentCode) return;
    navigator.clipboard.writeText(this.currentCode).then(() => {
      if (this.copyBtn) {
        const orig = this.copyBtn.innerHTML;
        this.copyBtn.innerHTML = `<span>✓ Copied!</span>`;
        setTimeout(() => { this.copyBtn.innerHTML = orig; }, 2000);
      }
    });
  }
}

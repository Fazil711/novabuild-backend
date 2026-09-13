// NovaBuild In-Browser Interactive App Preview Engine (Clean Dark System)

export class PreviewRunner {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.plan = null;
    this.activeRoute = "/";
    this.deviceMode = "desktop"; // "desktop" | "tablet" | "mobile"
    this.db = {}; // In-memory entity data stores: { [entityPlural]: Array<Object> }
    this.searchTerm = "";
    this.isAddModalOpen = false;
    this.user = { email: "alex@example.com", role: "admin" };
  }

  loadPlan(plan) {
    if (!plan) return;
    this.plan = plan;
    this.activeRoute = "/";
    this.searchTerm = "";
    this.initMockDatabase();
    this.render();
  }

  initMockDatabase() {
    this.db = {};
    const entities = this.plan.entities || [];
    
    entities.forEach(entity => {
      const table = entity.plural.toLowerCase();
      this.db[table] = this.generateSampleRecords(entity);
    });
  }

  generateSampleRecords(entity) {
    const records = [];
    const sampleNames = ["Alpha", "Beta", "Gamma", "Prime", "Nexus", "Apex"];
    
    for (let i = 1; i <= 3; i++) {
      const row = {
        id: `rec_${entity.name.toLowerCase()}_${i}`,
        created_at: new Date(Date.now() - i * 86400000).toISOString().split("T")[0],
      };
      
      (entity.fields || []).forEach(f => {
        if (f.type === "number") {
          row[f.name] = (i * 250) + 50;
        } else if (f.type === "boolean") {
          row[f.name] = i % 2 === 1;
        } else if (f.type === "date") {
          row[f.name] = new Date().toISOString().split("T")[0];
        } else if (f.type === "select") {
          row[f.name] = (f.options && f.options.length) ? f.options[(i - 1) % f.options.length] : "Active";
        } else if (f.type === "textarea") {
          row[f.name] = `Operational summary and notes for ${entity.name} #${i}.`;
        } else {
          row[f.name] = `${sampleNames[i - 1]} ${entity.name} #${i}`;
        }
      });
      records.push(row);
    }
    return records;
  }

  setDeviceMode(mode) {
    this.deviceMode = mode;
    this.render();
  }

  setRoute(route) {
    this.activeRoute = route;
    this.searchTerm = "";
    this.isAddModalOpen = false;
    this.render();
  }

  addRecord(entityName, formData) {
    const entity = (this.plan.entities || []).find(e => e.name.toLowerCase() === entityName.toLowerCase());
    if (!entity) return;
    
    const table = entity.plural.toLowerCase();
    const newRecord = {
      id: `rec_${entity.name.toLowerCase()}_${Date.now()}`,
      created_at: new Date().toISOString().split("T")[0],
      ...formData
    };

    if (!this.db[table]) this.db[table] = [];
    this.db[table].unshift(newRecord);
    this.isAddModalOpen = false;
    this.render();
  }

  deleteRecord(entityName, recordId) {
    const entity = (this.plan.entities || []).find(e => e.name.toLowerCase() === entityName.toLowerCase());
    if (!entity) return;
    
    const table = entity.plural.toLowerCase();
    this.db[table] = (this.db[table] || []).filter(r => r.id !== recordId);
    this.render();
  }

  render() {
    if (!this.container) return;
    if (!this.plan) {
      this.container.innerHTML = `
        <div class="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500">
          <span class="text-2xl mb-2 text-zinc-400">⚡</span>
          <p class="text-sm font-medium text-zinc-300">No Application Loaded in Preview</p>
          <p class="text-xs text-zinc-500 mt-1">Generate a blueprint to interact with the simulated application.</p>
        </div>
      `;
      return;
    }

    const { app_name, type, entities = [] } = this.plan;

    // Viewport Width constraints based on deviceMode
    const widthClass = this.deviceMode === "mobile" ? "max-w-[380px] mx-auto border-x border-zinc-800 shadow-2xl rounded-2xl" 
                     : this.deviceMode === "tablet" ? "max-w-[768px] mx-auto border-x border-zinc-800 shadow-2xl rounded-xl" 
                     : "w-full";

    // Navigation Links
    const navHtml = `
      <a href="javascript:void(0)" onclick="window.__previewRunner.setRoute('/')" class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${this.activeRoute === '/' ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'}">
        <span>📊</span> <span>Overview</span>
      </a>
      ${entities.map(e => {
        const route = `/${e.plural.toLowerCase()}`;
        const isActive = this.activeRoute === route;
        return `
          <a href="javascript:void(0)" onclick="window.__previewRunner.setRoute('${route}')" class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${isActive ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'}">
            <span>📦</span> <span>${e.plural}</span>
          </a>
        `;
      }).join("")}
    `;

    // Render Body Page Content
    let pageContentHtml = "";
    const activeEntity = entities.find(e => `/${e.plural.toLowerCase()}` === this.activeRoute);

    if (this.activeRoute === "/" || !activeEntity) {
      pageContentHtml = this.renderDashboardView();
    } else {
      pageContentHtml = this.renderEntityCrudView(activeEntity);
    }

    this.container.innerHTML = `
      <div class="h-full flex flex-col bg-[#0c0c0e] text-zinc-100 overflow-hidden ${widthClass}">
        <!-- Top App Navigation Bar -->
        <header class="px-4 py-2.5 bg-[#121215] border-b border-zinc-800/80 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-2.5">
            <div class="w-6 h-6 rounded-md bg-zinc-800 text-white flex items-center justify-center text-xs font-bold border border-zinc-700">
              ${app_name.charAt(0)}
            </div>
            <span class="text-xs font-bold text-zinc-100 truncate max-w-[140px]">${app_name}</span>
            <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono border border-zinc-700/60">${type}</span>
          </div>

          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span class="text-[11px] text-zinc-400 font-mono">${this.user.email}</span>
          </div>
        </header>

        <!-- Main Body: Sidebar + Dynamic Content -->
        <div class="flex-1 flex overflow-hidden">
          <!-- Sidebar -->
          <aside class="${this.deviceMode === 'mobile' ? 'hidden' : 'w-48'} bg-[#101013] border-r border-zinc-800 p-3 flex flex-col flex-shrink-0">
            <p class="text-[10px] uppercase font-bold text-zinc-500 px-2 mb-2 tracking-wider">Navigation</p>
            <nav class="space-y-1">
              ${navHtml}
            </nav>
            <div class="mt-auto pt-3 border-t border-zinc-800">
              <p class="text-[10px] text-zinc-500 px-2 font-mono">Next.js 14 + Supabase</p>
            </div>
          </aside>

          <!-- Main Scrollable View Area -->
          <main class="flex-1 p-4 sm:p-6 overflow-y-auto bg-[#09090b]">
            ${pageContentHtml}
          </main>
        </div>

        <!-- Mobile Bottom Nav -->
        ${this.deviceMode === 'mobile' ? `
          <nav class="flex items-center justify-around py-2 bg-[#121215] border-t border-zinc-800 text-[10px] text-zinc-400">
            <button onclick="window.__previewRunner.setRoute('/')" class="flex flex-col items-center ${this.activeRoute === '/' ? 'text-white font-bold' : ''}">
              <span>📊</span> <span>Home</span>
            </button>
            ${entities.slice(0, 3).map(e => `
              <button onclick="window.__previewRunner.setRoute('/${e.plural.toLowerCase()}')" class="flex flex-col items-center ${this.activeRoute === `/${e.plural.toLowerCase()}` ? 'text-white font-bold' : ''}">
                <span>📦</span> <span>${e.name}</span>
              </button>
            `).join("")}
          </nav>
        ` : ""}
      </div>
    `;
  }

  renderDashboardView() {
    const entities = this.plan.entities || [];

    const kpiCards = entities.map(entity => {
      const table = entity.plural.toLowerCase();
      const count = (this.db[table] || []).length;
      return `
        <div class="p-4 rounded-xl bg-[#121215] border border-zinc-800 hover:border-zinc-700 transition-all cursor-pointer" onclick="window.__previewRunner.setRoute('/${table}')">
          <div class="flex justify-between items-center mb-1">
            <span class="text-xs text-zinc-400 font-medium">${entity.plural}</span>
            <span class="text-zinc-500 text-xs">→</span>
          </div>
          <p class="text-2xl font-bold text-zinc-100 mt-1">${count}</p>
          <p class="text-[10px] text-zinc-500 mt-1">Active records</p>
        </div>
      `;
    }).join("");

    return `
      <div class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-zinc-100">${this.plan.app_name} Dashboard</h2>
          <p class="text-xs text-zinc-400 mt-1">${this.plan.description}</p>
        </div>

        <div>
          <h3 class="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">Entities Overview</h3>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            ${kpiCards || `<p class="text-xs text-zinc-500">No entities configured.</p>`}
          </div>
        </div>

        <div class="p-4 rounded-xl bg-[#121215] border border-zinc-800">
          <h3 class="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">⚡ Live Interactive Sandbox</h3>
          <p class="text-xs text-zinc-400 leading-relaxed">
            This live preview is powered by NovaBuild's in-memory simulator matching your Next.js 14 data model. Click on any entity in the sidebar to add, search, and delete records.
          </p>
        </div>
      </div>
    `;
  }

  renderEntityCrudView(entity) {
    const table = entity.plural.toLowerCase();
    const allRecords = this.db[table] || [];
    
    // Filter records by search term
    const records = allRecords.filter(r => {
      if (!this.searchTerm) return true;
      return Object.values(r).some(val => 
        String(val).toLowerCase().includes(this.searchTerm.toLowerCase())
      );
    });

    const fields = entity.fields || [];

    // Table Header
    const ths = fields.map(f => `
      <th class="px-3.5 py-2.5 text-left text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
        ${f.name}
      </th>
    `).join("");

    // Table Rows
    const trs = records.map(record => {
      const tds = fields.map(f => {
        const val = record[f.name];
        let displayVal = val;
        if (f.type === "boolean") {
          displayVal = val ? `<span class="text-emerald-400 font-bold">✓ Yes</span>` : `<span class="text-zinc-500">✗ No</span>`;
        } else if (f.type === "select") {
          displayVal = `<span class="px-2 py-0.5 rounded text-[10px] bg-zinc-800 text-zinc-300 border border-zinc-700/60 font-mono">${val || "-"}</span>`;
        } else if (f.type === "number") {
          displayVal = `<span class="font-mono text-zinc-200">${val != null ? Number(val).toLocaleString() : "-"}</span>`;
        } else {
          displayVal = val ?? `<span class="text-zinc-600">-</span>`;
        }

        return `
          <td class="px-3.5 py-3 text-xs text-zinc-300 border-b border-zinc-800/60">
            ${displayVal}
          </td>
        `;
      }).join("");

      return `
        <tr class="hover:bg-zinc-800/40 transition-colors">
          ${tds}
          <td class="px-3.5 py-3 text-right text-xs border-b border-zinc-800/60">
            <button 
              onclick="window.__previewRunner.deleteRecord('${entity.name}', '${record.id}')"
              class="text-rose-400 hover:text-rose-300 text-xs font-semibold hover:underline"
            >
              Delete
            </button>
          </td>
        </tr>
      `;
    }).join("");

    return `
      <div class="space-y-4">
        <!-- Header & Action Bar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800">
          <div>
            <h2 class="text-lg font-bold text-zinc-100 flex items-center gap-2">
              <span>${entity.plural}</span>
              <span class="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-normal">
                ${records.length} records
              </span>
            </h2>
            <p class="text-xs text-zinc-400 mt-0.5">Manage and inspect ${entity.name} items</p>
          </div>

          <div class="flex items-center gap-2">
            <!-- Search Box -->
            <input
              type="text"
              placeholder="Search ${entity.plural.toLowerCase()}..."
              value="${this.searchTerm}"
              oninput="window.__previewRunner.searchTerm = this.value; window.__previewRunner.render();"
              class="rounded-lg bg-[#121215] border border-zinc-800 px-3 py-1.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 w-44"
            />
            
            <!-- Add Record Button -->
            <button
              onclick="window.__previewRunner.openAddModal('${entity.name}')"
              class="px-3.5 py-1.5 rounded-lg bg-white hover:bg-zinc-200 text-zinc-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <span>+ Add ${entity.name}</span>
            </button>
          </div>
        </div>

        <!-- Table View -->
        <div class="rounded-xl border border-zinc-800 overflow-hidden bg-[#121215]">
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead class="bg-[#18181b] border-b border-zinc-800">
                <tr>
                  ${ths}
                  <th class="px-3.5 py-2.5 text-right text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-800/60">
                ${trs || `
                  <tr>
                    <td colspan="${fields.length + 1}" class="py-8 text-center text-xs text-zinc-500">
                      No records found. Click "+ Add ${entity.name}" to create one.
                    </td>
                  </tr>
                `}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Add Record Modal (when open) -->
        ${this.isAddModalOpen ? this.renderAddModal(entity) : ""}
      </div>
    `;
  }

  openAddModal(entityName) {
    this.isAddModalOpen = true;
    this.render();
  }

  closeAddModal() {
    this.isAddModalOpen = false;
    this.render();
  }

  renderAddModal(entity) {
    const fields = entity.fields || [];

    const inputs = fields.map(f => {
      let inputField = "";
      if (f.type === "select" && f.options && f.options.length) {
        inputField = `
          <select name="${f.name}" class="w-full rounded-lg bg-[#18181b] border border-zinc-800 px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-zinc-500">
            ${f.options.map(opt => `<option value="${opt}">${opt}</option>`).join("")}
          </select>
        `;
      } else if (f.type === "textarea") {
        inputField = `
          <textarea name="${f.name}" rows="2" placeholder="Enter ${f.name}..." class="w-full rounded-lg bg-[#18181b] border border-zinc-800 p-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"></textarea>
        `;
      } else if (f.type === "boolean") {
        inputField = `
          <select name="${f.name}" class="w-full rounded-lg bg-[#18181b] border border-zinc-800 px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-zinc-500">
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        `;
      } else if (f.type === "number") {
        inputField = `
          <input type="number" name="${f.name}" placeholder="0" class="w-full rounded-lg bg-[#18181b] border border-zinc-800 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500" />
        `;
      } else if (f.type === "date") {
        inputField = `
          <input type="date" name="${f.name}" class="w-full rounded-lg bg-[#18181b] border border-zinc-800 px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-zinc-500" />
        `;
      } else {
        inputField = `
          <input type="text" name="${f.name}" placeholder="Enter ${f.name}..." class="w-full rounded-lg bg-[#18181b] border border-zinc-800 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-500" />
        `;
      }

      return `
        <div>
          <label class="block text-[11px] font-semibold text-zinc-400 mb-1">
            ${f.name} ${f.required ? '<span class="text-rose-400">*</span>' : ''}
          </label>
          ${inputField}
        </div>
      `;
    }).join("");

    return `
      <div class="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
        <div class="bg-[#121215] border border-zinc-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl">
          <div class="flex items-center justify-between pb-2 border-b border-zinc-800">
            <h3 class="text-sm font-bold text-zinc-100">Add New ${entity.name}</h3>
            <button onclick="window.__previewRunner.closeAddModal()" class="text-zinc-500 hover:text-zinc-200 text-lg">&times;</button>
          </div>

          <form id="preview-add-form" onsubmit="window.__handlePreviewFormSubmit(event, '${entity.name}')" class="space-y-3">
            ${inputs}
            <div class="flex justify-end gap-2 pt-2 border-t border-zinc-800">
              <button type="button" onclick="window.__previewRunner.closeAddModal()" class="px-3 py-1.5 rounded-lg border border-zinc-800 text-xs font-medium text-zinc-300 hover:bg-zinc-800">
                Cancel
              </button>
              <button type="submit" class="px-4 py-1.5 rounded-lg bg-white hover:bg-zinc-200 text-zinc-950 font-semibold text-xs shadow-sm">
                Save Record
              </button>
            </div>
          </form>
        </div>
      </div>
    `;
  }
}

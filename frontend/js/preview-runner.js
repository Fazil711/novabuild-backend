// NovaBuild In-Browser Interactive App Preview Engine

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
          row[f.name] = `Sample notes and operational summary for record #${i}.`;
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
        <div class="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500">
          <span class="text-3xl mb-2">👁️</span>
          <p class="text-sm font-semibold text-slate-400">No Application Loaded in Preview</p>
          <p class="text-xs text-slate-500 mt-1">Generate a blueprint or load a project to interact with the live UI.</p>
        </div>
      `;
      return;
    }

    const { app_name, type, entities = [], navigation = [] } = this.plan;

    // Viewport Width constraints based on deviceMode
    const widthClass = this.deviceMode === "mobile" ? "max-w-[375px] mx-auto border-x border-slate-800 shadow-2xl rounded-3xl" 
                     : this.deviceMode === "tablet" ? "max-w-[768px] mx-auto border-x border-slate-800 shadow-2xl rounded-2xl" 
                     : "w-full";

    // Navigation Links
    const navHtml = `
      <a href="javascript:void(0)" onclick="window.__previewRunner.setRoute('/')" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${this.activeRoute === '/' ? 'bg-indigo-600/30 text-indigo-400 font-bold' : 'text-slate-300 hover:bg-slate-800'}">
        <span>📊</span> <span>Dashboard</span>
      </a>
      ${entities.map(e => {
        const route = `/${e.plural.toLowerCase()}`;
        const isActive = this.activeRoute === route;
        return `
          <a href="javascript:void(0)" onclick="window.__previewRunner.setRoute('${route}')" class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${isActive ? 'bg-indigo-600/30 text-indigo-400 font-bold' : 'text-slate-300 hover:bg-slate-800'}">
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
      <div class="h-full flex flex-col bg-slate-950 text-slate-100 overflow-hidden ${widthClass}">
        <!-- Top App Navigation / Header Bar -->
        <header class="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-lg bg-indigo-600 flex items-center justify-center text-xs font-bold text-white">
              ${app_name.charAt(0)}
            </div>
            <span class="text-xs font-bold text-white truncate max-w-[140px]">${app_name}</span>
            <span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono">${type}</span>
          </div>

          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span class="truncate max-w-[100px]">${this.user.email}</span>
            </div>
          </div>
        </header>

        <!-- Main Body: Sidebar + Dynamic Content -->
        <div class="flex-1 flex overflow-hidden">
          <!-- Sidebar (Hidden on mobile mode) -->
          <aside class="${this.deviceMode === 'mobile' ? 'hidden' : 'w-48'} bg-slate-900/50 border-r border-slate-800/80 p-3 flex flex-col flex-shrink-0">
            <p class="text-[10px] uppercase font-bold text-slate-500 px-3 mb-2 tracking-wider">Navigation</p>
            <nav class="space-y-1">
              ${navHtml}
            </nav>
            <div class="mt-auto pt-3 border-t border-slate-800/60">
              <p class="text-[10px] text-slate-500 px-3">Supabase RLS Enabled</p>
            </div>
          </aside>

          <!-- Main Scrollable View Area -->
          <main class="flex-1 p-4 sm:p-6 overflow-y-auto bg-slate-950/60">
            ${pageContentHtml}
          </main>
        </div>

        <!-- Mobile Bottom Nav (Shown only in mobile mode) -->
        ${this.deviceMode === 'mobile' ? `
          <nav class="flex items-center justify-around py-2 bg-slate-900 border-t border-slate-800 text-[10px] text-slate-400">
            <button onclick="window.__previewRunner.setRoute('/')" class="flex flex-col items-center ${this.activeRoute === '/' ? 'text-indigo-400 font-bold' : ''}">
              <span>📊</span> <span>Home</span>
            </button>
            ${entities.slice(0, 3).map(e => `
              <button onclick="window.__previewRunner.setRoute('/${e.plural.toLowerCase()}')" class="flex flex-col items-center ${this.activeRoute === `/${e.plural.toLowerCase()}` ? 'text-indigo-400 font-bold' : ''}">
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
    const totalEntitiesCount = entities.length;
    const totalRecordsCount = Object.values(this.db).reduce((acc, list) => acc + (list ? list.length : 0), 0);

    const kpiCards = entities.map(entity => {
      const table = entity.plural.toLowerCase();
      const count = (this.db[table] || []).length;
      return `
        <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/40 transition-colors cursor-pointer" onclick="window.__previewRunner.setRoute('/${table}')">
          <div class="flex justify-between items-center mb-1">
            <span class="text-xs text-slate-400 font-medium">${entity.plural}</span>
            <span class="text-indigo-400 text-xs">→</span>
          </div>
          <p class="text-2xl font-black text-white">${count}</p>
          <p class="text-[10px] text-slate-500 mt-1">Total active records</p>
        </div>
      `;
    }).join("");

    return `
      <div class="space-y-6">
        <div>
          <h2 class="text-xl font-bold text-white">Dashboard Overview</h2>
          <p class="text-xs text-slate-400 mt-1">${this.plan.description || "Live in-memory preview of your generated app"}</p>
        </div>

        <!-- Metric KPI Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
          ${kpiCards}
        </div>

        <!-- Quick Activity Section -->
        <div class="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-3">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300">Quick Actions</h3>
            <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800">● Live Sandbox Active</span>
          </div>
          <div class="flex flex-wrap gap-2">
            ${entities.map(e => `
              <button onclick="window.__previewRunner.setRoute('/${e.plural.toLowerCase()}')" class="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white text-xs font-semibold transition-colors">
                + Manage ${e.plural}
              </button>
            `).join("")}
          </div>
        </div>
      </div>
    `;
  }

  renderEntityCrudView(entity) {
    const table = entity.plural.toLowerCase();
    const allRecords = this.db[table] || [];
    
    // Filter records based on search term
    const records = allRecords.filter(r => {
      if (!this.searchTerm) return true;
      return Object.values(r).some(v => String(v).toLowerCase().includes(this.searchTerm.toLowerCase()));
    });

    const headersHtml = (entity.fields || []).map(f => `<th class="p-2.5 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider">${f.name}</th>`).join("");
    
    const rowsHtml = records.map(r => {
      const cells = (entity.fields || []).map(f => {
        const val = r[f.name];
        let displayVal = val !== undefined && val !== null ? String(val) : "-";
        if (f.type === "boolean") {
          displayVal = val ? `<span class="text-emerald-400 font-bold">✓ Yes</span>` : `<span class="text-slate-500">✗ No</span>`;
        }
        return `<td class="p-2.5 text-xs text-slate-200">${displayVal}</td>`;
      }).join("");

      return `
        <tr class="border-b border-slate-800/80 hover:bg-slate-800/40 transition-colors">
          ${cells}
          <td class="p-2.5 text-right">
            <button onclick="window.__previewRunner.deleteRecord('${entity.name}', '${r.id}')" class="text-rose-400 hover:text-rose-300 text-xs font-semibold">
              Delete
            </button>
          </td>
        </tr>
      `;
    }).join("");

    // Add Record Modal Form
    const modalFormFields = (entity.fields || []).map(f => {
      let inputEl = "";
      if (f.type === "boolean") {
        inputEl = `<input type="checkbox" name="${f.name}" class="h-4 w-4 rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-indigo-500" />`;
      } else if (f.type === "textarea") {
        inputEl = `<textarea name="${f.name}" rows="2" placeholder="Enter ${f.name}..." class="w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"></textarea>`;
      } else if (f.type === "select") {
        const options = (f.options || ["Option 1", "Option 2"]).map(o => `<option value="${o}">${o}</option>`).join("");
        inputEl = `<select name="${f.name}" class="w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">${options}</select>`;
      } else {
        const inputType = f.type === "number" ? "number" : f.type === "date" ? "date" : "text";
        inputEl = `<input type="${inputType}" name="${f.name}" placeholder="Enter ${f.name}..." ${f.required ? 'required' : ''} class="w-full rounded-lg bg-slate-900 border border-slate-700 p-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500" />`;
      }

      return `
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1 capitalize">${f.name} ${f.required ? '<span class="text-red-400">*</span>' : ''}</label>
          ${inputEl}
        </div>
      `;
    }).join("");

    return `
      <div class="space-y-4">
        <!-- Header with Title & Add button -->
        <div class="flex items-center justify-between gap-2">
          <div>
            <h2 class="text-lg font-bold text-white">${entity.plural}</h2>
            <p class="text-xs text-slate-400">Interactive live CRUD preview (${records.length} records)</p>
          </div>
          <button onclick="window.__previewRunner.toggleAddModal(true)" class="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow transition-colors flex items-center gap-1.5">
            <span>+ Add ${entity.name}</span>
          </button>
        </div>

        <!-- Search Bar -->
        <div class="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search ${entity.plural.toLowerCase()}..."
            value="${this.searchTerm}"
            oninput="window.__previewRunner.handleSearch(this.value)"
            class="w-full max-w-xs rounded-lg bg-slate-900 border border-slate-800 px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
        </div>

        <!-- Live Table -->
        <div class="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="bg-slate-800/60 border-b border-slate-800">
                <tr>
                  ${headersHtml}
                  <th class="p-2.5 text-right text-[11px] font-semibold text-slate-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${rowsHtml || `<tr><td colspan="${(entity.fields || []).length + 1}" class="p-8 text-center text-xs text-slate-500">No records found. Click "+ Add ${entity.name}" to create one!</td></tr>`}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Add Record Modal -->
        ${this.isAddModalOpen ? `
          <div class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div class="bg-slate-900 rounded-2xl max-w-md w-full p-6 border border-slate-700 shadow-2xl">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-bold text-white">Create New ${entity.name}</h3>
                <button onclick="window.__previewRunner.toggleAddModal(false)" class="text-slate-400 hover:text-white text-lg">&times;</button>
              </div>
              <form onsubmit="window.__previewRunner.handleFormSubmit(event, '${entity.name}')" class="space-y-3">
                ${modalFormFields}
                <div class="flex justify-end gap-2 pt-3 border-t border-slate-800">
                  <button type="button" onclick="window.__previewRunner.toggleAddModal(false)" class="px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:bg-slate-800">Cancel</button>
                  <button type="submit" class="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white">Save Record</button>
                </div>
              </form>
            </div>
          </div>
        ` : ""}
      </div>
    `;
  }

  toggleAddModal(isOpen) {
    this.isAddModalOpen = isOpen;
    this.render();
  }

  handleSearch(term) {
    this.searchTerm = term;
    this.render();
  }

  handleFormSubmit(e, entityName) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());
    
    // Handle checkboxes
    const entity = (this.plan.entities || []).find(ent => ent.name.toLowerCase() === entityName.toLowerCase());
    if (entity) {
      entity.fields.forEach(f => {
        if (f.type === "boolean") {
          payload[f.name] = formData.has(f.name);
        }
      });
    }

    this.addRecord(entityName, payload);
  }
}

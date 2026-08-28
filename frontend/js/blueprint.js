// Blueprint Renderer Module

export function renderBlueprint(plan, container) {
  if (!plan) {
    container.innerHTML = `<div class="p-8 text-center text-gray-500">No blueprint generated yet. Type your idea above and click "Generate Blueprint".</div>`;
    return;
  }

  const { app_name, type, description, project_dna, entities = [], features = [], pages = [], navigation = [], auth_config } = plan;

  // Render Project DNA if present
  let dnaHtml = "";
  if (project_dna && (project_dna.business_name || project_dna.industry || (project_dna.target_users && project_dna.target_users.length))) {
    const users = (project_dna.target_users || []).map(u => `<span class="px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-900/40 text-indigo-300 border border-indigo-700/50">${u}</span>`).join(" ");
    const goals = (project_dna.goals || []).map(g => `<li class="text-xs text-gray-300 flex items-center gap-1.5"><span class="text-indigo-400">✦</span> ${g}</li>`).join("");

    dnaHtml = `
      <div class="glass-card rounded-2xl p-5 border border-indigo-500/20 bg-gradient-to-br from-indigo-950/40 via-slate-900/50 to-slate-900/30">
        <div class="flex items-center gap-2 mb-3">
          <span class="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 text-sm">🧬</span>
          <h3 class="text-sm font-bold uppercase tracking-wider text-indigo-300">Project DNA & Business Profile</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p class="text-xs text-gray-400">Business / Industry</p>
            <p class="font-semibold text-white mt-0.5">${project_dna.business_name || app_name} <span class="text-xs font-normal text-indigo-300">(${project_dna.industry || type})</span></p>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-1">Target Users</p>
            <div class="flex flex-wrap gap-1.5">${users || '<span class="text-gray-500 text-xs">General Users</span>'}</div>
          </div>
          <div>
            <p class="text-xs text-gray-400">Primary Workflow</p>
            <p class="text-xs text-gray-300 mt-0.5">${project_dna.main_workflow || 'Standard CRUD with Auth'}</p>
          </div>
        </div>
        ${goals ? `<div class="mt-3 pt-3 border-t border-slate-800"><p class="text-xs text-gray-400 mb-1">Core Goals:</p><ul class="grid grid-cols-1 md:grid-cols-2 gap-1">${goals}</ul></div>` : ""}
      </div>
    `;
  }

  // Render Entities & Fields
  const entitiesHtml = entities.map(entity => {
    const fieldsHtml = (entity.fields || []).map(f => {
      const typeColors = {
        text: "bg-blue-900/40 text-blue-300 border-blue-800",
        number: "bg-amber-900/40 text-amber-300 border-amber-800",
        boolean: "bg-emerald-900/40 text-emerald-300 border-emerald-800",
        date: "bg-purple-900/40 text-purple-300 border-purple-800",
        textarea: "bg-cyan-900/40 text-cyan-300 border-cyan-800",
        select: "bg-rose-900/40 text-rose-300 border-rose-800"
      };
      const badgeClass = typeColors[f.type] || "bg-gray-800 text-gray-300 border-gray-700";
      const requiredBadge = f.required ? `<span class="text-xs text-red-400 font-bold ml-1">*</span>` : "";
      const optionsHtml = f.options && f.options.length ? `<span class="text-[10px] text-gray-400 block mt-0.5">options: [${f.options.join(", ")}]</span>` : "";

      return `
        <tr class="border-b border-slate-800/60 hover:bg-slate-800/30 transition-colors">
          <td class="py-2.5 px-3 font-mono text-xs text-indigo-300 font-medium">${f.name}${requiredBadge}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[11px] font-mono border ${badgeClass}">${f.type}</span>
            ${optionsHtml}
          </td>
          <td class="py-2.5 px-3 text-xs text-gray-400">${f.required ? 'Required' : 'Optional'}</td>
        </tr>
      `;
    }).join("");

    return `
      <div class="glass-card rounded-xl border border-slate-800 overflow-hidden">
        <div class="p-3.5 bg-slate-800/60 border-b border-slate-700/50 flex justify-between items-center">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
            <h4 class="font-bold text-white text-sm">${entity.name}</h4>
            <span class="text-xs text-gray-400 font-mono">(${entity.plural.toLowerCase()})</span>
          </div>
          <span class="text-xs text-gray-400">${(entity.fields || []).length} fields</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead>
              <tr class="text-[10px] uppercase font-bold text-gray-400 bg-slate-900/40 border-b border-slate-800">
                <th class="py-2 px-3">Field Name</th>
                <th class="py-2 px-3">Data Type</th>
                <th class="py-2 px-3">Constraint</th>
              </tr>
            </thead>
            <tbody>
              ${fieldsHtml}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }).join("");

  // Render Pages & Navigation
  const pagesHtml = (pages || []).map(p => `
    <div class="p-3 rounded-lg bg-slate-800/40 border border-slate-800 flex items-center justify-between">
      <div>
        <p class="text-xs font-semibold text-white">${p.title || p.name}</p>
        <p class="text-[11px] font-mono text-gray-400">${p.path}</p>
      </div>
      <span class="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-800 text-indigo-300 border border-indigo-900/50">${p.page_type || 'view'}</span>
    </div>
  `).join("");

  // Features list
  const featuresHtml = (features || []).map(f => `
    <li class="flex items-center gap-2 text-xs text-gray-300">
      <span class="text-emerald-400 font-bold">✓</span> ${f}
    </li>
  `).join("");

  container.innerHTML = `
    <div class="space-y-6">
      <!-- App Header Summary -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-indigo-900/30 via-slate-900/80 to-slate-900 border border-indigo-500/30">
        <div>
          <div class="flex items-center gap-3">
            <h2 class="text-2xl font-black text-white tracking-tight">${app_name}</h2>
            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${type}</span>
          </div>
          <p class="text-sm text-gray-300 mt-1 max-w-2xl">${description}</p>
        </div>
        <button id="approve-build-btn" class="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0">
          <span>🚀 Approve & Generate Code</span>
        </button>
      </div>

      ${dnaHtml}

      <!-- Entities Section -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center gap-2">
            <span>📦 Database Entities & Relations</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-gray-400">${entities.length} tables</span>
          </h3>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          ${entitiesHtml}
        </div>
      </div>

      <!-- Pages & Features Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Pages Hierarchy -->
        <div class="glass-card rounded-xl p-4 border border-slate-800">
          <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-2">
            <span>📱 UI Page Structure</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-400">${(pages || []).length} pages</span>
          </h4>
          <div class="space-y-2">
            ${pagesHtml || '<p class="text-xs text-gray-500">Auto-generated from entities</p>'}
          </div>
        </div>

        <!-- Features & Auth -->
        <div class="glass-card rounded-xl p-4 border border-slate-800 space-y-4">
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">⚡ Core Features</h4>
            <ul class="space-y-1.5">
              ${featuresHtml || '<li class="text-xs text-gray-500">Complete Next.js App with Supabase CRUD</li>'}
            </ul>
          </div>
          ${auth_config ? `
            <div class="pt-3 border-t border-slate-800">
              <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">🔐 Auth & RBAC</h4>
              <p class="text-xs text-gray-300">Roles: <span class="font-mono text-indigo-300">${(auth_config.roles || []).join(", ")}</span> (Default: ${auth_config.default_role || 'member'})</p>
            </div>
          ` : ""}
        </div>
      </div>
    </div>
  `;
}

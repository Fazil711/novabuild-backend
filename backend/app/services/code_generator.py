import json
import os
from typing import List, Dict, Any
from app.schemas import AppPlan, EntitySchema
from app.services.sql_generator import generate_sql

GENERATED_ROOT = os.path.join(os.getcwd(), "generated-apps")


def _input_for_field(f) -> str:
    if f.type == "boolean":
        return f'<input type="checkbox" name="{f.name}" className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />'
    if f.type == "textarea":
        return f'<textarea name="{f.name}" rows={{3}} placeholder="Enter {f.name}..." className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white" />'
    if f.type == "select":
        opts = "".join(f'<option value="{o}">{o}</option>' for o in (f.options or ["Option 1", "Option 2"]))
        return f'<select name="{f.name}" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white">{opts}</select>'
    
    html_type = "number" if f.type == "number" else "date" if f.type == "date" else "text"
    required = "required" if f.required else ""
    return f'<input type="{html_type}" name="{f.name}" placeholder="Enter {f.name}..." className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white" {required} />'


def _generate_package_json(plan: AppPlan) -> str:
    manifest = {
        "name": plan.app_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "next": "^14.2.5",
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "@supabase/supabase-js": "^2.45.0",
            "lucide-react": "^0.417.0",
            "clsx": "^2.1.1",
            "tailwind-merge": "^2.4.0"
        },
        "devDependencies": {
            "typescript": "^5.5.4",
            "@types/node": "^20.14.11",
            "@types/react": "^18.3.3",
            "@types/react-dom": "^18.3.0",
            "postcss": "^8.4.39",
            "tailwindcss": "^3.4.6",
            "autoprefixer": "^10.4.19"
        }
    }
    return json.dumps(manifest, indent=2)


def _generate_types_ts(plan: AppPlan) -> str:
    code = [
        "// Auto-generated TypeScript definitions for NovaBuild App",
        'export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];',
        ""
    ]
    for entity in plan.entities:
        fields = ["  id: string;", "  user_id: string;", "  created_at: string;", "  updated_at?: string;"]
        for f in entity.fields:
            ts_type = "number" if f.type == "number" else "boolean" if f.type == "boolean" else "string"
            optional = "" if f.required else "?"
            fields.append(f"  {f.name}{optional}: {ts_type};")
        
        code.append(f"export interface {entity.name} {{\n" + "\n".join(fields) + "\n}\n")
    return "\n".join(code)


def _generate_supabase_client() -> str:
    return """import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://your-project.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "your-anon-key";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
"""


def _generate_layout_tsx(plan: AppPlan) -> str:
    nav_links = []
    nav_links.append("""            <a href="/" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 transition-colors">
              <span className="font-semibold">Dashboard</span>
            </a>""")

    for entity in plan.entities:
        plural = entity.plural
        path = f"/{plural.lower()}"
        nav_links.append(f"""            <a href="{path}" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 transition-colors">
              <span>{plural}</span>
            </a>""")

    nav_rendered = "\n".join(nav_links)

    return f""""use client";
import React, {{ useState, useEffect }} from "react";
import "./globals.css";
import {{ supabase }} from "@/lib/supabase";

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  const [user, setUser] = useState<any>(null);

  useEffect(() => {{
    supabase.auth.getUser().then(({{ data }}) => setUser(data.user));
    const {{ data: authListener }} = supabase.auth.onAuthStateChange((_, session) => {{
      setUser(session?.user ?? null);
    }});
    return () => authListener.subscription.unsubscribe();
  }}, []);

  async function handleLogout() {{
    await supabase.auth.signOut();
    window.location.href = "/login";
  }}

  return (
    <html lang="en">
      <body className="bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 min-h-screen flex flex-col md:flex-row">
        <!-- Sidebar Navigation -->
        <aside className="w-full md:w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col">
          <div className="p-5 border-b border-gray-200 dark:border-gray-800">
            <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">{plan.app_name}</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 capitalize">{plan.type} Application</p>
          </div>
          <nav className="flex-1 p-4 space-y-1">
{nav_rendered}
          </nav>
          <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            {{user ? (
              <div className="flex items-center justify-between">
                <div className="text-xs truncate max-w-[140px] text-gray-600 dark:text-gray-400">
                  {{user.email}}
                </div>
                <button
                  onClick={{handleLogout}}
                  className="text-xs text-red-600 hover:text-red-700 font-medium"
                >
                  Logout
                </button>
              </div>
            ) : (
              <a
                href="/login"
                className="block text-center text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 dark:bg-indigo-900/30 py-2 rounded-md"
              >
                Sign In
              </a>
            )}}
          </div>
        </aside>

        <!-- Main Content Area -->
        <main className="flex-1 p-6 md:p-10 max-w-7xl overflow-y-auto">
          {{children}}
        </main>
      </body>
    </html>
  );
}}
"""


def _generate_dashboard_page(plan: AppPlan) -> str:
    entity_cards = []
    for entity in plan.entities:
        table = entity.plural.lower()
        entity_cards.append(f"""        <div className="bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{entity.plural}</h3>
            <a href="/{table}" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">View all &rarr;</a>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Manage and create records for {entity.plural.lower()}.</p>
          <a
            href="/{table}"
            className="inline-flex items-center px-4 py-2 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300 rounded-lg text-sm font-medium hover:bg-indigo-100"
          >
            Open {entity.plural} &rarr;
          </a>
        </div>""")

    cards_rendered = "\n".join(entity_cards)

    features_rendered = "".join(f'<li className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300"><span className="text-green-500">✓</span> {feat}</li>' for feat in plan.features)

    return f""""use client";
import React, {{ useEffect, useState }} from "react";
import {{ supabase }} from "@/lib/supabase";

export default function DashboardPage() {{
  const [user, setUser] = useState<any>(null);

  useEffect(() => {{
    supabase.auth.getUser().then(({{ data }}) => setUser(data.user));
  }}, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome back{{user ? `, ${{user.email}}` : ""}}</h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">{plan.description}</p>
      </div>

      <!-- Feature Highlights -->
      <div className="bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-900 p-5 rounded-xl">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-800 dark:text-indigo-300 mb-3">Core Features</h3>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {features_rendered}
        </ul>
      </div>

      <!-- Entities Grid -->
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
{cards_rendered}
      </div>
    </div>
  );
}}
"""


def _generate_login_page(plan: AppPlan) -> str:
    return f""""use client";
import React, {{ useState }} from "react";
import {{ supabase }} from "@/lib/supabase";

export default function AuthPage() {{
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {{
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {{
      if (isSignUp) {{
        const {{ error }} = await supabase.auth.signUp({{ email, password }});
        if (error) throw error;
        alert("Account created successfully! You can now sign in.");
        setIsSignUp(false);
      }} else {{
        const {{ error }} = await supabase.auth.signInWithPassword({{ email, password }});
        if (error) throw error;
        window.location.href = "/";
      }}
    }} catch (err: any) {{
      setErrorMsg(err.message || "Authentication failed");
    }} finally {{
      setLoading(false);
    }}
  }}

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-md bg-white dark:bg-gray-900 p-8 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-xl">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
          {{isSignUp ? "Create an Account" : "Sign In to " + "{plan.app_name}"}}
        </h2>
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mb-6">
          {{isSignUp ? "Sign up to access your workspace" : "Enter your credentials to continue"}}
        </p>

        {{errorMsg && (
          <div className="p-3 mb-4 rounded bg-red-50 text-red-700 text-sm border border-red-200">
            {{errorMsg}}
          </div>
        )}}

        <form onSubmit={{handleSubmit}} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input
              type="email"
              required
              value={{email}}
              onChange={{(e) => setEmail(e.target.value)}}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={{6}}
              value={{password}}
              onChange={{(e) => setPassword(e.target.value)}}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:bg-gray-800 dark:border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={{loading}}
            className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow transition-colors disabled:opacity-50"
          >
            {{loading ? "Processing..." : isSignUp ? "Sign Up" : "Sign In"}}
          </button>
        </form>

        <div className="text-center mt-6">
          <button
            type="button"
            onClick={{() => setIsSignUp(!isSignUp)}}
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
          >
            {{isSignUp ? "Already have an account? Sign In" : "Need an account? Sign Up"}}
          </button>
        </div>
      </div>
    </div>
  );
}}
"""


def _generate_entity_page(entity: EntitySchema) -> str:
    table = entity.plural.lower()
    
    form_fields = "\n".join(
        f'          <div>\n            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 capitalize">{f.name}</label>\n            {_input_for_field(f)}\n          </div>'
        for f in entity.fields
    )
    
    table_headers = "".join(f'<th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{f.name}</th>' for f in entity.fields)
    
    table_cells = "".join(f'<td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">{{String(item.{f.name} ?? "-")}}</td>' for f in entity.fields)

    return f""""use client";
import React, {{ useEffect, useState }} from "react";
import {{ supabase }} from "@/lib/supabase";
import {{ {entity.name} }} from "@/lib/types";

export default function {entity.name}Page() {{
  const [items, setItems] = useState<{entity.name}[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

  async function load() {{
    setLoading(true);
    const {{ data, error }} = await supabase
      .from("{table}")
      .select("*")
      .order("created_at", {{ ascending: false }});
    if (!error && data) setItems(data as {entity.name}[]);
    setLoading(false);
  }}

  useEffect(() => {{ load(); }}, []);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {{
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    const {{ data: {{ user }} }} = await supabase.auth.getUser();

    const {{ error }} = await supabase
      .from("{table}")
      .insert({{ ...payload, user_id: user?.id }});

    if (error) {{
      alert("Error adding {entity.name.lower()}: " + error.message);
    }} else {{
      e.currentTarget.reset();
      setShowModal(false);
      load();
    }}
  }}

  async function handleDelete(id: string) {{
    if (!confirm("Are you sure you want to delete this {entity.name.lower()}?")) return;
    const {{ error }} = await supabase.from("{table}").delete().eq("id", id);
    if (!error) load();
  }}

  const filtered = items.filter((item: any) =>
    Object.values(item).some((v) => String(v).toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <!-- Header with Action -->
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{entity.plural}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Create, search, and manage your {entity.plural.lower()}</p>
        </div>
        <button
          onClick={{() => setShowModal(true)}}
          className="inline-flex items-center justify-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium shadow transition-colors"
        >
          + Add {entity.name}
        </button>
      </div>

      <!-- Search & Filters -->
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Search {entity.plural.lower()}..."
          value={{search}}
          onChange={{(e) => setSearch(e.target.value)}}
          className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm dark:bg-gray-900 dark:border-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <!-- Data Table -->
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-800/50">
            <tr>
              {table_headers}
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
            {{loading ? (
              <tr><td colSpan={{{len(entity.fields) + 1}}} className="p-8 text-center text-sm text-gray-500">Loading {entity.plural.lower()}...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={{{len(entity.fields) + 1}}} className="p-8 text-center text-sm text-gray-500">No {entity.plural.lower()} found.</td></tr>
            ) : (
              filtered.map((item: any) => (
                <tr key={{item.id}} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  {table_cells}
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                    <button
                      onClick={{() => handleDelete(item.id)}}
                      className="text-red-600 hover:text-red-800 font-medium text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}}
          </tbody>
        </table>
      </div>

      <!-- Add New Modal Dialog -->
      {{showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-md w-full p-6 border border-gray-200 dark:border-gray-800 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">Add New {entity.name}</h3>
              <button onClick={{() => setShowModal(false)}} className="text-gray-400 hover:text-gray-600 text-lg">&times;</button>
            </div>
            <form onSubmit={{handleSubmit}} className="space-y-4">
{form_fields}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
                <button
                  type="button"
                  onClick={{() => setShowModal(false)}}
                  className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium"
                >
                  Save {entity.name}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}}
    </div>
  );
}}
"""


def _generate_readme(plan: AppPlan) -> str:
    return f"""# {plan.app_name}

{plan.description}

Auto-generated with **NovaBuild**.

## Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Configure Supabase Credentials**:
   Create a `.env.local` file:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

3. **Initialize Database Schema**:
   Run the statements in `schema.sql` inside your Supabase SQL Editor.

4. **Run Development Server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.
"""


def _generate_tailwind_config() -> str:
    return """/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""


def _generate_postcss_config() -> str:
    return """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""


def _generate_tsconfig() -> str:
    return """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""


def _generate_globals_css() -> str:
    return """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 249, 250, 251;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-start-rgb));
  font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
}
"""


def _entity_filename(entity: EntitySchema) -> str:
    return f"pages/{entity.plural.lower()}.tsx"


def write_entity_page(base_dir: str, entity: EntitySchema) -> str:
    filename = _entity_filename(entity)
    path = os.path.join(base_dir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_generate_entity_page(entity))
    
    # Also write to app/[entity]/page.tsx for Next.js App Router
    app_entity_path = os.path.join(base_dir, "app", entity.plural.lower(), "page.tsx")
    os.makedirs(os.path.dirname(app_entity_path), exist_ok=True)
    with open(app_entity_path, "w", encoding="utf-8") as f:
        f.write(_generate_entity_page(entity))
        
    return filename


def remove_entity_page(base_dir: str, entity_plural: str) -> str:
    filename = f"pages/{entity_plural.lower()}.tsx"
    path = os.path.join(base_dir, filename)
    if os.path.isfile(path):
        os.remove(path)
        
    app_entity_path = os.path.join(base_dir, "app", entity_plural.lower(), "page.tsx")
    if os.path.isfile(app_entity_path):
        os.remove(app_entity_path)
        
    return filename


def write_plan_json(base_dir: str, plan: AppPlan):
    with open(os.path.join(base_dir, "plan.json"), "w", encoding="utf-8") as f:
        f.write(plan.model_dump_json(indent=2))


def write_schema_sql(base_dir: str, plan: AppPlan) -> str:
    sql = generate_sql(plan)
    with open(os.path.join(base_dir, "schema.sql"), "w", encoding="utf-8") as f:
        f.write(sql)
    return sql


def generate_project_files(plan: AppPlan, project_id: str) -> dict:
    base_dir = os.path.join(GENERATED_ROOT, project_id)
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "pages"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "app"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "app", "login"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "lib"), exist_ok=True)

    # Core blueprint & database
    write_plan_json(base_dir, plan)
    write_schema_sql(base_dir, plan)

    # Complete Next.js project scaffolding
    with open(os.path.join(base_dir, "package.json"), "w", encoding="utf-8") as f:
        f.write(_generate_package_json(plan))

    with open(os.path.join(base_dir, "tsconfig.json"), "w", encoding="utf-8") as f:
        f.write(_generate_tsconfig())

    with open(os.path.join(base_dir, "tailwind.config.js"), "w", encoding="utf-8") as f:
        f.write(_generate_tailwind_config())

    with open(os.path.join(base_dir, "postcss.config.js"), "w", encoding="utf-8") as f:
        f.write(_generate_postcss_config())

    with open(os.path.join(base_dir, "app", "globals.css"), "w", encoding="utf-8") as f:
        f.write(_generate_globals_css())

    with open(os.path.join(base_dir, "lib", "supabase.ts"), "w", encoding="utf-8") as f:
        f.write(_generate_supabase_client())

    with open(os.path.join(base_dir, "lib", "types.ts"), "w", encoding="utf-8") as f:
        f.write(_generate_types_ts(plan))

    with open(os.path.join(base_dir, "app", "layout.tsx"), "w", encoding="utf-8") as f:
        f.write(_generate_layout_tsx(plan))

    with open(os.path.join(base_dir, "app", "page.tsx"), "w", encoding="utf-8") as f:
        f.write(_generate_dashboard_page(plan))

    with open(os.path.join(base_dir, "app", "login", "page.tsx"), "w", encoding="utf-8") as f:
        f.write(_generate_login_page(plan))

    with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(_generate_readme(plan))

    files = [
        "plan.json",
        "schema.sql",
        "package.json",
        "tsconfig.json",
        "tailwind.config.js",
        "postcss.config.js",
        "app/globals.css",
        "app/layout.tsx",
        "app/page.tsx",
        "app/login/page.tsx",
        "lib/supabase.ts",
        "lib/types.ts",
        "README.md",
    ]

    # Write entity pages
    for entity in plan.entities:
        files.append(write_entity_page(base_dir, entity))
        files.append(f"app/{entity.plural.lower()}/page.tsx")

    return {"project_id": project_id, "dir": base_dir, "files": sorted(list(set(files)))}
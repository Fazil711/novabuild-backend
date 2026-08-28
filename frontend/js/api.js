// NovaBuild API Client & Streaming Handler

export const API_BASE_URL = window.NOVABUILD_API_URL || "http://localhost:8000/api";
export const BACKEND_URL = window.NOVABUILD_BACKEND_URL || "http://localhost:8000";

export class ApiClient {
  static getToken() {
    return localStorage.getItem("novabuild_token");
  }

  static setToken(token) {
    if (token) {
      localStorage.setItem("novabuild_token", token);
    } else {
      localStorage.removeItem("novabuild_token");
    }
  }

  static getHeaders() {
    const headers = {
      "Content-Type": "application/json",
    };
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  static async checkHealth() {
    try {
      const res = await fetch(`${BACKEND_URL}/health`, { method: "GET" });
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch {
      return null;
    }
  }

  // ---- Auth Endpoints ----

  static async register(email, password, fullName) {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");
    this.setToken(data.access_token);
    return data;
  }

  static async login(email, password) {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Invalid email or password");
    this.setToken(data.access_token);
    return data;
  }

  static async getMe() {
    const token = this.getToken();
    if (!token) return null;
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: this.getHeaders(),
      });
      if (res.ok) return await res.json();
      this.setToken(null);
      return null;
    } catch {
      return null;
    }
  }

  static async logout() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: this.getHeaders(),
      });
    } finally {
      this.setToken(null);
    }
  }

  static async forgotPassword(email) {
    const res = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    return await res.json();
  }

  static async resetPassword(token, newPassword) {
    const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: newPassword }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Password reset failed");
    return data;
  }

  // ---- Prompt & Plan Streaming ----

  static async generatePlanStream(prompt, onEvent, onError, onComplete) {
    try {
      const res = await fetch(`${API_BASE_URL}/plan/stream`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({ prompt }),
      });

      if (!res.ok) {
        throw new Error(`HTTP Error ${res.status}: Failed to initiate plan generation`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep last incomplete chunk

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const payload = JSON.parse(line.replace("data: ", ""));
              if (payload.error) {
                onError && onError(payload.error);
                return;
              }
              onEvent && onEvent(payload);
              if (payload.percent === 100 && payload.blueprint) {
                onComplete && onComplete(payload.blueprint);
              }
            } catch (err) {
              console.warn("Error parsing SSE JSON:", err, line);
            }
          }
        }
      }
    } catch (err) {
      onError && onError(err.message || "Failed to stream blueprint");
    }
  }

  // ---- Build & Projects ----

  static async buildProject(plan) {
    const res = await fetch(`${API_BASE_URL}/build`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ plan }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to generate project");
    return data;
  }

  static async listProjects() {
    const res = await fetch(`${API_BASE_URL}/projects`, {
      headers: this.getHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load projects");
    return data;
  }

  static async getProject(projectId) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
      headers: this.getHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to fetch project details");
    return data;
  }

  static async getProjectFile(projectId, filePath) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/files/${filePath}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error("File not found");
    return await res.text();
  }

  static async iterateProject(projectId, instruction) {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/iterate`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ instruction }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Iteration update failed");
    return data;
  }

  static getDownloadUrl(projectId) {
    return `${API_BASE_URL}/projects/${projectId}/download`;
  }
}

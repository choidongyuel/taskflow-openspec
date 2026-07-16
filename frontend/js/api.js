// Shared API client: token storage, fetch wrapper, standard error unwrapping,
// and a 401 interceptor that clears the token and redirects to login.

// In production, frontend and backend are served from the same Vercel
// project/domain, so relative paths ("") are correct and CORS never
// enters the picture. Only fall back to the local FastAPI dev server
// when the frontend itself is being served from the local static
// server (python -m http.server on port 5500) used during development.
const API_BASE =
  window.API_BASE_URL !== undefined
    ? window.API_BASE_URL
    : location.port === "5500"
    ? "http://127.0.0.1:8000"
    : "";

const TokenStore = {
  get() {
    return localStorage.getItem("token");
  },
  set(token) {
    localStorage.setItem("token", token);
  },
  clear() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  },
  getUser() {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  },
  setUser(user) {
    localStorage.setItem("user", JSON.stringify(user));
  },
};

class ApiError extends Error {
  constructor(status, code, message, meta) {
    super(message);
    this.status = status;
    this.code = code;
    this.meta = meta;
  }
}

/**
 * @param {string} path e.g. "/auth/login"
 * @param {RequestInit & {json?: any}} options
 */
async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = TokenStore.get();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let body = options.body;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...options, headers, body });

  if (resp.status === 401) {
    TokenStore.clear();
    if (!location.pathname.endsWith("index.html") && location.pathname !== "/") {
      location.href = "index.html";
    }
    throw new ApiError(401, "TOKEN_EXPIRED", "인증이 만료되었습니다");
  }

  if (resp.status === 204 || resp.status === 200 && resp.headers.get("content-length") === "0") {
    return null;
  }

  const data = await resp.json().catch(() => null);

  if (!resp.ok) {
    const err = data?.error || { code: "UNKNOWN", message: "알 수 없는 오류가 발생했습니다" };
    throw new ApiError(resp.status, err.code, err.message, err.meta);
  }

  return data;
}

const Api = {
  signup: (email, password) => apiFetch("/auth/signup", { method: "POST", json: { email, password } }),
  login: (email, password) => apiFetch("/auth/login", { method: "POST", json: { email, password } }),
  me: () => apiFetch("/auth/me"),
  logout: () => apiFetch("/auth/logout", { method: "POST" }),

  createTeam: (name) => apiFetch("/teams", { method: "POST", json: { name } }),
  joinTeam: (invite_code) => apiFetch("/teams/join", { method: "POST", json: { invite_code } }),
  getTeam: (teamId) => apiFetch(`/teams/${teamId}`),
  getMembers: (teamId) => apiFetch(`/teams/${teamId}/members`),

  listTasks: (teamId, filter) =>
    apiFetch(`/teams/${teamId}/tasks${filter ? `?filter=${filter}` : ""}`),
  createTask: (teamId, title, assignee_id) =>
    apiFetch(`/teams/${teamId}/tasks`, { method: "POST", json: { title, assignee_id: assignee_id ?? null } }),
  getTask: (taskId) => apiFetch(`/tasks/${taskId}`),
  updateTask: (taskId, title, assignee_id) =>
    apiFetch(`/tasks/${taskId}`, { method: "PUT", json: { title, assignee_id: assignee_id ?? null } }),
  updateTaskStatus: (taskId, status) =>
    apiFetch(`/tasks/${taskId}/status`, { method: "PATCH", json: { status } }),
  deleteTask: (taskId) => apiFetch(`/tasks/${taskId}`, { method: "DELETE" }),

  listMessages: (teamId, since) =>
    apiFetch(`/teams/${teamId}/messages${since ? `?since=${encodeURIComponent(since)}` : ""}`),
  sendMessage: (teamId, content) =>
    apiFetch(`/teams/${teamId}/messages`, { method: "POST", json: { content } }),
  deleteMessage: (messageId) => apiFetch(`/messages/${messageId}`, { method: "DELETE" }),
};

function requireAuthOrRedirect() {
  if (!TokenStore.get()) {
    location.href = "index.html";
    return false;
  }
  return true;
}

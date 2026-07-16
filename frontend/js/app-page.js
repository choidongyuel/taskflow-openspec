// Main app shell: kanban + chat + members, desktop tabs / mobile hamburger,
// drag & drop (desktop) + long-press status menu (mobile), 5s chat polling.

(function () {
  if (!requireAuthOrRedirect()) return;

  const params = new URLSearchParams(location.search);
  const teamId = Number(params.get("team"));
  if (!teamId) {
    location.href = "team.html";
    return;
  }

  const STATUSES = ["TODO", "DOING", "DONE"];
  const COLUMN_LABELS = { TODO: "TODO", DOING: "DOING", DONE: "DONE" };
  const COLUMN_COLORS = { TODO: "bg-amber-50", DOING: "bg-blue-50", DONE: "bg-emerald-50" };

  let currentUser = null;
  let team = null;
  let members = [];
  let tasks = [];
  let currentFilter = "";
  let currentMobileColumn = "TODO";
  let activeView = "kanban";
  let selectedTaskId = null;
  let pendingDeleteTaskId = null;
  let chatSince = null;
  let pollTimer = null;
  let longPressTimer = null;
  let longPressTriggered = false;
  let longPressTaskId = null;

  // ---- Elements ----
  const kanbanBoard = document.getElementById("kanban-board");
  const chatMessagesEl = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatCharCount = document.getElementById("chat-char-count");
  const chatSendBtn = document.getElementById("chat-send-btn");
  const membersList = document.getElementById("members-list");
  const teamNameEl = document.getElementById("team-name");

  // ================= Init =================
  async function init() {
    try {
      [currentUser, team, members] = await Promise.all([Api.me(), Api.getTeam(teamId), Api.getMembers(teamId)]);
    } catch (err) {
      return; // apiFetch handles 401 redirects; other errors just bail quietly.
    }

    if (!currentUser.team_id || currentUser.team_id !== teamId) {
      location.href = currentUser.team_id ? `app.html?team=${currentUser.team_id}` : "team.html";
      return;
    }

    teamNameEl.textContent = team.name;
    document.getElementById("user-email-desktop").textContent = currentUser.email;
    document.getElementById("user-email-mobile").textContent = currentUser.email;
    document.getElementById("mobile-avatar").textContent = currentUser.email[0].toUpperCase();
    document.getElementById("team-role-mobile").textContent =
      `${team.name} · ${currentUser.id === team.owner_id ? "owner" : "member"}`;

    setupNav();
    setupFilters();
    setupMobileColumnTabs();
    setupModal();
    setupDeleteConfirm();
    setupMobileStatusMenu();
    setupChat();
    setupFab();
    setupLogout();
    setupHamburger();

    await loadTasks();
    renderMembers();
    switchView("kanban");
  }

  // ================= Navigation =================
  function setupNav() {
    document.querySelectorAll(".nav-tab, .nav-tab-mobile").forEach((btn) => {
      btn.addEventListener("click", () => {
        switchView(btn.dataset.view);
        document.getElementById("mobile-menu").classList.add("hidden");
      });
    });
  }

  function switchView(view) {
    activeView = view;
    ["kanban", "chat", "members"].forEach((v) => {
      const section = document.getElementById(`view-${v}`);
      section.classList.toggle("hidden", v !== view);
    });
    document.querySelectorAll(".nav-tab").forEach((btn) => {
      const active = btn.dataset.view === view;
      btn.classList.toggle("bg-teal-700", active);
      btn.classList.toggle("text-white", active);
      btn.classList.toggle("text-slate-600", !active);
    });
    document.querySelectorAll(".nav-tab-mobile").forEach((btn) => {
      btn.classList.toggle("bg-slate-100", btn.dataset.view === view);
    });
    document.getElementById("fab-add-task").classList.toggle("hidden", view !== "kanban");

    if (view === "chat") {
      startPolling();
    } else {
      stopPolling();
    }
  }

  function setupHamburger() {
    const menu = document.getElementById("mobile-menu");
    document.getElementById("hamburger-btn").addEventListener("click", () => menu.classList.remove("hidden"));
    document.getElementById("mobile-menu-backdrop").addEventListener("click", () => menu.classList.add("hidden"));
  }

  function setupLogout() {
    async function doLogout(e) {
      e.preventDefault();
      try {
        await Api.logout();
      } finally {
        TokenStore.clear();
        location.href = "index.html";
      }
    }
    document.getElementById("logout-link-desktop").addEventListener("click", doLogout);
    document.getElementById("logout-link-mobile").addEventListener("click", doLogout);
  }

  // ================= Kanban =================
  function setupFilters() {
    document.querySelectorAll(".filter-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentFilter = btn.dataset.filter;
        document.querySelectorAll(".filter-btn").forEach((b) => {
          const active = b === btn;
          b.classList.toggle("bg-slate-800", active);
          b.classList.toggle("text-white", active);
          b.classList.toggle("bg-slate-100", !active);
        });
        loadTasks();
      });
    });
    // Mark the default filter ("전체") active without triggering a fetch;
    // the initial load is done explicitly once in init().
    const defaultBtn = document.querySelector('.filter-btn[data-filter=""]');
    defaultBtn.classList.add("bg-slate-800", "text-white");
  }

  function setupMobileColumnTabs() {
    document.querySelectorAll(".col-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentMobileColumn = btn.dataset.col;
        highlightMobileColumnTab();
        const panel = document.getElementById(`col-panel-${btn.dataset.col}`);
        if (panel) panel.scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
      });
    });
    highlightMobileColumnTab();
  }

  function highlightMobileColumnTab() {
    document.querySelectorAll(".col-tab").forEach((b) => {
      const active = b.dataset.col === currentMobileColumn;
      b.classList.toggle("bg-slate-800", active);
      b.classList.toggle("text-white", active);
      b.classList.toggle("bg-slate-100", !active);
    });
  }

  async function loadTasks() {
    try {
      tasks = await Api.listTasks(teamId, currentFilter || undefined);
      renderKanban();
    } catch (err) {
      console.error(err);
    }
  }

  function renderKanban() {
    kanbanBoard.innerHTML = "";
    STATUSES.forEach((status) => {
      const columnTasks = tasks.filter((t) => t.status === status);
      const panel = document.createElement("div");
      panel.id = `col-panel-${status}`;
      panel.className = `kanban-mobile-panel w-full flex-shrink-0 md:w-auto md:flex-shrink flex flex-col rounded-lg ${COLUMN_COLORS[status]} p-3`;

      panel.innerHTML = `
        <div class="flex items-center justify-between mb-3">
          <span class="font-bold text-sm">${COLUMN_LABELS[status]} · ${columnTasks.length}</span>
          <button class="add-task-btn text-lg font-bold text-slate-500 hover:text-slate-800" data-status="${status}">+</button>
        </div>
        <div class="inline-form-slot"></div>
        <div class="task-list flex-1 space-y-2 min-h-[80px]" data-status="${status}"></div>
      `;

      const listEl = panel.querySelector(".task-list");
      if (columnTasks.length === 0) {
        listEl.innerHTML = `
          <div class="border-2 border-dashed border-slate-300 rounded p-6 text-center text-slate-400 text-sm">
            📋<br />카드 없음<br />
            ${status === "TODO" ? '<span class="add-task-btn text-teal-700 cursor-pointer" data-status="TODO">+ 첫 태스크 만들기</span>' : "드래그로 이동"}
          </div>
        `;
      } else {
        columnTasks.forEach((task) => listEl.appendChild(renderTaskCard(task)));
      }

      panel.querySelectorAll(".add-task-btn").forEach((btn) =>
        btn.addEventListener("click", () => showInlineForm(panel, btn.dataset.status))
      );

      // Drag & drop (desktop mouse)
      listEl.addEventListener("dragover", (e) => {
        e.preventDefault();
        listEl.classList.add("column-drop-target");
      });
      listEl.addEventListener("dragleave", () => listEl.classList.remove("column-drop-target"));
      listEl.addEventListener("drop", async (e) => {
        e.preventDefault();
        listEl.classList.remove("column-drop-target");
        const taskId = Number(e.dataTransfer.getData("text/plain"));
        if (!taskId) return;
        try {
          await Api.updateTaskStatus(taskId, status);
          await loadTasks();
        } catch (err) {
          alert(err.message);
        }
      });

      kanbanBoard.appendChild(panel);
    });
  }

  function assigneeLabel(task) {
    if (!task.assignee_id) return '<span class="text-amber-600">⚠ 미할당</span>';
    if (task.assignee_id === currentUser.id) return "@me";
    const m = members.find((mm) => mm.id === task.assignee_id);
    return m ? `@${m.email.split("@")[0]}` : "@?";
  }

  function renderTaskCard(task) {
    const card = document.createElement("div");
    card.className = "task-card bg-white rounded border p-3 shadow-sm fade-in";
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.innerHTML = `
      <div class="font-medium text-sm">${escapeHtml(task.title)}</div>
      <div class="text-xs text-slate-400 mt-1">#${task.id} · ${assigneeLabel(task)}</div>
    `;

    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(task.id));
    });

    card.addEventListener("click", () => {
      if (longPressTriggered) {
        longPressTriggered = false;
        return;
      }
      openTaskModal(task.id);
    });

    // Mobile long-press -> quick status menu
    card.addEventListener("touchstart", () => {
      longPressTriggered = false;
      longPressTaskId = task.id;
      longPressTimer = setTimeout(() => {
        longPressTriggered = true;
        if (navigator.vibrate) navigator.vibrate(15);
        openMobileStatusMenu(task.id);
      }, 500);
    });
    card.addEventListener("touchend", () => clearTimeout(longPressTimer));
    card.addEventListener("touchmove", () => clearTimeout(longPressTimer));

    return card;
  }

  function showInlineForm(panel, status) {
    const slot = panel.querySelector(".inline-form-slot");
    slot.innerHTML = `
      <div class="bg-white border-2 border-teal-600 rounded p-2 mb-2 fade-in">
        <input class="inline-title w-full border-b mb-2 px-1 py-1 text-sm focus:outline-none" placeholder="태스크 제목" />
        <select class="inline-assignee w-full text-sm border rounded px-1 py-1 mb-2">
          <option value="">담당자: 미할당</option>
          ${members.map((m) => `<option value="${m.id}">담당자: ${m.id === currentUser.id ? "@me" : m.email}</option>`).join("")}
        </select>
        <div class="text-xs text-slate-400">Enter: 저장 · Esc: 취소</div>
      </div>
    `;
    const titleInput = slot.querySelector(".inline-title");
    const assigneeSelect = slot.querySelector(".inline-assignee");
    titleInput.focus();

    async function save() {
      const title = titleInput.value.trim();
      if (!title) return;
      const assigneeId = assigneeSelect.value ? Number(assigneeSelect.value) : null;
      try {
        await Api.createTask(teamId, title, assigneeId);
        slot.innerHTML = "";
        await loadTasks();
      } catch (err) {
        alert(err.message);
      }
    }

    titleInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") save();
      if (e.key === "Escape") slot.innerHTML = "";
    });
  }

  function setupFab() {
    document.getElementById("fab-add-task").addEventListener("click", () => {
      const panel = document.getElementById(`col-panel-${currentMobileColumn}`);
      if (panel) showInlineForm(panel, currentMobileColumn);
    });
  }

  // ================= Task detail modal =================
  function setupModal() {
    document.getElementById("task-modal-close").addEventListener("click", closeTaskModal);
    document.getElementById("task-modal-save").addEventListener("click", saveTaskModal);
    document.getElementById("task-modal-delete").addEventListener("click", () => {
      pendingDeleteTaskId = selectedTaskId;
      const task = tasks.find((t) => t.id === selectedTaskId);
      document.getElementById("delete-confirm-detail").textContent =
        `'#${task.id} ${task.title}' — 되돌릴 수 없습니다`;
      document.getElementById("delete-confirm").classList.remove("hidden");
      document.getElementById("delete-confirm").classList.add("flex");
    });
    document.querySelectorAll(".status-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".status-btn").forEach((b) => b.classList.remove("bg-teal-700", "text-white"));
        btn.classList.add("bg-teal-700", "text-white");
        btn.dataset.selected = "true";
        document.querySelectorAll(".status-btn").forEach((b) => {
          if (b !== btn) delete b.dataset.selected;
        });
      });
    });
  }

  function openTaskModal(taskId) {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;
    selectedTaskId = taskId;

    document.getElementById("task-modal-id").textContent = `#${task.id}`;
    document.getElementById("task-modal-title-label").textContent = task.title;
    document.getElementById("task-modal-title-input").value = task.title;
    document.getElementById("task-modal-creator").textContent =
      memberLabelById(task.creator_id) || `user#${task.creator_id}`;
    document.getElementById("task-modal-created").textContent = new Date(task.created_at).toLocaleString("ko-KR");

    document.querySelectorAll(".status-btn").forEach((btn) => {
      const active = btn.dataset.status === task.status;
      btn.classList.toggle("bg-teal-700", active);
      btn.classList.toggle("text-white", active);
      if (active) btn.dataset.selected = "true";
      else delete btn.dataset.selected;
    });

    const assigneeSelect = document.getElementById("task-modal-assignee");
    assigneeSelect.innerHTML = `
      <option value="">미할당</option>
      ${members.map((m) => `<option value="${m.id}">${m.id === currentUser.id ? "@me" : m.email}</option>`).join("")}
    `;
    assigneeSelect.value = task.assignee_id ?? "";

    const isOwner = currentUser.id === team.owner_id;
    const isCreator = currentUser.id === task.creator_id;
    document.getElementById("task-modal-delete").classList.toggle("hidden", !(isOwner || isCreator));

    const modal = document.getElementById("task-modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  }

  function closeTaskModal() {
    const modal = document.getElementById("task-modal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    selectedTaskId = null;
  }

  async function saveTaskModal() {
    if (!selectedTaskId) return;
    const title = document.getElementById("task-modal-title-input").value.trim();
    const assigneeRaw = document.getElementById("task-modal-assignee").value;
    const assigneeId = assigneeRaw ? Number(assigneeRaw) : null;
    const selectedStatusBtn = document.querySelector('.status-btn[data-selected="true"]');
    const newStatus = selectedStatusBtn ? selectedStatusBtn.dataset.status : null;

    try {
      await Api.updateTask(selectedTaskId, title, assigneeId);
      const currentTask = tasks.find((t) => t.id === selectedTaskId);
      if (newStatus && currentTask && newStatus !== currentTask.status) {
        await Api.updateTaskStatus(selectedTaskId, newStatus);
      }
      closeTaskModal();
      await loadTasks();
    } catch (err) {
      alert(err.message);
    }
  }

  function setupDeleteConfirm() {
    document.getElementById("delete-confirm-cancel").addEventListener("click", () => {
      pendingDeleteTaskId = null;
      hideDeleteConfirm();
    });
    document.getElementById("delete-confirm-ok").addEventListener("click", async () => {
      if (!pendingDeleteTaskId) return;
      try {
        await Api.deleteTask(pendingDeleteTaskId);
        hideDeleteConfirm();
        closeTaskModal();
        await loadTasks();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  function hideDeleteConfirm() {
    const el = document.getElementById("delete-confirm");
    el.classList.add("hidden");
    el.classList.remove("flex");
  }

  // ================= Mobile status menu (long-press) =================
  function setupMobileStatusMenu() {
    document.querySelectorAll(".mobile-status-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!longPressTaskId) return;
        try {
          await Api.updateTaskStatus(longPressTaskId, btn.dataset.status);
          await loadTasks();
        } catch (err) {
          alert(err.message);
        } finally {
          closeMobileStatusMenu();
        }
      });
    });
    document.getElementById("mobile-status-cancel").addEventListener("click", closeMobileStatusMenu);
  }

  function openMobileStatusMenu(taskId) {
    longPressTaskId = taskId;
    const el = document.getElementById("mobile-status-menu");
    el.classList.remove("hidden");
    el.classList.add("flex");
  }

  function closeMobileStatusMenu() {
    const el = document.getElementById("mobile-status-menu");
    el.classList.add("hidden");
    el.classList.remove("flex");
  }

  // ================= Members =================
  function memberLabelById(id) {
    const m = members.find((mm) => mm.id === id);
    return m ? m.email : null;
  }

  function renderMembers() {
    membersList.innerHTML = members
      .map(
        (m) => `
        <li class="flex items-center justify-between border rounded px-4 py-3 bg-white">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-slate-600 text-white flex items-center justify-center text-sm font-bold">
              ${m.email[0].toUpperCase()}
            </div>
            <div>
              <div class="text-sm font-medium">${escapeHtml(m.email)}${m.id === currentUser.id ? " (나)" : ""}</div>
              <div class="text-xs text-slate-400">${m.is_owner ? "★ owner" : "member"}</div>
            </div>
          </div>
          <span class="text-xs text-slate-400">${new Date(m.created_at).toLocaleDateString("ko-KR")}</span>
        </li>
      `
      )
      .join("");
  }

  // ================= Chat =================
  function setupChat() {
    chatInput.addEventListener("input", () => {
      const len = chatInput.value.length;
      chatCharCount.textContent = String(len);
      const over = len > 1000;
      chatCharCount.parentElement.classList.toggle("text-red-600", over);
      chatSendBtn.disabled = over || len === 0;
    });

    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const content = chatInput.value;
      if (!content || content.length > 1000) return;
      try {
        await Api.sendMessage(teamId, content);
        chatInput.value = "";
        chatCharCount.textContent = "0";
        await pollMessages();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  function renderMessage(msg) {
    const isMine = msg.user_id === currentUser.id;
    const label = memberLabelById(msg.user_id) || `user#${msg.user_id}`;
    const time = new Date(msg.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
    const wrapper = document.createElement("div");
    wrapper.className = `flex ${isMine ? "justify-end" : "justify-start"} group`;
    wrapper.dataset.messageId = msg.id;
    wrapper.innerHTML = `
      <div class="max-w-[70%]">
        ${!isMine ? `<div class="text-xs text-slate-500 mb-1">${escapeHtml(label)} · ${time}</div>` : ""}
        <div class="flex items-center gap-2 ${isMine ? "flex-row-reverse" : ""}">
          <div class="${isMine ? "bg-teal-700 text-white" : "bg-white border"} rounded-lg px-3 py-2 text-sm">${escapeHtml(msg.content)}</div>
          ${isMine ? `<button class="delete-msg-btn opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 text-xs" data-message-id="${msg.id}">🗑</button>` : ""}
        </div>
        ${isMine ? `<div class="text-xs text-slate-400 mt-1 text-right">${time}</div>` : ""}
      </div>
    `;
    const deleteBtn = wrapper.querySelector(".delete-msg-btn");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", async () => {
        try {
          await Api.deleteMessage(msg.id);
          wrapper.remove();
        } catch (err) {
          alert(err.message);
        }
      });
    }
    return wrapper;
  }

  function renderEmptyChatState() {
    chatMessagesEl.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-slate-400">
        <div class="text-4xl mb-3">💬</div>
        <p class="font-semibold text-slate-600">아직 대화가 없습니다</p>
        <p class="text-sm">첫 메시지를 보내 팀원과 대화를 시작하세요</p>
      </div>
    `;
  }

  async function pollMessages() {
    try {
      const messages = await Api.listMessages(teamId, chatSince || undefined);
      if (messages.length === 0 && !chatSince) {
        renderEmptyChatState();
        return;
      }
      if (messages.length === 0) return;

      if (!chatSince) chatMessagesEl.innerHTML = "";
      messages.forEach((msg) => chatMessagesEl.appendChild(renderMessage(msg)));
      chatSince = messages[messages.length - 1].created_at;
      chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
    } catch (err) {
      console.error(err);
    }
  }

  function startPolling() {
    pollMessages();
    stopPolling();
    pollTimer = setInterval(pollMessages, 5000);
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
  }

  // ================= Utils =================
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  init();
})();

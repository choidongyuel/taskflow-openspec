// Team select screen: create a team, or join one via invite code.
// Enforces the "team_id NULL -> must pass through here" flow.

(function () {
  if (!requireAuthOrRedirect()) return;

  const userEmailEl = document.getElementById("user-email");
  const logoutLink = document.getElementById("logout-link");
  const createForm = document.getElementById("create-team-form");
  const teamNameInput = document.getElementById("team-name");
  const createError = document.getElementById("create-team-error");
  const joinForm = document.getElementById("join-team-form");
  const inviteCodeInput = document.getElementById("invite-code");
  const joinError = document.getElementById("join-team-error");

  async function init() {
    try {
      const user = await Api.me();
      TokenStore.setUser(user);
      userEmailEl.textContent = user.email;
      if (user.team_id) {
        // Already in a team: no need to be on this screen.
        location.href = `app.html?team=${user.team_id}`;
      }
    } catch (err) {
      // apiFetch already redirects to index.html on 401.
    }
  }

  logoutLink.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await Api.logout();
    } finally {
      TokenStore.clear();
      location.href = "index.html";
    }
  });

  createForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    createError.classList.add("hidden");
    const name = teamNameInput.value.trim();
    if (name.length < 1 || name.length > 30) {
      createError.textContent = "팀 이름은 1-30자여야 합니다";
      createError.classList.remove("hidden");
      return;
    }
    try {
      const team = await Api.createTeam(name);
      location.href = `app.html?team=${team.id}`;
    } catch (err) {
      createError.textContent = err.message;
      createError.classList.remove("hidden");
    }
  });

  joinForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    joinError.classList.add("hidden");
    const code = inviteCodeInput.value.trim().toUpperCase();
    try {
      const team = await Api.joinTeam(code);
      location.href = `app.html?team=${team.id}`;
    } catch (err) {
      joinError.textContent = err.message;
      joinError.classList.remove("hidden");
    }
  });

  init();
})();

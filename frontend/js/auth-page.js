// Login / Signup screen logic. Toggles between the two modes on one form.

(function () {
  let mode = "login"; // "login" | "signup"

  const form = document.getElementById("auth-form");
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const emailError = document.getElementById("email-error");
  const passwordError = document.getElementById("password-error");
  const serverError = document.getElementById("server-error");
  const submitBtn = document.getElementById("submit-btn");
  const formTitle = document.getElementById("form-title");
  const togglePrompt = document.getElementById("toggle-prompt");
  const toggleLink = document.getElementById("toggle-link");

  // Already logged in? Skip straight past this screen.
  if (TokenStore.get()) {
    location.href = "team.html";
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function setMode(next) {
    mode = next;
    if (mode === "login") {
      formTitle.textContent = "로그인";
      submitBtn.textContent = "로그인";
      togglePrompt.textContent = "계정이 없으신가요?";
      toggleLink.textContent = "회원가입";
    } else {
      formTitle.textContent = "회원가입";
      submitBtn.textContent = "가입하기";
      togglePrompt.textContent = "이미 계정이 있으신가요?";
      toggleLink.textContent = "로그인";
    }
    serverError.classList.add("hidden");
    emailError.classList.add("hidden");
    passwordError.classList.add("hidden");
  }

  toggleLink.addEventListener("click", (e) => {
    e.preventDefault();
    setMode(mode === "login" ? "signup" : "login");
  });

  function afterAuthSuccess(user) {
    if (!user.team_id) {
      location.href = "team.html";
    } else {
      location.href = `app.html?team=${user.team_id}`;
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    serverError.classList.add("hidden");
    emailError.classList.add("hidden");
    passwordError.classList.add("hidden");

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    let hasError = false;
    if (!isValidEmail(email)) {
      emailError.classList.remove("hidden");
      hasError = true;
    }
    if (mode === "signup" && password.length < 8) {
      passwordError.classList.remove("hidden");
      hasError = true;
    }
    if (hasError) return;

    submitBtn.disabled = true;
    submitBtn.textContent = "처리 중...";
    try {
      const result = mode === "login" ? await Api.login(email, password) : await Api.signup(email, password);
      TokenStore.set(result.token);
      TokenStore.setUser(result.user);
      afterAuthSuccess(result.user);
    } catch (err) {
      serverError.textContent = err.message || "요청 처리 중 오류가 발생했습니다";
      serverError.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = mode === "login" ? "로그인" : "가입하기";
    }
  });
})();

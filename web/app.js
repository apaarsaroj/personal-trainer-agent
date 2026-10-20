(() => {
  const STORAGE_KEY = "form.member";

  const gate = document.getElementById("gate");
  const chat = document.getElementById("chat");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const gateError = document.getElementById("gate-error");
  const messagesEl = document.getElementById("messages");
  const composer = document.getElementById("composer");
  const messageInput = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const memberLine = document.getElementById("member-line");
  const logoutBtn = document.getElementById("logout-btn");
  const modeButtons = document.querySelectorAll(".mode-btn");

  /** @type {{ member_id: string, first_name: string, profile: object } | null} */
  let session = null;
  let sending = false;

  function showError(message) {
    gateError.hidden = !message;
    gateError.textContent = message || "";
  }

  function setMode(mode) {
    modeButtons.forEach((btn) => {
      const active = btn.dataset.mode === mode;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    loginForm.classList.toggle("is-hidden", mode !== "login");
    registerForm.classList.toggle("is-hidden", mode !== "register");
    showError("");
  }

  function showGate() {
    chat.hidden = true;
    chat.classList.remove("is-active");
    gate.hidden = false;
    gate.classList.add("is-active");
  }

  function showChat() {
    gate.hidden = true;
    gate.classList.remove("is-active");
    chat.hidden = false;
    chat.classList.add("is-active");
  }

  function persistSession(data) {
    session = {
      member_id: data.member_id,
      first_name: data.first_name || data.profile?.first_name || "Member",
      profile: data.profile,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }

  function clearSession() {
    session = null;
    localStorage.removeItem(STORAGE_KEY);
  }

  function loadSession() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function appendMessage(role, text, extraClass = "") {
    const bubble = document.createElement("div");
    bubble.className = `msg msg-${role}${extraClass ? ` ${extraClass}` : ""}`;
    bubble.textContent = text;
    messagesEl.appendChild(bubble);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }

  function enterChat(data, { welcome = true } = {}) {
    persistSession(data);
    memberLine.textContent = `${session.first_name} · ${session.member_id}`;
    messagesEl.innerHTML = "";
    if (welcome) {
      appendMessage(
        "system",
        `Hi ${session.first_name}. Tell me what you want to train today — plans, form, logging, recovery.`,
      );
    }
    showChat();
    messageInput.focus();
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    let body = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      body = await response.json();
    } else {
      body = await response.text();
    }
    if (!response.ok) {
      let detail = body && body.detail;
      if (Array.isArray(detail)) {
        detail = detail
          .map((item) => item.msg || JSON.stringify(item))
          .join(" ");
      }
      if (!detail) {
        detail =
          typeof body === "string" && body.trim()
            ? body
            : `Request failed (${response.status})`;
      }
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  modeButtons.forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showError("");
    const memberId = new FormData(loginForm).get("member_id").toString().trim();
    const submit = loginForm.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      const data = await api("/api/login", {
        method: "POST",
        body: JSON.stringify({ member_id: memberId }),
      });
      enterChat(data);
    } catch (err) {
      showError(err.message || "Could not log in.");
    } finally {
      submit.disabled = false;
    }
  });

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showError("");
    const form = new FormData(registerForm);
    const payload = {
      first_name: form.get("first_name").toString().trim(),
      last_name: form.get("last_name").toString().trim(),
      age: Number(form.get("age")),
      weight_kg: Number(form.get("weight_kg")),
      height_cm: Number(form.get("height_cm")),
      fitness_level: form.get("fitness_level").toString(),
      days_per_week: Number(form.get("days_per_week")),
      goals: form
        .get("goals")
        .toString()
        .split(",")
        .map((g) => g.trim())
        .filter(Boolean),
      injuries: form
        .get("injuries")
        .toString()
        .split(",")
        .map((g) => g.trim())
        .filter(Boolean),
    };
    const submit = registerForm.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      const data = await api("/api/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      enterChat({
        member_id: data.member_id,
        first_name: data.profile.first_name,
        profile: data.profile,
      });
      appendMessage(
        "system",
        `Your member ID is ${data.member_id}. Save it — you will need it next time.`,
      );
    } catch (err) {
      showError(err.message || "Could not register.");
    } finally {
      submit.disabled = false;
    }
  });

  function autosize() {
    messageInput.style.height = "auto";
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 140)}px`;
  }

  messageInput.addEventListener("input", autosize);

  messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      composer.requestSubmit();
    }
  });

  composer.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!session || sending) return;
    const text = messageInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    messageInput.value = "";
    autosize();

    sending = true;
    sendBtn.disabled = true;
    messageInput.disabled = true;
    const pending = appendMessage("assistant", "Thinking through your next move…", "pending");

    try {
      const data = await api("/api/chat", {
        method: "POST",
        body: JSON.stringify({ member_id: session.member_id, message: text }),
      });
      pending.classList.remove("pending");
      pending.textContent = data.reply;
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } catch (err) {
      pending.classList.remove("pending");
      pending.textContent =
        err.message || "Something went wrong talking to your trainer. Try again in a moment.";
    } finally {
      sending = false;
      sendBtn.disabled = false;
      messageInput.disabled = false;
      messageInput.focus();
    }
  });

  logoutBtn.addEventListener("click", () => {
    clearSession();
    messagesEl.innerHTML = "";
    showGate();
    setMode("login");
  });

  async function boot() {
    const saved = loadSession();
    if (!saved?.member_id) {
      showGate();
      return;
    }
    try {
      const profile = await api(`/api/members/${encodeURIComponent(saved.member_id)}`);
      enterChat(
        {
          member_id: profile.member_id,
          first_name: profile.first_name,
          profile,
        },
        { welcome: true },
      );
    } catch {
      clearSession();
      showGate();
    }
  }

  boot();
})();

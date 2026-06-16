const state = {
  token: localStorage.getItem("santebien_token") || "",
  user: null,
  search: "",
  sort: "recent",
  tag: "",
};

const content = document.querySelector("#app-content");
const modalBackdrop = document.querySelector("#modal-backdrop");
const modalContent = document.querySelector("#modal-content");

const escapeHtml = (value = "") =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const formatDate = (value) =>
  new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(value),
  );

const initials = (name = "?") =>
  name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`/api${path}`, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(", ")
      : data.detail || "Une erreur est survenue";
    throw new Error(detail);
  }
  return data;
}

function toast(message, type = "success") {
  const node = document.createElement("div");
  node.className = `toast ${type}`;
  node.textContent = message;
  document.querySelector("#toast-container").append(node);
  setTimeout(() => node.remove(), 3500);
}

function setLoading() {
  content.innerHTML = `<div class="loading">Chargement de SanteBien...</div>`;
}

function requireAuth(message = "Connectez-vous pour continuer.") {
  if (state.user) return true;
  toast(message, "error");
  showAuth("login");
  return false;
}

function doctorBadge(user) {
  return user.role === "doctor"
    ? `<span class="doctor-badge">Médecin vérifié</span>`
    : user.role === "admin"
      ? `<span class="role-badge">Admin</span>`
      : "";
}

function tagsHtml(tags = []) {
  return `<div class="tags">${tags.map((tag) => `<button class="tag" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join("")}</div>`;
}

function authorHtml(user, createdAt) {
  return `<div class="author-line">
    ${doctorBadge(user)}
    <span class="author-name">${escapeHtml(user.display_name)}</span>
    <span>${formatDate(createdAt)}</span>
  </div>`;
}

function pageHead(eyebrow, title, description, action = "") {
  return `<header class="page-head">
    <div>
      <span class="eyebrow">${eyebrow}</span>
      <h1>${title}</h1>
      <p>${description}</p>
    </div>
    ${action}
  </header>`;
}

function questionCard(question) {
  return `<article class="question-card">
    <div class="question-metrics">
      <span><strong>${question.vote_count}</strong> votes</span>
      <span class="${question.comment_count ? "answered" : ""}"><strong>${question.comment_count}</strong> réponses</span>
      <span><strong>${question.view_count}</strong> vues</span>
    </div>
    <div class="question-content">
      <h2><a href="#/questions/${question.id}">${escapeHtml(question.title)}</a></h2>
      <p class="excerpt">${escapeHtml(question.description)}</p>
      <div class="item-footer">
        ${tagsHtml(question.tags)}
        ${authorHtml(question.author, question.created_at)}
      </div>
    </div>
  </article>`;
}

async function renderQuestions() {
  setLoading();
  const query = new URLSearchParams({ sort: state.sort });
  if (state.search) query.set("search", state.search);
  if (state.tag) query.set("tag", state.tag);
  const questions = await api(`/questions?${query}`);
  content.innerHTML = `
    ${pageHead(
      "Communauté",
      state.tag ? `Questions : ${escapeHtml(state.tag)}` : "Questions de santé",
      "Partagez une expérience, posez une question et échangez avec la communauté et les médecins vérifiés.",
      `<a class="button primary" href="#/ask">Poser une question</a>`,
    )}
    <div class="tabs">
      <button data-sort="recent" class="${state.sort === "recent" ? "active" : ""}">Récentes</button>
      <button data-sort="popular" class="${state.sort === "popular" ? "active" : ""}">Populaires</button>
      <button data-sort="unanswered" class="${state.sort === "unanswered" ? "active" : ""}">Sans réponse</button>
    </div>
    <section class="content-list">
      ${questions.length ? questions.map(questionCard).join("") : `<div class="empty">Aucune question ne correspond à cette recherche.</div>`}
    </section>`;
}

function answerCard(comment) {
  return `<article class="answer-card">
    <div class="vote-box"><button aria-label="Vote positif">↑</button><span>${comment.vote_count}</span></div>
    <div class="answer-body">
      <p>${escapeHtml(comment.content)}</p>
      ${authorHtml(comment.author, comment.created_at)}
    </div>
  </article>`;
}

async function renderQuestionDetail(id) {
  setLoading();
  const question = await api(`/questions/${id}`);
  content.innerHTML = `
    <article class="detail-card">
      ${tagsHtml(question.tags)}
      <h1>${escapeHtml(question.title)}</h1>
      <div class="detail-meta">
        <span>Posée le ${formatDate(question.created_at)}</span>
        <span>${question.view_count} vues</span>
        <span>${question.vote_count} votes</span>
      </div>
      <div class="answer-card">
        <div class="vote-box">
          <button data-vote-question="${question.id}" aria-label="Vote positif">↑</button>
          <span>${question.vote_count}</span>
        </div>
        <div class="answer-body">
          <p>${escapeHtml(question.description)}</p>
          ${authorHtml(question.author, question.created_at)}
        </div>
      </div>
    </article>
    <section class="answer-section">
      <h2>${question.comment_count} réponse${question.comment_count > 1 ? "s" : ""}</h2>
      ${question.comments.length ? question.comments.map(answerCard).join("") : `<div class="empty">Soyez la première personne à répondre.</div>`}
    </section>
    <section class="form-card" style="margin-top: 22px;">
      <h2>Votre réponse</h2>
      <p class="modal-intro">Partagez une expérience utile. Un avis médical ne remplace jamais une consultation.</p>
      <form class="form-grid" id="comment-form" data-question-id="${question.id}">
        <div class="field">
          <label for="comment-content">Réponse</label>
          <textarea id="comment-content" name="content" minlength="10" required placeholder="Écrivez une réponse claire et bienveillante..."></textarea>
        </div>
        <div class="form-actions"><button class="button primary">Publier la réponse</button></div>
      </form>
    </section>`;
}

async function renderArticles() {
  setLoading();
  const articles = await api(`/articles${state.search ? `?search=${encodeURIComponent(state.search)}` : ""}`);
  const canPublish = state.user && ["doctor", "admin"].includes(state.user.role);
  content.innerHTML = `
    ${pageHead(
      "Prévention",
      "Articles santé",
      "Des contenus pédagogiques publiés par les médecins vérifiés de la communauté.",
      canPublish ? `<a class="button primary" href="#/write-article">Publier un article</a>` : "",
    )}
    <section class="article-grid">
      ${articles.length ? articles.map((article) => `
        <article class="article-card">
          <div class="article-topline">${doctorBadge(article.author)}<span>${article.view_count} vues</span></div>
          <h2><a href="#/articles/${article.id}">${escapeHtml(article.title)}</a></h2>
          <p class="excerpt">${escapeHtml(article.summary)}</p>
          ${tagsHtml(article.tags)}
          <div style="margin-top: 18px;">${authorHtml(article.author, article.created_at)}</div>
        </article>`).join("") : `<div class="empty">Aucun article publié.</div>`}
    </section>`;
}

async function renderArticleDetail(id) {
  setLoading();
  const article = await api(`/articles/${id}`);
  content.innerHTML = `
    <article class="detail-card">
      ${tagsHtml(article.tags)}
      <h1>${escapeHtml(article.title)}</h1>
      <div class="detail-meta">${doctorBadge(article.author)}<span>Par ${escapeHtml(article.author.display_name)}</span><span>${formatDate(article.created_at)}</span><span>${article.view_count} vues</span></div>
      <p class="excerpt" style="font-size: 16px; -webkit-line-clamp: unset;">${escapeHtml(article.summary)}</p>
      <div class="detail-body">${escapeHtml(article.content)}</div>
    </article>
    <section class="answer-section">
      <h2>Commentaires</h2>
      ${article.comments.length ? article.comments.map(answerCard).join("") : `<div class="empty">Aucun commentaire pour le moment.</div>`}
    </section>
    <section class="form-card" style="margin-top: 22px;">
      <h2>Commenter l'article</h2>
      <form class="form-grid" id="article-comment-form" data-article-id="${article.id}">
        <div class="field"><textarea name="content" minlength="10" required placeholder="Partagez une remarque utile..."></textarea></div>
        <div class="form-actions"><button class="button primary">Publier</button></div>
      </form>
    </section>`;
}

function renderQuestionForm() {
  if (!requireAuth("Connectez-vous pour poser une question.")) return;
  content.innerHTML = `
    ${pageHead("Nouvelle question", "Posez une question utile", "Décrivez clairement votre situation sans publier d'informations personnelles sensibles.")}
    <form class="form-card form-grid" id="question-form">
      <div class="field"><label>Titre</label><input name="title" minlength="10" maxlength="180" required placeholder="Ex. Comment améliorer progressivement mon sommeil ?" /><small>Une phrase précise qui résume le sujet.</small></div>
      <div class="field"><label>Description</label><textarea name="description" minlength="20" required placeholder="Contexte, habitudes déjà testées, objectif recherché..."></textarea></div>
      <div class="field"><label>Tags</label><input name="tags" placeholder="sommeil, prévention, bien-être" /><small>Maximum cinq tags, séparés par des virgules.</small></div>
      <div class="ai-panel hidden" id="ai-analysis"></div>
      <div class="form-actions"><button class="button ghost" type="button" data-ai-analyze>Analyser avec l'IA frugale</button><button class="button primary">Publier la question</button><a class="button ghost" href="#/questions">Annuler</a></div>
    </form>`;
}

function renderArticleForm() {
  if (!requireAuth()) return;
  if (!["doctor", "admin"].includes(state.user.role)) {
    toast("Seuls les médecins vérifiés peuvent publier un article.", "error");
    location.hash = "#/doctor";
    return;
  }
  content.innerHTML = `
    ${pageHead("Médecins vérifiés", "Publier un article santé", "Créez un contenu pédagogique, clair et accessible.")}
    <form class="form-card form-grid" id="article-form">
      <div class="field"><label>Titre</label><input name="title" minlength="10" maxlength="180" required /></div>
      <div class="field"><label>Résumé</label><textarea name="summary" minlength="20" maxlength="320" required style="min-height: 90px;"></textarea></div>
      <div class="field"><label>Contenu</label><textarea name="content" minlength="100" required style="min-height: 260px;"></textarea></div>
      <div class="field"><label>Tags</label><input name="tags" placeholder="prévention, sommeil" /></div>
      <div class="form-actions"><button class="button primary">Publier l'article</button></div>
    </form>`;
}

async function renderProfile() {
  if (!requireAuth()) return;
  content.innerHTML = `
    <section class="profile-hero">
      <div class="avatar">${initials(state.user.display_name)}</div>
      <div><h1>${escapeHtml(state.user.display_name)}</h1><p>${escapeHtml(state.user.email)} · ${escapeHtml(state.user.role)}</p></div>
      ${doctorBadge(state.user)}
    </section>
    <form class="form-card form-grid" id="profile-form">
      <h2>Modifier mon profil</h2>
      <div class="field"><label>Nom affiché</label><input name="display_name" value="${escapeHtml(state.user.display_name)}" required /></div>
      <div class="field"><label>Biographie</label><textarea name="bio" style="min-height: 110px;">${escapeHtml(state.user.bio)}</textarea></div>
      <div class="field"><label>Spécialité</label><input name="specialty" value="${escapeHtml(state.user.specialty)}" placeholder="Optionnel" /></div>
      <div class="form-actions"><button class="button primary">Enregistrer</button><button type="button" class="button danger" data-action="logout">Se déconnecter</button></div>
    </form>`;
}

async function renderDoctorApplication() {
  if (!requireAuth()) return;
  if (state.user.role === "doctor") {
    content.innerHTML = `${pageHead("Profil vérifié", "Vous êtes médecin vérifié", "Votre profil peut publier des articles santé et vos réponses affichent le badge médecin.")}<div class="panel"><span class="doctor-badge">Médecin vérifié</span><h2>${escapeHtml(state.user.specialty || "Médecin")}</h2></div>`;
    return;
  }
  const application = await api("/doctor-applications/me");
  if (application) {
    content.innerHTML = `
      ${pageHead("Validation médicale", "Votre demande a été envoyée", "Un administrateur examinera vos justificatifs.")}
      <div class="panel">
        <span class="role-badge">${escapeHtml(application.status)}</span>
        <h2>${escapeHtml(application.specialty)}</h2>
        <p>Numéro professionnel : ${escapeHtml(application.license_number)}</p>
        <p>${escapeHtml(application.motivation)}</p>
        ${application.admin_note ? `<div class="statement">${escapeHtml(application.admin_note)}</div>` : ""}
      </div>`;
    return;
  }
  content.innerHTML = `
    ${pageHead("Validation médicale", "Devenir médecin vérifié", "Envoyez vos informations professionnelles. Elles seront examinées par les administrateurs.")}
    <form class="form-card form-grid" id="doctor-form">
      <div class="field"><label>Numéro professionnel / RPPS</label><input name="license_number" minlength="4" required /></div>
      <div class="field"><label>Spécialité</label><input name="specialty" minlength="3" required /></div>
      <div class="field"><label>Lien vers un justificatif</label><input name="document_url" type="url" required placeholder="https://..." /><small>Pour ce MVP, le justificatif est représenté par un lien sécurisé.</small></div>
      <div class="field"><label>Motivation</label><textarea name="motivation" minlength="30" required></textarea></div>
      <div class="form-actions"><button class="button primary">Envoyer ma demande</button></div>
    </form>`;
}

async function renderAdmin() {
  if (!requireAuth()) return;
  if (state.user.role !== "admin") {
    content.innerHTML = `<div class="empty">Cet espace est réservé aux administrateurs.</div>`;
    return;
  }
  const applications = await api("/admin/doctor-applications?status=pending");
  content.innerHTML = `
    ${pageHead("Administration", "Demandes de validation médecin", "Vérifiez les informations avant d'accorder le badge médecin.")}
    <section class="content-list">
      ${applications.length ? applications.map((item) => `
        <article class="admin-row">
          <div>
            <span class="pill">${escapeHtml(item.specialty)}</span>
            <h3>${escapeHtml(item.user.display_name)}</h3>
            <p>${escapeHtml(item.user.email)} · ${escapeHtml(item.license_number)}</p>
            <p>${escapeHtml(item.motivation)}</p>
            <a class="author-name" href="${escapeHtml(item.document_url)}" target="_blank" rel="noreferrer">Consulter le justificatif</a>
          </div>
          <div class="admin-actions">
            <button class="button primary small" data-review="${item.id}" data-status="approved">Approuver</button>
            <button class="button danger small" data-review="${item.id}" data-status="rejected">Refuser</button>
          </div>
        </article>`).join("") : `<div class="empty">Aucune demande en attente.</div>`}
    </section>`;
}

function showAuth(mode = "login") {
  const login = mode === "login";
  modalContent.innerHTML = `
    <span class="eyebrow">${login ? "Bienvenue" : "Rejoindre SanteBien"}</span>
    <h2 id="modal-title">${login ? "Se connecter" : "Créer un compte"}</h2>
    <p class="modal-intro">${login ? "Retrouvez vos questions et participez aux échanges." : "Un compte simple pour poser des questions et répondre."}</p>
    <form class="form-grid" id="auth-form" data-mode="${mode}">
      ${login ? "" : `<div class="field"><label>Nom affiché</label><input name="display_name" minlength="2" required /></div>`}
      <div class="field"><label>Email</label><input name="email" type="email" required /></div>
      <div class="field"><label>Mot de passe</label><input name="password" type="password" minlength="8" required /></div>
      <button class="button primary">${login ? "Connexion" : "Créer mon compte"}</button>
    </form>
    <p class="switch-auth">${login ? "Pas encore de compte ?" : "Déjà membre ?"} <button data-auth-switch="${login ? "register" : "login"}">${login ? "S'inscrire" : "Se connecter"}</button></p>
    ${login ? `<div class="statement">Démo : user@santebien.fr / User123!<br />Admin : admin@santebien.fr / Admin123!</div>` : ""}`;
  modalBackdrop.classList.remove("hidden");
}

function closeModal() {
  modalBackdrop.classList.add("hidden");
}

async function loadUser() {
  if (!state.token) return updateUserUi();
  try {
    state.user = await api("/auth/me");
  } catch {
    state.token = "";
    localStorage.removeItem("santebien_token");
  }
  updateUserUi();
}

function updateUserUi() {
  const actions = document.querySelector("#top-actions");
  const adminLink = document.querySelector(".admin-link");
  if (!state.user) {
    actions.innerHTML = `<button class="button ghost" data-action="login">Connexion</button><button class="button primary" data-action="register">Créer un compte</button>`;
    adminLink.classList.add("hidden");
    return;
  }
  actions.innerHTML = `<a class="button ghost" href="#/profile">${escapeHtml(state.user.display_name)}</a><a class="button primary" href="#/ask">Poser une question</a>`;
  adminLink.classList.toggle("hidden", state.user.role !== "admin");
}

async function loadStats() {
  try {
    const stats = await api("/stats");
    document.querySelector("#stats-grid").innerHTML = `
      <div><strong>${stats.members}</strong><span>Membres</span></div>
      <div><strong>${stats.questions}</strong><span>Questions</span></div>
      <div><strong>${stats.verified_doctors}</strong><span>Médecins</span></div>
      <div><strong>${stats.articles}</strong><span>Articles</span></div>`;
  } catch {}
}

async function router() {
  document.querySelector("#sidebar").classList.remove("open");
  const parts = location.hash.replace(/^#\//, "").split("/").filter(Boolean);
  const route = parts[0] || "questions";
  document.querySelectorAll("[data-nav]").forEach((link) => link.classList.toggle("active", link.dataset.nav === route));
  try {
    if (route === "questions" && parts[1]) await renderQuestionDetail(parts[1]);
    else if (route === "questions") await renderQuestions();
    else if (route === "articles" && parts[1]) await renderArticleDetail(parts[1]);
    else if (route === "articles") await renderArticles();
    else if (route === "ask") renderQuestionForm();
    else if (route === "write-article") renderArticleForm();
    else if (route === "profile") await renderProfile();
    else if (route === "doctor") await renderDoctorApplication();
    else if (route === "admin") await renderAdmin();
    else location.hash = "#/questions";
  } catch (error) {
    content.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

document.addEventListener("click", async (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "login" || action === "register") showAuth(action);
  if (action === "logout") {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    state.token = "";
    state.user = null;
    localStorage.removeItem("santebien_token");
    updateUserUi();
    location.hash = "#/questions";
    toast("Vous êtes déconnecté.");
  }

  const switchMode = event.target.closest("[data-auth-switch]")?.dataset.authSwitch;
  if (switchMode) showAuth(switchMode);

  const tag = event.target.closest("[data-tag]")?.dataset.tag;
  if (tag) {
    state.tag = tag;
    location.hash = "#/questions";
    await renderQuestions();
  }

  const sort = event.target.closest("[data-sort]")?.dataset.sort;
  if (sort) {
    state.sort = sort;
    await renderQuestions();
  }

  const analyze = event.target.closest("[data-ai-analyze]");
  if (analyze) {
    const form = document.querySelector("#question-form");
    const panel = document.querySelector("#ai-analysis");
    const values = Object.fromEntries(new FormData(form));
    try {
      const result = await api("/ai/analyze-question", {
        method: "POST",
        body: JSON.stringify({
          title: values.title,
          description: values.description,
          tags: values.tags.split(",").map((tag) => tag.trim()).filter(Boolean),
          mode: "int8",
        }),
      });
      panel.classList.remove("hidden");
      panel.innerHTML = `
        <div><strong>Catégorie IA :</strong> ${escapeHtml(result.category)} · confiance ${(result.confidence * 100).toFixed(1)} %</div>
        <div><strong>Orientation :</strong> ${escapeHtml(result.urgency)}</div>
        <div><strong>Modèle :</strong> FP32 ${result.model.fp32_size_bytes} B → INT8 ${result.model.int8_size_bytes} B (${result.model.compression_percent} % de réduction)</div>
        <small>${escapeHtml(result.disclaimer)}</small>`;
    } catch (error) {
      toast(error.message, "error");
    }
  }

  const voteId = event.target.closest("[data-vote-question]")?.dataset.voteQuestion;
  if (voteId && requireAuth()) {
    await api(`/questions/${voteId}/vote`, { method: "POST" });
    await renderQuestionDetail(voteId);
  }

  const review = event.target.closest("[data-review]");
  if (review) {
    await api(`/admin/doctor-applications/${review.dataset.review}`, {
      method: "PATCH",
      body: JSON.stringify({ status: review.dataset.status, admin_note: "" }),
    });
    toast(`Demande ${review.dataset.status === "approved" ? "approuvée" : "refusée"}.`);
    await renderAdmin();
  }
});

document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const values = Object.fromEntries(new FormData(form));
  try {
    if (form.id === "auth-form") {
      const mode = form.dataset.mode;
      const data = await api(`/auth/${mode}`, { method: "POST", body: JSON.stringify(values) });
      state.token = data.token;
      state.user = data.user;
      localStorage.setItem("santebien_token", state.token);
      updateUserUi();
      closeModal();
      toast(mode === "login" ? "Connexion réussie." : "Compte créé avec succès.");
      await router();
    }
    if (form.id === "question-form") {
      const data = await api("/questions", {
        method: "POST",
        body: JSON.stringify({ ...values, tags: values.tags.split(",").map((tag) => tag.trim()).filter(Boolean) }),
      });
      toast("Question publiée.");
      location.hash = `#/questions/${data.id}`;
    }
    if (form.id === "comment-form") {
      if (!requireAuth()) return;
      await api(`/questions/${form.dataset.questionId}/comments`, { method: "POST", body: JSON.stringify(values) });
      toast("Réponse publiée.");
      await renderQuestionDetail(form.dataset.questionId);
    }
    if (form.id === "article-form") {
      const data = await api("/articles", {
        method: "POST",
        body: JSON.stringify({ ...values, tags: values.tags.split(",").map((tag) => tag.trim()).filter(Boolean) }),
      });
      toast("Article publié.");
      location.hash = `#/articles/${data.id}`;
    }
    if (form.id === "article-comment-form") {
      if (!requireAuth()) return;
      await api(`/articles/${form.dataset.articleId}/comments`, { method: "POST", body: JSON.stringify(values) });
      toast("Commentaire publié.");
      await renderArticleDetail(form.dataset.articleId);
    }
    if (form.id === "profile-form") {
      state.user = await api("/auth/me", { method: "PATCH", body: JSON.stringify(values) });
      updateUserUi();
      toast("Profil mis à jour.");
      await renderProfile();
    }
    if (form.id === "doctor-form") {
      await api("/doctor-applications", { method: "POST", body: JSON.stringify(values) });
      toast("Demande envoyée.");
      await renderDoctorApplication();
    }
  } catch (error) {
    toast(error.message, "error");
  }
});

document.querySelector("#global-search").addEventListener("submit", (event) => {
  event.preventDefault();
  state.search = document.querySelector("#search-input").value.trim();
  state.tag = "";
  const route = location.hash.includes("/articles") ? "articles" : "questions";
  location.hash = `#/${route}`;
  router();
});

document.querySelector("#modal-close").addEventListener("click", closeModal);
modalBackdrop.addEventListener("click", (event) => {
  if (event.target === modalBackdrop) closeModal();
});
document.querySelector("#mobile-menu").addEventListener("click", () => document.querySelector("#sidebar").classList.toggle("open"));
window.addEventListener("hashchange", router);

async function start() {
  await loadUser();
  await loadStats();
  if (!location.hash) location.hash = "#/questions";
  await router();
}

start();

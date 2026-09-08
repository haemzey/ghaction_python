const $ = (selector) => document.querySelector(selector);
const state = { books: [], members: [], loans: [] };

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(data?.error || "Request failed");
  return data;
}

function showError(message) {
  const alert = $("#alert");
  alert.textContent = message;
  alert.classList.remove("hidden");
  setTimeout(() => alert.classList.add("hidden"), 4000);
}

function showSection(section) {
  document.querySelectorAll(".page-section").forEach((el) => el.classList.add("hidden"));
  $(`#${section}-section`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.toggle("active", el.dataset.section === section));
  $("#page-title").textContent = section[0].toUpperCase() + section.slice(1);
  if (section === "books") renderBooks();
  if (section === "members") renderMembers();
  if (section === "loans") renderLoans();
}

function bookCell(book) {
  return `<div class="book-title">${book.title}</div><div class="book-author">${book.author}</div>`;
}

function renderBooks() {
  const search = ($("#book-search")?.value || "").toLowerCase();
  const category = $("#category-filter")?.value || "";
  const books = state.books.filter((b) => (!category || b.category === category) && (`${b.title} ${b.author} ${b.isbn || ""}`).toLowerCase().includes(search));
  $("#books-table").innerHTML = books.length ? `<table><thead><tr><th>Book</th><th>Category</th><th>Copies</th><th>Availability</th></tr></thead><tbody>${books.map((b) => `<tr><td>${bookCell(b)}</td><td>${b.category || "—"}</td><td>${b.total_copies}</td><td><span class="pill">${b.available_copies} available</span></td></tr>`).join("")}</tbody></table>` : `<p class="muted">No books found.</p>`;
}

function renderMembers() {
  $("#members-table").innerHTML = state.members.length ? `<table><thead><tr><th>Member</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead><tbody>${state.members.map((m) => `<tr><td class="book-title">${m.name}</td><td>${m.email}</td><td>${m.phone || "—"}</td><td><span class="pill ${m.active ? "" : "returned"}">${m.active ? "Active" : "Inactive"}</span></td></tr>`).join("")}</tbody></table>` : `<p class="muted">No members yet.</p>`;
}

function renderLoans() {
  const filter = $("#loan-filter")?.value || "";
  const loans = state.loans.filter((l) => !filter || (filter === "true" ? !l.returned_at : l.returned_at));
  $("#loans-table").innerHTML = loans.length ? `<table><thead><tr><th>Book</th><th>Member</th><th>Due date</th><th>Status</th><th></th></tr></thead><tbody>${loans.map((l) => `<tr><td class="book-title">${l.book_title}</td><td>${l.member_name}</td><td>${l.due_date}</td><td><span class="pill ${l.returned_at ? "returned" : ""}">${l.returned_at ? "Returned" : "Active"}</span></td><td>${l.returned_at ? "" : `<button class="action return-loan" data-id="${l.id}">Return</button>`}</td></tr>`).join("")}</tbody></table>` : `<p class="muted">No loans found.</p>`;
  document.querySelectorAll(".return-loan").forEach((button) => button.addEventListener("click", async () => {
    try { await api(`/api/loans/${button.dataset.id}/return`, { method: "POST" }); await loadData(); } catch (error) { showError(error.message); }
  }));
}

function renderOverview() {
  const recent = state.loans.slice(0, 5);
  $("#recent-loans").innerHTML = recent.length ? `<table><thead><tr><th>Book</th><th>Member</th><th>Status</th></tr></thead><tbody>${recent.map((l) => `<tr><td>${l.book_title}</td><td>${l.member_name}</td><td><span class="pill ${l.returned_at ? "returned" : ""}">${l.returned_at ? "Returned" : "Active"}</span></td></tr>`).join("")}</tbody></table>` : `<p class="muted">No loan activity yet.</p>`;
  $("#collection-list").innerHTML = state.books.slice(0, 5).map((b) => `<div class="panel-heading"><div><div class="book-title">${b.title}</div><div class="book-author">${b.author}</div></div><span class="pill">${b.available_copies}/${b.total_copies}</span></div>`).join("") || `<p class="muted">No books yet.</p>`;
}

async function loadData() {
  try {
    const [stats, books, members, loans] = await Promise.all([api("/api/stats"), api("/api/books"), api("/api/members"), api("/api/loans")]);
    state.books = books.books; state.members = members.members; state.loans = loans.loans;
    $("#total-books").textContent = stats.books; $("#available-copies").textContent = stats.available_copies; $("#active-loans").textContent = stats.active_loans; $("#active-members").textContent = stats.active_members;
    const categories = [...new Set(state.books.map((b) => b.category).filter(Boolean))].sort();
    $("#category-filter").innerHTML = `<option value="">All categories</option>${categories.map((c) => `<option>${c}</option>`).join("")}`;
    $("#loan-book").innerHTML = state.books.filter((b) => b.available_copies).map((b) => `<option value="${b.id}">${b.title}</option>`).join("");
    $("#loan-member").innerHTML = state.members.filter((m) => m.active).map((m) => `<option value="${m.id}">${m.name}</option>`).join("");
    renderOverview(); renderBooks(); renderMembers(); renderLoans();
  } catch (error) { showError(error.message); }
}

async function submitForm(form, endpoint) {
  const data = Object.fromEntries(new FormData(form));
  ["published_year", "total_copies", "loan_days", "book_id", "member_id"].forEach((key) => { if (data[key] !== undefined && data[key] !== "") data[key] = Number(data[key]); });
  try { await api(endpoint, { method: "POST", body: JSON.stringify(data) }); form.closest(".modal").classList.add("hidden"); form.reset(); await loadData(); } catch (error) { showError(error.message); }
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => showSection(button.dataset.section)));
document.querySelectorAll("[data-section-link]").forEach((button) => button.addEventListener("click", () => showSection(button.dataset.sectionLink)));
document.querySelectorAll("[data-open-modal]").forEach((button) => button.addEventListener("click", () => $(`#${button.dataset.openModal}`).classList.remove("hidden")));
document.querySelectorAll("[data-close-modal]").forEach((button) => button.addEventListener("click", () => button.closest(".modal").classList.add("hidden")));
$("#book-form").addEventListener("submit", (event) => { event.preventDefault(); submitForm(event.target, "/api/books"); });
$("#member-form").addEventListener("submit", (event) => { event.preventDefault(); submitForm(event.target, "/api/members"); });
$("#loan-form").addEventListener("submit", (event) => { event.preventDefault(); submitForm(event.target, "/api/loans"); });
$("#refresh-btn").addEventListener("click", loadData);
$("#book-search").addEventListener("input", renderBooks);
$("#category-filter").addEventListener("change", renderBooks);
$("#loan-filter").addEventListener("change", renderLoans);
loadData();

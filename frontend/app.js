const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const bar = (p) => `<span class="bar"><i style="width:${Math.max(0, Math.min(100, p))}%"></i></span> ${p ?? "–"}`;

async function load() {
  const [ov, subs, rub] = await Promise.all(["/api/students", "/api/submissions", "/api/rubric"].map((u) => fetch(u).then((r) => r.json())));
  $("#engine").innerHTML = rub.engines.map((e) => `<option>${esc(e)}</option>`).join("");
  const t = ov.totals;
  $("#totals").innerHTML = [["Students", t.students], ["Submissions", t.submissions], ["Mean score", t.mean_score ?? "–"], ["Best", t.max_score ?? "–"], ["Lowest", t.min_score ?? "–"]]
    .map(([k, v]) => `<div class="stat"><b>${esc(v)}</b><span>${k}</span></div>`).join("");
  $("#students tbody").innerHTML = ov.students.map((s) => `<tr><td>${esc(s.name)}</td><td>${esc(s.group)}</td><td>${s.submissions}</td>
    <td>${Object.entries(s.criteria_avg).map(([k, v]) => `<span class="chip">${esc(k)} ${v}%</span>`).join("")}</td>
    <td>${bar(s.proposed_score)}%</td></tr>`).join("");
  $("#subs tbody").innerHTML = subs.map((s) => `<tr><td>${esc(new Date(s.created_at).toLocaleString())}</td><td>${esc(s.student)}</td>
    <td>${esc(s.course)} / ${esc(s.workshop)}</td>
    <td>${s.criteria.map((c) => `<span class="chip" title="${esc(c.feedback)}">${esc(c.name)} ${c.score}/${c.max_score}</span>`).join("")}</td>
    <td>${s.score}/${s.max_score}</td></tr>`).join("");
}

$("#upload").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = $("#msg");
  msg.className = ""; msg.textContent = "Grading…";
  const r = await fetch("/api/submissions", { method: "POST", body: new FormData(e.target) });
  const body = await r.json();
  if (r.ok) { msg.className = "ok"; msg.textContent = `Graded ${body.student}: ${body.score}/${body.max_score}`; e.target.reset(); load(); }
  else { msg.className = "err"; msg.textContent = body.detail; }
});

load();

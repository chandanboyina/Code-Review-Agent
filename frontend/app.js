const $ = (id) => document.getElementById(id);
const api = (path, options = {}) => fetch(path, {
  headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  ...options
}).then(async r => {
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
});

const demoDiff = `diff --git a/src/main/java/com/acme/payment/PaymentService.java b/src/main/java/com/acme/payment/PaymentService.java
index 1111111..2222222 100644
--- a/src/main/java/com/acme/payment/PaymentService.java
+++ b/src/main/java/com/acme/payment/PaymentService.java
@@ -20,8 +20,16 @@ public class PaymentService {
     public PaymentResult process(PaymentRequest request) {
+        if (request.amount() <= 0) {
+            throw new InvalidPaymentException("Amount must be positive");
+        }
+
         return repository.save(
             new Payment(request.customerId(), request.amount())
         );
     }
 }`;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[c]));
}

async function health() {
  try {
    const h = await api("/api/health");
    $("statusPill").innerHTML = `<span></span> Hindsight ${esc(h.hindsight)} · LLM ${esc(h.llm)}`;
  } catch {
    $("statusPill").innerHTML = `<span style="background:#ff7777"></span> API unavailable`;
  }
}

async function stats() {
  const project = $("project").value || "payments-service";
  try {
    const s = await api(`/api/stats?project=${encodeURIComponent(project)}`);
    $("reviewCount").textContent = s.reviews;
    $("feedbackCount").textContent = s.feedback_events;
    $("memoryHits").textContent = s.memory_hits;
  } catch {}
}

async function memory() {
  const project = $("project").value || "payments-service";
  try {
    const q = "What coding standards, architectural decisions, rejected suggestions, and review feedback does this team remember?";
    const data = await api(`/api/memory?project=${encodeURIComponent(project)}&q=${encodeURIComponent(q)}`);
    const list = $("memoryList");
    if (!data.memories.length) {
      list.innerHTML = `<div class="empty">No matching memories yet. Seed the demo or submit feedback.</div>`;
      return;
    }
    list.innerHTML = data.memories.map(m => `
      <div class="memory">
        <div class="type">${esc(m.type || "memory")} ${m.context ? "· " + esc(m.context) : ""}</div>
        <p>${esc(m.text)}</p>
      </div>
    `).join("");
  } catch (e) {
    $("memoryList").innerHTML = `<div class="empty">${esc(e.message)}</div>`;
  }
}

function renderResult(data) {
  const r = data.result;
  const findings = (r.findings || []).map(f => `
    <article class="finding">
      <div class="finding-top">
        <div class="finding-title">${esc(f.id)} · ${esc(f.title)}</div>
        <span class="badge ${esc(f.severity)}">${esc(f.severity)}</span>
      </div>
      <p>${esc(f.explanation)}</p>
      <div class="suggestion"><b>Suggested action:</b> ${esc(f.suggestion)}</div>
      <div class="basis">${esc(f.basis)}${f.line ? " · line " + esc(f.line) : ""}</div>
      <div class="feedback">
        <button onclick="sendFeedback(${data.review_id}, '${esc(f.id)}', 'accepted')">✓ Accept</button>
        <button onclick="sendFeedback(${data.review_id}, '${esc(f.id)}', 'rejected')">× Reject</button>
        <button onclick="sendFeedback(${data.review_id}, '${esc(f.id)}', 'corrected')">↺ Correct</button>
      </div>
    </article>
  `).join("");

  $("resultPanel").innerHTML = `
    <div class="result-head">
      <div>
        <div class="eyebrow">MEMORY-AWARE REVIEW #${data.review_id}</div>
        <h2>${esc(r.summary)}</h2>
        <div class="verdict ${esc(r.verdict)}">${esc(r.verdict.replaceAll("_", " "))}</div>
      </div>
      <div class="score"><strong>${esc(r.score)}</strong><span>/ 100</span></div>
    </div>
    <div class="findings">${findings}</div>
    <div class="learning">
      <h3>WHY THIS REVIEW IS DIFFERENT</h3>
      <ul>
        ${(r.learned_signals || []).map(x => `<li>${esc(x)}</li>`).join("") || "<li>No durable team signal was retrieved.</li>"}
      </ul>
      <h3 style="margin-top:12px">NEXT REVIEW FOCUS</h3>
      <ul>
        ${(r.next_review_focus || []).map(x => `<li>${esc(x)}</li>`).join("")}
      </ul>
    </div>
  `;
  memory();
  history();
  stats();
}

async function review() {
  const project = $("project").value.trim() || "payments-service";
  const language = $("language").value;
  const prUrl = $("prUrl").value.trim();
  const diff = $("diff").value.trim();

  if (!prUrl && !diff) {
    $("inputStatus").textContent = "Paste a diff or provide a GitHub PR URL.";
    return;
  }

  $("reviewBtn").disabled = true;
  $("reviewBtn").textContent = "Reviewing with memory…";
  $("inputStatus").textContent = "Recalling team knowledge before analysis.";

  try {
    const data = await api("/api/reviews", {
      method: "POST",
      body: JSON.stringify({
        project,
        reviewer: "demo-user",
        language,
        pr_url: prUrl,
        diff
      })
    });
    $("inputStatus").textContent = `Review complete · ${data.memories.length} memories recalled · Hindsight retained the outcome.`;
    renderResult(data);
  } catch (e) {
    $("inputStatus").textContent = e.message;
  } finally {
    $("reviewBtn").disabled = false;
    $("reviewBtn").innerHTML = 'Run memory-aware review <span>→</span>';
  }
}

async function seed() {
  const project = $("project").value.trim() || "payments-service";
  $("seedBtn").disabled = true;
  $("seedBtn").textContent = "Seeding…";
  try {
    const data = await api(`/api/demo/seed?project=${encodeURIComponent(project)}`, { method: "POST" });
    $("inputStatus").textContent = `Seeded ${data.seeded} durable team memories.`;
    await memory();
  } catch (e) {
    $("inputStatus").textContent = e.message;
  } finally {
    $("seedBtn").disabled = false;
    $("seedBtn").textContent = "Seed team memory";
  }
}

async function sendFeedback(reviewId, findingId, decision) {
  const comment = prompt(`Optional comment for ${decision}:`, "") ?? "";
  try {
    await api(`/api/reviews/${reviewId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ finding_id: findingId, decision, comment })
    });
    $("inputStatus").textContent = `Feedback "${decision}" retained as team memory.`;
    await Promise.all([memory(), stats()]);
  } catch (e) {
    $("inputStatus").textContent = e.message;
  }
}

async function history() {
  const project = $("project").value || "payments-service";
  try {
    const data = await api(`/api/reviews?project=${encodeURIComponent(project)}`);
    if (!data.length) {
      $("historyList").innerHTML = `<div class="empty">No reviews yet.</div>`;
      return;
    }
    $("historyList").innerHTML = data.map(r => `
      <div class="history-row">
        <span class="date">${esc(new Date(r.created_at).toLocaleString())}</span>
        <span>${esc(r.result.summary)}</span>
        <span class="memory">${esc(r.memory_used)} memories</span>
        <strong class="score">${esc(r.result.score)}</strong>
      </div>
    `).join("");
  } catch {}
}

$("reviewBtn").addEventListener("click", review);
$("seedBtn").addEventListener("click", seed);
$("sampleBtn").addEventListener("click", () => {
  $("diff").value = demoDiff;
  $("prUrl").value = "";
  $("inputStatus").textContent = "Demo change loaded.";
});
$("refreshMemory").addEventListener("click", memory);
$("refreshHistory").addEventListener("click", history);
$("project").addEventListener("change", () => { memory(); stats(); history(); });

window.sendFeedback = sendFeedback;

health();
memory();
stats();
history();

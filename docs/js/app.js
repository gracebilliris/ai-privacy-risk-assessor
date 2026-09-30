(function () {
  "use strict";

  const state = {
    risks: [],
    crossReferences: [],
  };

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatPct(value) {
    return Number(value).toFixed(2);
  }

  function groupRisksByCategory(risks) {
    const grouped = [];
    const byCategory = new Map();

    for (const risk of risks) {
      if (!byCategory.has(risk.category)) {
        const bucket = { category: risk.category, risks: [] };
        byCategory.set(risk.category, bucket);
        grouped.push(bucket);
      }
      byCategory.get(risk.category).risks.push(risk);
    }

    return grouped;
  }

  function buildRiskCard(risk) {
    const noteMarkup = risk.note
      ? `<p class="risk-note"><strong>Note:</strong> ${escapeHtml(risk.note)}</p>`
      : "";
    const tagMarkup = risk.category_tag
      ? `<span class="meta-pill">Tag ${escapeHtml(risk.category_tag)}</span>`
      : "";

    return `
      <article class="risk-card">
        <div class="risk-card-header">
          <div>
            <h3>${escapeHtml(risk.id)} — ${escapeHtml(risk.name)}</h3>
            <p class="risk-meta">
              Source paper ${escapeHtml(risk.source_paper)} · Frequency ${formatPct(risk.frequency_pct)}%
            </p>
          </div>
          ${tagMarkup}
        </div>
        <p class="risk-definition">${escapeHtml(risk.definition).trim()}</p>
        ${noteMarkup}
        <label class="field-label" for="rating__${escapeHtml(risk.id)}">Rating</label>
        <select id="rating__${escapeHtml(risk.id)}" name="rating__${escapeHtml(risk.id)}">
          <option value="" selected>— Not rated —</option>
          <option value="present">Present</option>
          <option value="not_present">Not present</option>
          <option value="not_applicable">Not applicable</option>
          <option value="unknown">Unknown</option>
        </select>
        <details class="citation-block">
          <summary>Source citation</summary>
          <p>
            <a href="#ref-paper-${escapeHtml(risk.source_paper.toLowerCase())}" title="${escapeHtml(risk.source_citation)}">Source citation*</a>
            — see References below.
          </p>
        </details>
      </article>
    `;
  }

  function renderForm(risks) {
    const container = document.getElementById("assessment-form-sections");
    container.innerHTML = groupRisksByCategory(risks)
      .map(
        (group) => `
          <section class="panel">
            <div class="section-heading">
              <div>
                <p class="eyebrow">Category</p>
                <h2>${escapeHtml(group.category)}</h2>
              </div>
              <span class="category-count">${group.risks.length} risks</span>
            </div>
            <div class="risk-grid">
              ${group.risks.map(buildRiskCard).join("")}
            </div>
          </section>
        `
      )
      .join("");
  }

  function buildRequest() {
    const systemNameInput = document.getElementById("system-name");
    const systemName = systemNameInput.value.trim() || "Unnamed System";
    const ratings = [];

    for (const risk of state.risks) {
      const select = document.getElementById(`rating__${risk.id}`);
      if (!select || !select.value) {
        continue;
      }
      ratings.push({
        risk_id: risk.id,
        rating: select.value,
      });
    }

    return { system_name: systemName, ratings };
  }

  function buildSummary(result) {
    const lines = [
      "Summary",
      `System: ${result.system_name}`,
      `Overall score: ${formatPct(result.overall_score_pct)}%`,
      "",
      "Category scores",
      ...result.category_scores.map(
        (score) =>
          `- ${score.category}: ${score.present_risks}/${score.applicable_risks} present (${formatPct(score.score_pct)}%)`
      ),
      "",
      "Flagged high-risk items",
    ];

    if (result.flagged_high_risk.length === 0) {
      lines.push("- None");
    } else {
      for (const flagged of result.flagged_high_risk) {
        lines.push(
          `- ${flagged.risk.id} | ${flagged.risk.name} | ${flagged.risk.source_paper} | ${formatPct(flagged.risk.frequency_pct)}%`
        );
      }
    }

    lines.push("", `Unrated risks: ${result.unrated_risks.length}`);
    return lines.join("\n");
  }

  function buildFlaggedMarkup(result) {
    if (result.flagged_high_risk.length === 0) {
      return "<p>No high-risk items were flagged in this assessment.</p>";
    }

    return result.flagged_high_risk
      .map((flagged) => {
        const crossRefs = flagged.related_cross_references.length
          ? `
            <div class="cross-reference-block">
              <strong>Related cross references</strong>
              <ul class="plain-list">
                ${flagged.related_cross_references
                  .map(
                    (ref) => `
                      <li>
                        <strong>${escapeHtml(ref.a_risk)} ↔ ${escapeHtml(ref.b_risk)}</strong>
                        (${escapeHtml(ref.confidence)}) — ${escapeHtml(ref.evidence_quote).trim()}
                      </li>
                    `
                  )
                  .join("")}
              </ul>
            </div>
          `
          : '<p class="muted">No mapped cross references.</p>';

        return `
          <article class="result-card">
            <div class="result-card-header">
              <div>
                <h3>${escapeHtml(flagged.risk.id)} — ${escapeHtml(flagged.risk.name)}</h3>
                <p class="risk-meta">
                  ${escapeHtml(flagged.risk.category)} · Source paper ${escapeHtml(flagged.risk.source_paper)} · Frequency ${formatPct(flagged.risk.frequency_pct)}%
                </p>
              </div>
              <span class="status-badge">High risk</span>
            </div>
            <p>${escapeHtml(flagged.risk.definition).trim()}</p>
            ${crossRefs}
          </article>
        `;
      })
      .join("");
  }

  function buildRecommendationsMarkup(result) {
    if (result.recommendations.length === 0) {
      return "<p>No additional recommendations were returned.</p>";
    }

    return `
      <ul class="plain-list">
        ${result.recommendations
          .map((item) => `<li>${escapeHtml(item)}</li>`)
          .join("")}
      </ul>
    `;
  }

  function buildUnratedMarkup(result) {
    if (result.unrated_risks.length === 0) {
      return "<p>All taxonomy risks were included in the submitted assessment.</p>";
    }

    return `
      <p class="muted">${result.unrated_risks.length} risks were left unrated.</p>
      <ul class="plain-list plain-list-columns">
        ${result.unrated_risks.map((riskId) => `<li>${escapeHtml(riskId)}</li>`).join("")}
      </ul>
    `;
  }

  function renderResult(result) {
    const resultsPanel = document.getElementById("results");
    document.getElementById("summary-output").textContent = buildSummary(result);
    document.getElementById("overall-score").textContent = `${formatPct(result.overall_score_pct)}%`;
    document.getElementById("flagged-count").textContent = String(result.flagged_high_risk.length);
    document.getElementById("unrated-count").textContent = String(result.unrated_risks.length);

    document.getElementById("category-score-body").innerHTML = result.category_scores
      .map(
        (score) => `
          <tr>
            <td>${escapeHtml(score.category)}</td>
            <td>${score.present_risks}</td>
            <td>${score.applicable_risks}</td>
            <td>${formatPct(score.score_pct)}%</td>
          </tr>
        `
      )
      .join("");

    document.getElementById("flagged-items").innerHTML = buildFlaggedMarkup(result);
    document.getElementById("recommendations").innerHTML = buildRecommendationsMarkup(result);
    document.getElementById("unrated-risks").innerHTML = buildUnratedMarkup(result);

    resultsPanel.hidden = false;
    resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showError(message) {
    const errorBox = document.getElementById("ui-error");
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function hideError() {
    const errorBox = document.getElementById("ui-error");
    errorBox.hidden = true;
    errorBox.textContent = "";
  }

  async function loadData() {
    const [risksResponse, crossRefsResponse] = await Promise.all([
      fetch("./data/risks.json"),
      fetch("./data/cross_references.json"),
    ]);

    if (!risksResponse.ok || !crossRefsResponse.ok) {
      throw new Error("Unable to load the local taxonomy assets for the demo.");
    }

    const [risks, crossReferences] = await Promise.all([
      risksResponse.json(),
      crossRefsResponse.json(),
    ]);

    state.risks = risks;
    state.crossReferences = crossReferences;
    renderForm(risks);
  }

  async function init() {
    const form = document.getElementById("assessment-form");

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      hideError();

      try {
        const request = buildRequest();
        const result = window.CapraScoring.assess(
          request,
          state.risks,
          state.crossReferences
        );
        renderResult(result);
      } catch (error) {
        showError(error instanceof Error ? error.message : "Assessment failed.");
      }
    });

    try {
      await loadData();
    } catch (error) {
      showError(error instanceof Error ? error.message : "Unable to load demo data.");
    }
  }

  window.addEventListener("DOMContentLoaded", init);
})();

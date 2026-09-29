(function (globalScope) {
  "use strict";

  const RISK_RATINGS = {
    PRESENT: "present",
    NOT_PRESENT: "not_present",
    NOT_APPLICABLE: "not_applicable",
    UNKNOWN: "unknown",
  };

  function cloneRisk(risk) {
    return {
      id: risk.id,
      name: risk.name,
      category: risk.category,
      source_paper: risk.source_paper,
      source_citation: risk.source_citation,
      frequency_count: risk.frequency_count,
      frequency_pct: risk.frequency_pct,
      definition: risk.definition,
      category_tag: risk.category_tag ?? null,
      note: risk.note ?? null,
    };
  }

  function cloneCrossReference(crossRef) {
    return {
      a_risk: crossRef.a_risk,
      b_risk: crossRef.b_risk,
      confidence: crossRef.confidence,
      evidence_quote: crossRef.evidence_quote,
    };
  }

  function _round_pct(numerator, denominator) {
    if (denominator === 0) {
      return 0.0;
    }

    const scaledNumerator = numerator * 10000;
    const quotient = Math.floor(scaledNumerator / denominator);
    const remainder = scaledNumerator % denominator;
    const doubledRemainder = remainder * 2;

    if (doubledRemainder < denominator) {
      return quotient / 100;
    }
    if (doubledRemainder > denominator) {
      return (quotient + 1) / 100;
    }
    return (quotient % 2 === 0 ? quotient : quotient + 1) / 100;
  }

  function _top_tertile_thresholds(risks) {
    const grouped = {};
    for (const risk of risks) {
      if (!grouped[risk.source_paper]) {
        grouped[risk.source_paper] = [];
      }
      grouped[risk.source_paper].push(risk.frequency_pct);
    }

    const thresholds = {};
    for (const [sourcePaper, values] of Object.entries(grouped)) {
      const ordered = [...values].sort((a, b) => b - a);
      const topCount = Math.max(1, Math.ceil(ordered.length / 3));
      thresholds[sourcePaper] = ordered[topCount - 1];
    }
    return thresholds;
  }

  function _build_recommendation(risk) {
    const definition = String(risk.definition).trim().split(/\s+/).join(" ");
    return `Prioritise controls for ${risk.id} (${risk.name}): ${definition}`;
  }

  function assess(request, risks, crossRefs) {
    const riskById = {};
    for (const risk of risks) {
      riskById[risk.id] = risk;
    }

    const seenIds = new Set();
    const ratingsById = {};
    const requestRatings = Array.isArray(request && request.ratings) ? request.ratings : [];

    for (const entry of requestRatings) {
      if (!riskById[entry.risk_id]) {
        throw new Error(`Unknown risk id: ${entry.risk_id}`);
      }
      if (seenIds.has(entry.risk_id)) {
        throw new Error(`Duplicate rating for risk id: ${entry.risk_id}`);
      }
      seenIds.add(entry.risk_id);
      ratingsById[entry.risk_id] = entry.rating;
    }

    const categoryOrder = [];
    const categoryCounts = {};
    for (const risk of risks) {
      if (!categoryCounts[risk.category]) {
        categoryCounts[risk.category] = { applicable: 0, present: 0 };
        categoryOrder.push(risk.category);
      }

      const rating = ratingsById[risk.id];
      if (
        rating === RISK_RATINGS.PRESENT ||
        rating === RISK_RATINGS.NOT_PRESENT
      ) {
        categoryCounts[risk.category].applicable += 1;
        if (rating === RISK_RATINGS.PRESENT) {
          categoryCounts[risk.category].present += 1;
        }
      }
    }

    const categoryScores = categoryOrder.map((category) => {
      const counts = categoryCounts[category];
      return {
        category,
        applicable_risks: counts.applicable,
        present_risks: counts.present,
        score_pct: _round_pct(counts.present, counts.applicable),
      };
    });

    const totalApplicable = categoryScores.reduce(
      (sum, score) => sum + score.applicable_risks,
      0
    );
    const totalPresent = categoryScores.reduce(
      (sum, score) => sum + score.present_risks,
      0
    );
    const thresholds = _top_tertile_thresholds(risks);

    const flaggedHighRisk = [];
    const recommendations = [];
    for (const risk of risks) {
      const rating = ratingsById[risk.id];
      if (rating !== RISK_RATINGS.PRESENT) {
        continue;
      }
      const threshold = thresholds[risk.source_paper];
      if (risk.frequency_pct < threshold) {
        continue;
      }

      const relatedCrossReferences = crossRefs
        .filter((crossRef) => crossRef.a_risk === risk.id || crossRef.b_risk === risk.id)
        .map(cloneCrossReference);

      flaggedHighRisk.push({
        risk: cloneRisk(risk),
        rating,
        related_cross_references: relatedCrossReferences,
      });
      recommendations.push(_build_recommendation(risk));
    }

    const unratedRisks = risks
      .filter((risk) => !(risk.id in ratingsById))
      .map((risk) => risk.id);

    return {
      system_name: request.system_name,
      overall_score_pct: _round_pct(totalPresent, totalApplicable),
      category_scores: categoryScores,
      flagged_high_risk: flaggedHighRisk,
      unrated_risks: unratedRisks,
      recommendations,
    };
  }

  const api = {
    RISK_RATINGS,
    _round_pct,
    _top_tertile_thresholds,
    assess,
  };

  globalScope.CapraScoring = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : window);

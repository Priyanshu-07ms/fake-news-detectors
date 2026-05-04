import React from "react";
import Charts from "./Charts";

const labelMeta = {
  fake: { text: "Likely Misleading", cls: "pill pill-fake" },
  real: { text: "Likely Reliable", cls: "pill pill-real" },
  uncertain: { text: "Needs Verification", cls: "pill pill-uncertain" },
};

const modelMeta = {
  logreg: "⚡ Logistic Regression",
  nb: "🪶 Naive Bayes",
  svm: "⚖ Support Vector Machine",
  bert: "🧠 DistilBERT (Deep Learning)",
};

const truncate = (t, max = 140) =>
  !t ? "" : t.length <= max ? t : t.slice(0, max) + "…";

function PredictionCard({
  loading,
  result,
  history,
  feedbackStatus,
  onFeedback,
}) {
  const labelBadge = (label) => {
    if (!label) return null;
    const meta = labelMeta[label] || labelMeta.uncertain;
    return <span className={meta.cls}>{meta.text}</span>;
  };

  const confidenceLevel = (c = 0) => {
    if (c >= 85) return { text: "High Confidence", color: "#22c55e" };
    if (c >= 65) return { text: "Moderate Confidence", color: "#eab308" };
    return { text: "Low Confidence", color: "#f97373" };
  };

  const confidenceBar = (c = 0) => ({
    width: `${c}%`,
    background:
      c >= 85 ? "#22c55e" : c >= 65 ? "#eab308" : "#f97373",
  });

  // =========================
  // LOADING
  // =========================
  if (loading) {
    return (
      <>
        <div className="panel-header">
          <h2>Analysis Result</h2>
        </div>
        <div className="loading-card">
          <div className="spinner-big" />
          <p>Analyzing content using AI models...</p>
        </div>
      </>
    );
  }

  // =========================
  // EMPTY
  // =========================
  if (!result) {
    return (
      <>
        <div className="panel-header">
          <h2>Analysis Result</h2>
        </div>
        <p className="placeholder">
          Paste content or a link and click <strong>Analyze Content</strong>.
        </p>

        {history.length > 0 && (
          <HistoryBlock history={history} labelBadge={labelBadge} />
        )}
      </>
    );
  }

  // =========================
  // 🔥 MULTI MODEL MODE
  // =========================
  if (result.results) {
    return (
      <>
        <div className="panel-header">
          <h2>Model Comparison</h2>
        </div>

        <div className="compare-grid">
          {Object.entries(result.results).map(([model, res]) => {
            const conf = confidenceLevel(res.confidence);

            return (
              <div key={model} className="compare-card">
                <h3>{modelMeta[model] || model}</h3>

                {labelBadge(res.label)}

                <p>
                  <strong>{res.confidence?.toFixed(1)}%</strong>
                </p>

                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={confidenceBar(res.confidence)}
                  />
                </div>

                <p style={{ color: conf.color }}>
                  {conf.text}
                </p>
              </div>
            );
          })}
        </div>

        <div className="prob-card">
          <Charts compareData={result.results} />
        </div>
      </>
    );
  }

  // =========================
  // 🔥 SINGLE MODEL MODE
  // =========================
  const conf = confidenceLevel(result.confidence);

  return (
    <>
      <div className="panel-header">
        <h2>Analysis Result</h2>
      </div>

      <div className="summary-card">
        <div className="summary-top">
          {labelBadge(result.label)}

          <span className="summary-value">
            {result.confidence?.toFixed(1)}%
          </span>
        </div>

        <div className="confidence-bar">
          <div
            className="confidence-fill"
            style={confidenceBar(result.confidence)}
          />
        </div>

        <div style={{ color: conf.color, marginTop: "6px" }}>
          {conf.text}
        </div>

        <div className="summary-extra">
          ⚙ {modelMeta[result.model] || result.model}
        </div>

        {result.message && (
          <div className="summary-extra">💡 {result.message}</div>
        )}
      </div>

      <div className="prob-card">
        <Charts
          fake={result.prob_fake || 0}
          real={result.prob_real || 0}
        />
      </div>

      {/* 🔥 IMPROVED FEEDBACK */}
      <div className="feedback-card">
        <p className="feedback-title">
          Was this analysis accurate?
        </p>

        <div className="feedback-buttons">
          <button
            className="btn btn-chip"
            onClick={() => onFeedback("correct")}
          >
            👍 Yes
          </button>

          <button
            className="btn btn-chip"
            onClick={() => onFeedback("incorrect")}
          >
            👎 Needs correction
          </button>
        </div>

        {feedbackStatus && (
          <p className="feedback-status">{feedbackStatus}</p>
        )}
      </div>

      {history.length > 0 && (
        <HistoryBlock history={history} labelBadge={labelBadge} />
      )}
    </>
  );
}

function HistoryBlock({ history, labelBadge }) {
  return (
    <div className="history-card">
      <div className="history-header">
        <span>Recent Analyses</span>
      </div>

      {history.map((h) => (
        <div key={h.id + h.createdAt} className="history-item">
          {labelBadge(h.label)}
          <p>{truncate(h.text)}</p>
          <small>⚙ {h.model}</small>
        </div>
      ))}
    </div>
  );
}

export default PredictionCard;
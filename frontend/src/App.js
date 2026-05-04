// src/App.js
import React, { useState } from "react";
import axios from "axios";
import "./App.css";

import PredictionCard from "./components/PredictionCard";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [model, setModel] = useState("logreg");
  const [compareMode, setCompareMode] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");

  const modelNameMap = {
    logreg: "Logistic Regression",
    nb: "Naive Bayes",
    svm: "SVM",
    bert: "DistilBERT",
  };

  // =========================
  // SINGLE MODEL
  // =========================
  const handlePredict = async () => {
    setErrorMsg("");
    setFeedbackStatus("");

    const trimmed = text.trim();
    if (!trimmed) {
      setErrorMsg("Please paste content to analyze.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const resp = await axios.post(`${API_BASE}/predict`, {
        text: trimmed,
        model: model,
      });

      const data = resp.data;

      setResult({ ...data, model });

      setHistory((prev) => [
        {
          id: data.id,
          label: data.label,
          confidence: data.confidence,
          text: trimmed,
          model: model,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ].slice(0, 6));

    } catch (err) {
      setErrorMsg(err.response?.data?.message || "Backend error.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // COMPARE MODE
  // =========================
  const handleCompare = async () => {
    setErrorMsg("");
    setFeedbackStatus("");

    const trimmed = text.trim();
    if (!trimmed) {
      setErrorMsg("Please paste content to analyze.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const resp = await axios.post(`${API_BASE}/predict-all`, {
        text: trimmed,
      });

      setResult({ results: resp.data.results });

    } catch {
      setErrorMsg("Model comparison failed.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // URL ANALYSIS
  // =========================
  const handleUrlPredict = async () => {
    setErrorMsg("");
    setFeedbackStatus("");

    if (!url.trim()) {
      setErrorMsg("Please enter a valid article link.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const resp = await axios.post(`${API_BASE}/predict-url`, {
        url: url.trim(),
      });

      setResult({ ...resp.data, model });

    } catch {
      setErrorMsg("Could not analyze the URL.");
    } finally {
      setLoading(false);
    }
  };

  // =========================
  // FEEDBACK
  // =========================
  const handleFeedback = async (userFeedback) => {
    if (!result?.id) return;

    try {
      setFeedbackStatus("");

      await axios.post(`${API_BASE}/feedback`, {
        prediction_id: result.id,
        user_feedback: userFeedback,
        correct_label: null,
      });

      setFeedbackStatus("Thanks! Feedback recorded 🙌");
    } catch {
      setFeedbackStatus("Failed to save feedback.");
    }
  };

  const resetAll = () => {
    setText("");
    setUrl("");
    setResult(null);
    setErrorMsg("");
    setFeedbackStatus("");
  };

  return (
    <div className="app-root">
      <div className="app-shell">

        {/* HEADER */}
        <header className="app-header">
          <h1>TruthLens AI</h1>
          <p>AI-powered News Credibility Analyzer</p>
        </header>

        <main className="app-main">

          {/* INPUT PANEL */}
          <section className="panel panel-input">

            <div className="panel-header">
              <h2>Analyze Content</h2>
            </div>

            {/* MODEL SECTION */}
            <div className="model-section">

              <div className="model-title">
                {compareMode
                  ? "Comparison Mode"
                  : `Selected Model: ${modelNameMap[model]}`}
              </div>

              <div className="model-toggle">
                <button
                  className={`btn ${!compareMode ? "btn-primary" : "btn-ghost"}`}
                  onClick={() => setCompareMode(false)}
                >
                  🔹 Single Analysis
                </button>

                <button
                  className={`btn ${compareMode ? "btn-primary" : "btn-ghost"}`}
                  onClick={() => setCompareMode(true)}
                >
                  ⚡ Compare Models
                </button>
              </div>

            </div>

            {/* MODEL SELECT */}
            {!compareMode && (
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                <option value="logreg">Logistic Regression</option>
                <option value="nb">Naive Bayes</option>
                <option value="svm">SVM</option>
                <option value="bert">DistilBERT</option>
              </select>
            )}

            {/* URL INPUT */}
            <input
              type="text"
              placeholder="Paste article link (optional)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />

            {/* TEXT INPUT */}
            <textarea
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste news content here..."
            />

            {/* ACTIONS */}
            <div className="actions-row">

              {!compareMode ? (
                <button
                  className="btn btn-primary"
                  onClick={handlePredict}
                  disabled={loading}
                >
                  Analyze Content
                </button>
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={handleCompare}
                  disabled={loading}
                >
                  Compare Models
                </button>
              )}

              <button
                className="btn btn-chip"
                onClick={handleUrlPredict}
                disabled={loading}
              >
                Analyze from URL
              </button>

              <button
                className="btn btn-ghost"
                onClick={resetAll}
                disabled={loading}
              >
                Reset
              </button>
            </div>

            {errorMsg && <div className="alert alert-error">{errorMsg}</div>}

          </section>

          {/* OUTPUT */}
          <section className="panel panel-output">
            <PredictionCard
              loading={loading}
              result={result}
              history={history}
              feedbackStatus={feedbackStatus}
              onFeedback={handleFeedback}
            />
          </section>

        </main>

        {/* FOOTER */}
        <footer className="app-footer">
          Powered by Multi-Model AI • Logistic • NB • SVM • BERT
        </footer>

      </div>
    </div>
  );
}

export default App;
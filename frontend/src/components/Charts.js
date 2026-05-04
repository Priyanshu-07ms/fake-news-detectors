// src/components/Charts.js
import React from "react";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from "chart.js";
import { Pie, Bar } from "react-chartjs-2";

// Register ALL required components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
);

// =============================
// 🔥 MAIN COMPONENT
// =============================
function Charts({ fake, real, compareData }) {
  // 🔥 CASE 1: MODEL COMPARISON MODE
  if (compareData) {
    const labels = Object.keys(compareData);

    const data = {
      labels: labels.map((m) => m.toUpperCase()),
      datasets: [
        {
          label: "Confidence (%)",
          data: labels.map((m) => compareData[m].confidence),
          backgroundColor: [
            "#3b82f6", // blue
            "#22c55e", // green
            "#eab308", // yellow
            "#ec4899", // pink
          ],
          borderRadius: 8,
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#e5e7eb" },
        },
        y: {
          ticks: { color: "#e5e7eb" },
          beginAtZero: true,
          max: 100,
        },
      },
    };

    return (
      <div className="chart-wrapper">
        <Bar data={data} options={options} />
      </div>
    );
  }

  // =============================
  // 🔥 CASE 2: NORMAL PIE CHART
  // =============================
  const data = {
    labels: ["Fake", "Real"],
    datasets: [
      {
        data: [fake, real],
        backgroundColor: ["#fb7185", "#4ade80"],
        borderColor: ["#be123c", "#166534"],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    plugins: {
      legend: {
        labels: {
          color: "#e5e7eb",
          font: { size: 11 },
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(1)}%`,
        },
      },
    },
  };

  return (
    <div className="chart-wrapper">
      <Pie data={data} options={options} />
    </div>
  );
}

export default Charts;
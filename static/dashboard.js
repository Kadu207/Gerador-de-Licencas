(function () {
  const dataEl = document.getElementById("dashboard-data");
  if (!dataEl || typeof Chart === "undefined") return;

  const charts = JSON.parse(dataEl.textContent);
  const tooltipDefaults = {
    enabled: true,
    backgroundColor: "rgba(50, 49, 48, 0.95)",
    titleFont: { size: 13, weight: "600" },
    bodyFont: { size: 12 },
    padding: 12,
    cornerRadius: 4,
    displayColors: true,
  };

  const currencyTooltip = {
    callbacks: {
      label(ctx) {
        const v = ctx.parsed.y ?? ctx.parsed;
        return ` ${ctx.dataset.label || ctx.label}: R$ ${Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
      },
    },
  };

  const countTooltip = {
    callbacks: {
      label(ctx) {
        const v = ctx.parsed.y ?? ctx.parsed ?? ctx.raw;
        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
        const pct = total ? ((v / total) * 100).toFixed(1) : 0;
        return ` ${ctx.label}: ${v} (${pct}%)`;
      },
    },
  };

  new Chart(document.getElementById("chartProducts"), {
    type: "doughnut",
    data: {
      labels: charts.licenses_by_product.labels,
      datasets: [{
        data: charts.licenses_by_product.values,
        backgroundColor: ["#0078d4", "#107c10", "#8764b8"],
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { tooltip: { ...tooltipDefaults, ...countTooltip }, legend: { position: "bottom" } },
    },
  });

  new Chart(document.getElementById("chartStatus"), {
    type: "pie",
    data: {
      labels: charts.status_distribution.labels,
      datasets: [{
        data: charts.status_distribution.values,
        backgroundColor: charts.status_distribution.colors,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { tooltip: { ...tooltipDefaults, ...countTooltip }, legend: { position: "bottom" } },
    },
  });

  new Chart(document.getElementById("chartRevenue"), {
    type: "bar",
    data: {
      labels: charts.revenue_by_month.labels,
      datasets: [{
        label: "Receita",
        data: charts.revenue_by_month.values,
        backgroundColor: "rgba(0, 120, 212, 0.75)",
        borderColor: "#0078d4",
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, ticks: { callback: (v) => "R$ " + v } } },
      plugins: { tooltip: { ...tooltipDefaults, ...currencyTooltip } },
    },
  });

  new Chart(document.getElementById("chartDelinquency"), {
    type: "bar",
    data: {
      labels: charts.delinquency_by_product.labels,
      datasets: [{
        label: "Inadimplentes",
        data: charts.delinquency_by_product.values,
        backgroundColor: "rgba(164, 38, 44, 0.75)",
        borderColor: "#a4262c",
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      plugins: {
        tooltip: {
          ...tooltipDefaults,
          callbacks: {
            label(ctx) {
              return ` ${ctx.label}: ${ctx.parsed.y} licença(s) inadimplente(s)`;
            },
          },
        },
      },
    },
  });

  new Chart(document.getElementById("chartPlans"), {
    type: "bar",
    data: {
      labels: charts.revenue_by_plan.labels,
      datasets: [{
        label: "Receita por plano",
        data: charts.revenue_by_plan.values,
        backgroundColor: ["#0078d4", "#ca5010", "#107c10"],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, ticks: { callback: (v) => "R$ " + v } } },
      plugins: { tooltip: { ...tooltipDefaults, ...currencyTooltip } },
    },
  });
})();

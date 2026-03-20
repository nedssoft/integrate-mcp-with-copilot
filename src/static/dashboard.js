document.addEventListener("DOMContentLoaded", () => {
  let allActivities = [];

  const activityFilter = document.getElementById("activity-filter");
  const utilizationFilter = document.getElementById("utilization-filter");
  const resetBtn = document.getElementById("reset-filters");

  // Fetch analytics data from API
  async function fetchAnalytics() {
    try {
      const response = await fetch("/analytics");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      allActivities = data.activities;

      // Populate summary cards
      document.getElementById("total-activities").textContent =
        data.total_activities;
      document.getElementById("total-enrolled").textContent =
        data.total_enrolled;
      document.getElementById("total-capacity").textContent =
        data.total_capacity;
      document.getElementById("overall-utilization").textContent =
        data.overall_utilization + "%";

      // Populate activity filter dropdown
      activityFilter.innerHTML = '<option value="">All Activities</option>';
      data.activities.forEach((a) => {
        const opt = document.createElement("option");
        opt.value = a.name;
        opt.textContent = a.name;
        activityFilter.appendChild(opt);
      });

      renderAll(allActivities);
    } catch (error) {
      showError("Failed to load analytics data. Please try again later.");
      console.error("Error fetching analytics:", error);
    }
  }

  // Apply current filters and re-render
  function applyFilters() {
    const selectedActivity = activityFilter.value;
    const selectedUtilization = utilizationFilter.value;

    let filtered = allActivities;

    if (selectedActivity) {
      filtered = filtered.filter((a) => a.name === selectedActivity);
    }

    if (selectedUtilization) {
      filtered = filtered.filter((a) => {
        const u = a.utilization;
        if (selectedUtilization === "low") return u < 50;
        if (selectedUtilization === "medium") return u >= 50 && u <= 80;
        if (selectedUtilization === "high") return u > 80 && u < 100;
        if (selectedUtilization === "full") return u >= 100;
        return true;
      });
    }

    renderAll(filtered);
  }

  // Render chart and table for a given list of activities
  function renderAll(activities) {
    renderChart(activities);
    renderTable(activities);
  }

  // Render horizontal bar chart
  function renderChart(activities) {
    const container = document.getElementById("chart-container");

    if (activities.length === 0) {
      container.innerHTML =
        '<p class="empty-state">No activities match the selected filters.</p>';
      return;
    }

    container.innerHTML = activities
      .map((a) => {
        const pct = Math.min(a.utilization, 100);
        const barClass =
          pct >= 100
            ? "bar-full"
            : pct >= 80
            ? "bar-high"
            : pct >= 50
            ? "bar-medium"
            : "bar-low";

        return `
        <div class="chart-row">
          <span class="chart-label" title="${a.name}">${a.name}</span>
          <div class="bar-track">
            <div class="bar-fill ${barClass}" style="width: ${pct}%"></div>
          </div>
          <span class="chart-pct">${a.utilization}%</span>
          <span class="chart-counts">${a.enrolled}/${a.capacity}</span>
        </div>`;
      })
      .join("");
  }

  // Render metrics table
  function renderTable(activities) {
    const tbody = document.getElementById("metrics-tbody");

    if (activities.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="empty-state">No activities match the selected filters.</td></tr>';
      return;
    }

    tbody.innerHTML = activities
      .map((a) => {
        const utilizationClass =
          a.utilization >= 100
            ? "util-full"
            : a.utilization >= 80
            ? "util-high"
            : a.utilization >= 50
            ? "util-medium"
            : "util-low";

        return `
        <tr>
          <td><strong>${escapeHtml(a.name)}</strong></td>
          <td class="schedule-cell">${escapeHtml(a.schedule)}</td>
          <td class="center">${a.enrolled}</td>
          <td class="center">${a.capacity}</td>
          <td class="center">${a.spots_left > 0 ? a.spots_left : '<span class="badge-full">Full</span>'}</td>
          <td class="center"><span class="util-badge ${utilizationClass}">${a.utilization}%</span></td>
          <td class="center">${a.waitlist > 0 ? a.waitlist : '<span class="no-waitlist">–</span>'}</td>
        </tr>`;
      })
      .join("");
  }

  // Show error state across all content areas
  function showError(message) {
    document.getElementById("chart-container").innerHTML =
      `<p class="error-state">${message}</p>`;
    document.getElementById("metrics-tbody").innerHTML =
      `<tr><td colspan="7" class="error-state">${message}</td></tr>`;
  }

  // Simple HTML escaping to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

  // Event listeners
  activityFilter.addEventListener("change", applyFilters);
  utilizationFilter.addEventListener("change", applyFilters);
  resetBtn.addEventListener("click", () => {
    activityFilter.value = "";
    utilizationFilter.value = "";
    applyFilters();
  });

  // Bootstrap the dashboard
  fetchAnalytics();
});

document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // ---------- Tab switching ----------
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.add("hidden"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.remove("hidden");
    });
  });

  // ---------- Helper: populate an <select> with activity names ----------
  function populateActivitySelect(selectEl, activities) {
    // Keep only the placeholder option
    while (selectEl.options.length > 1) selectEl.remove(1);
    Object.keys(activities).forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      selectEl.appendChild(opt);
    });
  }

  // ---------- Helper: show a message in a target div ----------
  function showMessage(div, text, type) {
    div.textContent = text;
    div.className = type;
    div.classList.remove("hidden");
    setTimeout(() => div.classList.add("hidden"), 5000);
  }

  // ---------- Fetch activities ----------
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitiesList.innerHTML = "";

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Populate the attendance-section dropdowns
      populateActivitySelect(document.getElementById("att-activity"), activities);
      populateActivitySelect(document.getElementById("summary-activity"), activities);

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // ---------- Unregister ----------
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");
      setTimeout(() => messageDiv.classList.add("hidden"), 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // ---------- Sign up ----------
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");
      setTimeout(() => messageDiv.classList.add("hidden"), 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // ---------- Mark / Edit Attendance ----------
  const attendanceForm = document.getElementById("attendance-form");
  const attendanceMessage = document.getElementById("attendance-message");

  async function submitAttendance(method) {
    const markedBy = document.getElementById("att-marked-by").value;
    const activity = document.getElementById("att-activity").value;
    const email = document.getElementById("att-email").value;
    const date = document.getElementById("att-date").value;
    const status = document.getElementById("att-status").value;

    if (!markedBy || !activity || !email || !date || !status) {
      showMessage(attendanceMessage, "Please fill in all fields.", "error");
      return;
    }

    const url =
      `/activities/${encodeURIComponent(activity)}/attendance` +
      `?email=${encodeURIComponent(email)}` +
      `&date=${encodeURIComponent(date)}` +
      `&status=${encodeURIComponent(status)}` +
      `&marked_by=${encodeURIComponent(markedBy)}`;

    try {
      const response = await fetch(url, { method });
      const result = await response.json();
      showMessage(
        attendanceMessage,
        result.message || result.detail || "An error occurred",
        response.ok ? "success" : "error"
      );
    } catch (error) {
      showMessage(attendanceMessage, "Failed to submit attendance.", "error");
      console.error("Error submitting attendance:", error);
    }
  }

  attendanceForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitAttendance("POST");
  });

  document.getElementById("edit-btn").addEventListener("click", () => {
    submitAttendance("PUT");
  });

  // ---------- Activity Attendance Summary ----------
  document.getElementById("load-summary-btn").addEventListener("click", async () => {
    const activity = document.getElementById("summary-activity").value;
    const date = document.getElementById("summary-date").value;
    const resultDiv = document.getElementById("summary-result");

    if (!activity) {
      resultDiv.innerHTML = "<p class='error'>Please select an activity.</p>";
      return;
    }

    let url = `/activities/${encodeURIComponent(activity)}/attendance`;
    if (date) url += `?date=${encodeURIComponent(date)}`;

    try {
      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        resultDiv.innerHTML = `<p class='error'>${data.detail || "Error loading summary."}</p>`;
        return;
      }

      if (date) {
        // Single-session view
        resultDiv.innerHTML = `
          <div class="attendance-summary">
            <h5>${activity} — ${date}</h5>
            <p>✅ Present (${data.present_count}): ${data.present.join(", ") || "none"}</p>
            <p>❌ Absent (${data.absent_count}): ${data.absent.join(", ") || "none"}</p>
          </div>`;
      } else {
        if (data.sessions.length === 0) {
          resultDiv.innerHTML = "<p><em>No attendance records found.</em></p>";
          return;
        }
        resultDiv.innerHTML = data.sessions
          .map(
            (s) => `
          <div class="attendance-summary">
            <h5>${s.date}</h5>
            <p>✅ Present (${s.present_count}): ${s.present.join(", ") || "none"}</p>
            <p>❌ Absent (${s.absent_count}): ${s.absent.join(", ") || "none"}</p>
          </div>`
          )
          .join("");
      }
    } catch (error) {
      resultDiv.innerHTML = "<p class='error'>Failed to load summary.</p>";
      console.error("Error loading summary:", error);
    }
  });

  // ---------- Student Attendance History ----------
  document.getElementById("load-student-btn").addEventListener("click", async () => {
    const email = document.getElementById("student-email").value;
    const resultDiv = document.getElementById("student-result");

    if (!email) {
      resultDiv.innerHTML = "<p class='error'>Please enter a student email.</p>";
      return;
    }

    try {
      const response = await fetch(`/students/${encodeURIComponent(email)}/attendance`);
      const data = await response.json();

      if (!response.ok) {
        resultDiv.innerHTML = `<p class='error'>${data.detail || "Error loading history."}</p>`;
        return;
      }

      if (data.total_sessions === 0) {
        resultDiv.innerHTML = "<p><em>No attendance records found for this student.</em></p>";
        return;
      }

      const pct =
        data.attendance_percentage !== null ? `${data.attendance_percentage}%` : "N/A";

      const rows = data.records
        .map(
          (r) =>
            `<tr>
              <td>${r.date}</td>
              <td>${r.activity}</td>
              <td class="${r.status === "present" ? "status-present" : "status-absent"}">${r.status}</td>
            </tr>`
        )
        .join("");

      resultDiv.innerHTML = `
        <div class="attendance-summary">
          <p><strong>Attendance rate:</strong> ${pct}
            (${data.present_count} present / ${data.total_sessions} sessions)</p>
          <table class="attendance-table">
            <thead><tr><th>Date</th><th>Activity</th><th>Status</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
    } catch (error) {
      resultDiv.innerHTML = "<p class='error'>Failed to load student history.</p>";
      console.error("Error loading student history:", error);
    }
  });

  // ---------- Initialize ----------
  fetchActivities();
});

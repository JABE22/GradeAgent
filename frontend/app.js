const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#notebooks");
const message = document.querySelector("#upload-message");
const list = document.querySelector("#submission-list");
const emptyState = document.querySelector("#empty-state");
const count = document.querySelector("#submission-count");
const clearButton = document.querySelector("#clear-submissions");
const submissions = [];

function addCell(row, value, className = "") {
  const cell = document.createElement("td");
  cell.textContent = value;
  if (className) cell.className = className;
  row.append(cell);
}

function render() {
  list.replaceChildren();
  submissions.forEach((submission) => {
    const row = document.createElement("tr");
    addCell(row, submission.filename, "filename");
    addCell(row, [submission.course, submission.workshop].filter(Boolean).join(" / ") || "—");
    addCell(row, submission.added);
    addCell(row, "100 / 100", "score");
    list.append(row);
  });
  count.textContent = String(submissions.length);
  emptyState.hidden = submissions.length > 0;
  clearButton.disabled = submissions.length === 0;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const selected = Array.from(fileInput.files || []);
  const notebooks = selected.filter((file) => file.name.toLowerCase().endsWith(".ipynb"));
  const skipped = selected.length - notebooks.length;

  if (notebooks.length === 0) {
    message.textContent = "Choose at least one .ipynb notebook to continue.";
    fileInput.value = "";
    return;
  }

  const added = new Date().toLocaleString();
  notebooks.forEach((file) => submissions.unshift({
    filename: file.name,
    course: form.elements.course.value.trim(),
    workshop: form.elements.workshop.value.trim(),
    added,
  }));
  render();
  message.textContent = `${notebooks.length} notebook${notebooks.length === 1 ? "" : "s"} added with a demo score of 100${skipped ? `; ${skipped} non-notebook file${skipped === 1 ? " was" : "s were"} skipped` : ""}.`;
  form.reset();
});

clearButton.addEventListener("click", () => {
  submissions.length = 0;
  render();
  message.textContent = "Session cleared. Files were not stored.";
});

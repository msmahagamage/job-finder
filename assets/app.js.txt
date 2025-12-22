async function load() {
  const res = await fetch("data/jobs.json?cachebust=" + Date.now());
  const data = await res.json();

  const listEl = document.getElementById("list");
  const metaEl = document.getElementById("meta");
  const qEl = document.getElementById("q");
  const sourceEl = document.getElementById("source");

  const sources = ["All", ...new Set(data.jobs.map(j => j.source))].sort();
  sourceEl.innerHTML = sources.map(s => `<option>${s}</option>`).join("");

  function render() {
    const q = (qEl.value || "").toLowerCase();
    const s = sourceEl.value;

    const filtered = data.jobs.filter(j => {
      const hay = `${j.title} ${j.company} ${j.location} ${j.summary}`.toLowerCase();
      const okQ = !q || hay.includes(q);
      const okS = (s === "All") || (j.source === s);
      return okQ && okS;
    });

    metaEl.textContent = `Last updated: ${data.updated_at} • Jobs: ${filtered.length}`;
    listEl.innerHTML = filtered.map(j => `
      <article class="card">
        <h3><a target="_blank" href="${j.url}">${j.title}</a></h3>
        <div class="row">
          <span><b>${j.company}</b></span>
          <span>${j.location || ""}</span>
          <span class="tag">${j.source}</span>
        </div>
        <p>${j.summary || ""}</p>
      </article>
    `).join("");
  }

  qEl.addEventListener("input", render);
  sourceEl.addEventListener("change", render);
  render();
}
load();

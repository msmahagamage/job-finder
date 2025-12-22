async function load() {
  const res = await fetch("data/jobs.json?cachebust=" + Date.now());
  const data = await res.json();

  const listEl = document.getElementById("list");
  const metaEl = document.getElementById("meta");
  const qEl = document.getElementById("q");
  const sourceEl = document.getElementById("source");

  // Build source dropdown
  const sources = ["All", ...new Set(data.jobs.map(j => j.source))].sort();
  sourceEl.innerHTML = sources.map(s => `<option value="${s}">${s}</option>`).join("");

  // ---- Job classification (your research areas) ----
  function classify(job) {
    const t = (job.title + " " + job.summary).toLowerCase();
    if (t.includes("traffic") || t.includes("transport")) return "Traffic";
    if (t.includes("evacuation")) return "Evacuation";
    if (t.includes("wildfire") || t.includes("fire")) return "Wildfire";
    if (t.includes("gis") || t.includes("geospatial")) return "GIS";
    return "Modeling";
  }

  // ---- Visa friendliness check ----
  function visaLabel(job) {
    const t = (job.title + " " + job.summary).toLowerCase();
    if (
      t.includes("u.s. citizen") ||
      t.includes("us citizen") ||
      t.includes("security clearance") ||
      t.includes("secret clearance") ||
      t.includes("top secret")
    ) {
      return " Restricted";
    }
    return "Visa-Friendly";
  }

  function render() {
    const q = (qEl.value || "").toLowerCase();
    const s = sourceEl.value;

    const filtered = data.jobs.filter(j => {
      const hay = `${j.title} ${j.company} ${j.location} ${j.summary}`.toLowerCase();
      const okQ = !q || hay.includes(q);
      const okS = (s === "All") || (j.source === s);
      return okQ && okS;
    });

    metaEl.textContent = `Last updated: ${data.updated_at} • Jobs shown: ${filtered.length}`;

    listEl.innerHTML = filtered.map(j => `
      <article class="card">
        <h3>
          <a target="_blank" href="${j.url}">${j.title}</a>
        </h3>

        <div class="row">
          <span><b>${j.company}</b></span>
          <span>${j.location || ""}</span>
        </div>

        <div class="row">
          <span class="tag">${j.source}</span>
          <span class="tag">${classify(j)}</span>
          <span class="tag">${visaLabel(j)}</span>
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

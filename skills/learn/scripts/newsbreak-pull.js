// Yeez NewsBreak pull. Run it with your browser tool's JavaScript runner inside a logged-in
// https://mp.newsbreak.com/home/content/post tab, after replacing SITE_LABEL with the buyer's site
// (e.g. example.com). It downloads two files to the computer's Downloads folder:
//   newsbreak-SITE_LABEL-YYYY-MM-DD.tsv        every article, all time: impressions, views, status, title
//   newsbreak-daily-SITE_LABEL-YYYY-MM-DD.tsv  the account's daily totals
// Then read window.__yeez for the result and fold the files with yeez_data.py ingest.
(async () => {
  const label = "SITE_LABEL";
  const day = new Date().toISOString().slice(0, 10);
  const clean = (v) => String(v ?? "").replace(/[\t\r\n]+/g, " ").trim();
  const save = (name, text) => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: "text/tab-separated-values" })); a.download = name; document.body.appendChild(a); a.click(); a.remove(); };
  try {
    const who = (document.body.innerText.match(/Welcome,\s*([^\n]+)/) || [])[1] || "";
    if (!who) { window.__yeez = { ok: false, error: "Not logged in. Open https://mp.newsbreak.com/home/content/post, log in, and run again." }; return; }
    const total = (await fetch("/api/post/media/post/count?queryString=&mode=", { credentials: "include" }).then((r) => r.json())).data || 0;
    const cols = ["date", "doc_id", "impression", "page_view", "in_app_page_view", "web_page_view", "like", "share", "comment", "status", "audit_status", "reason", "ctype", "isEvergreen", "media_id", "title"];
    const lines = [cols.join("\t")];
    for (let off = 0; off < 60000; off += 1000) {
      const d = (await fetch(`/api/post/media/post?offset=${off}&size=1000&queryString=&mode=`, { credentials: "include" }).then((r) => r.json())).data || [];
      for (const r of d) {
        const row = { ...r, impression: r.impression ?? (r.in_app_impression || 0) + (r.web_impression || 0), page_view: r.page_view ?? (r.in_app_page_view || 0) + (r.web_page_view || 0), status: r.state ?? r.status };
        lines.push(cols.map((c) => clean(row[c])).join("\t"));
      }
      if (d.length < 1000) break;
    }
    save(`newsbreak-${label}-${day}.tsv`, lines.join("\n"));
    let days = 0;
    try {
      const a = ((await fetch("/api/v1/stats/account/daily", { credentials: "include" }).then((r) => r.json())).data || {}).account_daily || [];
      const dc = ["date", "page_view", "impression", "in_app_page_view", "web_page_view", "follower"];
      save(`newsbreak-daily-${label}-${day}.tsv`, [dc.join("\t"), ...a.map((x) => dc.map((c) => clean(x[c])).join("\t"))].join("\n"));
      days = a.length;
    } catch (e) {}
    window.__yeez = { ok: true, account: who, articles: lines.length - 1, total_on_newsbreak: total, days, files: [`newsbreak-${label}-${day}.tsv`, days ? `newsbreak-daily-${label}-${day}.tsv` : null] };
  } catch (e) { window.__yeez = { ok: false, error: String((e && e.message) || e) }; }
})();

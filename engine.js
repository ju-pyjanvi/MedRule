/* MedRule engine, JavaScript port of engine.py (forward chaining + MYCIN certainty factors). */
(function (root) {
  const { SYMPTOMS, DISEASES, COMPOUND_RULES, TRIAGE_RULES, INTERMEDIATE_LABELS } = root.KB;
  const THRESHOLD = 0.2, TRIAGE_CUTOFF = 0.5;

  const label = f =>
    f.startsWith('dx:') ? f.slice(3) :
    f.startsWith('triage:') ? 'Triage ' + f.slice(7) :
    SYMPTOMS[f] ? SYMPTOMS[f].label : (INTERMEDIATE_LABELS[f] || f);

  const RULES = [];
  for (const [d, info] of Object.entries(DISEASES))
    for (const [s, cf] of Object.entries(info.symptoms))
      RULES.push({ id: 'R' + (RULES.length + 1), premises: [s], conclusion: 'dx:' + d, cf });
  for (const [p, c, cf] of [...COMPOUND_RULES, ...TRIAGE_RULES])
    RULES.push({ id: 'R' + (RULES.length + 1), premises: p, conclusion: c, cf });

  const combine = (a, b) => a + b * (1 - a);
  const ruleText = r => `IF ${r.premises.map(label).join(' AND ')} THEN ${label(r.conclusion)}`;

  function run(symptoms) {
    const wm = { ...symptoms }, fired = new Set(), trace = [];
    let cycle = 0;
    for (;;) {
      cycle++;
      const snap = { ...wm };
      const batch = RULES.filter(r => !fired.has(r.id) && r.premises.every(p => p in snap));
      if (!batch.length) break;
      for (const r of batch) {
        fired.add(r.id);
        const pc = {};
        r.premises.forEach(p => (pc[p] = snap[p]));
        const contrib = r.cf * Math.min(...Object.values(pc));
        const before = wm[r.conclusion];
        const after = before === undefined ? contrib : combine(before, contrib);
        wm[r.conclusion] = after;
        trace.push({ cycle, rule: r, pc, contrib, before, after });
      }
    }
    return { wm, trace, cycles: cycle - 1 };
  }

  const diagnoses = res =>
    Object.entries(res.wm).filter(([f, v]) => f.startsWith('dx:') && v >= THRESHOLD)
      .map(([f, v]) => [f.slice(3), v]).sort((a, b) => b[1] - a[1]);

  function triage(res) {
    for (const level of ['emergency', 'urgent']) {
      const cf = res.wm['triage:' + level] || 0;
      if (cf >= TRIAGE_CUTOFF) return { level, cf };
    }
    return { level: 'routine', cf: 0 };
  }

  function explain(res, disease) {
    const steps = res.trace.filter(s => s.rule.conclusion === 'dx:' + disease);
    const out = [];
    steps.forEach((s, i) => {
      const prem = Object.entries(s.pc).map(([p, v]) => `${label(p)} (${v.toFixed(2)})`).join(', ');
      out.push(`${i + 1}. ${s.rule.id}  ${ruleText(s.rule)}  [CF ${s.rule.cf.toFixed(2)}]`);
      out.push(`   evidence ${prem}`);
      out.push(`   ${s.rule.cf.toFixed(2)} x ${Math.min(...Object.values(s.pc)).toFixed(2)} = ${s.contrib.toFixed(3)}` +
        (s.before === undefined ? `   running ${s.after.toFixed(3)}`
          : `   combine ${s.before.toFixed(3)} + ${s.contrib.toFixed(3)} x (1 - ${s.before.toFixed(3)}) = ${s.after.toFixed(3)}`));
    });
    return out.join('\n');
  }

  /* ---------- text preprocessor: synonyms, spelling repair, negation, intensity ---------- */
  const NEG = new Set(['no', 'not', 'without', 'never', 'dont', "don't", 'denies', 'nothing']);
  const UP = new Set(['severe', 'very', 'extreme', 'terrible', 'intense', 'high', 'bad', 'worst', 'definitely']);
  const DOWN = new Set(['slight', 'slightly', 'mild', 'little', 'maybe', 'minor', 'occasional', 'bit', 'possibly']);
  const STOP = new Set('i a an the my is am are have has had feel feeling in on of to and with since from also got been me it its for at when while be having getting'.split(' '));

  const phrases = [];
  const vocab = new Set();
  for (const [id, info] of Object.entries(SYMPTOMS))
    for (const p of [info.label.toLowerCase(), ...info.synonyms]) {
      phrases.push([p, id]);
      p.split(/[^a-z']+/).forEach(w => w.length > 3 && vocab.add(w));
    }
  phrases.sort((a, b) => b[0].length - a[0].length);
  const phraseRx = phrases.map(([p, id]) => [new RegExp('\\b' + p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'g'), id]);

  function lev(a, b) {
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++)
      for (let j = 1; j <= b.length; j++)
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[a.length][b.length];
  }
  function fixSpelling(chunk) {
    return chunk.split(/\s+/).map(w => {
      const bare = w.replace(/[^a-z']/g, '');
      if (bare.length < 4 || vocab.has(bare) || STOP.has(bare) || UP.has(bare) || DOWN.has(bare) || NEG.has(bare)) return w;
      let best = null, bs = 0;
      for (const v of vocab) {
        const s = 1 - lev(bare, v) / Math.max(bare.length, v.length);
        if (s > bs) { bs = s; best = v; }
      }
      return bs >= 0.75 ? best : w;
    }).join(' ');
  }
  function phraseMatch(chunk) {
    const found = [];
    for (const [rx, id] of phraseRx) {
      rx.lastIndex = 0;
      if (rx.test(chunk)) { found.push(id); rx.lastIndex = 0; chunk = chunk.replace(rx, ' '); }
    }
    return found;
  }

  function parse(text) {
    const matches = [], negated = [];
    for (let chunk of text.toLowerCase().split(/[,.;\n]| and | but | also /)) {
      chunk = chunk.trim();
      if (!chunk) continue;
      const words = chunk.match(/[a-z']+/g) || [];
      if (words.some(w => NEG.has(w))) { negated.push(chunk); continue; }
      const cf = words.some(w => UP.has(w)) ? 1 : words.some(w => DOWN.has(w)) ? 0.5 : 0.8;
      let how = 'matched', ids = phraseMatch(chunk);
      if (!ids.length) { const fixed = fixSpelling(chunk); ids = phraseMatch(fixed); how = 'spelling fixed'; }
      ids.forEach(id => matches.push({ symptom: id, cf, how, heard: chunk }));
    }
    const best = {};
    matches.forEach(m => { if (!best[m.symptom] || m.cf > best[m.symptom].cf) best[m.symptom] = m; });
    return { matches: Object.values(best), negated };
  }

  root.MedEngine = { RULES, label, ruleText, run, diagnoses, triage, explain, parse, THRESHOLD };
})(window);

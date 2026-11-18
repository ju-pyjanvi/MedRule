(function () {
  const pages = [['index.html', 'Consult'], ['knowledge.html', 'Knowledge base'], ['lab.html', 'Inference lab'], ['about.html', 'How it works']];
  const cur = location.pathname.split('/').pop() || 'index.html';
  const beat = 'M0 24h70l6-7 6 7h18l5 5 8-30 9 40 6-15h20l8-8 8 8h30'.repeat(10);
  const svg = `<svg viewBox="0 -3 1940 52" width="1940" height="46" aria-hidden="true"><path d="${beat.replace(/M0 24/, 'M0 24')}"/></svg>`;
  document.getElementById('top').innerHTML =
    `<a class="brand" href="index.html">Med<b>✚</b>Rule</a>
     <nav aria-label="Pages">${pages.map(p => `<a href="${p[0]}"${p[0] === cur ? ' class="on" aria-current="page"' : ''}>${p[1]}</a>`).join('')}</nav>
     <div class="ecg"><div>${svg}${svg}</div></div>`;

  /* the header pulse reacts to the case: calm teal at rest, fast pink on a red flag */
  window.setPulse = function (level, top) {
    const s = document.documentElement.style;
    if (level === 'emergency') { s.setProperty('--pulse', '#ff206e'); s.setProperty('--beat', '1.6s'); }
    else if (level === 'urgent') { s.setProperty('--pulse', '#fbff12'); s.setProperty('--beat', '3s'); }
    else { s.setProperty('--pulse', '#41ead4'); s.setProperty('--beat', (7 - Math.min(top || 0, 1) * 3.5) + 's'); }
  };

  /* medical symbols, outlined, drifting at different speeds as you scroll */
  const g = [['✚', '#41ead4', '7vw', '6rem', 'auto', '-1rem', .09], ['℞', '#fbff12', 'auto', '8rem', '-1.5rem', '58vh', .16],
             ['⚕', '#ff206e', 'auto', '9rem', '4vw', '24vh', .22], ['♥', '#ff206e', '3vw', '5rem', 'auto', '78vh', .12], ['✚', '#fbff12', 'auto', '3.5rem', '38vw', '88vh', .3]];
  const box = document.createElement('div');
  box.className = 'glyphs'; box.setAttribute('aria-hidden', 'true');
  box.innerHTML = g.map(([c, col, l, size, r, t]) => `<span style="--c:${col};font-size:${size};left:${l};right:${r};top:${t}">${c}</span>`).join('');
  document.body.prepend(box);
  const spans = [...box.children];
  addEventListener('scroll', () => spans.forEach((s, i) => (s.style.transform = `translateY(${-scrollY * g[i][6]}px) rotate(${scrollY * g[i][6] * .06}deg)`)), { passive: true });

  document.body.insertAdjacentHTML('beforeend',
    `<footer><svg width="44" height="18" viewBox="0 0 44 18" aria-hidden="true"><rect x="1" y="1" width="42" height="16" rx="8" fill="#0c0f0a" stroke="#fff" stroke-width="2"/><path d="M22 1h13a8 8 0 010 16H22z" fill="#ff206e"/><path d="M22 1v16" stroke="#fff" stroke-width="2"/></svg>
     <p>MedRule is a college expert system built for learning. It is not medical advice, so see a doctor for real symptoms.</p></footer>`);
})();

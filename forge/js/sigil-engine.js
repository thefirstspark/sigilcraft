/**
 * Sigil Forge — engine
 * Deterministic: the same name + intention + style always compiles the same sigil.
 * Visual DNA inherited from Sigilcraft / The First Spark:
 * triangle, waves, infinity, binary, circle, golden angle.
 */
(function (global) {
  const PALETTES = [
    { main: '#26E4D8', accent: '#F3B23A', name: 'CYAN·GOLD' },
    { main: '#6B4DF2', accent: '#26E4D8', name: 'VIOLET·CYAN' },
    { main: '#FF6A3D', accent: '#F3B23A', name: 'EMBER·GOLD' },
    { main: '#26E4D8', accent: '#6B4DF2', name: 'CYAN·VIOLET' },
    { main: '#F3B23A', accent: '#FF6A3D', name: 'GOLD·EMBER' },
  ];

  // FNV-1a hash
  function hashString(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = (h * 16777619) >>> 0;
    }
    return h;
  }

  // Mulberry32 PRNG
  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      let t = seed;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /**
   * Classic sigil distillation:
   * statement → letters only → strip vowels → strip repeats.
   * What remains is the compressed "code" of the intention.
   */
  function distill(intention) {
    const letters = (intention || '').toUpperCase().replace(/[^A-Z]/g, '').split('');
    const seen = new Set();
    const out = [];
    for (const ch of letters) {
      if ('AEIOU'.includes(ch)) continue;
      if (seen.has(ch)) continue;
      seen.add(ch);
      out.push(ch);
    }
    return out;
  }

  function seedFor(name, intention, style) {
    return hashString(((name || '') + '::' + (intention || '') + '::' + (style || 'spark')).toLowerCase().trim());
  }

  /* ---------- drawing helpers ---------- */

  function vignette(ctx, W, H, color) {
    const g = ctx.createRadialGradient(W / 2, H / 2 - 20, 40, W / 2, H / 2 - 20, W * 0.62);
    g.addColorStop(0, color + '14');
    g.addColorStop(1, color + '00');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }

  // Smooth open path through points (quadratic through midpoints)
  function smoothPath(ctx, pts) {
    if (pts.length < 2) return;
    ctx.moveTo(pts[0][0], pts[0][1]);
    if (pts.length === 2) { ctx.lineTo(pts[1][0], pts[1][1]); return; }
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i][0] + pts[i + 1][0]) / 2;
      const my = (pts[i][1] + pts[i + 1][1]) / 2;
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], mx, my);
    }
    const last = pts[pts.length - 1];
    ctx.lineTo(last[0], last[1]);
  }

  // Classic sigil terminals: a small circle marks the entry…
  function entryCircle(ctx, x, y, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2); ctx.stroke();
  }
  // …and a crossbar marks the exit.
  function exitBar(ctx, x, y, angle, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x + Math.cos(angle) * 11, y + Math.sin(angle) * 11);
    ctx.lineTo(x - Math.cos(angle) * 11, y - Math.sin(angle) * 11);
    ctx.stroke();
  }
  function nodeDot(ctx, x, y, r, color) {
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  }

  /**
   * Map the distilled letters to glyph anchor points in the right half-plane.
   * Letter codes jump around the sweep (not a monotonic top→bottom walk), so
   * the stroke zig-zags and crosses itself — angular, not blobby. First and
   * last points are pinned to the vertical axis so the mirrored halves join.
   */
  function letterPoints(distilled, seed, cx, cy, R) {
    const rand = mulberry32(seed ^ 0xBEEF);
    const letters = distilled.length ? distilled : ['X', 'K'];
    const pts = [[cx, cy - R * (0.55 + rand() * 0.4)]];
    for (let i = 0; i < letters.length; i++) {
      const code = letters[i].charCodeAt(0) - 65; // 0..25
      const t = ((code * 5) % 26) / 25;           // scattered 0..1
      const a = -Math.PI / 2 + t * Math.PI;       // right half-plane
      const radius = R * (0.20 + 0.76 * (((code * 11) % 26) / 25));
      pts.push([cx + Math.cos(a) * radius, cy + Math.sin(a) * radius]);
    }
    pts.push([cx, cy + R * (0.55 + rand() * 0.4)]);
    return pts;
  }

  function mirror(pts, cx) {
    return pts.map(([x, y]) => [cx - (x - cx), y]);
  }

  function strokeGlyph(ctx, pts, color, width, glow, angular) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowColor = color;
    ctx.shadowBlur = glow;
    ctx.beginPath();
    if (angular) {
      pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
    } else {
      smoothPath(ctx, pts);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  function brandSeal(ctx, cx, cy, s, color, accent) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy - s);
    ctx.lineTo(cx - s * 0.9, cy + s * 0.7);
    ctx.lineTo(cx + s * 0.9, cy + s * 0.7);
    ctx.closePath();
    ctx.stroke();
    nodeDot(ctx, cx, cy + s * 0.1, 2.5, accent);
  }

  function signature(ctx, seed, pal, W, H, watermark) {
    const sig = seed.toString(2).padStart(32, '0').slice(0, 16);
    const sigId = seed.toString(36).toUpperCase().slice(0, 8);
    ctx.textAlign = 'center';
    ctx.font = 'bold 14px "Space Mono", monospace';
    ctx.fillStyle = pal.main + 'BB';
    ctx.fillText(sig, W / 2, H - 40);
    ctx.font = '10px "Space Mono", monospace';
    ctx.fillStyle = pal.accent + '99';
    ctx.fillText('SIGIL::' + sigId, W / 2, H - 20);
    if (watermark) {
      ctx.save();
      ctx.translate(W / 2, H / 2);
      ctx.rotate(-Math.PI / 8);
      ctx.font = 'bold 28px "Space Mono", monospace';
      ctx.fillStyle = '#FFFFFF18';
      ctx.fillText('UNCHARGED · SIGIL FORGE', 0, 0);
      ctx.restore();
    }
    return sigId;
  }

  /* ---------- style: SEAL (bilateral glyph in an inscribed ring) ---------- */
  function drawSeal(ctx, rand, pal, W, H, distilled, seed) {
    const cx = W / 2, cy = H / 2 - 16;
    const R = 176;

    // double ring with the distilled letters inscribed between
    ctx.strokeStyle = pal.main + '66';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(cx, cy, R + 52, 0, Math.PI * 2); ctx.stroke();
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(cx, cy, R + 26, 0, Math.PI * 2); ctx.stroke();

    const letters = distilled.length ? distilled : ['T', 'F', 'S'];
    const ringR = R + 39;
    ctx.font = '15px "Space Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    letters.forEach((ch, i) => {
      const a = -Math.PI / 2 + (i / letters.length) * Math.PI * 2;
      ctx.save();
      ctx.translate(cx + Math.cos(a) * ringR, cy + Math.sin(a) * ringR);
      ctx.rotate(a + Math.PI / 2);
      ctx.fillStyle = pal.accent + 'BB';
      ctx.fillText(ch, 0, 0);
      ctx.restore();
      // diamond tick between letters
      const b = a + Math.PI / letters.length;
      const tx = cx + Math.cos(b) * ringR, ty = cy + Math.sin(b) * ringR;
      ctx.save();
      ctx.translate(tx, ty); ctx.rotate(b);
      ctx.fillStyle = pal.main + '77';
      ctx.fillRect(-2.5, -2.5, 5, 5);
      ctx.restore();
    });

    // the glyph: angular strokes through letter points, mirrored for symmetry
    const pts = letterPoints(distilled, seed, cx, cy, R * 0.94);
    const mir = mirror(pts, cx);
    strokeGlyph(ctx, pts, pal.main, 3, 14, true);
    strokeGlyph(ctx, mir, pal.main, 3, 14, true);

    // nodes on both halves: most get dots, every third gets a small open circle
    pts.forEach(([x, y], i) => {
      if (i === 0 || i === pts.length - 1) return;
      if (i % 3 === 0) {
        ctx.strokeStyle = pal.main; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(x, y, 5.5, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(cx - (x - cx), y, 5.5, 0, Math.PI * 2); ctx.stroke();
      } else {
        nodeDot(ctx, x, y, 3.2, pal.main);
        nodeDot(ctx, cx - (x - cx), y, 3.2, pal.main);
      }
    });

    // terminals on the axis: entry circle above, exit bar below
    const top = pts[0], bot = pts[pts.length - 1];
    entryCircle(ctx, top[0], top[1], pal.accent);
    exitBar(ctx, bot[0], bot[1], 0, pal.accent);
    nodeDot(ctx, bot[0], bot[1], 3, pal.accent);

    // faint brand seal at heart
    brandSeal(ctx, cx, cy + 2, 14, pal.main + '55', pal.accent + '99');

    return { anchorY: cy };
  }

  /* ---------- style: LEY (witch's wheel, curved chords) ---------- */
  function drawLey(ctx, rand, pal, W, H, distilled) {
    const cx = W / 2, cy = H / 2 - 16;
    const R = 186;

    ctx.strokeStyle = pal.main + '55';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = pal.main + '33';
    ctx.beginPath(); ctx.arc(cx, cy, R + 22, 0, Math.PI * 2); ctx.stroke();

    // 26 letter stations
    const pos = {};
    for (let i = 0; i < 26; i++) {
      const a = -Math.PI / 2 + (i / 26) * Math.PI * 2;
      const ch = String.fromCharCode(65 + i);
      pos[ch] = { x: cx + Math.cos(a) * R, y: cy + Math.sin(a) * R, a };
      ctx.strokeStyle = pal.main + '3A';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R);
      ctx.lineTo(cx + Math.cos(a) * (R + 9), cy + Math.sin(a) * (R + 9));
      ctx.stroke();
    }

    const letters = distilled.length > 1 ? distilled : ['T', 'K'];

    // faint letter labels only at visited stations
    ctx.font = '13px "Space Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    letters.forEach((ch) => {
      const p = pos[ch];
      ctx.fillStyle = pal.accent + '88';
      ctx.fillText(ch, cx + (p.x - cx) * 1.11, cy + (p.y - cy) * 1.11);
    });

    // curved chords: each hop bends toward the center (bundled, elegant)
    ctx.strokeStyle = pal.accent;
    ctx.lineWidth = 2.8;
    ctx.lineCap = 'round';
    ctx.shadowColor = pal.accent;
    ctx.shadowBlur = 14;
    ctx.beginPath();
    for (let i = 0; i < letters.length - 1; i++) {
      const a = pos[letters[i]], b = pos[letters[i + 1]];
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const qx = mx + (cx - mx) * 0.45, qy = my + (cy - my) * 0.45;
      ctx.moveTo(a.x, a.y);
      ctx.quadraticCurveTo(qx, qy, b.x, b.y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // terminals + node dots
    const s = pos[letters[0]], e = pos[letters[letters.length - 1]];
    letters.forEach((ch) => nodeDot(ctx, pos[ch].x, pos[ch].y, 3.5, pal.main));
    entryCircle(ctx, s.x, s.y, pal.main);
    exitBar(ctx, e.x, e.y, e.a, pal.main);

    brandSeal(ctx, cx, cy, 16, pal.main + '66', pal.accent);

    return { anchorY: cy };
  }

  /* ---------- style: STAR (k-fold radial motif, mandala logic) ---------- */
  function drawStar(ctx, rand, pal, W, H, distilled, seed) {
    const cx = W / 2, cy = H / 2 - 16;
    const R = 190;
    const k = 5 + (seed % 4); // 5..8-fold symmetry

    ctx.strokeStyle = pal.main + '55';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(cx, cy, R + 28, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = pal.main + '2E';
    ctx.beginPath(); ctx.arc(cx, cy, R * 0.42, 0, Math.PI * 2); ctx.stroke();

    // one arm as a half-motif: a spiky zig-zag climbing outward, its angle
    // alternating sides, then mirrored within the wedge — each arm is
    // symmetric like a snowflake spine, ending in a sharp tip on the spoke.
    const letters = distilled.length ? distilled : ['S', 'G', 'L'];
    const wedge = Math.PI / k;
    const half = [[0, -R * 0.26]];
    const used = Math.min(letters.length, 5);
    for (let i = 0; i < used; i++) {
      const code = letters[i].charCodeAt(0) - 65;
      const t = (i + 1) / (used + 1);
      const side = ((code % 9) / 9) * wedge * 0.92; // 0..wedge, one side only
      const radius = R * (0.28 + 0.62 * t);
      half.push([Math.sin(side) * radius, -Math.cos(side) * radius]);
    }
    half.push([0, -R * 0.96]); // sharp tip on the spoke

    for (let f = 0; f < k; f++) {
      const rot = (f / k) * Math.PI * 2;
      const place = (m) => m.map(([x, y]) => [
        cx + x * Math.cos(rot) - y * Math.sin(rot),
        cy + x * Math.sin(rot) + y * Math.cos(rot),
      ]);
      const a = place(half);
      const b = place(half.map(([x, y]) => [-x, y])); // mirrored half
      strokeGlyph(ctx, a, pal.main + 'E6', 2.3, 9, true);
      strokeGlyph(ctx, b, pal.main + 'E6', 2.3, 9, true);
      const tip = a[a.length - 1];
      nodeDot(ctx, tip[0], tip[1], 4, pal.accent);
      a.slice(1, -1).forEach(([x, y]) => nodeDot(ctx, x, y, 2.2, pal.main));
      b.slice(1, -1).forEach(([x, y]) => nodeDot(ctx, x, y, 2.2, pal.main));
    }

    // ring pearls between arms
    for (let f = 0; f < k; f++) {
      const a = -Math.PI / 2 + ((f + 0.5) / k) * Math.PI * 2;
      nodeDot(ctx, cx + Math.cos(a) * (R + 28), cy + Math.sin(a) * (R + 28), 3, pal.accent + 'AA');
    }

    // center: entry circle + heart dot (the still point)
    entryCircle(ctx, cx, cy, pal.accent);
    nodeDot(ctx, cx, cy, 3.5, pal.accent);

    return { anchorY: cy };
  }

  /**
   * Render a sigil. opts: { name, intention, style, watermark }
   * Returns { id, seed, distilled, palette, style }
   */
  function draw(canvas, opts) {
    const style = opts.style || 'spark';
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const seed = seedFor(opts.name, opts.intention, style);
    const rand = mulberry32(seed);
    const pal = PALETTES[Math.floor(rand() * PALETTES.length)];
    const distilled = distill(opts.intention);

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#0B0B0C';
    ctx.fillRect(0, 0, W, H);
    vignette(ctx, W, H, pal.main);

    if (style === 'ley') drawLey(ctx, rand, pal, W, H, distilled);
    else if (style === 'star') drawStar(ctx, rand, pal, W, H, distilled, seed);
    else drawSeal(ctx, rand, pal, W, H, distilled, seed);

    const id = signature(ctx, seed, pal, W, H, opts.watermark);

    return { id, seed, distilled: distilled.join(''), palette: pal.name, style };
  }

  /* ---------- charging rituals ---------- */

  const METHODS = [
    {
      key: 'breath',
      name: 'Breath of Ignition',
      tool: 'Nothing but your lungs and your eyes.',
      best: 'Fast charges. When you need the sigil live today.',
      steps: [
        'Sit with the sigil at eye level. Let your gaze rest soft on its center.',
        'Breathe in for 4 counts, hold for 4, out for 4. Repeat until the lines start to shimmer at the edges of your focus.',
        'On your final exhale, breathe directly onto the sigil — you are transferring the intention from your body into the glyph.',
        'Look away. The charge is set the moment you stop looking.',
      ],
    },
    {
      key: 'flame',
      name: 'Flame Charge',
      tool: 'One candle. Any color that feels right — trust the pull.',
      best: 'Intentions of transformation, courage, and starting over.',
      steps: [
        'Light the candle and place the sigil (printed or on screen) behind or beside the flame.',
        'Speak your intention aloud once — the exact words you forged with. Only once.',
        'Watch the flame, not the sigil, until the words stop meaning anything and become pure sound in your memory.',
        'Snuff the candle (don’t blow it out — press it out or use a snuffer). Sealed.',
      ],
    },
    {
      key: 'lunar',
      name: 'Lunar Charge',
      tool: 'Moonlight. Full moon strongest; new moon for beginnings.',
      best: 'Long-game intentions. Things that need to grow over a cycle.',
      steps: [
        'On the night of the moon phase that matches your intention, place the sigil where moonlight can reach it — a windowsill counts.',
        'Before you set it down, hold it to your chest for nine slow breaths.',
        'Say: “I leave this in older hands than mine.”',
        'Leave it overnight. Retrieve it before noon and do not explain it to anyone.',
      ],
    },
    {
      key: 'water',
      name: 'Water Rite',
      tool: 'Running water — a shower works perfectly.',
      best: 'Release work, cleansing, unblocking what is stuck.',
      steps: [
        'Memorize the shape of your sigil. Take three slow looks, then close your eyes and redraw it in your mind until it holds steady.',
        'Step into running water. Visualize the sigil glowing on the surface of the water as it moves over you.',
        'Let the water carry the intention into every cell. Stay until the image dissolves on its own.',
        'Step out. Don’t look at the sigil again today.',
      ],
    },
    {
      key: 'kinetic',
      name: 'Kinetic Charge',
      tool: 'Music and a closed door.',
      best: 'Power, confidence, magnetism — anything that needs voltage.',
      steps: [
        'Put the sigil somewhere you can glimpse it while you move.',
        'Play one song that makes your body move without permission. Move — dance, shake, pace, whatever is true.',
        'At the peak of the song, lock eyes with the sigil for one full second. That second is the charge.',
        'When the song ends, stop completely. Stillness seals it.',
      ],
    },
    {
      key: 'release',
      name: 'The Release',
      tool: 'A printed copy and a safe way to destroy it.',
      best: 'The classic. For intentions you need to stop gripping.',
      steps: [
        'Print or hand-copy the sigil onto paper. Physical matters here.',
        'Charge it with any method above — then destroy it. Burn it safely, tear it to confetti, or bury it.',
        'The destruction is the point: you are handing the intention over completely.',
        'Forget it deliberately. Every time it comes to mind, think “sent,” and move on. The forgetting is the final step.',
      ],
    },
  ];

  function ritualFor(seed) {
    const rand = mulberry32(seed ^ 0x51611);
    const method = METHODS[Math.floor(rand() * METHODS.length)];
    const counts = [3, 7, 9, 11][Math.floor(rand() * 4)];
    const window = ['at dawn', 'at dusk', 'at 11:11', 'at midnight', 'when you first wake'][Math.floor(rand() * 5)];
    return { method, counts, window };
  }

  function monthlySeed(email, date) {
    const d = date || new Date();
    const key = (email || 'wanderer').toLowerCase() + '::' +
      d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
    return hashString(key);
  }

  const MONTH_THEMES = [
    'The Threshold', 'The Ember Held', 'The Long Signal', 'The Unlocking',
    'The Quiet Engine', 'The Golden Ratio', 'The Deep Current', 'The High Wire',
    'The Compiler', 'The Harvest Glyph', 'The Veil Thin', 'The Return Spark',
  ];

  function monthlyTheme(date) {
    const d = date || new Date();
    return MONTH_THEMES[d.getMonth()];
  }

  global.SigilEngine = {
    draw, distill, seedFor, ritualFor, monthlySeed, monthlyTheme,
    METHODS, hashString, mulberry32,
  };
})(window);

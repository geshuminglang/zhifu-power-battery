/*!
 * qrcode-lite.js  v1.0.0
 * Minimal, dependency-free QR Code (Model 2) encoder.
 * Byte mode with UTF-8 input. Error correction levels L / M / Q / H.
 * Versions 1-10 (up to 271 bytes at level L), automatic version selection,
 * automatic best-mask selection.
 *
 * Works in the browser (window.QRCodeLite) and in Node.js (module.exports).
 *
 * API
 *   QRCodeLite.generate(text, { ecLevel: 'M', maxVersion: 10 })
 *     -> { version, size, modules: [[bool]], mask, ecLevel }
 *   QRCodeLite.toSVG(result, { unit, quietZone, dark, light })
 *     -> SVG string
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.QRCodeLite = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* ------------------------------------------------------------------ *
   * Galois field GF(256), primitive polynomial 0x11D
   * ------------------------------------------------------------------ */
  var EXP = new Array(512);
  var LOG = new Array(256);
  (function () {
    var x = 1;
    for (var i = 0; i < 255; i++) {
      EXP[i] = x;
      LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= 0x11d;
    }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();

  function gexp(n) {
    while (n < 0) n += 255;
    while (n >= 255) n -= 255;
    return EXP[n];
  }
  function gmul(a, b) {
    if (a === 0 || b === 0) return 0;
    return EXP[(LOG[a] + LOG[b]) % 255];
  }

  /* ------------------------------------------------------------------ *
   * Reed-Solomon block layout, versions 1-10
   * [ecCodewordsPerBlock, blocksGroup1, dataPerBlock1, blocksGroup2, dataPerBlock2]
   * ------------------------------------------------------------------ */
  var RS_TABLE = {
    1:  { L: [7, 1, 19, 0, 0],   M: [10, 1, 16, 0, 0],   Q: [13, 1, 13, 0, 0],   H: [17, 1, 9, 0, 0] },
    2:  { L: [10, 1, 34, 0, 0],  M: [16, 1, 28, 0, 0],   Q: [22, 1, 22, 0, 0],   H: [28, 1, 16, 0, 0] },
    3:  { L: [15, 1, 55, 0, 0],  M: [26, 1, 44, 0, 0],   Q: [18, 2, 17, 0, 0],   H: [22, 2, 13, 0, 0] },
    4:  { L: [20, 1, 80, 0, 0],  M: [18, 2, 32, 0, 0],   Q: [26, 2, 24, 0, 0],   H: [16, 4, 9, 0, 0] },
    5:  { L: [26, 1, 108, 0, 0], M: [24, 2, 43, 0, 0],   Q: [18, 2, 15, 2, 16],  H: [22, 2, 11, 2, 12] },
    6:  { L: [18, 2, 68, 0, 0],  M: [16, 4, 27, 0, 0],   Q: [24, 4, 19, 0, 0],   H: [28, 4, 15, 0, 0] },
    7:  { L: [20, 2, 78, 0, 0],  M: [18, 4, 31, 0, 0],   Q: [18, 2, 14, 4, 15],  H: [26, 4, 13, 1, 14] },
    8:  { L: [24, 2, 97, 0, 0],  M: [22, 2, 38, 2, 39],  Q: [22, 4, 18, 2, 19],  H: [26, 4, 14, 2, 15] },
    9:  { L: [30, 2, 116, 0, 0], M: [22, 3, 36, 2, 37],  Q: [20, 4, 16, 4, 17],  H: [24, 4, 12, 4, 13] },
    10: { L: [18, 2, 68, 2, 69], M: [26, 4, 43, 1, 44],  Q: [24, 6, 19, 2, 20],  H: [28, 6, 15, 2, 16] }
  };

  var TOTAL_CODEWORDS = {
    1: 26, 2: 44, 3: 70, 4: 100, 5: 134,
    6: 172, 7: 196, 8: 242, 9: 292, 10: 346
  };

  // Remainder bits appended after the last codeword (ISO/IEC 18004 table 1).
  var REMAINDER_BITS = { 1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7, 7: 0, 8: 0, 9: 0, 10: 0 };

  var ALIGNMENT_PATTERN = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]
  };

  var EC_BITS = { L: 1, M: 0, Q: 3, H: 2 };
  var MODE_8BIT_BYTE = 4;
  var PAD0 = 0xec;
  var PAD1 = 0x11;

  /* ------------------------------------------------------------------ *
   * BCH codes for format / version information
   * ------------------------------------------------------------------ */
  function bchDigit(data) {
    var digit = 0;
    while (data !== 0) { digit++; data >>>= 1; }
    return digit;
  }

  function bchTypeInfo(data) {
    var d = data << 10;
    while (bchDigit(d) - bchDigit(0x537) >= 0) d ^= (0x537 << (bchDigit(d) - bchDigit(0x537)));
    return ((data << 10) | d) ^ 0x5412;
  }

  function bchVersionInfo(data) {
    var d = data << 12;
    while (bchDigit(d) - bchDigit(0x1f25) >= 0) d ^= (0x1f25 << (bchDigit(d) - bchDigit(0x1f25)));
    return (data << 12) | d;
  }

  /* ------------------------------------------------------------------ *
   * Small helpers
   * ------------------------------------------------------------------ */
  function utf8Bytes(str) {
    var out = [];
    for (var i = 0; i < str.length; i++) {
      var c = str.charCodeAt(i);
      if (c < 0x80) {
        out.push(c);
      } else if (c < 0x800) {
        out.push(0xc0 | (c >> 6), 0x80 | (c & 0x3f));
      } else if (c < 0xd800 || c >= 0xe000) {
        out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 0x3f), 0x80 | (c & 0x3f));
      } else {
        i++;
        var c2 = str.charCodeAt(i);
        var cp = 0x10000 + (((c & 0x3ff) << 10) | (c2 & 0x3ff));
        out.push(0xf0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3f), 0x80 | ((cp >> 6) & 0x3f), 0x80 | (cp & 0x3f));
      }
    }
    return out;
  }

  function countBitsFor(version) {
    return version <= 9 ? 8 : 16;
  }

  function rsBlocksFor(version, level) {
    var e = RS_TABLE[version][level];
    var ecPerBlock = e[0], g1 = e[1], d1 = e[2], g2 = e[3], d2 = e[4];
    var blocks = [];
    var acc = 0;
    for (var i = 0; i < g1; i++) { blocks.push({ totalCount: d1 + ecPerBlock, dataCount: d1 }); acc += d1 + ecPerBlock; }
    for (var j = 0; j < g2; j++) { blocks.push({ totalCount: d2 + ecPerBlock, dataCount: d2 }); acc += d2 + ecPerBlock; }
    if (acc !== TOTAL_CODEWORDS[version]) throw new Error('RS table mismatch v' + version + ' ' + level);
    return blocks;
  }

  function dataCodewordCount(version, level) {
    var blocks = rsBlocksFor(version, level);
    var n = 0;
    for (var i = 0; i < blocks.length; i++) n += blocks[i].dataCount;
    return n;
  }

  function capacityBytes(version, level) {
    return Math.floor((dataCodewordCount(version, level) * 8 - 4 - countBitsFor(version)) / 8);
  }

  function generatorPolynomial(ecCount) {
    var poly = [1];
    for (var i = 0; i < ecCount; i++) {
      var next = [];
      for (var k = 0; k <= poly.length; k++) next.push(0);
      for (var j = 0; j < poly.length; j++) {
        next[j] ^= gmul(poly[j], 1);
        next[j + 1] ^= gmul(poly[j], gexp(i));
      }
      poly = next;
    }
    return poly;
  }

  function rsEncode(data, ecCount) {
    var gen = generatorPolynomial(ecCount);
    var buf = data.slice();
    for (var i = 0; i < ecCount; i++) buf.push(0);
    for (var p = 0; p < data.length; p++) {
      var coef = buf[p];
      if (coef === 0) continue;
      for (var g = 0; g < gen.length; g++) buf[p + g] ^= gmul(gen[g], coef);
    }
    return buf.slice(data.length);
  }

  function maskBit(pattern, i, j) {
    switch (pattern) {
      case 0: return (i + j) % 2 === 0;
      case 1: return i % 2 === 0;
      case 2: return j % 3 === 0;
      case 3: return (i + j) % 3 === 0;
      case 4: return (Math.floor(i / 2) + Math.floor(j / 3)) % 2 === 0;
      case 5: return (((i * j) % 2) + ((i * j) % 3)) === 0;
      case 6: return ((((i * j) % 2) + ((i * j) % 3)) % 2) === 0;
      case 7: return ((((i + j) % 2) + ((i * j) % 3)) % 2) === 0;
    }
    return false;
  }

  /* ------------------------------------------------------------------ *
   * Codeword generation
   * ------------------------------------------------------------------ */
  function buildCodewords(version, level, bytes) {
    var blocks = rsBlocksFor(version, level);
    var totalData = dataCodewordCount(version, level);
    var bits = [];
    function put(value, length) {
      for (var i = length - 1; i >= 0; i--) bits.push((value >>> i) & 1);
    }
    put(MODE_8BIT_BYTE, 4);
    put(bytes.length, countBitsFor(version));
    for (var i = 0; i < bytes.length; i++) put(bytes[i], 8);
    var capacity = totalData * 8;
    if (bits.length > capacity) throw new Error('overflow');
    var terminator = Math.min(4, capacity - bits.length);
    for (var t = 0; t < terminator; t++) bits.push(0);
    while (bits.length % 8 !== 0) bits.push(0);
    var dataCodewords = [];
    for (var p = 0; p < bits.length; p += 8) {
      var v = 0;
      for (var q = 0; q < 8; q++) v = (v << 1) | bits[p + q];
      dataCodewords.push(v);
    }
    var toggle = 0;
    while (dataCodewords.length < totalData) {
      dataCodewords.push(toggle === 0 ? PAD0 : PAD1);
      toggle ^= 1;
    }

    var dc = [], ec = [], offset = 0, maxDc = 0, maxEc = 0;
    for (var r = 0; r < blocks.length; r++) {
      var dcCount = blocks[r].dataCount;
      var ecCount = blocks[r].totalCount - dcCount;
      dc[r] = dataCodewords.slice(offset, offset + dcCount);
      offset += dcCount;
      ec[r] = rsEncode(dc[r], ecCount);
      if (dcCount > maxDc) maxDc = dcCount;
      if (ecCount > maxEc) maxEc = ecCount;
    }
    var out = [];
    for (var d = 0; d < maxDc; d++) {
      for (var rb = 0; rb < blocks.length; rb++) if (d < dc[rb].length) out.push(dc[rb][d]);
    }
    for (var e2 = 0; e2 < maxEc; e2++) {
      for (var rc = 0; rc < blocks.length; rc++) if (e2 < ec[rc].length) out.push(ec[rc][e2]);
    }
    return out;
  }

  /* ------------------------------------------------------------------ *
   * Module layout
   * ------------------------------------------------------------------ */
  function functionTemplate(version) {
    var count = version * 4 + 17;
    var t = [];
    for (var r = 0; r < count; r++) t.push(new Array(count).fill(false));

    function mark(row, col) {
      if (row < 0 || count <= row || col < 0 || count <= col) return;
      t[row][col] = true;
    }
    function probe(row, col) {
      for (var r = -1; r <= 7; r++) for (var c = -1; c <= 7; c++) mark(row + r, col + c);
    }
    probe(0, 0);
    probe(count - 7, 0);
    probe(0, count - 7);

    // alignment patterns, skipping any that overlap a finder pattern
    var pos = ALIGNMENT_PATTERN[version];
    for (var i = 0; i < pos.length; i++) {
      for (var j = 0; j < pos.length; j++) {
        var row = pos[i], col = pos[j];
        if (t[row][col]) continue;
        for (var r2 = -2; r2 <= 2; r2++) for (var c2 = -2; c2 <= 2; c2++) mark(row + r2, col + c2);
      }
    }
    for (var k = 0; k < count; k++) { mark(6, k); mark(k, 6); }
    for (var f = 0; f < 9; f++) { mark(8, f); mark(f, 8); }
    for (var g = 0; g < 8; g++) { mark(8, count - 1 - g); mark(count - 1 - g, 8); }
    if (version >= 7) {
      for (var v = 0; v < 18; v++) {
        var a = Math.floor(v / 3), b = v % 3;
        mark(count - 11 + b, a);
        mark(a, count - 11 + b);
      }
    }
    return t;
  }

  function buildMatrix(version, codewords) {
    var count = version * 4 + 17;
    var modules = [];
    for (var r = 0; r < count; r++) modules.push(new Array(count).fill(null));

    function probe(row, col) {
      for (var r = -1; r <= 7; r++) {
        if (row + r < 0 || count <= row + r) continue;
        for (var c = -1; c <= 7; c++) {
          if (col + c < 0 || count <= col + c) continue;
          var dark = (0 <= r && r <= 6 && (c === 0 || c === 6)) ||
                     (0 <= c && c <= 6 && (r === 0 || r === 6)) ||
                     (2 <= r && r <= 4 && 2 <= c && c <= 4);
          modules[row + r][col + c] = dark;
        }
      }
    }
    probe(0, 0);
    probe(count - 7, 0);
    probe(0, count - 7);

    var pos = ALIGNMENT_PATTERN[version];
    for (var i = 0; i < pos.length; i++) {
      for (var j = 0; j < pos.length; j++) {
        var row = pos[i], col = pos[j];
        if (modules[row][col] !== null) continue;
        for (var r2 = -2; r2 <= 2; r2++) {
          for (var c2 = -2; c2 <= 2; c2++) {
            modules[row + r2][col + c2] =
              (r2 === -2 || r2 === 2 || c2 === -2 || c2 === 2 || (r2 === 0 && c2 === 0));
          }
        }
      }
    }
    for (var t2 = 8; t2 < count - 8; t2++) {
      if (modules[t2][6] === null) modules[t2][6] = (t2 % 2 === 0);
      if (modules[6][t2] === null) modules[6][t2] = (t2 % 2 === 0);
    }
    modules[count - 8][8] = true;
    for (var f = 0; f < 9; f++) {
      if (modules[8][f] === null) modules[8][f] = false;
      if (modules[f][8] === null) modules[f][8] = false;
    }
    for (var g = 0; g < 8; g++) {
      if (modules[8][count - 1 - g] === null) modules[8][count - 1 - g] = false;
      if (modules[count - 1 - g][8] === null) modules[count - 1 - g][8] = false;
    }
    if (version >= 7) {
      for (var v = 0; v < 18; v++) {
        var a = Math.floor(v / 3), b = v % 3;
        if (modules[count - 11 + b][a] === null) modules[count - 11 + b][a] = false;
        if (modules[a][count - 11 + b] === null) modules[a][count - 11 + b] = false;
      }
    }

    var inc = -1, row3 = count - 1, bitIndex = 7, byteIndex = 0;
    for (var col3 = count - 1; col3 > 0; col3 -= 2) {
      if (col3 === 6) col3--;
      for (;;) {
        for (var c3 = 0; c3 < 2; c3++) {
          if (modules[row3][col3 - c3] === null) {
            var dark3 = false;
            if (byteIndex < codewords.length) dark3 = ((codewords[byteIndex] >>> bitIndex) & 1) === 1;
            modules[row3][col3 - c3] = dark3;
            bitIndex--;
            if (bitIndex === -1) { byteIndex++; bitIndex = 7; }
          }
        }
        row3 += inc;
        if (row3 < 0 || count <= row3) { row3 -= inc; inc = -inc; break; }
      }
    }
    return modules;
  }

  function writeFormatInfo(modules, level, mask) {
    var count = modules.length;
    var bits = bchTypeInfo((EC_BITS[level] << 3) | mask);
    for (var i = 0; i < 15; i++) {
      var dark = ((bits >> i) & 1) === 1;
      if (i < 6) modules[i][8] = dark;
      else if (i < 8) modules[i + 1][8] = dark;
      else modules[count - 15 + i][8] = dark;
    }
    for (var j = 0; j < 15; j++) {
      var dark2 = ((bits >> j) & 1) === 1;
      if (j < 8) modules[8][count - j - 1] = dark2;
      else if (j < 9) modules[8][15 - j - 1 + 1] = dark2;
      else modules[8][15 - j - 1] = dark2;
    }
    modules[count - 8][8] = true;
  }

  function writeVersionInfo(modules, version) {
    if (version < 7) return;
    var count = modules.length;
    var bits = bchVersionInfo(version);
    for (var i = 0; i < 18; i++) {
      var dark = ((bits >> i) & 1) === 1;
      var a = Math.floor(i / 3), b = i % 3;
      modules[count - 11 + b][a] = dark;
      modules[a][count - 11 + b] = dark;
    }
  }

  function applyMaskWithTemplate(modules, mask, version) {
    var tpl = functionTemplate(version);
    var count = modules.length;
    for (var r = 0; r < count; r++) {
      for (var c = 0; c < count; c++) {
        if (tpl[r][c]) continue;
        if (maskBit(mask, r, c)) modules[r][c] = !modules[r][c];
      }
    }
  }

  function penalty(modules) {
    var count = modules.length;
    var score = 0;
    function runScore(len) { return len >= 5 ? 3 + (len - 5) : 0; }

    for (var r = 0; r < count; r++) {
      var color = modules[r][0], len = 1;
      for (var c = 1; c < count; c++) {
        if (modules[r][c] === color) len++;
        else { score += runScore(len); color = modules[r][c]; len = 1; }
      }
      score += runScore(len);
    }
    for (var c2 = 0; c2 < count; c2++) {
      var color2 = modules[0][c2], len2 = 1;
      for (var r2 = 1; r2 < count; r2++) {
        if (modules[r2][c2] === color2) len2++;
        else { score += runScore(len2); color2 = modules[r2][c2]; len2 = 1; }
      }
      score += runScore(len2);
    }
    for (var r3 = 0; r3 < count - 1; r3++) {
      for (var c3 = 0; c3 < count - 1; c3++) {
        var v = modules[r3][c3];
        if (v === modules[r3][c3 + 1] && v === modules[r3 + 1][c3] && v === modules[r3 + 1][c3 + 1]) score += 3;
      }
    }
    var pat1 = [true, false, true, true, true, false, true, false, false, false, false];
    var pat2 = [false, false, false, false, true, false, true, true, true, false, true];
    for (var r4 = 0; r4 < count; r4++) {
      for (var c4 = 0; c4 <= count - 11; c4++) {
        var m1 = true, m2 = true;
        for (var k = 0; k < 11; k++) {
          if (modules[r4][c4 + k] !== pat1[k]) m1 = false;
          if (modules[r4][c4 + k] !== pat2[k]) m2 = false;
        }
        if (m1) score += 40;
        if (m2) score += 40;
      }
    }
    for (var c5 = 0; c5 < count; c5++) {
      for (var r5 = 0; r5 <= count - 11; r5++) {
        var n1 = true, n2 = true;
        for (var k2 = 0; k2 < 11; k2++) {
          if (modules[r5 + k2][c5] !== pat1[k2]) n1 = false;
          if (modules[r5 + k2][c5] !== pat2[k2]) n2 = false;
        }
        if (n1) score += 40;
        if (n2) score += 40;
      }
    }
    var darkCount = 0;
    for (var r6 = 0; r6 < count; r6++) for (var c6 = 0; c6 < count; c6++) if (modules[r6][c6]) darkCount++;
    var ratio = (darkCount * 100) / (count * count);
    score += Math.floor(Math.abs(ratio - 50) / 5) * 10;
    return score;
  }

  function cloneMatrix(m) {
    return m.map(function (row) { return row.slice(); });
  }

  /* ------------------------------------------------------------------ *
   * Public API
   * ------------------------------------------------------------------ */
  function pickVersion(byteLength, level, maxVersion) {
    for (var v = 1; v <= maxVersion; v++) {
      if (byteLength <= capacityBytes(v, level)) return v;
    }
    return -1;
  }

  function generate(text, options) {
    options = options || {};
    var level = options.ecLevel || 'M';
    var maxVersion = options.maxVersion || 10;
    if (!/^[LMQH]$/.test(level)) throw new Error('invalid ecLevel');
    var bytes = utf8Bytes(String(text));
    var version = pickVersion(bytes.length, level, maxVersion);
    if (version < 0) {
      throw new Error('content too long (' + bytes.length + ' bytes) for QR versions 1-' + maxVersion + ' at level ' + level);
    }
    var codewords = buildCodewords(version, level, bytes);
    var base = buildMatrix(version, codewords);

    var best = null, bestMask = 0, bestScore = Infinity;
    for (var mask = 0; mask < 8; mask++) {
      var trial = cloneMatrix(base);
      applyMaskWithTemplate(trial, mask, version);
      writeFormatInfo(trial, level, mask);
      writeVersionInfo(trial, version);
      var s = penalty(trial);
      if (s < bestScore) { bestScore = s; best = trial; bestMask = mask; }
    }

    var tpl = functionTemplate(version);
    var dataModules = 0;
    for (var r = 0; r < best.length; r++) for (var c = 0; c < best.length; c++) if (!tpl[r][c]) dataModules++;
    var expected = TOTAL_CODEWORDS[version] * 8 + REMAINDER_BITS[version];
    if (dataModules !== expected) {
      throw new Error('layout mismatch: ' + dataModules + ' != ' + expected);
    }
    return { version: version, size: best.length, modules: best, mask: bestMask, ecLevel: level };
  }

  function toSVG(result, options) {
    options = options || {};
    var quiet = options.quietZone == null ? 4 : options.quietZone;
    var unit = options.unit || 8;
    var dark = options.dark || '#0b1220';
    var light = options.light || '#ffffff';
    var size = result.size;
    var dim = (size + quiet * 2) * unit;
    var path = [];
    for (var r = 0; r < size; r++) {
      for (var c = 0; c < size; c++) {
        if (!result.modules[r][c]) continue;
        path.push('M' + ((c + quiet) * unit) + ' ' + ((r + quiet) * unit) + 'h' + unit + 'v' + unit + 'h-' + unit + 'z');
      }
    }
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + dim + '" height="' + dim +
      '" viewBox="0 0 ' + dim + ' ' + dim + '" shape-rendering="crispEdges" role="img">' +
      '<rect width="' + dim + '" height="' + dim + '" fill="' + light + '"/>' +
      '<path d="' + path.join('') + '" fill="' + dark + '"/></svg>';
  }

  return {
    generate: generate,
    toSVG: toSVG,
    _internal: {
      utf8Bytes: utf8Bytes,
      generatorPolynomial: generatorPolynomial,
      rsEncode: rsEncode,
      capacityBytes: capacityBytes,
      dataCodewordCount: dataCodewordCount,
      rsBlocksFor: rsBlocksFor,
      bchTypeInfo: bchTypeInfo,
      bchVersionInfo: bchVersionInfo,
      TOTAL_CODEWORDS: TOTAL_CODEWORDS,
      functionTemplate: functionTemplate
    }
  };
});

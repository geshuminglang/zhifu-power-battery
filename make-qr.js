#!/usr/bin/env node
/*
 * make-qr.js — generate offline QR code files (SVG + PNG) for any URL or text.
 *
 * Usage:
 *   node tools/make-qr.js "https://your-domain.com" --name website
 *   node tools/make-qr.js "https://your-domain.com/products/72v-30ah.html" --name 72v-30ah
 *   node tools/make-qr.js "https://x.com" --out ./out --color 0b1220 --scale 10
 *
 * Options:
 *   --name <slug>     base file name (default: qr)
 *   --out <dir>       output directory (default: current directory)
 *   --scale <n>       PNG pixels per module (default: 10)
 *   --quiet <n>       quiet zone in modules (default: 4)
 *   --color <hex>     dark colour hex without '#', e.g. 0b1220 (default: 000000)
 *   --ec <L|M|Q|H>    error correction level (default: M)
 */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const QR = require(path.join(__dirname, '..', 'assets', 'js', 'qrcode-lite.js'));

/* ------------------------------ PNG writer ------------------------------ */
const CRC_TABLE = (function () {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

function matrixToPng(result, opts) {
  const scale = opts.scale, quiet = opts.quiet;
  const size = result.size;
  const dim = (size + quiet * 2) * scale;
  const [dr, dg, db] = opts.dark;
  const [lr, lg, lb] = opts.light;

  const raw = Buffer.alloc(dim * (dim * 3 + 1));
  let p = 0;
  for (let y = 0; y < dim; y++) {
    raw[p++] = 0; // filter: none
    const my = Math.floor(y / scale) - quiet;
    for (let x = 0; x < dim; x++) {
      const mx = Math.floor(x / scale) - quiet;
      const isDark = my >= 0 && my < size && mx >= 0 && mx < size && result.modules[my][mx];
      raw[p++] = isDark ? dr : lr;
      raw[p++] = isDark ? dg : lg;
      raw[p++] = isDark ? db : lb;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(dim, 0);
  ihdr.writeUInt32BE(dim, 4);
  ihdr[8] = 8;             // bit depth
  ihdr[9] = 2;             // colour type: truecolour RGB
  ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    pngChunk('IHDR', ihdr),
    pngChunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
    pngChunk('IEND', Buffer.alloc(0))
  ]);
}

/* ------------------------------- CLI parsing ---------------------------- */
function parseArgs(argv) {
  const out = { text: null, name: 'qr', out: '.', scale: 10, quiet: 4, color: '000000', ec: 'M' };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--name') out.name = argv[++i];
    else if (a === '--out') out.out = argv[++i];
    else if (a === '--scale') out.scale = parseInt(argv[++i], 10);
    else if (a === '--quiet') out.quiet = parseInt(argv[++i], 10);
    else if (a === '--color') out.color = String(argv[++i]).replace(/^#/, '');
    else if (a === '--ec') out.ec = String(argv[++i]).toUpperCase();
    else rest.push(a);
  }
  out.text = rest[0] || null;
  return out;
}

function hexToRgb(hex) {
  const h = hex.padStart(6, '0').slice(0, 6);
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.text) {
    console.error('Usage: node tools/make-qr.js "<text-or-url>" [--name slug] [--out dir] [--scale 10] [--quiet 4] [--color 000000] [--ec M]');
    process.exit(2);
  }
  const dark = hexToRgb(args.color);
  const result = QR.generate(args.text, { ecLevel: args.ec });
  fs.mkdirSync(args.out, { recursive: true });

  const svg = QR.toSVG(result, { unit: 8, quietZone: args.quiet, dark: '#' + args.color, light: '#ffffff' });
  const svgPath = path.join(args.out, args.name + '.svg');
  fs.writeFileSync(svgPath, svg);

  const png = matrixToPng(result, { scale: args.scale, quiet: args.quiet, dark, light: [255, 255, 255] });
  const pngPath = path.join(args.out, args.name + '.png');
  fs.writeFileSync(pngPath, png);

  console.log('content : ' + args.text);
  console.log('version : ' + result.version + '  (' + result.size + 'x' + result.size + ' modules, EC ' + result.ecLevel + ', mask ' + result.mask + ')');
  console.log('svg     : ' + svgPath);
  console.log('png     : ' + pngPath + '  (' + ((result.size + args.quiet * 2) * args.scale) + 'px)');
}

main();

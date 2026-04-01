"""
cli/interface.py
Command-line interface for XScanner.
"""

import asyncio
import time
import sys
import os
from typing import Optional

import click
from rich.console import Console

from utils.config import ScanConfig
from utils.logger import banner, info, warn, error, success, set_verbose, section
from scanner.engine import ScanEngine
from reports.reporter import Reporter

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option("3.0.0", "-V", "--version", prog_name="xscanner")
# ── Preset Mode ──────────────────────────────────────────────────────────────
@click.option("--mode", "-m",
              type=click.Choice(["quick","hunt","bypass","bounty","stealth","blind","spa"]),
              default=None,
              help="Preset mode — gabungan flag yang sudah dikurasi. "
                   "Jalankan --list-modes untuk lihat detail setiap mode.")
@click.option("--list-modes", is_flag=True, default=False,
              help="Tampilkan semua preset mode beserta flag-flag yang dicakup, lalu exit.")
# ── Core targeting ───────────────────────────────────────────────────────────
@click.option("-u", "--url",       multiple=True, help="Target URL(s). Can specify multiple: -u url1 -u url2")
@click.option("-l", "--list",      "url_file",    type=click.Path(exists=True), help="File with target URLs (one per line)")
# ── Scan tuning ──────────────────────────────────────────────────────────────
@click.option("--threads",         default=10,    show_default=True, help="Concurrent threads")
@click.option("--timeout",         default=10,    show_default=True, help="Request timeout in seconds")
@click.option("--depth",           default=2,     show_default=True, help="Crawl depth")
@click.option("--profile",         default="normal", type=click.Choice(["fast","normal","deep","stealth"]), show_default=True)
@click.option("--deep",            is_flag=True,  help="Shorthand for --profile deep")
@click.option("--no-crawl",        is_flag=True,  help="Don't crawl — only test provided URL params")
@click.option("--no-waf-bypass",   is_flag=True,  help="Disable WAF evasion techniques")
# ── Request customization ────────────────────────────────────────────────────
@click.option("-H", "--header",    multiple=True, help="Custom header(s): 'Name: Value'")
@click.option("-c", "--cookie",    multiple=True, help="Cookie(s): 'name=value'")
@click.option("--proxy",           default=None,  help="Proxy URL: http://127.0.0.1:8080")
@click.option("--rate-limit",      default=0.0,   help="Seconds between requests (0 = unlimited)")
# ── Authentication ───────────────────────────────────────────────────────────
@click.option("--login-url",       default=None,  help="Login form URL for authenticated scanning")
@click.option("--username",        default=None,  help="Login username")
@click.option("--password",        default=None,  help="Login password")
# ── Scope control ────────────────────────────────────────────────────────────
@click.option("--scope",           multiple=True, help="In-scope domain(s): example.com or *.example.com")
@click.option("--exclude-scope",   multiple=True, help="Out-of-scope domain(s) to skip")
@click.option("--exclude-path",    multiple=True, help="URL path prefix(es) to exclude: /logout /admin")
# ── Extended test modules ────────────────────────────────────────────────────
@click.option("--test-headers",    is_flag=True,  help="Test XSS via HTTP headers (User-Agent, Referer, X-Forwarded-For, etc.)")
@click.option("--test-hpp",        is_flag=True,  help="Test HTTP Parameter Pollution")
@click.option("--test-new-events", is_flag=True,  help="[2025] Test XSS via event handler HTML5 baru (onbeforetoggle, onanimationcancel, dll)")
@click.option("--test-parser-diff",is_flag=True,  help="[2025] Test parser differential bypass (Ethiack Research 2025, bypass 14/17 WAF)")
@click.option("--test-hpp-2025",   is_flag=True,  help="[2025] HPP ASP.NET comma concat exploit (Ethiack Research 2025)")
@click.option("--start-rich-blind-server", is_flag=True, help="Jalankan Rich Blind XSS server (XSS Hunter-style) dengan screenshot + data exfil")
@click.option("--blind-server-port",     default=8765,  show_default=True, help="Port untuk blind XSS server")
@click.option("--blind-output-dir",      default="./blind_xss_hits", show_default=True, help="Direktori simpan blind XSS hits (screenshot, DOM, JSON)")
@click.option("--no-blind-screenshot",   is_flag=True,  help="Nonaktifkan screenshot html2canvas di probe")
@click.option("--run-afb",               is_flag=True,  help="[KNOXSS] Advanced Filter Bypass — probe tiap karakter kritis")
@click.option("--generate-poc",          is_flag=True,  help="[KNOXSS] Generate HTML PoC per finding (siap bug bounty submit)")
@click.option("--poc-output-dir",        default="./xss_pocs", show_default=True, help="Direktori output HTML PoC")
@click.option("--knoxss-validate",       is_flag=True,  help="[KNOXSS] Validasi setiap finding di browser nyata")
@click.option("--scan-timeout",    default=0,     show_default=True, help="Batas waktu total scan dalam detik (0 = tidak ada batas)")
@click.option("--max-findings",    default=0,     show_default=True, help="Berhenti setelah N finding (0 = tidak ada batas)")
@click.option("--payload-file",    default=None,  type=click.Path(exists=True), help="File berisi custom XSS payloads (satu per baris)")
@click.option("--no-progress",     is_flag=True,  help="Nonaktifkan progress bar")
@click.option("--test-json",       is_flag=True,  help="Test JSON API endpoints with JSON-specific payloads")
@click.option("--second-order",    is_flag=True,  help="Track & verify stored/second-order XSS on POST endpoints")
@click.option("--js-crawl",        is_flag=True,  help="Extract parameters from JavaScript files (SPA support)")
# ── Blind XSS ────────────────────────────────────────────────────────────────
@click.option("--blind-callback",  default=None,  help="Blind XSS callback URL (e.g. http://your-server.com/xss)")
@click.option("--start-blind-server", is_flag=True, help="Start local blind XSS listener on port 8765")
# ── Verification ─────────────────────────────────────────────────────────────
@click.option("--verify-headless", is_flag=True,  help="Confirm findings in headless Chromium (requires Playwright)")
# ── Output ───────────────────────────────────────────────────────────────────
@click.option("-o", "--output",    default="xscanner_report.json", show_default=True, help="JSON report output path")
@click.option("--report-html",     default=None,  help="Also save HTML report to this path")
@click.option("--report-csv",      default=None,  help="Also save CSV report to this path")
@click.option("--report-md",       default=None,  help="Also save Markdown report to this path")
@click.option("--report-sarif",    default=None,  help="Also save SARIF report to this path (for CI/CD)")
# ── Misc ─────────────────────────────────────────────────────────────────────
@click.option("--checkpoint",      is_flag=True,  help="Save/resume scan state (auto checkpoint)")
@click.option("-v", "--verbose",   is_flag=True,  help="Verbose output")
@click.option("--details",         is_flag=True,  help="Print full payload + evidence for each finding")
# ── vOVERPOWER options ─────────────────────────────────────────────────────────
@click.option("--engine-version",  default="v2",  type=click.Choice(["v1","v2"]), help="Payload engine version")
@click.option("--test-csp-bypass", is_flag=True,  help="Test CSP bypass techniques")
@click.option("--test-prototype",  is_flag=True,  help="Test prototype pollution XSS")
@click.option("--test-websocket",  is_flag=True,  help="Test WebSocket/SSE injection")
@click.option("--test-template",   is_flag=True,  help="Test template injection (Angular/Vue/React/Jinja)")
@click.option("--test-smuggling",  is_flag=True,  help="Test HTTP request smuggling XSS")
@click.option("--browser-quirks",  is_flag=True,  help="Enable browser-specific payload variants")
@click.option("--unicode-bypass",  is_flag=True,  help="Enable Unicode/homoglyph WAF evasion")
@click.option("--dom-clobbering",  is_flag=True,  help="Enable DOM clobbering payloads")
@click.option("--ai-assist",       is_flag=True,  help="Enable AI-powered payload suggestions (needs ANTHROPIC_API_KEY)")
@click.option("--waf-chain-depth", default=3,     help="WAFChain depth: 2=pairs 3=triples 4=quads [default: 3]")
@click.option("--engine-v3",       is_flag=True,  help="Use ScanEngineV3 (vOVERPOWER, all engines active)")
# ── Fix #2 & Fix #3 flags ──────────────────────────────────────────────────────
@click.option("--dom-xss-scan",   is_flag=True,  help="[Fix#2] DOM XSS via JS instrumentation (Playwright)")
@click.option("--spa-crawl",      is_flag=True,  help="[Fix#3] SPA crawling via Playwright (React/Vue/Angular)")
@click.option("--spa-interact",   is_flag=True,  help="[Fix#3] Interact with forms during SPA crawl")
def main(mode, list_modes,
    
    url, url_file, threads, timeout, depth, profile, deep, no_crawl,
    no_waf_bypass, header, cookie, proxy, rate_limit,
    login_url, username, password,
    scope, exclude_scope, exclude_path,
    test_headers, test_hpp, test_json, second_order, js_crawl,
    test_new_events, test_parser_diff, test_hpp_2025,
    start_rich_blind_server, blind_server_port, blind_output_dir,
    no_blind_screenshot, run_afb, generate_poc, poc_output_dir, knoxss_validate,
    scan_timeout, max_findings, payload_file, no_progress,
    blind_callback, start_blind_server, verify_headless,
    output, report_html, report_csv, report_md, report_sarif,
    checkpoint, verbose, details,
    engine_version, test_csp_bypass, test_prototype, test_websocket,
    test_template, test_smuggling, browser_quirks, unicode_bypass,
    dom_clobbering, ai_assist, waf_chain_depth, engine_v3,
    dom_xss_scan, spa_crawl, spa_interact,
):
    """
    \b
    XScanner — Next-Generation XSS Security Research Framework
    ──────────────────────────────────────────────────────────
    ⚠  Untuk authorized penetration testing dan security research ONLY.
    ⚠  Penggunaan tanpa izin tertulis adalah tindakan ilegal.

    \b
    CARA CEPAT — pakai --mode:
      python xscanner.py -u "https://target.com" --mode quick    # triage 5 menit
      python xscanner.py -u "https://target.com" --mode hunt     # full scan 1-3 jam
      python xscanner.py -u "https://target.com" --mode bypass   # lolos WAF
      python xscanner.py -u "https://target.com" --mode bounty   # laporan lengkap
      python xscanner.py -u "https://target.com" --mode spa      # React/Vue/Angular
      python xscanner.py -u "https://target.com" --mode blind --blind-callback https://cb.io
      python xscanner.py --list-modes                            # lihat semua mode

    \b
    ALUR KERJA BUG BOUNTY:
      1. quick   →  lihat ada yang menarik tidak
      2. hunt    →  gali dalam di target yang menarik
      3. bypass  →  kalau ada XSS tapi diblokir WAF
      4. bounty  →  generate bukti + laporan siap submit
    """
    banner()

    # ─── Collect targets ─────────────────────────────────────────────────────

    # ── --list-modes: tampilkan semua mode dan exit ───────────────────────────
    if list_modes:
        from utils.config import SCAN_MODES
        import click as _click

        _click.echo("""
  ╔══════════════════════════════════════════════════════════════════╗
  ║            XScanner — Scan Modes Reference                      ║
  ╚══════════════════════════════════════════════════════════════════╝

  ALUR KERJA YANG DIREKOMENDASIKAN:
  ─────────────────────────────────
  1. quick   → "Ada XSS ga di sini?" (triage awal)
  2. hunt    → "Gali lebih dalam, cari semua" (main scan)
  3. bypass  → "Ada XSS tapi keblokir WAF" (fokus bypass)
  4. bounty  → "Siapkan bukti untuk laporan" (final step)

  Mode kondisi khusus (butuh setup tambahan):
  ─────────────────────────────────────────
  blind  → Admin panel / stored XSS (butuh callback server)
  spa    → React / Vue / Angular app (butuh Playwright)
  stealth→ Target sensitif dengan IDS (sangat lambat)
""")
        for _name, _cfg in SCAN_MODES.items():
            _flags = {k:v for k,v in _cfg.items()
                      if k not in ("desc","detail") and v not in (False, None)}
            _bool_on  = [k for k,v in _flags.items() if v is True]
            _non_bool = {k:v for k,v in _flags.items() if v is not True}

            _click.echo(f"  ┌─ --mode {_name}")
            _click.echo(f"  │  {_cfg['desc']}")
            _click.echo(f"  │")
            _click.echo(f"  │  {_cfg.get('detail','')}")
            _click.echo(f"  │")
            if _non_bool:
                for _k,_v in _non_bool.items():
                    _click.echo(f"  │  {_k} = {_v}")
            if _bool_on:
                _click.echo(f"  │  Aktif: {', '.join(_bool_on[:6])}")
                if len(_bool_on) > 6:
                    _click.echo(f"  │         {', '.join(_bool_on[6:12])}")
            _click.echo(f"  └{'─'*60}")
            _click.echo("")

        _click.echo("""  CONTOH PENGGUNAAN:
  ─────────────────────────────────────────────────────────────
  # Triage cepat
  python xscanner.py -u "https://target.com" --mode quick

  # Full scan dengan laporan
  python xscanner.py -u "https://target.com" --mode hunt -o hasil.json

  # Bypass WAF yang ketat
  python xscanner.py -u "https://target.com/search?q=test" --mode bypass

  # Bug bounty lengkap
  python xscanner.py -u "https://target.com" --mode bounty \
    --blind-callback "https://your-server.com" \
    --scan-timeout 7200

  # Aplikasi SPA
  python xscanner.py -u "https://target.com" --mode spa

  # Blind XSS (butuh ngrok/VPS untuk server lokal)
  python xscanner.py -u "https://target.com" --mode blind \
    --blind-callback "https://your-vps.com"

  # Override flag setelah mode
  python xscanner.py -u "https://target.com" --mode hunt \
    --threads 20 --scan-timeout 3600 --payload-file my_payloads.txt
""")
        return

    # ── Apply preset mode (sebelum individual flags di-process) ──────────────
    if mode:
        from utils.config import SCAN_MODES
        _preset = SCAN_MODES.get(mode, {})
        # Map preset key → local variable override
        # Hanya override jika user tidak set flag secara eksplisit
        # (Click tidak expose "apakah user set ini", jadi kita pakai nilai default sebagai proxy)
        _mode_map = {
            "profile":               lambda v: v,
            "depth":                 lambda v: v,
            "threads":               lambda v: v,
            "rate_limit":            lambda v: v,
            "waf_chain_depth":       lambda v: v,
            "engine_version":        lambda v: v,
            "report_html":           lambda v: v,
            "report_md":             lambda v: v,
            "report_sarif":          lambda v: v,
        }
        # Boolean flags — aktifkan dari preset
        _bool_flags = [
            "crawl","waf_bypass","test_headers","test_hpp","test_hpp_2025",
            "test_json","test_csp_bypass","test_prototype","test_template",
            "test_new_events","test_parser_diff","unicode_bypass","browser_quirks",
            "dom_clobbering","second_order","js_crawl","dom_xss_scan","run_afb",
            "knoxss_validate","generate_poc","verify_headless","checkpoint",
            "start_rich_blind_server","blind_screenshot","spa_crawl",
        ]
        # Apply preset values ke locals
        for _key, _val in _preset.items():
            if _key == "desc":
                continue
            if _key in _mode_map and _val is not None:
                locals()[_key] = _val
            elif _key in _bool_flags and _val is True:
                locals()[_key] = True
            elif _key == "no_crawl" and _val is False:
                no_crawl = False

        import click as _c
        _c.echo(f"  [mode: {mode}] {_preset.get('desc','')}\n")

    targets = list(url)
    if url_file:
        with open(url_file) as f:
            targets += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not targets:
        error("No targets specified. Use -u <url> or -l <file>")
        sys.exit(1)

    # ─── Parse headers ───────────────────────────────────────────────────────
    parsed_headers = {}
    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            parsed_headers[k.strip()] = v.strip()

    # ─── Parse cookies ───────────────────────────────────────────────────────
    parsed_cookies = {}
    for c in cookie:
        if "=" in c:
            k, v = c.split("=", 1)
            parsed_cookies[k.strip()] = v.strip()

    # ─── Build config ────────────────────────────────────────────────────────
    if deep:
        profile = "deep"

    config = ScanConfig(
        # Core
        targets         = targets,
        threads         = threads,
        timeout         = timeout,
        depth           = depth,
        profile         = profile,
        headers         = parsed_headers,
        cookies         = parsed_cookies,
        proxy           = proxy,
        output          = output,
        crawl           = not no_crawl,
        deep            = deep,
        blind_callback  = blind_callback,
        waf_bypass      = not no_waf_bypass,
        verify_headless = verify_headless,
        verbose         = verbose,
        rate_limit      = rate_limit,
        # Auth
        login_url       = login_url,
        username        = username,
        password        = password,
        # Scope
        scope           = list(scope),
        exclude_scope   = list(exclude_scope),
        exclude_path    = list(exclude_path),
        # Extended modules
        test_headers    = test_headers,
        test_hpp        = test_hpp,
        test_new_events = test_new_events,
        test_parser_diff= test_parser_diff,
        test_hpp_2025   = test_hpp_2025,
        start_rich_blind_server = start_rich_blind_server,
        blind_server_port       = blind_server_port,
        blind_output_dir        = blind_output_dir,
        blind_screenshot        = not no_blind_screenshot,
        run_afb                 = run_afb,
        generate_poc            = generate_poc,
        poc_output_dir          = poc_output_dir,
        knoxss_validate         = knoxss_validate,
        scan_timeout    = scan_timeout,
        max_findings    = max_findings,
        payload_file    = payload_file,
        show_progress   = not no_progress,
        test_json       = test_json,
        second_order    = second_order,
        js_crawl        = js_crawl,
        # Reports
        report_html     = report_html,
        report_csv      = report_csv,
        report_md       = report_md,
        report_sarif    = report_sarif,
        # Checkpoint
        checkpoint      = checkpoint,
        # vOVERPOWER new flags
        engine_version  = engine_version,
        test_csp_bypass = test_csp_bypass,
        test_prototype  = test_prototype,
        test_websocket  = test_websocket,
        test_template   = test_template,
        test_smuggling  = test_smuggling,
        browser_quirks  = browser_quirks,
        unicode_bypass  = unicode_bypass,
        dom_clobbering  = dom_clobbering,
        ai_assist       = ai_assist,
        waf_chain_depth = waf_chain_depth,
        # Fix #2 & #3
        dom_xss_scan    = dom_xss_scan,
        spa_crawl       = spa_crawl,
        spa_interact    = spa_interact,
    )

    set_verbose(verbose)

    # ─── Print scan config ───────────────────────────────────────────────────
    section("Scan Configuration")
    info(f"Targets:     {len(targets)}")
    info(f"Profile:     {profile}")
    info(f"Threads:     {threads}")
    info(f"Crawl depth: {depth}")
    info(f"WAF bypass:  {'Enabled' if config.waf_bypass else 'Disabled'}")
    if proxy:
        info(f"Proxy:       {proxy}")
    if blind_callback:
        info(f"Blind XSS:   {blind_callback}")
    if login_url:
        info(f"Auth:        {login_url}")
    if scope:
        info(f"Scope:       {', '.join(scope)}")
    extras = [f for f, v in [
        ("headers", test_headers), ("hpp", test_hpp), ("json", test_json),
        ("new_events_2025", test_new_events), ("parser_diff_2025", test_parser_diff),
        ("hpp_2025", test_hpp_2025),
        ("second-order", second_order), ("js-crawl", js_crawl),
    ] if v]
    if extras:
        info(f"Extra tests: {', '.join(extras)}")
    if verify_headless:
        info(f"Verification: headless Chromium enabled")

    # ─── Run ─────────────────────────────────────────────────────────────────
    # BUG FIX #9: default engine_version="v2" was incorrectly routing ALL scans to ScanEngineV3
    # even when user did not pass --engine-v3. Now V3 only activates with --engine-v3 flag explicitly.
    asyncio.run(_run(config, details, start_blind_server, use_v3=engine_v3))


async def _run(config: ScanConfig, print_details: bool, blind_server: bool, use_v3: bool = False):
    from scanner.engine_v3 import ScanEngineV3
    from scanner.engine_v2 import ScanEngineV2
    from scanner.blind_server import BlindXSSServer
    from scanner.verifier import HeadlessVerifier

    # ── Blind XSS listener ───────────────────────────────────────────────────
    bserver = None
    if blind_server:
        bserver = BlindXSSServer(port=8765)
        await bserver.start()
        if not config.blind_callback:
            config.blind_callback = "http://127.0.0.1:8765"

    # ── Headless verifier ────────────────────────────────────────────────────
    verifier = None
    if config.verify_headless:
        verifier = HeadlessVerifier()
        await verifier.start()

    section("Scanning")
    if use_v3:
        engine = ScanEngineV3(config)
        info("Engine: vOVERPOWER (ScanEngineV3) — 4.50B combinations")
    else:
        engine = ScanEngineV2(config)
        info("Engine: v1 (ScanEngineV2) — 152M combinations")
    start  = time.monotonic()

    try:
        findings = await engine.run()
    finally:
        await engine.close()
        if bserver:
            await bserver.stop()

    # ── Headless verification pass ────────────────────────────────────────────
    if verifier and findings:
        info(f"Verifying {len(findings)} findings in headless browser...")
        for f in findings:
            f.verified = await verifier.verify(f)
        await verifier.stop()
        verified_count = sum(1 for f in findings if f.verified)
        info(f"Headless verification: {verified_count}/{len(findings)} confirmed")

    elapsed = time.monotonic() - start

    # ── Reports ───────────────────────────────────────────────────────────────
    section("Results")
    reporter = Reporter(findings, config.targets, elapsed)
    reporter.print_summary()

    if print_details and findings:
        reporter.print_finding_details()

    saved = reporter.save_json(config.output)
    success(f"JSON report  → {saved}")

    if config.report_html:
        p = reporter.save_html(config.report_html)
        success(f"HTML report  → {p}")
    if config.report_csv:
        p = reporter.save_csv(config.report_csv)
        success(f"CSV report   → {p}")
    if config.report_md:
        p = reporter.save_md(config.report_md)
        success(f"MD report    → {p}")
    if config.report_sarif:
        p = reporter.save_sarif(config.report_sarif)
        success(f"SARIF report → {p}")

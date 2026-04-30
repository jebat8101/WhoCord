import re
import time
import requests
import shutil
import functools
import os
import sys
import threading
import subprocess as _sp
from datetime import datetime

# Constants
MAX_SCRAPE_WORKERS = 5
REQUEST_DELAY = 2.0
CACHE_DIR = "./investigation_cache"

DEBUG_MODE = False
_log_file = None

def debug_log(msg="", end="\n"):
    print(msg, end=end)
    if _log_file:
        _log_file.write(msg + end)
        _log_file.flush()

def debug_subprocess(cmd, **kwargs):
    """
    Run a command. In debug mode output streams live AND is captured.
    Content fields in JSON output are truncated to keep console clean.
    """
    def _filter_line(line):
        # Replace the ENTIRE "Content": "..." value (including escaped quotes)
        return re.sub(
            r'("Content"\s*:\s*)"(?:[^"\\]|\\.)*"',
            r'\1"<content truncated>"',
            line
        )

    if DEBUG_MODE:
        debug_log(f"[DEBUG] Running: {' '.join(cmd)}")

        # Pop timeout if present – we'll handle it with Popen + wait
        timeout = kwargs.pop('timeout', None)
        kwargs['stdout'] = _sp.PIPE
        kwargs['stderr'] = _sp.STDOUT
        kwargs.pop('capture_output', None)
        kwargs.pop('text', None)

        proc = _sp.Popen(cmd, **kwargs)

        captured_lines = []

        def reader():
            """Read lines from stdout, print them filtered, and store them."""
            for raw_line in iter(proc.stdout.readline, b''):
                line = raw_line.decode('utf-8', errors='replace')
                filtered = _filter_line(line)
                print(filtered, end='')
                captured_lines.append(line)      # store unfiltered for parsing
            proc.stdout.close()

        reader_thread = threading.Thread(target=reader, daemon=True)
        reader_thread.start()

        try:
            proc.wait(timeout=timeout)
        except _sp.TimeoutExpired:
            proc.kill()
            proc.wait()
            debug_log(f"[!] Command timed out after {timeout}s")
        finally:
            reader_thread.join(timeout=5)

        stdout_text = ''.join(captured_lines)

        result = _sp.CompletedProcess(args=cmd, returncode=proc.returncode,
                                      stdout=stdout_text, stderr='')
        return result, stdout_text, ''
    else:
        # Non-debug: silent capture
        kwargs['capture_output'] = True
        kwargs['text'] = True
        result = _sp.run(cmd, **kwargs)
        return result, result.stdout, result.stderr

def init_debug_log(target_id):
    global _log_file
    if DEBUG_MODE:
        log_dir = os.path.join(CACHE_DIR, "debug_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(
            log_dir,
            f"debug_{target_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        _log_file = open(log_path, 'w', encoding='utf-8')
        debug_log(f"=== Debug log started for target {target_id} ===")

# =================== HTTP SESSION SETUP ===================
def get_http_session(retries=3, backoff_factor=1):
    session = requests.Session()
    retry_strategy = requests.adapters.Retry(
        total=retries, backoff_factor=backoff_factor,
        status_forcelist=[429,500,502,503,504], allowed_methods=["GET","POST"])
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

http_session = get_http_session()

def _get_ip_via_doh(host, dns="https://dns.google/resolve"):
    try:
        resp = requests.get(dns, params={"name":host,"type":"A"}, timeout=5)
        if resp.status_code==200:
            for a in resp.json().get("Answer",[]):
                if a.get("type")==1: return a["data"]
    except: pass
    return None

def _force_github_resolution(session, host, resolved_ip):
    class ForceIPHTTPAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs['assert_hostname'] = host
            super().init_poolmanager(*args, **kwargs)
        def cert_verify(self, conn, url, verify, cert):
            conn.assert_hostname = host
            return super().cert_verify(conn, url, verify, cert)
    adapter = ForceIPHTTPAdapter()
    session.mount(f"https://{host}/", adapter)
    orig = session.request
    def patched(method, url, **kw):
        if host in url:
            url = url.replace(f"https://{host}", f"https://{resolved_ip}")
        return orig(method, url, **kw)
    session.request = patched

def _get_github_session():
    sess = get_http_session()
    try:
        test = sess.get("https://api.github.com", timeout=5)
        if test.status_code == 200 and "current_user_url" in test.json():
            return sess
    except:
        pass
    print("GitHub API unreachable normally – trying DoH...")
    new_ip = _get_ip_via_doh("api.github.com")
    if new_ip:
        print(f"Using IP {new_ip} for api.github.com")
        _force_github_resolution(sess, "api.github.com", new_ip)
    return sess

github_session = _get_github_session()

# =================== UTILITIES ===================
def resilient_task(max_retries=3, backoff_factor=1.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try: return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    wait = backoff_factor**attempt
                    print(f"    [!] {func.__name__} failed (attempt {attempt+1}/{max_retries}), retrying in {wait:.1f}s...")
                    time.sleep(wait)
            print(f"    [X] {func.__name__} permanently failed: {last_exc}")
            return None
        return wrapper
    return decorator

def tool_available(name):
    return shutil.which(name) is not None

def clean_username(raw: str) -> str:
    raw = raw.strip()
    cleaned = re.sub(r'^\.+', '', raw)
    return cleaned if cleaned else raw

EXT_TOOLS = {
    "sherlock": "pip install sherlock-project",
    "maigret": "pip install maigret",
    "holehe": "pip install holehe",
    "h8mail": "pip install h8mail",
    "gitfive": "pip install gitfive",
    "naminter": "pip install naminter",
    "socid_extractor": "pip install socid-extractor",
    "socialscan": "pip install socialscan",
    "linkook": "pip install linkook",
    "sociopath": "pip install sociopath",
    "sharetrace": "pip install sharetrace",
    "scylla": "pip install scylla",
    "phoneinfoga": "pip install phoneinfoga",
    "whois": "apt-get install whois (or brew install whois)",
}

def check_dependencies():
    missing = []
    for tool, install_cmd in EXT_TOOLS.items():
        if not shutil.which(tool):
            missing.append(f"{tool}: {install_cmd}")
    if missing:
        print("Missing external tools:")
        for m in missing:
            print(f"  - {m}")
        print("Please install them before running investigations.\n")
    return missing

#!/usr/bin/env python3
"""
Selenium Compilation Live Monitor
Permite ver el progreso en tiempo real tanto en la consola como en una interfaz web visual moderna.
"""

import os
import sys
import time
import json
import urllib.request
import http.server
import socketserver
import threading
from pathlib import Path

OUT_DIR = Path(r"C:\src\chromium\src\out\thorium")
PORT_FILE = OUT_DIR / ".siso_port"

def get_siso_port():
    if not PORT_FILE.exists():
        return None
    try:
        content = PORT_FILE.read_text().strip()
        if ":" in content:
            return content.split(":")[-1]
        return content
    except Exception:
        return None

def fetch_progress():
    port = get_siso_port()
    if not port:
        return None
    url = f"http://127.0.0.1:{port}/api/progress"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SeleniumMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def format_eta(seconds):
    if seconds <= 0:
        return "Calculando..."
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m {secs}s"

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/status":
            data = fetch_progress()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data or {}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Selenium 159 - Monitor de Compilación</title>
    <link rel="icon" href="https://chromium.googlesource.com/chromium/src/+/refs/heads/main/chrome/app/theme/chromium/product_logo_32.png?format=ICON">
    <style>
        :root {
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text-main: #f0f6fc;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --accent-green: #3fb950;
            --bar-bg: #21262d;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            padding: 24px;
            display: flex;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 900px;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        .title {
            font-size: 24px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .badge {
            background-color: rgba(56, 139, 253, 0.15);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid rgba(56, 139, 253, 0.4);
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--accent-green);
            display: inline-block;
            box-shadow: 0 0 8px var(--accent-green);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }
        .card-label {
            color: var(--text-muted);
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .card-value {
            font-size: 26px;
            font-weight: 600;
            color: var(--text-main);
        }
        .progress-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: 500;
        }
        .progress-bar-bg {
            height: 16px;
            background: var(--bar-bg);
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #1f6feb, #388bfd, #3fb950);
            width: 0%;
            transition: width 0.4s ease;
        }
        .progress-desc {
            margin-top: 10px;
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }
        .active-tasks-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }
        .active-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 14px;
            color: var(--text-main);
        }
        .task-list {
            list-style: none;
            padding: 0;
            margin: 0;
            max-height: 380px;
            overflow-y: auto;
        }
        .task-item {
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px;
            padding: 8px 10px;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .task-item:last-child {
            border-bottom: none;
        }
        .task-name {
            color: var(--accent);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 12px;
        }
        .task-dur {
            color: var(--text-muted);
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <span class="status-dot"></span>
                Selenium Browser (M159.0.8133.1)
                <span class="badge">AVX2 + Helium</span>
            </div>
            <div id="status-text" style="color: var(--accent-green); font-size: 14px;">Compilando activamente</div>
        </div>

        <div class="stats-grid">
            <div class="card">
                <div class="card-label">Progreso Global</div>
                <div class="card-value" id="overall-pct">0%</div>
            </div>
            <div class="card">
                <div class="card-label">Pasos Completados</div>
                <div class="card-value" id="steps-done">0</div>
            </div>
            <div class="card">
                <div class="card-label">Pasos Restantes</div>
                <div class="card-value" id="steps-remaining">0</div>
            </div>
            <div class="card">
                <div class="card-label">Velocidad Aprox.</div>
                <div class="card-value" id="speed-text">-- pasos/min</div>
            </div>
        </div>

        <div class="progress-box">
            <div class="progress-header">
                <span>Fase Actual de Construcción</span>
                <span id="active-pct-text">0%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progress-bar"></div>
            </div>
            <div class="progress-desc">
                <span id="cache-info">Caché previa: 0 pasos</span>
                <span id="eta-text">Calculando tiempo restante...</span>
            </div>
        </div>

        <div class="active-tasks-box">
            <div class="active-title">Hilos de Compilación Activos (Clang / Siso)</div>
            <ul class="task-list" id="task-list">
                <li class="task-item" style="color: var(--text-muted);">Cargando objetivos activos...</li>
            </ul>
        </div>
    </div>

    <script>
        let lastDone = 0;
        let lastTime = Date.now();
        let speed = 0;

        async function updateProgress() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                if (!data || !data.total) {
                    document.getElementById('status-text').innerText = "Esperando Siso...";
                    return;
                }

                const done = data.done || 0;
                const total = data.total || 1;
                const skipped = data.skipped || 0;
                const grandTotal = total + skipped;
                const grandDone = done + skipped;

                const overallPct = ((grandDone / grandTotal) * 100).toFixed(1);
                const activePct = ((done / total) * 100).toFixed(1);

                document.getElementById('overall-pct').innerText = overallPct + '%';
                document.getElementById('active-pct-text').innerText = done.toLocaleString() + ' / ' + total.toLocaleString() + ' (' + activePct + '%)';
                document.getElementById('progress-bar').style.width = activePct + '%';

                document.getElementById('steps-done').innerText = grandDone.toLocaleString();
                const remaining = total - done;
                document.getElementById('steps-remaining').innerText = remaining.toLocaleString();

                document.getElementById('cache-info').innerText = 'Reutilizado en caché: ' + skipped.toLocaleString() + ' pasos';

                // Speed & ETA
                const now = Date.now();
                if (lastDone > 0 && done > lastDone) {
                    const diffSteps = done - lastDone;
                    const diffMinutes = (now - lastTime) / 60000;
                    if (diffMinutes > 0) {
                        const currentSpeed = diffSteps / diffMinutes;
                        speed = speed === 0 ? currentSpeed : (speed * 0.7 + currentSpeed * 0.3);
                        document.getElementById('speed-text').innerText = Math.round(speed) + ' pasos/min';
                        const remMins = Math.round(remaining / speed);
                        const hours = Math.floor(remMins / 60);
                        const mins = remMins % 60;
                        document.getElementById('eta-text').innerText = 'Tiempo restante aprox: ' + (hours > 0 ? hours + 'h ' + mins + 'm' : mins + 'm');
                    }
                }
                lastDone = done;
                lastTime = now;

                // Active steps
                const list = document.getElementById('task-list');
                list.innerHTML = '';
                const active = (data.active_steps || []).slice(0, 16);
                if (active.length === 0) {
                    list.innerHTML = '<li class="task-item" style="color: var(--text-muted);">Sin tareas en cola inmediata</li>';
                } else {
                    active.forEach(item => {
                        const li = document.createElement('li');
                        li.className = 'task-item';
                        li.innerHTML = '<span class="task-name">' + (item.Desc || item.ID) + '</span><span class="task-dur">' + (item.Dur || '') + '</span>';
                        list.appendChild(li);
                    });
                }
            } catch (err) {
                console.error(err);
            }
        }

        setInterval(updateProgress, 2000);
        updateProgress();
    </script>
</body>
</html>
"""

def run_console_dashboard():
    os.system("cls" if os.name == "nt" else "clear")
    print("==============================================================================")
    print("           MONITOR VISUAL DE COMPILACIÓN: SELENIUM (CHROMIUM M159)            ")
    print("==============================================================================")
    last_done = 0
    last_time = time.time()
    speed = 0

    while True:
        data = fetch_progress()
        if not data:
            print("\r[ESPERANDO] Siso no está reportando progreso activo...", end="", flush=True)
            time.sleep(2)
            continue

        done = data.get("done", 0)
        total = data.get("total", 1)
        skipped = data.get("skipped", 0)
        grand_total = total + skipped
        grand_done = done + skipped
        overall_pct = (grand_done / grand_total) * 100
        active_pct = (done / total) * 100

        now = time.time()
        if last_done > 0 and done > last_done:
            diff_steps = done - last_done
            diff_time = (now - last_time) / 60.0
            if diff_time > 0:
                current_speed = diff_steps / diff_time
                speed = current_speed if speed == 0 else (speed * 0.7 + current_speed * 0.3)

        last_done = done
        last_time = now

        eta_str = "--"
        if speed > 0:
            rem_sec = ((total - done) / speed) * 60.0
            eta_str = format_eta(rem_sec)

        bar_len = 35
        filled = int((active_pct / 100.0) * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        active = data.get("active_steps", [])
        active_desc = active[0].get("Desc", "Compilando...") if active else "Procesando..."
        if len(active_desc) > 65:
            active_desc = active_desc[:62] + "..."

        sys.stdout.write("\033[H")
        print("==============================================================================")
        print(f"  SELENIUM BROWSER (M159.0.8133.1 AVX2) - COMPILACIÓN EN CURSO               ")
        print("==============================================================================")
        print(f"  Progreso Global Total : [{bar}] {overall_pct:5.1f}% ({grand_done:,} / {grand_total:,})")
        print(f"  Fase Activa Pendiente : {active_pct:5.1f}% ({done:,} / {total:,}) | Caché: {skipped:,}")
        print(f"  Velocidad Actual      : {int(speed):3d} pasos/min  |  Tiempo Restante: {eta_str}")
        print("------------------------------------------------------------------------------")
        print(f"  Actividad de núcleos  : {len(active)} tareas concurrentes")
        print(f"  Actual                : {active_desc}")
        print("==============================================================================")
        print("  Presiona Ctrl+C para salir del monitor (la compilación continuará).        \n")
        sys.stdout.flush()
        time.sleep(2)

def start_web_server(port=8080):
    server = socketserver.TCPServer(("127.0.0.1", port), DashboardHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return port

if __name__ == "__main__":
    if "--server" in sys.argv:
        port = start_web_server(8080)
        print(f"Servidor web del Monitor iniciado en: http://127.0.0.1:{port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    elif "--both" in sys.argv:
        port = start_web_server(8080)
        print(f"Panel web disponible en: http://127.0.0.1:{port}")
        time.sleep(1)
        run_console_dashboard()
    else:
        run_console_dashboard()

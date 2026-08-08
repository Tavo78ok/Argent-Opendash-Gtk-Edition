#!/usr/bin/env python3
"""
Argent Opendash Gtk4 libadwaita v3.1 – Argent Platinum Edition
Monitor, Optimizador y Gestor del Sistema

ARQUITECTURA v3.1
  Sección 1 — Constantes y paleta
  Sección 2 — CSS
  Sección 3 — Helpers UI
  Sección 4 — Capa de hardware  (toda la lógica de sistema aquí)
  Sección 5 — Widgets Cairo
  Sección 6 — Ventana principal
    6a  Construcción de pestañas  (solo UI)
    6b  Manejadores de eventos
    6c  Hilos de datos  (con timeout en cada llamada)
    6d  Acciones del sistema
    6e  Tick UI
  Sección 7 — Entrada de la app

Tavo78ok · MIT License
https://github.com/Tavo78ok/Argent-Opendash-Gtk4-libadwaita
"""

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 1 — CONSTANTES Y PALETA
# ═══════════════════════════════════════════════════════════
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

import os, math, re, stat, threading, subprocess, platform
from collections import deque
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import psutil

APP_ID      = 'io.github.Tavo78ok.ArgentOpendash'
APP_NAME    = 'Argent Opendash Gtk4 libadwaita'
APP_VERSION = '3.1'
BINARY      = 'argent-opendash'
AUTOSTART_F = os.path.expanduser('~/.config/autostart/argent-opendash.desktop')
PERFIL_F    = os.path.expanduser('~/.opendash_perfil')

# Paleta neon (r, g, b) — 0.0–1.0
C_GREEN  = (0.00, 1.00, 0.64)
C_CYAN   = (0.00, 0.81, 1.00)
C_AMBER  = (0.98, 0.75, 0.18)
C_RED    = (1.00, 0.27, 0.27)
C_PURPLE = (0.65, 0.55, 0.98)

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 2 — CSS
# ═══════════════════════════════════════════════════════════
APP_CSS = """
.od-bg       { background-color: #0d0f14; }
.od-card     { background-color: #141720; border-radius: 14px;
               border: 1px solid rgba(255,255,255,0.06); }
.od-card-sm  { background-color: #141720; border-radius: 10px;
               border: 1px solid rgba(255,255,255,0.05); }
.od-detail   { background-color: #0d1018; border-radius: 12px;
               border: 1px solid rgba(255,255,255,0.08); }
.od-value    { font-size: 26px; font-weight: 900; color: white; }
.od-unit     { font-size: 13px; font-weight: 600;
               color: rgba(255,255,255,0.38); }
.od-sublabel { font-size: 10px; font-weight: 700; letter-spacing: 2px;
               color: rgba(255,255,255,0.32); }
.od-section  { font-size: 10px; font-weight: 800; letter-spacing: 4px;
               color: rgba(255,255,255,0.22); }
.od-mono     { font-family: monospace; font-size: 12px;
               color: rgba(255,255,255,0.72); }
.od-desc     { font-size: 11px; color: rgba(255,255,255,0.45); }
.od-warn     { color: #fbbf24; font-size: 11px; }
.od-tag      { font-size: 10px; font-weight: 700; letter-spacing: 1px;
               border-radius: 6px; padding: 2px 8px; }
.od-tag-on   { background-color: rgba(0,255,163,0.16); color: #00ffa3; }
.od-tag-off  { background-color: rgba(255,255,255,0.07);
               color: rgba(255,255,255,0.40); }
.od-tag-flat { background-color: rgba(0,207,255,0.14); color: #00cfff; }
.c-green  { color: #00ffa3; }
.c-cyan   { color: #00cfff; }
.c-amber  { color: #fbbf24; }
.c-red    { color: #ff4444; }
.c-purple { color: #a68bf8; }
.od-btn-start   { background-color: rgba(0,255,163,0.12); color: #00ffa3;
                  border-radius: 8px; padding: 4px 12px; }
.od-btn-stop    { background-color: rgba(255,68,68,0.14); color: #ff7070;
                  border-radius: 8px; padding: 4px 12px; }
.od-btn-action  { background-color: #00ffa3; color: #060a08;
                  font-weight: 800; border-radius: 8px; }
.od-btn-install { background-color: rgba(0,207,255,0.14); color: #00cfff;
                  border-radius: 8px; padding: 4px 12px; }
.od-profile-on  { background-color: rgba(0,255,163,0.16); color: #00ffa3;
                  border: 1px solid rgba(0,255,163,0.40);
                  border-radius: 12px; }
levelbar trough              { background-color: #1c2030;
                               border-radius: 4px; min-height: 8px; }
levelbar trough block.filled { border-radius: 4px; }
levelbar.warn trough block.filled { background-color: #fbbf24; }
levelbar.err  trough block.filled { background-color: #ff4444; }
scale trough           { background-color: #1c1f2a; min-height: 5px;
                         border-radius: 3px; }
scale trough highlight { border-radius: 3px; }
scrollbar               { background-color: transparent; }
scrollbar slider        { background-color: rgba(255,255,255,0.13);
                          border-radius: 4px;
                          min-width: 5px; min-height: 5px; }
list     { background-color: transparent; }
list row { background-color: transparent; }
list row:selected { background-color: rgba(0,255,163,0.12); }
"""

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 3 — HELPERS UI
# ═══════════════════════════════════════════════════════════
def lbl(text, css=None, markup=False, xalign=None,
        selectable=False, wrap=False):
    w = Gtk.Label()
    if markup: w.set_markup(text)
    else:      w.set_label(text)
    if css:
        for c in css.split(): w.add_css_class(c)
    if xalign is not None: w.set_xalign(xalign)
    if selectable: w.set_selectable(True)
    if wrap:
        w.set_wrap(True); w.set_max_width_chars(54)
    return w

def vbox(spacing=0, css=None):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
    if css:
        for c in css.split(): b.add_css_class(c)
    return b

def hbox(spacing=0, css=None):
    b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)
    if css:
        for c in css.split(): b.add_css_class(c)
    return b

def spacer():
    s = Gtk.Box(); s.set_hexpand(True); return s

def hsep():
    s = Gtk.Separator()
    s.set_margin_top(4); s.set_margin_bottom(4)
    return s

def clear(widget):
    ch = widget.get_first_child()
    while ch:
        nx = ch.get_next_sibling()
        widget.remove(ch); ch = nx

def card(inner_widget, mt=12, mb=12, ms=14, me=14):
    """Envuelve un widget en una od-card con márgenes."""
    c = vbox(css='od-card')
    inner_widget.set_margin_top(mt); inner_widget.set_margin_bottom(mb)
    inner_widget.set_margin_start(ms); inner_widget.set_margin_end(me)
    c.append(inner_widget)
    return c

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 4 — CAPA DE HARDWARE
# ═══════════════════════════════════════════════════════════
_hw_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='hw')

def safe_hw(fn, *args, timeout=2.5, default=None):
    """Ejecuta fn(*args) con timeout estricto. Nunca bloquea."""
    try:
        return _hw_pool.submit(fn, *args).result(timeout=timeout)
    except Exception:
        return default

def hw_cmd(*args, timeout=4):
    """Subprocess seguro con timeout."""
    try:
        return subprocess.check_output(
            list(args), text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout).strip()
    except Exception:
        return ''

def hw_cpu_percent():
    return safe_hw(psutil.cpu_percent, interval=None, default=0.0)

def hw_memory():
    return safe_hw(psutil.virtual_memory, default=None)

def hw_disk_root():
    return safe_hw(psutil.disk_usage, '/', default=None)

def hw_net_io():
    return safe_hw(psutil.net_io_counters, default=None)

def hw_net_addrs():
    return safe_hw(psutil.net_if_addrs, default={})

def hw_temp():
    """Temperatura con timeout corto — puede bloquearse en hardware antiguo."""
    def _read():
        temps = psutil.sensors_temperatures()
        for key in ('coretemp','k10temp','zenpower','cpu_thermal','acpitz'):
            if key in temps and temps[key]:
                return temps[key][0].current
        return None
    return safe_hw(_read, timeout=1.5, default=None)

def hw_partitions():
    """Particiones con timeout — puede ser lento en algunos sistemas."""
    skip_fs = {'tmpfs','devtmpfs','squashfs','overlay','proc',
               'sysfs','cgroup','cgroup2','pstore','efivarfs',''}
    def _read():
        result = []
        for p in psutil.disk_partitions(all=False):
            if p.fstype in skip_fs: continue
            try:
                u = psutil.disk_usage(p.mountpoint)
                result.append({
                    'mount':  p.mountpoint,
                    'device': p.device.replace('/dev/', ''),
                    'fstype': p.fstype,
                    'total':  u.total / (1024**3),
                    'used':   u.used  / (1024**3),
                    'free':   u.free  / (1024**3),
                    'pct':    u.percent})
            except Exception:
                pass
        return result
    return safe_hw(_read, timeout=3.0, default=[])

def hw_procs_top():
    """Top procesos por CPU directo sin saturar el thread pool."""
    try:
        procs = sorted(
            psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
            key=lambda p: p.info['cpu_percent'] or 0,
            reverse=True)
        hdr   = f"{'PID':<8}{'PROCESO':<22}{'CPU%':<8}{'RAM%'}\n" + '─'*50 + '\n'
        rows  = ''.join(
            f"{p.info['pid']:<8}{p.info['name'][:20]:<22}"
            f"{p.info['cpu_percent'] or 0:<8.1f}"
            f"{p.info['memory_percent'] or 0:.1f}%\n"
            for p in procs[:15])
        return hdr + rows
    except Exception:
        return "Cargando procesos..."

def hw_cpu_model():
    try:
        for line in open('/proc/cpuinfo'):
            if 'model name' in line:
                return line.split(':')[1].strip()[:44]
    except Exception:
        pass
    return platform.processor()[:44] or 'N/A'

def hw_get_volume():
    try:
        out = hw_cmd('pactl', 'get-sink-volume', '@DEFAULT_SINK@')
        m   = re.search(r'(\d+)%', out)
        return int(m.group(1)) if m else 50
    except Exception:
        return 50

def hw_set_volume(pct):
    try:
        subprocess.run(
            ['pactl','set-sink-volume','@DEFAULT_SINK@',f'{int(pct)}%'],
            capture_output=True, timeout=2)
    except Exception:
        pass

def _backlight_dev():
    try:
        devs = os.listdir('/sys/class/backlight')
        if devs: return '/sys/class/backlight/' + devs[0]
    except Exception:
        pass
    return None

def hw_get_brightness():
    dev = _backlight_dev()
    if dev:
        try:
            cur = int(open(f'{dev}/brightness').read())
            mx  = int(open(f'{dev}/max_brightness').read())
            return cur/mx*100 if mx else 100.0
        except Exception:
            pass
    try:
        cur = hw_cmd('brightnessctl','get')
        mx  = hw_cmd('brightnessctl','max')
        if cur and mx and int(mx) > 0:
            return int(cur)/int(mx)*100
    except Exception:
        pass
    try:
        out = hw_cmd('xrandr','--verbose')
        m   = re.search(r'Brightness:\s*([\d.]+)', out)
        if m: return float(m.group(1))*100
    except Exception:
        pass
    return 100.0

def hw_set_brightness(pct):
    pct = max(1, min(100, int(pct)))
    try:
        r = subprocess.run(
            ['brightnessctl','set',f'{pct}%'],
            capture_output=True, timeout=2)
        if r.returncode == 0: return
    except Exception:
        pass
    dev = _backlight_dev()
    if dev:
        try:
            mx = int(open(f'{dev}/max_brightness').read())
            v  = max(1, int(mx*pct/100))
            try: open(f'{dev}/brightness','w').write(str(v)); return
            except PermissionError:
                subprocess.run(['pkexec','tee',f'{dev}/brightness'],
                               input=str(v), text=True,
                               capture_output=True, timeout=5)
                return
        except Exception:
            pass
    try:
        b = pct/100
        out = hw_cmd('xrandr')
        for mon in re.findall(r'^(\S+) connected', out, re.MULTILINE):
            subprocess.run(
                ['xrandr','--output',mon,'--brightness',f'{b:.2f}'],
                capture_output=True, timeout=2)
    except Exception:
        pass

def hw_flatpak_available():
    return bool(hw_cmd('which','flatpak'))

def hw_powerprofiles_available():
    return bool(hw_cmd('which','powerprofilesctl'))

def _run_in_terminal(script, need_root=True):
    path = '/tmp/argent_od_script.sh'
    try:
        with open(path,'w') as f: f.write(script)
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        return
    base_cmd = ['pkexec','bash',path] if need_root else ['bash',path]
    for term in ['x-terminal-emulator','mate-terminal','gnome-terminal',
                 'xfce4-terminal','xterm','konsole']:
        try:
            if term in ['gnome-terminal', 'mate-terminal', 'xfce4-terminal']:
                subprocess.Popen([term, '--'] + base_cmd)
            else:
                subprocess.Popen([term, '-e', ' '.join(base_cmd)])
            return
        except FileNotFoundError:
            continue

def run_bg(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 5 — WIDGETS CAIRO
# ═══════════════════════════════════════════════════════════
class RingMeter(Gtk.DrawingArea):
    def __init__(self, color, size=76):
        super().__init__()
        self._color = color; self._val = 0.0
        self.set_content_width(size); self.set_content_height(size)
        self.set_draw_func(self._draw, None)

    def set_value(self, v):
        self._val = max(0.0, min(1.0, float(v))); self.queue_draw()

    def _draw(self, _, cr, w, h, __):
        cx, cy = w/2, h/2
        r  = min(w,h)/2 - 7
        lw = max(5, int(r*0.13))
        st = math.pi*0.75; sp = math.pi*1.5
        cr.set_line_width(lw)
        cr.arc(cx,cy,r,st,st+sp)
        cr.set_source_rgba(0.13,0.15,0.20,1); cr.stroke()
        if self._val > 0.01:
            end = st + self._val*sp
            rr,g,b = self._color
            cr.set_line_width(lw+6); cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,0.07); cr.stroke()
            cr.set_line_width(lw);   cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,1.0); cr.stroke()

class HistoryGraph(Gtk.DrawingArea):
    def __init__(self, color, label='', maxlen=60, height=70):
        super().__init__()
        self._color = color; self._label = label
        self._data  = deque([0.0]*maxlen, maxlen=maxlen)
        self.set_content_height(height); self.set_hexpand(True)
        self.set_draw_func(self._draw, None)

    def push(self, pct):
        self._data.append(max(0.0,min(100.0,float(pct)))/100.0)
        self.queue_draw()

    def _draw(self, _, cr, w, h, __):
        cr.set_source_rgba(0.06,0.07,0.10,1)
        cr.rectangle(0,0,w,h); cr.fill()
        pts = list(self._data); n = len(pts)
        if n < 2: return
        step = w/(n-1); rr,g,b = self._color; pad = h*0.08
        def py(v): return h-pad-v*(h-2*pad)
        cr.set_line_width(0.5)
        for p in (0.25,0.5,0.75):
            cr.set_source_rgba(1,1,1,0.04)
            cr.move_to(0,py(p)); cr.line_to(w,py(p)); cr.stroke()
        cr.move_to(0,h)
        for i,v in enumerate(pts): cr.line_to(i*step,py(v))
        cr.line_to((n-1)*step,h); cr.close_path()
        cr.set_source_rgba(rr,g,b,0.10); cr.fill()
        cr.move_to(0,py(pts[0]))
        for i,v in enumerate(pts[1:],1): cr.line_to(i*step,py(v))
        cr.set_source_rgba(rr,g,b,1.0); cr.set_line_width(1.7); cr.stroke()
        cr.set_source_rgba(rr,g,b,0.85); cr.set_font_size(10)
        cr.move_to(7,14); cr.show_text(f'{self._label}  {pts[-1]*100:.0f}%')

class MetricCard(Gtk.Box):
    def __init__(self, title, color, ring_size=76):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class('od-card'); self.set_hexpand(True)
        inner = vbox(spacing=4)
        inner.set_margin_top(10); inner.set_margin_bottom(10)
        inner.set_margin_start(8);  inner.set_margin_end(8)
        self._ring = RingMeter(color, ring_size)
        self._ring.set_halign(Gtk.Align.CENTER); inner.append(self._ring)
        self._val  = lbl('—','od-value')
        self._val.set_halign(Gtk.Align.CENTER); inner.append(self._val)
        self._sub  = lbl(title.upper(),'od-sublabel')
        self._sub.set_halign(Gtk.Align.CENTER); inner.append(self._sub)
        self.append(inner)

    def update(self, txt, pct):
        self._val.set_label(txt); self._ring.set_value(pct/100)

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 6 — VENTANA PRINCIPAL
# ═══════════════════════════════════════════════════════════
class OpenDashWindow(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(f'{APP_NAME} v{APP_VERSION}')
        self.set_default_size(980, 680)
        self.set_icon_name('argent-opendash')

        self._dark       = True
        self._gamer_btns = []
        self._part_bars  = {}
        self._parts_ok   = False
        self._tray_icon  = None
        self._tray_on    = False
        self._all_apt    = []
        self._all_flat   = []
        self._sel_apt    = None
        self._sel_flat   = None
        self._services   = []

        self._br_timer = self._vol_timer = None
        self._br_pend  = self._vol_pend  = None

        self._m   = {}
        self._procs_txt = '...'
        self._tick_n = 0

        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK)
        self._apply_css()
        self._build_ui()
        self.connect('close-request', self._on_close)

        threading.Thread(target=self._hw_loop, daemon=True).start()
        threading.Thread(target=self._procs_loop, daemon=True).start()

        GLib.timeout_add(1000,  self._tick)
        GLib.timeout_add(500,   self._init_heavy)

    def _apply_css(self):
        p = Gtk.CssProvider(); p.load_from_data(APP_CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_ui(self):
        tb = Adw.ToolbarView()
        hdr = Adw.HeaderBar()
        hdr.set_title_widget(Adw.WindowTitle.new(APP_NAME, f'v{APP_VERSION}'))
        self._theme_btn = Gtk.Button(icon_name='weather-clear-night-symbolic')
        self._theme_btn.set_tooltip_text('Cambiar tema')
        self._theme_btn.connect('clicked', self._toggle_theme)
        hdr.pack_end(self._theme_btn); tb.add_top_bar(hdr)

        self._tabs = Adw.TabView()
        tab_bar = Adw.TabBar(); tab_bar.set_view(self._tabs)
        tb.add_top_bar(tab_bar)

        self._toast_ov = Adw.ToastOverlay()
        self._toast_ov.set_child(self._tabs)
        tb.set_content(self._toast_ov)
        self.set_content(tb)

        for build_fn, title, icon in [
            (self._tab_dashboard,  'Dashboard',  'computer-symbolic'),
            (self._tab_monitor,    'Monitor',    'utilities-system-monitor-symbolic'),
            (self._tab_gamer,      'Gamer',      'applications-games-symbolic'),
            (self._tab_software,   'Software',   'system-software-install-symbolic'),
            (self._tab_inicio,     'Inicio',     'system-run-symbolic'),
            (self._tab_servicios,  'Servicios',  'preferences-system-symbolic'),
            (self._tab_controles,  'Controles',  'preferences-desktop-symbolic'),
        ]:
            sc = Gtk.ScrolledWindow()
            sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sc.set_child(build_fn())
            pg = self._tabs.append(sc)
            pg.set_title(title)
            pg.set_icon(Gio.ThemedIcon.new(icon))

    def _toast(self, msg):
        t = Adw.Toast.new(msg); t.set_timeout(3)
        self._toast_ov.add_toast(t)

    def _tab_dashboard(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=8)
        inner.set_margin_top(10); inner.set_margin_bottom(10)
        inner.set_margin_start(14); inner.set_margin_end(14)

        hdr = hbox(spacing=10)
        hdr.append(lbl('ESTADO DEL SISTEMA','od-section'))
        hdr.append(spacer())
        btn_ram = Gtk.Button(label='⚡ Optimizar RAM')
        btn_ram.add_css_class('od-btn-action')
        btn_ram.connect('clicked', self._do_optimize_ram)
        btn_cln = Gtk.Button(label='🧹 Limpieza')
        btn_cln.add_css_class('od-btn-action')
        btn_cln.connect('clicked', self._do_clean)
        hdr.append(btn_ram); hdr.append(btn_cln)
        inner.append(hdr)

        cards = hbox(spacing=10)
        self._c_cpu  = MetricCard('CPU',   C_GREEN)
        self._c_ram  = MetricCard('RAM',   C_CYAN)
        self._c_disk = MetricCard('Disco', C_AMBER)
        self._c_temp = MetricCard('Temp',  C_RED)
        for c in (self._c_cpu,self._c_ram,self._c_disk,self._c_temp):
            cards.append(c)
        inner.append(cards)

        graphs = hbox(spacing=10)
        for color, attr, label in (
            (C_GREEN,  '_g_cpu', 'CPU'),
            (C_CYAN,   '_g_ram', 'RAM'),
            (C_PURPLE, '_g_net', 'Red KB/s'),
        ):
            g = HistoryGraph(color, label)
            setattr(self, attr, g)
            wrap = vbox(css='od-card'); wrap.set_hexpand(True)
            p = vbox()
            p.set_margin_top(8); p.set_margin_bottom(8)
            p.set_margin_start(10); p.set_margin_end(10)
            p.append(g); wrap.append(p); graphs.append(wrap)
        inner.append(graphs)

        pc = vbox()
        pc.set_margin_top(8); pc.set_margin_bottom(8)
        pc.set_margin_start(12); pc.set_margin_end(12)
        pc.append(lbl('💾  PARTICIONES','od-section'))
        self._parts_box = vbox(spacing=6)
        pc.append(self._parts_box)
        inner.append(card(pc, 10, 10, 12, 12))

        sc = vbox()
        sc.set_margin_top(8); sc.set_margin_bottom(8)
        sc.set_margin_start(14); sc.set_margin_end(14)
        sc.append(lbl('🛡️  ESPECIFICACIONES DEL SISTEMA','od-section'))
        self._info_lbl = lbl('Cargando...','od-mono',xalign=0,selectable=True)
        sc.append(self._info_lbl)
        self._ip_lbl = lbl('—','od-mono',xalign=0)
        sc.append(self._ip_lbl)
        inner.append(card(sc, 10, 10, 14, 14))

        root.append(inner); return root

    def _tab_monitor(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=10)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        inner.append(lbl('MONITOR DETALLADO','od-section'))

        row = hbox(spacing=10)
        tc = vbox(spacing=6)
        tc.set_hexpand(True)
        tc.append(lbl('🌡️  TEMPERATURA','od-sublabel'))
        self._temp_lbl = lbl('—','od-mono',xalign=0); tc.append(self._temp_lbl)
        self._g_temp = HistoryGraph(C_RED,'TEMP °C',height=65)
        tc.append(self._g_temp)
        row.append(card(tc, 10, 10, 12, 12))

        nc = vbox(spacing=6)
        nc.set_hexpand(True)
        nc.append(lbl('🌐  RED','od-sublabel'))
        self._net_lbl = lbl('—','od-mono',xalign=0); nc.append(self._net_lbl)
        self._g_net_m = HistoryGraph(C_PURPLE,'KB/s',height=65)
        nc.append(self._g_net_m)
        row.append(card(nc, 10, 10, 12, 12))
        inner.append(row)

        inner.append(lbl('🔍  PROCESOS (ORDENADOS POR CPU)','od-section'))
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(280)
        pc = vbox()
        pc.set_margin_top(10); pc.set_margin_bottom(10)
        pc.set_margin_start(14); pc.set_margin_end(14)
        self._proc_lbl = lbl('—','od-mono',xalign=0,selectable=True)
        pc.append(self._proc_lbl)
        wrap = vbox(css='od-card'); wrap.append(pc)
        sc.set_child(wrap); inner.append(sc)
        root.append(inner); return root

    def _tab_gamer(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=12)
        inner.set_margin_top(16); inner.set_margin_bottom(16)
        inner.set_margin_start(30); inner.set_margin_end(30)
        inner.append(lbl(
            f'<span size="18000" weight="900" foreground="#00ffa3">'
            f'🚀  OPTIMIZACIÓN DE RENDIMIENTO</span>',markup=True))
        inner.append(lbl('Seleccioná un perfil de energía.','od-unit'))

        self._gamer_btns = []
        for key, icon, title, desc in [
            ('power-saver','🍃','MODO AHORRO',
             'Reduce frecuencia del CPU. Ideal para batería y silencio.'),
            ('balanced','⚖️','MODO BALANCEADO',
             'Equilibrio inteligente entre temperatura y velocidad.'),
            ('performance','🔥','MODO GAMER',
             'Desbloquea límites de energía para máxima performance.'),
        ]:
            btn = Gtk.Button(); btn.set_hexpand(True)
            bi  = hbox(spacing=14)
            bi.set_margin_top(14); bi.set_margin_bottom(14)
            bi.set_margin_start(18); bi.set_margin_end(18)
            bi.append(lbl(icon))
            tx = vbox(spacing=2); tx.set_hexpand(True)
            tx.append(lbl(title)); tx.append(lbl(desc,'od-unit'))
            bi.append(tx); btn.set_child(bi); btn.set_name(key)
            btn.connect('clicked', self._on_profile)
            self._gamer_btns.append(btn); inner.append(btn)

        self._ppd_warn = lbl('','od-warn',xalign=0,wrap=True)
        self._ppd_warn.set_visible(False); inner.append(self._ppd_warn)

        tc = vbox(css='od-card-sm'); tp = vbox(spacing=4)
        tp.set_margin_top(10); tp.set_margin_bottom(10)
        tp.set_margin_start(14); tp.set_margin_end(14)
        tp.append(lbl('💡  TIPS','od-sublabel'))
        tp.append(lbl('• Modo Gamer: enchufado a la corriente.\n'
                      '• Balanceado: si los ventiladores hacen ruido.\n'
                      '• Ahorro: para navegar sin calentar.','od-mono'))
        tc.append(tp); inner.append(tc)
        root.append(inner)
        GLib.timeout_add(300, self._load_perfil)
        return root

    def _tab_software(self):
        root  = vbox(css='od-bg')
        outer = vbox(spacing=8)
        outer.set_margin_top(10); outer.set_margin_bottom(10)
        outer.set_margin_start(12); outer.set_margin_end(12)

        sw_row = hbox(spacing=0)
        sw_row.set_halign(Gtk.Align.CENTER)
        self._btn_apt  = Gtk.ToggleButton(label='📦  APT')
        self._btn_flat = Gtk.ToggleButton(label='📱  Flatpak')
        self._btn_flat.set_group(self._btn_apt)
        self._btn_apt.set_active(True)
        self._btn_apt.connect('toggled', self._sw_toggle)
        sw_row.append(self._btn_apt); sw_row.append(self._btn_flat)
        outer.append(sw_row)

        self._sw_stack = Gtk.Stack()
        self._sw_stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._sw_stack.add_named(self._apt_panel(), 'apt')
        self._sw_stack.add_named(self._flat_panel(), 'flatpak')
        outer.append(self._sw_stack)
        root.append(outer); return root

    def _apt_panel(self):
        box = hbox(spacing=10)
        left = vbox(spacing=8); left.set_hexpand(True)
        tb = hbox(spacing=8)
        tb.append(lbl('PAQUETES APT','od-section')); tb.append(spacer())
        self._apt_cnt = lbl('','od-unit'); tb.append(self._apt_cnt)
        left.append(tb)
        self._apt_entry = Gtk.SearchEntry()
        self._apt_entry.set_placeholder_text('Buscar por nombre o descripción...')
        self._apt_entry.set_hexpand(True)
        self._apt_entry.connect('search-changed', self._filter_apt)
        left.append(self._apt_entry)
        br = hbox(spacing=8)
        bi = Gtk.Button(label='📦 Instalar')
        bi.add_css_class('od-btn-install')
        bi.connect('clicked', self._apt_install_dlg)
        bu = Gtk.Button(label='🗑️ Desinstalar')
        bu.add_css_class('od-btn-stop')
        bu.connect('clicked', self._apt_uninstall)
        bref = Gtk.Button(label='↺')
        bref.set_tooltip_text('Actualizar lista')
        bref.connect('clicked', lambda _: run_bg(self._load_apt))
        br.append(bi); br.append(bu); br.append(spacer()); br.append(bref)
        left.append(br)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(360)
        self._apt_lb = Gtk.ListBox()
        self._apt_lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._apt_lb.add_css_class('od-card')
        self._apt_lb.connect('row-selected', self._apt_selected)
        sc.set_child(self._apt_lb); left.append(sc); box.append(left)

        right = vbox(spacing=8); right.set_size_request(260,-1)
        dp = vbox(spacing=8)
        dp.set_margin_top(14); dp.set_margin_bottom(14)
        dp.set_margin_start(14); dp.set_margin_end(14)
        dp.set_vexpand(True)
        dp.append(lbl('DETALLE','od-section'))
        self._apt_name = lbl('—','c-green',xalign=0)
        self._apt_ver  = lbl('Versión: —','od-unit',xalign=0)
        self._apt_sz   = lbl('Tamaño: —','od-unit',xalign=0)
        self._apt_arch = lbl('Arch: —','od-unit',xalign=0)
        self._apt_sec  = lbl('Sección: —','od-unit',xalign=0)
        for w in (self._apt_name,self._apt_ver,self._apt_sz,
                  self._apt_arch,self._apt_sec): dp.append(w)
        dp.append(hsep())
        dp.append(lbl('Descripción:','od-sublabel',xalign=0))
        self._apt_desc = Gtk.Label(label='—')
        self._apt_desc.set_xalign(0); self._apt_desc.set_wrap(True)
        self._apt_desc.set_max_width_chars(32)
        self._apt_desc.add_css_class('od-desc'); dp.append(self._apt_desc)
        dp.append(spacer())
        bcp = Gtk.Button(label='📋 Copiar nombre')
        bcp.connect('clicked', self._apt_copy); dp.append(bcp)
        dc = vbox(css='od-detail'); dc.append(dp)
        right.append(dc); box.append(right)
        return box

    def _flat_panel(self):
        box = hbox(spacing=10)
        left = vbox(spacing=8); left.set_hexpand(True)
        tb = hbox(spacing=8)
        tb.append(lbl('APPS FLATPAK','od-section')); tb.append(spacer())
        self._flat_cnt = lbl('','od-unit'); tb.append(self._flat_cnt)
        left.append(tb)
        self._flat_entry = Gtk.SearchEntry()
        self._flat_entry.set_placeholder_text('Buscar app Flatpak...')
        self._flat_entry.set_hexpand(True)
        self._flat_entry.connect('search-changed', self._filter_flat)
        left.append(self._flat_entry)
        br = hbox(spacing=8)
        bu = Gtk.Button(label='🗑️ Desinstalar')
        bu.add_css_class('od-btn-stop')
        bu.connect('clicked', self._flat_uninstall)
        bref = Gtk.Button(label='↺')
        bref.connect('clicked', lambda _: run_bg(self._load_flat))
        br.append(bu); br.append(spacer()); br.append(bref)
        self._flat_warn = lbl('','od-unit',xalign=0); left.append(self._flat_warn)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(360)
        self._flat_lb = Gtk.ListBox()
        self._flat_lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._flat_lb.add_css_class('od-card')
        self._flat_lb.connect('row-selected', self._flat_selected)
        sc.set_child(self._flat_lb); left.append(sc); box.append(left)

        right = vbox(spacing=8); right.set_size_request(260,-1)
        dp = vbox(spacing=8)
        dp.set_margin_top(14); dp.set_margin_bottom(14)
        dp.set_margin_start(14); dp.set_margin_end(14)
        dp.set_vexpand(True)
        dp.append(lbl('DETALLE','od-section'))
        self._flat_name = lbl('—','c-cyan',xalign=0)
        self._flat_id   = lbl('ID: —','od-unit',xalign=0)
        self._flat_ver  = lbl('Versión: —','od-unit',xalign=0)
        self._flat_sz   = lbl('Tamaño: —','od-unit',xalign=0)
        self._flat_orig = lbl('Origen: —','od-unit',xalign=0)
        for w in (self._flat_name,self._flat_id,self._flat_ver,
                  self._flat_sz,self._flat_orig): dp.append(w)
        dp.append(spacer())
        bcp = Gtk.Button(label='📋 Copiar App ID')
        bcp.connect('clicked', self._flat_copy); dp.append(bcp)
        dc = vbox(css='od-detail'); dc.append(dp)
        right.append(dc); box.append(right)
        return box

    def _tab_inicio(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=8)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        hdr = hbox(spacing=10)
        hdr.append(lbl('GESTIÓN DE AUTOSTART','od-section'))
        hdr.append(spacer())
        br = Gtk.Button(label='↺ Recargar')
        br.connect('clicked', lambda _: self._load_autostart())
        hdr.append(br); inner.append(hdr)
        self._as_box = vbox(spacing=8); inner.append(self._as_box)
        root.append(inner)
        GLib.timeout_add(400, lambda: (self._load_autostart(), False)[1])
        return root

    def _tab_servicios(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=8)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        hdr = hbox(spacing=10)
        hdr.append(lbl('SERVICIOS SYSTEMD','od-section')); hdr.append(spacer())
        self._svc_search = Gtk.SearchEntry()
        self._svc_search.set_placeholder_text('Filtrar...')
        self._svc_search.set_size_request(200,-1)
        self._svc_search.connect('search-changed',
                                 lambda _: self._render_svcs())
        hdr.append(self._svc_search)
        brel = Gtk.Button(label='↺ Recargar')
        brel.connect('clicked', lambda _: run_bg(self._load_svcs))
        hdr.append(brel); inner.append(hdr)
        leg = hbox(spacing=16)
        for d,t in (('🟢','Activo'),('⚫','Inactivo'),('🔴','Fallido')):
            leg.append(lbl(f'{d} {t}','od-unit'))
        inner.append(leg)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(420)
        self._svc_box = vbox(spacing=6); sc.set_child(self._svc_box)
        inner.append(sc); root.append(inner); return root

    def _tab_controles(self):
        root  = vbox(css='od-bg')
        inner = vbox(spacing=12)
        inner.set_margin_top(14); inner.set_margin_bottom(14)
        inner.set_margin_start(24); inner.set_margin_end(24)
        inner.append(lbl('CONTROLES DEL SISTEMA','od-section'))

        a = hbox(spacing=12)
        a.set_margin_top(12); a.set_margin_bottom(12)
        a.set_margin_start(16); a.set_margin_end(16)
        ac = vbox(spacing=2); ac.set_hexpand(True)
        ac.append(lbl('🚀   INICIAR CON EL SISTEMA'))
        ac.append(lbl('Agrega OpenDash al autostart de tu sesión.','od-unit'))
        a.append(ac)
        self._as_sw = Gtk.Switch()
        self._as_sw.set_active(os.path.exists(AUTOSTART_F))
        self._as_sw.set_valign(Gtk.Align.CENTER)
        self._as_sw.connect('state-set', self._on_autostart)
        a.append(self._as_sw)
        inner.append(self._ctrl_wrap(a))

        b = vbox(spacing=8)
        b.set_margin_top(12); b.set_margin_bottom(12)
        b.set_margin_start(16); b.set_margin_end(16)
        bh = hbox(spacing=8)
        bh.append(lbl('☀️   BRILLO DE PANTALLA')); bh.append(spacer())
        self._br_val = lbl('—','c-amber'); bh.append(self._br_val); b.append(bh)
        dev = _backlight_dev()
        if dev:         meth = 'backlight físico'
        elif hw_cmd('which','brightnessctl'): meth = 'brightnessctl'
        else:           meth = 'xrandr (escritorio)'
        b.append(lbl(f'Método: {meth}','od-unit'))
        self._br_sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,1,100,1)
        self._br_sc.set_hexpand(True); self._br_sc.set_draw_value(False)
        run_bg(lambda: GLib.idle_add(self._br_sc.set_value, hw_get_brightness()) or
                       GLib.idle_add(self._br_val.set_label, f'{int(hw_get_brightness())}%'))
        self._br_sc.connect('value-changed', self._on_br)
        b.append(self._br_sc)
        inner.append(self._ctrl_wrap(b))

        v = vbox(spacing=8)
        v.set_margin_top(12); v.set_margin_bottom(12)
        v.set_margin_start(16); v.set_margin_end(16)
        vh = hbox(spacing=8)
        vh.append(lbl('🔊   VOLUMEN DEL SISTEMA')); vh.append(spacer())
        self._vol_val = lbl('—','c-cyan'); vh.append(self._vol_val); v.append(vh)
        self._vol_sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1)
        self._vol_sc.set_hexpand(True); self._vol_sc.set_draw_value(False)
        vol = hw_get_volume()
        self._vol_sc.set_value(vol); self._vol_val.set_label(f'{vol}%')
        self._vol_sc.connect('value-changed', self._on_vol)
        v.append(self._vol_sc)
        inner.append(self._ctrl_wrap(v))

        tr = hbox(spacing=12)
        tr.set_margin_top(12); tr.set_margin_bottom(12)
        tr.set_margin_start(16); tr.set_margin_end(16)
        trc = vbox(spacing=2); trc.set_hexpand(True)
        trc.append(lbl('💿   TRIM SSD'))
        trc.append(lbl('Ejecuta fstrim -av para optimizar SSDs montados.','od-unit'))
        tr.append(trc)
        bt = Gtk.Button(label='Ejecutar TRIM')
        bt.add_css_class('od-btn-start')
        bt.set_valign(Gtk.Align.CENTER)
        bt.connect('clicked', self._do_trim); tr.append(bt)
        inner.append(self._ctrl_wrap(tr))

        th = hbox(spacing=12)
        th.set_margin_top(12); th.set_margin_bottom(12)
        th.set_margin_start(16); th.set_margin_end(16)
        th.append(lbl('🎨   TEMA DE INTERFAZ')); th.append(spacer())
        self._theme_lbl = lbl('Oscuro','c-green'); th.append(self._theme_lbl)
        self._theme_sw = Gtk.Switch()
        self._theme_sw.set_active(True)
        self._theme_sw.set_valign(Gtk.Align.CENTER)
        self._theme_sw.connect('state-set', self._on_theme_sw)
        th.append(self._theme_sw)
        inner.append(self._ctrl_wrap(th))

        root.append(inner); return root

    def _ctrl_wrap(self, widget):
        c = vbox(css='od-card'); c.append(widget); return c

    def _toggle_theme(self, _):
        self._dark = not self._dark
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if self._dark
            else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_btn.set_icon_name(
            'weather-clear-night-symbolic' if self._dark
            else 'weather-clear-symbolic')
        if hasattr(self,'_theme_sw'):
            self._theme_sw.handler_block_by_func(self._on_theme_sw)
            self._theme_sw.set_active(self._dark)
            self._theme_sw.handler_unblock_by_func(self._on_theme_sw)
            self._theme_lbl.set_label('Oscuro' if self._dark else 'Claro')

    def _on_theme_sw(self, sw, state):
        self._dark = state
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if state else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_lbl.set_label('Oscuro' if state else 'Claro')
        self._theme_btn.set_icon_name(
            'weather-clear-night-symbolic' if state else 'weather-clear-symbolic')

    def _on_autostart(self, sw, state):
        if state:
            try:
                os.makedirs(os.path.dirname(AUTOSTART_F), exist_ok=True)
                open(AUTOSTART_F,'w').write(
                    '[Desktop Entry]\nType=Application\n'
                    f'Name={APP_NAME}\nExec={BINARY}\n'
                    'Hidden=false\nNoDisplay=false\n'
                    'X-GNOME-Autostart-enabled=true\n')
                self._toast(f'{APP_NAME} agregado al inicio')
            except Exception as e:
                self._toast(f'Error: {e}')
        else:
            try:
                os.remove(AUTOSTART_F)
                self._toast(f'{APP_NAME} removido del inicio')
            except FileNotFoundError:
                pass

    def _on_br(self, sc):
        v = int(sc.get_value()); self._br_val.set_label(f'{v}%')
        self._br_pend = v
        if self._br_timer: GLib.source_remove(self._br_timer)
        self._br_timer = GLib.timeout_add(250, self._apply_br)

    def _apply_br(self):
        self._br_timer = None
        if self._br_pend is not None:
            run_bg(hw_set_brightness, self._br_pend)
        return False

    def _on_vol(self, sc):
        v = int(sc.get_value()); self._vol_val.set_label(f'{v}%')
        self._vol_pend = v
        if self._vol_timer: GLib.source_remove(self._vol_timer)
        self._vol_timer = GLib.timeout_add(150, self._apply_vol)

    def _apply_vol(self):
        self._vol_timer = None
        if self._vol_pend is not None:
            run_bg(hw_set_volume, self._vol_pend)
        return False

    def _on_profile(self, btn):
        key = btn.get_name()
        for b in self._gamer_btns: b.remove_css_class('od-profile-on')
        btn.add_css_class('od-profile-on')
        try: open(PERFIL_F,'w').write(key)
        except Exception: pass
        if not hw_powerprofiles_available():
            self._ppd_warn.set_label(
                '⚠ power-profiles-daemon no está instalado.\n'
                '  sudo apt install power-profiles-daemon')
            self._ppd_warn.set_visible(True)
            self._toast('⚠ power-profiles-daemon no instalado')
            return
        self._ppd_warn.set_visible(False)
        def _apply():
            hw_cmd('powerprofilesctl','set',key)
            GLib.idle_add(self._toast, f'Perfil activado: {key}')
        run_bg(_apply)

    def _load_perfil(self):
        key = 'balanced'
        if os.path.exists(PERFIL_F): key = open(PERFIL_F).read().strip()
        for b in self._gamer_btns:
            if b.get_name() == key: b.add_css_class('od-profile-on')
        if not hw_powerprofiles_available():
            self._ppd_warn.set_label(
                '⚠ power-profiles-daemon no está instalado.\n'
                '  sudo apt install power-profiles-daemon')
            self._ppd_warn.set_visible(True)
        return False

    def _sw_toggle(self, btn):
        self._sw_stack.set_visible_child_name(
            'apt' if btn.get_active() else 'flatpak')

    def _on_close(self, window):
        if os.path.exists(AUTOSTART_F):
            self.hide()
            if not self._tray_on:
                run_bg(self._start_tray)
            return True
        return False

    def _load_autostart(self):
        clear(self._as_box)
        path = os.path.expanduser('~/.config/autostart')
        if not os.path.exists(path):
            self._as_box.append(lbl('No hay apps de autostart.','od-unit'))
            return
        for f in sorted(os.listdir(path)):
            if not f.endswith(('.desktop','.disabled')): continue
            activo = f.endswith('.desktop')
            nombre = f.replace('.desktop','').replace('.disabled','').capitalize()
            row = hbox(spacing=10,css='od-card-sm'); row.set_margin_bottom(4)
            rp  = hbox(spacing=10)
            rp.set_margin_top(8); rp.set_margin_bottom(8)
            rp.set_margin_start(12); rp.set_margin_end(12)
            rp.append(lbl('🚀' if activo else '⏸️'))
            rp.append(lbl(nombre)); rp.append(spacer())
            btn = Gtk.Button(label='Desactivar' if activo else 'Activar')
            btn.add_css_class('od-btn-stop' if activo else 'od-btn-start')
            btn.connect('clicked', lambda _,a=f: self._toggle_as(a))
            rp.append(btn); row.append(rp); self._as_box.append(row)

    def _toggle_as(self, archivo):
        path = os.path.expanduser('~/.config/autostart')
        old  = os.path.join(path, archivo)
        new  = (old.replace('.desktop','.disabled')
                if archivo.endswith('.desktop')
                else old.replace('.disabled','.desktop'))
        try: os.rename(old,new); self._load_autostart()
        except Exception as e: self._toast(f'Error: {e}')

    def _start_tray(self):
        if self._tray_on: return
        try:
            import pystray as _pt
            from PIL import Image as _PI, ImageDraw as _PD
        except Exception:
            GLib.idle_add(self.get_application().quit); return
        self._tray_on = True
        icon_img = None
        for p in ('/usr/share/pixmaps/argent-opendash.png',
                  '/usr/share/icons/hicolor/256x256/apps/argent-opendash.png'):
            if os.path.exists(p):
                try:
                    icon_img = _PI.open(p).convert('RGBA').resize((48,48),_PI.LANCZOS)
                    break
                except Exception: pass
        if icon_img is None:
            icon_img = _PI.new('RGBA',(48,48),(0,0,0,0))
            d = _PD.Draw(icon_img)
            d.ellipse([4,4,44,44],fill=(0,255,163,255))
            d.ellipse([14,14,34,34],fill=(14,15,20,255))
        menu = _pt.Menu(
            _pt.MenuItem('Argent Opendash Gtk4 libadwaita', self._tr_show, default=True),
            _pt.Menu.SEPARATOR,
            _pt.MenuItem('Mostrar ventana',     self._tr_show),
            _pt.Menu.SEPARATOR,
            _pt.MenuItem('⚡ Optimizar RAM',     self._tr_ram),
            _pt.MenuItem('🧹 Limpieza',          self._tr_clean),
            _pt.MenuItem('💿 TRIM SSD',           self._tr_trim),
            _pt.Menu.SEPARATOR,
            _pt.MenuItem('✕ Salir',              self._tr_quit),
        )
        self._tray_icon = _pt.Icon('argent-opendash',icon_img,APP_NAME,menu)
        threading.Thread(target=self._tray_icon.run,daemon=True).start()

    def _tr_show(self,i=None,it=None):  GLib.idle_add(self.present)
    def _tr_ram(self,i=None,it=None):   GLib.idle_add(self._do_optimize_ram,None)
    def _tr_clean(self,i=None,it=None): GLib.idle_add(self._do_clean,None)
    def _tr_trim(self,i=None,it=None):  GLib.idle_add(self._do_trim,None)
    def _tr_quit(self,i=None,it=None):
        if self._tray_icon: self._tray_icon.stop()
        GLib.idle_add(self.get_application().quit)

    def _apt_selected(self, _, row):
        if not row: return
        self._sel_apt = row.get_name()
        pkg = next((p for p in self._all_apt if p['name']==self._sel_apt),None)
        if pkg:
            self._apt_name.set_label(pkg['name'])
            self._apt_ver.set_label(f"Versión:  {pkg['ver']}")
            self._apt_sz.set_label(f"Tamaño:  {pkg['size']}")
            self._apt_arch.set_label(f"Arch:       {pkg['arch']}")
            self._apt_sec.set_label(f"Sección:  {pkg['sec']}")
            self._apt_desc.set_label(pkg['desc'] or '—')

    def _apt_copy(self, _):
        if not self._sel_apt:
            self._toast('Seleccioná un paquete'); return
        Gdk.Display.get_default().get_clipboard().set(self._sel_apt)
        self._toast(f'Copiado: {self._sel_apt}')

    def _apt_uninstall(self, _):
        if not self._sel_apt:
            self._toast('Seleccioná un paquete'); return
        name = self._sel_apt
        dlg = Adw.MessageDialog.new(self,'Confirmar desinstalación')
        dlg.set_body(f'¿Eliminar «{name}»?')
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Desinstalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.DESTRUCTIVE)
        def _r(d,r):
            if r=='ok':
                def _l():
                    _run_in_terminal(
                        f'#!/bin/bash\napt purge -y {name} && apt autoremove -y\n'
                        f'echo\nread -p "Listo. Presione Enter..."',
                        need_root=True)
                    GLib.idle_add(self._toast,f'Desinstalando {name}...')
                    import time; time.sleep(10)
                    run_bg(self._load_apt)
                run_bg(_l)
        dlg.connect('response',_r); dlg.present()

    def _apt_install_dlg(self, _):
        dlg = Adw.MessageDialog.new(self,'Instalar paquete APT')
        dlg.set_body('Nombre del paquete:')
        e = Gtk.Entry(); e.set_placeholder_text('ej: htop, vlc...')
        e.set_margin_top(8); dlg.set_extra_child(e)
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Instalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.SUGGESTED)
        def _r(d,r):
            if r=='ok':
                name = e.get_text().strip()
                if not name: return
                def _l():
                    _run_in_terminal(
                        f'#!/bin/bash\napt install -y {name}\n'
                        f'echo\nread -p "Listo. Presione Enter..."',
                        need_root=True)
                    GLib.idle_add(self._toast,f'Instalando {name}...')
                    import time; time.sleep(12)
                    run_bg(self._load_apt)
                run_bg(_l)
        dlg.connect('response',_r); dlg.present()

    def _flat_selected(self, _, row):
        if not row: return
        self._sel_flat = row.get_name()
        pkg = next((p for p in self._all_flat if p['id']==self._sel_flat),None)
        if pkg:
            self._flat_name.set_label(pkg['name'])
            self._flat_id.set_label(f"App ID:   {pkg['id']}")
            self._flat_ver.set_label(f"Versión:  {pkg['ver']}")
            self._flat_sz.set_label(f"Tamaño:  {pkg['size']}")
            self._flat_orig.set_label(f"Origen:   {pkg['origin']}")

    def _flat_copy(self, _):
        if not self._sel_flat:
            self._toast('Seleccioná una app'); return
        Gdk.Display.get_default().get_clipboard().set(self._sel_flat)
        self._toast(f'Copiado: {self._sel_flat}')

    def _flat_uninstall(self, _):
        if not self._sel_flat:
            self._toast('Seleccioná una app'); return
        app_id = self._sel_flat
        dlg = Adw.MessageDialog.new(self,'Desinstalar Flatpak')
        dlg.set_body(f'¿Eliminar «{app_id}»?')
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Desinstalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.DESTRUCTIVE)
        def _r(d,r):
            if r=='ok':
                def _l():
                    _run_in_terminal(
                        f'#!/bin/bash\nflatpak uninstall -y {app_id}\n'
                        f'echo\nread -p "Listo. Presione Enter..."',
                        need_root=False)
                    GLib.idle_add(self._toast,f'Desinstalando {app_id}...')
                    import time; time.sleep(8)
                    run_bg(self._load_flat)
                run_bg(_l)
        dlg.connect('response',_r); dlg.present()

    def _render_svcs(self):
        q = (self._svc_search.get_text().lower()
             if hasattr(self,'_svc_search') else '')
        clear(self._svc_box); shown = 0
        for name,active,sub,desc in self._services:
            if q and q not in name.lower() and q not in desc.lower(): continue
            if shown >= 120: break
            shown += 1
            row = hbox(spacing=8,css='od-card-sm'); row.set_margin_bottom(2)
            rp  = hbox(spacing=10)
            rp.set_margin_top(6); rp.set_margin_bottom(6)
            rp.set_margin_start(12); rp.set_margin_end(12)
            dot = '🟢' if sub=='running' else ('🔴' if active=='failed' else '⚫')
            rp.append(lbl(dot))
            info = vbox(spacing=0); info.set_hexpand(True)
            info.append(lbl(name,xalign=0))
            if desc: info.append(lbl(desc[:64],'od-unit',xalign=0))
            rp.append(info)
            running = sub=='running'
            btn = Gtk.Button(label='■ Detener' if running else '▶ Iniciar')
            btn.add_css_class('od-btn-stop' if running else 'od-btn-start')
            btn.connect('clicked',
                lambda _,n=name,r=running:
                self._svc_action(n,'stop' if r else 'start'))
            rp.append(btn); row.append(rp); self._svc_box.append(row)
        if shown == 0:
            self._svc_box.append(
                lbl('Sin resultados.' if q else 'Cargando...','od-unit'))

    def _svc_action(self, name, action):
        def _run():
            try:
                subprocess.run(
                    ['pkexec','systemctl',action,f'{name}.service'],
                    capture_output=True, timeout=12)
                GLib.idle_add(self._toast,f'{action.capitalize()}: {name}')
                run_bg(self._load_svcs)
            except Exception as e:
                GLib.idle_add(self._toast,f'Error: {e}')
        run_bg(_run)

    # ── 6c HILOS DE DATOS ───────────────────────────────────

    def _hw_loop(self):
        """Hilo principal de métricas secuencial en segundo plano (Evita fugas de hilos)."""
        import time
        try:
            prev_io = psutil.net_io_counters()
        except Exception:
            prev_io = None

        while True:
            try:
                cpu  = psutil.cpu_percent(interval=None)
                mem  = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                temp = None
                try:
                    temps = psutil.sensors_temperatures()
                    for key in ('coretemp','k10temp','zenpower','cpu_thermal','acpitz'):
                        if key in temps and temps[key]:
                            temp = temps[key][0].current
                            break
                except Exception:
                    temp = None

                io = psutil.net_io_counters()
                try:
                    addrs = psutil.net_if_addrs()
                except Exception:
                    addrs = {}

                diff = 0.0
                if io and prev_io:
                    diff = ((io.bytes_recv + io.bytes_sent) -
                            (prev_io.bytes_recv + prev_io.bytes_sent)) / 1024
                if io: prev_io = io

                ifaces = {}
                for name, ads in (addrs or {}).items():
                    if name == 'lo': continue
                    for a in ads:
                        if a.family == 2:
                            ifaces[name] = a.address; break

                self._m = {
                    'cpu':      cpu or 0,
                    'ram_used': mem.used/(1024**3) if mem else 0,
                    'ram_pct':  mem.percent if mem else 0,
                    'disk_free':disk.free/(1024**3) if disk else 0,
                    'disk_pct': disk.percent if disk else 0,
                    'temp':     temp,
                    'net_diff': max(0, diff),
                    'net_recv': io.bytes_recv/(1024**3) if io else 0,
                    'net_sent': io.bytes_sent/(1024**3) if io else 0,
                    'ifaces':   ifaces,
                }
            except Exception:
                pass
            time.sleep(1)

    def _procs_loop(self):
        """Hilo de procesos — actualiza cada 3s con un limitador seguro."""
        import time
        while True:
            try:
                self._procs_txt = hw_procs_top()
            except Exception:
                pass
            time.sleep(3)

    def _init_heavy(self):
        run_bg(self._load_sys_info)
        run_bg(self._load_apt)
        run_bg(self._load_flat)
        run_bg(self._load_svcs)
        run_bg(self._load_parts)
        GLib.timeout_add_seconds(30, lambda: (run_bg(self._load_parts), True)[1])
        return False

    def _load_sys_info(self):
        try:
            u    = platform.uname()
            cpu  = hw_cpu_model()
            pkgs = hw_cmd('sh','-c','dpkg -l | wc -l',timeout=6)
            gpu  = hw_cmd('sh','-c',
                          r"lspci | grep -E 'VGA|3D' | cut -d: -f3 | head -1",
                          timeout=4)[:42] or 'N/A'
            mem  = hw_memory()
            ram  = f'{mem.total/(1024**3):.1f} GB' if mem else '—'
            try:
                s = float(open('/proc/uptime').read().split()[0])
                up = f"{int(s//3600)}h {int((s%3600)//60)}m"
            except Exception:
                up = 'N/A'
            text = (f' OS:       Argent Platinum Edition\n'
                    f' HOST:     {u.node}\n'
                    f' KERNEL:   {u.release}\n'
                    f' CPU:      {cpu}\n'
                    f' GPU:      {gpu}\n'
                    f' RAM:      {ram} total\n'
                    f' PAQUETES: {pkgs} (dpkg)\n'
                    f' UPTIME:   {up}')
            GLib.idle_add(self._info_lbl.set_label, text)
        except Exception:
            pass

    def _load_parts(self):
        parts = hw_partitions()
        if parts:
            GLib.idle_add(self._update_parts_ui, parts)

    def _update_parts_ui(self, parts):
        if not self._parts_ok:
            clear(self._parts_box)
            self._part_bars = {}
            for p in parts:
                row = hbox(spacing=10); row.set_hexpand(True)
                row.set_margin_top(2); row.set_margin_bottom(2)
                ml = lbl(f"{p['mount']}  ({p['device']}  {p['fstype']})",
                         'od-mono', xalign=0)
                ml.set_size_request(200,-1); row.append(ml)
                bar = Gtk.LevelBar()
                bar.set_min_value(0); bar.set_max_value(100)
                bar.set_value(p['pct']); bar.set_hexpand(True)
                bar.set_valign(Gtk.Align.CENTER)
                if p['pct'] >= 90:   bar.add_css_class('err')
                elif p['pct'] >= 70: bar.add_css_class('warn')
                row.append(bar)
                sz = lbl(f"{p['used']:.1f}/{p['total']:.1f} GB ({int(p['pct'])}%)",
                         'od-unit')
                sz.set_size_request(165,-1); row.append(sz)
                self._parts_box.append(row)
                self._part_bars[p['mount']] = (bar, sz)
            self._parts_ok = True
        else:
            for p in parts:
                if p['mount'] in self._part_bars:
                    bar,sz = self._part_bars[p['mount']]
                    bar.set_value(p['pct'])
                    sz.set_label(
                        f"{p['used']:.1f}/{p['total']:.1f} GB ({int(p['pct'])}%)")
        return False

    def _load_apt(self):
        try:
            out = hw_cmd(
                'sh','-c',
                "dpkg-query -W -f='${Package}\\t${Version}\\t"
                "${Installed-Size}\\t${Architecture}\\t"
                "${Section}\\t${binary:Summary}\\n'",
                timeout=20)
            apps = []
            for line in out.split('\n'):
                if not line.strip(): continue
                parts = line.split('\t')
                if len(parts) < 6: continue
                name,ver,sk,arch,sec,desc = parts[:6]
                if not name.strip(): continue
                try:
                    k = int(sk.strip())
                    ss = f'{k//1024} MB' if k>=1024 else f'{k} KB'
                except Exception:
                    ss = '—'
                apps.append({'name':name.strip(),'ver':ver.strip(),
                             'size':ss,'arch':arch.strip(),
                             'sec':sec.strip() or '—','desc':desc.strip()})
            apps.sort(key=lambda x: x['name'])
            GLib.idle_add(self._set_apt, apps)
        except Exception:
            pass

    def _set_apt(self, apps):
        self._all_apt = apps; self._filter_apt(None); return False

    def _filter_apt(self, _):
        q = self._apt_entry.get_text().lower() if hasattr(self,'_apt_entry') else ''
        ch = self._apt_lb.get_first_child()
        while ch:
            nx = ch.get_next_sibling(); self._apt_lb.remove(ch); ch = nx
        shown = total = 0
        for pkg in self._all_apt:
            if q and q not in pkg['name'].lower() and q not in pkg['desc'].lower():
                continue
            total += 1
            if shown >= 200: continue
            shown += 1
            row = Gtk.ListBoxRow(); row.set_name(pkg['name'])
            ri = hbox(spacing=8)
            ri.set_margin_top(5); ri.set_margin_bottom(5)
            ri.set_margin_start(12); ri.set_margin_end(8)
            col = vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(pkg['name'],xalign=0))
            d = pkg['desc'][:54]+('…' if len(pkg['desc'])>54 else '')
            col.append(lbl(d,'od-desc',xalign=0))
            ri.append(col); ri.append(lbl(pkg['size'],'od-unit'))
            row.set_child(ri); self._apt_lb.append(row)
        suf = f' (+{total-shown} más)' if total>shown else ''
        self._apt_cnt.set_label(f'{total} paquetes{suf}')
        return False

    def _load_flat(self):
        if not hw_flatpak_available():
            GLib.idle_add(self._flat_warn.set_label,
                          '⚠ Flatpak no está instalado.')
            return
        GLib.idle_add(self._flat_warn.set_label, '')
        apps = []
        for cols in ('name,application,version,size,origin',
                     'name,app,version,branch,origin'):
            out = hw_cmd('sh','-c',
                         f'flatpak list --app --columns={cols}',
                         timeout=15)
            if out and '\t' in out:
                for line in out.split('\n'):
                    if not line.strip(): continue
                    p = line.split('\t')
                    if len(p) < 2: continue
                    aid = p[1].strip() if len(p)>1 else '—'
                    if '.' in aid:
                        apps.append({
                            'name':  p[0].strip() or aid,
                            'id':    aid,
                            'ver':   p[2].strip() if len(p)>2 else '—',
                            'size':  p[3].strip() if len(p)>3 else '—',
                            'origin':p[4].strip() if len(p)>4 else '—'})
                if apps: break
        apps.sort(key=lambda x: x['name'].lower())
        GLib.idle_add(self._set_flat, apps)

    def _set_flat(self, apps):
        self._all_flat = apps; self._filter_flat(None); return False

    def _filter_flat(self, _):
        q = self._flat_entry.get_text().lower() if hasattr(self,'_flat_entry') else ''
        ch = self._flat_lb.get_first_child()
        while ch:
            nx = ch.get_next_sibling(); self._flat_lb.remove(ch); ch = nx
        total = 0
        for pkg in self._all_flat:
            if q and q not in pkg['name'].lower() and q not in pkg['id'].lower():
                continue
            total += 1
            row = Gtk.ListBoxRow(); row.set_name(pkg['id'])
            ri = hbox(spacing=8)
            ri.set_margin_top(5); ri.set_margin_bottom(5)
            ri.set_margin_start(12); ri.set_margin_end(8)
            col = vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(pkg['name'],xalign=0))
            col.append(lbl(pkg['id'],'od-desc',xalign=0))
            ri.append(col)
            ri.append(lbl('Flatpak','od-tag od-tag-flat'))
            ri.append(lbl(pkg['size'],'od-unit'))
            row.set_child(ri); self._flat_lb.append(row)
        self._flat_cnt.set_label(f'{total} apps Flatpak')
        if total == 0 and not self._all_flat:
            row = Gtk.ListBoxRow()
            row.set_child(lbl('No hay apps Flatpak instaladas.','od-unit'))
            self._flat_lb.append(row)
        return False

    def _load_svcs(self):
        try:
            out = hw_cmd(
                'systemctl','list-units','--type=service',
                '--all','--no-pager','--plain','--no-legend',timeout=10)
            svcs = []
            for line in out.strip().split('\n'):
                p = line.split(None,4)
                if len(p) >= 4:
                    svcs.append((p[0].replace('.service',''),p[2],p[3],
                                 p[4] if len(p)>4 else ''))
            GLib.idle_add(self._set_svcs, svcs)
        except Exception as e:
            GLib.idle_add(self._toast,f'Error servicios: {e}')

    def _set_svcs(self, svcs):
        self._services = svcs; self._render_svcs(); return False

    # ── 6d ACCIONES DEL SISTEMA ─────────────────────────────

    def _do_clean(self, _):
        usuario = os.environ.get('USER','user')
        def _launch():
            _run_in_terminal(
                '#!/bin/bash\n'
                "echo '=== Argent OpenDash - Limpieza ==='\n"
                'echo\n'
                "echo '>> Cache de RAM...'\n"
                'sync\necho 3 > /proc/sys/vm/drop_caches\n'
                "echo '   OK'\n"
                "echo '>> Papelera...'\n"
                f'rm -rf /home/{usuario}/.local/share/Trash/files/* 2>/dev/null || true\n'
                f'rm -rf /home/{usuario}/.local/share/Trash/info/*  2>/dev/null || true\n'
                "echo '   OK'\n"
                "echo '>> Cache de APT...'\n"
                'apt clean\n'
                "echo '   OK'\n"
                'echo\n'
                "echo '=== Limpieza completada ==='\n"
                "echo\nread -p 'Presione Enter para cerrar...'\n",
                need_root=True)
        run_bg(_launch)
        self._toast('Limpieza iniciada...')

    def _do_optimize_ram(self, _):
        def _run():
            try:
                r = subprocess.run(
                    ['pkexec','sh','-c',
                     'sync; echo 3 > /proc/sys/vm/drop_caches'],
                    capture_output=True, timeout=15)
                GLib.idle_add(self._toast,
                    '¡RAM optimizada!' if r.returncode==0
                    else 'No se pudo optimizar RAM')
            except Exception as e:
                GLib.idle_add(self._toast,f'Error: {e}')
        run_bg(_run)

    def _do_trim(self, _):
        def _run():
            _run_in_terminal(
                '#!/bin/bash\n'
                "echo '=== TRIM SSD ==='\n"
                '/usr/sbin/fstrim -av\n'
                "echo\nread -p 'Listo. Presione Enter...'\n",
                need_root=True)
            GLib.idle_add(self._toast,'TRIM iniciado...')
        run_bg(_run)

    # ── 6e TICK UI ──────────────────────────────────────────

    def _tick(self):
        self._tick_n += 1
        m = self._m
        if not m: return True
        try:
            cpu = m.get('cpu',0)
            self._c_cpu.update(f'{int(cpu)}%', cpu)
            self._g_cpu.push(cpu)

            ru  = m.get('ram_used',0); rp = m.get('ram_pct',0)
            self._c_ram.update(f'{ru:.1f}G', rp)
            self._g_ram.push(rp)

            df = m.get('disk_free',0); dp = m.get('disk_pct',0)
            self._c_disk.update(f'{df:.0f}G', dp)

            temp = m.get('temp')
            if temp is not None:
                self._c_temp.update(f'{int(temp)}°', min(temp,100))
                self._g_temp.push(min(temp,100))
                self._temp_lbl.set_label(f'CPU: {int(temp)} °C')
            else:
                self._c_temp.update('N/A', 0)
                self._temp_lbl.set_label('Sensor no detectado')

            diff = m.get('net_diff',0)
            np   = min(diff/500*100, 100)
            self._g_net.push(np); self._g_net_m.push(np)

            self._net_lbl.set_label(
                f"↓ {m.get('net_recv',0):.2f} GB  "
                f"↑ {m.get('net_sent',0):.2f} GB  "
                f"  {diff:.1f} KB/s")

            ifaces = m.get('ifaces',{})
            self._iface_lbl_safe(ifaces)

            if self._tick_n % 3 == 0:
                self._proc_lbl.set_label(self._procs_txt)

        except Exception:
            pass
        return True

    def _iface_lbl_safe(self, ifaces):
        try:
            lines = [f'🌐  {n.upper():<12} {ip}' for n,ip in ifaces.items()]
            txt   = '\n'.join(lines) if lines else '—'
            self._ip_lbl.set_label(' RED:  ' + '  |  '.join(
                f'{n}: {ip}' for n,ip in ifaces.items()) if ifaces else ' RED:  —')
            self._iface_lbl_val = txt
        except Exception:
            pass

    @property
    def _iface_lbl(self):
        return type('_', (), {'set_label': lambda s,t: None})()

# ═══════════════════════════════════════════════════════════
#  SECCIÓN 7 — ENTRADA DE LA APP
# ═══════════════════════════════════════════════════════════
class OpenDashApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self._activate)

    def _activate(self, _):
        OpenDashWindow(self).present()

if __name__ == '__main__':
    import sys
    sys.exit(OpenDashApp().run(sys.argv))
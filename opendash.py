#!/usr/bin/env python3
"""
ArgOs OpenDash GTK4 v3.0 – ArgOs Platinum Edition
Monitor, Optimizador y Gestor del Sistema
GTK4 + libadwaita  ·  Tavo78ok  ·  MIT License
https://github.com/Tavo78ok/Opendash-Gtk-Edition

NOVEDADES v3.0:
  - Nuevo nombre: ArgOs OpenDash GTK4
  - Dashboard mejorado: particiones, IP, modelo CPU/GPU
  - Software: pestaña APT + Flatpak
  - Repositorios: Extrepo Manager (ver, buscar, habilitar, deshabilitar)
  - Controles: toggle "Iniciar con el sistema"
  - Todas las ops bloqueantes en hilos daemon
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
import psutil, subprocess, platform, os, math, re, threading, stat
from collections import deque

# ═══════════════════════════════════════════════════════════
#  CONSTANTES
# ═══════════════════════════════════════════════════════════
APP_ID       = 'io.github.Tavo78ok.ArgosOpendash'
APP_NAME     = 'ArgOs OpenDash GTK4'
APP_VERSION  = '3.0'
BINARY_NAME  = 'argos-opendash'
AUTOSTART_FILE = os.path.expanduser(
    '~/.config/autostart/argos-opendash.desktop')

C_GREEN  = (0.00, 1.00, 0.64)
C_CYAN   = (0.00, 0.81, 1.00)
C_AMBER  = (0.98, 0.75, 0.18)
C_RED    = (1.00, 0.27, 0.27)
C_PURPLE = (0.65, 0.55, 0.98)
C_ORANGE = (0.98, 0.57, 0.19)
C_SKY    = (0.22, 0.74, 0.98)
C_PINK   = (0.96, 0.45, 0.71)

# ═══════════════════════════════════════════════════════════
#  CSS
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
.c-orange { color: #fb923c; }
.c-pink   { color: #f472b6; }
.c-sky    { color: #38bdf8; }

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

levelbar trough            { background-color: #1c2030;
                             border-radius: 4px; min-height: 8px; }
levelbar trough block.filled { border-radius: 4px; }
levelbar.warn trough block.filled { background-color: #fbbf24; }
levelbar.err  trough block.filled { background-color: #ff4444; }

scale trough           { background-color: #1c1f2a; min-height: 5px;
                         border-radius: 3px; }
scale trough highlight { border-radius: 3px; }

scrollbar        { background-color: transparent; }
scrollbar slider { background-color: rgba(255,255,255,0.13);
                   border-radius: 4px; min-width: 5px; min-height: 5px; }

list     { background-color: transparent; }
list row { background-color: transparent; }
list row:selected { background-color: rgba(0,255,163,0.12); }
"""

# ═══════════════════════════════════════════════════════════
#  HELPERS UI
# ═══════════════════════════════════════════════════════════
def lbl(text, css=None, markup=False, xalign=None,
        selectable=False, wrap=False):
    w = Gtk.Label()
    if markup: w.set_markup(text)
    else:      w.set_label(text)
    if css:
        for c in css.split(): w.add_css_class(c)
    if xalign is not None: w.set_xalign(xalign)
    if selectable:         w.set_selectable(True)
    if wrap:
        w.set_wrap(True); w.set_max_width_chars(50)
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

def sep():
    s = Gtk.Separator()
    s.set_margin_top(4); s.set_margin_bottom(4)
    return s

def clear(w):
    ch = w.get_first_child()
    while ch:
        nx = ch.get_next_sibling(); w.remove(ch); ch = nx

def run_cmd_safe(*args, shell=False, timeout=6):
    try:
        return subprocess.check_output(
            args if not shell else args[0],
            shell=shell, text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout).strip()
    except Exception:
        return ''

def run_bg(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start(); return t

# ═══════════════════════════════════════════════════════════
#  HARDWARE HELPERS
# ═══════════════════════════════════════════════════════════
def get_cpu_model():
    try:
        for line in open('/proc/cpuinfo'):
            if 'model name' in line:
                return line.split(':')[1].strip()[:44]
    except Exception:
        pass
    return platform.processor()[:44] or 'N/A'

def get_temp():
    try:
        temps = psutil.sensors_temperatures()
        for key in ('coretemp','k10temp','zenpower','cpu_thermal','acpitz'):
            if key in temps and temps[key]:
                return temps[key][0].current
    except Exception:
        pass
    return None

def get_volume():
    try:
        out = run_cmd_safe('pactl','get-sink-volume','@DEFAULT_SINK@')
        m = re.search(r'(\d+)%', out)
        return int(m.group(1)) if m else 50
    except Exception:
        return 50

def set_volume_cmd(pct):
    try:
        subprocess.run(
            ['pactl','set-sink-volume','@DEFAULT_SINK@',f'{int(pct)}%'],
            capture_output=True, timeout=2)
    except Exception:
        pass

def _backlight_device():
    try:
        devs = os.listdir('/sys/class/backlight')
        if devs: return '/sys/class/backlight/' + devs[0]
    except Exception:
        pass
    return None

def get_brightness():
    dev = _backlight_device()
    if dev:
        try:
            cur = int(open(f'{dev}/brightness').read())
            mx  = int(open(f'{dev}/max_brightness').read())
            return cur/mx*100 if mx else 100.0
        except Exception:
            pass
    try:
        cur = run_cmd_safe('brightnessctl','get')
        mx  = run_cmd_safe('brightnessctl','max')
        if cur and mx and int(mx) > 0:
            return int(cur)/int(mx)*100
    except Exception:
        pass
    try:
        out = run_cmd_safe('xrandr','--verbose')
        m = re.search(r'Brightness:\s*([\d.]+)', out)
        if m: return float(m.group(1))*100
    except Exception:
        pass
    return 100.0

def set_brightness_cmd(pct):
    pct = max(1, min(100, int(pct)))
    try:
        r = subprocess.run(['brightnessctl','set',f'{pct}%'],
                           capture_output=True, timeout=2)
        if r.returncode == 0: return
    except Exception:
        pass
    dev = _backlight_device()
    if dev:
        try:
            mx  = int(open(f'{dev}/max_brightness').read())
            val = max(1, int(mx*pct/100))
            try:
                open(f'{dev}/brightness','w').write(str(val)); return
            except PermissionError:
                subprocess.run(['pkexec','tee',f'{dev}/brightness'],
                               input=str(val), text=True,
                               capture_output=True, timeout=5)
                return
        except Exception:
            pass
    try:
        bright = pct/100
        out = run_cmd_safe('xrandr')
        for mon in re.findall(r'^(\S+) connected', out, re.MULTILINE):
            subprocess.run(['xrandr','--output',mon,
                            '--brightness',f'{bright:.2f}'],
                           capture_output=True, timeout=2)
    except Exception:
        pass

def extrepo_available():
    return bool(run_cmd_safe('which','extrepo'))

def _extrepo_all_repos():
    """Lee repos disponibles desde /usr/share/extrepo/ o extrepo search."""
    repos = []
    # Método 1: directorio de datos de extrepo (más fiable)
    for d in ('/usr/share/extrepo', '/usr/share/extrepo/data'):
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith('.yaml') or f.endswith('.yml'):
                    name = f.replace('.yaml','').replace('.yml','')
                    # Leer descripción del yaml
                    desc = ''
                    try:
                        for line in open(os.path.join(d,f)):
                            if line.strip().startswith('Description:') or                                line.strip().startswith('description:'):
                                desc = line.split(':',1)[1].strip().strip('"').strip("'")
                                break
                    except Exception:
                        pass
                    repos.append({'name': name, 'desc': desc})
            if repos:
                return repos
    # Método 2: extrepo search vacío
    for pattern in ('', '.*', '.'):
        out = run_cmd_safe('extrepo', 'search', pattern, timeout=10)
        if out:
            for line in out.split('\n'):
                line = line.strip().lstrip('* ')
                if not line or line.startswith('#'): continue
                if ':' in line:
                    name, _, desc = line.partition(':')
                    name = name.strip()
                    if name and not name.startswith('-'):
                        repos.append({'name': name, 'desc': desc.strip()})
            if repos:
                return repos
    # Método 3: extrepo list (solo disponibles, sin descripción)
    out = run_cmd_safe('extrepo', 'list', timeout=8)
    if out:
        for line in out.split('\n'):
            name = line.strip().lstrip('* ')
            if name and not name.startswith('#'):
                repos.append({'name': name, 'desc': ''})
    return repos

def flatpak_available():
    return bool(run_cmd_safe('which','flatpak'))

# ═══════════════════════════════════════════════════════════
#  RING METER
# ═══════════════════════════════════════════════════════════
class RingMeter(Gtk.DrawingArea):
    def __init__(self, color, size=96):
        super().__init__()
        self._color = color; self._val = 0.0
        self.set_content_width(size); self.set_content_height(size)
        self.set_draw_func(self._draw, None)

    def set_value(self, v):
        self._val = max(0.0, min(1.0, float(v))); self.queue_draw()

    def _draw(self, _, cr, w, h, __):
        cx,cy = w/2, h/2
        r  = min(w,h)/2-9
        lw = max(6,int(r*0.13))
        st = math.pi*0.75; sp = math.pi*1.5
        cr.set_line_width(lw)
        cr.arc(cx,cy,r,st,st+sp)
        cr.set_source_rgba(0.13,0.15,0.20,1); cr.stroke()
        if self._val > 0.01:
            end = st+self._val*sp
            rr,g,b = self._color
            cr.set_line_width(lw+8); cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,0.07); cr.stroke()
            cr.set_line_width(lw); cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,1.0); cr.stroke()

# ═══════════════════════════════════════════════════════════
#  HISTORY GRAPH
# ═══════════════════════════════════════════════════════════
class HistoryGraph(Gtk.DrawingArea):
    def __init__(self, color, label='', maxlen=60, height=90):
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

# ═══════════════════════════════════════════════════════════
#  METRIC CARD
# ═══════════════════════════════════════════════════════════
class MetricCard(Gtk.Box):
    def __init__(self, title, color, ring_size=76):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class('od-card'); self.set_hexpand(True)
        inner = vbox(spacing=4)
        inner.set_margin_top(10); inner.set_margin_bottom(10)
        inner.set_margin_start(8); inner.set_margin_end(8)
        self._ring = RingMeter(color, ring_size)
        self._ring.set_halign(Gtk.Align.CENTER); inner.append(self._ring)
        self._val_lbl = lbl('—','od-value')
        self._val_lbl.set_halign(Gtk.Align.CENTER); inner.append(self._val_lbl)
        self._sub_lbl = lbl(title.upper(),'od-sublabel')
        self._sub_lbl.set_halign(Gtk.Align.CENTER); inner.append(self._sub_lbl)
        self.append(inner)

    def update(self, txt, pct):
        self._val_lbl.set_label(txt); self._ring.set_value(pct/100)

# ═══════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ═══════════════════════════════════════════════════════════
class OpenDashWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(f'{APP_NAME} v{APP_VERSION}')
        self.set_default_size(980, 680)
        self.set_icon_name('argos-opendash')

        # Estado
        self._dark      = True
        self._net_last  = (psutil.net_io_counters().bytes_recv
                           + psutil.net_io_counters().bytes_sent)
        self._metrics   = {}
        self._procs_text = 'Cargando...'
        self._services  = []
        self._all_apt   = []
        self._all_flatpak = []
        self._repos_list  = []
        self._selected_apt  = None
        self._selected_flat = None
        self._gamer_btns    = []
        self._part_bars     = {}

        # Debounce sliders
        self._br_timer  = None; self._vol_timer = None
        self._br_pending = None; self._vol_pending = None

        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK)
        self._apply_css()
        self._build_ui()

        GLib.timeout_add(1000, self._tick_ui)
        GLib.timeout_add(3000, self._tick_procs_ui)
        GLib.timeout_add(400,  self._init_heavy)
        self._start_metrics_thread()
        self._start_procs_thread()

    # ── CSS ─────────────────────────────────────────────────
    def _apply_css(self):
        p = Gtk.CssProvider(); p.load_from_data(APP_CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # ── Hilos de datos ────────────────────────────────────
    def _start_metrics_thread(self):
        def _loop():
            while True:
                try:
                    cpu  = psutil.cpu_percent(interval=1)
                    mem  = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    temp = get_temp()
                    io   = psutil.net_io_counters()
                    total = io.bytes_recv + io.bytes_sent
                    diff  = (total - self._net_last) / 1024
                    self._net_last = total
                    ifaces = {}
                    for name, addrs in psutil.net_if_addrs().items():
                        if name == 'lo': continue
                        for addr in addrs:
                            if addr.family == 2:
                                ifaces[name] = addr.address; break

                    self._metrics = {
                        'cpu':cpu, 'ram_used':mem.used/(1024**3),
                        'ram_pct':mem.percent,
                        'disk_free':disk.free/(1024**3),
                        'disk_pct':disk.percent, 'temp':temp,
                        'net_diff':diff,
                        'net_recv':io.bytes_recv/(1024**3),
                        'net_sent':io.bytes_sent/(1024**3),
                        'ifaces':ifaces}
                except Exception:
                    pass
        threading.Thread(target=_loop, daemon=True).start()

    def _start_procs_thread(self):
        import time
        def _loop():
            while True:
                try:
                    procs = sorted(
                        psutil.process_iter(
                            ['pid','name','cpu_percent','memory_percent']),
                        key=lambda p: p.info['cpu_percent'] or 0,
                        reverse=True)
                    hdr  = f"{'PID':<8}{'PROCESO':<22}{'CPU%':<8}{'RAM%'}\n"+"─"*50+"\n"
                    rows = ''.join(
                        f"{p.info['pid']:<8}{p.info['name'][:20]:<22}"
                        f"{p.info['cpu_percent'] or 0:<8.1f}"
                        f"{p.info['memory_percent'] or 0:.1f}%\n"
                        for p in procs)
                    self._procs_text = hdr+rows
                except Exception:
                    pass
                time.sleep(3)
        threading.Thread(target=_loop, daemon=True).start()

    def _init_heavy(self):
        run_bg(self._load_sys_info_bg)
        run_bg(self._load_apt_bg)
        run_bg(self._load_flatpak_bg)
        run_bg(self._load_services_bg)
        run_bg(self._load_partitions_bg)
        # Refrescar particiones cada 30s
        GLib.timeout_add_seconds(30, self._refresh_partitions)
        return False

    def _refresh_partitions(self):
        run_bg(self._load_partitions_bg)
        return True  # repetir

    def _load_partitions_bg(self):
        """Carga particiones en hilo separado y actualiza UI."""
        try:
            parts = []
            for p in psutil.disk_partitions(all=False):
                # Ignorar pseudo-filesystems
                if p.fstype in ('', 'tmpfs', 'devtmpfs', 'squashfs',
                                'overlay', 'proc', 'sysfs', 'cgroup',
                                'cgroup2', 'pstore', 'efivarfs'):
                    continue
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    parts.append({
                        'mount':  p.mountpoint,
                        'device': p.device.replace('/dev/', ''),
                        'fstype': p.fstype,
                        'total':  u.total / (1024**3),
                        'used':   u.used  / (1024**3),
                        'free':   u.free  / (1024**3),
                        'pct':    u.percent})
                except (PermissionError, OSError):
                    pass

            if parts:
                GLib.idle_add(self._update_partition_ui, parts)
        except Exception as e:
            pass

    def _update_partition_ui(self, parts):
        """Construye o actualiza las barras de partición en el hilo principal."""
        if not self._part_bars:
            self._build_partition_bars(parts)
        else:
            for p in parts:
                if p['mount'] in self._part_bars:
                    bar, size_lbl = self._part_bars[p['mount']]
                    bar.set_value(p['pct'])
                    size_lbl.set_label(
                        f"{p['used']:.1f}/{p['total']:.1f} GB  "
                        f"({int(p['pct'])}%)")
        return False

    # ── UI principal ──────────────────────────────────────
    def _build_ui(self):
        tb = Adw.ToolbarView()
        hdr = Adw.HeaderBar()
        # Título con logo
        title_w = Adw.WindowTitle.new(APP_NAME, f'v{APP_VERSION}')
        hdr.set_title_widget(title_w)
        self._theme_btn = Gtk.Button(icon_name='weather-clear-night-symbolic')
        self._theme_btn.set_tooltip_text('Cambiar tema')
        self._theme_btn.connect('clicked', self._toggle_theme)
        hdr.pack_end(self._theme_btn); tb.add_top_bar(hdr)
        self._tabs = Adw.TabView()
        tab_bar = Adw.TabBar(); tab_bar.set_view(self._tabs)
        tb.add_top_bar(tab_bar)
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(self._tabs)
        tb.set_content(self._toast_overlay)
        self.set_content(tb)

        for builder, title, icon in [
            (self._build_dashboard,   'Dashboard',   'computer-symbolic'),
            (self._build_monitor,     'Monitor',     'utilities-system-monitor-symbolic'),
            (self._build_gamer,       'Gamer',       'applications-games-symbolic'),
            (self._build_software,    'Software',    'system-software-install-symbolic'),
            (self._build_inicio,      'Inicio',      'system-run-symbolic'),
            (self._build_servicios,   'Servicios',   'preferences-system-symbolic'),
            (self._build_controles,   'Controles',   'preferences-desktop-symbolic'),
        ]:
            sc = Gtk.ScrolledWindow()
            sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sc.set_child(builder())
            pg = self._tabs.append(sc)
            pg.set_title(title)
            pg.set_icon(Gio.ThemedIcon.new(icon))

    def _toast(self, msg):
        t = Adw.Toast.new(msg); t.set_timeout(3)
        self._toast_overlay.add_toast(t)

    def _toggle_theme(self, _):
        self._dark = not self._dark
        sm = Adw.StyleManager.get_default()
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK if self._dark
                            else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_btn.set_icon_name(
            'weather-clear-night-symbolic' if self._dark
            else 'weather-clear-symbolic')
        if hasattr(self, '_theme_sw'):
            self._theme_sw.handler_block_by_func(self._on_theme_sw)
            self._theme_sw.set_active(self._dark)
            self._theme_sw.handler_unblock_by_func(self._on_theme_sw)
            self._theme_lbl.set_label('Oscuro' if self._dark else 'Claro')

    # ════════════════════════════════════════════════════════
    #  TAB 1 — DASHBOARD (mejorado)
    # ════════════════════════════════════════════════════════
    def _build_dashboard(self):
        root = vbox(css='od-bg')
        inner = vbox(spacing=8)
        inner.set_margin_top(10); inner.set_margin_bottom(10)
        inner.set_margin_start(14); inner.set_margin_end(14)

        # Encabezado
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

        # Ring meters
        cards = hbox(spacing=12)
        self._card_cpu  = MetricCard('CPU',   C_GREEN, 76)
        self._card_ram  = MetricCard('RAM',   C_CYAN,  76)
        self._card_disk = MetricCard('Disco', C_AMBER, 76)
        self._card_temp = MetricCard('Temp',  C_RED,   76)
        for c in (self._card_cpu,self._card_ram,
                  self._card_disk,self._card_temp):
            cards.append(c)
        inner.append(cards)

        # Gráficos históricos
        graphs = hbox(spacing=12)
        for color, attr, label in (
            (C_GREEN,  '_graph_cpu', 'CPU'),
            (C_CYAN,   '_graph_ram', 'RAM'),
            (C_PURPLE, '_graph_net', 'Red KB/s'),
        ):
            g = HistoryGraph(color, label, height=70)
            setattr(self, attr, g)
            wrap = vbox(css='od-card'); wrap.set_hexpand(True)
            p = vbox()
            p.set_margin_top(10); p.set_margin_bottom(10)
            p.set_margin_start(12); p.set_margin_end(12)
            p.append(g); wrap.append(p); graphs.append(wrap)
        inner.append(graphs)

        # ── Particiones de disco ─────────────────────────
        part_card = vbox(css='od-card')
        pp = vbox(spacing=6)
        pp.set_margin_top(10); pp.set_margin_bottom(10)
        pp.set_margin_start(14); pp.set_margin_end(14)
        ph = hbox(spacing=8)
        ph.append(lbl('💾  PARTICIONES','od-section'))
        ph.append(spacer())
        self._parts_box = vbox(spacing=8); self._parts_box.set_hexpand(True)
        pp.append(ph)
        pp.append(self._parts_box)
        part_card.append(pp); inner.append(part_card)

        # ── Especificaciones mejoradas ──────────────────
        spec_card = vbox(css='od-card')
        sp = vbox(spacing=6)
        sp.set_margin_top(12); sp.set_margin_bottom(12)
        sp.set_margin_start(16); sp.set_margin_end(16)
        sp.append(lbl('🛡️  ESPECIFICACIONES DEL SISTEMA','od-section'))
        self._info_lbl = lbl('Cargando...','od-mono',
                             xalign=0, selectable=True)
        sp.append(self._info_lbl)
        # IP inline en specs
        self._dash_ip_lbl = lbl('—','od-mono', xalign=0)
        sp.append(self._dash_ip_lbl)
        spec_card.append(sp)
        inner.append(spec_card)

        root.append(inner); return root

    def _load_sys_info_bg(self):
        try:
            u     = platform.uname()
            cpu   = get_cpu_model()
            pkgs  = run_cmd_safe('dpkg -l | wc -l', shell=True)
            gpu   = run_cmd_safe(
                r"lspci | grep -E 'VGA|3D' | cut -d: -f3 | head -1",
                shell=True)[:44] or 'N/A'
            ram   = psutil.virtual_memory()
            ram_s = f'{ram.total/(1024**3):.1f} GB'
            try:
                s  = float(open('/proc/uptime').read().split()[0])
                up = f"{int(s//3600)}h {int((s%3600)//60)}m"
            except Exception:
                up = 'N/A'
            text = (
                f' OS:       ArgOs Platinum Edition\n'
                f' HOST:     {u.node}\n'
                f' KERNEL:   {u.release}\n'
                f' CPU:      {cpu}\n'
                f' GPU:      {gpu}\n'
                f' RAM:      {ram_s} total\n'
                f' PAQUETES: {pkgs} (dpkg)\n'
                f' UPTIME:   {up}'
            )
            GLib.idle_add(self._info_lbl.set_label, text)
        except Exception:
            pass

    def _build_partition_bars(self, parts):
        """Construye las barras de partición."""
        clear(self._parts_box)
        self._part_bars = {}
        for p in parts:
            row = hbox(spacing=10)
            row.set_hexpand(True)
            row.set_margin_top(2); row.set_margin_bottom(2)
            # Etiqueta: mount (device fstype)
            fs = p.get('fstype','')
            label_txt = f"{p['mount']}  ({p['device']}  {fs})"
            ml = lbl(label_txt, 'od-mono', xalign=0)
            ml.set_size_request(200, -1); row.append(ml)
            # LevelBar
            bar = Gtk.LevelBar()
            bar.set_min_value(0); bar.set_max_value(100)
            bar.set_value(p['pct']); bar.set_hexpand(True)
            bar.set_valign(Gtk.Align.CENTER)
            if p['pct'] >= 90:   bar.add_css_class('err')
            elif p['pct'] >= 70: bar.add_css_class('warn')
            row.append(bar)
            # Texto uso
            size_lbl = lbl(
                f"{p['used']:.1f}/{p['total']:.1f} GB  "
                f"({int(p['pct'])}%)", 'od-unit')
            size_lbl.set_size_request(170, -1)
            row.append(size_lbl)
            self._parts_box.append(row)
            self._part_bars[p['mount']] = (bar, size_lbl)

    # ════════════════════════════════════════════════════════
    #  TAB 2 — MONITOR
    # ════════════════════════════════════════════════════════
    def _build_monitor(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=10)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        inner.append(lbl('MONITOR DETALLADO','od-section'))
        top = hbox(spacing=12)
        tc = vbox(css='od-card'); tp = vbox(spacing=8)
        tp.set_margin_top(10); tp.set_margin_bottom(10)
        tp.set_margin_start(12); tp.set_margin_end(12)
        tp.set_hexpand(True)
        tp.append(lbl('🌡️  TEMPERATURA CPU/GPU','od-sublabel'))
        self._temp_detail_lbl = lbl('—','od-mono',xalign=0)
        tp.append(self._temp_detail_lbl)
        self._graph_temp = HistoryGraph(C_RED,'TEMP °C',height=65)
        tp.append(self._graph_temp); tc.append(tp); top.append(tc)
        nc = vbox(css='od-card'); np = vbox(spacing=8)
        np.set_margin_top(10); np.set_margin_bottom(10)
        np.set_margin_start(12); np.set_margin_end(12)
        np.set_hexpand(True)
        np.append(lbl('🌐  RED','od-sublabel'))
        self._net_detail_lbl = lbl('—','od-mono',xalign=0)
        np.append(self._net_detail_lbl)
        self._graph_net_monitor = HistoryGraph(C_PURPLE,'KB/s',height=65)
        np.append(self._graph_net_monitor)
        nc.append(np); top.append(nc); inner.append(top)
        inner.append(lbl('🔍  TOP 10 PROCESOS','od-section'))
        pc = vbox(css='od-card'); pp = vbox()
        pp.set_margin_top(12); pp.set_margin_bottom(12)
        pp.set_margin_start(16); pp.set_margin_end(16)
        self._proc_lbl = lbl('—','od-mono',xalign=0,selectable=True)
        pp.append(self._proc_lbl); pc.append(pp)
        sc_proc = Gtk.ScrolledWindow()
        sc_proc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc_proc.set_vexpand(True)
        sc_proc.set_min_content_height(260)
        sc_proc.set_child(pc)
        inner.append(sc_proc)
        root.append(inner); return root

    # ════════════════════════════════════════════════════════
    #  TAB 3 — GAMER
    # ════════════════════════════════════════════════════════
    def _build_gamer(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=12)
        inner.set_margin_top(16); inner.set_margin_bottom(16)
        inner.set_margin_start(30); inner.set_margin_end(30)
        inner.append(lbl(
            f'<span size="20000" weight="900" foreground="#00ffa3">'
            f'🚀  OPTIMIZACIÓN DE RENDIMIENTO</span>', markup=True))
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
            bi = hbox(spacing=16)
            bi.set_margin_top(16); bi.set_margin_bottom(16)
            bi.set_margin_start(20); bi.set_margin_end(20)
            bi.append(lbl(icon))
            tx = vbox(spacing=2); tx.set_hexpand(True)
            tx.append(lbl(title)); tx.append(lbl(desc,'od-unit'))
            bi.append(tx); btn.set_child(bi); btn.set_name(key)
            btn.connect('clicked', self._on_profile)
            self._gamer_btns.append(btn); inner.append(btn)
        tc = vbox(css='od-card-sm'); tp = vbox(spacing=4)
        tp.set_margin_top(12); tp.set_margin_bottom(12)
        tp.set_margin_start(16); tp.set_margin_end(16)
        tp.append(lbl('💡  TIPS','od-sublabel'))
        tp.append(lbl('• Modo Gamer: enchufado a la corriente.\n'
                      '• Balanceado: si los ventiladores hacen ruido.\n'
                      '• Ahorro: para navegar sin calentar.','od-mono'))
        tc.append(tp); inner.append(tc)
        root.append(inner)
        GLib.timeout_add(200, self._load_perfil)
        return root

    def _on_profile(self, btn):
        key = btn.get_name()
        for b in self._gamer_btns: b.remove_css_class('od-profile-on')
        btn.add_css_class('od-profile-on')
        run_bg(run_cmd_safe, 'powerprofilesctl', 'set', key)
        try:
            open(os.path.expanduser('~/.opendash_perfil'),'w').write(key)
        except Exception: pass
        self._toast(f'Perfil activado: {key}')

    def _load_perfil(self):
        ruta = os.path.expanduser('~/.opendash_perfil')
        key  = 'balanced'
        if os.path.exists(ruta): key = open(ruta).read().strip()
        for b in self._gamer_btns:
            if b.get_name() == key: b.add_css_class('od-profile-on')
        return False

    # ════════════════════════════════════════════════════════
    #  TAB 4 — RED
    # ════════════════════════════════════════════════════════
    def _build_network(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=14)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        inner.append(lbl('INTERFACES DE RED','od-section'))
        ic = vbox(css='od-card'); ip = vbox(spacing=4)
        ip.set_margin_top(12); ip.set_margin_bottom(12)
        ip.set_margin_start(16); ip.set_margin_end(16)
        self._iface_lbl = lbl('Cargando...','od-mono',xalign=0)
        ip.append(self._iface_lbl); ic.append(ip); inner.append(ic)
        inner.append(lbl('TRÁFICO EN TIEMPO REAL','od-section'))
        nc = vbox(css='od-card'); np = vbox()
        np.set_margin_top(10); np.set_margin_bottom(10)
        np.set_margin_start(14); np.set_margin_end(14)
        self._graph_net_tab = HistoryGraph(C_PURPLE,'KB/s',height=100)
        np.append(self._graph_net_tab); nc.append(np); inner.append(nc)
        inner.append(lbl('PROCESOS ACTIVOS','od-section'))
        pc = vbox(css='od-card'); pp = vbox()
        pp.set_margin_top(10); pp.set_margin_bottom(10)
        pp.set_margin_start(16); pp.set_margin_end(16)
        self._net_proc_lbl = lbl('—','od-mono',xalign=0)
        pp.append(self._net_proc_lbl); pc.append(pp); inner.append(pc)
        root.append(inner); return root

    # ════════════════════════════════════════════════════════
    #  TAB 5 — SOFTWARE (APT + Flatpak)
    # ════════════════════════════════════════════════════════
    def _build_software(self):
        root = vbox(css='od-bg')
        outer = vbox(spacing=8)
        outer.set_margin_top(10); outer.set_margin_bottom(10)
        outer.set_margin_start(12); outer.set_margin_end(12)

        # ── Switcher APT / Flatpak ───────────────────────
        sw_row = hbox(spacing=0)
        sw_row.set_halign(Gtk.Align.CENTER)
        self._sw_apt_btn  = Gtk.ToggleButton(label='📦  APT')
        self._sw_flat_btn = Gtk.ToggleButton(label='📱  Flatpak')
        self._sw_flat_btn.set_group(self._sw_apt_btn)
        self._sw_apt_btn.set_active(True)
        self._sw_apt_btn.connect('toggled', self._on_sw_toggle)
        sw_row.append(self._sw_apt_btn)
        sw_row.append(self._sw_flat_btn)
        outer.append(sw_row)

        # Stack
        self._sw_stack = Gtk.Stack()
        self._sw_stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._sw_stack.add_named(self._build_apt_panel(), 'apt')
        self._sw_stack.add_named(self._build_flatpak_panel(), 'flatpak')
        outer.append(self._sw_stack)
        root.append(outer); return root

    def _on_sw_toggle(self, btn):
        self._sw_stack.set_visible_child_name(
            'apt' if btn.get_active() else 'flatpak')

    # ── APT ──────────────────────────────────────────────
    def _build_apt_panel(self):
        box = hbox(spacing=12)
        left = vbox(spacing=8); left.set_hexpand(True)
        tb2 = hbox(spacing=8)
        tb2.append(lbl('PAQUETES APT','od-section'))
        tb2.append(spacer())
        self._apt_count_lbl = lbl('','od-unit')
        tb2.append(self._apt_count_lbl); left.append(tb2)
        self._apt_entry = Gtk.SearchEntry()
        self._apt_entry.set_placeholder_text('Buscar por nombre o descripción...')
        self._apt_entry.set_hexpand(True)
        self._apt_entry.connect('search-changed', self._filter_apt)
        left.append(self._apt_entry)
        br = hbox(spacing=8)
        b_inst = Gtk.Button(label='📦 Instalar')
        b_inst.add_css_class('od-btn-install')
        b_inst.connect('clicked', self._show_apt_install)
        b_un = Gtk.Button(label='🗑️ Desinstalar')
        b_un.add_css_class('od-btn-stop')
        b_un.connect('clicked', self._uninstall_apt)
        b_ref = Gtk.Button(label='↺')
        b_ref.set_tooltip_text('Actualizar lista')
        b_ref.connect('clicked', lambda _: run_bg(self._load_apt_bg))
        br.append(b_inst); br.append(b_un)
        br.append(spacer()); br.append(b_ref)
        left.append(br)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(380)
        self._apt_listbox = Gtk.ListBox()
        self._apt_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._apt_listbox.add_css_class('od-card')
        self._apt_listbox.connect('row-selected', self._on_apt_selected)
        sc.set_child(self._apt_listbox); left.append(sc); box.append(left)
        # Panel detalle APT
        right = vbox(spacing=10); right.set_size_request(270,-1)
        dc = vbox(css='od-detail'); dp = vbox(spacing=10)
        dp.set_margin_top(16); dp.set_margin_bottom(16)
        dp.set_margin_start(16); dp.set_margin_end(16)
        dp.set_vexpand(True)
        dp.append(lbl('DETALLE','od-section'))
        self._apt_name_lbl = lbl('—','c-green',xalign=0)
        self._apt_ver_lbl  = lbl('Versión: —','od-unit',xalign=0)
        self._apt_size_lbl = lbl('Tamaño: —','od-unit',xalign=0)
        self._apt_arch_lbl = lbl('Arch: —','od-unit',xalign=0)
        self._apt_sec_lbl  = lbl('Sección: —','od-unit',xalign=0)
        self._apt_desc_lbl = Gtk.Label(label='—')
        self._apt_desc_lbl.set_xalign(0); self._apt_desc_lbl.set_wrap(True)
        self._apt_desc_lbl.set_max_width_chars(32)
        self._apt_desc_lbl.add_css_class('od-desc')
        for w in (self._apt_name_lbl, self._apt_ver_lbl,
                  self._apt_size_lbl, self._apt_arch_lbl,
                  self._apt_sec_lbl):
            dp.append(w)
        dp.append(sep()); dp.append(lbl('Descripción:','od-sublabel',xalign=0))
        dp.append(self._apt_desc_lbl); dp.append(spacer())
        btn_cp = Gtk.Button(label='📋 Copiar nombre')
        btn_cp.connect('clicked', self._copy_apt_name); dp.append(btn_cp)
        dc.append(dp); right.append(dc); box.append(right)
        return box

    def _load_apt_bg(self):
        try:
            out = run_cmd_safe(
                "dpkg-query -W -f='${Package}\\t${Version}\\t"
                "${Installed-Size}\\t${Architecture}\\t"
                "${Section}\\t${binary:Summary}\\n'",
                shell=True, timeout=20)
            apps = []
            for line in out.split('\n'):
                if not line.strip(): continue
                parts = line.split('\t')
                if len(parts) < 6: continue
                name,ver,size_kb,arch,sec,desc = parts[:6]
                if not name.strip(): continue
                try:
                    sk = int(size_kb.strip())
                    ss = f'{sk//1024} MB' if sk>=1024 else f'{sk} KB'
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
        ch = self._apt_listbox.get_first_child()
        while ch:
            nx = ch.get_next_sibling(); self._apt_listbox.remove(ch); ch = nx
        shown = total = 0
        for pkg in self._all_apt:
            if q and q not in pkg['name'].lower() and q not in pkg['desc'].lower():
                continue
            total += 1
            if shown >= 200: continue
            shown += 1
            row = Gtk.ListBoxRow(); row.set_name(pkg['name'])
            ri = hbox(spacing=8)
            ri.set_margin_top(6); ri.set_margin_bottom(6)
            ri.set_margin_start(12); ri.set_margin_end(8)
            col = vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(pkg['name'], xalign=0))
            d = pkg['desc'][:54]+('…' if len(pkg['desc'])>54 else '')
            col.append(lbl(d,'od-desc',xalign=0))
            ri.append(col); ri.append(lbl(pkg['size'],'od-unit'))
            row.set_child(ri); self._apt_listbox.append(row)
        suf = f' (+{total-shown} más)' if total > shown else ''
        self._apt_count_lbl.set_label(f'{total} paquetes{suf}')
        return False

    def _on_apt_selected(self, _, row):
        if not row: return
        self._selected_apt = row.get_name()
        pkg = next((p for p in self._all_apt
                    if p['name'] == self._selected_apt), None)
        if pkg:
            self._apt_name_lbl.set_label(pkg['name'])
            self._apt_ver_lbl.set_label(f"Versión:  {pkg['ver']}")
            self._apt_size_lbl.set_label(f"Tamaño:  {pkg['size']}")
            self._apt_arch_lbl.set_label(f"Arch:       {pkg['arch']}")
            self._apt_sec_lbl.set_label(f"Sección:  {pkg['sec']}")
            self._apt_desc_lbl.set_label(pkg['desc'] or 'Sin descripción.')

    def _copy_apt_name(self, _):
        if not self._selected_apt:
            self._toast('Seleccioná un paquete primero'); return
        Gdk.Display.get_default().get_clipboard().set(self._selected_apt)
        self._toast(f'Copiado: {self._selected_apt}')

    def _uninstall_apt(self, _):
        if not self._selected_apt:
            self._toast('Seleccioná un paquete primero'); return
        name = self._selected_apt
        dlg = Adw.MessageDialog.new(self,'Confirmar desinstalación')
        dlg.set_body(f'¿Eliminar «{name}»?\nEsta acción no es fácilmente reversible.')
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Desinstalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.set_default_response('cancel')
        def _resp(d, r):
            if r == 'ok':
                def _launch():
                    script = (f'#!/bin/bash\napt purge -y {name} && '
                              f'apt autoremove -y\n'
                              f'echo\nread -p "Listo. Presione Enter..."')
                    _run_in_terminal(script)
                    GLib.idle_add(self._toast, f'Desinstalando {name}...')
                    import time; time.sleep(10)
                    GLib.idle_add(lambda: run_bg(self._load_apt_bg))
                run_bg(_launch)
        dlg.connect('response', _resp); dlg.present()

    def _show_apt_install(self, _):
        dlg = Adw.MessageDialog.new(self,'Instalar paquete APT')
        dlg.set_body('Ingresá el nombre del paquete:')
        entry = Gtk.Entry(); entry.set_placeholder_text('ej: htop, vlc...')
        entry.set_margin_top(8); dlg.set_extra_child(entry)
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Instalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.SUGGESTED)
        def _resp(d, r):
            if r == 'ok':
                name = entry.get_text().strip()
                if not name: return
                def _launch():
                    script = (f'#!/bin/bash\napt install -y {name}\n'
                              f'echo\nread -p "Listo. Presione Enter..."')
                    _run_in_terminal(script)
                    GLib.idle_add(self._toast, f'Instalando {name}...')
                    import time; time.sleep(12)
                    GLib.idle_add(lambda: run_bg(self._load_apt_bg))
                run_bg(_launch)
        dlg.connect('response', _resp); dlg.present()

    # ── Flatpak ───────────────────────────────────────────
    def _build_flatpak_panel(self):
        box = hbox(spacing=12)
        left = vbox(spacing=8); left.set_hexpand(True)
        tb2 = hbox(spacing=8)
        tb2.append(lbl('APPS FLATPAK','od-section'))
        tb2.append(spacer())
        self._flat_count_lbl = lbl('','od-unit')
        tb2.append(self._flat_count_lbl); left.append(tb2)
        self._flat_entry = Gtk.SearchEntry()
        self._flat_entry.set_placeholder_text('Buscar app Flatpak...')
        self._flat_entry.set_hexpand(True)
        self._flat_entry.connect('search-changed', self._filter_flatpak)
        left.append(self._flat_entry)
        br = hbox(spacing=8)
        b_un = Gtk.Button(label='🗑️ Desinstalar')
        b_un.add_css_class('od-btn-stop')
        b_un.connect('clicked', self._uninstall_flatpak)
        b_ref = Gtk.Button(label='↺')
        b_ref.connect('clicked', lambda _: run_bg(self._load_flatpak_bg))
        br.append(b_un); br.append(spacer()); br.append(b_ref)
        left.append(br)
        # Aviso si flatpak no está
        self._flat_warn = lbl('','od-unit',xalign=0)
        left.append(self._flat_warn)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(380)
        self._flat_listbox = Gtk.ListBox()
        self._flat_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._flat_listbox.add_css_class('od-card')
        self._flat_listbox.connect('row-selected', self._on_flat_selected)
        sc.set_child(self._flat_listbox); left.append(sc); box.append(left)
        # Panel detalle Flatpak
        right = vbox(spacing=10); right.set_size_request(270,-1)
        dc = vbox(css='od-detail'); dp = vbox(spacing=10)
        dp.set_margin_top(16); dp.set_margin_bottom(16)
        dp.set_margin_start(16); dp.set_margin_end(16)
        dp.set_vexpand(True)
        dp.append(lbl('DETALLE','od-section'))
        self._flat_name_lbl = lbl('—','c-cyan',xalign=0)
        self._flat_id_lbl   = lbl('ID: —','od-unit',xalign=0)
        self._flat_ver_lbl  = lbl('Versión: —','od-unit',xalign=0)
        self._flat_size_lbl = lbl('Tamaño: —','od-unit',xalign=0)
        self._flat_orig_lbl = lbl('Origen: —','od-unit',xalign=0)
        for w in (self._flat_name_lbl, self._flat_id_lbl,
                  self._flat_ver_lbl, self._flat_size_lbl,
                  self._flat_orig_lbl):
            dp.append(w)
        dp.append(spacer())
        btn_cp2 = Gtk.Button(label='📋 Copiar App ID')
        btn_cp2.connect('clicked', self._copy_flat_id); dp.append(btn_cp2)
        dc.append(dp); right.append(dc); box.append(right)
        return box

    def _load_flatpak_bg(self):
        if not flatpak_available():
            GLib.idle_add(self._flat_warn.set_label,
                          '⚠ Flatpak no está instalado en este sistema.')
            return
        GLib.idle_add(self._flat_warn.set_label, '')
        try:
            # Intentar con columna 'application' y fallback a 'app'
            apps = []
            for cols in ('name,application,version,size,origin',
                         'name,app,version,branch,origin',
                         'name,application,version,branch,origin'):
                out = run_cmd_safe(
                    f'flatpak list --app --columns={cols}',
                    shell=True, timeout=15)
                if out and '\t' in out:
                    for line in out.split('\n'):
                        if not line.strip(): continue
                        parts = line.split('\t')
                        if len(parts) < 2: continue
                        name   = parts[0].strip() or '—'
                        app_id = parts[1].strip() or '—'
                        ver    = parts[2].strip() if len(parts) > 2 else '—'
                        size   = parts[3].strip() if len(parts) > 3 else '—'
                        origin = parts[4].strip() if len(parts) > 4 else '—'
                        if app_id and '.' in app_id:
                            apps.append({'name': name or app_id,
                                         'id': app_id, 'ver': ver,
                                         'size': size, 'origin': origin})
                    if apps:
                        break
            # Fallback: flatpak list sin columnas
            if not apps:
                out = run_cmd_safe('flatpak', 'list', '--app', timeout=15)
                for line in out.split('\n'):
                    if not line.strip(): continue
                    parts = line.split()
                    if parts:
                        # Buscar el app ID (contiene puntos)
                        app_id = next((p for p in parts if '.' in p and
                                       p[0].isupper()), None)
                        if app_id:
                            apps.append({'name': parts[0], 'id': app_id,
                                         'ver': '—', 'size': '—',
                                         'origin': '—'})
            apps.sort(key=lambda x: x['name'].lower())
            GLib.idle_add(self._set_flatpak, apps)
        except Exception as e:
            GLib.idle_add(self._flat_warn.set_label, f'Error: {e}')

    def _set_flatpak(self, apps):
        self._all_flatpak = apps; self._filter_flatpak(None); return False

    def _filter_flatpak(self, _):
        q = self._flat_entry.get_text().lower() \
            if hasattr(self,'_flat_entry') else ''
        ch = self._flat_listbox.get_first_child()
        while ch:
            nx = ch.get_next_sibling(); self._flat_listbox.remove(ch); ch = nx
        shown = total = 0
        for pkg in self._all_flatpak:
            if q and q not in pkg['name'].lower() and q not in pkg['id'].lower():
                continue
            total += 1; shown += 1
            row = Gtk.ListBoxRow(); row.set_name(pkg['id'])
            ri = hbox(spacing=8)
            ri.set_margin_top(6); ri.set_margin_bottom(6)
            ri.set_margin_start(12); ri.set_margin_end(8)
            col = vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(pkg['name'], xalign=0))
            col.append(lbl(pkg['id'],'od-desc',xalign=0))
            ri.append(col)
            tag = lbl('Flatpak','od-tag od-tag-flat')
            ri.append(tag)
            ri.append(lbl(pkg['size'],'od-unit'))
            row.set_child(ri); self._flat_listbox.append(row)
        self._flat_count_lbl.set_label(f'{total} apps Flatpak')
        if total == 0 and not q:
            row = Gtk.ListBoxRow()
            row.set_child(lbl('No hay apps Flatpak instaladas.','od-unit'))
            self._flat_listbox.append(row)
        return False

    def _on_flat_selected(self, _, row):
        if not row: return
        app_id = row.get_name()
        self._selected_flat = app_id
        pkg = next((p for p in self._all_flatpak if p['id']==app_id), None)
        if pkg:
            self._flat_name_lbl.set_label(pkg['name'])
            self._flat_id_lbl.set_label(f"App ID:   {pkg['id']}")
            self._flat_ver_lbl.set_label(f"Versión:  {pkg['ver']}")
            self._flat_size_lbl.set_label(f"Tamaño:  {pkg['size']}")
            self._flat_orig_lbl.set_label(f"Origen:   {pkg['origin']}")

    def _copy_flat_id(self, _):
        if not self._selected_flat:
            self._toast('Seleccioná una app primero'); return
        Gdk.Display.get_default().get_clipboard().set(self._selected_flat)
        self._toast(f'Copiado: {self._selected_flat}')

    def _uninstall_flatpak(self, _):
        if not self._selected_flat:
            self._toast('Seleccioná una app primero'); return
        app_id = self._selected_flat
        dlg = Adw.MessageDialog.new(self,'Confirmar desinstalación Flatpak')
        dlg.set_body(f'¿Eliminar «{app_id}»?')
        dlg.add_response('cancel','Cancelar')
        dlg.add_response('ok','Desinstalar')
        dlg.set_response_appearance('ok',Adw.ResponseAppearance.DESTRUCTIVE)
        def _resp(d, r):
            if r == 'ok':
                def _launch():
                    script = (f'#!/bin/bash\nflatpak uninstall -y {app_id}\n'
                              f'echo\nread -p "Listo. Presione Enter..."')
                    _run_in_terminal(script, need_root=False)
                    GLib.idle_add(self._toast, f'Desinstalando {app_id}...')
                    import time; time.sleep(8)
                    GLib.idle_add(lambda: run_bg(self._load_flatpak_bg))
                run_bg(_launch)
        dlg.connect('response', _resp); dlg.present()

    # ════════════════════════════════════════════════════════
    #  TAB 6 — INICIO
    # ════════════════════════════════════════════════════════
    def _build_inicio(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=8)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        hdr = hbox(spacing=10)
        hdr.append(lbl('GESTIÓN DE AUTOSTART','od-section'))
        hdr.append(spacer())
        btn_r = Gtk.Button(label='↺ Recargar')
        btn_r.connect('clicked', lambda _: self._load_autostart())
        hdr.append(btn_r); inner.append(hdr)
        self._autostart_box = vbox(spacing=8); inner.append(self._autostart_box)
        root.append(inner)
        GLib.timeout_add(300, lambda: (self._load_autostart(), False)[1])
        return root

    def _load_autostart(self):
        clear(self._autostart_box)
        path = os.path.expanduser('~/.config/autostart')
        if not os.path.exists(path):
            self._autostart_box.append(lbl('No hay apps de autostart.','od-unit'))
            return
        for archivo in sorted(os.listdir(path)):
            if not archivo.endswith(('.desktop','.disabled')): continue
            activo = archivo.endswith('.desktop')
            nombre = (archivo.replace('.desktop','')
                      .replace('.disabled','').capitalize())
            row = hbox(spacing=10,css='od-card-sm'); row.set_margin_bottom(4)
            rp  = hbox(spacing=10)
            rp.set_margin_top(10); rp.set_margin_bottom(10)
            rp.set_margin_start(14); rp.set_margin_end(14)
            rp.append(lbl('🚀' if activo else '⏸️'))
            rp.append(lbl(nombre)); rp.append(spacer())
            btn = Gtk.Button(label='Desactivar' if activo else 'Activar')
            btn.add_css_class('od-btn-stop' if activo else 'od-btn-start')
            btn.connect('clicked', lambda _,a=archivo: self._toggle_autostart(a))
            rp.append(btn); row.append(rp); self._autostart_box.append(row)

    def _toggle_autostart(self, archivo):
        path = os.path.expanduser('~/.config/autostart')
        old  = os.path.join(path, archivo)
        new  = (old.replace('.desktop','.disabled')
                if archivo.endswith('.desktop')
                else old.replace('.disabled','.desktop'))
        try:
            os.rename(old, new); self._load_autostart()
        except Exception as e:
            self._toast(f'Error: {e}')

    # ════════════════════════════════════════════════════════
    #  TAB 7 — SERVICIOS
    # ════════════════════════════════════════════════════════
    def _build_servicios(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=8)
        inner.set_margin_top(12); inner.set_margin_bottom(12)
        inner.set_margin_start(14); inner.set_margin_end(14)
        hdr = hbox(spacing=10)
        hdr.append(lbl('SERVICIOS SYSTEMD','od-section')); hdr.append(spacer())
        self._svc_search = Gtk.SearchEntry()
        self._svc_search.set_placeholder_text('Filtrar servicios...')
        self._svc_search.set_size_request(220,-1)
        self._svc_search.connect('search-changed',
                                 lambda _: self._render_services())
        hdr.append(self._svc_search)
        btn_rel = Gtk.Button(label='↺ Recargar')
        btn_rel.connect('clicked', lambda _: run_bg(self._load_services_bg))
        hdr.append(btn_rel); inner.append(hdr)
        leg = hbox(spacing=16)
        for dot,txt in (('🟢','Activo'),('⚫','Inactivo'),('🔴','Fallido')):
            leg.append(lbl(f'{dot} {txt}','od-unit'))
        inner.append(leg)
        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(450)
        self._svc_box = vbox(spacing=6); sc.set_child(self._svc_box)
        inner.append(sc); root.append(inner); return root

    def _load_services_bg(self):
        try:
            out = run_cmd_safe(
                'systemctl','list-units','--type=service',
                '--all','--no-pager','--plain','--no-legend',timeout=10)
            svcs = []
            for line in out.strip().split('\n'):
                parts = line.split(None,4)
                if len(parts) >= 4:
                    svcs.append((parts[0].replace('.service',''),
                                 parts[2], parts[3],
                                 parts[4] if len(parts)>4 else ''))
            GLib.idle_add(self._set_services, svcs)
        except Exception as e:
            GLib.idle_add(self._toast, f'Error: {e}')

    def _set_services(self, svcs):
        self._services = svcs; self._render_services(); return False

    def _render_services(self):
        q = (self._svc_search.get_text().lower()
             if hasattr(self,'_svc_search') else '')
        clear(self._svc_box); shown = 0
        for name,active,sub,desc in self._services:
            if q and q not in name.lower() and q not in desc.lower(): continue
            if shown >= 120: break
            shown += 1
            row = hbox(spacing=8,css='od-card-sm'); row.set_margin_bottom(2)
            rp  = hbox(spacing=10)
            rp.set_margin_top(7); rp.set_margin_bottom(7)
            rp.set_margin_start(12); rp.set_margin_end(12)
            dot = ('🟢' if sub=='running'
                   else ('🔴' if active=='failed' else '⚫'))
            rp.append(lbl(dot))
            info = vbox(spacing=0); info.set_hexpand(True)
            info.append(lbl(name,xalign=0))
            if desc: info.append(lbl(desc[:64],'od-unit',xalign=0))
            rp.append(info)
            running = sub == 'running'
            btn = Gtk.Button(label='■ Detener' if running else '▶ Iniciar')
            btn.add_css_class('od-btn-stop' if running else 'od-btn-start')
            btn.connect('clicked',
                        lambda _,n=name,r=running:
                        self._svc_action(n,'stop' if r else 'start'))
            rp.append(btn); row.append(rp); self._svc_box.append(row)
        if shown == 0:
            self._svc_box.append(
                lbl('Sin resultados.' if q else 'Cargando servicios...','od-unit'))

    def _svc_action(self, name, action):
        def _run():
            try:
                subprocess.run(
                    ['pkexec','systemctl',action,f'{name}.service'],
                    capture_output=True, timeout=12)
                GLib.idle_add(self._toast, f'{action.capitalize()}: {name}')
                GLib.idle_add(lambda: run_bg(self._load_services_bg))
            except Exception as e:
                GLib.idle_add(self._toast, f'Error: {e}')
        run_bg(_run)

    # ════════════════════════════════════════════════════════
    #  TAB 8 — REPOSITORIOS (Extrepo Manager)
    # ════════════════════════════════════════════════════════
    def _build_repositorios(self):
        root = vbox(css='od-bg')
        outer = hbox(spacing=12)
        outer.set_margin_top(20); outer.set_margin_bottom(20)
        outer.set_margin_start(20); outer.set_margin_end(20)

        # Columna izquierda
        left = vbox(spacing=10); left.set_hexpand(True)
        hdr = hbox(spacing=8)
        hdr.append(lbl('EXTREPO MANAGER','od-section'))
        hdr.append(spacer())
        self._repo_count_lbl = lbl('','od-unit')
        hdr.append(self._repo_count_lbl); left.append(hdr)

        self._repo_search = Gtk.SearchEntry()
        self._repo_search.set_placeholder_text('Buscar repositorio...')
        self._repo_search.set_hexpand(True)
        self._repo_search.connect('search-changed',
                                  lambda _: self._render_repos())
        left.append(self._repo_search)

        br = hbox(spacing=8)
        b_on = Gtk.Button(label='✅ Habilitar')
        b_on.add_css_class('od-btn-start')
        b_on.connect('clicked', lambda _: self._toggle_repo(True))
        b_off = Gtk.Button(label='❌ Deshabilitar')
        b_off.add_css_class('od-btn-stop')
        b_off.connect('clicked', lambda _: self._toggle_repo(False))
        b_ref = Gtk.Button(label='↺ Recargar')
        b_ref.connect('clicked', lambda _: run_bg(self._load_repos_bg))
        br.append(b_on); br.append(b_off)
        br.append(spacer()); br.append(b_ref); left.append(br)

        # Aviso si extrepo no está
        self._repo_warn = lbl('','od-unit',xalign=0)
        left.append(self._repo_warn)

        sc = Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(400)
        self._repo_listbox = Gtk.ListBox()
        self._repo_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._repo_listbox.add_css_class('od-card')
        self._repo_listbox.connect('row-selected', self._on_repo_selected)
        sc.set_child(self._repo_listbox); left.append(sc); outer.append(left)

        # Panel detalle
        right = vbox(spacing=10); right.set_size_request(280,-1)
        dc = vbox(css='od-detail'); dp = vbox(spacing=10)
        dp.set_margin_top(16); dp.set_margin_bottom(16)
        dp.set_margin_start(16); dp.set_margin_end(16)
        dp.set_vexpand(True)
        dp.append(lbl('DETALLE DEL REPO','od-section'))
        self._repo_name_lbl   = lbl('—','c-green',xalign=0)
        self._repo_status_lbl = lbl('Estado: —','od-unit',xalign=0)
        self._repo_desc_lbl   = Gtk.Label(label='—')
        self._repo_desc_lbl.set_xalign(0); self._repo_desc_lbl.set_wrap(True)
        self._repo_desc_lbl.set_max_width_chars(34)
        self._repo_desc_lbl.add_css_class('od-desc')
        for w in (self._repo_name_lbl, self._repo_status_lbl):
            dp.append(w)
        dp.append(sep()); dp.append(lbl('Descripción:','od-sublabel',xalign=0))
        dp.append(self._repo_desc_lbl)
        dp.append(spacer())
        # Instrucción de instalación extrepo
        inst_box = vbox(spacing=4,css='od-card-sm')
        ip2 = vbox(spacing=4)
        ip2.set_margin_top(10); ip2.set_margin_bottom(10)
        ip2.set_margin_start(12); ip2.set_margin_end(12)
        ip2.append(lbl('Instalar extrepo:','od-sublabel',xalign=0))
        ip2.append(lbl('sudo apt install extrepo','od-mono',
                       selectable=True, xalign=0))
        inst_box.append(ip2); dp.append(inst_box)
        dc.append(dp); right.append(dc); outer.append(right)
        root.append(outer)
        self._selected_repo = None
        return root

    def _load_repos_bg(self):
        if not extrepo_available():
            GLib.idle_add(self._repo_warn.set_label,
                          '⚠ extrepo no está instalado. '
                          'Instalá con:  sudo apt install extrepo')
            GLib.idle_add(self._repo_count_lbl.set_label, 'No disponible')
            return
        GLib.idle_add(self._repo_warn.set_label, '')
        try:
            # Repos habilitados: archivos en /etc/apt/sources.list.d/
            enabled = set()
            for sources_dir in ('/etc/apt/sources.list.d',
                                '/etc/apt/sources.list.d/'):
                try:
                    for f in os.listdir(sources_dir):
                        if f.startswith('extrepo_'):
                            name = (f.replace('extrepo_','')
                                    .replace('.sources','')
                                    .replace('.list','')
                                    .replace('.conf',''))
                            enabled.add(name)
                except Exception:
                    pass

            # Obtener todos los repos disponibles
            all_repos = _extrepo_all_repos()

            repos = []
            for r in all_repos:
                repos.append({
                    'name':    r['name'],
                    'desc':    r['desc'],
                    'enabled': r['name'] in enabled
                })

            if not repos:
                GLib.idle_add(self._repo_warn.set_label,
                              '⚠ No se encontraron repositorios. '
                              'Probá: extrepo search en terminal.')
                return

            repos.sort(key=lambda x: (not x['enabled'], x['name']))
            GLib.idle_add(self._set_repos, repos)
        except Exception as e:
            GLib.idle_add(self._toast, f'Error extrepo: {e}')

    def _set_repos(self, repos):
        self._repos_list = repos; self._render_repos(); return False

    def _render_repos(self):
        q = (self._repo_search.get_text().lower()
             if hasattr(self,'_repo_search') else '')
        ch = self._repo_listbox.get_first_child()
        while ch:
            nx = ch.get_next_sibling(); self._repo_listbox.remove(ch); ch = nx
        shown = total = 0
        for repo in self._repos_list:
            if q and q not in repo['name'].lower() and \
               q not in repo['desc'].lower():
                continue
            total += 1; shown += 1
            row = Gtk.ListBoxRow(); row.set_name(repo['name'])
            ri = hbox(spacing=8)
            ri.set_margin_top(7); ri.set_margin_bottom(7)
            ri.set_margin_start(12); ri.set_margin_end(8)
            dot = lbl('🟢' if repo['enabled'] else '⚫')
            ri.append(dot)
            col = vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(repo['name'], xalign=0))
            if repo['desc']:
                col.append(lbl(repo['desc'][:56],'od-desc',xalign=0))
            ri.append(col)
            tag_css = 'od-tag od-tag-on' if repo['enabled'] else 'od-tag od-tag-off'
            ri.append(lbl('Activo' if repo['enabled'] else 'Inactivo',tag_css))
            row.set_child(ri); self._repo_listbox.append(row)
        self._repo_count_lbl.set_label(f'{total} repositorios')
        if total == 0 and not self._repos_list:
            row = Gtk.ListBoxRow()
            row.set_child(lbl('Cargando repositorios...','od-unit'))
            self._repo_listbox.append(row)
        return False

    def _on_repo_selected(self, _, row):
        if not row: return
        self._selected_repo = row.get_name()
        repo = next((r for r in self._repos_list
                     if r['name']==self._selected_repo), None)
        if repo:
            self._repo_name_lbl.set_label(repo['name'])
            status = '🟢 Habilitado' if repo['enabled'] else '⚫ Deshabilitado'
            self._repo_status_lbl.set_label(f'Estado:  {status}')
            self._repo_desc_lbl.set_label(repo['desc'] or '—')

    def _toggle_repo(self, enable):
        if not self._selected_repo:
            self._toast('Seleccioná un repositorio primero'); return
        name   = self._selected_repo
        action = 'enable' if enable else 'disable'
        def _run():
            try:
                script = (f'#!/bin/bash\n'
                          f'extrepo {action} {name}\n')
                if enable:
                    script += 'apt update\n'
                script += f'echo\nread -p "Listo. Presione Enter..."'
                _run_in_terminal(script, need_root=True)
                GLib.idle_add(self._toast,
                              f'{"Habilitando" if enable else "Deshabilitando"}'
                              f' {name}...')
                import time; time.sleep(10)
                GLib.idle_add(lambda: run_bg(self._load_repos_bg))
            except Exception as e:
                GLib.idle_add(self._toast, f'Error: {e}')
        run_bg(_run)

    # ════════════════════════════════════════════════════════
    #  TAB 9 — CONTROLES (+ toggle autostart propio)
    # ════════════════════════════════════════════════════════
    def _build_controles(self):
        root = vbox(css='od-bg'); inner = vbox(spacing=12)
        inner.set_margin_top(14); inner.set_margin_bottom(14)
        inner.set_margin_start(24); inner.set_margin_end(24)
        inner.append(lbl('CONTROLES DEL SISTEMA','od-section'))

        # ── Iniciar con el sistema ──────────────────────
        as_card = vbox(css='od-card')
        asp = hbox(spacing=12)
        asp.set_margin_top(12); asp.set_margin_bottom(12)
        asp.set_margin_start(16); asp.set_margin_end(16)
        ac = vbox(spacing=2); ac.set_hexpand(True)
        ac.append(lbl('🚀   INICIAR CON EL SISTEMA'))
        ac.append(lbl('Agrega OpenDash al autostart de tu sesión.','od-unit'))
        asp.append(ac)
        self._autostart_sw = Gtk.Switch()
        self._autostart_sw.set_active(os.path.exists(AUTOSTART_FILE))
        self._autostart_sw.set_valign(Gtk.Align.CENTER)
        self._autostart_sw.connect('state-set', self._on_autostart_self)
        asp.append(self._autostart_sw)
        as_card.append(asp); inner.append(as_card)

        # ── Brillo ──────────────────────────────────────
        brc = vbox(css='od-card'); brp = vbox(spacing=10)
        brp.set_margin_top(12); brp.set_margin_bottom(12)
        brp.set_margin_start(16); brp.set_margin_end(16)
        brh = hbox(spacing=8)
        brh.append(lbl('☀️   BRILLO DE PANTALLA'))
        brh.append(spacer())
        self._br_val = lbl('—','c-amber'); brh.append(self._br_val)
        brp.append(brh)
        if _backlight_device():       meth = 'backlight físico'
        elif run_cmd_safe('which','brightnessctl'): meth = 'brightnessctl'
        else:                          meth = 'xrandr (escritorio)'
        brp.append(lbl(f'Método: {meth}','od-unit'))
        self._br_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,1,100,1)
        self._br_scale.set_hexpand(True); self._br_scale.set_draw_value(False)
        def _init_br():
            v = get_brightness()
            GLib.idle_add(self._br_scale.set_value, v)
            GLib.idle_add(self._br_val.set_label, f'{int(v)}%')
        run_bg(_init_br)
        self._br_scale.connect('value-changed', self._on_brightness)
        brp.append(self._br_scale); brc.append(brp); inner.append(brc)

        # ── Volumen ──────────────────────────────────────
        vc = vbox(css='od-card'); vp = vbox(spacing=10)
        vp.set_margin_top(12); vp.set_margin_bottom(12)
        vp.set_margin_start(16); vp.set_margin_end(16)
        vh = hbox(spacing=8)
        vh.append(lbl('🔊   VOLUMEN DEL SISTEMA'))
        vh.append(spacer())
        self._vol_val = lbl('—','c-cyan'); vh.append(self._vol_val)
        vp.append(vh)
        self._vol_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,0,100,1)
        self._vol_scale.set_hexpand(True); self._vol_scale.set_draw_value(False)
        def _init_vol():
            v = get_volume()
            GLib.idle_add(self._vol_scale.set_value, v)
            GLib.idle_add(self._vol_val.set_label, f'{v}%')
        run_bg(_init_vol)
        self._vol_scale.connect('value-changed', self._on_volume)
        vp.append(self._vol_scale); vc.append(vp); inner.append(vc)

        # ── TRIM SSD ────────────────────────────────────
        trim_card = vbox(css='od-card'); trimp = hbox(spacing=12)
        trimp.set_margin_top(12); trimp.set_margin_bottom(12)
        trimp.set_margin_start(16); trimp.set_margin_end(16)
        tc2 = vbox(spacing=2); tc2.set_hexpand(True)
        tc2.append(lbl('💿   TRIM SSD'))
        tc2.append(lbl('Ejecuta fstrim -av para optimizar SSDs montados.','od-unit'))
        trimp.append(tc2)
        btn_trim = Gtk.Button(label='Ejecutar TRIM')
        btn_trim.add_css_class('od-btn-start')
        btn_trim.set_valign(Gtk.Align.CENTER)
        btn_trim.connect('clicked', self._do_trim)
        trimp.append(btn_trim)
        trim_card.append(trimp); inner.append(trim_card)

        # ── Tema ─────────────────────────────────────────
        tc = vbox(css='od-card'); tp = hbox(spacing=12)
        tp.set_margin_top(12); tp.set_margin_bottom(12)
        tp.set_margin_start(16); tp.set_margin_end(16)
        tp.append(lbl('🎨   TEMA DE INTERFAZ')); tp.append(spacer())
        self._theme_lbl = lbl('Oscuro','c-green'); tp.append(self._theme_lbl)
        self._theme_sw  = Gtk.Switch()
        self._theme_sw.set_active(True)
        self._theme_sw.set_valign(Gtk.Align.CENTER)
        self._theme_sw.connect('state-set', self._on_theme_sw)
        tp.append(self._theme_sw); tc.append(tp); inner.append(tc)

        root.append(inner); return root

    def _on_autostart_self(self, sw, state):
        if state:
            try:
                os.makedirs(os.path.dirname(AUTOSTART_FILE), exist_ok=True)
                content = (
                    '[Desktop Entry]\n'
                    'Type=Application\n'
                    f'Name={APP_NAME}\n'
                    f'Exec={BINARY_NAME}\n'
                    'Hidden=false\n'
                    'NoDisplay=false\n'
                    'X-GNOME-Autostart-enabled=true\n'
                )
                open(AUTOSTART_FILE,'w').write(content)
                self._toast(f'{APP_NAME} agregado al inicio del sistema')
            except Exception as e:
                self._toast(f'Error: {e}')
        else:
            try:
                os.remove(AUTOSTART_FILE)
                self._toast(f'{APP_NAME} removido del inicio del sistema')
            except FileNotFoundError:
                pass
            except Exception as e:
                self._toast(f'Error: {e}')

    def _on_brightness(self, scale):
        v = int(scale.get_value()); self._br_val.set_label(f'{v}%')
        self._br_pending = v
        if self._br_timer: GLib.source_remove(self._br_timer)
        self._br_timer = GLib.timeout_add(250, self._apply_brightness)

    def _apply_brightness(self):
        self._br_timer = None
        if self._br_pending is not None:
            run_bg(set_brightness_cmd, self._br_pending)
        return False

    def _on_volume(self, scale):
        v = int(scale.get_value()); self._vol_val.set_label(f'{v}%')
        self._vol_pending = v
        if self._vol_timer: GLib.source_remove(self._vol_timer)
        self._vol_timer = GLib.timeout_add(150, self._apply_volume)

    def _apply_volume(self):
        self._vol_timer = None
        if self._vol_pending is not None:
            run_bg(set_volume_cmd, self._vol_pending)
        return False

    def _on_theme_sw(self, sw, state):
        self._dark = state
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if state
            else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_lbl.set_label('Oscuro' if state else 'Claro')
        self._theme_btn.set_icon_name(
            'weather-clear-night-symbolic' if state
            else 'weather-clear-symbolic')

    # ════════════════════════════════════════════════════════
    #  ACCIONES DEL SISTEMA
    # ════════════════════════════════════════════════════════
    def _do_clean(self, _):
        usuario = os.environ.get('USER','user')
        def _launch():
            script = (
                '#!/bin/bash\n'
                "echo '========================================='\n"
                "echo '   ArgOs OpenDash - Limpieza Profunda'\n"
                "echo '========================================='\n"
                'echo\n'
                "echo '>> Liberando cache del sistema...'\n"
                'sync\n'
                'echo 3 > /proc/sys/vm/drop_caches\n'
                "echo '   OK'\n"
                'echo\n'
                "echo '>> Eliminando paquetes huerfanos...'\n"
                'apt autoremove -y\n'
                'echo\n'
                "echo '>> Limpiando cache de apt...'\n"
                'apt clean\n'
                'echo\n'
                "echo '>> Vaciando papelera...'\n"
                f'rm -rf /home/{usuario}/.local/share/Trash/files/* '
                f'2>/dev/null || true\n'
                f'rm -rf /home/{usuario}/.local/share/Trash/info/* '
                f'2>/dev/null || true\n'
                "echo '   OK'\n"
                'echo\n'
                "echo '========================================='\n"
                "echo '   Limpieza completada exitosamente'\n"
                "echo '========================================='\n"
                'echo\n'
                "read -p 'Presione Enter para cerrar...'\n"
            )
            _run_in_terminal(script, need_root=True)
        run_bg(_launch)
        self._toast('Limpieza profunda iniciada...')

    def _do_trim(self, _):
        def _run():
            try:
                script = (
                    '#!/bin/bash\n'
                    "echo '=== TRIM SSD ==='\n"
                    'fstrim -av\n'
                    'echo\n'
                    "read -p 'Listo. Presione Enter...'\n"
                )
                _run_in_terminal(script, need_root=True)
                GLib.idle_add(self._toast, 'TRIM iniciado...')
            except Exception as e:
                GLib.idle_add(self._toast, f'Error TRIM: {e}')
        run_bg(_run)

    def _do_optimize_ram(self, _):
        def _run():
            try:
                r = subprocess.run(
                    ['pkexec','sh','-c',
                     'sync; echo 3 > /proc/sys/vm/drop_caches'],
                    capture_output=True, timeout=15)
                GLib.idle_add(
                    self._toast,
                    '¡Memoria RAM optimizada!' if r.returncode==0
                    else 'No se pudo optimizar RAM')
            except subprocess.TimeoutExpired:
                GLib.idle_add(self._toast,'Tiempo de espera agotado')
            except Exception as e:
                GLib.idle_add(self._toast, f'Error: {e}')
        run_bg(_run)

    # ════════════════════════════════════════════════════════
    #  TICKS UI
    # ════════════════════════════════════════════════════════
    def _tick_ui(self):
        m = self._metrics
        if not m: return True
        try:
            cpu = m.get('cpu', 0)
            self._card_cpu.update(f'{int(cpu)}%', cpu)
            self._graph_cpu.push(cpu)

            ru = m.get('ram_used',0); rp = m.get('ram_pct',0)
            self._card_ram.update(f'{ru:.1f}G', rp)
            self._graph_ram.push(rp)

            df = m.get('disk_free',0); dp2 = m.get('disk_pct',0)
            self._card_disk.update(f'{df:.0f}G', dp2)

            temp = m.get('temp')
            if temp is not None:
                self._card_temp.update(f'{int(temp)}°', min(temp,100))
                self._graph_temp.push(min(temp,100))
                self._temp_detail_lbl.set_label(f'CPU: {int(temp)} °C')
            else:
                self._card_temp.update('N/A', 0)
                self._temp_detail_lbl.set_label('Sensor no detectado')

            diff = m.get('net_diff',0)
            np2  = min(diff/500*100, 100)
            self._graph_net.push(np2)
            self._graph_net_monitor.push(np2)
            self._graph_net_tab.push(np2)

            self._net_detail_lbl.set_label(
                f"↓ Recibido:  {m.get('net_recv',0):.2f} GB\n"
                f"↑ Enviado:   {m.get('net_sent',0):.2f} GB\n"
                f"Velocidad:   {diff:.1f} KB/s")

            ifaces = m.get('ifaces',{})
            lines  = [f'🌐  {n.upper():<12} {ip}'
                      for n,ip in ifaces.items()]
            iface_txt = '\n'.join(lines) or 'Sin interfaz activa'
            self._iface_lbl.set_label(iface_txt)
            self._dash_ip_lbl.set_label(
                ' RED:  ' + '  |  '.join(
                    f'{n}: {ip}' for n,ip in ifaces.items()
                ) if ifaces else ' RED:  —')


        except Exception:
            pass
        return True

    def _tick_procs_ui(self):
        try:
            txt = getattr(self,'_procs_text','—')
            self._proc_lbl.set_label(txt)
            self._net_proc_lbl.set_label(txt)
        except Exception:
            pass
        return True


# ═══════════════════════════════════════════════════════════
#  HELPER: Ejecutar script en terminal con/sin pkexec
# ═══════════════════════════════════════════════════════════
def _run_in_terminal(script_body, need_root=True):
    """Escribe script temporal y lo lanza en una terminal."""
    path = '/tmp/argos_opendash_script.sh'
    try:
        with open(path,'w') as f: f.write(script_body)
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        return
    cmd = ['pkexec','bash',path] if need_root else ['bash',path]
    for term in ['x-terminal-emulator','xterm','mate-terminal',
                 'gnome-terminal','konsole','xfce4-terminal']:
        try:
            subprocess.Popen([term,'-e',' '.join(cmd)])
            return
        except FileNotFoundError:
            continue

# ═══════════════════════════════════════════════════════════
#  APLICACIÓN
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

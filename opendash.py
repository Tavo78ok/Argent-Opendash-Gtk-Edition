#!/usr/bin/env python3
"""
OpenDash v2.1 – ArgOs Platinum Edition
GTK4 + libadwaita  ·  Tavo78ok  ·  MIT License

CORRECCIONES v2.1:
  - Todas las ops bloqueantes en hilos daemon (nunca en hilo principal)
  - Brillo con debounce 250ms + fallback xrandr para escritorio
  - Volumen con debounce 150ms
  - psutil.sensors_temperatures y process_iter en hilo secundario
  - pkexec nunca bloquea GTK
  - Tab Software: tamaño, versión, descripción, panel detalle, instalar
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk
import psutil, subprocess, platform, os, math, re, threading
from collections import deque

C_GREEN  = (0.00, 1.00, 0.64)
C_CYAN   = (0.00, 0.81, 1.00)
C_AMBER  = (0.98, 0.75, 0.18)
C_RED    = (1.00, 0.27, 0.27)
C_PURPLE = (0.65, 0.55, 0.98)

APP_CSS = """
.od-bg       { background-color: #0d0f14; }
.od-card     { background-color: #141720; border-radius: 14px;
               border: 1px solid rgba(255,255,255,0.06); }
.od-card-sm  { background-color: #141720; border-radius: 10px;
               border: 1px solid rgba(255,255,255,0.05); }
.od-detail   { background-color: #0d1018; border-radius: 12px;
               border: 1px solid rgba(255,255,255,0.08); }
.od-value    { font-size: 34px; font-weight: 900; color: white; }
.od-unit     { font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.38); }
.od-sublabel { font-size: 10px; font-weight: 700; letter-spacing: 2px;
               color: rgba(255,255,255,0.32); }
.od-section  { font-size: 10px; font-weight: 800; letter-spacing: 4px;
               color: rgba(255,255,255,0.22); }
.od-mono     { font-family: monospace; font-size: 12px; color: rgba(255,255,255,0.72); }
.od-desc     { font-size: 11px; color: rgba(255,255,255,0.45); }
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
                  border: 1px solid rgba(0,255,163,0.40); border-radius: 12px; }
scale trough           { background-color: #1c1f2a; min-height: 5px; border-radius: 3px; }
scale trough highlight { border-radius: 3px; }
scrollbar        { background-color: transparent; }
scrollbar slider { background-color: rgba(255,255,255,0.13); border-radius: 4px;
                   min-width: 5px; min-height: 5px; }
list     { background-color: transparent; }
list row { background-color: transparent; }
list row:selected { background-color: rgba(0,255,163,0.12); }
"""

# ─── Helpers UI ───────────────────────────────────────────
def lbl(text, css=None, markup=False, xalign=None, selectable=False, wrap=False):
    w = Gtk.Label()
    if markup: w.set_markup(text)
    else: w.set_label(text)
    if css:
        for c in css.split(): w.add_css_class(c)
    if xalign is not None: w.set_xalign(xalign)
    if selectable: w.set_selectable(True)
    if wrap: w.set_wrap(True); w.set_max_width_chars(55)
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

def clear(w):
    ch = w.get_first_child()
    while ch:
        nx = ch.get_next_sibling(); w.remove(ch); ch = nx

def run_cmd_safe(*args, shell=False, timeout=4):
    try:
        return subprocess.check_output(
            args if not shell else args[0], shell=shell,
            text=True, stderr=subprocess.DEVNULL, timeout=timeout).strip()
    except Exception:
        return ""

def run_bg(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start(); return t

# ─── Hardware helpers ─────────────────────────────────────
def get_temp():
    try:
        temps = psutil.sensors_temperatures()
        for key in ('coretemp','k10temp','zenpower','cpu_thermal','acpitz'):
            if key in temps and temps[key]:
                return temps[key][0].current
    except Exception: pass
    return None

def get_volume():
    try:
        out = run_cmd_safe('pactl','get-sink-volume','@DEFAULT_SINK@')
        m = re.search(r'(\d+)%', out)
        return int(m.group(1)) if m else 50
    except Exception: return 50

def set_volume_cmd(pct):
    try:
        subprocess.run(['pactl','set-sink-volume','@DEFAULT_SINK@',f'{int(pct)}%'],
                       capture_output=True, timeout=2)
    except Exception: pass

def _backlight_device():
    try:
        devs = os.listdir('/sys/class/backlight')
        if devs: return '/sys/class/backlight/' + devs[0]
    except Exception: pass
    return None

def get_brightness():
    dev = _backlight_device()
    if dev:
        try:
            cur = int(open(f'{dev}/brightness').read())
            mx  = int(open(f'{dev}/max_brightness').read())
            return cur/mx*100 if mx else 100.0
        except Exception: pass
    try:
        cur = run_cmd_safe('brightnessctl','get')
        mx  = run_cmd_safe('brightnessctl','max')
        if cur and mx and int(mx)>0: return int(cur)/int(mx)*100
    except Exception: pass
    try:
        out = run_cmd_safe('xrandr','--verbose')
        m = re.search(r'Brightness:\s*([\d.]+)', out)
        if m: return float(m.group(1))*100
    except Exception: pass
    return 100.0

def set_brightness_cmd(pct):
    """Aplica brillo en hilo secundario. Prueba 3 métodos."""
    pct = max(1, min(100, int(pct)))
    # 1) brightnessctl (sin root)
    try:
        r = subprocess.run(['brightnessctl','set',f'{pct}%'],
                           capture_output=True, timeout=2)
        if r.returncode == 0: return
    except Exception: pass
    # 2) backlight directo
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
        except Exception: pass
    # 3) xrandr (escritorio sin backlight)
    try:
        bright = pct/100
        out = run_cmd_safe('xrandr')
        for mon in re.findall(r'^(\S+) connected', out, re.MULTILINE):
            subprocess.run(['xrandr','--output',mon,'--brightness',f'{bright:.2f}'],
                           capture_output=True, timeout=2)
    except Exception: pass

# ─── Ring Meter ───────────────────────────────────────────
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
        cr.arc(cx,cy,r,st,st+sp); cr.set_source_rgba(0.13,0.15,0.20,1); cr.stroke()
        if self._val>0.01:
            end = st+self._val*sp
            rr,g,b = self._color
            cr.set_line_width(lw+8); cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,0.07); cr.stroke()
            cr.set_line_width(lw); cr.arc(cx,cy,r,st,end)
            cr.set_source_rgba(rr,g,b,1.0); cr.stroke()

# ─── History Graph ────────────────────────────────────────
class HistoryGraph(Gtk.DrawingArea):
    def __init__(self, color, label="", maxlen=60, height=90):
        super().__init__()
        self._color=color; self._label=label
        self._data=deque([0.0]*maxlen, maxlen=maxlen)
        self.set_content_height(height); self.set_hexpand(True)
        self.set_draw_func(self._draw, None)

    def push(self, pct):
        self._data.append(max(0.0,min(100.0,float(pct)))/100.0); self.queue_draw()

    def _draw(self, _, cr, w, h, __):
        cr.set_source_rgba(0.06,0.07,0.10,1)
        cr.rectangle(0,0,w,h); cr.fill()
        pts=list(self._data); n=len(pts)
        if n<2: return
        step=w/(n-1); rr,g,b=self._color; pad=h*0.08
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
        cur=pts[-1]*100
        cr.set_source_rgba(rr,g,b,0.85); cr.set_font_size(10)
        cr.move_to(7,14); cr.show_text(f"{self._label}  {cur:.0f}%")

# ─── Metric Card ──────────────────────────────────────────
class MetricCard(Gtk.Box):
    def __init__(self, title, color, ring_size=92):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class('od-card'); self.set_hexpand(True)
        inner=vbox(spacing=4)
        inner.set_margin_top(14); inner.set_margin_bottom(14)
        inner.set_margin_start(10); inner.set_margin_end(10)
        self._ring=RingMeter(color, ring_size)
        self._ring.set_halign(Gtk.Align.CENTER); inner.append(self._ring)
        self._val_lbl=lbl("—","od-value"); self._val_lbl.set_halign(Gtk.Align.CENTER)
        inner.append(self._val_lbl)
        self._sub_lbl=lbl(title.upper(),"od-sublabel"); self._sub_lbl.set_halign(Gtk.Align.CENTER)
        inner.append(self._sub_lbl); self.append(inner)

    def update(self, txt, pct):
        self._val_lbl.set_label(txt); self._ring.set_value(pct/100)

# ═══════════════════════════════════════════════════════════
#  VENTANA PRINCIPAL
# ═══════════════════════════════════════════════════════════
class OpenDashWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("OpenDash v2.1"); self.set_default_size(1120,700)
        self.set_icon_name("opendash")
        self._dark=True
        self._net_last=(psutil.net_io_counters().bytes_recv
                        +psutil.net_io_counters().bytes_sent)
        self._services=[]; self._all_apps=[]; self._gamer_btns=[]
        self._selected_pkg=None
        self._br_timer=None; self._vol_timer=None
        self._br_pending=None; self._vol_pending=None
        self._metrics={}; self._procs_text="Cargando..."
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self._apply_css(); self._build_ui()
        GLib.timeout_add(1000, self._tick_ui)
        GLib.timeout_add(3000, self._tick_procs_ui)
        GLib.timeout_add(300,  self._init_heavy)
        self._start_metrics_thread()
        self._start_procs_thread()

    def _apply_css(self):
        p=Gtk.CssProvider(); p.load_from_data(APP_CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),p,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # ─── Hilos de datos ───────────────────────────────────
    def _start_metrics_thread(self):
        def _loop():
            while True:
                try:
                    cpu  = psutil.cpu_percent(interval=1)
                    mem  = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    temp = get_temp()
                    io   = psutil.net_io_counters()
                    total= io.bytes_recv+io.bytes_sent
                    diff = (total-self._net_last)/1024
                    self._net_last=total
                    ifaces={}
                    for name,addrs in psutil.net_if_addrs().items():
                        if name=='lo': continue
                        for addr in addrs:
                            if addr.family==2: ifaces[name]=addr.address; break
                    self._metrics={
                        'cpu':cpu,'ram_used':mem.used/(1024**3),
                        'ram_pct':mem.percent,'disk_free':disk.free/(1024**3),
                        'disk_pct':disk.percent,'temp':temp,
                        'net_diff':diff,'net_recv':io.bytes_recv/(1024**3),
                        'net_sent':io.bytes_sent/(1024**3),'ifaces':ifaces}
                except Exception: pass
        threading.Thread(target=_loop,daemon=True).start()

    def _start_procs_thread(self):
        import time
        def _loop():
            while True:
                try:
                    procs=sorted(
                        psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                        key=lambda p:p.info['cpu_percent'] or 0,reverse=True)[:10]
                    hdr=f"{'PID':<8}{'PROCESO':<22}{'CPU%':<8}{'RAM%'}\n"+"─"*50+"\n"
                    rows="".join(
                        f"{p.info['pid']:<8}{p.info['name'][:20]:<22}"
                        f"{p.info['cpu_percent'] or 0:<8.1f}"
                        f"{p.info['memory_percent'] or 0:.1f}%\n" for p in procs)
                    self._procs_text=hdr+rows
                except Exception: pass
                time.sleep(3)
        threading.Thread(target=_loop,daemon=True).start()

    def _init_heavy(self):
        run_bg(self._load_sys_info_bg)
        run_bg(self._load_apps_bg)
        run_bg(self._load_services_bg)
        return False

    # ─── UI ───────────────────────────────────────────────
    def _build_ui(self):
        tb=Adw.ToolbarView()
        hdr=Adw.HeaderBar()
        self._theme_btn=Gtk.Button(icon_name="weather-clear-night-symbolic")
        self._theme_btn.set_tooltip_text("Cambiar tema")
        self._theme_btn.connect("clicked",self._toggle_theme)
        hdr.pack_end(self._theme_btn); tb.add_top_bar(hdr)
        self._tabs=Adw.TabView()
        tab_bar=Adw.TabBar(); tab_bar.set_view(self._tabs); tb.add_top_bar(tab_bar)
        self._toast_overlay=Adw.ToastOverlay()
        self._toast_overlay.set_child(self._tabs); tb.set_content(self._toast_overlay)
        self.set_content(tb)
        for builder,title,icon in [
            (self._build_dashboard,"Dashboard","computer-symbolic"),
            (self._build_monitor,"Monitor","utilities-system-monitor-symbolic"),
            (self._build_gamer,"Gamer","applications-games-symbolic"),
            (self._build_network,"Red","network-wired-symbolic"),
            (self._build_software,"Software","system-software-install-symbolic"),
            (self._build_inicio,"Inicio","system-run-symbolic"),
            (self._build_servicios,"Servicios","preferences-system-symbolic"),
            (self._build_controles,"Controles","preferences-desktop-symbolic"),
        ]:
            sc=Gtk.ScrolledWindow()
            sc.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
            sc.set_child(builder())
            pg=self._tabs.append(sc)
            pg.set_title(title); pg.set_icon(Gio.ThemedIcon.new(icon))

    def _toast(self,msg):
        t=Adw.Toast.new(msg); t.set_timeout(3); self._toast_overlay.add_toast(t)

    def _toggle_theme(self,_):
        self._dark=not self._dark
        sm=Adw.StyleManager.get_default()
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK if self._dark
                            else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_btn.set_icon_name(
            "weather-clear-night-symbolic" if self._dark else "weather-clear-symbolic")
        if hasattr(self,'_theme_sw'):
            self._theme_sw.handler_block_by_func(self._on_theme_sw)
            self._theme_sw.set_active(self._dark)
            self._theme_sw.handler_unblock_by_func(self._on_theme_sw)
            self._theme_lbl.set_label("Oscuro" if self._dark else "Claro")

    # ──────────── TAB 1: DASHBOARD ────────────────────────
    def _build_dashboard(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=14)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        hdr=hbox(spacing=10); hdr.append(lbl("ESTADO DEL SISTEMA","od-section"))
        hdr.append(spacer())
        btn_ram=Gtk.Button(label="⚡ Optimizar RAM")
        btn_ram.add_css_class('od-btn-action'); btn_ram.connect("clicked",self._do_optimize_ram)
        btn_cln=Gtk.Button(label="🧹 Limpieza")
        btn_cln.add_css_class('od-btn-action'); btn_cln.connect("clicked",self._do_clean)
        hdr.append(btn_ram); hdr.append(btn_cln); inner.append(hdr)
        cards=hbox(spacing=12)
        self._card_cpu=MetricCard("CPU",C_GREEN)
        self._card_ram=MetricCard("RAM",C_CYAN)
        self._card_disk=MetricCard("Disco",C_AMBER)
        self._card_temp=MetricCard("Temp",C_RED)
        for c in (self._card_cpu,self._card_ram,self._card_disk,self._card_temp):
            cards.append(c)
        inner.append(cards)
        graphs=hbox(spacing=12)
        for color,attr,label in ((C_GREEN,'_graph_cpu','CPU'),(C_CYAN,'_graph_ram','RAM'),(C_PURPLE,'_graph_net','Red KB/s')):
            g=HistoryGraph(color,label,height=90); setattr(self,attr,g)
            wrap=vbox(css="od-card"); wrap.set_hexpand(True)
            p=vbox(); p.set_margin_top(10); p.set_margin_bottom(10)
            p.set_margin_start(12); p.set_margin_end(12); p.append(g); wrap.append(p)
            graphs.append(wrap)
        inner.append(graphs)
        spec=vbox(spacing=6,css="od-card"); sp=vbox(spacing=6)
        sp.set_margin_top(14); sp.set_margin_bottom(14)
        sp.set_margin_start(16); sp.set_margin_end(16)
        sp.append(lbl("🛡️  ESPECIFICACIONES","od-section"))
        self._info_lbl=lbl("Cargando...","od-mono",xalign=0,selectable=True)
        sp.append(self._info_lbl); spec.append(sp); inner.append(spec)
        root.append(inner); return root

    def _load_sys_info_bg(self):
        try:
            u=platform.uname()
            pkgs=run_cmd_safe("dpkg -l | wc -l",shell=True)
            gpu=run_cmd_safe(r"lspci | grep -E 'VGA|3D' | cut -d: -f3 | head -1",shell=True)[:42] or "N/A"
            try:
                s=float(open('/proc/uptime').read().split()[0])
                up=f"{int(s//3600)}h {int((s%3600)//60)}m"
            except Exception: up="N/A"
            text=(f" OS:       ArgOs Platinum Edition\n"
                  f" HOST:     {u.node}\n"
                  f" KERNEL:   {u.release}\n"
                  f" CPU:      {u.processor[:42]}\n"
                  f" GPU:      {gpu}\n"
                  f" PAQUETES: {pkgs} (dpkg)\n"
                  f" UPTIME:   {up}")
            GLib.idle_add(self._info_lbl.set_label,text)
        except Exception: pass

    # ──────────── TAB 2: MONITOR ──────────────────────────
    def _build_monitor(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=14)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        inner.append(lbl("MONITOR DETALLADO","od-section"))
        top=hbox(spacing=12)
        tc=vbox(css="od-card"); tp=vbox(spacing=8)
        tp.set_margin_top(14); tp.set_margin_bottom(14)
        tp.set_margin_start(16); tp.set_margin_end(16); tp.set_hexpand(True)
        tp.append(lbl("🌡️  TEMPERATURA","od-sublabel"))
        self._temp_detail_lbl=lbl("—","od-mono",xalign=0); tp.append(self._temp_detail_lbl)
        self._graph_temp=HistoryGraph(C_RED,"TEMP °C",height=80); tp.append(self._graph_temp)
        tc.append(tp); top.append(tc)
        nc=vbox(css="od-card"); np=vbox(spacing=8)
        np.set_margin_top(14); np.set_margin_bottom(14)
        np.set_margin_start(16); np.set_margin_end(16); np.set_hexpand(True)
        np.append(lbl("🌐  RED","od-sublabel"))
        self._net_detail_lbl=lbl("—","od-mono",xalign=0); np.append(self._net_detail_lbl)
        self._graph_net_monitor=HistoryGraph(C_PURPLE,"KB/s",height=80); np.append(self._graph_net_monitor)
        nc.append(np); top.append(nc); inner.append(top)
        inner.append(lbl("🔍  TOP 10 PROCESOS","od-section"))
        pc=vbox(css="od-card"); pp=vbox()
        pp.set_margin_top(12); pp.set_margin_bottom(12)
        pp.set_margin_start(16); pp.set_margin_end(16)
        self._proc_lbl=lbl("—","od-mono",xalign=0); pp.append(self._proc_lbl)
        pc.append(pp); inner.append(pc); root.append(inner); return root

    # ──────────── TAB 3: GAMER ────────────────────────────
    def _build_gamer(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=18)
        inner.set_margin_top(30); inner.set_margin_bottom(30)
        inner.set_margin_start(60); inner.set_margin_end(60)
        inner.append(lbl('<span size="20000" weight="900" foreground="#00ffa3">🚀  OPTIMIZACIÓN DE RENDIMIENTO</span>',markup=True))
        inner.append(lbl("Seleccioná un perfil de energía para ajustar tu equipo.","od-unit"))
        self._gamer_btns=[]
        for key,icon,title,desc in [
            ("power-saver","🍃","MODO AHORRO","Reduce frecuencia del CPU. Ideal para batería y silencio."),
            ("balanced","⚖️","MODO BALANCEADO","Equilibrio inteligente entre temperatura y velocidad."),
            ("performance","🔥","MODO GAMER","Desbloquea límites de energía para máxima performance."),
        ]:
            btn=Gtk.Button(); btn.set_hexpand(True)
            bi=hbox(spacing=16); bi.set_margin_top(16); bi.set_margin_bottom(16)
            bi.set_margin_start(20); bi.set_margin_end(20); bi.append(lbl(icon))
            tx=vbox(spacing=2); tx.set_hexpand(True)
            tx.append(lbl(title)); tx.append(lbl(desc,"od-unit"))
            bi.append(tx); btn.set_child(bi); btn.set_name(key)
            btn.connect("clicked",self._on_profile)
            self._gamer_btns.append(btn); inner.append(btn)
        tc=vbox(css="od-card-sm"); tp=vbox(spacing=4)
        tp.set_margin_top(12); tp.set_margin_bottom(12)
        tp.set_margin_start(16); tp.set_margin_end(16)
        tp.append(lbl("💡  TIPS","od-sublabel"))
        tp.append(lbl("• Modo Gamer: usalo enchufado a la corriente.\n"
                      "• Balanceado: si los ventiladores hacen ruido.\n"
                      "• Ahorro: para navegar sin calentar.","od-mono"))
        tc.append(tp); inner.append(tc); root.append(inner)
        GLib.timeout_add(200,self._load_perfil); return root

    def _on_profile(self,btn):
        key=btn.get_name()
        for b in self._gamer_btns: b.remove_css_class('od-profile-on')
        btn.add_css_class('od-profile-on')
        run_bg(run_cmd_safe,'powerprofilesctl','set',key)
        try:
            open(os.path.expanduser("~/.opendash_perfil"),"w").write(key)
        except Exception: pass
        self._toast(f"Perfil activado: {key}")

    def _load_perfil(self):
        ruta=os.path.expanduser("~/.opendash_perfil")
        key="balanced"
        if os.path.exists(ruta): key=open(ruta).read().strip()
        for b in self._gamer_btns:
            if b.get_name()==key: b.add_css_class('od-profile-on')
        return False

    # ──────────── TAB 4: RED ──────────────────────────────
    def _build_network(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=14)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        inner.append(lbl("INTERFACES DE RED","od-section"))
        ic=vbox(css="od-card"); ip=vbox(spacing=4)
        ip.set_margin_top(12); ip.set_margin_bottom(12)
        ip.set_margin_start(16); ip.set_margin_end(16)
        self._iface_lbl=lbl("Cargando...","od-mono",xalign=0)
        ip.append(self._iface_lbl); ic.append(ip); inner.append(ic)
        inner.append(lbl("TRÁFICO EN TIEMPO REAL","od-section"))
        nc=vbox(css="od-card"); np=vbox()
        np.set_margin_top(10); np.set_margin_bottom(10)
        np.set_margin_start(14); np.set_margin_end(14)
        self._graph_net_tab=HistoryGraph(C_PURPLE,"KB/s",height=100)
        np.append(self._graph_net_tab); nc.append(np); inner.append(nc)
        inner.append(lbl("PROCESOS ACTIVOS","od-section"))
        pc=vbox(css="od-card"); pp=vbox()
        pp.set_margin_top(10); pp.set_margin_bottom(10)
        pp.set_margin_start(16); pp.set_margin_end(16)
        self._net_proc_lbl=lbl("—","od-mono",xalign=0)
        pp.append(self._net_proc_lbl); pc.append(pp); inner.append(pc)
        root.append(inner); return root

    # ──────────── TAB 5: SOFTWARE (mejorada) ──────────────
    def _build_software(self):
        root=vbox(css="od-bg")
        outer=hbox(spacing=12)
        outer.set_margin_top(20); outer.set_margin_bottom(20)
        outer.set_margin_start(20); outer.set_margin_end(20)

        # Lista
        left=vbox(spacing=10); left.set_hexpand(True)
        tb2=hbox(spacing=8); tb2.append(lbl("GESTOR DE PAQUETES","od-section"))
        tb2.append(spacer())
        self._sw_count_lbl=lbl("","od-unit"); tb2.append(self._sw_count_lbl)
        left.append(tb2)
        self._sw_entry=Gtk.SearchEntry()
        self._sw_entry.set_placeholder_text("Buscar por nombre o descripción...")
        self._sw_entry.set_hexpand(True)
        self._sw_entry.connect("search-changed",self._filter_apps)
        left.append(self._sw_entry)
        br=hbox(spacing=8)
        b_inst=Gtk.Button(label="📦 Instalar")
        b_inst.add_css_class('od-btn-install'); b_inst.connect("clicked",self._show_install_dialog)
        b_un=Gtk.Button(label="🗑️ Desinstalar")
        b_un.add_css_class('od-btn-stop'); b_un.connect("clicked",self._uninstall_app)
        b_ref=Gtk.Button(label="↺ Actualizar")
        b_ref.connect("clicked",lambda _: run_bg(self._load_apps_bg))
        br.append(b_inst); br.append(b_un); br.append(spacer()); br.append(b_ref)
        left.append(br)
        sc=Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(420)
        self._sw_listbox=Gtk.ListBox()
        self._sw_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._sw_listbox.add_css_class('od-card')
        self._sw_listbox.connect("row-selected",self._on_pkg_selected)
        sc.set_child(self._sw_listbox); left.append(sc); outer.append(left)

        # Panel detalle
        right=vbox(spacing=10); right.set_size_request(290,-1)
        dc=vbox(css="od-detail"); dp=vbox(spacing=10)
        dp.set_margin_top(16); dp.set_margin_bottom(16)
        dp.set_margin_start(16); dp.set_margin_end(16); dp.set_vexpand(True)
        dp.append(lbl("DETALLE DEL PAQUETE","od-section"))
        self._pkg_name_lbl=lbl("—","c-green",xalign=0)
        self._pkg_ver_lbl=lbl("Versión: —","od-unit",xalign=0)
        self._pkg_size_lbl=lbl("Tamaño: —","od-unit",xalign=0)
        self._pkg_arch_lbl=lbl("Arch: —","od-unit",xalign=0)
        self._pkg_sec_lbl=lbl("Sección: —","od-unit",xalign=0)
        for w in (self._pkg_name_lbl,self._pkg_ver_lbl,self._pkg_size_lbl,
                  self._pkg_arch_lbl,self._pkg_sec_lbl): dp.append(w)
        sep=Gtk.Separator(); sep.set_margin_top(6); sep.set_margin_bottom(6)
        dp.append(sep)
        dp.append(lbl("Descripción:","od-sublabel",xalign=0))
        self._pkg_desc_lbl=Gtk.Label(label="—")
        self._pkg_desc_lbl.set_xalign(0); self._pkg_desc_lbl.set_wrap(True)
        self._pkg_desc_lbl.set_max_width_chars(34)
        self._pkg_desc_lbl.add_css_class("od-desc"); dp.append(self._pkg_desc_lbl)
        dp.append(spacer())
        btn_copy=Gtk.Button(label="📋 Copiar nombre")
        btn_copy.connect("clicked",self._copy_pkg_name); dp.append(btn_copy)
        dc.append(dp); right.append(dc); outer.append(right)
        root.append(outer); return root

    def _load_apps_bg(self):
        try:
            out=run_cmd_safe(
                "dpkg-query -W -f='${Package}\\t${Version}\\t${Installed-Size}\\t"
                "${Architecture}\\t${Section}\\t${binary:Summary}\\n'",
                shell=True,timeout=20)
            apps=[]
            for line in out.split('\n'):
                if not line.strip(): continue
                parts=line.split('\t')
                if len(parts)<6: continue
                name,ver,size_kb,arch,sec,desc=parts[:6]
                if not name.strip(): continue
                try:
                    sk=int(size_kb.strip())
                    ss=f"{sk//1024} MB" if sk>=1024 else f"{sk} KB"
                except Exception: ss="—"
                apps.append({'name':name.strip(),'ver':ver.strip(),'size':ss,
                             'arch':arch.strip(),'sec':sec.strip() or "—",'desc':desc.strip()})
            apps.sort(key=lambda x:x['name'])
            GLib.idle_add(self._set_apps,apps)
        except Exception: pass

    def _set_apps(self,apps):
        self._all_apps=apps; self._filter_apps(None); return False

    def _filter_apps(self,_):
        q=self._sw_entry.get_text().lower() if hasattr(self,'_sw_entry') else ""
        ch=self._sw_listbox.get_first_child()
        while ch:
            nx=ch.get_next_sibling(); self._sw_listbox.remove(ch); ch=nx
        shown=total=0
        for pkg in self._all_apps:
            if q and q not in pkg['name'].lower() and q not in pkg['desc'].lower(): continue
            total+=1
            if shown>=200: continue
            shown+=1
            row=Gtk.ListBoxRow(); row.set_name(pkg['name'])
            ri=hbox(spacing=8)
            ri.set_margin_top(6); ri.set_margin_bottom(6)
            ri.set_margin_start(12); ri.set_margin_end(8)
            col=vbox(spacing=1); col.set_hexpand(True)
            col.append(lbl(pkg['name'],xalign=0))
            col.append(lbl((pkg['desc'][:54]+"…" if len(pkg['desc'])>54 else pkg['desc']),"od-desc",xalign=0))
            ri.append(col); ri.append(lbl(pkg['size'],"od-unit"))
            row.set_child(ri); self._sw_listbox.append(row)
        suf=f" (+{total-shown} más)" if total>shown else ""
        self._sw_count_lbl.set_label(f"{total} paquetes{suf}")
        return False

    def _on_pkg_selected(self,_,row):
        if not row: return
        name=row.get_name(); self._selected_pkg=name
        pkg=next((p for p in self._all_apps if p['name']==name),None)
        if pkg:
            self._pkg_name_lbl.set_label(pkg['name'])
            self._pkg_ver_lbl.set_label(f"Versión:  {pkg['ver']}")
            self._pkg_size_lbl.set_label(f"Tamaño:  {pkg['size']}")
            self._pkg_arch_lbl.set_label(f"Arch:       {pkg['arch']}")
            self._pkg_sec_lbl.set_label(f"Sección:  {pkg['sec']}")
            self._pkg_desc_lbl.set_label(pkg['desc'] or "Sin descripción.")

    def _copy_pkg_name(self,_):
        if not self._selected_pkg: self._toast("Seleccioná un paquete primero"); return
        Gdk.Display.get_default().get_clipboard().set(self._selected_pkg)
        self._toast(f"Copiado: {self._selected_pkg}")

    def _uninstall_app(self,_):
        if not self._selected_pkg: self._toast("Seleccioná un paquete primero"); return
        name=self._selected_pkg
        dlg=Adw.MessageDialog.new(self,"Confirmar desinstalación")
        dlg.set_body(f"¿Eliminar «{name}» y sus dependencias?\nEsta acción no se puede deshacer fácilmente.")
        dlg.add_response("cancel","Cancelar")
        dlg.add_response("ok","Desinstalar")
        dlg.set_response_appearance("ok",Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.set_default_response("cancel")
        def _resp(d,r):
            if r=="ok":
                def _launch():
                    cmd=(f"pkexec bash -c 'apt purge -y {name} && apt autoremove -y;"
                         f"echo; echo Listo. Presione Enter.; read'")
                    try: subprocess.Popen(["x-terminal-emulator","-e","bash","-c",cmd])
                    except FileNotFoundError:
                        for term in ["xterm","mate-terminal","gnome-terminal","konsole"]:
                            try: subprocess.Popen([term,"-e","bash","-c",cmd]); break
                            except FileNotFoundError: continue
                    GLib.idle_add(self._toast,f"Desinstalando {name}...")
                    import time; time.sleep(8)
                    GLib.idle_add(lambda: run_bg(self._load_apps_bg))
                run_bg(_launch)
        dlg.connect("response",_resp); dlg.present()

    def _show_install_dialog(self,_):
        dlg=Adw.MessageDialog.new(self,"Instalar paquete")
        dlg.set_body("Ingresá el nombre exacto del paquete a instalar:")
        entry=Gtk.Entry(); entry.set_placeholder_text("ej: htop, vlc, gimp...")
        entry.set_margin_top(8); dlg.set_extra_child(entry)
        dlg.add_response("cancel","Cancelar")
        dlg.add_response("ok","Instalar")
        dlg.set_response_appearance("ok",Adw.ResponseAppearance.SUGGESTED)
        dlg.set_default_response("ok")
        def _resp(d,r):
            if r=="ok":
                name=entry.get_text().strip()
                if not name: return
                def _launch():
                    cmd=(f"pkexec bash -c 'apt install -y {name};"
                         f"echo; echo Listo. Presione Enter.; read'")
                    try: subprocess.Popen(["x-terminal-emulator","-e","bash","-c",cmd])
                    except FileNotFoundError:
                        for term in ["xterm","mate-terminal","gnome-terminal","konsole"]:
                            try: subprocess.Popen([term,"-e","bash","-c",cmd]); break
                            except FileNotFoundError: continue
                    GLib.idle_add(self._toast,f"Instalando {name}...")
                    import time; time.sleep(12)
                    GLib.idle_add(lambda: run_bg(self._load_apps_bg))
                run_bg(_launch)
        dlg.connect("response",_resp); dlg.present()

    # ──────────── TAB 6: INICIO ───────────────────────────
    def _build_inicio(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=14)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        hdr=hbox(spacing=10); hdr.append(lbl("GESTIÓN DE AUTOSTART","od-section"))
        hdr.append(spacer())
        btn_r=Gtk.Button(label="↺ Recargar")
        btn_r.connect("clicked",lambda _: self._load_autostart()); hdr.append(btn_r)
        inner.append(hdr)
        self._autostart_box=vbox(spacing=8); inner.append(self._autostart_box)
        root.append(inner)
        GLib.timeout_add(300,lambda:(self._load_autostart(),False)[1]); return root

    def _load_autostart(self):
        clear(self._autostart_box)
        path=os.path.expanduser("~/.config/autostart")
        if not os.path.exists(path):
            self._autostart_box.append(lbl("No hay apps de autostart.","od-unit")); return
        for archivo in sorted(os.listdir(path)):
            if not archivo.endswith(('.desktop','.disabled')): continue
            activo=archivo.endswith('.desktop')
            nombre=(archivo.replace('.desktop','').replace('.disabled','').capitalize())
            row=hbox(spacing=10,css="od-card-sm"); row.set_margin_bottom(4)
            rp=hbox(spacing=10)
            rp.set_margin_top(10); rp.set_margin_bottom(10)
            rp.set_margin_start(14); rp.set_margin_end(14)
            rp.append(lbl("🚀" if activo else "⏸️")); rp.append(lbl(nombre)); rp.append(spacer())
            btn=Gtk.Button(label="Desactivar" if activo else "Activar")
            btn.add_css_class('od-btn-stop' if activo else 'od-btn-start')
            btn.connect("clicked",lambda _,a=archivo: self._toggle_autostart(a))
            rp.append(btn); row.append(rp); self._autostart_box.append(row)

    def _toggle_autostart(self,archivo):
        path=os.path.expanduser("~/.config/autostart")
        old=os.path.join(path,archivo)
        new=(old.replace('.desktop','.disabled') if archivo.endswith('.desktop')
             else old.replace('.disabled','.desktop'))
        try: os.rename(old,new); self._load_autostart()
        except Exception as e: self._toast(f"Error: {e}")

    # ──────────── TAB 7: SERVICIOS ────────────────────────
    def _build_servicios(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=12)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(20); inner.set_margin_end(20)
        hdr=hbox(spacing=10); hdr.append(lbl("SERVICIOS SYSTEMD","od-section")); hdr.append(spacer())
        self._svc_search=Gtk.SearchEntry()
        self._svc_search.set_placeholder_text("Filtrar servicios...")
        self._svc_search.set_size_request(220,-1)
        self._svc_search.connect("search-changed",lambda _: self._render_services())
        hdr.append(self._svc_search)
        btn_rel=Gtk.Button(label="↺ Recargar")
        btn_rel.connect("clicked",lambda _: run_bg(self._load_services_bg))
        hdr.append(btn_rel); inner.append(hdr)
        leg=hbox(spacing=16)
        for dot,txt in (("🟢","Activo"),("⚫","Inactivo"),("🔴","Fallido")):
            leg.append(lbl(f"{dot} {txt}","od-unit"))
        inner.append(leg)
        sc=Gtk.ScrolledWindow()
        sc.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        sc.set_vexpand(True); sc.set_min_content_height(450)
        self._svc_box=vbox(spacing=6); sc.set_child(self._svc_box); inner.append(sc)
        root.append(inner); return root

    def _load_services_bg(self):
        try:
            out=run_cmd_safe('systemctl','list-units','--type=service',
                             '--all','--no-pager','--plain','--no-legend',timeout=10)
            svcs=[]
            for line in out.strip().split('\n'):
                parts=line.split(None,4)
                if len(parts)>=4:
                    svcs.append((parts[0].replace('.service',''),parts[2],parts[3],
                                 parts[4] if len(parts)>4 else ''))
            GLib.idle_add(self._set_services,svcs)
        except Exception as e: GLib.idle_add(self._toast,f"Error: {e}")

    def _set_services(self,svcs):
        self._services=svcs; self._render_services(); return False

    def _render_services(self):
        q=(self._svc_search.get_text().lower() if hasattr(self,'_svc_search') else "")
        clear(self._svc_box); shown=0
        for name,active,sub,desc in self._services:
            if q and q not in name.lower() and q not in desc.lower(): continue
            if shown>=120: break
            shown+=1
            row=hbox(spacing=8,css="od-card-sm"); row.set_margin_bottom(2)
            rp=hbox(spacing=10)
            rp.set_margin_top(7); rp.set_margin_bottom(7)
            rp.set_margin_start(12); rp.set_margin_end(12)
            dot=("🟢" if sub=="running" else ("🔴" if active=="failed" else "⚫"))
            rp.append(lbl(dot))
            info=vbox(spacing=0); info.set_hexpand(True)
            info.append(lbl(name,xalign=0))
            if desc: info.append(lbl(desc[:64],"od-unit",xalign=0))
            rp.append(info)
            running=sub=="running"
            btn=Gtk.Button(label="■ Detener" if running else "▶ Iniciar")
            btn.add_css_class('od-btn-stop' if running else 'od-btn-start')
            btn.connect("clicked",lambda _,n=name,r=running: self._svc_action(n,"stop" if r else "start"))
            rp.append(btn); row.append(rp); self._svc_box.append(row)
        if shown==0:
            self._svc_box.append(lbl("Sin resultados." if q else "Cargando servicios...","od-unit"))

    def _svc_action(self,name,action):
        def _run():
            try:
                subprocess.run(['pkexec','systemctl',action,f'{name}.service'],
                               capture_output=True,timeout=12)
                GLib.idle_add(self._toast,f"{action.capitalize()}: {name}")
                GLib.idle_add(lambda: run_bg(self._load_services_bg))
            except Exception as e: GLib.idle_add(self._toast,f"Error: {e}")
        run_bg(_run)

    # ──────────── TAB 8: CONTROLES ────────────────────────
    def _build_controles(self):
        root=vbox(css="od-bg"); inner=vbox(spacing=18)
        inner.set_margin_top(30); inner.set_margin_bottom(30)
        inner.set_margin_start(50); inner.set_margin_end(50)
        inner.append(lbl("CONTROLES DEL SISTEMA","od-section"))

        # Brillo
        brc=vbox(css="od-card"); brp=vbox(spacing=10)
        brp.set_margin_top(18); brp.set_margin_bottom(18)
        brp.set_margin_start(22); brp.set_margin_end(22)
        brh=hbox(spacing=8); brh.append(lbl("☀️   BRILLO DE PANTALLA")); brh.append(spacer())
        self._br_val=lbl("—","c-amber"); brh.append(self._br_val); brp.append(brh)
        # Detectar método
        if _backlight_device(): meth="backlight físico"
        elif run_cmd_safe('which','brightnessctl'): meth="brightnessctl"
        else: meth="xrandr (escritorio)"
        brp.append(lbl(f"Método detectado: {meth}","od-unit"))
        self._br_scale=Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,1,100,1)
        self._br_scale.set_hexpand(True); self._br_scale.set_draw_value(False)
        def _init_br():
            v=get_brightness()
            GLib.idle_add(self._br_scale.set_value,v)
            GLib.idle_add(self._br_val.set_label,f"{int(v)}%")
        run_bg(_init_br)
        self._br_scale.connect("value-changed",self._on_brightness)
        brp.append(self._br_scale); brc.append(brp); inner.append(brc)

        # Volumen
        vc=vbox(css="od-card"); vp=vbox(spacing=10)
        vp.set_margin_top(18); vp.set_margin_bottom(18)
        vp.set_margin_start(22); vp.set_margin_end(22)
        vh=hbox(spacing=8); vh.append(lbl("🔊   VOLUMEN DEL SISTEMA")); vh.append(spacer())
        self._vol_val=lbl("—","c-cyan"); vh.append(self._vol_val); vp.append(vh)
        self._vol_scale=Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL,0,100,1)
        self._vol_scale.set_hexpand(True); self._vol_scale.set_draw_value(False)
        def _init_vol():
            v=get_volume()
            GLib.idle_add(self._vol_scale.set_value,v)
            GLib.idle_add(self._vol_val.set_label,f"{v}%")
        run_bg(_init_vol)
        self._vol_scale.connect("value-changed",self._on_volume)
        vp.append(self._vol_scale); vc.append(vp); inner.append(vc)

        # Tema
        tc=vbox(css="od-card"); tp=hbox(spacing=12)
        tp.set_margin_top(18); tp.set_margin_bottom(18)
        tp.set_margin_start(22); tp.set_margin_end(22)
        tp.append(lbl("🎨   TEMA DE INTERFAZ")); tp.append(spacer())
        self._theme_lbl=lbl("Oscuro","c-green"); tp.append(self._theme_lbl)
        self._theme_sw=Gtk.Switch(); self._theme_sw.set_active(True)
        self._theme_sw.set_valign(Gtk.Align.CENTER)
        self._theme_sw.connect("state-set",self._on_theme_sw)
        tp.append(self._theme_sw); tc.append(tp); inner.append(tc)
        root.append(inner); return root

    def _on_brightness(self,scale):
        v=int(scale.get_value()); self._br_val.set_label(f"{v}%")
        self._br_pending=v
        if self._br_timer: GLib.source_remove(self._br_timer)
        self._br_timer=GLib.timeout_add(250,self._apply_brightness)

    def _apply_brightness(self):
        self._br_timer=None
        if self._br_pending is not None: run_bg(set_brightness_cmd,self._br_pending)
        return False

    def _on_volume(self,scale):
        v=int(scale.get_value()); self._vol_val.set_label(f"{v}%")
        self._vol_pending=v
        if self._vol_timer: GLib.source_remove(self._vol_timer)
        self._vol_timer=GLib.timeout_add(150,self._apply_volume)

    def _apply_volume(self):
        self._vol_timer=None
        if self._vol_pending is not None: run_bg(set_volume_cmd,self._vol_pending)
        return False

    def _on_theme_sw(self,sw,state):
        self._dark=state
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if state else Adw.ColorScheme.FORCE_LIGHT)
        self._theme_lbl.set_label("Oscuro" if state else "Claro")
        self._theme_btn.set_icon_name(
            "weather-clear-night-symbolic" if state else "weather-clear-symbolic")

    # ─── Acciones del sistema (TODAS en hilos) ─────────────
    def _do_clean(self,_):
        usuario=os.environ.get('USER','user')
        def _launch():
            # Escribir script temporal para evitar conflictos de comillas con pkexec
            script = f"""#!/bin/bash
echo '========================================='
echo '   OpenDash - Limpieza Profunda'
echo '========================================='
echo
echo '>> Liberando cache del sistema...'
sync
echo 3 > /proc/sys/vm/drop_caches
echo '   OK'
echo
echo '>> Eliminando paquetes huerfanos...'
apt autoremove -y
echo
echo '>> Limpiando cache de apt...'
apt clean
echo
echo '>> Vaciando papelera...'
rm -rf /home/{usuario}/.local/share/Trash/files/* 2>/dev/null || true
rm -rf /home/{usuario}/.local/share/Trash/info/* 2>/dev/null || true
echo '   OK'
echo
echo '========================================='
echo '   Limpieza completada exitosamente'
echo '========================================='
echo
read -p 'Presione Enter para cerrar...'
"""
            script_path = '/tmp/opendash_clean.sh'
            try:
                with open(script_path, 'w') as f:
                    f.write(script)
                import stat
                os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except Exception as e:
                GLib.idle_add(self._toast, f"Error preparando limpieza: {e}")
                return
            launched = False
            for term in ["x-terminal-emulator","xterm","mate-terminal","gnome-terminal","konsole"]:
                try:
                    subprocess.Popen([term, "-e", "pkexec", "bash", script_path])
                    launched = True
                    break
                except FileNotFoundError:
                    continue
            if not launched:
                GLib.idle_add(self._toast, "No se encontró un emulador de terminal")
        run_bg(_launch)
        self._toast("Limpieza profunda iniciada...")

    def _do_optimize_ram(self,_):
        def _run():
            try:
                r=subprocess.run(["pkexec","sh","-c","sync; echo 3 > /proc/sys/vm/drop_caches"],
                                 capture_output=True,timeout=15)
                GLib.idle_add(self._toast,"¡Memoria RAM optimizada!" if r.returncode==0
                              else "No se pudo optimizar RAM")
            except subprocess.TimeoutExpired:
                GLib.idle_add(self._toast,"Tiempo de espera agotado")
            except Exception as e:
                GLib.idle_add(self._toast,f"Error: {e}")
        run_bg(_run)

    # ─── Ticks UI (solo actualizan widgets, datos ya en cache) ─
    def _tick_ui(self):
        m=self._metrics
        if not m: return True
        try:
            cpu=m.get('cpu',0)
            self._card_cpu.update(f"{int(cpu)}%",cpu); self._graph_cpu.push(cpu)
            ru=m.get('ram_used',0); rp=m.get('ram_pct',0)
            self._card_ram.update(f"{ru:.1f}G",rp); self._graph_ram.push(rp)
            df=m.get('disk_free',0); dp2=m.get('disk_pct',0)
            self._card_disk.update(f"{df:.0f}G",dp2)
            temp=m.get('temp')
            if temp is not None:
                self._card_temp.update(f"{int(temp)}°",min(temp,100))
                self._graph_temp.push(min(temp,100))
                self._temp_detail_lbl.set_label(f"CPU: {int(temp)} °C")
            else:
                self._card_temp.update("N/A",0)
                self._temp_detail_lbl.set_label("Sensor no detectado")
            diff=m.get('net_diff',0); np2=min(diff/500*100,100)
            self._graph_net.push(np2); self._graph_net_monitor.push(np2)
            self._graph_net_tab.push(np2)
            self._net_detail_lbl.set_label(
                f"↓ Recibido:  {m.get('net_recv',0):.2f} GB\n"
                f"↑ Enviado:   {m.get('net_sent',0):.2f} GB\n"
                f"Velocidad:   {diff:.1f} KB/s")
            ifaces=m.get('ifaces',{})
            self._iface_lbl.set_label(
                '\n'.join(f"🌐  {n.upper():<12} IP: {ip}" for n,ip in ifaces.items())
                or "Sin interfaz activa")
        except Exception: pass
        return True

    def _tick_procs_ui(self):
        try:
            txt=getattr(self,'_procs_text','—')
            self._proc_lbl.set_label(txt); self._net_proc_lbl.set_label(txt)
        except Exception: pass
        return True

# ─── App ──────────────────────────────────────────────────
class OpenDashApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='io.github.Tavo78ok.OpenDash',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate',self._activate)
    def _activate(self,_): OpenDashWindow(self).present()

if __name__=='__main__':
    import sys
    sys.exit(OpenDashApp().run(sys.argv))

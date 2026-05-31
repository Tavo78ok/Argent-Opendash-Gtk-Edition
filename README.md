## ArgOs OpenDash GTK4

### Monitor, Optimizador y Gestor del Sistema — ArgOs Platinum Edition

![GTK4](https://img.shields.io/badge/GTK-4.0-brightgreen?style=flat-square)
![Libadwaita](https://img.shields.io/badge/libadwaita-1.x-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow?style=flat-square)
![Version](https://img.shields.io/badge/Versión-3.0-purple?style=flat-square)
![License](https://img.shields.io/badge/Licencia-MIT-lightgrey?style=flat-square)
![Platform](https://img.shields.io/badge/Plataforma-Debian%20%2F%20Ubuntu-orange?style=flat-square)

---

## Descripción

**ArgOs OpenDash GTK4** es un dashboard de rendimiento y gestión del sistema diseñado para **ArgOs Platinum Edition**. Construido con **GTK4 + libadwaita**, ofrece monitoreo en tiempo real con estética neon sobre fondo oscuro, gráficos históricos animados, gestión completa de paquetes APT y Flatpak, y herramientas de administración del sistema.

---

## Capturas

> Dashboard principal con ring meters, gráficos históricos, particiones con LevelBar y especificaciones del sistema.

---

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-00-48" src="https://github.com/user-attachments/assets/d759f050-abce-4ca2-9736-9749fd0985ba" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-01-02" src="https://github.com/user-attachments/assets/95b02bfc-febc-4ceb-a0e5-620bc6f209c3" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-01-13" src="https://github.com/user-attachments/assets/ff6b8e1e-300b-4cf5-ba0d-4ee6d7ca9f6c" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-01-31" src="https://github.com/user-attachments/assets/2aa3879f-ed6c-48c4-ab9b-6f56965bb7a1" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-01-48" src="https://github.com/user-attachments/assets/2716bee2-d624-49fd-b533-1a99d1926bc1" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-02-01" src="https://github.com/user-attachments/assets/71490b28-fa42-45dc-b8ca-9bf51599143a" />

<img width="1440" height="900" alt="Captura de pantalla de 2026-05-31 19-02-13" src="https://github.com/user-attachments/assets/bc58f685-730a-4a53-9622-e20034bcfd07" />


## Funciones por pestaña

### 🖥️ Dashboard
- **4 Ring meters** animados con Cairo: CPU, RAM, Disco, Temperatura
- **Gráficos históricos** en tiempo real: CPU, RAM y Red (últimos 60 segundos)
- **Particiones montadas** con LevelBar, tamaño usado/total y porcentaje — refresco automático cada 30 segundos
- **Especificaciones del sistema**: OS, HOST, KERNEL, CPU, GPU, RAM total, paquetes instalados, uptime e IP de red
- Botones de acción rápida: **Optimizar RAM** y **Limpieza Profunda**

### 📊 Monitor
- Temperatura CPU/GPU en tiempo real con gráfico histórico
- Estadísticas de red: bytes recibidos/enviados y velocidad actual con gráfico
- **Todos los procesos activos** ordenados por CPU, con scroll y texto seleccionable

### 🚀 Gamer
- Perfiles de energía con highlight neon al activar:
  - 🍃 **Modo Ahorro** — reduce frecuencia del CPU
  - ⚖️ **Modo Balanceado** — equilibrio temperatura/velocidad
  - 🔥 **Modo Gamer** — máxima performance
- El perfil se guarda y restaura al abrir la app

### 📦 Software
- **Switcher APT / Flatpak** con transición animada
- **APT**: lista con nombre, descripción y tamaño; panel de detalle con versión, arquitectura y sección; instalar y desinstalar con confirmación
- **Flatpak**: lista con App ID, versión, tamaño y origen; desinstalar con confirmación; copiar App ID al portapapeles
- Búsqueda en tiempo real en ambas listas

### ⚙️ Inicio
- Gestión de apps de **autostart** (`~/.config/autostart`)
- Toggle activar/desactivar por app sin salir de la interfaz

### 🔧 Servicios
- Lista completa de **servicios systemd** con estado en tiempo real
- Indicadores: 🟢 Activo / ⚫ Inactivo / 🔴 Fallido
- Búsqueda por nombre o descripción
- Iniciar/detener con autenticación via `pkexec`

### 🎛️ Controles
- Toggle **Iniciar con el sistema** — agrega/elimina el `.desktop` de autostart
- Slider de **brillo de pantalla** con debounce 250ms (soporta backlight físico, brightnessctl y xrandr)
- Slider de **volumen del sistema** con debounce 150ms via `pactl`
- **TRIM SSD** — ejecuta `fstrim -av` con pkexec, muestra particiones trimmeadas
- Toggle **tema claro/oscuro** sincronizado con el botón del header

---

## Instalación

### Opción 1 — Paquete .deb (recomendado)

```bash
sudo dpkg -i argos-opendash_3.0_all.deb
```

El script de post-instalación detecta e instala automáticamente todas las dependencias necesarias.

### Opción 2 — Desde el código fuente

```bash
sudo apt install python3 python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 python3-pip \
    brightnessctl pulseaudio-utils power-profiles-daemon \
    policykit-1 flatpak

pip3 install psutil --break-system-packages

python3 opendash.py
```

---

## Dependencias

| Paquete | Uso | Tipo |
|---|---|---|
| `python3-gi` | Bindings GTK4/Adwaita | Requerido |
| `gir1.2-gtk-4.0` | GTK4 | Requerido |
| `gir1.2-adw-1` | libadwaita | Requerido |
| `python3-gi-cairo` | Gráficos Cairo | Requerido |
| `psutil` | Métricas del sistema | Requerido |
| `brightnessctl` | Control de brillo | Opcional |
| `pulseaudio-utils` | Control de volumen (`pactl`) | Opcional |
| `power-profiles-daemon` | Perfiles de energía | Opcional |
| `policykit-1` | Autenticación `pkexec` | Opcional |
| `flatpak` | Gestión de apps Flatpak | Opcional |

---

## Construir el .deb desde el fuente

```bash
git clone https://github.com/Tavo78ok/Opendash-Gtk-Edition
cd Opendash-Gtk-Edition
chmod +x build-deb.sh
./build-deb.sh
```

---

## Arquitectura

```
opendash.py
├── Helpers UI (lbl, vbox, hbox, spacer, clear...)
├── Hardware helpers
│   ├── get_cpu_model, get_temp
│   ├── get/set_volume_cmd
│   └── get/set_brightness_cmd  (3 métodos: backlight, brightnessctl, xrandr)
├── RingMeter          — gauge circular Cairo animado
├── HistoryGraph       — gráfico de línea histórico Cairo
├── MetricCard         — tarjeta con ring + valor + etiqueta
├── _run_in_terminal   — lanzador de scripts con pkexec
└── OpenDashWindow     — ventana principal (7 pestañas)
    ├── Hilos de datos
    │   ├── _start_metrics_thread  (CPU/RAM/temp/red cada 1s)
    │   ├── _start_procs_thread    (procesos cada 3s)
    │   └── _load_partitions_bg    (particiones cada 30s)
    ├── Dashboard  — ring meters + gráficos + particiones + specs
    ├── Monitor    — temperatura + red + todos los procesos
    ├── Gamer      — perfiles de energía
    ├── Software   — APT stack + Flatpak stack
    ├── Inicio     — autostart manager
    ├── Servicios  — systemd manager
    └── Controles  — autostart propio + brillo + volumen + TRIM + tema
```

---

## Comando en terminal

```bash
argos-opendash
```

---

## Changelog

### v3.0 (Mayo 2026)
- Nuevo nombre: **ArgOs OpenDash GTK4**
- Dashboard: particiones montadas con LevelBar (hilo dedicado, refresco cada 30s)
- Dashboard: especificaciones mejoradas con CPU, GPU, RAM total e IP de red
- Software: pestaña **APT + Flatpak** con switcher animado
- Controles: toggle **Iniciar con el sistema**
- Controles: botón **TRIM SSD** (`fstrim -av`)
- Eliminadas pestañas Red y Repositorios
- Rendimiento mejorado: particiones en hilo separado, debounce en sliders
- UI más compacta: ventana 980×680, ring meters 76px, márgenes reducidos

### v2.1
- Migración completa a GTK4 + libadwaita
- Todas las operaciones bloqueantes en hilos daemon
- Brillo con debounce + fallback xrandr
- Tab Software con detalle de paquetes, instalar/desinstalar
- Tab Servicios systemd con pkexec
- Sistema de notificaciones con Adw.Toast

### v2.0
- Primera versión GTK4/libadwaita
- Ring meters Cairo, gráficos históricos
- 8 pestañas: Dashboard, Monitor, Gamer, Red, Software, Inicio, Servicios, Controles

### v1.5
- Dashboard con CustomTkinter
- Perfiles de energía, limpieza del sistema

---

## Autor

**Tavo** ([@Tavo78ok](https://github.com/Tavo78ok))
Proyecto: **ArgOs Platinum Edition**
Licencia: MIT


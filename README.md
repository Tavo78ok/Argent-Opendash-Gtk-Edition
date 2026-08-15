## ArgentOs OpenDash GTK4

### Monitor, Optimizador y Gestor del Sistema — ArgentOs Platinum Edition

![GTK4](https://img.shields.io/badge/GTK-4.0-brightgreen?style=flat-square)
![Libadwaita](https://img.shields.io/badge/libadwaita-1.x-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow?style=flat-square)
![Version](https://img.shields.io/badge/Versión-3.0-purple?style=flat-square)
![License](https://img.shields.io/badge/Licencia-MIT-lightgrey?style=flat-square)
![Platform](https://img.shields.io/badge/Plataforma-Debian%20%2F%20Ubuntu-orange?style=flat-square)


Monitor, optimizador y gestor del sistema para Linux, escrito en **Python + GTK4 + libadwaita**, con una interfaz de estética neón sobre fondo oscuro (o claro).

---


<img width="1440" height="900" alt="Captura de pantalla de 2026-08-06 17-10-48" src="https://github.com/user-attachments/assets/f8886291-91e7-467d-a9af-bea0c7e72871" />

---

## ✨ Características

**Dashboard**
- Medidores en tiempo real de CPU, RAM, disco y temperatura.
- Gráficas históricas de CPU, RAM y red.
- Estado de particiones y especificaciones del sistema (host, kernel, CPU, GPU, RAM, paquetes instalados).

**Monitor**
- Temperatura y red con gráficas dedicadas.
- Lista de procesos ordenados por uso de CPU.

**Gamer**
- Perfiles de energía (Rendimiento / Balanceado / Ahorro) vía `power-profiles-daemon`.

**Software**
- Gestor de paquetes **APT**: buscar, instalar, desinstalar, ver detalle (versión, tamaño, arquitectura, sección, descripción).
- Gestor de apps **Flatpak**: buscar, desinstalar, ver detalle.

**Inicio**
- Activar/desactivar aplicaciones del autostart de la sesión.

**Servicios**
- Ver, filtrar, activar, desactivar y reiniciar unidades **systemd**.

**Controles**
- Autostart de la propia app.
- Brillo de pantalla (backlight físico, `brightnessctl` o `xrandr` según disponibilidad).
- Volumen del sistema.
- TRIM de SSD (`fstrim -av`).
- Tema claro / oscuro.

**Extra**
- Ícono opcional en la bandeja del sistema (accesos rápidos a optimizar RAM, limpieza, TRIM y mostrar/ocultar ventana).
- Acciones de mantenimiento: limpieza de caché de RAM, papelera y APT; optimización de RAM.

---

## 📋 Requisitos

| Componente | Paquete (Debian/Ubuntu) | Uso |
|---|---|---|
| Python 3.8+ | `python3` | Runtime |
| PyGObject | `python3-gi` | Bindings GTK/Adw |
| GTK4 | `gir1.2-gtk-4.0` | Interfaz gráfica |
| libadwaita | `gir1.2-adw-1` | Estilo/adaptación GNOME |
| psutil | `python3-psutil` | Métricas de sistema |
| polkit | `policykit-1` o `pkexec` | Acciones con privilegios |

Opcionales (habilitan funciones puntuales; si faltan, esa función se degrada o se avisa en la UI):

| Paquete | Habilita |
|---|---|
| `python3-pystray` + `python3-pil` | Ícono en la bandeja del sistema |
| `brightnessctl` | Control de brillo en más equipos |
| `power-profiles-daemon` | Pestaña Gamer (perfiles de energía) |
| `flatpak` | Gestor de apps Flatpak |

---

## 📦 Instalación

### Opción A — Paquete `.deb` (recomendado en Debian/Ubuntu y derivados)

```bash
git clone https://github.com/Tavo78ok/Argent-Opendash-Gtk4-libadwaita.git
cd Argent-Opendash-Gtk4-libadwaita
./build-deb.sh
sudo apt install ./dist/argent-opendash_3.1_all.deb
```

`build-deb.sh` arma el `.deb` a partir de `opendash.py` y de lo que hay en `packaging/` (lanzador `.desktop` e íconos), y lo deja en `dist/`. Instala el ejecutable en `/usr/bin/argent-opendash`, el lanzador en el menú de aplicaciones y los íconos en `hicolor` y `pixmaps`.

Para desinstalar:

```bash
sudo apt remove argent-opendash
```

### Opción B — Ejecución directa (sin empaquetar)

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil
python3 opendash.py
```

---

## ▶️ Uso

Abrí **Argent Opendash Gtk4 libadwaita** desde el menú de aplicaciones, o ejecutá `argent-opendash` en una terminal. Las acciones que modifican el sistema (limpieza, TRIM, optimizar RAM, cambiar perfiles de energía, gestionar servicios/paquetes) piden autenticación mediante `pkexec` cuando corresponde.

---

## 🏗️ Arquitectura del código

`opendash.py` está organizado en secciones numeradas dentro del propio archivo:

1. Constantes y paleta
2. CSS
3. Helpers de UI
4. Capa de hardware (toda la lógica de sistema, con timeout en cada llamada)
5. Widgets Cairo (medidores y gráficas)
6. Ventana principal
   - 6a. Construcción de pestañas (solo UI)
   - 6b. Manejadores de eventos
   - 6c. Hilos de datos (con timeout en cada llamada)
   - 6d. Acciones del sistema
   - 6e. Tick de UI
7. Entrada de la app

---
## Dona para seguir este proyecto:

*Mercado Pago:
tavo.78.ok

*Paypal:
https://paypal.me/GustavoCuevas582

## 🤝 Contribuir

Los *pull requests* son bienvenidos. Para cambios grandes, abrí primero un *issue* para discutir qué te gustaría modificar.

---

## 📄 Licencia

MIT © Tavo78ok — ver [LICENSE](LICENSE).


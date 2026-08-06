#!/usr/bin/env bash
#
# build-deb.sh — Empaqueta Argent Opendash Gtk4 libadwaita en un .deb instalable.
#
# Uso:
#   ./build-deb.sh
#   DEB_MAINTAINER="Tavo78ok <el-tavo78@hotmail.com>" ./build-deb.sh
#
# Requiere: dpkg-deb (paquete 'dpkg-dev' en Debian/Ubuntu)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

SRC="opendash.py"
DESKTOP_SRC="packaging/argent-opendash.desktop"

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "✗ Falta dpkg-deb. Instalalo con: sudo apt install dpkg-dev" >&2
    exit 1
fi
if [[ ! -f "$SRC" ]]; then
    echo "✗ No se encontró '$SRC' en $ROOT" >&2
    exit 1
fi
if [[ ! -f "$DESKTOP_SRC" ]]; then
    echo "✗ No se encontró '$DESKTOP_SRC'" >&2
    exit 1
fi

# ── Metadatos, extraídos directamente del script para no duplicarlos ──
extract() { grep -m1 "^$1" "$SRC" | sed -E "s/.*=[[:space:]]*'([^']*)'.*/\1/"; }
APP_NAME="$(extract APP_NAME)"
APP_VERSION="$(extract APP_VERSION)"
BINARY="$(extract BINARY)"
ARCH="all"
MAINTAINER="${DEB_MAINTAINER:-Gustavo <el-tavo78@hotmail.com>}"
ICON_SRC="packaging/icons/${BINARY}.png"

if [[ -z "$APP_NAME" || -z "$APP_VERSION" || -z "$BINARY" ]]; then
    echo "✗ No se pudieron leer APP_NAME/APP_VERSION/BINARY desde $SRC" >&2
    exit 1
fi
if [[ ! -f "$ICON_SRC" ]]; then
    echo "✗ No se encontró el ícono '$ICON_SRC'" >&2
    exit 1
fi

echo "→ Empaquetando: $APP_NAME  v$APP_VERSION  ($BINARY, $ARCH)"

BUILD_DIR="$ROOT/build"
PKG="$BUILD_DIR/pkgroot"
DIST_DIR="$ROOT/dist"

rm -rf "$BUILD_DIR"
mkdir -p \
    "$PKG/DEBIAN" \
    "$PKG/usr/bin" \
    "$PKG/usr/share/applications" \
    "$PKG/usr/share/icons/hicolor/256x256/apps" \
    "$PKG/usr/share/pixmaps" \
    "$PKG/usr/share/doc/$BINARY"
mkdir -p "$DIST_DIR"

# ── Binario ──
install -Dm755 "$SRC" "$PKG/usr/bin/$BINARY"

# ── Lanzador de escritorio ──
install -Dm644 "$DESKTOP_SRC" "$PKG/usr/share/applications/${BINARY}.desktop"

# ── Íconos (hicolor + fallback pixmaps, igual que busca el tray en el código) ──
install -Dm644 "$ICON_SRC" "$PKG/usr/share/icons/hicolor/256x256/apps/${BINARY}.png"
install -Dm644 "$ICON_SRC" "$PKG/usr/share/pixmaps/${BINARY}.png"

# ── Copyright / licencia ──
cat > "$PKG/usr/share/doc/$BINARY/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Argent Opendash Gtk4 libadwaita
Source: https://github.com/Tavo78ok/Argent-Opendash-Gtk4-libadwaita

Files: *
Copyright: Tavo78ok
License: MIT

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a
 copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to
 the following conditions:
 .
 The above copyright notice and this permission notice shall be included
 in all copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
EOF

# ── control ──
INSTALLED_SIZE="$(du -sk "$PKG" | cut -f1)"

cat > "$PKG/DEBIAN/control" <<EOF
Package: $BINARY
Version: $APP_VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.8), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, python3-psutil, power-profiles-daemon, policykit-1 | pkexec
Recommends: python3-pystray, python3-pil, brightnessctl, power-profiles-daemon, flatpak
Maintainer: $MAINTAINER
Homepage: https://github.com/Tavo78ok/Argent-Opendash-Gtk4-libadwaita
Description: Monitor, optimizador y gestor del sistema (GTK4 + libadwaita)
 $APP_NAME es un panel de control de escritorio para Linux escrito en
 Python, GTK4 y libadwaita. Monitorea CPU, RAM, disco, temperatura y
 red en tiempo real; gestiona paquetes APT y Flatpak, servicios
 systemd y aplicaciones de autostart; aplica perfiles de energia; y
 ejecuta tareas de mantenimiento (limpieza de cache, optimizacion de
 RAM, TRIM de SSD) desde una interfaz con estetica neon.
EOF

chmod 755 "$PKG/DEBIAN"
find "$PKG" -type d -exec chmod 755 {} \;

DEB_FILE="$DIST_DIR/${BINARY}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$PKG" "$DEB_FILE"

echo
echo "✓ Paquete generado: $DEB_FILE"
echo
echo "Instalar con:"
echo "  sudo apt install \"$DEB_FILE\""
echo "  # o bien: sudo dpkg -i \"$DEB_FILE\" && sudo apt -f install"
       


    
 

#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  Argent Opendash Gtk4 libadwaita v3.1.3 — build-appimage.sh
#  Uso: chmod +x build-appimage.sh && ./build-appimage.sh
#
#  Requiere en el sistema host:
#    python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1
# ═══════════════════════════════════════════════════════════
set -e

NAME="ArgentOpendash"
VERSION="1.0"
ARCH="x86_64"
OUT="${NAME}-${VERSION}-${ARCH}.AppImage"
APPDIR="${NAME}.AppDir"
ID="io.github.Tavo78ok.ArgentOpendash"

G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

echo -e "\n${C}╔══════════════════════════════════════════╗"
echo -e "║  Argent Opendash Gtk4 v${VERSION} — AppImage   ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"

[ ! -f "argent-opendash.py" ] && echo -e "${R}✗ argent-opendash.py no encontrado${N}" && exit 1

echo -e "${Y}▶ Verificando GTK4...${N}"
python3 -c "
import gi
gi.require_version('Gtk','4.0')
gi.require_version('Adw','1')
from gi.repository import Gtk, Adw
" 2>/dev/null || {
    echo -e "${R}✗ GTK4/libadwaita no disponible${N}"
    echo "  sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 libadwaita-1-0"
    exit 1
}
echo -e "${G}  ✓ GTK4 + libadwaita OK${N}"

echo -e "${Y}▶ appimagetool...${N}"
if command -v appimagetool &>/dev/null; then
    TOOL=appimagetool
    echo -e "${G}  ✓ encontrado${N}"
else
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O /tmp/appimagetool
    chmod +x /tmp/appimagetool
    TOOL=/tmp/appimagetool
    echo -e "${G}  ✓ descargado${N}"
fi

echo -e "${Y}▶ Creando AppDir...${N}"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/argent-opendash"
mkdir -p "$APPDIR/usr/lib/python-packages"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/48x48/apps"
echo -e "${G}  ✓${N}"

echo -e "${Y}▶ Bundleando dependencias Python...${N}"
pip3 install psutil pystray Pillow \
    --target="$APPDIR/usr/lib/python-packages" \
    --quiet --no-deps 2>/dev/null || \
pip3 install psutil pystray Pillow \
    --target="$APPDIR/usr/lib/python-packages" \
    --quiet 2>/dev/null
echo -e "${G}  ✓ psutil, pystray, Pillow${N}"

echo -e "${Y}▶ Copiando app...${N}"
cp argent-opendash.py "$APPDIR/usr/lib/argent-opendash/argent-opendash.py"
chmod 644 "$APPDIR/usr/lib/argent-opendash/argent-opendash.py"

ICO="argent-opendash.png"
if [ -f "$ICO" ]; then
    cp "$ICO" "$APPDIR/argent-opendash.png"
    cp "$ICO" "$APPDIR/usr/share/icons/hicolor/256x256/apps/argent-opendash.png"
    command -v convert &>/dev/null && {
        convert "$ICO" -resize 128x128 \
            "$APPDIR/usr/share/icons/hicolor/128x128/apps/argent-opendash.png"
        convert "$ICO" -resize 48x48 \
            "$APPDIR/usr/share/icons/hicolor/48x48/apps/argent-opendash.png"
    }
    echo -e "${G}  ✓ Íconos${N}"
else
    echo -e "${Y}  ⚠ argent-opendash.png no encontrado${N}"
    python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA',(64,64),(0,0,0,0))
d = ImageDraw.Draw(img)
d.ellipse([4,4,60,60],fill=(0,255,163,255))
d.ellipse([18,18,46,46],fill=(14,15,20,255))
img.save('$APPDIR/argent-opendash.png','PNG')
" 2>/dev/null || true
fi

cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$APPDIR/usr/lib/python-packages:${PYTHONPATH:-}"
exec python3 "$APPDIR/usr/lib/argent-opendash/argent-opendash.py" "$@"
APPRUN
chmod 755 "$APPDIR/AppRun"

cat > "$APPDIR/usr/share/applications/${ID}.desktop" << DESKTOP
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Argent Opendash Gtk4 libadwaita
GenericName=Monitor del Sistema
Comment=Monitor, Optimizador y Gestor del Sistema Argent Platinum
Exec=argent-opendash
Icon=argent-opendash
Terminal=false
Categories=System;Monitor;
Keywords=system;monitor;cpu;ram;temperatura;servicios;
StartupNotify=true
X-AppImage-Version=${VERSION}
DESKTOP
cp "$APPDIR/usr/share/applications/${ID}.desktop" "$APPDIR/${ID}.desktop"

echo -e "${Y}▶ Construyendo ${OUT}...${N}"
ARCH=x86_64 "$TOOL" --no-appstream "$APPDIR" "$OUT" 2>/dev/null \
    || ARCH=x86_64 "$TOOL" "$APPDIR" "$OUT"

SZ=$(du -h "$OUT" | cut -f1)
echo -e "\n${G}╔══════════════════════════════════════════════════╗"
echo -e "║  ✅ ${OUT} (${SZ}) listo"
echo -e "╚══════════════════════════════════════════════════╝${N}\n"
echo "  Ejecutar:   chmod +x ${OUT} && ./${OUT}"
echo "  Limpiar:    rm -rf ${APPDIR}"

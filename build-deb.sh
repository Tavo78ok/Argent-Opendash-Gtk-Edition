#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  Argent Opendash Gtk4 libadwaita v3.1 — build-deb.sh
#  Uso: chmod +x build-deb.sh && ./build-deb.sh
# ═══════════════════════════════════════════════════════════
set -e

PKG="argent-opendash"
VERSION="3.1"
ARCH="all"
DEB="${PKG}_${VERSION}_${ARCH}.deb"
DIR="deb_build/${PKG}_${VERSION}_${ARCH}"
BIN="argent-opendash"
LIB="usr/lib/argent-opendash"

G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; R='\033[0;31m'; N='\033[0m'

echo -e "\n${C}╔══════════════════════════════════════════╗"
echo -e "║  Argent Opendash Gtk4 v${VERSION} — .deb        ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"

[ ! -f "argent-opendash.py" ] && echo -e "${R}✗ argent-opendash.py no encontrado${N}" && exit 1

echo -e "${Y}▶ Herramientas...${N}"
MISS=()
command -v dpkg-deb &>/dev/null || MISS+=("dpkg-dev")
command -v convert  &>/dev/null || MISS+=("imagemagick")
[ ${#MISS[@]} -gt 0 ] && sudo apt-get install -y "${MISS[@]}" -q
echo -e "${G}  ✓${N}"

echo -e "${Y}▶ Estructura...${N}"
rm -rf deb_build
mkdir -p "${DIR}/DEBIAN" "${DIR}/usr/bin" "${DIR}/${LIB}"
mkdir -p "${DIR}/usr/share/applications"
mkdir -p "${DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${DIR}/usr/share/pixmaps"
echo -e "${G}  ✓${N}"

echo -e "${Y}▶ Copiando archivos...${N}"
cp argent-opendash.py "${DIR}/${LIB}/argent-opendash.py"
chmod 644 "${DIR}/${LIB}/argent-opendash.py"

ICO="argent-opendash.png"
if [ -f "$ICO" ]; then
    convert "$ICO" -resize 256x256 "${DIR}/usr/share/icons/hicolor/256x256/apps/argent-opendash.png"
    convert "$ICO" -resize 128x128 "${DIR}/usr/share/icons/hicolor/128x128/apps/argent-opendash.png"
    convert "$ICO" -resize 48x48   "${DIR}/usr/share/icons/hicolor/48x48/apps/argent-opendash.png"
    cp "$ICO" "${DIR}/usr/share/pixmaps/argent-opendash.png"
    echo -e "${G}  ✓ Íconos${N}"
else
    echo -e "${Y}  ⚠ argent-opendash.png no encontrado${N}"
fi

cat > "${DIR}/usr/bin/${BIN}" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/argent-opendash/argent-opendash.py "$@"
EOF
chmod 755 "${DIR}/usr/bin/${BIN}"

cat > "${DIR}/usr/share/applications/argent-opendash.desktop" << DESKTOP
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=Argent Opendash Gtk4 libadwaita
GenericName=Monitor del Sistema
Comment=Monitor, Optimizador y Gestor del Sistema Argent Platinum
Exec=${BIN}
Icon=argent-opendash
Terminal=false
Categories=System;Monitor;
Keywords=system;monitor;cpu;ram;temperatura;servicios;flatpak;
StartupNotify=true
StartupWMClass=argent-opendash
DESKTOP
echo -e "${G}  ✓${N}"

cat > "${DIR}/DEBIAN/control" << CONTROL
Package: ${PKG}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.8), python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1, python3-pip
Maintainer: Tavo (Tavo78ok) <tavo78ok@github.com>
Homepage: https://github.com/Tavo78ok/Argent-Opendash-Gtk4-libadwaita
Description: Argent Opendash Gtk4 libadwaita v${VERSION}
 Dashboard GTK4 + libadwaita. Sin freezes en XFCE ni Cinnamon.
 Temperatura desde sysfs. Deteccion automatica del entorno.
CONTROL

cat > "${DIR}/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; N='\033[0m'
echo -e "\n${C}╔══════════════════════════════════════════╗"
echo -e "║   Argent Opendash Gtk4 v3.1              ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"
apt_q() { DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@" 2>/dev/null; }
py_ok() { python3 -c "import $1" 2>/dev/null; }
pip_q() { pip3 install "$1" --break-system-packages -q 2>/dev/null || pip3 install "$1" -q 2>/dev/null || true; }
echo -e "${Y}▶ psutil...${N}"
py_ok psutil && echo -e "${G}  ✓${N}" || { apt_q python3-psutil 2>/dev/null || pip_q psutil; }
for pkg in gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi python3-gi-cairo libadwaita-1-0; do
    echo -e "${Y}▶ $pkg...${N}"
    dpkg -l "$pkg" 2>/dev/null | grep -q '^ii' && echo -e "${G}  ✓${N}" \
        || { apt_q "$pkg" 2>/dev/null && echo -e "${G}  ✓${N}" || echo -e "${Y}  ⚠ verificá tu distro${N}"; }
done
echo -e "${Y}▶ power-profiles-daemon...${N}"
command -v powerprofilesctl &>/dev/null && echo -e "${G}  ✓${N}" \
    || { apt_q power-profiles-daemon 2>/dev/null && echo -e "${G}  ✓${N}" \
        || echo -e "${Y}  ⚠ sudo apt install power-profiles-daemon${N}"; }
for pkg in policykit-1 brightnessctl pulseaudio-utils flatpak; do
    echo -e "${Y}▶ $pkg (opcional)...${N}"
    dpkg -l "$pkg" 2>/dev/null | grep -q '^ii' && echo -e "${G}  ✓${N}" \
        || { apt_q "$pkg" 2>/dev/null && echo -e "${G}  ✓${N}" || echo -e "${Y}  ⚠ opcional${N}"; }
done
echo -e "${Y}▶ pystray (bandeja)...${N}"
py_ok pystray && echo -e "${G}  ✓${N}" \
    || { pip_q pystray && echo -e "${G}  ✓${N}" || echo -e "${Y}  ⚠ pip3 install pystray${N}"; }
chmod +x /usr/bin/argent-opendash /usr/lib/argent-opendash/argent-opendash.py
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo -e "\n${G}╔══════════════════════════════════════════╗"
echo -e "║  ✅ Argent Opendash Gtk4 v3.1 instalado  ║"
echo -e "║  Terminal: argent-opendash                ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"
exit 0
POSTINST
chmod 755 "${DIR}/DEBIAN/postinst"

printf '#!/bin/bash\nupdate-desktop-database /usr/share/applications/ 2>/dev/null || true\nexit 0\n' \
    > "${DIR}/DEBIAN/prerm"
chmod 755 "${DIR}/DEBIAN/prerm"

echo -e "${Y}▶ Construyendo ${DEB}...${N}"
dpkg-deb --build --root-owner-group "${DIR}" "${DEB}"

SZ=$(du -h "${DEB}" | cut -f1)
echo -e "\n${G}╔══════════════════════════════════════════════════╗"
echo -e "║  ✅ ${DEB} (${SZ}) listo"
echo -e "╚══════════════════════════════════════════════════╝${N}\n"
echo "  Instalar:     sudo dpkg -i ${DEB}"
echo "  Limpiar:      rm -rf deb_build"

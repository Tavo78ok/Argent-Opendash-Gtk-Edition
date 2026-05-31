#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  ArgOs OpenDash GTK4 v3.0 — build-deb.sh
#  Construye el paquete .deb listo para distribuir
#
#  Uso:
#    chmod +x build-deb.sh
#    ./build-deb.sh
#
#  Requiere: dpkg-deb, imagemagick (para íconos)
# ═══════════════════════════════════════════════════════════

set -e

PKG="argos-opendash"
VERSION="3.0"
ARCH="all"
DEB_NAME="${PKG}_${VERSION}_${ARCH}.deb"
BUILD_DIR="deb_build/${PKG}_${VERSION}_${ARCH}"
BINARY="argos-opendash"
LIB_DIR="usr/lib/argos-opendash"

G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; N='\033[0m'

echo -e "\n${C}╔══════════════════════════════════════════╗"
echo -e "║   ArgOs OpenDash GTK4 v${VERSION} — Build .deb  ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"

# ── 1. Dependencias de construcción ─────────────────────────
echo -e "${Y}▶ Verificando herramientas...${N}"
MISSING=()
command -v dpkg-deb &>/dev/null || MISSING+=("dpkg-dev")
command -v convert  &>/dev/null || MISSING+=("imagemagick")
if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  Instalando: ${MISSING[*]}"
    sudo apt-get install -y "${MISSING[@]}" -q
fi
echo -e "${G}  ✓ OK${N}"

# ── 2. Verificar código fuente ───────────────────────────────
if [ ! -f "opendash.py" ]; then
    echo -e "\n${Y}  ✗ No se encontró opendash.py en el directorio actual.${N}"
    echo "    Ejecutá este script desde la raíz del repositorio."
    exit 1
fi

# ── 3. Estructura ────────────────────────────────────────────
echo -e "${Y}▶ Creando estructura...${N}"
rm -rf deb_build
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/${LIB_DIR}"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${BUILD_DIR}/usr/share/pixmaps"
echo -e "${G}  ✓ OK${N}"

# ── 4. Archivos ──────────────────────────────────────────────
echo -e "${Y}▶ Copiando archivos...${N}"
cp opendash.py "${BUILD_DIR}/${LIB_DIR}/opendash.py"
chmod 644 "${BUILD_DIR}/${LIB_DIR}/opendash.py"

if [ -f "argos-opendash.png" ]; then
    convert argos-opendash.png -resize 256x256 \
        "${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/argos-opendash.png"
    convert argos-opendash.png -resize 128x128 \
        "${BUILD_DIR}/usr/share/icons/hicolor/128x128/apps/argos-opendash.png"
    convert argos-opendash.png -resize 48x48 \
        "${BUILD_DIR}/usr/share/icons/hicolor/48x48/apps/argos-opendash.png"
    cp argos-opendash.png "${BUILD_DIR}/usr/share/pixmaps/argos-opendash.png"
    echo -e "${G}  ✓ Íconos generados${N}"
else
    echo -e "${Y}  ⚠ argos-opendash.png no encontrado — sin ícono${N}"
fi

# ── 5. Launcher ──────────────────────────────────────────────
cat > "${BUILD_DIR}/usr/bin/${BINARY}" << 'LAUNCHER'
#!/bin/bash
exec python3 /usr/lib/argos-opendash/opendash.py "$@"
LAUNCHER
chmod 755 "${BUILD_DIR}/usr/bin/${BINARY}"

# ── 6. .desktop ──────────────────────────────────────────────
cat > "${BUILD_DIR}/usr/share/applications/argos-opendash.desktop" << DESKTOP
[Desktop Entry]
Version=${VERSION}
Type=Application
Name=ArgOs OpenDash GTK4
GenericName=Monitor del Sistema
Comment=Monitor, Optimizador y Gestor del Sistema ArgOs Platinum
Exec=${BINARY}
Icon=argos-opendash
Terminal=false
Categories=System;Monitor;
Keywords=system;monitor;cpu;ram;temperatura;servicios;flatpak;
StartupNotify=true
StartupWMClass=argos-opendash
DESKTOP

# ── 7. control ───────────────────────────────────────────────
cat > "${BUILD_DIR}/DEBIAN/control" << CONTROL
Package: ${PKG}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Conflicts: opendash
Replaces: opendash
Depends: python3 (>= 3.8), python3-gi, python3-gi-cairo, gir1.2-gtk-4.0, gir1.2-adw-1, python3-pip
Maintainer: Tavo (Tavo78ok) <tavo78ok@github.com>
Homepage: https://github.com/Tavo78ok/Opendash-Gtk-Edition
Description: ArgOs OpenDash GTK4 v${VERSION} - Monitor y Gestor del Sistema
 Dashboard GTK4 + libadwaita con 7 pestanas: Dashboard con particiones
 y especificaciones, Monitor, Gamer, Software APT + Flatpak, Inicio,
 Servicios systemd y Controles con brillo, volumen, TRIM y autostart.
CONTROL

# ── 8. postinst ──────────────────────────────────────────────
cat > "${BUILD_DIR}/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e
G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; N='\033[0m'
echo -e "\n${C}╔══════════════════════════════════════════╗"
echo -e "║   ArgOs OpenDash GTK4 v3.0               ║"
echo -e "║   Configurando dependencias...            ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"
apt_q() { DEBIAN_FRONTEND=noninteractive apt-get install -y \
          --no-install-recommends "$@" 2>/dev/null; }
py_ok() { python3 -c "import $1" 2>/dev/null; }
pip_q() { pip3 install "$1" --break-system-packages -q 2>/dev/null \
          || pip3 install "$1" -q 2>/dev/null || true; }
echo -e "${Y}▶ psutil...${N}"
py_ok psutil && echo -e "${G}  ✓${N}" \
    || { apt_q python3-psutil 2>/dev/null || pip_q psutil; }
for pkg in gir1.2-gtk-4.0 gir1.2-adw-1 python3-gi \
           python3-gi-cairo libadwaita-1-0; do
    echo -e "${Y}▶ $pkg...${N}"
    dpkg -l "$pkg" 2>/dev/null | grep -q '^ii' \
        && echo -e "${G}  ✓${N}" \
        || { apt_q "$pkg" 2>/dev/null && echo -e "${G}  ✓${N}" \
            || echo -e "${Y}  ⚠ verificá tu distro${N}"; }
done
for pkg in policykit-1 power-profiles-daemon \
           brightnessctl pulseaudio-utils flatpak; do
    echo -e "${Y}▶ $pkg (opcional)...${N}"
    dpkg -l "$pkg" 2>/dev/null | grep -q '^ii' \
        && echo -e "${G}  ✓${N}" \
        || { apt_q "$pkg" 2>/dev/null && echo -e "${G}  ✓${N}" \
            || echo -e "${Y}  ⚠ opcional${N}"; }
done
chmod +x /usr/bin/argos-opendash /usr/lib/argos-opendash/opendash.py
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo -e "\n${G}╔══════════════════════════════════════════╗"
echo -e "║  ✅ ArgOs OpenDash GTK4 v3.0 instalado   ║"
echo -e "║  Terminal:  argos-opendash                ║"
echo -e "║  Menú:      buscar ArgOs OpenDash         ║"
echo -e "╚══════════════════════════════════════════╝${N}\n"
exit 0
POSTINST
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# ── 9. prerm ─────────────────────────────────────────────────
printf '#!/bin/bash\nupdate-desktop-database /usr/share/applications/ 2>/dev/null || true\nexit 0\n' \
    > "${BUILD_DIR}/DEBIAN/prerm"
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"

# ── 10. Build ────────────────────────────────────────────────
echo -e "${Y}▶ Construyendo ${DEB_NAME}...${N}"
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${DEB_NAME}"

SIZE=$(du -h "${DEB_NAME}" | cut -f1)
echo -e "\n${G}╔══════════════════════════════════════════════════╗"
echo -e "║  ✅ ${DEB_NAME} (${SIZE}) listo"
echo -e "╚══════════════════════════════════════════════════╝${N}\n"
echo "Para instalar:         sudo dpkg -i ${DEB_NAME}"
echo "Para limpiar temp:     rm -rf deb_build"

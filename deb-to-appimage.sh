#!/usr/bin/env bash
# ==============================================================================
# Script para convertir argent-opendash.deb a AppImage
# ==============================================================================

set -e

# --- CONFIGURACIÓN DE TU PAQUETE ---
DEB_FILE="argent-opendash_3.1_all.deb"
APP_NAME="argent-opendash"
APP_VERSION="3.1"

# --- VARIABLES DE ENTORNO Y DIRECTORIOS ---
ARCH=$(uname -m)
BUILD_DIR="build_appimage"
APP_DIR="${BUILD_DIR}/AppDir"
OUTPUT_APPIMAGE="${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

echo "=================================================="
echo " Convirtiendo ${DEB_FILE} a AppImage"
echo "=================================================="

# 1. Comprobar que existe el archivo .deb
if [ ! -f "${DEB_FILE}" ]; then
    echo " [!] Error: No se encuentra '${DEB_FILE}' en el directorio actual."
    exit 1
fi

# 2. Limpieza previa y desempaquetado
rm -rf "${BUILD_DIR}"
mkdir -p "${APP_DIR}"

echo "--> Desempaquetando contenido del paquete .deb..."
dpkg-deb -x "${DEB_FILE}" "${APP_DIR}"

# 3. Obtener appimagetool si no está presente
APPIMAGETOOL="appimagetool-${ARCH}.AppImage"
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "--> Descargando appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage" -O "${APPIMAGETOOL}"
    chmod +x "${APPIMAGETOOL}"
fi

# 4. Ubicar y vincular el archivo .desktop e ícono en la raíz del AppDir
echo "--> Organizando acceso directo e íconos..."
DESKTOP_SRC=$(find "${APP_DIR}/usr/share/applications" -name "*.desktop" 2>/dev/null | head -n 1)
ICON_SRC=$(find "${APP_DIR}/usr/share/icons" -name "*.png" 2>/dev/null | head -n 1)

if [ -n "${DESKTOP_SRC}" ]; then
    cp "${DESKTOP_SRC}" "${APP_DIR}/${APP_NAME}.desktop"
else
    # Si no encuentra .desktop dentro del .deb, crea uno básico
    cat <<EOF > "${APP_DIR}/${APP_NAME}.desktop"
[Desktop Entry]
Type=Application
Name=Argent OpenDash
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=Utility;System;
Terminal=false
EOF
fi

if [ -n "${ICON_SRC}" ]; then
    cp "${ICON_SRC}" "${APP_DIR}/${APP_NAME}.png"
    cp "${ICON_SRC}" "${APP_DIR}/.DirIcon"
else
    touch "${APP_DIR}/${APP_NAME}.png"
fi

# 5. Generar el punto de entrada AppRun
echo "--> Creando script lanzador (AppRun)..."
cat <<EOF > "${APP_DIR}/AppRun"
#!/usr/bin/env bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"

# Configuración de rutas internas
export PATH="\${HERE}/usr/bin:\${PATH}"
export LD_LIBRARY_PATH="\${HERE}/usr/lib:\${LD_LIBRARY_PATH}:\${HERE}/lib"
export XDG_DATA_DIRS="\${HERE}/usr/share:\${XDG_DATA_DIRS}"

# Detectar y ejecutar el ejecutable principal
if [ -f "\${HERE}/usr/bin/${APP_NAME}" ]; then
    exec "\${HERE}/usr/bin/${APP_NAME}" "\$@"
elif [ -f "\${HERE}/usr/bin/opendash" ]; then
    exec "\${HERE}/usr/bin/opendash" "\$@"
else
    # Si ejecuta via script Python dentro de /usr
    PYTHON_SCRIPT=\$(find "\${HERE}/usr" -name "*.py" | head -n 1)
    exec python3 "\${PYTHON_SCRIPT}" "\$@"
fi
EOF

chmod +x "${APP_DIR}/AppRun"

# 6. Empaquetar a AppImage
echo "--> Empaquetando la AppImage final..."
ARCH="${ARCH}" ./"${APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT_APPIMAGE}"

echo "=================================================="
echo " ¡Proceso completado!"
echo " Se generó el archivo: ${OUTPUT_APPIMAGE}"
echo "=================================================="
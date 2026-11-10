#!/usr/bin/env bash
# DevDeck Auto-Installer for Linux & macOS
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "======================================================="
echo "⚡ Installation de DevDeck — Cockpit Développeur"
echo "======================================================="

# 1. Vérification de Python 3
if ! command -v python3 &>/dev/null; then
  echo "❌ Erreur : Python 3 n'est pas installé sur votre machine."
  echo "Veuillez installer Python 3 (ex: sudo apt install python3) puis relancer."
  exit 1
fi

PY_VERSION=$(python3 --version)
echo "✅ Python détecté : $PY_VERSION"

# 2. Permissions d'exécution
chmod +x "$DIR/devdeck"
echo "✅ Permissions d'exécution accordées à ./devdeck"

# 3. Création du raccourci bureau .desktop sous Linux
if [ "$(uname)" = "Linux" ]; then
  DESKTOP_DIR="$HOME/.local/share/applications"
  mkdir -p "$DESKTOP_DIR"
  
  cat > "$DESKTOP_DIR/devdeck.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DevDeck
Comment=Cockpit et gestionnaire de projets pour développeurs
Exec=$DIR/devdeck
Path=$DIR
Icon=utilities-terminal
Terminal=false
Categories=Development;IDE;
StartupNotify=true
EOF

  chmod +x "$DESKTOP_DIR/devdeck.desktop"
  echo "✅ Raccourci application installé dans $DESKTOP_DIR/devdeck.desktop"
fi

# 4. Initialisation du dossier de données local
mkdir -p "$DIR/data"
touch "$DIR/data/.gitkeep"

echo ""
echo "🎉 Installation terminée avec succès !"
echo ""
echo "Pour démarrer DevDeck :"
echo "  👉  ./devdeck"
echo "  ou lancez-le depuis votre menu d'applications !"
echo "======================================================="

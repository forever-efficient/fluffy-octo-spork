#!/bin/bash

# Define venv path
VENV_PATH="/opt/osint-venv"

echo "🔧 Adding OSINT environment helpers to ~/.bashrc..."

cat <<EOL >> ~/.bashrc

# ==== OSINT Environment Shortcuts ====
alias osintenv='source ${VENV_PATH}/bin/activate'
alias spiderfoot='cd /opt/spiderfoot && ${VENV_PATH}/bin/python3 sf.py'
alias osintgram='cd /opt/OSINTgram && ${VENV_PATH}/bin/python3 main.py'
# =====================================
EOL

echo "✅ Shortcuts added:"
echo "🔹 Run 'osintenv' to activate the Python OSINT environment"
echo "🔹 Run 'spiderfoot' to start SpiderFoot"
echo "🔹 Run 'osintgram' to start OSINTgram"

echo "🌀 Reloading shell..."
exec bash

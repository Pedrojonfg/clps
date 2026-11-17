#!/usr/bin/env bash
# Compila (pdflatex) UN frame aislado y lo renderiza a PNG para revisarlo.
# Uso: ./build-frame.sh 07        -> build/f07.pdf y build/f07-<n>.png (una por overlay)
set -euo pipefail
cd "$(dirname "$0")"
n="$1"
f=$(ls frames/${n}-*.tex | head -1)
mkdir -p build
cat > build/f${n}.tex <<EOF
\\documentclass[aspectratio=169,11pt]{beamer}
\\usepackage{theme}
\\begin{document}
\\input{${f%.tex}}
\\end{document}
EOF
TEXINPUTS=".:./build:" /usr/bin/pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build build/f${n}.tex > build/f${n}.log.txt 2>&1 \
  || { grep -n -A5 '^!' build/f${n}.log 2>/dev/null | head -40; echo "FAILED (see build/f${n}.log)"; exit 1; }
# segunda pasada para remember picture
TEXINPUTS=".:./build:" /usr/bin/pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build build/f${n}.tex > /dev/null 2>&1 || true
rm -f build/f${n}-*.png
pdftoppm -png -r 80 build/f${n}.pdf build/f${n}
grep -E "Overfull|Underfull \\\\hbox|LaTeX Warning: File" build/f${n}.log | head -10 || true
ls build/f${n}-*.png

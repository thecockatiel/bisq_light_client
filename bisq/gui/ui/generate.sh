#!/bin/sh

here="$(dirname "$(realpath "$0" 2> /dev/null || grealpath "$0")")"

mkdir -p "$here/out"

rm -rf "$here/out"/*

find "$here" -name "*.ui" | while read ui_file; do
    base_name=$(basename "$ui_file" .ui)
    py_file="$here/out/${base_name}.py"
    pyuic5 --import-from=bisq.gui.ui.out "$ui_file" -o "$py_file"
    echo "Generated $py_file from $ui_file"
done

pyrcc5 "$here/resources.qrc" -o "$here/out/resources_rc.py"
echo "Generated $here/out/resources.py from $here/resources.qrc"
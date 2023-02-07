#!/usr/bin/bash
one=$'web1\nweb2'
two="message: sub1 sub2"
res=$(python ./scripts/update_root_index.py "$one" "$two")
echo "Res: $res"
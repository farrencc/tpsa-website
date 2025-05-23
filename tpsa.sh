#!/bin/bash

# update all by default
src=$(basename -s -body.html content/*-body.html)

# if an arg is passed just update that one
[[ -z $1 ]] || {
  src=$1
  [[ -f content/${src}-body.html ]] || {
    echo no such source file
    exit 1
  }
}

for f in $src; do
  cat templates/header.html content/${f}-body.html templates/footer.html > site/${f}.html
done

ls -l site/*.html

# start the live server
echo "Starting HTML live server..."
DIR=$(pwd)
cd site/ && python -m http.server && cd "$DIR"
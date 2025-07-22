#!/bin/bash

# update all by default
src=$(basename -s -body.html content/*-body.html)

# if an arg is passed just update that one
[[ -z $1 ]] || {
  # Check if first argument is "server"
  if [[ $1 == "server" ]]; then
    # Build all pages first, then start server
    for f in $src; do
      cat templates/header.html content/${f}-body.html templates/footer.html > site/${f}.html
    done
    
    echo "Starting HTML live server..."
    DIR=$(pwd)
    cd site/ && python -m http.server && cd "$DIR"
    exit 0
  fi
}

# Build the pages
for f in $src; do
  cat templates/header.html content/${f}-body.html templates/footer.html > site/${f}.html
done

ls -l site/*.html

echo "Build complete! Run './tpsa.sh server' to start the development server."
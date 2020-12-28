#!/usr/bin/env bash

set -e

cd "$(dirname "$0")"

pyoxidizer build --release
mkdir -p build/dist
cp build/x86_64-apple-darwin/release/exe/synacor-challenge build/dist/
cp docs/dist.txt build/dist/README.md
pushd build
  pushd dist
    codesign -s "CFJYV723M9" --verbose --timestamp ./synacor-challenge
  popd
  mv dist sjml-synacor-challenge
  zip -q -9 -r sjml-synacor-challenge.zip sjml-synacor-challenge/
popd

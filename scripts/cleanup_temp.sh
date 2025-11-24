#!/bin/sh
set -eu

DIR="${I2PDF_TMPDIR:-/tmp/i2pdf}"

# Skip if directory does not exist
[ -d "$DIR" ] || exit 0

find "$DIR" -type f -mmin +30 -delete 2>/dev/null || true
find "$DIR" -type d -empty -mmin +30 -delete 2>/dev/null || true





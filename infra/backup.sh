#!/bin/sh
# Nightly backup of the bookkeeping database and uploaded documents (run by cron
# on the server, installed by .github/workflows/deploy-bookkeeping.yml).
# Daily copies are kept 40 days; the copy of the 1st of each month is kept for
# good, as the books and their documents must be kept 10 years (Loi 9-88 art. 22).
set -eu
DIR=/opt/backups/bookkeeping
DAY=$(date +%F)
mkdir -p "$DIR"
docker exec dmc-cmr-db pg_dump -U postgres dmc_bookkeeping | gzip > "$DIR/db_$DAY.sql.gz.tmp"
mv "$DIR/db_$DAY.sql.gz.tmp" "$DIR/db_$DAY.sql.gz"
tar -czf "$DIR/media_$DAY.tar.gz.tmp" -C /opt/dmc-bookkeeping media
mv "$DIR/media_$DAY.tar.gz.tmp" "$DIR/media_$DAY.tar.gz"
find "$DIR" -name 'db_*.sql.gz' -mtime +40 ! -name '*-01.sql.gz' -delete
find "$DIR" -name 'media_*.tar.gz' -mtime +40 ! -name '*-01.tar.gz' -delete

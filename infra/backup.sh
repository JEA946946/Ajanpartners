#!/bin/sh
# Automatisk backup hos en tredjepart i EU (Bogføringsloven § 15 og bekendtgørelsen
# om krav til digitale standardbogføringssystemer).
#
#   backup.sh backup         dump pr. skema + bilag pr. skema → krypteret → S3 (EU)
#   backup.sh prune          slet daglige kopier ældre end 40 dage (månedlige gemmes)
#   backup.sh restore-test   hent seneste backup, dekryptér og gendan i en midlertidig
#                            database; tjek at alle skemaer og tabeller kom med
#   backup.sh list           vis backups i lageret
#
# Opbevaring: daglige kopier i RETAIN_DAILY_DAYS (40) dage; kopien fra den 1. i
# måneden lægges under monthly/ og slettes aldrig af scriptet. Bogføringsloven
# kræver 5 år; månedlige kopier gemmes for altid (slet dem manuelt efter 5 år + 1
# regnskabsår, hvis ønsket). Brug en bucket med object lock/versionering, så
# backupperne ikke kan slettes af en angriber med serverens nøgler.
#
# Konfiguration (miljøvariabler, se .env.example):
#   PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE   Postgres
#   MEDIA_ROOT                                   bilag (MEDIA_ROOT/<skema>/...)
#   BACKUP_DIR                                   lokal mellemlagring (default /tmp/bogforing-backup; slettes efter upload)
#   BACKUP_ENCRYPTION   age | gpg                (default age)
#   BACKUP_AGE_RECIPIENT  offentlig age-nøgle (age1...) – kun den offentlige nøgle på serveren
#   BACKUP_AGE_IDENTITY   fil med privat age-nøgle (kun til restore-test/gendannelse)
#   BACKUP_GPG_RECIPIENT  gpg-nøgle-id (hvis BACKUP_ENCRYPTION=gpg)
#   BACKUP_S3_BUCKET  BACKUP_S3_PREFIX  BACKUP_S3_ENDPOINT  BACKUP_S3_REGION
#   AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY      S3-kompatibel lagring i EU (aws-cli)
#   RETAIN_DAILY_DAYS                            (default 40)
#   BACKUP_HEALTHCHECK_URL                       valgfri: pinges ved succes (dead man's switch)
set -eu
# Fang fejl i pg_dump/tar i en pipe (dash ≥ 0.5.11 og bash understøtter pipefail).
(set -o pipefail) 2>/dev/null && set -o pipefail

: "${PGHOST:=db}" "${PGPORT:=5432}" "${PGUSER:=postgres}" "${PGDATABASE:=ajanpartners}"
: "${MEDIA_ROOT:=/app/media}" "${BACKUP_DIR:=/tmp/bogforing-backup}"
: "${BACKUP_ENCRYPTION:=age}" "${BACKUP_S3_PREFIX:=bogforing}" "${RETAIN_DAILY_DAYS:=40}"
export PGHOST PGPORT PGUSER PGDATABASE

log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
die() { log "FEJL: $*"; exit 1; }

aws_s3() {
    [ -n "${BACKUP_S3_BUCKET:-}" ] || die "BACKUP_S3_BUCKET er ikke sat"
    set -- s3 "$@"
    [ -n "${BACKUP_S3_REGION:-}" ] && set -- --region "$BACKUP_S3_REGION" "$@"
    [ -n "${BACKUP_S3_ENDPOINT:-}" ] && set -- --endpoint-url "$BACKUP_S3_ENDPOINT" "$@"
    aws "$@"
}

encrypt() {  # stdin → stdout
    case "$BACKUP_ENCRYPTION" in
        age) [ -n "${BACKUP_AGE_RECIPIENT:-}" ] || die "BACKUP_AGE_RECIPIENT mangler"
             age -r "$BACKUP_AGE_RECIPIENT" ;;
        gpg) [ -n "${BACKUP_GPG_RECIPIENT:-}" ] || die "BACKUP_GPG_RECIPIENT mangler"
             gpg --batch --yes --trust-model always -e -r "$BACKUP_GPG_RECIPIENT" ;;
        *) die "Ukendt BACKUP_ENCRYPTION: $BACKUP_ENCRYPTION" ;;
    esac
}

decrypt() {  # stdin → stdout
    case "$BACKUP_ENCRYPTION" in
        age) [ -n "${BACKUP_AGE_IDENTITY:-}" ] || die "BACKUP_AGE_IDENTITY mangler (privat nøgle til gendannelse)"
             age -d -i "$BACKUP_AGE_IDENTITY" ;;
        gpg) gpg --batch --yes -d ;;
    esac
}

ext() { [ "$BACKUP_ENCRYPTION" = gpg ] && echo gpg || echo age; }

schemas() {
    psql -At -c "SELECT nspname FROM pg_namespace
                 WHERE nspname = 'public' OR nspname LIKE 'c\\_%' ORDER BY nspname"
}

do_backup() {
    day=$(date -u +%F)
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    work="$BACKUP_DIR/$stamp"
    mkdir -p "$work"
    trap 'rm -rf "$work"' EXIT
    e=$(ext)
    count=0
    for s in $(schemas); do
        # Ét dump pr. skema: en kundes bøger kan gendannes og udleveres for sig.
        pg_dump --format=custom --no-owner --schema="$s" "$PGDATABASE" | encrypt > "$work/db_${s}.dump.$e"
        if [ -d "$MEDIA_ROOT/$s" ]; then
            tar -C "$MEDIA_ROOT" -czf - "$s" | encrypt > "$work/media_${s}.tar.gz.$e"
        fi
        count=$((count + 1))
    done
    # Roller/rettigheder (uden adgangskoder) til fuld gendannelse
    pg_dumpall --globals-only --no-role-passwords | encrypt > "$work/globals.sql.$e"
    (cd "$work" && sha256sum ./* > SHA256SUMS)
    printf 'created=%s\nschemas=%s\nencryption=%s\nhost=%s\n' "$stamp" "$count" "$BACKUP_ENCRYPTION" \
        "$(hostname)" > "$work/MANIFEST"

    dest="s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/$day"
    aws_s3 cp --recursive --only-show-errors "$work" "$dest/"
    if [ "$(date -u +%d)" = "01" ]; then
        aws_s3 cp --recursive --only-show-errors "$work" "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/monthly/$(date -u +%Y-%m)/"
    fi
    log "Backup af $count skemaer lagt i $dest"
    [ -n "${BACKUP_HEALTHCHECK_URL:-}" ] && curl -fsS -m 10 "$BACKUP_HEALTHCHECK_URL" >/dev/null || true
}

do_prune() {
    cutoff=$(date -u -d "-$RETAIN_DAILY_DAYS days" +%F 2>/dev/null || date -u -v-"$RETAIN_DAILY_DAYS"d +%F)
    aws_s3 ls "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/" | awk '/PRE/ {print $2}' | tr -d / |
    while read -r d; do
        if [ "$d" \< "$cutoff" ]; then
            log "Sletter daglig backup $d (ældre end $RETAIN_DAILY_DAYS dage)"
            aws_s3 rm --recursive --only-show-errors "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/$d/"
        fi
    done
    # monthly/ røres aldrig her.
}

do_list() {
    aws_s3 ls "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/"
    aws_s3 ls "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/monthly/"
}

do_restore_test() {
    latest=$(aws_s3 ls "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/" | awk '/PRE/ {print $2}' | tr -d / | sort | tail -1)
    [ -n "$latest" ] || die "Ingen backups fundet"
    work=$(mktemp -d)
    testdb="restore_test_$(date -u +%Y%m%d%H%M%S)"
    trap 'rm -rf "$work"; dropdb --if-exists "$testdb" 2>/dev/null || true' EXIT
    aws_s3 cp --recursive --only-show-errors "s3://$BACKUP_S3_BUCKET/$BACKUP_S3_PREFIX/daily/$latest/" "$work/"
    (cd "$work" && sha256sum -c --quiet SHA256SUMS) || die "Checksum passer ikke for backup $latest"
    createdb "$testdb"
    e=$(ext)
    n=0
    for f in "$work"/db_*.dump."$e"; do
        decrypt < "$f" | pg_restore --no-owner --dbname="$testdb"
        n=$((n + 1))
    done
    for f in "$work"/media_*.tar.gz."$e"; do
        [ -e "$f" ] || continue
        decrypt < "$f" | tar -tzf - >/dev/null || die "Bilagsarkivet $f kan ikke læses"
    done
    restored=$(psql -At -d "$testdb" -c "SELECT count(*) FROM pg_namespace WHERE nspname = 'public' OR nspname LIKE 'c\\_%'")
    [ "$restored" -eq "$n" ] || die "Gendannede $restored skemaer, forventede $n"
    tables=$(psql -At -d "$testdb" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema LIKE 'c\\_%'")
    log "Restore-test OK: backup $latest, $n skemaer, $tables tabeller i kundeskemaerne"
}

case "${1:-backup}" in
    backup) do_backup; do_prune ;;
    prune) do_prune ;;
    list) do_list ;;
    restore-test) do_restore_test ;;
    *) echo "Brug: $0 backup|prune|list|restore-test" >&2; exit 2 ;;
esac

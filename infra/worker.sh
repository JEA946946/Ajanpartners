#!/bin/sh
# Planlagte job (kører i worker-containeren). Ingen cron-dæmon: en løkke, der hvert
# minut ser, om et job skal køre. Tider i lokal tid (TZ=Europe/Copenhagen).
#   BANK_FEED_AT  (default 06:00)  manage.py fetch_bank_feeds og bank_feed_reminders
#                                  (opgave til kunden, når samtykket udløber om under 14 dage)
#   BACKUP_AT     (default 02:30)  backup.sh backup (dump, kryptering, upload, oprydning)
#   RESTORE_TEST_DAY (default 1 = den 1. i måneden) backup.sh restore-test kl. 04:00
set -u
: "${BANK_FEED_AT:=06:00}" "${BACKUP_AT:=02:30}" "${RESTORE_TEST_DAY:=01}"
cd /app
log() { printf '%s worker: %s\n' "$(date +%FT%T)" "$*"; }
run() {
    log "start $*"
    if "$@"; then log "ok $*"; else log "FEJL ($?) $*"; fi
}
log "klar (bankkobling $BANK_FEED_AT, backup $BACKUP_AT, restore-test den $RESTORE_TEST_DAY. kl. 04:00)"
last=""
while true; do
    now=$(date +%H:%M)
    if [ "$now" != "$last" ]; then
        last=$now
        if [ "$now" = "$BANK_FEED_AT" ]; then
            run python manage.py fetch_bank_feeds
            run python manage.py bank_feed_reminders
        fi
        [ "$now" = "$BACKUP_AT" ] && run /usr/local/bin/backup.sh backup
        [ "$now" = "04:00" ] && [ "$(date +%d)" = "$RESTORE_TEST_DAY" ] && run /usr/local/bin/backup.sh restore-test
        # Opbevaringspligt (5 år) udløbet for arkiverede kunder → opgave til en partner
        [ "$now" = "05:00" ] && [ "$(date +%d)" = "01" ] && run python manage.py retention_report
        # Kundekendskab (hvidvask) forfaldent eller manglende → opgave til den ansvarlige
        [ "$now" = "05:10" ] && [ "$(date +%d)" = "01" ] && run python manage.py kyc_review_report
        # Materialelister med punkter over fristen → intern opgave til den opgaveansvarlige (dagligt)
        [ "$now" = "05:20" ] && run python manage.py pbc_reminders
        # Fuldmagter, der udløber inden for 30 dage → intern opgave (dagligt)
        [ "$now" = "05:25" ] && run python manage.py poa_expiry_report
    fi
    sleep 20
done

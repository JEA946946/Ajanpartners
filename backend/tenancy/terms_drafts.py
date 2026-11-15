"""Udkast til forretningsbetingelser, databehandleraftale og privatlivspolitik.

UDKAST – skal gennemgås af en advokat, før de bruges over for kunder. Teksterne
oprettes som version "2026-11" af `seed_terms` og kan derefter rettes i
admin-portalen (Betingelser), hvor en ny version publiceres.
"""

VERSION = "2026-11"

NOTICE = "> **Udkast – skal gennemgås af advokat før brug.**\n\n"

TERMS = NOTICE + """# Forretningsbetingelser for Ajan Partners Bogføring

## 1. Parterne og aftalen
Betingelserne gælder mellem Ajan Partners (**revisorhuset**) og den virksomhed, der bruger bogføringsprogrammet Ajan Partners Bogføring (**kunden**). De supplerer kundens opdragsbrev eller kundeaftale med revisorhuset. Er der modstrid, går opdragsbrevet forud.

Kunden accepterer betingelserne ved første login. Den, der accepterer, bekræfter at have ret til at forpligte kunden.

## 2. Ydelsen
Kunden får gratis adgang til programmet, så længe kunden er kunde hos revisorhuset. Funktionerne afhænger af den pakke, der følger af kundens aftale (fx Mini, Standard eller Pro). Revisorhuset kan ændre funktioner og pakker med rimeligt varsel.

## 3. Revisorhusets adgang til bøgerne
Revisorhuset har adgang til kundens bogføring for at levere de ydelser, der følger af kundens aftale, fx bogføring, momsangivelse, løn, årsregnskab og rådgivning. Adgangen gælder fra oprettelsen og indtil aftalen ophører. Revisorhusets medarbejdere har kun adgang til de kunder, de arbejder for, og al deres læsning og ændring logges.

## 4. Kundens ansvar
Kunden er bogføringspligtig efter bogføringsloven og ansvarlig for, at registreringer og bilag er rigtige og fuldstændige, også når revisorhuset hjælper med bogføringen. Kunden er ansvarlig for sine brugere og deres adgangskoder og skal straks give besked ved mistanke om misbrug.

## 5. Opbevaring og backup
Regnskabsmaterialet opbevares digitalt i 5 år fra udgangen af det regnskabsår, det vedrører, også efter at aftalen er ophørt. Der tages dagligt en krypteret backup hos en tredjepart i EU.

## 6. Ophør og flytning af data
Aftalen om programmet ophører, når kunden ikke længere er kunde hos revisorhuset. Kunden kan altid, også efter ophør, hente alt regnskabsmateriale (SAF-T-fil efter Erhvervsstyrelsens standard, saldobalancer, bilag og log) og flytte det til et andet system. Efter ophør bliver bøgerne skrivebeskyttede og opbevares i resten af opbevaringsperioden.

## 7. Drift og ansvar
Revisorhuset tilstræber høj oppetid men garanterer ikke uafbrudt drift. Revisorhuset er ikke ansvarligt for indirekte tab, herunder driftstab, tabt fortjeneste og tab af data, der kunne være undgået ved kundens egen kontrol. Ansvaret for programmet er begrænset til [beløb – udfyldes]. Ansvar for revisorhusets rådgivning og øvrige ydelser følger af opdragsbrevet.

## 8. Personoplysninger
Revisorhusets behandling af personoplysninger for kunden sker efter databehandleraftalen, som er en del af disse betingelser.

## 9. Ændringer
Revisorhuset kan ændre betingelserne med mindst 30 dages varsel. Ændringerne skal accepteres ved næste login.

## 10. Lovvalg og værneting
Dansk ret gælder. Tvister afgøres ved revisorhusets hjemting.
"""

DPA = NOTICE + """# Databehandleraftale

Aftalen er indgået mellem kunden (**den dataansvarlige**) og Ajan Partners (**databehandleren**). Den bygger på Datatilsynets standardkontraktbestemmelser efter databeskyttelsesforordningens artikel 28, stk. 3.

## 1. Formål og varighed
Databehandleren behandler personoplysninger for den dataansvarlige for at levere bogføringsprogrammet og de ydelser, der følger af kundens aftale. Aftalen gælder, så længe databehandleren behandler oplysninger for den dataansvarlige, også i opbevaringsperioden efter ophør.

## 2. Kategorier af registrerede og oplysninger
- Kunder og leverandører: navn, adresse, kontaktoplysninger, CVR-nummer, betalings- og fakturaoplysninger.
- Ansatte (ved løn): navn, adresse, CPR-nummer, skatteoplysninger, løn, pension, ferie og fravær.
- Brugere af programmet: navn, e-mail og logdata.

## 3. Den dataansvarliges instruks
Databehandleren behandler kun oplysningerne efter dokumenteret instruks. Instruksen er brugen af programmet og kundens aftale med revisorhuset.

## 4. Fortrolighed og sikkerhed
Kun medarbejdere, der arbejder for kunden, har adgang, og de har tavshedspligt. Sikkerhedsforanstaltningerne omfatter:
- adskilt database pr. kunde
- krypteret forbindelse
- kryptering af CPR-numre
- to-faktor-login for revisorhusets medarbejdere
- logning af al adgang
- daglig krypteret backup i EU
- regelmæssig test af gendannelse

## 5. Underdatabehandlere
Den dataansvarlige giver generel godkendelse til følgende underdatabehandlere. Ændringer varsles med 30 dage.

| Underdatabehandler | Formål | Placering |
|---|---|---|
| [Hostingudbyder] | Drift af servere og database | EU |
| [Backupudbyder] | Krypteret backup | EU |
| [Access point for e-faktura] | Afsendelse og modtagelse af e-fakturaer | EU |
| [Udbyder af bankdata] | Hentning af kontoudtog (kun ved tilvalg) | EU |

## 6. Overførsel til tredjelande
Oplysningerne overføres ikke til lande uden for EU/EØS uden den dataansvarliges forudgående instruks.

## 7. Bistand og brud
- Databehandleren bistår den dataansvarlige med de registreredes rettigheder og med sikkerhed.
- Brud på persondatasikkerheden meddeles uden unødig forsinkelse og senest 48 timer efter, at databehandleren er blevet opmærksom på det.

## 8. Sletning og tilbagelevering
Ved ophør kan den dataansvarlige hente alle oplysninger, jf. forretningsbetingelserne punkt 6. Oplysningerne slettes, når opbevaringspligten efter bogføringsloven er udløbet, medmindre anden lovgivning kræver længere opbevaring.

## 9. Revision og tilsyn
Databehandleren stiller de oplysninger til rådighed, der er nødvendige for at påvise overholdelse af aftalen, og giver adgang til revision efter aftale.
"""

PRIVACY = NOTICE + """# Privatlivspolitik for Ajan Partners Bogføring

Ajan Partners er dataansvarlig for oplysninger om programmets brugere (navn, e-mail, logdata og to-faktor-oplysninger). Oplysningerne bruges til at give adgang, sikre programmet og dokumentere, hvem der har gjort hvad (bogføringsloven).

Oplysningerne i kundernes bøger behandles efter databehandleraftalen med hver kunde.

Du har ret til indsigt, berigtigelse og, inden for bogføringslovens rammer, sletning. Kontakt Ajan Partners. Du kan klage til Datatilsynet.
"""

DRAFTS = [
    ("terms", "Forretningsbetingelser for Ajan Partners Bogføring", TERMS),
    ("dpa", "Databehandleraftale", DPA),
    ("privacy", "Privatlivspolitik", PRIVACY),
]


def seed_terms(user=None):
    """Opret og publicér udkastene, hvis der endnu ikke findes en publiceret version."""
    from django.utils import timezone

    from .models import TermsDocument

    created = 0
    for kind, title, body in DRAFTS:
        if TermsDocument.current(kind):
            continue
        TermsDocument.objects.get_or_create(kind=kind, version=VERSION, defaults={
            "title": title, "body": body, "published_at": timezone.now(), "created_by": user})
        created += 1
    return created

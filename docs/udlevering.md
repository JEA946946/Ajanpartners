# Procedure: udlevering af regnskabsmateriale

Gælder når en kunde stopper, et bo skal behandles af en kurator, eller en myndighed (Skattestyrelsen, Erhvervsstyrelsen, politiet) beder om materiale. Bogføringsloven kræver, at materialet kan udleveres digitalt i et struktureret format, og at det opbevares i 5 år fra udgangen af det regnskabsår, det vedrører.

## 1. Kunden selv
Kundens administrator kan altid hente alt under **Indstillinger → Eksport af data**, også når kunden er stoppet og bøgerne er arkiveret (read-only). Det kræver ingen hjælp fra revisorhuset.

## 2. Kunden stopper
1. En partner arkiverer kunden i admin-portalen (Kundedetalje → Stamdata → Arkivér). Bøgerne bliver read-only, og opbevaringsperioden sættes.
2. Kunden får besked om, at eksporten kan hentes under Eksport af data. Partneren kan også hente den (**Eksportér alt**) og sende den sikkert, fx via en krypteret delingsløsning. Den må ikke sendes som almindelig e-mail, fordi den kan indeholde CPR-numre og lønoplysninger.
3. Kundens brugere beholder læseadgang i hele opbevaringsperioden.

## 3. Kurator eller myndighed
1. Henvendelsen registreres som en intern opgave på kunden i admin-portalen med dokumentation for retsgrundlaget (fx kendelse om konkurs, påbud eller anmodning med hjemmel).
2. En partner vurderer hjemlen og omfanget. Er kunden aktiv, orienteres kunden, medmindre myndigheden har bedt om det modsatte.
3. Er kunden arkiveret, kan partneren hente **Eksportér alt** uden kundens samtykke i systemet. Er kunden aktiv, har revisorhuset adgang efter kundeaftalen (eller kunden henter selv). Hver eksport logges i revisorhusets log (`export_all`) og i kundens audit-log.
4. Eksporten indeholder `MANIFEST.txt` med SHA-256 for alle filer. Kontrolsummen noteres i opgaven, så det senere kan dokumenteres, hvad der blev udleveret.

## 4. Hvis Ajan Partners ophører med at drive systemet
- Den private backupnøgle (age) opbevares offline hos to navngivne personer og i deponering (escrow) hos en advokat.
- Adgangen til backuplageret og en kopi af denne procedure deponeres samme sted.
- Kunderne får besked med mindst 3 måneders varsel og en eksport af alt. Backups bevares i resten af opbevaringsperioden.

## 5. Efter opbevaringsperioden
Jobbet `retention_report` opretter en intern opgave til en partner, når perioden er udløbet. Partneren tjekker, at der ikke er verserende sager (skattesag, konkursbo, tvist), som kræver længere opbevaring. Først derefter slettes skema, bilag og backups manuelt. Sletningen dokumenteres i opgaven.

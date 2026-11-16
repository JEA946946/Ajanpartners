---
{
  "title": "Følgebrev – årsrapport til godkendelse og underskrift",
  "description": "Fremsendelse af årsrapport, ledelseserklæring og evt. protokollat til digital underskrift, med vejledning om generalforsamling, indsendelse til Erhvervsstyrelsen og skat.",
  "kind": "brev",
  "references": ["Årsregnskabsloven §§ 8, 9, 138", "Selskabsloven §§ 88, 90, 101", "Selskabsskatteloven/skattekontrolloven (selvangivelse)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": false,
  "fields": [
    {"name": "underskrift_frist", "label": "Underskriv senest", "type": "date"},
    {"name": "gf_dato", "label": "Foreslået dato for generalforsamling", "type": "date"},
    {"name": "underskriftsloesning", "label": "Underskriftsløsning", "type": "select", "options": ["MitID via e-mail-link", "Penneo", "Underskrift i bogføringsprogrammet", "Fysisk underskrift"], "default": "MitID via e-mail-link"},
    {"name": "erklaering", "label": "Vores erklæring", "type": "select", "options": ["Revisionspåtegning", "Erklæring om udvidet gennemgang", "Reviewerklæring", "Erklæring om assistance med opstilling"], "default": "Revisionspåtegning"},
    {"name": "selskabsskat", "label": "Selskabsskat for året (kr.)", "type": "number"},
    {"name": "restskat_frist", "label": "Frist for betaling af evt. restskat", "type": "text", "default": "20. november"},
    {"name": "udbytte", "label": "Foreslået udbytte (kr.)", "type": "number"},
    {"name": "bilag", "label": "Vedlagte dokumenter", "type": "textarea", "default": "Årsrapport {{ regnskab.aar }}\nLedelseserklæring\nGeneralforsamlingsreferat (udkast)"}
  ]
}
---
{{ kunde.navn }}
Att.: {{ kunde.ledelsesorgan }}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Årsrapport {{ regnskab.aar }} til godkendelse

Kære {{ kunde.navn }}

Vi har nu afsluttet arbejdet med årsrapporten for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} og sender den hermed til jeres gennemgang og underskrift. Vi forventer at afgive en **{{ felt.erklaering }}**.

## Hovedtal
| | {{ regnskab.aar }} |
|---|---|
| Omsætning/bruttofortjeneste | {{ regnskab.omsaetning }} |
| Årets resultat | {{ regnskab.resultat }} |
| Egenkapital | {{ regnskab.egenkapital }} |
| Balancesum | {{ regnskab.balancesum }} |
| Selskabsskat | {{ felt.selskabsskat }} |
| Foreslået udbytte | {{ felt.udbytte }} |

## Det skal I gøre
1. **Læs årsrapporten igennem.** I er som ledelse ansvarlige for årsrapporten og skal kunne stå inde for indholdet. Giv os besked, hvis noget er forkert eller mangler.
2. **Underskriv ledelsespåtegningen og ledelseserklæringen** senest **{{ felt.underskrift_frist }}** via {{ felt.underskriftsloesning }}. Ledelsespåtegningen skal underskrives af alle medlemmer af {{ kunde.ledelsesorgan }} (ÅRL § 8). Ledelseserklæringen er jeres skriftlige bekræftelse over for os af, at I har givet os alle oplysninger. Først når den er underskrevet, kan vi underskrive vores erklæring.
3. **Afhold generalforsamling** (foreslået dato {{ felt.gf_dato }}). Den ordinære generalforsamling skal afholdes i så god tid, at den godkendte årsrapport kan nå at blive indsendt rettidigt (SL § 88). Generalforsamlingen godkender årsrapporten, beslutter anvendelse af overskud/dækning af underskud{% if felt.udbytte %} og udbytte{% endif %} og meddeler evt. decharge. {% if kunde.selskabsform_kode == "aps" or kunde.selskabsform_kode == "holding" %}I et anpartsselskab kan generalforsamlingen afholdes skriftligt, hvis alle anpartshavere er enige (SL § 101).{% endif %} Vi har vedlagt et udkast til referat.
4. **Indsendelse.** Når årsrapporten er godkendt, indsender vi den digitalt til Erhvervsstyrelsen. Årsrapporten skal være **modtaget i Erhvervsstyrelsen senest {{ regnskab.frist_aarsrapport }}** og skal indsendes uden ugrundet ophold efter godkendelsen (ÅRL § 138). Fristen kan ikke forlænges.

## Skat
Selskabets selvangivelse indberettes af os senest 6 måneder efter regnskabsårets udløb. Hvis der er restskat, skal den betales senest {{ felt.restskat_frist }} i året efter indkomståret for at undgå yderligere tillæg; vi giver jer besked om beløbet. {% if felt.udbytte %}Udbytte skal angives og udbytteskat indeholdes og betales senest den 10. i måneden efter beslutningen om udlodning (for udbytte til personer).{% endif %}

## Vedlagt
{{ felt.bilag }}

Vi gennemgår gerne årsrapporten med jer på et møde. Kontakt {{ kunde.ansvarlig }}, hvis I har spørgsmål.

Med venlig hilsen

{{ firma.navn }}

{{ medarbejder.navn }}
{{ medarbejder.titel }}

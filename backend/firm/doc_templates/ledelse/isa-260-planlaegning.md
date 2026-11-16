---
{
  "title": "Kommunikation med den øverste ledelse – planlægning (ISA 260)",
  "description": "Brev til den øverste ledelse (bestyrelse eller direktion) før revisionen: revisors ansvar, planlagt omfang og tidsplan, væsentlighed, betydelige risici (branchetilpasset), uafhængighed og forespørgsler om besvigelser, lovgivning og nærtstående parter.",
  "kind": "brev",
  "references": ["ISA 260, afsnit 14-17", "ISA 240, afsnit 21-22", "ISA 250", "ISA 550", "ISA 300", "ISA 320", "Revisorloven § 24 (uafhængighed)"],
  "legal_forms": ["aps", "as", "ivs", "holding", "fmba", "andet"],
  "industry_aware": true,
  "fields": [
    {"name": "har_bestyrelse", "label": "Selskabet har en bestyrelse (ApS)", "type": "checkbox", "default": false},
    {"name": "vaesentlighed", "label": "Foreløbig væsentlighed (kr.)", "type": "number"},
    {"name": "vaesentlighed_grundlag", "label": "Grundlag for væsentlighed", "type": "text", "default": "en procentdel af omsætningen"},
    {"name": "interim", "label": "Tidspunkt for interimrevision", "type": "text"},
    {"name": "statusrevision", "label": "Tidspunkt for statusrevision", "type": "text"},
    {"name": "lageroptaelling", "label": "Dato for lageroptælling, vi overværer (hvis relevant)", "type": "text"},
    {"name": "moede_afslutning", "label": "Planlagt afslutningsmøde/bestyrelsesmøde", "type": "text"},
    {"name": "risici_ekstra", "label": "Øvrige betydelige risici (valgfrit)", "type": "textarea"},
    {"name": "team", "label": "Revisionsteam (navne og roller)", "type": "textarea", "default": "{{ medarbejder.navn }} (ansvarlig revisor)"},
    {"name": "andre_ydelser", "label": "Andre ydelser vi leverer (fx skat, opstilling)", "type": "text"},
    {"name": "revisor_titel", "label": "Revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"}
  ]
}
---
**{{ kunde.navn }}**
Att.: {% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}bestyrelsen{% else %}{{ kunde.ledelsesorgan }}{% endif %}
{{ kunde.adresse }}
{{ kunde.postnr }} {{ kunde.by }}

{{ dato.idag }}

# Planlægning af revisionen for {{ regnskab.aar }}

Som led i vores revision af årsregnskabet for {{ kunde.navn }} for regnskabsåret {{ regnskab.start }} – {{ regnskab.slut }} orienterer vi hermed {% if kunde.selskabsform_kode == "as" or felt.har_bestyrelse %}bestyrelsen{% else %}direktionen{% endif %} om den planlagte revision, jf. ISA 260. Brevet supplerer opdragsbrevet.

## Vores ansvar

Vi skal udtrykke en konklusion om, hvorvidt årsregnskabet giver et retvisende billede i overensstemmelse med årsregnskabsloven, og udtale os om ledelsesberetningen. Revisionen fritager ikke ledelsen for dens ansvar for regnskabsaflæggelsen, den interne kontrol og forebyggelse og opdagelse af besvigelser.

## Omfang og tidsplan

| Aktivitet | Tidspunkt |
|---|---|
| Interimrevision (processer og kontroller) | {{ felt.interim }} |
{% if branche.lager %}| Overværelse af lageroptælling | {{ felt.lageroptaelling }} |
{% endif %}| Statusrevision | {{ felt.statusrevision }} |
| Afslutningsmøde og afgivelse af påtegning | {{ felt.moede_afslutning }} |
| Frist for indsendelse af årsrapport | {{ regnskab.frist_aarsrapport }} |

Revisionsteam: {{ felt.team }}

## Væsentlighed

Vi har foreløbigt fastsat væsentlighed for årsregnskabet som helhed til {{ felt.vaesentlighed }} kr. med udgangspunkt i {{ felt.vaesentlighed_grundlag }}. Væsentligheden revurderes, når det endelige regnskab foreligger. Kvalitative forhold, fx transaktioner med ledelse og kapitalejere, vurderes uanset beløb.

## Betydelige risici, vi vil fokusere på

- **Ledelsens tilsidesættelse af kontroller** (en formodet risiko i alle revisioner).
- **Indregning af omsætning**, herunder periodeafgrænsning{% if branche.kontantintensiv %} og fuldstændighed af kontantsalg{% endif %}.
{% if branche.lager %}- **Varelager:** eksistens, kostpris og nedskrivning til nettorealisationsværdi.
{% endif %}{% if branche.igangvaerende_arbejder %}- **Igangværende arbejder:** færdiggørelsesgrad, forventede restomkostninger og tabsgivende kontrakter.
{% endif %}{% if branche.investeringsejendomme %}- **Investeringsejendomme:** dagsværdimåling og forudsætninger i afkastmodellen.
{% endif %}{% if branche.momsfritaget %}- **Moms og lønsumsafgift:** delvis fradragsret og afgiftsgrundlag.
{% endif %}{% if branche.landbrug %}- **Biologiske aktiver og landbrugsstøtte:** måling og indregning.
{% endif %}{% if branche.holding %}- **Kapitalandele:** måling og nedskrivning samt koncerninterne mellemværender.
{% endif %}{% if felt.risici_ekstra %}{{ felt.risici_ekstra }}
{% endif %}
## Uafhængighed

Vi har vurderet vores uafhængighed i forhold til revisorlovens § 24 og IESBA Code og bekræfter, at vi er uafhængige af selskabet.{% if felt.andre_ydelser %} Ud over revisionen leverer vi {{ felt.andre_ydelser }}. Ydelserne er vurderet til ikke at true vores uafhængighed, bl.a. fordi ledelsen træffer alle beslutninger.{% endif %}

## Forespørgsler til den øverste ledelse

For at vi kan tilrettelægge revisionen, beder vi om svar på følgende:

1. Har I kendskab til besvigelser eller mistanke om besvigelser, der vedrører selskabet?
2. Hvordan fører I tilsyn med ledelsens processer for at identificere og håndtere risikoen for besvigelser?
3. Er I bekendt med overtrædelser af love og øvrig regulering, herunder skat, moms, hvidvask og databeskyttelse?
4. Hvilke nærtstående parter har selskabet, og er der indgået transaktioner med dem i året?
5. Er der forhold, som I ønsker, at vi særligt har fokus på under revisionen?

Vi ser frem til samarbejdet og gennemgår gerne planen på et møde.

Med venlig hilsen

**{{ firma.navn }}**

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

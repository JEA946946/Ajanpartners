---
{
  "title": "Henvendelse til fratrædende revisor ved revisorskifte",
  "description": "Brev fra tiltrædende revisor til fratrædende revisor (og evt. revisor for seneste erklæring) efter revisorlovens § 18, stk. 2, med anmodning om fratrædelsesgrunde og adgang til relevante oplysninger.",
  "kind": "brev",
  "references": ["Revisorloven § 18, stk. 2", "ISA 300 afsnit 13", "ISA 510", "FSR – danske revisorers Etiske regler (afsnit 320)", "Selskabsloven § 146"],
  "legal_forms": [],
  "industry_aware": false,
  "fields": [
    {"name": "revisor_titel", "label": "Underskrivende revisors titel", "type": "select", "options": ["statsautoriseret revisor", "registreret revisor"], "default": "statsautoriseret revisor"},
    {"name": "tidligere_firma", "label": "Fratrædende revisionsvirksomhed", "type": "text"},
    {"name": "tidligere_revisor", "label": "Fratrædende revisor (navn)", "type": "text"},
    {"name": "tidligere_adresse", "label": "Adresse/e-mail", "type": "textarea"},
    {"name": "seneste_erklaering", "label": "Seneste erklæring afgivet af en anden revisor (navn og firma, ellers tom)", "type": "text"},
    {"name": "seneste_aar", "label": "Seneste regnskabsår med erklæring", "type": "text"},
    {"name": "valgt_dato", "label": "Dato for valg af os som revisor", "type": "text"},
    {"name": "svarfrist", "label": "Svarfrist", "type": "date"}
  ]
}
---
**{{ felt.tidligere_firma }}**
Att.: {{ felt.tidligere_revisor }}
{{ felt.tidligere_adresse }}

{{ dato.idag }}

# Revisorskifte – {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }}

{{ firma.navn }} er {% if felt.valgt_dato %}den {{ felt.valgt_dato }} {% endif %}valgt som ny revisor for {{ kunde.navn }}, hvor I har været revisor og senest har afgivet erklæring på årsregnskabet for {{ felt.seneste_aar }}.

I henhold til revisorlovens § 18, stk. 2, retter vi henvendelse til jer som fratrædende revisor og beder jer oplyse grundene til jeres fratræden, som I efter bestemmelsen har pligt til at oplyse. Vi beder jer samtidig oplyse, om I er bekendt med forhold, som efter jeres opfattelse bør indgå i vores overvejelser om at acceptere hvervet, fx:

1. uenighed med ledelsen om regnskabsmæssig behandling, revisionsprocedurer eller erklæringens indhold;
2. forhold, der har ført til modifikation af konklusionen, fremhævelse af forhold eller supplerende oplysninger i erklæringer, herunder om ledelsens ansvar;
3. forhold, som er eller burde have været indført i revisionsprotokollen eller meddelt ledelsen skriftligt;
4. kendte eller formodede besvigelser, overtrædelser af lovgivningen eller forhold omfattet af revisorlovens § 22;
5. forhold, der giver anledning til tvivl om ledelsens integritet;
6. ubetalte honorarer.

Vi er opmærksomme på, at I efter hvidvasklovens § 38 ikke må oplyse, om der er sket underretning til Hvidvasksekretariatet. Vi beder alene om de oplysninger, I lovligt kan give os.

Endvidere beder vi om adgang til relevante oplysninger om virksomheden, jf. revisorlovens § 18, stk. 2, 4. pkt., herunder:

- seneste årsrapport, revisionsprotokol/ledelsesbreve og ledelseserklæring;
- arbejdspapirer vedrørende åbningsbalancen pr. {{ regnskab.start }} (ISA 510), herunder specifikationer af væsentlige balanceposter, lager, igangværende arbejder, tilgodehavender, hensatte forpligtelser og eventualforpligtelser;
- skatteopgørelser og opgørelse af udskudt skat;
- oplysninger om væsentlige kontrakter, tvister og sikkerhedsstillelser, som I er bekendt med.

{% if felt.seneste_erklaering %}Da den seneste erklæring er afgivet af {{ felt.seneste_erklaering }}, retter vi tillige henvendelse dertil, jf. revisorlovens § 18, stk. 2, 3. pkt.{% endif %}

{{ kunde.ledelsesorgan }} har givet samtykke til, at I udtaler jer til os og udleverer materialet, jf. vedlagte fuldmagt.

Vi beder om jeres svar senest {{ felt.svarfrist }}. Vi kan ikke afgive erklæring, før vi har modtaget jeres svar. Hvis I har spørgsmål, er I velkomne til at kontakte undertegnede.

Med venlig hilsen

{{ firma.navn }}

&nbsp;

______________________________
{{ medarbejder.navn }}
{{ felt.revisor_titel }}

Bilag: Samtykke fra {{ kunde.navn }}

* * *

### Samtykke

{{ kunde.navn }} giver hermed {{ felt.tidligere_firma }} tilladelse til at give {{ firma.navn }} alle oplysninger, der er relevante for revisorskiftet, og til at udlevere kopi af arbejdspapirer og andet materiale om selskabet.

Dato: ________________

______________________________
{{ kunde.ledelsesorgan }}

---
{
  "title": "Notat om kapitalejerlån",
  "description": "Revisors notat om lån og mellemregninger mellem selskab og kapitalejere/ledelse: selskabsretlig vurdering efter ophævelsen af SL §§ 210-212 pr. 1. januar 2025, ældre lån, LL § 16 E-beskatning, indeholdelse og revisors underretningspligt.",
  "kind": "arbejdspapir",
  "references": ["Lov nr. 1668 af 30. december 2024 (ophævelse af SL §§ 210-212 pr. 1. januar 2025)", "Selskabsloven §§ 115, 118, 127 og 179", "Selskabsloven §§ 206-209 (selvfinansiering)", "Ligningsloven § 16 E", "Ligningsloven § 2", "Kildeskatteloven §§ 46 og 65", "Revisorloven § 22", "Årsregnskabsloven § 73 (lån til ledelsen)"],
  "legal_forms": ["aps", "as", "holding"],
  "industry_aware": false,
  "fields": [
    {"name": "laantager", "label": "Låntager (navn, relation: kapitalejer/ledelse/nærtstående)", "type": "text"},
    {"name": "personlig", "label": "Låntager er en fysisk person (eller nærtstående) med kontrol (LL § 16 E)", "type": "checkbox", "default": true},
    {"name": "saldo_primo", "label": "Saldo primo (kr.)", "type": "number"},
    {"name": "tilgang", "label": "Årets hævninger/udlæg (kr.)", "type": "number"},
    {"name": "afgang", "label": "Årets indbetalinger/modregninger (kr.)", "type": "number"},
    {"name": "saldo_ultimo", "label": "Saldo ultimo (kr.)", "type": "number"},
    {"name": "maks_saldo", "label": "Største debetsaldo i året (kr.)", "type": "number"},
    {"name": "opstaaet", "label": "Hvornår opstod lånet", "type": "select", "options": ["Efter 1. januar 2025", "Før 1. januar 2025 (ulovligt efter de dagældende regler)", "Før 1. januar 2025 (lovligt efter dagældende § 210, stk. 2)"], "default": "Efter 1. januar 2025"},
    {"name": "vilkaar", "label": "Lånevilkår (rente, afdrag, sikkerhed, dokument)", "type": "textarea"},
    {"name": "haandtering", "label": "Valgt håndtering", "type": "select", "options": ["Indfries straks", "Omposteres til løn (A-skat/AM-bidrag)", "Omposteres til udbytte (udbytteskat)", "Bevares som lån – udbytte-/lønbeskattet efter LL § 16 E", "Lån er ikke omfattet af LL § 16 E (sædvanlig forretningsmæssig disposition)"], "default": "Omposteres til udbytte (udbytteskat)"},
    {"name": "konklusion", "label": "Konklusion og aftale med kunden", "type": "textarea"}
  ]
}
---
# Notat om kapitalejerlån

**Kunde:** {{ kunde.navn }}, CVR-nr. {{ kunde.cvr }} · **Regnskabsår:** {{ regnskab.aar }}
**Låntager:** {{ felt.laantager }}
**Udarbejdet af:** {{ medarbejder.navn }}, {{ dato.idag }}

## 1. Bevægelser
| | Kr. |
|---|---|
| Saldo primo | {{ felt.saldo_primo }} |
| Hævninger/udlæg | {{ felt.tilgang }} |
| Indbetalinger/modregninger | {{ felt.afgang }} |
| **Saldo ultimo** | **{{ felt.saldo_ultimo }}** |
| Største debetsaldo i året | {{ felt.maks_saldo }} |

Lånevilkår: {{ felt.vilkaar }}

Mellemregningen er afstemt til bogføringen, og alle posteringer er gennemgået for private udgifter afholdt af selskabet.

## 2. Selskabsretlig vurdering
**Gældende regler:** Selskabslovens særlige regler om kapitalejerlån (§§ 210-212) er ophævet med virkning fra 1. januar 2025. Lån til kapitalejere og ledelse er derfor ikke længere selskabsretligt forbudt eller underlagt kravene om frie reserver, generalforsamlingsbeslutning og markedsvilkår i den tidligere § 210, stk. 2. Følgende gælder fortsat:

- **Forsvarlighed og selskabets interesse:** Ledelsen skal sikre, at lånet er forsvarligt under hensyn til selskabets økonomiske stilling og kapitalberedskab og er i selskabets interesse (selskabslovens §§ 115, 118 og 179). Et lån, der reelt er en skjult udlodning, skal overholde udlodningsreglerne i §§ 179-183.
- **Generalklausulen:** Ledelsen må ikke foretage dispositioner, der åbenbart er egnet til at skaffe visse kapitalejere eller andre en utilbørlig fordel på andre kapitalejeres eller selskabets bekostning (§ 127).
- **Selvfinansiering:** Lån eller sikkerhedsstillelse i forbindelse med tredjemands erhvervelse af kapitalandele i selskabet eller moderselskabet kræver fortsat opfyldelse af §§ 206-209.
- **Inhabilitet:** Låntager må ikke deltage i ledelsens behandling af lånet (§ 131).
- **Regnskab:** Lån til og sikkerhedsstillelse for ledelsesmedlemmer oplyses i noterne med rente, vilkår og indfriede beløb (ÅRL § 73), og transaktioner med nærtstående oplyses efter regnskabsklassens krav.

{% if felt.opstaaet == "Før 1. januar 2025 (ulovligt efter de dagældende regler)" %}
**Ældre lån:** Lånet er ydet før 1. januar 2025 i strid med den dagældende § 210. Ophævelsen (lov nr. 1668 af 30. december 2024) gør ikke tidligere ulovlige lån lovlige. Lånet er fortsat ulovligt og skal tilbagebetales til selskabet med rente efter den dagældende § 215, stk. 1 (rente svarende til renteloven § 5 med tillæg). Erhvervsstyrelsen kan fortsat påbyde tilbagebetaling. Ifølge forarbejderne bør verserende straffesager om de særlige betingelser dog ikke videreføres. Det anbefales, at lånet indfries med rente og dokumenteres (alternativt omdannes til løn/udbytte ved lovlig beslutning, hvorved tilbagebetalingskravet modregnes). Den skattemæssige behandling efter LL § 16 E er uændret.
{% elif felt.opstaaet == "Før 1. januar 2025 (lovligt efter dagældende § 210, stk. 2)" %}
**Ældre lån:** Lånet blev ydet lovligt efter den dagældende § 210, stk. 2 (frie reserver, markedsvilkår, beslutning). Lånet afvikles efter de aftalte vilkår. Skattemæssigt er lånet omfattet af LL § 16 E, hvis det er ydet efter 13. august 2012 til en person med kontrol.
{% else %}
**Lån ydet efter 1. januar 2025:** Lånet vurderes efter de almindelige regler ovenfor. Ledelsen har dokumenteret sin vurdering af forsvarlighed og selskabets interesse.
{% endif %}

## 3. Skattemæssig vurdering – ligningslovens § 16 E
{% if felt.personlig %}
Lån fra selskabet til en fysisk person, der alene eller sammen med nærtstående har **kontrol** over selskabet (jf. LL § 2: mere end 50 % af kapital eller stemmer, eller bestemmende indflydelse), eller til en nærtstående, sidestilles skattemæssigt med en hævning uden tilbagebetalingspligt. Det er uden betydning, at lånet er lovligt selskabsretligt, eller at det tilbagebetales senere (en senere indbetaling anses som et nyt indskud).

- Lån til en person, der **både er ansat/direktør og kapitalejer**, behandles som **løn** (A-skat og AM-bidrag) eller **udbytte** afhængigt af de faktiske forhold; Skattestyrelsens praksis er udbytte, medmindre lånet har sammenhæng med ansættelsen.
- Behandles beløbet som udbytte, skal selskabet indeholde **udbytteskat 27 %** (kildeskattelovens § 65); som løn indeholdes A-skat og AM-bidrag. Selskabet hæfter for manglende indeholdelse, medmindre det har udvist fornøden agtpågivenhed.
- Undtaget er lån som led i sædvanlige forretningsmæssige dispositioner, fx almindelig kundekredit på normale vilkår, samt lån fra pengeinstitutter på sædvanlige vilkår.
- Låntager kan ikke fratrække renter som renteudgift, og selskabets fordring kan ikke afskrives skattemæssigt.
- Selskabets renteindtægter af lånet er fortsat skattepligtige, og tilbagebetalinger anses som indskud.

Bagatelagtige udlæg (fx en enkelt privat udgift afholdt ved fejl, der straks refunderes) vurderes konkret. Saldoen i året har maksimalt udgjort {{ felt.maks_saldo }} kr.
{% else %}
Låntager er ikke en fysisk person med kontrol (eller nærtstående), og LL § 16 E finder ikke anvendelse. Lånet skal være på markedsvilkår (LL § 2 om kontrollerede transaktioner), herunder markedsrente, og dokumenteres.
{% endif %}

## 4. Håndtering
Valgt håndtering: **{{ felt.haandtering }}**

{% if felt.haandtering == "Omposteres til udbytte (udbytteskat)" %}- [ ] Beslutning om (ekstraordinært) udbytte dokumenteres (generalforsamling), og frie reserver kontrolleres.
- [ ] Udbytteskat angives og indbetales; udbytte indberettes.
- [ ] Mellemregningen nulstilles mod udbyttegæld.
{% elif felt.haandtering == "Omposteres til løn (A-skat/AM-bidrag)" %}- [ ] Beløbet indberettes til eIndkomst som løn (bruttobeløb, A-skat og AM-bidrag) i den periode, hvor hævningen skete; korrektion af tidligere perioder ved behov.
- [ ] Lønsumsafgift vurderes, hvis selskabet er lønsumsafgiftspligtigt.
{% elif felt.haandtering == "Indfries straks" %}- [ ] Indfrielse dokumenteret med kontoudtog. Bemærk: indfrielse ændrer ikke den skattemæssige behandling efter LL § 16 E for lån, der allerede er ydet.
{% else %}- [ ] Begrundelse dokumenteret.
{% endif %}- [ ] Kunden er orienteret skriftligt om reglerne og om ikke at foretage private hævninger på selskabets konti.

## 5. Revisors pligter
- Revisor skal efter revisorlovens § 22 underrette ledelsen og, hvis forholdet ikke berigtiges, Skattestyrelsen, hvis der er begrundet mistanke om væsentlige overtrædelser af skatte- og afgiftslovgivningen, der kan medføre ledelsesansvar, herunder manglende indeholdelse af kildeskat på lån til kapitalejere.
- Revisor skal ikke længere særskilt kontrollere de ophævede betingelser i SL § 210, men manglende forsvarlighed kan udgøre en ledelsesansvarspådragende overtrædelse.
- Forholdet medtages i revisionsprotokollatet/ledelsesbrevet.

## 6. Konklusion
{{ felt.konklusion }}

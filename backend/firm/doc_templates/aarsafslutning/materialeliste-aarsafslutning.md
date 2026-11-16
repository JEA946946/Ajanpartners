---
{
  "title": "Materialeliste til årsafslutning (PBC)",
  "description": "Liste over materiale, kunden skal levere til årsafslutning, revision eller review. Tilpasser sig branche (lager, igangværende arbejder, kontanter, ejendomme, transport, landbrug, holding) og selskabsform.",
  "kind": "tjekliste",
  "references": ["Bogføringsloven §§ 4-12", "Årsregnskabsloven § 22", "ISA 500", "ISA 501", "ISA 505"],
  "legal_forms": [],
  "industry_aware": true,
  "fields": [
    {"name": "frist_materiale", "label": "Frist for levering af materiale", "type": "date"},
    {"name": "opgavetype", "label": "Opgavetype", "type": "select", "options": ["Revision", "Udvidet gennemgang", "Review", "Opstilling (assistance)", "Skatteregnskab"], "default": "Revision"},
    {"name": "leveringsform", "label": "Levering", "type": "select", "options": ["Upload i bogføringsprogrammet", "Sikker mail", "Delt mappe"], "default": "Upload i bogføringsprogrammet"},
    {"name": "saerlige_forhold", "label": "Særlige forhold i året (fx opkøb, nye lån, retssager)", "type": "textarea"}
  ]
}
---
# Materialeliste til årsafslutning {{ regnskab.aar }}

**Kunde:** {{ kunde.navn }}, CVR {{ kunde.cvr }}
**Regnskabsperiode:** {{ regnskab.start }} – {{ regnskab.slut }}
**Opgave:** {{ felt.opgavetype }}
**Frist for levering:** {{ felt.frist_materiale }}
**Levering:** {{ felt.leveringsform }}
**Kontaktperson hos {{ firma.navn }}:** {{ kunde.ansvarlig }}

Listen viser det materiale, vi skal bruge for at kunne udarbejde {% if kunde.er_kapitalselskab %}årsrapporten{% else %}årsregnskabet og skatteregnskabet{% endif %}. Sæt kryds, når et punkt er leveret, og skriv "ikke relevant", hvis et punkt ikke vedrører virksomheden. Alt materiale skal kunne afstemmes til bogføringen pr. {{ regnskab.slut }}.

{% if felt.saerlige_forhold %}**Særlige forhold, vi er orienteret om:** {{ felt.saerlige_forhold }}{% endif %}

## 1. Generelt og bogføring
- [ ] Bekræftelse af, at al bogføring for perioden er afsluttet, og at alle bilag er uploadet til bogføringsprogrammet
- [ ] Saldobalance pr. {{ regnskab.slut }} (dannes i programmet – vi henter den selv, hvis I har givet os adgang)
- [ ] Oversigt over væsentlige begivenheder i året (nye aktiviteter, ophør, nye kunder/leverandører, ændret ejerkreds, nye lokaler)
- [ ] Referater fra generalforsamlinger{% if kunde.selskabsform_kode == "as" %}, bestyrelsesmøder{% endif %} og ejermøder i perioden og frem til i dag
- [ ] Nye eller ændrede væsentlige kontrakter (lejekontrakter, leasingaftaler, låneaftaler, samarbejds- og agentaftaler, forsikringer)
- [ ] Oplysning om evt. tvister, retssager, krav eller klager – og navn på advokat, der har bistået i året
- [ ] Budget og likviditetsbudget for det kommende år (bruges til vurdering af fortsat drift)

## 2. Likvider og finansiering
- [ ] Kontoudtog for alle bankkonti pr. {{ regnskab.slut }} (også konti i udenlandsk valuta og opsparingskonti)
- [ ] Årsoversigt/engagementsoversigt fra pengeinstituttet (vi indhenter selv engagementsforespørgsel, når I har underskrevet fuldmagten)
- [ ] Låneaftaler og årsopgørelser for alle lån (bank, realkredit, leasing, kassekredit) med restgæld, rente og afdragsprofil
- [ ] Oversigt over sikkerhedsstillelser (ejerpantebreve, virksomhedspant, kaution, transport i fordringer, deponerede beløb)
- [ ] Oversigt over værdipapirer med depotudskrift pr. {{ regnskab.slut }}
{% if branche.kontantintensiv %}
## 3. Kasse og kontantsalg
- [ ] Kasseoptælling pr. {{ regnskab.slut }} underskrevet af den, der har optalt (dato, klokkeslæt, sedler/mønter)
- [ ] Kassebog/kasserapporter for hele året – daglig afstemning af kasse mod Z-rapport
- [ ] Z-rapporter (dagsafslutninger) fra kasseapparat/POS-system for hele året, inkl. oversigt over evt. huller i nummerrækken
- [ ] Opgørelse over betalinger med kort og MobilePay pr. dag, afstemt til indbetalinger på bankkontoen (indløserens afregningsoversigt)
- [ ] Liste over kassedifferencer og forklaring på større differencer
- [ ] Bilag for kontante udbetalinger (betalinger over 8.000 kr. inkl. moms, der ikke er betalt via pengeinstitut, giver som udgangspunkt ikke fradrag, medmindre betalingen indberettes til Skattestyrelsen senest 14 dage efter, jf. ligningsloven § 8 Y; erhvervsdrivende, der ikke er omfattet af hvidvaskloven § 1, stk. 1, må ikke modtage kontantbetalinger på 15.000 kr. eller derover, jf. hvidvaskloven § 5)
- [ ] Oplysning om kasseapparatets/POS-systemets type og leverandør
{% if branche.restauration %}- [ ] Opgørelse over drikkepenge og personaleforplejning samt evt. take-away/udbringning via platforme (afregningsoversigter fra fx Wolt, Just Eat)
- [ ] Oversigt over gavekort/klippekort udstedt, men ikke indløst pr. {{ regnskab.slut }}
{% endif %}{% endif %}
## {% if branche.kontantintensiv %}4{% else %}3{% endif %}. Tilgodehavender
- [ ] Debitorliste (aldersfordelt) pr. {{ regnskab.slut }} afstemt til saldobalancen
- [ ] Liste over debitorer, der er betalt efter statusdagen, frem til i dag
- [ ] Oversigt over tvivlsomme debitorer med jeres vurdering af nedskrivningsbehov (konkurs, rekonstruktion, inkasso)
- [ ] Kreditnotaer udstedt efter statusdagen, der vedrører salg før statusdagen
- [ ] Specifikation af andre tilgodehavender, deposita og forudbetalte omkostninger (periodeafgrænsningsposter)
{% if branche.lager %}
## Varelager
- [ ] Lagerliste pr. {{ regnskab.slut }} med varenummer, antal, kostpris og samlet værdi – underskrevet af ansvarlig for optællingen
- [ ] Optællingslister (originale) og dokumentation for optællingsprocedure (se særskilt instruks for lageroptælling)
- [ ] Oplysning om dato for optælling; hvis optalt før/efter statusdagen: til- og afgang mellem optællingsdag og {{ regnskab.slut }}
- [ ] Dokumentation for kostpriser (seneste købsfakturaer for de største varenumre)
{% if branche.fremstilling %}- [ ] Kalkulation af kostpris for egenproducerede varer og varer i arbejde (materialer, direkte løn og indirekte produktionsomkostninger)
{% endif %}- [ ] Liste over ukurante, beskadigede eller langsomt omsættelige varer og forslag til nedskrivning
- [ ] Oplysning om varer på lager hos andre (konsignation, tredjepartslager) og andres varer på jeres lager
- [ ] Varemodtagelser og forsendelser omkring statusdagen (sidste følgesedler før og første efter {{ regnskab.slut }}) til kontrol af periodeafgrænsning
{% if branche.bilhandel %}- [ ] Billiste med stelnummer, købspris, istandsættelse og forventet salgspris; oversigt over brugtmoms-biler og demobiler
- [ ] Afstemning af registreringsafgift og evt. afgiftsfritagne/eksportbiler
{% endif %}{% endif %}{% if branche.igangvaerende_arbejder %}
## Igangværende arbejder og entreprisekontrakter
- [ ] Liste over alle igangværende sager/projekter pr. {{ regnskab.slut }} med aftalt pris, faktureret aconto, afholdte omkostninger og færdiggørelsesgrad
- [ ] Kontrakter og evt. tillægsaftaler (ekstraarbejder) for de væsentligste sager
- [ ] Forventede restomkostninger og forventet resultat for hver sag – herunder sager med forventet tab (tab hensættes fuldt ud)
- [ ] Timeopgørelser og timesatser pr. sag (registrerede, ikke fakturerede timer)
{% if branche.byggeri %}- [ ] Oversigt over sikkerhedsstillelser (garantier/bankgarantier efter AB 18/ABT 18), tilbageholdte beløb og afleveringsforretninger
- [ ] Oversigt over mangelsager, 1- og 5-årsgennemgange og forventede garantiforpligtelser
- [ ] Oplysning om omvendt betalingspligt for moms ved byggeydelser til andre momsregistrerede (hvis relevant) og RUT/udenlandske underentreprenører
{% endif %}- [ ] Faktureringsplan og fakturaer udstedt efter statusdagen for arbejde udført før
{% endif %}
## Anlægsaktiver
- [ ] Oversigt over køb og salg af driftsmidler, inventar, biler, it-udstyr og immaterielle aktiver i året (fakturaer, salgsaftaler)
- [ ] Afskrivningsgrundlag og anlægskartotek – hvis I fører et
- [ ] Aktiver, der er skrottet eller solgt (salgspris, salgsdato)
- [ ] Leasingaftaler (operationel/finansiel) med restløbetid og ydelser
- [ ] Udviklingsprojekter: dokumentation for aktivering og bunden reserve for udviklingsomkostninger (ÅRL § 83)
{% if branche.ejendom %}
## Ejendomme
- [ ] Seneste offentlige ejendomsvurdering og grundværdi for hver ejendom (Vurderingsportalen)
- [ ] Lejeliste pr. {{ regnskab.slut }} med lejer, areal, årlig leje, depositum og forudbetalt leje
- [ ] Lejekontrakter for nye lejemål og ændringer i året; oplysning om tomgang og lejeforhøjelser
- [ ] Driftsregnskab pr. ejendom og varmeregnskaber/forbrugsregnskaber (afregning med lejere)
- [ ] Oversigt over forbedringer vs. vedligeholdelse (større fakturaer specificeret)
- [ ] Ejendomsskattebilletter og forsikringspolicer
- [ ] Ved måling til dagsværdi (ÅRL § 38): jeres eller valuarens værdiansættelse med afkastkrav og forudsætninger
- [ ] Køb/salg af ejendom: skøde, refusionsopgørelse og handelsdokumenter
{% endif %}{% if branche.transport %}
## Transport og køretøjer
- [ ] Kørebøger for køretøjer, hvor der er privat kørsel eller udbetales skattefri kørselsgodtgørelse
- [ ] Oversigt over køretøjer (reg.nr., type, gul/hvid plade, ejet/leaset) og fri bil-beskatning
- [ ] Tachografdata/udskrifter (dokumentation for udbetalte skattefri rejse- og udetillæg til chauffører)
- [ ] Oversigt over vejafgifter, brobizz, brændstofkort og evt. tilbagebetaling af udenlandsk moms/energiafgift
- [ ] Vognmandstilladelser/fællesskabstilladelser og evt. taxatilladelser
- [ ] Kørselsrapporter/turoversigter, der kan afstemmes til omsætningen
{% endif %}{% if branche.landbrug %}
## Landbrug
- [ ] Opgørelse over besætning pr. {{ regnskab.slut }} (antal og kategori) – biologiske aktiver
- [ ] Opgørelse over beholdninger af afgrøder, foder, gødning og planteværn
- [ ] Opgørelse over markafgrøder på roden og forudbetalte/afholdte omkostninger til næste høst
- [ ] Ansøgning om og afregning af EU-støtte (arealstøtte, økostøtte, projekttilskud) og evt. krav om tilbagebetaling
- [ ] Afregninger fra slagteri, mejeri og grovvarer (efterbetalinger og andelskapital i andelsselskaber)
- [ ] Oversigt over jord (ejet/forpagtet) og forpagtningsaftaler
{% endif %}{% if branche.holding or branche.finans %}
## Kapitalandele og koncernforhold
- [ ] Årsrapporter (eller udkast) for alle datterselskaber og associerede virksomheder for {{ regnskab.aar }}
- [ ] Koncernoversigt med ejerandele og stemmerettigheder pr. {{ regnskab.slut }}
- [ ] Køb og salg af kapitalandele i året (overdragelsesaftaler, værdiansættelse)
- [ ] Udbytte modtaget fra datterselskaber (generalforsamlingsprotokol) og indeholdt udbytteskat
- [ ] Mellemregninger med koncernselskaber, afstemt med modparten
- [ ] Oplysning om sambeskatning (administrationsselskab, fordeling af skat)
- [ ] Ved koncernregnskab: oplysning om undtagelse efter ÅRL §§ 110-112
{% endif %}
## Gæld og forpligtelser
- [ ] Kreditorliste pr. {{ regnskab.slut }} afstemt til saldobalancen
- [ ] Fakturaer modtaget efter statusdagen, der vedrører perioden (fx el, vand, varme, telefon, revisor, advokat)
- [ ] Oversigt over skyldige omkostninger og forudbetalinger fra kunder
- [ ] Opgørelse over garantiforpligtelser og andre hensatte forpligtelser
- [ ] Eventualforpligtelser (kautioner, garantier, huslejeforpligtelse i uopsigelighedsperioden, købsforpligtelser)

## Løn og personale
- [ ] Lønoversigt/lønsedler for december (eller sidste måned) og årsoversigt pr. medarbejder
- [ ] Afstemning af løn til eIndkomst (vi foretager den, hvis lønnen kører i programmet)
- [ ] Feriepengeforpligtelse pr. {{ regnskab.slut }} (optjent, ikke afholdt ferie og ferietillæg) og evt. indbetaling til FerieKonto
- [ ] Oversigt over personalegoder (fri bil, telefon, sundhedsforsikring) og indberetning heraf
- [ ] Bonusser og andre lønforpligtelser optjent i året, men udbetalt senere
- [ ] Gennemsnitligt antal heltidsbeskæftigede i året (vi beregner det ud fra lønoplysningerne, hvis I ikke har tallet)
{% if branche.vikar or branche.rengoering %}- [ ] Oversigt over udenlandske medarbejdere og evt. arbejdsudleje (skat af lønindkomst ved arbejdsudleje)
{% endif %}
## Moms og afgifter
- [ ] Momsangivelser for alle perioder i regnskabsåret (vi henter dem i TastSelv, hvis vi har fuldmagt)
- [ ] Afstemning af momskonto til skattekontoen pr. {{ regnskab.slut }}
{% if branche.momsfritaget %}- [ ] Oplysning om fordeling af momspligtige og momsfrie aktiviteter (delvis fradragsret, pro rata-sats) og evt. lønsumsafgift
{% endif %}- [ ] Øvrige afgifter (energiafgifter, emballage, lønsumsafgift) med opgørelser

## Skat og ejerforhold
- [ ] Skattekontoudskrift pr. {{ regnskab.slut }} og årsopgørelse for {% if kunde.er_kapitalselskab %}selskabsskat{% else %}personlig skat{% endif %} for sidste år
{% if kunde.er_kapitalselskab %}- [ ] Acontoskat indbetalt i året (ordinær og frivillig)
- [ ] Udbytte deklareret og udbetalt i året samt indeholdt udbytteskat
- [ ] Mellemregning med {{ kunde.kapitalejere }} og ledelse – alle bevægelser i året (vi vurderer bl.a., om der er tale om lån, der skal beskattes efter ligningsloven § 16 E)
- [ ] Oplysning om transaktioner med nærtstående parter (køb, salg, leje, lån, honorarer) – se særskilt skema
{% else %}- [ ] Private hævninger og indskud i året; private andele af bil, telefon, internet og bolig
- [ ] Ønsker om anvendelse af virksomhedsordningen eller kapitalafkastordningen
- [ ] Ægtefælles medarbejde i virksomheden
{% endif %}

## Bekræftelse
Vi bekræfter, at det leverede materiale er fuldstændigt og retvisende, og at alle transaktioner er registreret i bogføringen.

Dato: ______________________

______________________________________
{{ kunde.navn }} – for {{ kunde.ledelsesorgan }}

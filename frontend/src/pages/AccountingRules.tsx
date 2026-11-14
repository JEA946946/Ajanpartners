import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Tabs, Tab, Alert,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import {
  BANK, CASH, PAYABLE, RECEIVABLE, RETAINED_EARNINGS, OWNER_RESULT, SUSPENSE, VAT_EU_GOODS,
  VAT_EU_SERVICES, VAT_INPUT, VAT_OUTPUT, VAT_SETTLEMENT, REMINDER_FEES, FX_GAIN, FX_LOSS,
} from '../utils/chart';

// De danske bogføringsregler, som systemet følger. Teksten er på dansk (lovtekst);
// overskrifterne kan oversættes.

type Row = [string, string];

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <Card>
    <CardContent>
      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{title}</Typography>
      {children}
    </CardContent>
  </Card>
);

const P: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Typography variant="body2" sx={{ mb: 1 }}>{children}</Typography>
);

const RuleTable: React.FC<{ head: [string, string]; rows: Row[] }> = ({ head, rows }) => (
  <TableContainer component={Paper} variant="outlined">
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell sx={{ fontWeight: 600, width: '35%' }}>{head[0]}</TableCell>
          <TableCell sx={{ fontWeight: 600 }}>{head[1]}</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map(([a, b]) => (
          <TableRow key={a}>
            <TableCell sx={{ verticalAlign: 'top' }}>{a}</TableCell>
            <TableCell>{b}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

const AccountingRules: React.FC = () => {
  const { t } = useTranslation();
  const [tab, setTab] = useState(0);

  const bookkeeping = (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Section title={t('accountingRules.bfTitle', 'Bogføringsloven')}>
        <P>
          Bogføringsloven (lov nr. 700 af 24. maj 2022) og bekendtgørelserne om digitale
          standardbogføringssystemer stiller krav til, hvordan bøgerne føres og opbevares. Systemet er bygget
          efter dem:
        </P>
        <RuleTable head={['Krav', 'Sådan gør systemet']} rows={[
          ['Hver transaktion registreres med bilag',
            'Hver postering ligger i én journal og kan have bilag vedhæftet. Bilag gemmes digitalt med SHA-256-fingeraftryk, så en udskiftet fil kan opdages. Månedslukning advarer om posteringer uden bilag.'],
          ['Registreringer kan følges (sporbarhed)',
            'Alle ændringer skrives i en hash-kædet audit-log, som ikke kan ændres. Handlinger fra revisorhuset markeres og logges også hos Ajan Partners.'],
          ['Fortløbende nummerering',
            'Posteringer får et kladdenummer (KL-…) og ved månedslukning et fortløbende nummer pr. journal og år (fx BANK-2026-00001) i datoorden og uden huller. Fakturaer og kreditnotaer får deres fortløbende nummer, når de udstedes.'],
          ['Ingen ændring af afsluttede tal',
            'En lukket måned kan ikke ændres; posteringerne er låst både i programmet og i databasen. Rettelser sker med en tilbageføring i en åben måned.'],
          ['Opbevaring i 5 år',
            'Regnskabsmateriale opbevares i 5 år fra udgangen af det regnskabsår, det vedrører. En kunde, der ophører, arkiveres read-only; bøgerne slettes ikke.'],
          ['Bankafstemning',
            'En måned kan ikke lukkes, før hver bankkonto er afstemt pr. månedens sidste dag.'],
          ['Eksport (SAF-T)',
            'Hver konto har standardkontoplanens nummer (standard_code), som bruges til SAF-T-eksporten.'],
        ]} />
      </Section>
      <Section title={t('accountingRules.journalsTitle', 'Journaler og tilstande')}>
        <RuleTable head={['Journal', 'Bruges til']} rows={[
          ['BANK, BANK2 …', 'Én journal pr. bankkonto: importerede kontoudtog og afstemning.'],
          ['KAS', 'Kasse: kontante udgifter.'],
          ['SALG', 'Fakturaer, kreditnotaer og rykkergebyrer.'],
          ['KØB', 'Regninger og udgifter.'],
          ['LØN', 'Lønkørsler.'],
          ['DIV', 'Manuelle posteringer, momsafregning og tilbageføringer.'],
          ['PRIMO', 'Primoposteringer (åbningsbalance).'],
          ['ÅA', 'Årsafslutning: resultatet overføres til egenkapitalen.'],
        ]} />
        <P>
          En postering er en <b>kladde</b> (ikke i bøgerne), <b>bogført</b> (i bøgerne, kan rettes) eller
          <b> valideret</b> (måneden er lukket; kan aldrig ændres).
        </P>
      </Section>
    </Box>
  );

  const vat = (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Section title={t('accountingRules.vatTitle', 'Moms (momsloven)')}>
        <P>
          Momssatsen er 25 % (momslovens § 33). Momskoderne følger Erhvervsstyrelsens momskodeliste, og hver
          linje bogføres med sin kode, så momsangivelsen og SAF-T kan dannes direkte fra bøgerne.
        </P>
        <RuleTable head={['Momskode', 'Bogføring']} rows={[
          ['S01 Salg 25 %', `Kredit omsætning, kredit salgsmoms (${VAT_OUTPUT}).`],
          ['S21/S22/S23 EU-salg B2B', 'Ingen moms; beløbet indgår i rubrik B. Fakturaen skal have købers momsnummer og teksten "Omvendt betalingspligt" ved ydelser.'],
          ['S41/S42 Uden for EU', 'Ingen moms; indgår i rubrik C.'],
          ['S02 Indenlandsk omvendt betalingspligt', 'Sælger lægger ikke moms på (fx byggeydelser, momslovens § 46); beløbet indgår i rubrik C.'],
          ['S82 Momsfritaget', 'Momsfrit salg efter momslovens § 13; indgår ikke på angivelsen.'],
          ['K010 Køb 25 %', `Debet omkostning, debet købsmoms (${VAT_INPUT}).`],
          ['K070 Restaurant og repræsentation', 'Kun 25 % af momsen kan trækkes fra (momslovens § 42, stk. 2); resten er en omkostning. Anden repræsentation (fx gaver) giver ikke fradrag.'],
          ['K110 Delvis fradrag', 'Fradragsprocenten (pro rata) sættes på momskoden for kunder med både momspligtige og momsfrie aktiviteter.'],
          ['K210 EU-varekøb', `Erhvervelsesmoms: kredit moms af varekøb i udlandet (${VAT_EU_GOODS}), debet købsmoms; beløbet indgår i rubrik A varer.`],
          ['K260 EU-ydelseskøb', `Omvendt betalingspligt: kredit moms af ydelseskøb i udlandet (${VAT_EU_SERVICES}), debet købsmoms; rubrik A ydelser.`],
          ['K410/K460 Uden for EU', 'Importmoms af varer og moms af ydelser med omvendt betalingspligt; indgår i felterne for køb i udlandet.'],
          ['K660 Byggeydelser m.m.', 'Indenlandsk omvendt betalingspligt: køber beregner salgsmoms og trækker købsmomsen fra.'],
          ['E-EL, E-OLIE, E-GAS, E-KUL, E-CO2, E-VAND', 'Energiafgifter, der kan godtgøres. Beløbet bogføres på afgiftskontoen og fratrækkes i momsangivelsen. Kun afgift af energi til momspligtig proces kan godtgøres.'],
        ]} />
      </Section>
      <Section title={t('accountingRules.vatReturnTitle', 'Momsangivelse og -afregning')}>
        <P>
          Momsangivelsen laves for kundens momsperiode (måned, kvartal eller halvår). Felterne er Skats: salgsmoms,
          moms af varekøb og ydelseskøb i udlandet, købsmoms, olie- og flaskegasafgift, elafgift, naturgas- og
          bygasafgift, kulafgift, CO2-afgift, vandafgift og rubrik A, B og C. Felterne tages fra momskontiene og
          kan derfor afstemmes mod saldobalancen.
        </P>
        <P>
          Ved afregning nulstilles momskontiene mod momsafregningskontoen ({VAT_SETTLEMENT}) med beløbet i hele
          kroner; øredifferencen går til øreafrunding. Når perioden er angivet hos Skat, låses den: der kan ikke
          bogføres i den bagefter.
        </P>
        <Alert severity="info">
          Frister: måned den 25. i den følgende måned; kvartal og halvår den 1. i den tredje måned efter
          periodens udløb. Skat kan flytte en frist, der falder på en weekend eller helligdag: tjek Skats
          momskalender.
        </Alert>
      </Section>
    </Box>
  );

  const chart = (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Section title={t('accountingRules.chartTitle', 'Kontoplan og årsregnskab')}>
        <P>
          Kontoplanen er Erhvervsstyrelsens standardkontoplan (gyldig fra 1. januar 2026): resultatopgørelsen
          1000-3999 og balancen 5000-8099. Alle konti oprettes; skabelonen (selskab, holding eller
          enkeltmandsvirksomhed) bestemmer, hvilke der er aktive fra start. Overskrifter (hovedkonti og
          gruppekonti) kan ikke bogføres på.
        </P>
        <P>
          Hver konto er knyttet til en linje i årsregnskabslovens skema (bilag 2): nettoomsætning, vareforbrug,
          andre eksterne omkostninger, personaleomkostninger, af- og nedskrivninger, finansielle poster og skat,
          og på balancen anlægsaktiver, varebeholdninger, tilgodehavender, likvider, egenkapital, hensatte
          forpligtelser og gæld. Resultatopgørelse og balance stilles op efter disse linjer.
        </P>
        <RuleTable head={['Konto', 'Bruges til']} rows={[
          [`${BANK} / ${CASH}`, 'Bank og kasse. Flere bankkonti oprettes med eget nummer og standardkonto 6480; hver får sin egen journal.'],
          [RECEIVABLE, 'Debitorer (pr. kunde, udlignes mod betalinger).'],
          [PAYABLE, 'Kreditorer (pr. leverandør).'],
          [SUSPENSE, 'Uafklarede poster: importerede banklinjer venter her, til de afstemmes.'],
          [`${FX_GAIN} / ${FX_LOSS}`, 'Kursgevinst og kurstab.'],
          [REMINDER_FEES, 'Renter og rykkergebyrer fra debitorer.'],
        ]} />
      </Section>
      <Section title={t('accountingRules.currencyTitle', 'Valuta')}>
        <P>
          Bøgerne føres i danske kroner. Debet og kredit er altid DKK. Et bilag i fremmed valuta registreres med
          valuta, kurs (DKK pr. 1 enhed) og beløbet i valutaen, så det kan følges tilbage til bilaget.
        </P>
      </Section>
    </Box>
  );

  const closing = (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Section title={t('accountingRules.closingTitle', 'Månedslukning og årsafslutning')}>
        <P>
          Månederne lukkes i rækkefølge. Ved lukning valideres og nummereres alle posteringer, og måneden låses.
          Lukningen kræver, at der ikke er kladder eller posteringer, der ikke balancerer, og at bankkontiene er
          afstemt.
        </P>
        <P>
          Ved årsafslutningen nulstilles resultatkontiene mod egenkapitalen (overført resultat, {RETAINED_EARNINGS},
          for selskaber; årets resultat, {OWNER_RESULT}, for enkeltmandsvirksomheder) i journalen ÅA på årets sidste
          dag. Balancens saldi overføres som primo til næste år (PRIMO), pr. debitor og kreditor, og året låses.
          Alle årets måneder skal være lukket først.
        </P>
      </Section>
    </Box>
  );

  const invoicing = (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Section title={t('accountingRules.invoiceTitle', 'Fakturakrav (momsbekendtgørelsens § 58)')}>
        <RuleTable head={['Krav', 'Sådan gør systemet']} rows={[
          ['Udstedelsesdato og fortløbende nummer', 'Nummeret gives, når fakturaen udstedes, så slettede udkast ikke giver huller.'],
          ['Sælgers navn, adresse og CVR-/SE-nummer', 'Hentes fra Indstillinger; fakturaen kan ikke udstedes uden.'],
          ['Købers navn og adresse', 'Påkrævet. Ved EU-salg uden moms også købers momsnummer.'],
          ['Leveringsdato', 'Leveringsdatoen vises; uden en særskilt dato er det fakturadatoen.'],
          ['Mængde og art', 'Hver linje har beskrivelse, antal og enhed.'],
          ['Pris uden moms, momssats og momsbeløb', 'Momsen specificeres pr. sats. Ved fremmed valuta vises momsbeløbet også i DKK.'],
          ['Omvendt betalingspligt', 'Teksten "Omvendt betalingspligt" kommer på fakturaen, når køber skal betale momsen.'],
          ['Offentlige kunder', 'Kræver EAN-/GLN-nummer og sendes som e-faktura (OIOUBL/Peppol via NemHandel).'],
        ]} />
        <P>En udstedt faktura kan ikke ændres eller slettes. Rettelser sker med en kreditnota.</P>
      </Section>
      <Section title={t('accountingRules.reminderTitle', 'Betalingsbetingelser, rykkere og renter (renteloven)')}>
        <RuleTable head={['Regel', 'Indhold']} rows={[
          ['Betalingsbetingelser', 'Netto 8, 14 eller 30 dage, løbende måned + 15 eller 30 dage, eller kontant.'],
          ['Rykkergebyr (§ 9 b)', 'Højst 100 kr. pr. rykker og højst 3 rykkere med gebyr, med mindst 10 dage imellem. Gebyret er ikke momspligtigt.'],
          ['Morarenter (§ 5)', 'Referencesatsen + 8 procentpoint pr. år. Uden aftalt forfald løber renten fra 30 dage efter, at fakturaen er sendt (§ 3).'],
          ['FI-kort (+71)', 'Fakturaen kan vise et FI-indbetalingskort type 71 med betalingsidentifikation og kreditornummer.'],
        ]} />
      </Section>
    </Box>
  );

  const tabs = [
    { label: t('accountingRules.tabBookkeeping', 'Bogføringsloven'), content: bookkeeping },
    { label: t('accountingRules.tabVat', 'Moms'), content: vat },
    { label: t('accountingRules.tabChart', 'Kontoplan og ÅRL'), content: chart },
    { label: t('accountingRules.tabClosing', 'Afslutning'), content: closing },
    { label: t('accountingRules.tabInvoicing', 'Fakturaer og rykkere'), content: invoicing },
  ];

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 0.5 }}>
        {t('accountingRules.title', 'Bogføringsregler')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('accountingRules.subtitle', 'De danske regler, systemet bogfører efter. Teksten er en vejledning og erstatter ikke rådgivning fra revisor.')}
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" sx={{ mb: 2 }}>
        {tabs.map((x) => <Tab key={x.label} label={x.label} />)}
      </Tabs>
      {tabs[tab].content}
    </Box>
  );
};

export default AccountingRules;

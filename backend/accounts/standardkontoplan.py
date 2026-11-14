"""Erhvervsstyrelsens standardkontoplan (version gyldig fra 2026-01-01).

Kilde: git.erst.dk/standard-filformater/standard-filformater,
Standardkontoplanen/JSON/2026-01-01-Standardkontoplan.json. Rækkerne nedenfor er
afskrevet direkte fra filen (kun mellemrum er normaliseret). Når Erhvervsstyrelsen
udgiver en ny version, erstattes STANDARD_TEXT og VERSION.

Typer: H = hovedkonto (overskrift), G = gruppekonto (overskrift over de konti,
der følger), K = konto, der kan bogføres på.

Hver konto får:
  - `standard_code`: standardkontoplanens nummer (bruges i SAF-T),
  - `arl_line`: linjen i årsregnskabslovens skema (bilag 2, artsopdelt
    resultatopgørelse og balance i kontoform), se ARL_LINES,
  - kontotype (aktiv/passiv/egenkapital/indtægt/omkostning).

Skabelonerne (TEMPLATES) bestemmer, hvilke konti der er aktive fra start. Alle
konti oprettes altid, så kunden kan aktivere flere uden at oprette nye numre.
"""

VERSION = "2026-01-01"

STANDARD_TEXT = """
1000;H;RESULTATOPGØRELSE
1001;G;Nettoomsætning
1010;K;Salg af varer og ydelser
1050;K;Salg af varer udland, EU
1100;K;Salg af varer udland, ikke-EU
1150;K;Salg af ydelser udland, EU
1200;K;Salg af ydelser udland, ikke-EU
1210;K;Salgsrabatter
1250;K;Salgsfragt
1300;K;Regulering igangværende arbejder
1400;G;Ændring i lagre af færdigvarer og varer under fremstilling
1410;K;Varelagerregulering på lagre af færdigvarer og varer under fremstilling
1430;K;Nedskrivning på lagre af færdigvarer og varer under fremstilling
1450;K;Andel af nedskrivning på lagre af færdigvarer og varer under fremstilling (ej fradragsberettiget skattemæssigt)
1460;K;Øvrige ændringer på lagre af færdigvarer og varer under fremstilling
1495;G;Arbejde udført for egen regning og opført under aktiver
1496;K;Arbejde udført for egen regning og opført under aktiver
1500;G;Andre driftsindtægter
1510;K;Gevinst ved salg af immaterielle anlægsaktiver
1530;K;Gevinst ved salg af materielle anlægsaktiver
1545;K;Offentlige tilskud
1550;K;Øvrige andre driftsindtægter
1595;H;Eksterne omkostninger
1600;G;Omkostninger til råvarer og hjælpematerialer
1610;K;Varekøb
1630;K;Varekøb udland, EU
1650;K;Varekøb udland, ikke-EU
1660;K;Ydelseskøb
1710;K;Ydelseskøb udland, EU
1740;K;Ydelseskøb, udland, ikke-EU
1745;K;Underleverandører (varer/ydelser leveret til kunder)
1760;K;Fragtomkostninger
1770;K;Varelagerregulering på lagre af råvarer og hjælpematerialer
1800;K;Nedskrivning på varelager
1801;K;Øvrige produktionsomkostninger
1805;K;Andel af nedskrivning på varelager (ej fradragsberettiget skattemæssigt)
1807;K;Værdi af eget vareforbrug (kun klasse A)
1820;H;Andre eksterne omkostninger
1821;G;Salgsomkostninger
1850;K;Annoncering og reklame
1870;K;Udstillinger og dekoration
1910;K;Repræsentationsomkostninger, skattemæssigt begrænset fradrag
1930;K;Repræsentationsomkostninger, fuld fradragsret skattemæssigt
1950;K;Andre salgsomkostninger
1990;K;Gaver og blomster
2000;K;Rejseomkostninger (salgsomkostning)
2020;G;Lokaleomkostninger
2030;K;Husleje
2050;K;El
2060;K;Elafgift
2070;K;Vand
2080;K;Varme
2085;K;Privat andel el, vand og varme (kun klasse A)
2090;K;Vandafgift
2100;K;Olie- og flaskegasafgift
2110;K;Kulafgift
2120;K;Naturgas- og bygasafgift
2130;K;Co2-afgift
2140;K;Øvrige afgifter
2150;K;Rengøring og renovation (affaldshåndtering)
2160;K;Reparation og vedligeholdelse
2170;K;Reparation og vedligeholdelse, ejendom skattemæssigt afskrivningsberettiget, bygning 1
2180;K;Forsikringer til lokaler og bygninger
2190;K;Ejendomsskatter
2200;K;Andre lokaleomkostninger
2220;G;Administrationsomkostninger
2230;K;Småanskaffelser under skattemæssig grænse for småaktiver
2240;K;Småanskaffelser over skattemæssig grænse for småaktiver
2255;K;Forskningsomkostninger
2260;K;Udviklingsomkostninger
2265;K;Andel af forskningsomkostninger (berettiget til forhøjet skattemæssigt fradrag)
2266;K;Andel af udviklingsomkostninger (berettiget til forhøjet skattemæssigt fradrag)
2280;K;Tab på tilgodehavender fra salg og tjenesteydelser
2290;K;Regulering af nedskrivning på tilgodehavender fra salg og tjenesteydelser
2295;K;Andel af regulering af nedskrivning på tilgodehavender fra salg og tjenesteydelser (ej fradragsberettiget skattemæssigt)
2310;K;It-udstyr (hardware, software inkl. licenser og abonnementer)
2350;K;Kantineomkostninger
2370;K;Kontingenter
2375;K;Aviser og blade
2380;K;Faglitteratur
2390;K;Porto og gebyrer
2410;K;Telefon og internet mv. (kun virksomhed)
2430;K;Privat andel / fri-telefon (kun klasse A)
2450;K;Kontorartikler
2460;K;Leje og operationelle leasingydelser (ekskl. husleje)
2470;K;Rejseomkostninger (administrationsomkostning)
2480;K;Vikarassistance
2510;K;Konsulentydelser
2530;K;Leasingomkostninger, personbiler
2540;K;Driftsomkostninger, personbiler
2548;K;Leasingomkostninger, blandet benyttet personbil (kun klasse A)
2550;K;Privat andel af biludgifter (kun klasse A)
2560;K;Driftsomkostninger, varebiler
2567;K;Leasingomkostninger, blandet benyttet varebil (kun klasse A)
2569;K;Leasingomkostninger, varebiler
2580;K;Privat andel af blandet benyttet varebil (kun klasse A)
2620;K;Parkeringsomkostninger
2650;K;Øvrige forsikringer
2660;K;Offentlige gebyrer og bøder (ej fradragsberettiget skattemæssigt)
2670;K;Revision og regnskabsmæssig assistance
2680;K;Advokatmæssig assistance
2690;K;Øvrige rådgivningshonorarer
2700;K;Ej skattemæssigt fradragsberettigede rådgivningshonorarer
2710;K;Administrationsvederlag/management fee
2720;K;Øreafrunding/kassedifferencer
2810;K;Andre eksterne omkostninger
2841;H;Personaleomkostninger
2842;G;Lønninger
2845;K;AM Bidragspligtig A-Indkomst
2846;K;AM Bidragsfri A-Indkomst
2847;K;B-honorar
2860;K;Feriepenge og SH-tillæg
2865;K;Ferietillæg
2866;K;Feriepengeforpligtelse, regulering
2870;K;Jubilæumsgratiale og fratrædelsesgodtgørelse
2880;K;Bestyrelseshonorar
2885;K;Lønrefusioner
2887;K;Personalegoder
2888;K;Fri bil
2895;K;Skattefri rejse- og befordringsgodtgørelse
2896;K;Kursusudgifter
2897;K;ATP, medarbejder
2898;K;ATP, arbejdsgiver
2906;G;Pensioner
2910;K;Pensioner, arbejdsgiver
2920;K;Vederlag til afløsning af pensionstilsagn
2925;K;Øvrige pensionsomkostninger
2927;G;Andre omkostninger til social sikring
2930;K;Øvrige omkostninger til social sikring
2946;K;Lønsumsafgift
2947;K;Arbejdsskadeforsikringer
2991;G;Af- og nedskrivninger af materielle og immaterielle anlægsaktiver
3000;K;Af- og nedskrivninger af erhvervede immaterielle anlægsaktiver
3010;K;Af- og nedskrivninger af goodwill
3020;K;Af- og nedskrivninger af grunde og bygninger
3030;K;Af- og nedskrivninger af produktionsanlæg og maskiner
3040;K;Af- og nedskrivninger af indretning af lejede lokaler
3050;K;Af- og nedskrivninger af andre anlæg, driftsmateriel og inventar
3060;K;Af- og nedskrivninger af software
3070;K;Af- og nedskrivninger af finansielt leasede grunde og bygninger
3080;K;Af- og nedskrivninger af finansielt leasede produktionsanlæg og maskiner
3090;K;Af- og nedskrivninger af finansielt leasede andre anlæg, driftsmateriel og inventar
3095;K;Privat andel af af- og nedskrivninger (kun klasse A)
3097;K;Gevinst ved salg af andre anlæg, driftsmateriel og inventar blandet benyttet (kun klasse A)
3099;K;Tab ved salg af andre anlæg, driftsmateriel og inventar blandet benyttet (kun klasse A)
3120;G;Nedskrivning af omsætningsaktiver, som overstiger normale nedskrivninger
3130;K;Nedskrivning af omsætningsaktiver, som overstiger normale nedskrivninger
3150;G;Andre driftsomkostninger
3160;K;Tab ved salg af immaterielle anlægsaktiver
3165;K;Tab ved salg af materielle anlægsaktiver
3170;K;Øvrige andre driftsomkostninger
3180;G;Dagsværdiregulering af investeringsejendomme
3185;K;Værdireguleringer af investeringsejendomme
3191;H;Indtægter af kapitalandele i tilknyttede og associerede virksomheder
3192;G;Indtægter af kapitalandele i tilknyttede virksomheder
3193;K;Modtagne udbytter fra tilknyttede virksomheder
3194;K;Gevinst ved afhændelse af kapitalandele i tilknyttede virksomheder
3196;K;Tab ved afhændelse af kapitalandele i tilknyttede virksomheder
3197;K;Nedskrivning af kapitalandele i tilknyttede virksomheder
3198;K;Tilbageførsel af nedskrivning af kapitalandele i tilknyttede virksomheder
3200;K;Øvrige indtægter af kapitalandele i tilknyttede virksomheder
3210;G;Indtægter af kapitalandele i associerede virksomheder
3211;K;Modtagne udbytter fra associerede virksomheder
3212;K;Gevinst ved afhændelse af kapitalandele i associerede virksomheder
3214;K;Tab ved afhændelse af kapitalandele i associerede virksomheder
3215;K;Nedskrivning af kapitalandele i associerede virksomheder
3216;K;Tilbageførsel af nedskrivning af kapitalandele i associerede virksomheder
3217;K;Øvrige indtægter af kapitalandele i associerede virksomheder
3220;G;Indtægter af kapitalinteresser
3221;K;Modtagne udbytter fra kapitalinteresser
3222;K;Gevinst ved afhændelse af kapitalinteresser
3224;K;Tab ved afhændelse af kapitalinteresser
3225;K;Nedskrivning af kapitalinteresser
3226;K;Tilbageførsel af nedskrivning af kapitalinteresser
3230;K;Øvrige indtægter af kapitalinteresser
3251;G;Resultatandele, der hidrører fra tilknyttede virksomheder
3252;K;Resultatandele, der hidrører fra tilknyttede virksomheder
3261;G;Resultatandele, der hidrører fra associerede virksomheder
3262;K;Resultatandele, der hidrører fra associerede virksomheder
3271;G;Resultatandele, der hidrører fra kapitalinteresser
3272;K;Resultatandele, der hidrører fra kapitalinteresser
3370;G;Indtægter af andre kapitalandele, værdipapirer og tilgodehavender, der er anlægsaktiver
3380;K;Udbytte fra unoterede porteføljeaktier (bruttoudbytte)
3385;K;Kursgevinster af andre kapitalandele, værdipapirer og tilgodehavender, der er anlægsaktiver
3390;K;Renteindtægter af andre kapitalandele, værdipapirer og tilgodehavender, der er anlægsaktiver
3395;K;Værdiregulering af andre kapitalandele og værdipaprer, der er anlægsaktiver
3400;K;Øvrige indtægter af andre kapitalandele, værdipapirer og tilgodehavender, der er anlægsaktiver
3411;G;Andre finansielle indtægter fra tilknyttede virksomheder
3440;K;Andre finansielle indtægter fra tilknyttede virksomheder
3445;K;Renteindtægter fra tilknyttede virksomheder
3451;G;Andre finansielle indtægter
3470;K;Renter fra banker
3490;K;Renter vedr. tilgodehavende fra salg af varer og tjenesteydelser
3510;K;Rentetillæg mv. fra det offentlige (ej skattepligtig)
3530;K;Øvrige finansielle indtægter
3535;K;Valutakursregulering (gevinst)
3536;K;Værdiregulering af børsnoterede værdipapirer, der er omsætningsaktiver
3537;K;Værdiregulering af andre kapitalandele og værdipaprer, der er omsætningsaktiver
3541;G;Nedskrivning af finansielle aktiver
3560;K;Nedskrivning af finansielle anlægs- og omsætningsaktiver
3571;H;Øvrige finansielle omkostninger
3572;G;Finansielle omkostninger, der hidrører fra tilknyttede virksomheder
3590;K;Finansielle omkostninger, der hidrører fra tilknyttede virksomheder
3596;K;Valutakursreguleringer, udenlandske dattervirksomheder
3601;G;Andre finansielle omkostninger
3610;K;Valutakursregulering (tab)
3630;K;Kurstab på likvider, bankgæld og prioritetsgæld
3640;K;Renter på finansiel leasinggæld
3650;K;Renter vedr. leverandører af varer og tjenesteydelser
3670;K;Renter til banker og realkreditinstitutter
3675;K;Renter til det offentlige (ej fradragsberettiget skattemæssigt)
3690;K;Øvrige finansielle omkostninger
3703;G;Skat af årets resultat
3740;K;Årets skat (skat af årets skattepligtige indkomst)
3760;K;Årets regulering af udskudt skat
3780;K;Regulering af skat vedrørende tidligere år
3791;G;Andre skatter
3810;K;Andre skatter
5000;H;BALANCE
5001;H;AKTIVER
5002;H;Anlægsaktiver
5003;H;Immaterielle anlægsaktiver
5004;G;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter
5010;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Kostpris primo
5011;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Årets tilgange
5012;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Årets afgange
5015;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Intern overførsel til/fra andre poster
5020;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, opskrivninger primo
5021;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Årets opskrivninger
5022;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, årets tilbageførsler af tidligere års opskrivninger
5030;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Af- og nedskrivninger primo
5031;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Årets af- og nedskrivninger
5032;K;Færdiggjort udviklingsprojekter, herunder patenter og lignende rettigheder, der stammer fra udviklingsprojekter, Tilbageførte af- og nedskrivninger
5041;G;Erhvervede immaterielle anlægsaktiver
5042;K;Erhvervede immaterielle anlægsaktiver, kostpris primo
5043;K;Erhvervede immaterielle anlægsaktiver, årets tilgange
5044;K;Erhvervede immaterielle anlægsaktiver, årets afgange
5050;K;Erhvervede immaterielle anlægsaktiver, Opskrivninger primo
5051;K;Erhvervede immaterielle anlægsaktiver, Årets opskrivninger
5052;K;Erhvervede immaterielle anlægsaktiver, Tilbageførte opskrivninger fra tidligere år
5055;K;Erhvervede immaterielle anlægsaktiver, Af- og nedskrivninger primo
5056;K;Erhvervede immaterielle anlægsaktiver, årets af- og nedskrivninger
5057;K;Erhvervede immaterielle anlægsaktiver, tilbageførte af- og nedskrivninger
5061;G;Goodwill
5062;K;Goodwill, kostpris primo
5063;K;Goodwill, årets tilgange
5064;K;Goodwill, årets afgange
5075;K;Goodwill, af- og nedskrivninger primo
5076;K;Goodwill, årets af- og nedskrivninger
5077;K;Goodwill, tilbageførte afskrivninger
5080;G;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver
5085;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Kostpris primo
5090;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Årets tilgange
5095;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Årets afgange
5100;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Intern overførsel til/fra andre poster
5110;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Af- og nedskrivninger primo
5111;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Årets af- og nedskrivninger
5112;K;Udviklingsprojekter under udførelse og forudbetalinger for immaterielle anlægsaktiver, Tilbageførte af- og nedskrivninger
5142;H;Materielle anlægsaktiver
5150;G;Investeringsejendomme
5160;K;Investeringsejendomme, kostpris primo
5170;K;Investeringsejendomme, årets tilgange
5180;K;Investeringsejendomme, årets afgange
5185;K;Investeringsejendomme, intern overførsel til/fra andre poster
5190;K;Investeringsejendomme, årets forbedringer
5200;K;Investeringsejendomme, værdireguleringer primo
5201;K;Investeringsejendomme, årets værdireguleringer
5205;K;Investeringsejendomme, Af- og nedskrivninger primo
5210;K;Investeringsejendomme, årets af- og nedskrivninger
5220;K;Investeringsejendomme, tilbageførte af- og nedskrivninger
5231;G;Investeringsejendomme under opførelse
5240;K;Investeringsejendomme under opførelse, kostpris primo
5250;K;Investeringsejendomme under opførelse, årets tilgange
5260;K;Investeringsejendomme under opførelse, årets afgange
5265;K;Investeringsejendomme, intern overførsel til/fra andre poster
5280;K;Investeringsejendomme under opførelse, øvrige værdireguleringer primo
5281;K;Investeringsejendomme under opførelse, årets værdireguleringer
5282;K;Investeringsejendomme under opførelse, nedskrivninger, primo
5290;K;Investeringsejendomme under opførelse, årets nedskrivninger
5300;K;Investeringsejendomme under opførelse, tilbageførte nedskrivninger
5311;G;Grunde og bygninger
5320;K;Grunde og bygninger, kostpris primo
5330;K;Grunde og bygninger, årets tilgange
5340;K;Grunde og bygninger, årets afgange
5350;K;Grunde og bygninger, årets forbedringer
5370;K;Grunde og bygninger, værdireguleringer primo
5371;K;Grunde og bygninger, årets værdireguleringer
5372;K;Grunde og bygninger, Af- og nedskrivninger primo
5390;K;Grunde og bygninger, årets af- og nedskrivninger
5400;K;Grunde og bygninger, tilbageførte af- og nedskrivninger
5411;G;Produktionsanlæg og maskiner
5420;K;Produktionsanlæg og maskiner, kostpris primo
5430;K;Produktionsanlæg og maskiner, årets tilgange
5440;K;Produktionsanlæg og maskiner, årets afgange
5450;K;Produktionsanlæg og maskiner, Værdireguleringer primo
5451;K;Produktionsanlæg og maskiner, Årets værdireguleringer
5452;K;Produktionsanlæg og maskiner, Af- og nedskrivninger primo
5470;K;Produktionsanlæg og maskiner, årets af- og nedskrivninger
5480;K;Produktionsanlæg og maskiner, tilbageførte af- og nedskrivninger
5491;G;Indretning af lejede lokaler
5500;K;Indretning af lejede lokaler, kostpris primo
5510;K;Indretning af lejede lokaler, årets tilgange
5520;K;Indretning af lejede lokaler, årets afgange
5530;K;Indretning af lejede lokaler, Værdireguleringer primo
5531;K;Indretning af lejede lokaler, Årets værdireguleringer
5532;K;Indretning af lejede lokaler, Af- og nedskrivninger primo
5540;K;Indretning af lejede lokaler, årets af- og nedskrivninger
5550;K;Indretning af lejede lokaler, tilbageførte af- og nedskrivninger
5561;G;Andre anlæg, driftsmateriel og inventar
5570;K;Andre anlæg, driftsmateriel og inventar, kostpris primo
5580;K;Andre anlæg, driftsmateriel og inventar, årets tilgange
5590;K;Andre anlæg, driftsmateriel og inventar, årets afgange
5600;K;Andre anlæg, driftsmateriel og inventar, Værdireguleringer primo
5601;K;Andre anlæg, driftsmateriel og inventar, Årets værdireguleringer
5602;K;Andre anlæg, driftsmateriel og inventar, Af- og nedskrivninger primo
5610;K;Andre anlæg, driftsmateriel og inventar, årets af- og nedskrivninger
5620;K;Andre anlæg, driftsmateriel og inventar, tilbageførte af- og nedskrivninger
5631;G;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver
5640;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, kostpris primo
5650;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, årets tilgange
5660;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, årets afgange
5670;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, værdireguleringer primo
5671;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, årets værdireguleringer
5675;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, nedskrivninger primo
5676;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, årets nedskrivninger
5677;K;Materielle anlægsaktiver under udførelse og forudbetalinger for materielle anlægsaktiver, tilbageførte nedskrivninger
5681;G;Andre anlæg, driftsmateriel og inventar blandet benyttet (kun klasse A)
5682;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, kostpris primo (kun klasse A)
5683;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Årets tilgange (kun klasse A)
5684;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Årets afgange (kun klasse A)
5685;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Værdireguleringer primo (kun klasse A)
5686;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Årets værdireguleringer (kun klasse A)
5687;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Af- og nedskrivninger primo (kun klasse A)
5688;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Årets af- og nedskrivninger (kun klasse A)
5689;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, tilbageførte af- og nedskrivninger (kun klasse A)
5690;K;Andre anlæg, driftsmateriel og inventar blandet benyttet, Gevinst og tab (kun klasse A)
5701;G;Finansielt leasede aktiver
5710;K;Finansielt leasede aktiver, Kostpris primo
5720;K;Finansielt leasede aktiver, årets tilgange
5730;K;Finansielt leasede aktiver, årets afgange
5740;K;Finansielt leasede aktiver, værdireguleringer primo
5741;K;Finansielt leasede aktiver, årets værdireguleringer
5745;K;Finansielt leasede aktiver, af- og nedskrivninger primo
5750;K;Finansielt leasede aktiver, årets af- og nedskrivninger
5760;K;Finansielt leasede aktiver, tilbageførte af- og nedskrivninger
5772;H;Finansielle anlægsaktiver
5773;G;Kapitalandele i tilknyttede virksomheder
5800;K;Kapitalandele i tilknyttede virksomheder, kostpris primo
5810;K;Kapitalandele i tilknyttede virksomheder, årets tilgange
5820;K;Kapitalandele i tilknyttede virksomheder, årets afgange
5825;K;Kapitalandele i tilknyttede virksomheder, intern overførsel til/fra andre poster
5829;K;Kapitalandele i tilknyttede virksomheder, opskrivninger primo
5830;K;Kapitalandele i tilknyttede virksomheder, årets opskrivninger
5831;K;Kapitalandele i tilknyttede virksomheder, årets tilbageførsler af tidligere års opskrivninger
5835;K;Kapitalandele i tilknyttede virksomheder, nedskrivninger primo
5836;K;Kapitalandele i tilknyttede virksomheder, årets nedskrivninger
5837;K;Kapitalandele i tilknyttede virksomheder, årets tilbageførsler af tidligere års nedskrivninger
5841;G;Tilgodehavender hos tilknyttede virksomheder (anlægsaktiv)
5842;K;Tilgodehavender hos tilknyttede virksomheder (anlægsaktiv)
5843;K;Tilgodehavender hos tilknyttede virksomheder, nedskrivninger primo (anlægsaktiv)
5844;K;Tilgodehavender hos tilknyttede virksomheder, nedskrivninger i årets løb (anlægsaktiv)
5845;K;Tilgodehavender hos tilknyttede virksomheder, tilbageførsel af tidligere års nedskrivninger (anlægsaktiv)
5851;G;Kapitalandele i associerede virksomheder
5852;K;Kapitalandele i associerede virksomheder, kostpris primo
5853;K;Kapitalandele i associerede virksomheder, årets tilgange
5854;K;Kapitalandele i associerede virksomheder, årets afgange
5855;K;Kapitalandele i associerede virksomheder, intern overførsel til/fra andre poster
5860;K;Kapitalandele i associerede virksomheder, opskrivninger primo
5861;K;Kapitalandele i associerede virksomheder, årets opskrivninger
5862;K;Kapitalandele i associerede virksomheder, årets tilbageførsler af tidligere års opskrivninger
5870;K;Kapitalandele i associerede virksomheder, nedskrivninger primo
5871;K;Kapitalandele i associerede virksomheder, årets nedskrivninger
5872;K;Kapitalandele i associerede virksomheder, årets tilbageførsler af tidligere års nedskrivninger
5881;G;Tilgodehavender hos associerede virksomheder (anlægsaktiv)
5882;K;Tilgodehavender hos associerede virksomheder (anlægsaktiv)
5883;K;Tilgodehavender hos associerede virksomheder, nedskrivninger primo (anlægsaktiv)
5884;K;Tilgodehavender hos associerede virksomheder, nedskrivninger i årets løb (anlægsaktiv)
5885;K;Tilgodehavender hos associerede virksomheder, tilbageførsel af tidligere års nedskrivninger (anlægsaktiv)
5891;G;Kapitalinteresser
5900;K;Kapitalinteresser, kostpris primo
5910;K;Kapitalinteresser, årets tilgange
5920;K;Kapitalinteresser, årets afgange
5925;K;Kapitalinteresser, intern overførsel til/fra andre poster
5929;K;Kapitalinteresser, opskrivninger primo
5930;K;Kapitalinteresser, årets opskrivninger
5931;K;Kapitalinteresser, årets tilbageførsler af tidligere års opskrivninger
5935;K;Kapitalinteresser, nedskrivninger primo
5940;K;Kapitalinteresser, årets nedskrivninger
5950;K;Kapitalinteresser, årets tilbageførsler af tidligere års nedskrivninger
5961;G;Tilgodehavender hos kapitalinteresser (anlægsaktiv)
5970;K;Tilgodehavender hos kapitalinteresser (anlægsaktiv)
5980;K;Tilgodehavender hos kapitalinteresser, nedskrivninger primo (anlægsaktiv)
5984;K;Tilgodehavender hos kapitalinteresser, nedskrivninger i årets løb (anlægsaktiv)
5985;K;Tilgodehavender hos kapitalinteresser, tilbageførsel af tidligere års nedskrivninger (anlægsaktiv)
5991;G;Andre værdipapirer og kapitalandele
6000;K;Andre værdipapirer og kapitalandele
6011;G;Andre tilgodehavender (anlægsaktiv)
6020;K;Udskudte skatteaktiver (anlægsaktiv)
6030;K;Øvrige tilgodehavender (anlægsaktiv)
6040;K;Deposita (anlægsaktiv)
6051;G;Tilgodehavender hos virksomhedsdeltagere og ledelse (anlægsaktiv)
6061;K;Tilgodehavender hos direktionen (anlægsaktiv)
6062;K;Tilgodehavender hos bestyrelsen (anlægsaktiv)
6063;K;Tilgodehavender hos tilsynsråd (anlægsaktiv)
6064;K;Tilgodehavender hos repræsentantskab (anlægsaktiv)
6073;H;Omsætningsaktiver
6074;H;Varebeholdninger
6075;G;Råvarer og hjælpematerialer
6080;K;Råvarer og hjælpematerialer, kostpris primo
6081;K;Råvarer og hjælpematerialer, årets tilgange
6082;K;Råvarer og hjælpematerialer, årets afgange
6083;K;Råvarer og hjælpematerialer, intern overførsel til/fra andre poster
6085;K;Råvarer og hjælpematerialer, nedskrivninger primo
6090;K;Råvarer og hjælpematerialer, årets nedskrivning
6091;K;Råvarer og hjælpematerialer, tilbageførsel af tidligere års nedskrivninger
6101;G;Varer under fremstilling
6110;K;Varer under fremstilling, kostpris primo
6111;K;Varer under fremstilling, årets tilgange
6112;K;Varer under fremstilling, årets afgange
6113;K;Varer under fremstilling, intern overførsel til/fra andre poster
6115;K;Varer under fremstilling, nedskrivninger primo
6120;K;Varer under fremstilling, årets nedskrivning
6121;K;Varer under fremstilling, tilbageførsel af tidligere års nedskrivninger
6131;G;Fremstillede varer og handelsvarer
6140;K;Fremstillede varer og handelsvarer, kostpris primo
6141;K;Fremstillede varer og handelsvarer, årets tilgange
6142;K;Fremstillede varer og handelsvarer, årets afgange
6143;K;Fremstillede varer og handelsvarer, intern overførsel til/fra andre poster
6145;K;Fremstillede varer og handelsvarer, nedskrivninger primo
6150;K;Fremstillede varer og handelsvarer, årets nedskrivning
6151;K;Fremstillede varer og handelsvarer, tilbageførsel af tidligere års nedskrivninger
6161;G;Forudbetalinger for varer
6170;K;Forudbetalinger for varer
6182;H;Tilgodehavender
6183;G;Tilgodehavender fra salg og tjenesteydelser
6190;K;Tilgodehavender fra salg og tjenesteydelser
6200;K;Tilgodehavender fra salg og tjenesteydelser, nedskrivninger primo
6201;K;Nedskrivninger i årets løb
6202;K;Tilbageførsel af tidligere års nedskrivninger
6231;G;Igangværende arbejder for fremmed regning
6240;K;Igangværende arbejder for fremmed regning
6251;G;Tilgodehavender hos tilknyttede virksomheder (omsætningsaktiv)
6252;K;Tilgodehavender hos tilknyttede virksomheder (omsætningsaktiv)
6255;K;Tilgodehavender hos tilknyttede virksomheder, nedskrivninger primo (omsætningsaktiv)
6256;K;Tilgodehavender hos tilknyttede virksomheder, nedskrivninger i årets løb
6257;K;Tilgodehavender hos tilknyttede virksomheder, tilbageførsel af tidligere års nedskrivninger (omsætningsaktiv)
6261;G;Tilgodehavender hos associerede virksomheder (omsætningsaktiv)
6262;K;Tilgodehavender hos associerede virksomheder (omsætningsaktiv)
6265;K;Tilgodehavender hos associerede virksomheder, nedskrivninger primo (omsætningsaktiv)
6266;K;Tilgodehavender hos associerede virksomheder, nedskrivninger i årets løb (omsætningsaktiv)
6267;K;Tilgodehavender hos associerede virksomheder, tilbageførsel af tidligere års nedskrivninger (omsætningsaktiv)
6281;G;Tilgodehavender hos kapitalinteresser (omsætningsaktiv)
6282;K;Tilgodehavender hos kapitalinteresser (omsætningsaktiv)
6285;K;Tilgodehavender hos kapitalinteresser, nedskrivninger primo (omsætningsaktiv)
6286;K;Tilgodehavender hos kapitalinteresser, nedskrivninger i årets løb (omsætningsaktiv)
6287;K;Tilgodehavender hos kapitalinteresser, tilbageførsel af tidligere års nedskrivninger (omsætningsaktiv)
6301;G;Andre tilgodehavender (omsætningsaktiv)
6305;K;Udskudte skatteaktiver (omsætningsaktiv)
6310;K;Tilgodehavende kildeskat (omsætningsaktiv)
6315;K;Tilgodehavende selskabsskat (omsætningsaktiv)
6320;K;Tilgodehavende moms (omsætningsaktiv)
6330;K;Øvrige tilgodehavender (omsætningsaktiv)
6341;G;Krav på indbetaling af virksomhedskapital og overkurs
6350;K;Krav på indbetaling af virksomhedskapital og overkurs
6361;G;Tilgodehavender hos virksomhedsdeltagere og ledelse (omsætningsaktiv)
6365;K;Tilgodehavender hos direktionen (omsætningsaktiv)
6370;K;Tilgodehavender hos bestyrelsens (omsætningsaktiv)
6375;K;Tilgodehavender hos tilsynsråd (omsætningsaktiv)
6376;K;Tilgodehavender hos repræsentantskab (omsætningsaktiv)
6381;G;Periodeafgrænsningsposter
6390;K;Periodeafgrænsningsposter, der kan opretholdes skattemæssigt
6400;K;Periodeafgrænsningsposter, der ikke kan opretholdes skattemæssigt
6412;H;Værdipapirer og kapitalandele
6413;G;Kapitalandele i tilknyttede virksomheder
6420;K;Kapitalandele i tilknyttede virksomheder som ikke er bestemt til vedvarende eje
6431;G;Andre værdipapirer og kapitalandele
6450;K;Andre værdipapirer og kapitalandele som ikke er bestemt til vedvarende eje
6462;G;Likvide beholdninger
6470;K;Likvide beholdninger
6480;K;Bankkonto
6500;H;PASSIVER
6501;H;Egenkapital
6502;G;Virksomhedskapital
6510;K;Registreret kapital mv.
6520;K;Indbetalt registreret kapital mv.
6525;K;Ikke indbetalt registreret kapital mv.
6531;G;Overkurs ved emission
6540;K;Overkurs ved emission
6551;G;Reserve for opskrivninger
6560;K;Reserve for opskrivninger
6591;G;Andre reserver
6800;K;Reserve for nettoopskrivning efter den indre værdis metode
6810;K;Reserve for udlån og sikkerhedsstillelse
6830;K;Reserve for ikke indbetalt virksomhedskapital og overkurs
6840;K;Reserve for udviklingsomkostninger
6870;K;Øvrige lovpligtige reserver
6890;K;Vedtægtsmæssige reserver
6910;K;Øvrige reserver
6914;K;Reserve for iværksætterselskaber
6915;K;Egenkapital primo (kun klasse A)
6916;K;Årets resultat (kun klasse A)
6917;K;Fri bil (kun klasse A)
6918;K;Rejse og befordringsgodtgørelse (kun klasse A)
6919;K;Fri telefon (Kun klasse A)
6920;K;Private andele (Kun klasse A)
6921;K;Private afskrivninger (Kun klasse A)
6922;K;Driftsudgifter uden fradrag (Kun klasse A)
6923;K;Privat hævet (kun klasse A)
6924;K;Privat indskud (kun klasse A)
6931;G;Overført resultat
6935;K;Overført resultat, primo
6940;K;Overført resultat, jf. resultatdisponering
6951;G;Foreslået udbytte indregnet under egenkapitalen
6955;K;Foreslået udbytte, primo
6956;K;Udloddet udbytte
6960;K;Foreslået udbytte jf. resultatdisponeringen
6972;H;Hensatte forpligtelser
6980;G;Hensættelser til pensioner og lignende forpligtelser
6985;K;Hensættelser til pensioner og lignende forpligtelser
7000;G;Hensættelse til udskudt skat
7010;K;Hensættelser til udskudt skat
7031;G;Andre hensatte forpligtelser
7040;K;Andre hensatte forpligtelser
7052;H;Langfristede gældsforpligtelser
7053;G;Gæld, der er optaget ved udstedelse af obligationer (langfristet)
7055;K;Gæld, der er optaget ved udstedelse af obligationer (langfristet)
7061;G;Konvertible og udbyttegivende gældsbreve (langfristet)
7065;K;Konvertible og udbyttegivende gældsbreve (langfristet)
7080;G;Gæld til kreditinstitutter (langfristet)
7110;K;Gæld til kredit- og realkreditinstitutter (langfristet)
7120;K;Gæld til banker (langfristet)
7125;K;Leasingforpligtelser (langfristet)
7126;K;Øvrig langfristet gæld
7141;G;Modtagne forudbetalinger fra kunder (langfristet)
7145;K;Modtagne forudbetalinger fra kunder (langfristet)
7151;G;Leverandører af varer og tjenesteydelser (langfristet)
7155;K;Leverandører af varer og tjenesteydelser (langfristet)
7161;G;Vekselgæld (langfristet)
7165;K;Vekselgæld (langfristet)
7171;G;Gæld til tilknyttede virksomheder (langfristet)
7175;K;Gæld til tilknyttede virksomheder (langfristet)
7181;G;Gæld til kapitalinteresser (langfristet)
7185;K;Gæld til kapitalinteresser (langfristet)
7191;G;Anden gæld, herunder skyldige skatter og skyldige bidrag til social sikring (langfristet)
7195;K;Anden gæld (langfristet)
7210;K;Gæld til virksomhedssdeltagere og ledelse (langfristet)
7230;K;Deposita (langfristet)
7240;K;Leasingforpligtelse (langfristet)
7250;K;Skyldig selskabsskat (langfristet)
7261;G;Periodeafgrænsningsposter (langfristet)
7265;K;Periodeafgrænsningsposter (langfristet)
7280;H;Kortfristede gældsforpligtelser
7281;G;Gæld, der er optaget ved udstedelse af obligationer (kortfristet)
7285;K;Gæld, der er optaget ved udstedelse af obligationer (kortfristet)
7291;G;Konvertible og udbyttegivende gældsbreve (kortfristet)
7295;K;Konvertible og udbyttegivende gældsbreve (kortfristet)
7301;G;Gæld til kreditinstitutter (kortfristet)
7310;K;Gæld til kredit- og realkreditinstitutter (kortfristet)
7330;K;Gæld til banker (kortfristet)
7345;K;Leasingforpligtelser (kortfristet)
7350;K;Øvrig kortfristet gæld
7401;G;Modtagne forudbetalinger fra kunder (kortfristet)
7410;K;Modtagne forudbetalinger fra kunder (kortfristet)
7421;G;Leverandører af varer og tjenesteydelser (kortfristet)
7440;K;Leverandører af varer og tjenesteydelser (kortfristet)
7451;G;Igangværende arbejder for fremmed regning (kortfristet gæld)
7455;K;Igangværende arbejder for fremmed regning (kortfristet gæld)
7456;K;Modtagne acontobetalinger (kortfristet gæld)
7461;G;Vekselgæld (kortfristet)
7465;K;Vekselgæld (kortfristet)
7501;G;Gæld til tilknyttede virksomheder (kortfristet)
7510;K;Gæld til tilknyttede virksomheder (kortfristet)
7531;G;Gæld til kapitalinteresser (kortfristet)
7535;K;Gæld til kapitalinteresser (kortfristet)
7581;G;Anden gæld, herunder skyldige skatter og skyldige bidrag til social sikring (kortfristet)
7590;K;Gæld til virksomhedsdeltagere og ledelse (kortfristet)
7610;K;Deposita (kortfristet)
7680;K;Salgsmoms
7700;K;Moms af varekøb udland, EU og ikke-EU
7720;K;Moms af ydelseskøb udland, EU og ikke-EU
7740;K;Købsmoms
7760;K;Olie- og flaskegasafgift
7780;K;Elafgift
7800;K;Naturgas- og bygasafgift
7810;K;Kulafgift
7820;K;Vandafgift
7830;K;Co2-afgift
7840;K;Skyldig moms
7860;K;Skyldig løn og gager
7880;K;Skyldig bonus og tantieme
7900;K;Skyldige feriepenge
7920;K;Skyldig A-skat
7940;K;Skyldigt AM-bidrag
7960;K;Skyldigt ATP-bidrag
7980;K;Skyldigt AMP-bidrag
8000;K;Anden skyldig pension
8010;K;Skyldig arbejdsgiverbidrag (samlet betaling)
8030;K;Skyldig feriepengeforpligtigelse
8035;K;Skyldigt ferietillæg
8040;K;Øvrig anden gæld
8045;K;Modtagne offentlige tilskud til senere beskatning
8051;G;Periodeafgrænsningsposter (kortfristet)
8070;K;Periodeafgrænsningsposter (kortfristet)
"""

# ─── ÅRL-linjer (årsregnskabsloven, bilag 2, skema 2 artsopdelt og balance) ───
ARL_LINES = [
    # (nøgle, navn, side)  side: "result" | "asset" | "liability"
    ("nettoomsaetning", "Nettoomsætning", "result"),
    ("lagerforandring", "Ændring i lagre af færdigvarer og varer under fremstilling", "result"),
    ("eget_arbejde", "Arbejde udført for egen regning og opført under aktiver", "result"),
    ("andre_driftsindtaegter", "Andre driftsindtægter", "result"),
    ("vareforbrug", "Omkostninger til råvarer og hjælpematerialer (vareforbrug)", "result"),
    ("andre_eksterne_omkostninger", "Andre eksterne omkostninger", "result"),
    ("personaleomkostninger", "Personaleomkostninger", "result"),
    ("af_og_nedskrivninger", "Af- og nedskrivninger af materielle og immaterielle anlægsaktiver", "result"),
    ("nedskrivning_omsaetningsaktiver", "Nedskrivning af omsætningsaktiver, som overstiger normale nedskrivninger", "result"),
    ("andre_driftsomkostninger", "Andre driftsomkostninger", "result"),
    ("indtaegter_kapitalandele", "Indtægter af kapitalandele i tilknyttede og associerede virksomheder", "result"),
    ("finansielle_indtaegter", "Finansielle indtægter", "result"),
    ("finansielle_omkostninger", "Finansielle omkostninger", "result"),
    ("skat", "Skat af årets resultat", "result"),
    ("immaterielle_anlaegsaktiver", "Immaterielle anlægsaktiver", "asset"),
    ("materielle_anlaegsaktiver", "Materielle anlægsaktiver", "asset"),
    ("finansielle_anlaegsaktiver", "Finansielle anlægsaktiver", "asset"),
    ("varebeholdninger", "Varebeholdninger", "asset"),
    ("tilgodehavender", "Tilgodehavender", "asset"),
    ("vaerdipapirer", "Værdipapirer og kapitalandele", "asset"),
    ("likvide_beholdninger", "Likvide beholdninger", "asset"),
    ("virksomhedskapital", "Virksomhedskapital", "liability"),
    ("overkurs", "Overkurs ved emission", "liability"),
    ("reserver", "Reserver", "liability"),
    ("overfoert_resultat", "Overført resultat", "liability"),
    ("foreslaaet_udbytte", "Foreslået udbytte", "liability"),
    ("hensatte_forpligtelser", "Hensatte forpligtelser", "liability"),
    ("langfristet_gaeld", "Langfristede gældsforpligtelser", "liability"),
    ("kortfristet_gaeld", "Kortfristede gældsforpligtelser", "liability"),
]
ARL_LINE_NAMES = {k: name for k, name, _ in ARL_LINES}
ARL_LINE_SIDE = {k: side for k, _, side in ARL_LINES}

# Nummerintervaller (inklusive) → (ÅRL-linje, kontotype). Kontotyperne er
# AccountType.name i seed_accounts: Asset, Liability, Equity, Revenue, Expense.
# TODO(revisor): "Dagsværdiregulering af investeringsejendomme" (3180-3190) og
# "Nedskrivning af finansielle aktiver" (3541-3560) har egne linjer i ÅRL § 38 /
# bilag 2; her er de lagt under andre driftsomkostninger og finansielle
# omkostninger. Opdel, hvis en kunde har sådanne poster.
RANGES = [
    (1000, 1399, "nettoomsaetning", "Revenue"),
    (1400, 1494, "lagerforandring", "Expense"),
    (1495, 1499, "eget_arbejde", "Revenue"),
    (1500, 1594, "andre_driftsindtaegter", "Revenue"),
    (1595, 1819, "vareforbrug", "Expense"),
    (1820, 2840, "andre_eksterne_omkostninger", "Expense"),
    (2841, 2990, "personaleomkostninger", "Expense"),
    (2991, 3119, "af_og_nedskrivninger", "Expense"),
    (3120, 3149, "nedskrivning_omsaetningsaktiver", "Expense"),
    (3150, 3190, "andre_driftsomkostninger", "Expense"),
    (3191, 3369, "indtaegter_kapitalandele", "Revenue"),
    (3370, 3540, "finansielle_indtaegter", "Revenue"),
    (3541, 3700, "finansielle_omkostninger", "Expense"),
    (3701, 4999, "skat", "Expense"),
    (5000, 5141, "immaterielle_anlaegsaktiver", "Asset"),
    (5142, 5771, "materielle_anlaegsaktiver", "Asset"),
    (5772, 6072, "finansielle_anlaegsaktiver", "Asset"),
    (6073, 6181, "varebeholdninger", "Asset"),
    (6182, 6411, "tilgodehavender", "Asset"),
    (6412, 6461, "vaerdipapirer", "Asset"),
    (6462, 6499, "likvide_beholdninger", "Asset"),
    (6500, 6530, "virksomhedskapital", "Equity"),
    (6531, 6550, "overkurs", "Equity"),
    (6551, 6930, "reserver", "Equity"),
    (6931, 6950, "overfoert_resultat", "Equity"),
    (6951, 6971, "foreslaaet_udbytte", "Equity"),
    (6972, 7051, "hensatte_forpligtelser", "Liability"),
    (7052, 7279, "langfristet_gaeld", "Liability"),
    (7280, 8999, "kortfristet_gaeld", "Liability"),
]

# Overskrifternes placering. En gruppekonto hører under den nærmeste
# hovedkonto før den, undtagen dem i GROUP_PARENT. Hovedkonti nester efter
# HEAD_PARENT.
HEAD_PARENT = {
    "1595": "1000", "1820": "1595", "2841": "1000", "3191": "1000", "3571": "1000",
    "5001": "5000", "5002": "5001", "5003": "5002", "5142": "5002", "5772": "5002",
    "6073": "5001", "6074": "6073", "6182": "6073", "6412": "6073",
    "6500": "5000", "6501": "6500", "6972": "6500", "7052": "6500", "7280": "6500",
}
GROUP_PARENT = {
    "2991": "1000", "3120": "1000", "3150": "1000", "3180": "1000",
    "3370": "1000", "3411": "1000", "3451": "1000", "3541": "1000",
    "3703": "1000", "3791": "1000", "6462": "6073",
}

# Egne konti ud over standardkontoplanen: (nummer, navn, gruppekonto, standard_code).
OWN_ACCOUNTS = [
    ("6335", "Uafklarede poster (mellemregning)", "6301", "6330"),
    ("8042", "Skyldig selskabsskat", "7581", "8040"),
]
# Navne, som er tydeligere i daglig brug end standardkontoplanens (nummeret og
# standard_code er uændret).
DISPLAY_NAMES = {
    "6470": "Kasse",
    "6480": "Bank",
    "6190": "Debitorer",
    "7440": "Kreditorer",
    "7840": "Momsafregning (skyldig moms)",
    "2390": "Porto og gebyrer (inkl. bankgebyrer)",
    "3490": "Renter og rykkergebyrer fra debitorer",
}


def parse():
    """[(nummer, type, navn)] i standardkontoplanens rækkefølge."""
    rows = []
    for line in STANDARD_TEXT.strip().splitlines():
        number, kind, name = line.split(";", 2)
        rows.append((number, kind, name))
    return rows


def classify(code):
    """(arl_line, account type name) for a standard code."""
    n = int(str(code)[:4])
    for lo, hi, arl, type_name in RANGES:
        if lo <= n <= hi:
            return arl, type_name
    raise ValueError(f"Kontonummer {code} er uden for standardkontoplanen")


def all_accounts():
    """Every account to seed: dicts with code, name, kind (H/G/K), parent,
    standard_code, arl_line, type. Parents always come before their children."""
    out = []
    last_head = None
    for number, kind, name in parse():
        arl, type_name = classify(number)
        if kind == "H":
            parent = HEAD_PARENT.get(number)
            last_head = number
        elif kind == "G":
            parent = GROUP_PARENT.get(number, last_head)
            group = number
        else:
            parent = group
        out.append({
            "code": number, "name": DISPLAY_NAMES.get(number, name), "kind": kind, "parent": parent,
            "standard_code": number if kind == "K" else "", "arl_line": arl, "type": type_name,
        })
    for number, name, group, std in OWN_ACCOUNTS:
        arl, type_name = classify(std)
        out.append({"code": number, "name": name, "kind": "K", "parent": group,
                    "standard_code": std, "arl_line": arl, "type": type_name})
    return out


# ─── Skabeloner: hvilke konti er aktive fra start ───
_COMMON = {
    # Nettoomsætning og andre driftsindtægter
    "1010", "1050", "1100", "1150", "1200", "1210", "1545", "1550",
    # Vareforbrug
    "1610", "1630", "1650", "1660", "1710", "1740", "1760",
    # Salgsomkostninger
    "1850", "1910", "1930", "1990", "2000",
    # Lokaleomkostninger (inkl. energiafgifter)
    "2030", "2050", "2060", "2070", "2080", "2090", "2100", "2120", "2150", "2160", "2180", "2200",
    # Administration
    "2230", "2240", "2280", "2310", "2370", "2380", "2390", "2410", "2450", "2460", "2470", "2480",
    "2510", "2540", "2560", "2569", "2620", "2650", "2660", "2670", "2680", "2690", "2720", "2810",
    # Personale (bruges af lønmodulet, se chart.DK_*)
    "2845", "2846", "2847", "2860", "2865", "2866", "2885", "2887", "2888", "2895", "2896",
    "2897", "2898", "2910", "2930", "2947",
    # Afskrivninger og andre driftsomkostninger
    "3050", "3060", "3165", "3170",
    # Finansielle poster
    "3470", "3490", "3510", "3530", "3535", "3610", "3630", "3650", "3670", "3675", "3690",
    # Materielle anlægsaktiver: driftsmateriel og inventar
    "5570", "5580", "5590", "5602", "5610",
    # Tilgodehavender og likvider
    "6040", "6140", "6190", "6200", "6201", "6320", "6330", "6335", "6390", "6470", "6480",
    # Gæld
    "7110", "7120", "7330", "7410", "7440", "7590", "7610",
    "7680", "7700", "7720", "7740", "7760", "7780", "7800", "7810", "7820", "7830", "7840",
    "7860", "7900", "7920", "7940", "7960", "7980", "8000", "8010", "8030", "8035", "8040", "8070",
}
_COMPANY = {
    # Selskaber (ApS/A/S): kapital, overført resultat, udbytte og selskabsskat
    "6510", "6935", "6940", "6955", "6956", "6960", "7010", "3740", "3760", "3780",
    "6315", "8042", "6365", "7210",
}
_HOLDING = {
    # Kapitalandele og udbytte fra datterselskaber
    "3193", "3194", "3196", "3197", "3211", "3252", "3262",
    "5800", "5810", "5820", "5835", "5836", "5842", "5852", "5862", "6000", "6252", "7510",
    "3440", "3590",
}
_SOLE_TRADER = {
    # Enkeltmandsvirksomhed (klasse A): egenkapital og private andele
    "6915", "6916", "6917", "6918", "6919", "6920", "6921", "6922", "6923", "6924",
    "2085", "2430", "2550", "2580", "1807", "3095",
}
# Holding har typisk ingen varer eller personale, men kontiene beholdes aktive
# for lønmodulet (DK_*), som skal kunne finde dem.
TEMPLATES = {
    "standard": _COMMON | _COMPANY,
    "holding": _COMMON | _COMPANY | _HOLDING,
    "enkeltmand": _COMMON | _SOLE_TRADER,
}
TEMPLATE_NAMES = {
    "standard": "Selskab (ApS/A/S), standard",
    "holding": "Holdingselskab",
    "enkeltmand": "Enkeltmandsvirksomhed",
}


def active_codes(template):
    if template not in TEMPLATES:
        raise ValueError(f"Ukendt kontoplanskabelon: {template} (vælg {', '.join(TEMPLATES)})")
    return TEMPLATES[template]

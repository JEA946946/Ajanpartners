# Kundeaccept og uafhængighed – kildegrundlag

Kontrolleret 17. november 2026 mod de officielle PDF'er på retsinformation.dk. Tjeklisterne ligger i `backend/firm/checklists/acceptance.json` og `independence.json`.

## Kilder

| Kort | Kilde | Status 17/11 2026 |
|---|---|---|
| RL | Revisorloven, LBK nr. 206 af 20/02/2025 – https://www.retsinformation.dk/eli/lta/2025/206 | Senere ændret ved lov nr. 729 af 01/09/2026 (bl.a. nedlæggelse af Revisorrådet). Ændringen er **ikke** gennemgået; de anvendte §§ 16, 18, 24 og 26 er læst i LBK 206. |
| BEK 520 | BEK nr. 520 af 24/05/2024 om godkendte revisorers og revisionsvirksomheders uafhængighed – https://www.retsinformation.dk/eli/lta/2024/520 | Gældende (udskrift 17/11 2026) |
| BEK 512 | BEK nr. 512 af 24/05/2024 om godkendte revisionsvirksomheders interne organisation – https://www.retsinformation.dk/eli/lta/2024/512 | Gældende (udskrift 17/11 2026) |
| HVL | Hvidvaskloven – se `opdrag-hvidvask.md` | – |

## Kundeaccept (`acceptance.json`)

| Spørgsmål | Hjemmel | Bemærkning |
|---|---|---|
| Politikker for accept og fortsættelse | BEK 512 § 3, stk. 1, nr. 4 | Bekendtgørelsen kræver politikker og procedurer, men fastsætter ikke spørgsmålene. Spørgsmålene nedenfor er afgrænset til krav, der står direkte i RL/BEK. |
| Kundekendskab før etablering | HVL § 14, stk. 1 | Systemet kræver godkendt KYC før accept. |
| Trusler, der altid udelukker opgaven | BEK 520 § 2, stk. 1-3 | § 2, stk. 2: altid så betydelige, at revisor skal afstå → blokerer accept. |
| Øvrige trusler (selvrevision, partsrepræsentation, andre familiebånd) | BEK 520 § 7; RL § 24, stk. 3 og 5 | Kræver dokumentation af trusler og sikkerhedsforanstaltninger (RL § 24, stk. 5). |
| Henvendelse til fratrædende revisor | RL § 18, stk. 2 | "Ikke relevant" tilladt. |
| Kompetencer og ressourcer | BEK 512 § 3, stk. 1, nr. 6; RL § 16, stk. 1 | |
| God revisorskik, integritet, objektivitet, skepsis | RL § 16, stk. 1-2 | |
| Vederlag | RL § 26, stk. 1 | |

## Uafhængighedserklæring (`independence.json`)

| Spørgsmål | Hjemmel |
|---|---|
| Ledelsesfunktion hos kunden inden for 2 år | BEK 520 § 2, stk. 1, nr. 1 |
| Økonomisk interesse / finansielle instrumenter / tilknyttet virksomhed | BEK 520 § 2, stk. 1, nr. 2-3 |
| Gaver og fordele ud over ubetydelig værdi | BEK 520 § 2, stk. 1, nr. 4 |
| Forretningsforbindelse med fælles kommerciel interesse | BEK 520 § 2, stk. 1, nr. 5 |
| Tætte familiemæssige bånd (definition i stk. 3) | BEK 520 § 2, stk. 1, nr. 6, og stk. 3 |
| Partsrepræsentation i tvister inden for 2 år | BEK 520 § 7, stk. 1, nr. 2 |
| Andre familiemæssige bånd | BEK 520 § 7, stk. 1, nr. 3 |
| Bekræftelse af kendskab til husets politikker | BEK 512 § 1, stk. 4; § 2, stk. 1, nr. 2 |

## Systemregler afledt af kilderne

- Et registreret forhold fjerner straks medarbejderen fra kunden (BEK 520 § 3, stk. 3; § 4, stk. 2) og spærrer ny tildeling, indtil en partner har afklaret det.
- Afklaringen "sikkerhedsforanstaltninger" er kun mulig for øvrige trusler (§ 7). Trusler efter § 2 kan ikke afhjælpes med sikkerhedsforanstaltninger (§ 2, stk. 2); økonomiske interesser skal afhændes senest én måned efter kendskab (§ 4).
- Netværksreglen (BEK 520 § 8) og reglerne for virksomheder af interesse for offentligheden (§§ 5-6, RL §§ 24 a-25) er ikke indarbejdet og skal vurderes særskilt, hvis huset har netværkssamarbejde eller sådanne kunder.

## Ikke afklaret – til fagperson

- Om lov nr. 729/2026 ændrer de anvendte paragraffer i revisorloven.
- FSR's/IESBA's etiske regler (ud over BEK 520) er ikke gennemgået og er ikke indarbejdet.
- Spørgsmålene er et minimum efter lov og bekendtgørelse – husets egne kvalitetspolitikker (ISQM 1) kan kræve flere.

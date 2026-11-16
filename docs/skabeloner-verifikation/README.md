# Verifikation af skabeloner

Hver skabelon i `backend/firm/doc_templates/` er gennemgået påstand for påstand (satser, beløbsgrænser, frister,
paragrafhenvisninger, lov- og bekendtgørelsesnumre, standardhenvisninger og faglige udsagn).

Regler for gennemgangen:
1. En påstand er **bekræftet**, når den er fundet i en primær kilde (retsinformation.dk, skat.dk / Den juridiske
   vejledning, erhvervsstyrelsen.dk, FSR – danske revisorer, Finanstilsynet, Datatilsynet) – og om muligt krydstjekket
   mod en publikation fra et større revisions- eller advokatfirma.
2. En påstand, der ikke kan bekræftes, **fjernes** eller erstattes af et felt, revisor selv udfylder. Intet gættes.
3. En påstand, der er forkert, **rettes** med kildehenvisning.

Én fil pr. kategori. Kolonner: skabelon · påstand · status (bekræftet / rettet / fjernet / felt) · kilde (URL).

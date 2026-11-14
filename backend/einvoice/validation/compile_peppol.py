"""Kompilér Peppol BIS 3.0-schematron (.sch) til XSLT med ISO-skeleton'en i iso/.

    python einvoice/validation/compile_peppol.py
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def compile_schematron(src, out):
    from saxonche import PySaxonProcessor

    with PySaxonProcessor(license=False) as proc:
        xslt = proc.new_xslt30_processor()
        step = str(src)
        for i, name in enumerate(("iso_dsdl_include.xsl", "iso_abstract_expand.xsl", "iso_svrl_for_xslt2.xsl")):
            target = str(out) if i == 2 else f"{out}.step{i}.xml"
            xslt.compile_stylesheet(stylesheet_file=str(HERE / "iso" / name)).transform_to_file(
                source_file=step, output_file=target)
            step = target
    for i in range(2):
        Path(f"{out}.step{i}.xml").unlink(missing_ok=True)


if __name__ == "__main__":
    compile_schematron(HERE / "peppol" / "PEPPOL-EN16931-UBL.sch", HERE / "peppol" / "PEPPOL-EN16931-UBL.xslt")
    print("peppol/PEPPOL-EN16931-UBL.xslt opdateret")

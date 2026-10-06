"""Build a Word (.docx) security report from a findings JSON file.

Standard library only (no python-docx), so it runs on any machine with Python 3.8+.

Usage:
    python .claude/scripts/security_report_docx.py findings.json security-reports/report.docx

Input JSON shape (only "findings" is required):
{
  "title": "Security Scan Report",
  "project": "Demo Bank IT PMO Kanban",
  "date": "2026-10-06",
  "scope": {"commit": "c7d8e10", "branch": "main", "files": ["index.html", "v2/index.html"]},
  "executive_summary": "One or two paragraphs.",
  "methodology": ["Static review of ...", "Headless Chrome XSS probe ..."],
  "findings": [{
    "id": "SEC-001", "title": "...", "severity": "Critical|High|Medium|Low|Info",
    "category": "OWASP A03:2021 Injection", "cwe": "CWE-79", "boundary": "B1",
    "location": "v2/index.html:812", "description": "...", "impact": "...",
    "evidence": "code or command output", "recommendation": "...",
    "fix_snippet": "suggested code", "effort": "Low|Medium|High", "status": "Open"
  }],
  "controls_ok": ["escapeHtml() applied to every interpolation", "..."],
  "residual_risk": "Paragraph.",
  "roadmap": [{"priority": "Now", "action": "...", "findings": "SEC-001, SEC-003"}]
}
"""

import datetime
import json
import re
import sys
import zipfile
from xml.sax.saxutils import escape

SEVERITIES = ["Critical", "High", "Medium", "Low", "Info"]
SEV_COLOR = {"Critical": "7B1E1E", "High": "C0392B", "Medium": "D35400", "Low": "2471A3", "Info": "5D6D7E"}
SEV_TINT = {"Critical": "F2D7D5", "High": "FADBD8", "Medium": "FDEBD0", "Low": "D6EAF8", "Info": "EAEDED"}
ACCENT = "1F3A5F"
_INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def x(text):
    return escape(_INVALID_XML.sub("", str(text)), {'"': "&quot;"})


# ---------- run / paragraph / table builders ----------

def run(text, bold=False, italic=False, color=None, size=None, mono=False):
    props = ""
    if mono:
        props += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
    if bold:
        props += "<w:b/>"
    if italic:
        props += "<w:i/>"
    if color:
        props += f'<w:color w:val="{color}"/>'
    if size:
        props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    parts = str(text).split("\n")
    body = '<w:br/>'.join(f'<w:t xml:space="preserve">{x(p)}</w:t>' for p in parts)
    return f"<w:r><w:rPr>{props}</w:rPr>{body}</w:r>"


def para(content="", style=None, align=None, shade=None, keep_next=False, space_after=None):
    """content is run XML (build it with run()), not plain text."""
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += "<w:keepNext/>"
    if shade:
        ppr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    if space_after is not None:
        ppr += f'<w:spacing w:after="{space_after}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{content}</w:p>"


def heading(text, level):
    return para(run(text), style=f"Heading{level}", keep_next=True)


def bullet(text):
    return para(run(text), style="ListBullet")


def code_block(text):
    lines = str(text).rstrip("\n").split("\n")
    return "".join(para(run(line or " ", mono=True, size=17), style="Code") for line in lines)


def cell(content, width, fill=None, bold=False, color=None, header=False):
    if isinstance(content, str) or content is None:
        content = para(run(content or "", bold=bold or header, color=color or ("FFFFFF" if header else None)), space_after=0)
    tcpr = f'<w:tcW w:w="{width}" w:type="dxa"/>'
    if header:
        fill = fill or ACCENT
    if fill:
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
    return f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{content}</w:tc>"


def table(rows, widths, header=True):
    border = "".join(
        f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="BFC5CC"/>'
        for side in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [
        f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
        f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
        f'<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        f"<w:tblGrid>{grid}</w:tblGrid>"
    ]
    for i, row in enumerate(rows):
        is_header = header and i == 0
        trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if is_header else "<w:trPr><w:cantSplit/></w:trPr>"
        cells = []
        for c, w in zip(row, widths):
            if isinstance(c, dict):
                cells.append(cell(c.get("text"), w, fill=c.get("fill"), bold=c.get("bold", False), color=c.get("color"), header=is_header))
            else:
                cells.append(cell(c, w, header=is_header))
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out) + para("", space_after=0)


def sev_cell(sev):
    return {"text": sev, "fill": SEV_COLOR.get(sev, "5D6D7E"), "color": "FFFFFF", "bold": True}


# ---------- document body ----------

def normalise(data):
    findings = data.get("findings") or []
    for i, f in enumerate(findings, 1):
        sev = str(f.get("severity", "Info")).strip().capitalize()
        if sev == "Informational":
            sev = "Info"
        if sev not in SEVERITIES:
            raise SystemExit(f"Finding {f.get('id', i)}: severity '{f.get('severity')}' is not one of {SEVERITIES}")
        f["severity"] = sev
        f.setdefault("id", f"SEC-{i:03d}")
        f.setdefault("status", "Open")
    findings.sort(key=lambda f: (SEVERITIES.index(f["severity"]), f["id"]))
    data["findings"] = findings
    return data


def build_body(d):
    findings = d["findings"]
    scope = d.get("scope") or {}
    date = d.get("date") or datetime.date.today().isoformat()
    b = []

    # Cover
    b.append(para(run(d.get("title", "Security Scan Report"), bold=True, color=ACCENT, size=48), space_after=120))
    b.append(para(run(d.get("project", ""), size=28, color="5D6D7E"), space_after=240))
    meta = [["Field", "Value"], ["Report date", date]]
    if scope.get("branch"):
        meta.append(["Branch", scope["branch"]])
    if scope.get("commit"):
        meta.append(["Commit", scope["commit"]])
    if scope.get("files"):
        meta.append(["Files in scope", ", ".join(scope["files"])])
    meta.append(["Total findings", str(len(findings))])
    meta.append(["Classification", "Internal: contains unfixed vulnerability details"])
    b.append(table(meta, [2400, 6626]))

    # Executive summary
    b.append(heading("1. Executive summary", 1))
    for p in str(d.get("executive_summary", "")).split("\n\n"):
        if p.strip():
            b.append(para(run(p.strip())))
    counts = [["Severity", "Count", "Meaning"]]
    meaning = {
        "Critical": "Exploitable now with serious impact. Fix before the next deploy.",
        "High": "Likely exploitable or high impact. Fix this sprint.",
        "Medium": "Needs specific conditions or has limited impact. Plan a fix.",
        "Low": "Hardening gap or defence-in-depth improvement.",
        "Info": "Observation or good-practice note. No direct risk.",
    }
    for s in SEVERITIES:
        n = sum(1 for f in findings if f["severity"] == s)
        counts.append([sev_cell(s), {"text": str(n), "bold": True}, meaning[s]])
    b.append(table(counts, [1600, 1000, 6426]))

    # Methodology
    if d.get("methodology"):
        b.append(heading("2. Scope and methodology", 1))
        for m in d["methodology"]:
            b.append(bullet(m))

    # Findings overview
    b.append(heading("3. Findings overview", 1))
    if findings:
        rows = [["ID", "Severity", "Title", "Category", "Location"]]
        for f in findings:
            rows.append([f["id"], sev_cell(f["severity"]), f.get("title", ""),
                         " / ".join(v for v in (f.get("category"), f.get("cwe")) if v), f.get("location", "")])
        b.append(table(rows, [1000, 1150, 2900, 2176, 1800]))
    else:
        b.append(para(run("No vulnerabilities were found in scope.")))

    # Detailed findings
    b.append(heading("4. Detailed findings and recommended fixes", 1))
    for f in findings:
        b.append(heading(f"{f['id']}: {f.get('title', '')}", 2))
        info = [
            ["Severity", sev_cell(f["severity"])],
            ["Category", f.get("category", "")],
            ["CWE", f.get("cwe", "")],
            ["Trust boundary", f.get("boundary", "")],
            ["Location", f.get("location", "")],
            ["Fix effort", f.get("effort", "")],
            ["Status", f.get("status", "Open")],
        ]
        info = [[{"text": k, "bold": True, "fill": SEV_TINT[f["severity"]]}, v] for k, v in info if (v if isinstance(v, str) else True)]
        b.append(table(info, [2200, 6826], header=False))
        for label, key in (("Description", "description"), ("Impact", "impact")):
            if f.get(key):
                b.append(heading(label, 3))
                b.append(para(run(f[key])))
        if f.get("evidence"):
            b.append(heading("Evidence", 3))
            b.append(code_block(f["evidence"]))
        if f.get("recommendation"):
            b.append(heading("Recommended fix", 3))
            b.append(para(run(f["recommendation"])))
        if f.get("fix_snippet"):
            b.append(code_block(f["fix_snippet"]))

    # Controls OK
    if d.get("controls_ok"):
        b.append(heading("5. Controls verified as working", 1))
        for c in d["controls_ok"]:
            b.append(bullet(c))

    # Roadmap
    if d.get("roadmap"):
        b.append(heading("6. Remediation roadmap", 1))
        rows = [["Priority", "Action", "Findings"]]
        for r in d["roadmap"]:
            rows.append([{"text": r.get("priority", ""), "bold": True}, r.get("action", ""), r.get("findings", "")])
        b.append(table(rows, [1500, 5726, 1800]))

    if d.get("residual_risk"):
        b.append(heading("7. Residual risk", 1))
        b.append(para(run(d["residual_risk"])))

    return "".join(b)


# ---------- package parts ----------

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


def document_xml(body):
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1300" w:right="1440" w:bottom="1300" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
            '</w:sectPr>')
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}{sect}</w:body></w:document>'


def footer_xml(title):
    fld = lambda instr: (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                         f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}>'
            f'<w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>'
            f'{run(title + "  |  Internal  |  Page ", color="7F8C8D", size=16)}{fld("PAGE")}'
            f'{run(" of ", color="7F8C8D", size=16)}{fld("NUMPAGES")}</w:p></w:ftr>')


STYLES = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-GB"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="{ACCENT}"/></w:pBdr><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr><w:b/><w:color w:val="{ACCENT}"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr><w:b/><w:color w:val="{ACCENT}"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="160" w:after="60"/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr><w:b/><w:color w:val="34495E"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/>
<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:spacing w:after="60"/><w:ind w:left="360" w:hanging="360"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/>
<w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F4F6F7"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="120" w:right="120"/></w:pPr>
<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/></w:style>
<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>
<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>
</w:styles>'''

NUMBERING = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>
<w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'''

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdNumbering" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>'''


def core_xml(title):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{x(title)}</dc:title><dc:creator>security-scanner agent</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')


APP_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>security_report_docx.py</Application></Properties>')


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dest = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        data = normalise(json.load(fh))
    title = data.get("title", "Security Scan Report")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/document.xml", document_xml(build_body(data)))
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/numbering.xml", NUMBERING)
        z.writestr("word/footer1.xml", footer_xml(title))
        z.writestr("docProps/core.xml", core_xml(title))
        z.writestr("docProps/app.xml", APP_XML)
    counts = {s: sum(1 for f in data["findings"] if f["severity"] == s) for s in SEVERITIES}
    print(f"Wrote {dest}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()

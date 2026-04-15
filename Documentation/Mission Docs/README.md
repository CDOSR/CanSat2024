# Mission Documents — PDR & CDR

LaTeX source for the 2024 CanSat Preliminary Design Report (PDR) and Critical Design Report (CDR), plus the compiled PDFs.

## Layout

```
Mission Docs/
├── PDR/
│   ├── CanSat_2024_PDR_CDOSR.pdf        (latest compiled)
│   └── src/
│       ├── CanSat_2024_PDR_CDOSR.tex    (main file — compile this)
│       ├── CDOSR_CanSat.sty
│       ├── hyperendnotes.sty
│       └── section_1/ .. section_7/
├── CDR/
│   ├── CanSat_2024_CDR_CDOSR.pdf        (latest compiled)
│   └── src/
│       ├── CanSat_2024_CDR_CDOSR.tex    (main file — compile this)
│       ├── CDOSR_CanSat.sty
│       ├── hyperendnotes.sty
│       └── section_0/ .. section_7/
├── common/
│   ├── icons/                           (shared iconography)
│   └── images/                          (shared figures; both .eps and .pdf)
└── Presentations/
```

Shared images live in `common/` and are reached from each `src/` via
`\graphicspath{{../../common/}{./}}` in the main `.tex` file.

## Building

Requires a recent LaTeX distribution (MiKTeX 23+, TeX Live 2023+, or TinyTeX) with the usual packages: `enumitem`, `fancyhdr`, `hyperref`, `pdflscape`, `amssymb`, `array`, `wrapfig`, `endnotes`, plus everything `CDOSR_CanSat.sty` pulls in.

### PDR

```bash
cd "Documentation/Mission Docs/PDR/src"
pdflatex CanSat_2024_PDR_CDOSR.tex
pdflatex CanSat_2024_PDR_CDOSR.tex    # second pass for TOC and cross-refs
```

### CDR

```bash
cd "Documentation/Mission Docs/CDR/src"
pdflatex CanSat_2024_CDR_CDOSR.tex
pdflatex CanSat_2024_CDR_CDOSR.tex    # second pass for TOC and cross-refs
```

The compiled `.pdf` is written alongside the `.tex` in `src/`. LaTeX build artifacts (`.aux`, `.log`, `.toc`, etc.) and stray PDFs inside `src/` are gitignored — the deliverable PDFs at `PDR/CanSat_2024_PDR_CDOSR.pdf` and `CDR/CanSat_2024_CDR_CDOSR.pdf` are kept tracked.

## Notes

- **EPS figures are pre-converted.** Every `.eps` in `common/images/` has a sibling `.pdf`, and `\includegraphics` calls drop the `.eps` extension so pdflatex auto-picks the `.pdf`. This sidesteps MiKTeX's `epstopdf` restricted-mode failure when images sit across a `..` directory hop. If you add a new `.eps`, run `epstopdf <file>.eps` in `common/images/` to generate the matching `.pdf` before committing.
- **Shared `.sty` files** (`CDOSR_CanSat.sty`, `hyperendnotes.sty`) are duplicated in each `src/` because LaTeX package resolution does not follow `\graphicspath`. If you edit one, sync the other by hand.
- **Team roster** inclusion is controlled in `section_1/subsection_1_2.tex` — comment or uncomment `\input{section_1/team_members/...}` lines to add/remove members.

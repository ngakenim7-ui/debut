"""Construit ebook/Ebook_Data_Scientist_Evaluateur.{html,pdf} à partir des chapitres Markdown.

Dépendances : pandoc (binaire), matplotlib (rendu des formules), weasyprint (PDF).
Usage : python ebook/outils/construire_pdf.py
"""
from __future__ import annotations

import base64
import html as html_lib
import hashlib
import io
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RACINE = Path(__file__).resolve().parents[1]
CHAP = RACINE / "chapitres"
SORTIE_HTML = RACINE / "Ebook_Data_Scientist_Evaluateur.html"
SORTIE_PDF = RACINE / "Ebook_Data_Scientist_Evaluateur.pdf"

plt.rcParams["mathtext.fontset"] = "dejavuserif"


def _adapter_mathtext(tex: str) -> str:
    """Adapte quelques commandes LaTeX à mathtext (sous-ensemble de LaTeX de Matplotlib)."""
    tex = tex.replace(r"\dfrac", r"\frac")
    tex = re.sub(r"\\text\{([^}]*)\}", lambda m: r"\mathrm{" + m.group(1).replace(" ", r"\ ") + "}", tex)
    tex = tex.replace(r"\,", r"\ ").replace(r"\ne ", r"\neq ")
    tex = re.sub(r"\\sqrt\s+(\w)", r"\\sqrt{\1}", tex)
    return tex


_cache: dict[str, str] = {}


def formule_en_svg(tex: str, bloc: bool) -> str:
    cle = hashlib.md5(f"{bloc}{tex}".encode()).hexdigest()
    if cle in _cache:
        return _cache[cle]
    taille = 13 if bloc else 10.5
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${_adapter_mathtext(tex)}$", fontsize=taille)
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02, transparent=True)
    except ValueError as e:
        plt.close(fig)
        print("   [formule non rendue, affichée en texte]", tex, "|", str(e).strip().splitlines()[-1])
        return f"<code>{tex}</code>"
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()
    classe = "math-bloc" if bloc else "math-ligne"
    alt = html_lib.escape(tex, quote=True)
    html = f'<img class="{classe}" alt="{alt}" src="data:image/svg+xml;base64,{b64}"/>'
    _cache[cle] = html
    return html


def remplacer_maths(md: str) -> str:
    # Ne pas toucher aux blocs de code
    morceaux = re.split(r"(```.*?```|`[^`\n]*`)", md, flags=re.S)
    for i in range(0, len(morceaux), 2):
        m = morceaux[i]
        m = re.sub(r"\$\$(.+?)\$\$", lambda x: "\n\n" + f'<div class="math-bloc">{formule_en_svg(x.group(1).strip(), True)}</div>' + "\n\n", m, flags=re.S)
        m = re.sub(r"(?<![\\$])\$([^$\n]+?)\$", lambda x: formule_en_svg(x.group(1), False), m)
        morceaux[i] = m
    return "".join(morceaux)


def images_en_base64(html: str) -> str:
    def rempl(m):
        chemin = (CHAP / m.group(1)).resolve()
        data = base64.b64encode(chemin.read_bytes()).decode()
        return f'src="data:image/png;base64,{data}"'
    return re.sub(r'src="(\.\./sorties/figures/[^"]+\.png)"', rempl, html)


CSS = """
@page { size: A4; margin: 2cm 1.8cm 2.2cm 1.8cm;
        @bottom-center { content: counter(page); font-size: 9pt; color: #666; } }
@page :first { @bottom-center { content: none; } }
:root { --texte: #1d1d1f; --secondaire: #5a5a5f; --accent: #1f5fae; --fond-code: #f5f6f8; --bord: #dfe1e5; }
body { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.5pt; line-height: 1.5; color: var(--texte);
       background: #fff; max-width: 860px; margin: 0 auto; padding: 0 16px; }
h1 { font-family: "DejaVu Sans", sans-serif; color: var(--accent); font-size: 21pt; margin-top: 0;
     page-break-before: always; border-bottom: 2px solid var(--accent); padding-bottom: 6px; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-family: "DejaVu Sans", sans-serif; font-size: 14pt; margin-top: 1.4em; color: var(--texte); }
h3 { font-family: "DejaVu Sans", sans-serif; font-size: 11.5pt; margin-top: 1.2em; color: var(--secondaire); }
h2, h3 { page-break-after: avoid; }
p, li { text-align: justify; hyphens: auto; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.6pt; background: var(--fond-code);
       padding: 0 3px; border-radius: 3px; }
pre { background: var(--fond-code); border: 1px solid var(--bord); border-left: 3px solid var(--accent);
      padding: 8px 10px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.3pt; line-height: 1.35; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9pt; page-break-inside: avoid; }
th { background: #eaf0f8; text-align: left; }
th, td { border: 1px solid var(--bord); padding: 4px 6px; vertical-align: top; text-align: left !important; }
td { hyphens: auto; }
blockquote { margin: 1em 0; padding: 6px 12px; background: #fbf7ec; border-left: 4px solid #e0a800;
             color: var(--texte); page-break-inside: avoid; }
img { max-width: 100%; }
figure img { display: block; margin: 0.6em auto; }
figure { margin: 0.8em 0; text-align: center; page-break-inside: avoid; }
figcaption { font-size: 9pt; color: var(--secondaire); }
img.math-ligne { vertical-align: middle; margin: 0 1px; display: inline; }
div.math-bloc { text-align: center; margin: 0.8em 0; }
div.math-bloc img { display: inline; }
hr { border: none; border-top: 1px solid var(--bord); margin: 1.5em 0; }
nav#TOC { page-break-after: always; }
nav#TOC ul { list-style: none; padding-left: 1em; }
nav#TOC > ul > li { margin-top: 4px; font-weight: bold; }
nav#TOC > ul > li > ul { font-weight: normal; font-size: 9.5pt; }
nav#TOC a { color: var(--texte); text-decoration: none; }
.couverture { text-align: center; padding-top: 5cm; page-break-after: always; }
.couverture h1 { border: none; font-size: 30pt; page-break-before: avoid; }
.couverture p { text-align: center; color: var(--secondaire); font-size: 13pt; }
"""


def main() -> None:
    fichiers = sorted(CHAP.glob("*.md"))
    md = "\n\n".join(f.read_text(encoding="utf-8") for f in fichiers)
    # La préface commence par le titre du livre : on le transforme en couverture
    md = md.replace(
        "# Le Data Scientist Évaluateur\n\n## Raisonner, vérifier et critiquer : statistiques, code, modèles et réponses d'IA\n\n*Un manuel pratique avec jeux de données, projets guidés et exercices corrigés.*\n\n---\n",
        '<div class="couverture"><h1 class="unnumbered">Le Data Scientist Évaluateur</h1>'
        "<p>Raisonner, vérifier et critiquer :<br/>statistiques, code, modèles et réponses d'IA</p>"
        "<p><em>Manuel pratique avec jeux de données, projets guidés et exercices corrigés</em></p></div>\n",
    )
    md = remplacer_maths(md)
    html = subprocess.run(
        ["pandoc", "-f", "markdown-tex_math_dollars-tex_math_single_backslash-task_lists", "-t", "html5", "--toc", "--toc-depth=2",
         "--standalone", "--metadata", "title=Le Data Scientist Évaluateur", "--metadata", "lang=fr",
         "--syntax-highlighting=none"],
        input=md, capture_output=True, text=True, check=False,
    )
    if html.returncode != 0:  # anciennes versions de pandoc : --no-highlight
        html = subprocess.run(
            ["pandoc", "-f", "markdown-tex_math_dollars-tex_math_single_backslash-task_lists", "-t", "html5", "--toc", "--toc-depth=2",
             "--standalone", "--metadata", "title=Le Data Scientist Évaluateur", "--metadata", "lang=fr", "--no-highlight"],
            input=md, capture_output=True, text=True, check=True,
        )
    page = html.stdout
    page = re.sub(r"<style>.*?</style>", f"<style>{CSS}</style>", page, flags=re.S)
    page = re.sub(r'<header id="title-block-header">.*?</header>', "", page, flags=re.S)
    # Placer la table des matières après la couverture
    toc = re.search(r'<nav id="TOC".*?</nav>', page, flags=re.S)
    if toc:
        page = page.replace(toc.group(0), "")
        page = page.replace("</div>\n", "</div>\n" + '<h2 class="unnumbered">Table des matières</h2>' + toc.group(0), 1)
    page = re.sub(r"<colgroup>.*?</colgroup>", "", page, flags=re.S)  # largeurs de colonnes automatiques
    page = images_en_base64(page)
    SORTIE_HTML.write_text(page, encoding="utf-8")
    print("HTML ->", SORTIE_HTML)
    from weasyprint import HTML
    HTML(string=page, base_url=str(CHAP)).write_pdf(SORTIE_PDF)
    print("PDF  ->", SORTIE_PDF)


if __name__ == "__main__":
    main()

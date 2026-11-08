"""Génère le PDF du cours à partir des chapitres Markdown.

Usage (depuis la racine du dépôt) :
    pip install markdown pygments pypdf playwright
    playwright install chromium            # une seule fois
    python cours-git/outils/generer_pdf.py

Produit :
    cours-git/cours-git.html   (version web, imprimable avec Ctrl+P si besoin)
    cours-git/cours-git.pdf    (avec les exemples zippés en pièce jointe)

Variable d'environnement optionnelle : CHROMIUM_PATH (chemin d'un Chromium déjà installé).
"""

from __future__ import annotations

import datetime as dt
import html
import io
import os
import re
import sys
import zipfile
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode
from pygments.formatters import HtmlFormatter

COURS = Path(__file__).resolve().parent.parent
EXEMPLES = COURS / "exemples"
SORTIE_HTML = COURS / "cours-git.html"
SORTIE_PDF = COURS / "cours-git.pdf"

CHAPITRES = [
    ("README.md", "Introduction"),
    ("01-git.md", "Git"),
    ("02-git-bash.md", "Git Bash"),
    ("03-github.md", "GitHub"),
    ("04-github-desktop.md", "GitHub Desktop"),
    ("05-github-actions.md", "GitHub Actions"),
    ("06-gitlab.md", "GitLab"),
    ("07-gitlab-ci-cd.md", "GitLab CI/CD"),
    ("08-gitkraken.md", "GitKraken"),
    ("09-tp-final.md", "TP final"),
]

# Fichiers d'exemple reproduits en annexe : (chemin relatif à exemples/, langage pygments)
ANNEXES = [
    ("projet-demo/pyproject.toml", "toml"),
    ("projet-demo/requirements-dev.txt", "text"),
    ("projet-demo/src/demo/__init__.py", "python"),
    ("projet-demo/src/demo/stats.py", "python"),
    ("projet-demo/tests/test_stats.py", "python"),
    ("github-actions/ci.yml", "yaml"),
    ("github-actions/rapport-hebdo.yml", "yaml"),
    ("gitlab-ci/.gitlab-ci.yml", "yaml"),
    ("gitignore-data-science", "text"),
]

PREFIXES = {nom: f"c{i}" for i, (nom, _) in enumerate(CHAPITRES)}


def id_annexe(chemin: str) -> str:
    return "annexe-" + re.sub(r"[^a-z0-9]+", "-", chemin.lower()).strip("-")


def reecrire_liens(html_chap: str, prefixe: str) -> str:
    """Préfixe les id du chapitre et transforme les liens .md / exemples/ en ancres internes."""
    html_chap = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefixe}-{m.group(1)}"', html_chap)

    def lien(m: re.Match) -> str:
        cible = html.unescape(m.group(1))
        if cible.startswith(("http://", "https://", "mailto:")):
            return m.group(0)
        chemin, _, ancre = cible.partition("#")
        if not chemin:  # ancre dans le même chapitre
            return f'href="#{prefixe}-{ancre}"'
        nom = Path(chemin).name
        if nom in PREFIXES:
            p = PREFIXES[nom]
            return f'href="#{p}-{ancre}"' if ancre else f'href="#{p}"'
        if chemin.startswith("exemples/"):
            rel = chemin.removeprefix("exemples/").rstrip("/")
            if rel == "projet-demo":
                rel = "projet-demo/src/demo/stats.py"
            return f'href="#{id_annexe(rel)}"'
        return m.group(0)

    return re.sub(r'href="([^"]+)"', lien, html_chap)


def retirer_encart_pdf(texte: str) -> str:
    """Retire l'encart « Version PDF » du README : dans le PDF lui-même, il n'a pas de sens."""
    lignes, sortie, dans_encart = texte.split("\n"), [], False
    for ligne in lignes:
        if ligne.startswith("> 📄"):
            dans_encart = True
        elif dans_encart and not ligne.startswith(">"):
            dans_encart = False
        if not dans_encart:
            sortie.append(ligne)
    return "\n".join(sortie)


def convertir(md_texte: str) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "highlight"},
            "toc": {"slugify": slugify_unicode},
        },
    )
    return md.convert(md_texte)


def bloc_code(code: str, langage: str) -> str:
    return convertir(f"```{langage}\n{code.rstrip()}\n```")


def construire_html() -> str:
    corps = []
    sommaire = []
    for i, (nom, court) in enumerate(CHAPITRES):
        texte = (COURS / nom).read_text(encoding="utf-8")
        # Les liens "➡️ Suite" / "⬅️ Retour" n'ont pas de sens dans un PDF linéaire.
        texte = re.sub(r"^(➡️|⬅️) .*$", "", texte, flags=re.MULTILINE)
        if nom == "README.md":
            texte = texte.replace("## 📚 Sommaire", "## 📚 Chapitres", 1)
            texte = retirer_encart_pdf(texte)
        prefixe = PREFIXES[nom]
        chap = reecrire_liens(convertir(texte), prefixe)
        titre = re.search(r"<h1[^>]*>(.*?)</h1>", chap, re.DOTALL)
        sommaire.append((prefixe, re.sub(r"<[^>]+>", "", titre.group(1)) if titre else court))
        corps.append(f'<section class="chapitre" id="{prefixe}">{chap}</section>')

    # Annexe : code source complet des exemples
    annexe = [
        '<section class="chapitre" id="annexe">',
        "<h1>Annexe — Code source complet des exemples</h1>",
        (
            "<p>Ces fichiers sont ceux utilisés dans les chapitres 5, 7 et 9. Ils sont aussi "
            "<strong>joints au PDF</strong> (pièce jointe <code>exemples-cours-git.zip</code>, "
            "visible dans le panneau « Pièces jointes » d'Adobe Reader, Firefox, Okular…) : "
            "préfère cette version, car un copier-coller depuis un PDF peut abîmer "
            "l'indentation, fatale en Python et en YAML.</p>"
        ),
        "<p><strong>Arborescence à recréer :</strong></p>",
        bloc_code(
            "exemples/\n"
            "├── projet-demo/\n"
            "│   ├── pyproject.toml\n"
            "│   ├── requirements-dev.txt\n"
            "│   ├── src/demo/__init__.py\n"
            "│   ├── src/demo/stats.py\n"
            "│   └── tests/test_stats.py\n"
            "├── github-actions/ci.yml            → à copier dans .github/workflows/\n"
            "├── github-actions/rapport-hebdo.yml → à copier dans .github/workflows/\n"
            "├── gitlab-ci/.gitlab-ci.yml         → à copier à la racine du dépôt\n"
            "└── gitignore-data-science           → à renommer en .gitignore",
            "text",
        ),
        "<p><strong>Vérifier en local :</strong></p>",
        bloc_code(
            "cd exemples/projet-demo\n"
            "python -m venv .venv\n"
            "source .venv/bin/activate      # Git Bash (Windows) : source .venv/Scripts/activate\n"
            "pip install -r requirements-dev.txt\n"
            "ruff check .                   # attendu : All checks passed!\n"
            "python -m pytest --cov=demo    # attendu : 6 passed, couverture 100 %",
            "bash",
        ),
    ]
    for rel, langage in ANNEXES:
        contenu = (EXEMPLES / rel).read_text(encoding="utf-8")
        annexe.append(f'<h2 id="{id_annexe(rel)}"><code>exemples/{html.escape(rel)}</code></h2>')
        annexe.append(bloc_code(contenu, langage))
    annexe.append("</section>")
    corps.append("\n".join(annexe))
    sommaire.append(("annexe", "Annexe — Code source complet des exemples"))

    date = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%d/%m/%Y")
    couverture = f"""
<section class="couverture">
  <div class="sur-titre">Cours complet</div>
  <h1 class="titre">Git, GitHub &amp; GitLab</h1>
  <p class="sous-titre">et leurs outils : Git Bash · GitHub Desktop · GitHub Actions ·
     GitLab CI/CD · GitKraken</p>
  <p class="public">Orienté data science, data analytics et développement —
     explications, exemples testés et TP final</p>
  <p class="date">Version du {date}</p>
</section>"""
    toc = "\n".join(
        f'<li><a href="#{p}"><span>{html.escape(t)}</span></a></li>' for p, t in sommaire
    )
    toc_html = f'<section class="sommaire"><h1>Sommaire</h1><ol>{toc}</ol></section>'

    css_pygments = HtmlFormatter(style="friendly").get_style_defs(".highlight")
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>Cours Git, GitHub &amp; GitLab</title>
<style>{CSS}\n{css_pygments}\n.highlight {{ background: var(--code-bg); }}</style>
</head><body>{couverture}{toc_html}{''.join(corps)}</body></html>"""


CSS = """
:root { --accent:#c2410c; --encre:#1f2328; --gris:#59636e; --bord:#d0d7de;
        --code-bg:#f6f8fa; --note:#fff8e6; }
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "DejaVu Sans", "Liberation Sans", Arial, "Noto Color Emoji", sans-serif;
       font-size: 9.6pt; line-height: 1.5; color: var(--encre); margin: 0; }
h1, h2, h3, h4 { line-height: 1.25; break-after: avoid; page-break-after: avoid; }
h1 { font-size: 20pt; color: var(--accent); border-bottom: 2px solid var(--accent);
     padding-bottom: 4pt; margin: 0 0 12pt; }
h2 { font-size: 13.5pt; margin: 18pt 0 6pt; border-bottom: 1px solid var(--bord);
     padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; }
.chapitre { break-before: page; page-break-before: always; }
p, li { orphans: 3; widows: 3; }
a { color: #0550ae; text-decoration: none; }
code { font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; font-size: 8.4pt;
       background: var(--code-bg); padding: 0.5pt 3pt; border-radius: 3px; }
pre { font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; font-size: 7.9pt;
      line-height: 1.38; white-space: pre-wrap; overflow-wrap: anywhere;
      background: var(--code-bg); border: 1px solid var(--bord); border-left: 3px solid var(--accent);
      border-radius: 4px; padding: 6pt 8pt; margin: 6pt 0 10pt; }
pre code { background: none; padding: 0; font-size: inherit; }
.highlight pre { break-inside: auto; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 12pt; font-size: 8.8pt; }
th, td { border: 1px solid var(--bord); padding: 3.5pt 6pt; vertical-align: top; text-align: left; }
th { background: #eef1f4; }
tr { break-inside: avoid; page-break-inside: avoid; }
td code, th code { font-size: 7.9pt; }
blockquote { margin: 8pt 0; padding: 5pt 10pt; background: var(--note);
             border-left: 4px solid #d4a72c; border-radius: 3px; break-inside: avoid; }
blockquote p { margin: 3pt 0; }
hr { border: none; border-top: 1px solid var(--bord); margin: 14pt 0; }
.couverture { height: 255mm; display: flex; flex-direction: column; justify-content: center;
              padding: 0 10mm; border-left: 8mm solid var(--accent); }
.couverture .sur-titre { text-transform: uppercase; letter-spacing: 3pt; color: var(--gris);
                         font-size: 11pt; }
.couverture .titre { font-size: 38pt; border: none; color: var(--encre); margin: 6pt 0 10pt; }
.couverture .sous-titre { font-size: 14pt; color: var(--accent); margin: 0 0 18pt; }
.couverture .public { font-size: 11pt; color: var(--gris); }
.couverture .date { margin-top: 40mm; color: var(--gris); }
.sommaire { break-before: page; page-break-before: always; }
.sommaire ol { font-size: 12pt; line-height: 2.1; padding-left: 28pt; }
.sommaire a { color: var(--encre); }
"""


def imprimer_pdf(source_html: Path, cible_pdf: Path) -> None:
    from playwright.sync_api import sync_playwright

    pied = (
        '<div style="width:100%;font-size:7.5pt;color:#59636e;padding:0 15mm;'
        'display:flex;justify-content:space-between;font-family:DejaVu Sans,Arial">'
        "<span>Cours Git, GitHub &amp; GitLab</span>"
        '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
    )
    with sync_playwright() as p:
        navigateur = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        page = navigateur.new_page()
        page.goto(source_html.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(cible_pdf),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=pied,
            outline=True,  # signets PDF à partir des titres (Chromium récent)
            tagged=True,
        )
        navigateur.close()


def joindre_exemples(cible_pdf: Path) -> None:
    from pypdf import PdfReader, PdfWriter

    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(EXEMPLES.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and ".pytest_cache" not in f.parts:
                z.write(f, Path("exemples") / f.relative_to(EXEMPLES))
    writer = PdfWriter(clone_from=PdfReader(cible_pdf))
    writer.add_attachment("exemples-cours-git.zip", tampon.getvalue())
    writer.add_metadata(
        {"/Title": "Cours Git, GitHub & GitLab", "/Subject": "Git, GitHub, GitLab et outils"}
    )
    with cible_pdf.open("wb") as f:
        writer.write(f)


def main() -> int:
    SORTIE_HTML.write_text(construire_html(), encoding="utf-8")
    print(f"HTML : {SORTIE_HTML}")
    try:
        imprimer_pdf(SORTIE_HTML, SORTIE_PDF)
    except ImportError:
        print("Playwright absent : ouvre le fichier HTML dans Chrome et fais Ctrl+P → PDF.")
        return 1
    joindre_exemples(SORTIE_PDF)
    print(f"PDF  : {SORTIE_PDF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

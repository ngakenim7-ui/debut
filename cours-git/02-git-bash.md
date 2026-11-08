# Chapitre 2 — Git Bash : un terminal Linux sous Windows

## 2.1 C'est quoi ?

**Git Bash** est un terminal installé automatiquement avec **Git for Windows**. Il fournit :

- le shell **Bash** (le même que sous Linux/macOS) ;
- les commandes Unix courantes : `ls`, `cd`, `pwd`, `cat`, `grep`, `find`, `touch`, `mkdir`, `rm`, `cp`, `mv`, `head`, `tail`, `less`, `nano`/`vim` ;
- `ssh` et `ssh-keygen` (pour les clés SSH GitHub/GitLab) ;
- bien sûr la commande `git`.

Techniquement, c'est un environnement basé sur **MSYS2** affiché dans le terminal **MinTTY**.

> **Pourquoi l'utiliser ?** Les tutoriels Git, les docs et les scripts CI sont écrits en Bash. Avec Git Bash, tu tapes exactement les mêmes commandes que sur un serveur Linux ou dans GitHub Actions / GitLab CI. Sous macOS/Linux, tu n'en as pas besoin : ton terminal fait déjà tout ça.

---

## 2.2 Installation et ouverture

1. Télécharger Git for Windows sur <https://git-scm.com/download/win>.
2. Pendant l'installation, choix recommandés :
   - Éditeur par défaut : **VS Code** (ou Notepad++) plutôt que Vim si tu débutes ;
   - Nom de la branche initiale : **main** ;
   - « Git from the command line and also from 3rd-party software » ;
   - Fins de ligne : « Checkout Windows-style, commit Unix-style » (= `core.autocrlf true`).
3. Ouvrir : menu Démarrer → **Git Bash**, ou clic droit dans un dossier → **Open Git Bash here** (sous Windows 11 : « Afficher d'autres options »).

Dans VS Code : `Ctrl + Maj + P` → « Terminal: Select Default Profile » → **Git Bash**.

---

## 2.3 Les chemins : la différence à connaître

| Windows (PowerShell/cmd) | Git Bash |
|---|---|
| `C:\Users\Nim\Documents` | `/c/Users/Nim/Documents` |
| `\` séparateur | `/` séparateur |
| `%USERPROFILE%` | `~` ou `$HOME` |

```bash
cd /c/Users/Nim/Documents/projets
cd ~                # dossier personnel
cd ..               # dossier parent
cd -                # dossier précédent
pwd                 # où suis-je ?
explorer .          # ouvre le dossier courant dans l'Explorateur Windows
code .              # ouvre le dossier dans VS Code
```

> 💡 Les chemins avec espaces doivent être entre guillemets : `cd "/c/Users/Nim/Mes Documents"`.

---

## 2.4 Commandes Bash essentielles

```bash
ls                  # lister
ls -la              # lister tout, y compris les fichiers cachés (.git, .gitignore)
mkdir -p projet/data/raw   # créer une arborescence
touch notes.md      # créer un fichier vide
cat fichier.txt     # afficher le contenu
head -n 5 data.csv  # 5 premières lignes (pratique pour inspecter un CSV)
tail -f app.log     # suivre un log en direct
wc -l data.csv      # nombre de lignes
grep -rn "TODO" src/        # chercher "TODO" récursivement avec numéros de ligne
find . -name "*.ipynb"      # trouver tous les notebooks
cp source.py copie.py
mv ancien.py nouveau.py
rm fichier.txt
rm -r dossier/      # ⚠️ suppression définitive, pas de corbeille
history             # commandes précédentes  (flèche ↑ aussi)
clear               # nettoyer l'écran (ou Ctrl + L)
```

**Raccourcis :** `Tab` = autocomplétion (fichiers, branches Git !), `Ctrl + C` = interrompre, `Ctrl + R` = rechercher dans l'historique. Copier/coller dans MinTTY : `Ctrl + Inser` / `Maj + Inser` (ou sélection = copie, clic droit = coller selon la config).

---

## 2.5 Exemple complet : premier projet en Git Bash

```bash
cd /c/Users/Nim/Documents
mkdir analyse-ventes && cd analyse-ventes
git init
echo "# Analyse des ventes" > README.md
printf '__pycache__/\n.venv/\n.env\ndata/raw/\n' > .gitignore
git add README.md .gitignore
git commit -m "Initialise le projet"
git log --oneline
```

---

## 2.6 Créer une clé SSH (pour GitHub ou GitLab)

```bash
ssh-keygen -t ed25519 -C "ton.email@exemple.com"
# Appuie sur Entrée pour l'emplacement par défaut (~/.ssh/id_ed25519)
# Choisis une passphrase (recommandé)

eval "$(ssh-agent -s)"          # démarre l'agent SSH
ssh-add ~/.ssh/id_ed25519       # ajoute la clé à l'agent

cat ~/.ssh/id_ed25519.pub       # clé PUBLIQUE à copier dans GitHub/GitLab
clip < ~/.ssh/id_ed25519.pub    # Windows : copie directement dans le presse-papiers
```

Puis colle-la dans **GitHub → Settings → SSH and GPG keys** ou **GitLab → Preferences → SSH Keys**, et teste :

```bash
ssh -T git@github.com     # "Hi <utilisateur>! You've successfully authenticated..."
ssh -T git@gitlab.com     # "Welcome to GitLab, @<utilisateur>!"
```

> ⚠️ Ne partage **jamais** le fichier sans `.pub` (`id_ed25519`) : c'est ta clé privée.

---

## 2.7 Personnaliser : alias et `.bashrc`

Alias Git (stockés dans `~/.gitconfig`) :

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.sw switch
git config --global alias.lg "log --oneline --graph --all --decorate"
# Ensuite : git lg
```

Alias Bash (dans `~/.bashrc`, rechargé avec `source ~/.bashrc`) :

```bash
alias gs='git status'
alias activate='source .venv/Scripts/activate'   # venv Python sous Windows/Git Bash
```

> 💡 Sous Git Bash, un environnement virtuel Python s'active avec `source .venv/Scripts/activate` (dossier `Scripts` sous Windows, `bin` sous Linux/macOS).

---

## 2.8 Pièges fréquents

| Problème | Cause / Solution |
|---|---|
| `python` ouvre le Microsoft Store ou ne répond pas | Désactive les « alias d'exécution d'application » Windows, ou utilise `py` ; si un script interactif bloque, préfixe avec `winpty python` |
| `warning: LF will be replaced by CRLF` | Normal avec `core.autocrlf true` ; ajoute un `.gitattributes` avec `* text=auto` pour uniformiser l'équipe |
| `Permission denied (publickey)` | Clé SSH non ajoutée à GitHub/GitLab ou à l'agent (voir 2.6) |
| Bloqué dans un écran avec `:` ou `~` | Tu es dans `less` ou Vim : tape `q` (less) ou `Échap` puis `:q!` + Entrée (Vim) |

➡️ Suite : [Chapitre 3 — GitHub](03-github.md)

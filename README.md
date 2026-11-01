# Kit du contributeur — ateliers Epitech Academy

Tu as un atelier de programmation (en Markdown, PDF, DOCX, ou sur une page web) et tu veux qu'il
tourne sur la plateforme d'ateliers d'Epitech Academy ? Ce dépôt contient de quoi le porter.

La plateforme est un plugin CTFd : les étapes se débloquent une à une, l'application de
l'atelier (éditeur, jeu, console) s'ouvre à côté du texte, et la progression de chaque
participant est suivie. Pour qu'un atelier y soit importé, il doit être rangé dans un **dépôt de
sujet** au format « convention 2.0 ».

## Ce qu'il y a ici

| Fichier | À quoi il sert |
|---|---|
| [`PROMPT.md`](PROMPT.md) | Un prompt à donner à un assistant IA de code (Claude Code, par exemple). Il transforme ton atelier en dépôt de sujet, puis le vérifie avec le linter de la plateforme. |

## Porter un atelier en 4 étapes

1. **Rassemble tes fichiers** dans un dossier : le texte, les images, le code de départ, et les
   corrigés s'il y en a.
2. **Ouvre ton assistant IA** dans un dossier vide, colle le contenu de `PROMPT.md` (tout ce qui
   suit `PROMPT STARTS HERE`), et dis-lui où sont tes fichiers.
3. **Réponds à ses questions** et relis le plan qu'il te montre : il attend ton accord avant
   d'écrire quoi que ce soit.
4. **Récupère le résultat** : un dépôt `<nom>_subject` qui passe le linter, et un rapport qui
   liste ce qui a été changé, ce qui manque (captures d'écran, contenu) et les questions à
   trancher.

Le prompt est en anglais parce qu'il s'adresse à l'IA. L'assistant te parle dans ta langue, et
le texte de ton atelier reste dans la sienne.

## Les règles qui ne se négocient pas

- **On ne donne jamais à l'élève le code d'une étape qu'il doit écrire**, ni dans le texte, ni
  dans un indice, ni dans une capture. Seules les étapes « de modelage » (les toutes premières, ou
  celles qui introduisent une notion nouvelle) donnent le code, et c'est marqué.
- **Les réponses ne sont jamais dans le Markdown** : réponses des quiz, flags et corrigés vivent à
  part, chiffrés si le dépôt est public.
- **Les images sont dans le dépôt**, jamais en lien vers un autre site.
- **Pas de secret** (mot de passe, jeton, e-mail personnel) dans un fichier ou un commit.

Le guide de style des contenus (ton, outils, public) est dans
[ContributionGuide](https://github.com/Manta-Epitech-Academy/ContributionGuide).

## Références

- La convention et son linter :
  [workshop-content-tools](https://github.com/kevin-cazal/workshop-content-tools)
  (`CONTENT_CONVENTION.md`, `ws_parser.py`, `examples/minimal/`).
- Le guide court pour les auteurs, et le protocole des applications d'atelier :
  [ctfd-workshop-platform](https://github.com/Manta-Epitech-Academy/ctfd-workshop-platform)
  (`docs/CONTRIBUER.md`, `docs/RUNTIME_PROTOCOL.md`).
- Des ateliers déjà portés, à prendre pour modèle :
  - [tortue_subject](https://github.com/kevin-cazal/tortue_subject) : Python turtle, quiz,
    indices, boîte à outils, bonus ;
  - [pacman-ghost-ai_subject](https://github.com/kevin-cazal/pacman-ghost-ai_subject) : Lua,
    deux parties, codes de validation chiffrés ;
  - [voxel-world_subject](https://github.com/Manta-Epitech-Academy/voxel-world_subject/tree/ctfd-workshop-plugin) :
    sept étapes dans un seul document, validées par l'application elle-même, avec captures.

## Ce que le prompt ne fait pas

- **Il ne porte pas l'application de l'atelier.** Si ton atelier a besoin d'une application web
  que la plateforme n'a pas encore, il porte le sujet et te le signale : brancher une nouvelle
  application est un travail à part (`docs/RUNTIME_PROTOCOL.md`).
- **Il ne publie rien.** Pas de push, pas de pull request, pas de déploiement sans ta demande.

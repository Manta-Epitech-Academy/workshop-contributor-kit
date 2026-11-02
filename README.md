# Kit du contributeur — ateliers Epitech Academy

Tu as un atelier de programmation et tu veux qu'il tourne sur la plateforme d'ateliers d'Epitech
Academy ? Ce dépôt contient de quoi le porter.

La plateforme est un plugin CTFd : les étapes se débloquent une à une, l'application de
l'atelier (éditeur, jeu, console) s'ouvre à côté du texte, et la progression de chaque
participant est suivie. Un atelier, c'est donc deux choses :

- **le sujet** : le texte, les étapes, les indices, les quiz, rangés dans un dépôt de sujet au
  format « convention 2.0 » ;
- **l'application** (facultative) : la page web où l'élève travaille, que la plateforme appelle
  un *runtime*.

## Ce qu'il y a ici

| Dossier | À quoi il sert |
|---|---|
| [`workshop-subject/PROMPT.md`](workshop-subject/PROMPT.md) | Porter le **sujet** : un atelier en Markdown, PDF, DOCX ou page web devient un dépôt de sujet, vérifié par le linter de la plateforme. |
| [`workshop-app/PROMPT.md`](workshop-app/PROMPT.md) | Porter ou créer l'**application** : une application web existante (sources ou simple fichier construit), ou une nouvelle, branchée sur la plateforme et capable, si elle le peut, de valider elle-même les étapes. |

Ce sont des prompts à donner à un assistant IA de code, Claude Code par exemple. Ils sont en
anglais parce qu'ils s'adressent à l'IA. L'assistant te parle dans ta langue, et le texte de
ton atelier reste dans la sienne.

Commence par le sujet. Ne passe à l'application que si l'atelier en a besoin et que la
plateforme ne l'a pas déjà : TIC-80, Python turtle, Pac-Man, MiniASM et le terminal Linux
existent.

## Comment s'en servir

1. **Rassemble tes fichiers** dans un dossier : le texte, les images, le code de départ, les
   corrigés, et l'application (ses sources, ou ce que tu en as).
2. **Ouvre ton assistant IA** dans un dossier vide, colle le contenu du prompt (tout ce qui suit
   `PROMPT STARTS HERE`), et dis-lui où sont tes fichiers.
3. **Réponds à ses questions** et relis le plan qu'il te montre : il attend ton accord avant
   d'écrire quoi que ce soit.
4. **Récupère le résultat** :
   - pour le sujet, un dépôt `<nom>_subject` qui passe le linter ;
   - pour l'application, un dépôt `<nom>_runtime` testé, et les fichiers à ajouter côté
     plateforme.

   Dans les deux cas, il te remet un rapport : ce qui a été fait, ce qui a été testé, ce qui
   manque, et les questions à trancher.

## Les règles qui ne se négocient pas

- **On ne donne jamais à l'élève le code d'une étape qu'il doit écrire**, ni dans le texte, ni
  dans un indice, ni dans une capture, ni dans l'application (pas de bouton « corrigé »). Seules
  les étapes « de modelage » donnent le code, et c'est marqué dans le sujet.
- **Les réponses ne sont jamais dans le Markdown**, et les corrigés ne sont jamais dans ce qui est
  servi aux élèves. Ils vivent à part, chiffrés ou dans un dépôt privé.
- **L'application ne valide jamais une étape à la place de l'élève** : elle vérifie, montre, et
  propose. C'est l'élève qui soumet.
- **Tout est dans les dépôts** : pas d'image en lien vers un autre site, pas de bibliothèque
  chargée depuis Internet pendant l'atelier.
- **Pas de secret** (mot de passe, jeton, e-mail personnel) dans un fichier ou un commit.
- **Rien n'est mis en ligne sans l'équipe** : pas de push sur `main`, pas de déploiement.

Le guide de style des contenus (ton, outils, public) est dans
[ContributionGuide](https://github.com/Manta-Epitech-Academy/ContributionGuide).

## Références

- La convention des sujets et son linter :
  [workshop-content-tools](https://github.com/kevin-cazal/workshop-content-tools).
- La plateforme, le guide court des auteurs et le protocole des applications :
  [ctfd-workshop-platform](https://github.com/Manta-Epitech-Academy/ctfd-workshop-platform)
  (`docs/CONTRIBUER.md`, `docs/RUNTIME_PROTOCOL.md`).
- Des sujets déjà portés :
  [tortue_subject](https://github.com/kevin-cazal/tortue_subject),
  [pacman-ghost-ai_subject](https://github.com/kevin-cazal/pacman-ghost-ai_subject),
  [voxel-world_subject](https://github.com/Manta-Epitech-Academy/voxel-world_subject/tree/ctfd-workshop-plugin).
- Des applications déjà branchées :
  - [pacman-ghost-ai_runtime](https://github.com/Manta-Epitech-Academy/pacman-ghost-ai_runtime) :
    site statique, sans validation par l'application ;
  - [miniasm_runtime](https://github.com/Manta-Epitech-Academy/miniasm_runtime) : l'application
    valide les étapes et donne un code ;
  - [voxel-world_runtime](https://github.com/Manta-Epitech-Academy/voxel-world_runtime/tree/wrp-port) :
    application sans sources, portée en patchant sa page construite, avec un plan de portage.

# Le format de recette, et les cas pénibles

## Structure

```json
{
  "url": "https://exemple.fr/atelier",
  "viewport": [1280, 800],
  "scale": 2,
  "theme": "dark",
  "locale": "fr-FR",
  "hide": [".cookie-banner", "#chat-widget"],
  "out": "img",
  "into": "sujet/atelier1.md",
  "steps": [ ... ]
}
```

`into` est le fichier markdown dans lequel les images seront écrites ; chaque étape peut le
surcharger avec sa propre clé `into`. Sans ancre, une capture remplace le premier
`[CAPTURE À FAIRE]` restant du fichier ; avec `marker`, `after` ou `before`, elle se place où vous
voulez. Relancer la recette remplace l'image en place au lieu d'en ajouter une deuxième.

`hide` masque des éléments sur **toutes** les captures : bandeaux de cookies, widgets de support,
barres de debug. Ça évite d'avoir à les retirer image par image.

## Les étapes disponibles

| Étape | Effet |
|---|---|
| `{"goto": "url"}` | naviguer |
| `{"wait_for": "#sel"}` | attendre qu'un élément existe (30 s max, `timeout` pour changer) |
| `{"wait": 1.5}` | attendre des secondes |
| `{"click": "#sel"}` | cliquer |
| `{"fill": "#sel", "text": "..."}` | remplir un champ classique |
| `{"type": "#sel", "text": "...", "delay": 25}` | taper caractère par caractère |
| `{"key": "Enter"}` | une touche |
| `{"js": "..."}` | exécuter du JS dans la page — la porte de sortie |
| `{"scroll_to": "#sel"}` | faire défiler jusqu'à un élément |
| `{"hide": "#sel"}` | masquer, à cet instant |
| `{"highlight": "#sel"}` | contour rouge dessiné **dans la page** |
| `{"label": "#sel", "text": "X + 2", "side": "top", "class": "..."}` | étiquette ajoutée **dans la page**, avec la police de la cible (ou une classe de l'app) |
| `{"clear_labels": true}` | retirer toutes les étiquettes |
| `{"shot": "nom", "selector": "#sel", "alt": "...", "annotate": [...]}` | une capture |
| `{"gif": "nom", "selector": "#sel", "seconds": 4, "fps": 8, "during": [...]}` | une animation ; `during` joue des étapes **pendant** l'enregistrement ; `step` la filme image par image (cas 9) |

`shot` accepte aussi `"full": true` (page entière) et `"animate": true` (ne pas figer les
animations CSS, utile juste avant un gif).

Au niveau de la recette, `keycast` affiche les touches frappées (voir cas 8).

---

## Cas 1 — un éditeur de code

`fill` ne marche pas sur CodeMirror, Monaco ou Ace : le `<textarea>` visible n'est pas la source
de vérité. Passer par l'API de l'éditeur :

```json
{"js": "document.querySelector('.cm-editor').cloneNode; window.view.dispatch({changes:{from:0,to:window.view.state.doc.length,insert:'return { canGoLeft = true }'}})"}
```

Si l'objet éditeur n'est pas exposé globalement, deuxième solution : cliquer dedans, tout
sélectionner, taper.

```json
{"click": ".cm-content"},
{"key": "Control+a"},
{"type": ".cm-content", "text": "return { canGoLeft = true }", "delay": 10}
```

C'est plus lent mais ça marche partout, et le rendu ressemble à ce que l'élève verra.

## Cas 2 — un jeu sur `<canvas>`

Un canvas se capture comme n'importe quel élément, mais son contenu dépend d'une boucle
d'animation : il faut attendre un état stable, et non un sélecteur.

```json
{"click": "#start"},
{"wait": 1.2},
{"gif": "poursuite", "selector": "canvas", "seconds": 4, "fps": 8}
```

Pour une image fixe reproductible, mieux vaut mettre le jeu en pause avant :
`{"js": "window.game && window.game.pause()"}`.

## Cas 3 — le contenu est dans une iframe

`probe` signale les iframes. Les sélecteurs de la page principale ne les traversent pas. Le plus
simple est de capturer l'iframe **entière** comme un élément :

```json
{"shot": "runtime", "selector": "iframe#runtime"}
```

Pour cliquer à l'intérieur, viser directement l'URL de l'iframe avec `goto` : c'est presque
toujours une page autonome.

## Cas 4 — attendre le bon moment

Le piège le plus courant : capturer trop tôt et livrer une image d'un écran de chargement.

- Attendre un élément qui n'existe **qu'une fois prêt** : `{"wait_for": "#resultat"}`
- Attendre un texte : `{"js": "return document.body.innerText.includes('Terminé')"}` dans une
  boucle n'existe pas ici — utiliser `wait_for` sur un sélecteur, puis un `wait` court.
- Pour les polices et les images, un `{"wait": 0.5}` après `wait_for` suffit presque toujours.

## Cas 5 — il faut se connecter

Ne mettez jamais de mot de passe dans une recette versionnée. Deux options :

```json
{"goto": "https://exemple.fr/login"},
{"fill": "#user", "text": "demo"},
{"fill": "#pass", "text": "__ENV__"},
```

Le plus simple reste de capturer une instance de démo sans authentification, ou une instance
locale. Une capture d'atelier ne devrait de toute façon jamais montrer un compte réel.

## Cas 6 — la même capture pour dix étapes

Quand chaque étape ajoute une ligne de code et change le résultat, une seule recette suffit :
enchaîner `js` (poser le code de l'étape N) → `click` (relancer) → `wait` → `shot`. Dix étapes,
dix images cohérentes, un seul passage. C'est là que ce script rembourse son écriture.

## Cas 7 — une étiquette, dessinée par le runtime

Une étiquette n'est jamais peinte sur l'image après la capture : elle est dessinée **par le
runtime**, avant, pour avoir sa police, sa taille et ses couleurs.

**Page web.** L'étape `label` ajoute un élément dans la page, à côté de la cible. Sans `class`, il
reprend la police, la taille et la couleur de la cible. Avec `class`, il prend le style d'un
composant qui existe déjà dans l'app (badge, tag, pastille) : c'est le rendu le plus homogène.

```json
{"label": "#ghost", "text": "X + 2", "side": "top"},
{"label": ".score", "text": "+100", "side": "right", "class": "badge"},
{"shot": "etape4", "selector": "#game", "alt": "Le fantôme avance de 2 pixels vers la droite à chaque image"},
{"clear_labels": true}
```

**Runtime sur canvas (TIC-80, jeu web).** L'étape `label` ne peut rien faire : le contenu du
canvas n'est pas dans le DOM. L'étiquette s'écrit dans le programme d'illustration, avec la
fonction de texte du runtime :

```lua
-- TIC-80 : même police que la console et que le jeu de l'élève
print("X + 2", ex + 10, ey - 8, 4)
print("0", 2, 2, 12)
```

Pour un jeu en JavaScript, `ctx.fillText` avec la police que le jeu utilise déjà.

## Cas 8 — filmer une frappe au clavier

Deux morceaux : `during` joue des étapes **pendant** que le gif s'enregistre, et `keycast` montre
les touches, comme *showmethekey* ou *KeyCastr* sur un enregistrement de bureau.

```json
{
  "url": "http://localhost:8090/",
  "keycast": {"selector": "#game", "position": "bottom-right", "keep": 1.2},
  "out": "sujet/img",
  "steps": [
    {"wait_for": "#game"},
    {"gif": "etape1-studio", "selector": "#game", "seconds": 5, "fps": 10,
     "during": [{"at": 0.5, "type": "#game", "text": "studio", "delay": 160},
                {"at": 2.5, "key": "Enter"}]}
  ]
}
```

- `at` est la seconde depuis le début du gif. Toutes les étapes d'action marchent dans `during`.
- `selector` sur `keycast` ancre les touches **dans** le panneau filmé : sans lui, elles se
  placent dans le coin de la fenêtre, donc hors d'une capture d'élément.
- Les touches nommées deviennent des symboles (`↵`, `Esc`, `⇥`, `↑`), un raccourci s'affiche en
  une seule touche (`Ctrl + R`), et les modificateurs seuls ne s'affichent pas.
- Ce n'est pas une entorse à la règle sur le texte : c'est le navigateur qui dessine ces touches
  dans la page, avant la capture, avec la police de la page. Elles s'effacent toutes seules après
  `keep` secondes.

## Cas 9 — un jeu filmé image par image (`step`)

Filmer en temps réel suppose que chaque capture prend moins d'un intervalle. Sur un jeu en canvas
ce n'est pas le cas : une capture d'élément prend 100 à 200 ms, donc un gif annoncé à 20 i/s en
contient 5 par seconde réelle, l'animation est accélérée et les appuis de `during` tombent au
mauvais endroit.

Quand la page peut faire avancer le jeu elle-même, `step` règle ça : c'est une expression JS
exécutée **avant chaque image**. Le film se compte alors en images, et `at` devient un temps
*dans le gif*.

```json
{"js": "freeRun(false)"},
{"gif": "pad-limites", "selector": "#stage", "seconds": 5, "fps": 20, "step": "advance(3)",
 "during": [{"at": 0.4, "js": "hold('ArrowRight')"}, {"at": 1.9, "js": "release('ArrowRight')"}]},
{"js": "freeRun(true)"}
```

Ici `advance(3)` fait tourner trois tours de boucle du jeu (60 par seconde, 20 images par
seconde). C'est la page qui fournit `advance` : pour un runtime emscripten ou tout jeu piloté par
`requestAnimationFrame`, il suffit de remplacer `requestAnimationFrame` par une file que l'on vide
à la main. Le résultat est identique d'une exécution à l'autre.

Pour du pixel art ou des aplats, ajouter `"dither": "none"` : le tramage par défaut, fait pour les
dégradés d'une page web, mouchette une couleur unie en plusieurs teintes voisines.

---

## Rappels de qualité

- **Aucun texte peint après la capture.** Une étiquette, si elle est utile, est dessinée par le
  runtime (étape `label`, ou `print` dans le programme). Seulement des termes courts : `X`, `Y`,
  `largeur`, `longueur`, `hauteur`, des nombres et des signes (`8`, `-10`, `+100`, `X + 2`). Pas
  de mot long, pas de phrase, et jamais une étiquette qui gêne la lecture de la capture. Les
  phrases vont dans la légende sous l'image. Une capture est nue, encadrée,
  fléchée, ou étiquetée par le runtime.
- Un seul `viewport` et un seul `theme` pour tout l'atelier.
- Cibler un panneau (`selector`) plutôt que la page.
- Flouter tout nom, avatar, e-mail ou jeton avant diffusion.
- Nommer les fichiers d'après l'étape : `etape3-resultat.png`.
- Regarder les images produites avant de les livrer. Le script écrit un fichier même quand la
  capture ne montre pas ce que vous croyez.

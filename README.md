# raz-landing

Landing page for רז מאיר כהן, under קבוצת תום הרוש.
Live at **https://tom-harush.co.il/raz-meir-cohen/**

## Layout

    index.html          the page
    assets/             lottie icons, images, vendored lottie_light.min.js
    tools/              build + deploy scripts, never deployed

## Icons

`tools/recolor.py` converts the seven LordIcon lotties that Gal supplied from
their placeholder palette (`#E8B9BB` line art, `#FF0000` accent) to the page
palette (stone `#F1EDE7`, brand red `#C2151C`) and writes them to `assets/`.
Sources live in `Downloads/רז מאיר כהן/`, named in Hebrew, one per timeline stage.

Playback speed is **0.75** everywhere. Gal's call.

## Preview

Lottie loads its JSON by XHR, which Chrome blocks on `file://`, so opening
index.html directly renders empty icon boxes. Always preview over HTTP:

    python -m http.server 8777

## Deploy

    python tools/deploy.py

Uploads the site to the real path over FTPS. Credentials live in
`tools/.ftp.json`, which is gitignored and never leaves this machine.
GitHub Pages serves the same commit as a preview URL.

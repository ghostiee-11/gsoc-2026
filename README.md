# GSoC 2026 work product — Lumen + xarray

Final work product for Google Summer of Code 2026 with **HoloViz**, under **NumFOCUS**.

**Read it here: https://ghostiee-11.github.io/gsoc-2026/**

Contributor: [Aman Kumar](https://github.com/ghostiee-11) ·
Mentors: [Andrew Huang](https://github.com/ahuang11), [Andy Maloney](https://github.com/amaloney) ·
Project: *Lumen and xarray integration*, 350 hours.

The page is one self-contained `index.html`: no build step, no dependencies, no network
calls at runtime. Every pull request state and diff size shown on it is read from the
GitHub API rather than typed by hand.

## Rebuilding it

```sh
python3 build/collect.py     # read GitHub through the gh CLI, writes build/data.json
python3 build/render.py      # inline that data into build/page.html, writes index.html
```

`collect.py` needs an authenticated [`gh`](https://cli.github.com); set `GH=/path/to/gh` if
it is not on `PATH`. `render.py` fails loudly if the page references a pull request that
is not in the data, or an image that is not in `assets/`.

Edit `build/page.html`, never `index.html` — the latter is generated.

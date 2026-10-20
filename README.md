# Auto BG Removal

Outil local de suppression de fond d'images basé sur **SAM 2** (Meta), avec édition interactive du masque (clics +/−, box, brush manuel) et export PNG transparent.

```
┌─────────────────────────────────────────────────────────────┐
│ Auto BG Removal              [tiny ●] [Charger] [Export]   │
├─────────────────────────────────────────────────────────────┤
│ Points  Box  Brush+  Brush−   Auto   Undo  Redo   Reset    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│             ░░░ image avec masque cyan ░░░                  │
│                  ● points verts (incl)                      │
│                  ● points rouges (excl)                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Modèle: tiny  ·  Image: 1920×1080  ·  Outil: points  ·  …  │
└─────────────────────────────────────────────────────────────┘
```

## Modes de fonctionnement

| Mode (`PREDICTOR_BACKEND`) | Usage | Prérequis |
|---|---|---|
| `fake` | Dev sans GPU. Mock géométrique (disque/rect/ellipse). | Python 3.10+ |
| `sam2` | SAM 2 réel sur GPU NVIDIA. | CUDA + `nvidia-container-toolkit` + 4-12 GB VRAM |

## Quickstart Docker (avec SAM 2)

```bash
# 1. Télécharger un checkpoint (commence par tiny pour aller vite)
./scripts/download_checkpoints.sh tiny

# 2. Configurer
cp .env.example .env
# Édite .env : PREDICTOR_BACKEND=sam2, INSTALL_SAM2=1, DEFAULT_MODEL=sam2_hiera_tiny

# 3. Build (compile l'extension CUDA de SAM 2, ~3-5 min) et démarrer
docker compose build
docker compose up -d
```

Ouvre `http://localhost:5173`. Status `ok` en bas si SAM 2 est chargé, `degraded` si checkpoint manquant.

Pour tester sans GPU, garde `PREDICTOR_BACKEND=fake` et `INSTALL_SAM2=0`.

## Dev local sans Docker

```bash
# Backend (terminal 1)
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/uvicorn auto_bg.main:app --app-dir src --reload
```

```bash
# Frontend (terminal 2)
cd frontend
pnpm install
pnpm dev
```

→ `http://localhost:5173`.

## Workflow

1. **Charger** une image (PNG/JPEG/WebP) via le bouton en haut à droite.
2. **Points** (`P`) : clic = inclure (vert), Shift+clic = exclure (rouge). Multi-clics raffinent itérativement.
3. **Box** (`R`) : drag pour entourer le sujet.
4. **Brush+** (`B`) / **Brush−** (`E`) : édition pixel-précise au pinceau (taille via `[` / `]`).
5. **Auto** (`A`) : `SAM2AutomaticMaskGenerator` + heuristique de sélection (exclut background et bruit, favorise grand + central). 2-30s selon checkpoint et taille image.
6. **Undo / Redo** : `Ctrl+Z` / `Ctrl+Shift+Z`. 50 ops max.
7. **Export PNG** : applique `(samMask | brushAdd) & ~brushErase` comme alpha sur l'image originale.

## Raccourcis clavier

| Touche | Action |
|---|---|
| `P` | Outil Points |
| `R` | Outil Box |
| `B` | Brush + (ajouter au masque) |
| `E` | Brush − (retirer du masque) |
| `1`-`4` | Outil par index |
| `A` | Auto-segment |
| `[` / `]` | Diminuer / agrandir le pinceau |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` ou `Ctrl+Y` | Redo |

## Tests

```bash
cd backend && .venv/bin/pytest
```

49 tests : RLE codec round-trip + compatibilité **bit-exact** avec pycocotools, LRU eviction, FakePredictor géométrique, contrat HTTP complet (sessions, predict 3 modes, switch model, recompute, export PNG RGBA, delete), ModelManager (lock asyncio, transitions, swap concurrent), heuristique de sélection auto-mask (background, bruit, scoring central).

## Architecture

```
backend/src/auto_bg/
├── api/                      # routes HTTP, schemas Pydantic, error handlers
├── segmentation/
│   ├── predictor.py          # Protocol Predictor (interface)
│   ├── fake_predictor.py     # mock géométrique (dev sans GPU)
│   ├── sam2_predictor.py     # wrapper SAM 2 + snapshot d'embedding par session
│   ├── model_manager.py      # singleton, lock asyncio, swap à chaud
│   └── registry.py           # mapping nom → (config Hydra, checkpoint, URL)
├── session/store.py          # LRU embedding store thread-safe
└── imaging/mask_codec.py     # RLE COCO via pycocotools

frontend/src/
├── api/                      # client HTTP + types miroir backend
├── codec/rle.ts              # port JS bit-exact compatible pycocotools
├── state/
│   ├── editor.ts             # store zustand (cœur du domaine)
│   └── history.ts            # pile undo/redo (RLE pour SAM, bbox slice pour brush)
├── canvas/
│   ├── EditorCanvas.tsx      # 3 layers natifs stackés
│   └── use{Image,Mask,Overlay}Layer.ts
├── tools/                    # handlers Points / Box / Brush (factories)
├── components/               # Toolbar, ModelSelector, BrushSize, etc.
└── hooks/useKeyboardShortcuts.ts
```

## Choix techniques notables

- **RLE COCO sur le wire** (5–30 KB JSON) au lieu de PNG base64 (~700 KB) → divise la latence interactive par ~50.
- **Composition mask 3 couches** : `(samMask | userAdd) & ~userErase`. Évite que les éditions brush soient « fantômées » par un nouveau clic SAM.
- **Snapshot d'embedding par session** : `SAM2ImagePredictor` est mono-image, on snapshot `_features`/`_orig_hw` après `set_image` et on les restore avant chaque predict — permet plusieurs sessions sans recompute.
- **`asyncio.to_thread` + `torch.inference_mode()` + `bfloat16`** : SAM 2 GPU sync-bloquant n'est jamais directement awaité — la boucle event reste réactive pendant les 1-2s d'inférence.
- **Swap atomique de modèle** : si le nouveau loader échoue, l'ancien reste actif. Permet une UX safe quand un checkpoint manque.
- **`warmup()` non-fatal** : si SAM 2 ne peut pas charger (checkpoint absent, OOM…), l'app démarre quand même en mode dégradé exposé via `/api/health`.

## Limitations connues / pour plus tard

- Pas de zoom/pan dans l'éditeur — l'image est rendue en `contain` du viewport. Pour des images 4K avec édition fine au pixel, un zoom serait utile.
- Mono-utilisateur : le LRU d'embedding est local au process backend.
- Le `SAM2AutomaticMaskGenerator` est lazy mais reste lent sur de grosses images (10-30s en `large` sur 4K). Un endpoint séparé async + polling serait plus propre qu'un long-poll.

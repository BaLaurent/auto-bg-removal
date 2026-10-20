from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    name: str
    config_yaml: str  # path Hydra relatif au package sam2 (sans extension recherchée par Hydra)
    checkpoint: str  # nom de fichier dans MODEL_DIR
    download_url: str
    size_mb: int


# Source Meta : https://dl.fbaipublicfiles.com/segment_anything_2/092824/<file>.pt
# Configs Hydra fournies par le package `sam2` (installé via pip install git+facebookresearch/sam2).
_BASE_URL = "https://dl.fbaipublicfiles.com/segment_anything_2/092824"

REGISTRY: dict[str, ModelSpec] = {
    "sam2_hiera_tiny": ModelSpec(
        name="sam2_hiera_tiny",
        config_yaml="configs/sam2.1/sam2.1_hiera_t.yaml",
        checkpoint="sam2.1_hiera_tiny.pt",
        download_url=f"{_BASE_URL}/sam2.1_hiera_tiny.pt",
        size_mb=149,
    ),
    "sam2_hiera_small": ModelSpec(
        name="sam2_hiera_small",
        config_yaml="configs/sam2.1/sam2.1_hiera_s.yaml",
        checkpoint="sam2.1_hiera_small.pt",
        download_url=f"{_BASE_URL}/sam2.1_hiera_small.pt",
        size_mb=176,
    ),
    "sam2_hiera_base_plus": ModelSpec(
        name="sam2_hiera_base_plus",
        config_yaml="configs/sam2.1/sam2.1_hiera_b+.yaml",
        checkpoint="sam2.1_hiera_base_plus.pt",
        download_url=f"{_BASE_URL}/sam2.1_hiera_base_plus.pt",
        size_mb=309,
    ),
    "sam2_hiera_large": ModelSpec(
        name="sam2_hiera_large",
        config_yaml="configs/sam2.1/sam2.1_hiera_l.yaml",
        checkpoint="sam2.1_hiera_large.pt",
        download_url=f"{_BASE_URL}/sam2.1_hiera_large.pt",
        size_mb=898,
    ),
}


FAKE_MODEL_NAME = "fake_predictor"


def known_models() -> list[str]:
    return list(REGISTRY.keys())


def get_spec(name: str) -> ModelSpec:
    if name not in REGISTRY:
        raise ValueError(f"Unknown SAM 2 model: {name}. Known: {list(REGISTRY)}")
    return REGISTRY[name]

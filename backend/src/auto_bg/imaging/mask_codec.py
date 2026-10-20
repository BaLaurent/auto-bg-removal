import base64
from dataclasses import dataclass

import numpy as np
from pycocotools import mask as coco_mask


@dataclass(frozen=True)
class MaskRLE:
    """Format de transfert RLE COCO. `counts` est base64(bytes COCO),
    `size` est [hauteur, largeur]. Compatible pycocotools.
    """

    counts_b64: str
    height: int
    width: int


def encode(mask: np.ndarray) -> MaskRLE:
    """Encode un mask binaire H×W (uint8 ou bool) en RLE COCO base64."""
    if mask.ndim != 2:
        raise ValueError(f"mask doit être 2D, reçu {mask.shape}")
    arr = np.asfortranarray(mask.astype(np.uint8))
    rle = coco_mask.encode(arr)
    counts_bytes: bytes = rle["counts"] if isinstance(rle["counts"], bytes) else rle["counts"].encode()
    return MaskRLE(
        counts_b64=base64.b64encode(counts_bytes).decode("ascii"),
        height=int(rle["size"][0]),
        width=int(rle["size"][1]),
    )


def decode(mask_rle: MaskRLE) -> np.ndarray:
    """Decode un MaskRLE en numpy H×W uint8 (0 ou 1)."""
    counts = base64.b64decode(mask_rle.counts_b64.encode("ascii"))
    rle = {"counts": counts, "size": [mask_rle.height, mask_rle.width]}
    return coco_mask.decode(rle).astype(np.uint8)

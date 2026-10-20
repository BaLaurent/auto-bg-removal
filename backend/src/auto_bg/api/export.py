import base64

from fastapi import APIRouter, HTTPException, Request, Response

from ..imaging import MaskRLE, compose_rgba, decode as decode_mask, encode_png
from .deps import get_session
from .schemas import ExportRequest

router = APIRouter(tags=["export"])


@router.post("/sessions/{session_id}/export")
async def export(
    request: Request,
    session_id: str,
    body: ExportRequest,
) -> Response:
    get_session(request, session_id)
    image = request.app.state.session_images.get(session_id)
    if image is None:
        raise HTTPException(status_code=410, detail="image_unavailable")

    h, w = body.mask.size
    if (h, w) != image.shape[:2]:
        raise HTTPException(
            status_code=400,
            detail=f"mask_size_mismatch: image is {image.shape[:2]}, mask is {(h, w)}",
        )

    # b64 quoting tolerant
    counts_b64 = body.mask.counts
    try:
        base64.b64decode(counts_b64.encode("ascii"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_mask_counts")

    rle = MaskRLE(counts_b64=counts_b64, height=h, width=w)
    mask = decode_mask(rle)
    rgba = compose_rgba(image, mask)
    png = encode_png(rgba)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="cutout-{session_id}.png"'},
    )

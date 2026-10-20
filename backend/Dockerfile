FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HYDRA_FULL_ERROR=1 \
    # Réduit la fragmentation VRAM (utile pour AutomaticMaskGenerator)
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

WORKDIR /app

# build-essential nécessaire pour compiler les extensions CUDA de SAM 2
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git curl ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

ARG INSTALL_SAM2=0

# `pip install -e .` doit pouvoir scanner src/ (déclaré comme racine des packages
# dans pyproject.toml), donc on copie src AVANT l'install. Le mount runtime dans
# docker-compose remplace ce src par le vivant pour le hot-reload.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip
RUN if [ "$INSTALL_SAM2" = "1" ]; then \
        pip install -e ".[dev,sam2]"; \
    else \
        pip install -e ".[dev]"; \
    fi

# SAM 2 est installé séparément avec --no-build-isolation pour utiliser le torch
# déjà présent dans l'image (sinon pip recompile la CUDA toolchain dans un venv
# isolé, ~8 min). Le repo Meta déclare son name comme « SAM-2 » (avec tiret) mais
# expose le module Python `sam2` ; on installe sans #egg= pour éviter le mismatch.
RUN if [ "$INSTALL_SAM2" = "1" ]; then \
        pip install --no-build-isolation \
            "git+https://github.com/facebookresearch/sam2.git@main"; \
    fi

EXPOSE 8000

CMD ["uvicorn", "auto_bg.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "src"]

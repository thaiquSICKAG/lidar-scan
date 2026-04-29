# ----------------------------------------
# Stage 1: Build sick_scan_xd C++ library
# ----------------------------------------
FROM ubuntu:22.04 AS backend-builder

ENV ROS_VERSION=0
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
  git \
  build-essential \
  cmake \
  gdb \
  ninja-build \
  && rm -rf /var/lib/apt/lists/*

RUN git clone -b 3.9.0 https://github.com/SICKAG/sick_scan_xd.git /workspace/sick_scan_xd \
  && mkdir -p /workspace/build \
  && cd /workspace/build \
  && rm -rf ./* \
  && export ROS_VERSION=0 \
  && cmake -DROS_VERSION=0 -DLDMRS=0 -G "Unix Makefiles" ../sick_scan_xd \
  && make -j4 \
  && make install

# ----------------------------------------
# Stage 2: Build Angular frontend
# ----------------------------------------
FROM --platform=$BUILDPLATFORM node:24-slim AS frontend-builder
WORKDIR /web
# Copy package manifests first for caching
COPY web/package*.json ./
RUN npm ci
# Copy rest of frontend source and build
COPY web/ ./
RUN npm run build -- --configuration production

# ----------------------------------------
# Stage 3: Cython compilation (source → .so)
# ----------------------------------------
FROM python:3.12-slim-bookworm AS cython-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir cython setuptools

WORKDIR /src
COPY app/ ./app/
COPY main.py build_cython.py ./

# Compile .py → .so, then strip source for compiled modules only.
# __init__.py files are always kept so package discovery still works.
# Files with Pydantic/ORM models are auto-skipped by the build script
# and remain as .py (their metaclass magic is incompatible with Cython).
RUN python build_cython.py build_ext --inplace \
  && find app/ -name '*.so' -print \
     | sed 's/\.cpython-[^.]*\.so$/.py/' \
     | xargs rm -f \
  && find app/ -name '*.c' -delete \
  && rm -f build_cython.py \
  && rm -rf build/

# ----------------------------------------
# Stage 4: Install & strip Python dependencies
# ----------------------------------------
FROM python:3.12-slim-bookworm AS deps-builder

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --compile-bytecode \
  #
  # ── Strip packages only needed for Open3D visualization / notebooks ──
  # These are transitive deps of open3d-cpu that the app never imports.
  # The app uses Open3D purely for geometry/registration, not visualization.
  #
  && cd .venv/lib/python3.12/site-packages \
  && rm -rf \
     plotly _plotly_utils dash dash_core_components dash_html_components dash_table \
     scikit_learn sklearn scikit_learn.libs joblib threadpoolctl.py \
     matplotlib matplotlib_inline mpl_toolkits pylab.py \
     pandas \
     fontTools \
     jedi parso \
     IPython ipython_pygments_lexers.py pexpect ptyprocess \
     prompt_toolkit wcwidth \
     pygments \
     stack_data executing asttokens pure_eval \
     kiwisolver kiwisolver*.so cycler contourpy pyparsing \
     traitlets decorator.py \
     narwhals retrying.py \
     flask werkzeug blinker itsdangerous \
     widgetsnbextension ipywidgets jupyterlab_widgets jupyter.py jupyter_core \
     nbformat comm js \
     setuptools _distutils_hack distutils-precedence.pth \
     nest_asyncio.py \
  && cd /app \
  && find .venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
  && find .venv -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true \
  && find .venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
  && find .venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true \
  #
  # ── Strip debug symbols from native extensions (~40 MB) ──
  #
  && find .venv -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
  #
  # ── Patch Open3D to make plotly/dash imports optional ──
  # Open3D unconditionally imports draw_plotly at init, but we only use
  # geometry/registration — not visualization.  Wrap in try/except.
  #
  && python -c "\
p='.venv/lib/python3.12/site-packages/open3d/__init__.py'; \
t=open(p).read(); \
t=t.replace('import open3d.visualization','try:\n    import open3d.visualization\nexcept ImportError:\n    pass'); \
t=t.replace('import open3d.ml','try:\n    import open3d.ml\nexcept ImportError:\n    pass'); \
open(p,'w').write(t)"

# ----------------------------------------
# Stage 5: Final Python Application
# ----------------------------------------
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONPATH=/app

WORKDIR /app

# Runtime C libraries required by Open3D and NumPy
RUN apt-get update && apt-get install -y --no-install-recommends \
  libegl1 \
  libgl1 \
  libgomp1 \
  && rm -rf /var/lib/apt/lists/*

# ✅ Pre-built, stripped venv — no uv, pip, or build tools in final image
COPY --from=deps-builder /app/.venv/ ./.venv/

# ✅ C++ artifacts grouped — they change together
COPY --from=backend-builder \
  /workspace/build/libsick_scan_xd_shared_lib.so \
  /workspace/build/sick_generic_caller \
  /workspace/build/sick_scan_xd_api_test \
  ./build/
COPY --from=backend-builder /workspace/sick_scan_xd/launch/ ./launch/

# ✅ Compiled app: .so extensions + __init__.py stubs + non-Python assets
COPY main.py .
COPY --from=cython-builder /src/app/ ./app/

# ✅ Static frontend assets
COPY --from=frontend-builder /web/dist/web/browser/ ./app/static/

EXPOSE 8005
CMD ["/app/.venv/bin/python", "main.py"]
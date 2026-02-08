# Jupyter container

Docker image for the pricing project's Jupyter environment. Used by `docker-compose` from the repo root.

## What it does

- **Base:** `jupyter/scipy-notebook:latest`
- **Auth:** Disabled (no token/password) so http://localhost:8888 opens straight to JupyterLab. For local development only.
- **Default notebook:** Opens `demo.ipynb` on load. The demo notebook (in this repo at `jupyter/demo.ipynb`) is copied into the image at `/home/jovyan/demo.ipynb`. The file browser shows only the `client` folder and `demo.ipynb` at root (no `work` or `jupyter` folders).
- **Client:** The `client` package is installed at startup from the mounted volume (`/home/jovyan/client`). The repo’s `client/` directory must be mounted there (done in docker-compose).

## Build and run

From the repo root:

```bash
docker-compose up --build
```

Jupyter is available at http://localhost:8888.

## Build only (no compose)

From the repo root:

```bash
docker build -f jupyter/Dockerfile -t pricing-jupyter .
```

Run with a client mount:

```bash
docker run -p 8888:8888 -v "$(pwd)/client:/home/jovyan/client" pricing-jupyter
```

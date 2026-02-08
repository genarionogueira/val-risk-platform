# Jupyter container for the pricing project: client pre-installed, no auth, opens to demo notebook.
# Expects build context = repo root. Client directory is mounted at /home/jovyan/client (docker-compose).

FROM jupyter/scipy-notebook:latest

# No token/password so localhost goes straight to JupyterLab (local dev only).
ENV JUPYTER_ENABLE_LAB=yes \
    JUPYTER_TOKEN=''

# Copy demo notebook to root so JupyterLab shows only: client/ folder + demo.ipynb.
COPY jupyter/demo.ipynb /home/jovyan/demo.ipynb
USER root
RUN fix-permissions /home/jovyan/demo.ipynb && \
    rm -rf /home/jovyan/work /home/jovyan/jupyter 2>/dev/null || true
# ipywidgets for live blotter in the real-time demo.
RUN pip install --no-cache-dir ipywidgets
USER jovyan

# Install client from mounted volume and start Jupyter with no auth and default URL to demo.
# Remove work/jupyter dirs at startup so the file browser shows only client/ and demo.ipynb.
CMD bash -c "rm -rf /home/jovyan/work /home/jovyan/jupyter 2>/dev/null; \
             pip install -e /home/jovyan/client && \
             start-notebook.sh \
               --IdentityProvider.token='' \
               --ServerApp.password='' \
               --ServerApp.default_url='/lab/tree/demo.ipynb'"

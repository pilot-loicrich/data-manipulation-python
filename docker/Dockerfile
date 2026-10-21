FROM spark:4.2.0-python3

USER root

RUN python3 -m pip install --no-cache-dir \
    jupyterlab \
    pandas \
    numpy \
    pyarrow \
    openpyxl

WORKDIR /workspace

EXPOSE 8888 4040

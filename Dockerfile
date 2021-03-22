FROM pytorch/pytorch:1.7.1-cuda11.0-cudnn8-runtime

RUN apt-get update && apt-get install -y tzdata
ENV TZ=Europe/Ljubljana
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN  mkdir /pipeline
WORKDIR /pipeline
COPY setup.py /pipeline/
COPY marcell_sl_pipeline /pipeline/marcell_sl_pipeline

RUN pip install --no-cache-dir .

RUN python -c "import classla; classla.download('sl')"

WORKDIR /
RUN rm -rf /pipeline/

RUN pip install --no-cache-dir flask gunicorn && \
    mkdir /api
WORKDIR /api
COPY api.py /api/

# TODO: Fix preloading. For now every worker loads its seperate models in memory.
CMD ["gunicorn", "--bind", "0.0.0.0:80", "-w", "1", "--timeout", "1800", "--access-logfile", "-",  "api:app"]

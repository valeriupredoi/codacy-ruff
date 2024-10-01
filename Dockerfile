FROM python:3.11-alpine3.20
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY src/codacy_ruff.py codacy_ruff.py
COPY src/codacy_ruff_test.py codacy_ruff_test.py
COPY docs /docs
RUN adduser -u 2004 -D docker
RUN chown -R docker:docker /docs /home/docker
USER docker
ENTRYPOINT [ "python" ]
CMD [ "codacy_ruff.py" ]

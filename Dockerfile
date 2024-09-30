FROM python:3.11-alpine3.20
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
COPY src/codacy_prospector.py codacy_prospector.py
COPY src/codacy_prospector_test.py codacy_prospector_test.py
COPY docs /docs
RUN adduser -u 2004 -D docker
RUN chown -R docker:docker /docs /home/docker
USER docker
ENTRYPOINT [ "python" ]
CMD [ "codacy_prospector.py" ]

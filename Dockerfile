FROM alpine #TODO: review

RUN mkdir -p /dir #just if needed
WORKDIR /dir #just if needed

COPY file /dir
COPY file /dir

RUN bash install.sh
RUN bash run.sh

EXPOSE 8080

CMD["npm","start"] # si npm se para, se parará el contenedor

# finally:
# docker build -t wppParser:latest .
#                           ^tag^  ^Dockerfile dir^
# once the image has been generated:
# docker run -p 8080:8080 wppParser:latest

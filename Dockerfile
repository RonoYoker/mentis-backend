# Use Ubuntu as the base image
FROM ubuntu:20.04
LABEL maintainer="Mentis Team"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHON_VERSION=3.8
RUN apt-get update && apt-get install -y \
    wget \
    git \
    make \
    python3-setuptools \
    python3-pip \
    python3-dev \
    zlib1g-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    libpq-dev \
    libsqlite3-dev \
    libexpat1-dev \
    libbz2-dev \
    libffi-dev \
    libxslt1-dev \
    libxml2-dev \
    xmlsec1 \
    libxmlsec1-dev \
    perl \
    libpcre3-dev \
    libtool \
    nginx \
    supervisor \
    ffmpeg \
    xfonts-75dpi \
    xfonts-base \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install supervisor
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org supervisor && \
    mkdir -p /var/log/supervisor /etc/supervisord.d /logs /opt/logs

EXPOSE 80
EXPOSE 8080

# # Install librdkafka with ssl and sasl
# RUN \
#  cd /opt && \
#  wget https://github.com/edenhill/librdkafka/archive/v1.4.2.tar.gz -O - | tar -xvz && \
#  cd librdkafka-1.4.2 && \
#  ./configure --enable-ssl --enable-sasl --prefix=/usr && \
#  make && \
#  make install && ldconfig


RUN \
 cd /opt && \
 wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz  && \
 tar xvf Python-3.10.0.tgz && \
 cd /opt/Python-3.10.0 && \
 ./configure --enable-shared --with-system-ffi --with-system-expat --enable-unicode=ucs4 --prefix=/usr/local/python3.10 LDFLAGS="-L/usr/local/python3.10/lib -Wl,--rpath=/usr/local/python3.10/lib"  && \
 make && \
 make altinstall && \
 rm -f /etc/localtime && \
 ln -s /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
 rm -Rf Python-3.10.0.tgz /opt/Python-3.10.0

# RUN \
#  cd /opt && \
#  git clone https://deploy-goibibo:g01b1b098@github.com/goibibo/goibibo_saml_service_provider.git saml_service_provider && \
#  rm -Rf /opt/saml_service_provider/tests

WORKDIR /usr/local/mentis/mentis/

# ENV PYTHONPATH /usr/local/goibibo/flock/flock_proj/flock_proj/:/usr/local/goibibo/flock:$PYTHONPATH


COPY mentis_proj/config/supervisord /etc/rc.d/init.d/supervisord
ADD  mentis_proj/config/services/* /etc/supervisord.d/
COPY mentis_proj/config/nginx/nginx.conf /etc/nginx/nginx.conf
COPY mentis_proj/config/nginx/uwsgi_params /etc/nginx/uwsgi_params
COPY mentis_proj/config/nginx/uwsgi_params /etc/nginx/conf.d/uwsgi_params
COPY mentis_proj/config/uwsgi/mentis_uwsgi.ini /etc/mentis_uwsgi.ini
COPY mentis_proj/config/uwsgi/mentis.conf /etc/nginx/conf.d/mentis.conf
# COPY mentis_proj/config/newrelic/* /etc/newrelic/

COPY mentis_proj/config/pip/requirements.txt /etc/pip/requirements.txt
RUN /usr/local/python3.10/bin/pip3.10 install -r /etc/pip/requirements.txt

# RUN /usr/local/python3.8/bin/pip3.8 install --no-binary :all: confluent-kafka[avro]

# frequent changes may happen in this file.
# COPY flock_proj/config/pip/requirements_github.txt /etc/pip/requirements_github.txt
# RUN \
#   /usr/local/python3.8/bin/pip3.8 install -r /etc/pip/requirements_github.txt


COPY ./ /usr/local/mentis/mentis

RUN \
  /usr/local/python3.10/bin/python3.10  /usr/local/mentis/mentis/mentis_proj/manage.py collectstatic && \
  chmod 755 /etc/rc.d/init.d/supervisord

#CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisord.d/mentis_web_service.conf"]

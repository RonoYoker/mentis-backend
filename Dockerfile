FROM centos:7
LABEL maintainer="Creditas Team"

RUN \
 yum install -y epel-release && \
 yum install -y wget \
                git \
                which \
                make \
                python-setuptools \
                python-pip \
                python-dev \
                zlib-devel \
                openssl-devel \
                mysql-devel \
                python-devel \
                gcc-c++ \
                snappy-devel \
                gcc \
                postgresql \
                postgresql-devel \
                sqlite-devel \
                expat-devel \
                bzip2-devel \
                libffi-devel \
                zlib-devel \
                libxslt-devel \
                libxml2-devel \
                python-argparse \
                xmlsec1-devel \
                xmlsec1-openssl-devel \
                libtool-ltdl-devel && \
 yum install -y nginx && \
 yum install -y screen && \
 pip install supervisor && \

 mkdir -p /var/log/supervisor /etc/supervisord.d /logs /opt/logs && \
 yum clean all

EXPOSE 80

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
 wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz  && \
 tar xvf Python-3.8.0.tgz && \
 cd /opt/Python-3.8.0 && \
 ./configure --enable-shared --with-system-ffi --with-system-expat --enable-unicode=ucs4 --prefix=/usr/local/python3.8 LDFLAGS="-L/usr/local/python3.8/lib -Wl,--rpath=/usr/local/python3.8/lib"  && \
 make && \
 make altinstall && \
 rm -f /etc/localtime && \
 ln -s /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
 rm -Rf Python-3.8.0.tgz /opt/Python-3.8.0

# RUN \
#  cd /opt && \
#  git clone https://deploy-goibibo:g01b1b098@github.com/goibibo/goibibo_saml_service_provider.git saml_service_provider && \
#  rm -Rf /opt/saml_service_provider/tests

WORKDIR /usr/local/creditas/Onyx/

# ENV PYTHONPATH /usr/local/goibibo/flock/flock_proj/flock_proj/:/usr/local/goibibo/flock:$PYTHONPATH

COPY onyx_proj/config/supervisord /etc/rc.d/init.d/supervisord
ADD  onyx_proj/config/services/* /etc/supervisord.d/
COPY onyx_proj/config/uwsgi/onyx.conf /etc/nginx/nginx.conf
COPY onyx_proj/config/nginx/uwsgi_params /etc/nginx/uwsgi_params
COPY onyx_proj/config/nginx/uwsgi_params /etc/nginx/conf.d/uwsgi_params
COPY onyx_proj/config/uwsgi/onyx_uwsgi.ini /etc/onyx_uwsgi.ini
COPY onyx_proj/config/uwsgi/onyx.conf /etc/nginx/conf.d/onyx.conf
# COPY flock_proj/config/newrelic/* /etc/newrelic/




COPY onyx_proj/config/pip/requirements.txt /etc/pip/requirements.txt
RUN /usr/local/python3.8/bin/pip3.8 install -r /etc/pip/requirements.txt

# RUN /usr/local/python3.8/bin/pip3.8 install --no-binary :all: confluent-kafka[avro]

# frequent changes may happen in this file.
# COPY flock_proj/config/pip/requirements_github.txt /etc/pip/requirements_github.txt
# RUN \
#   /usr/local/python3.8/bin/pip3.8 install -r /etc/pip/requirements_github.txt


COPY ./ /usr/local/creditas/Onyx

RUN \
#   /usr/local/python3.8/bin/python3.8  /usr/local/creditas/Onyx/onyx_proj/manage.py collectstatic && \
  chmod 755 /etc/rc.d/init.d/supervisord

#CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisord.d/onyx_web_service.conf"]

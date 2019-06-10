FROM ubuntu

RUN apt-get update
RUN apt-get install -y git python python-pip libglib2.0-dev libyaml-dev libpython2.7-dev usbutils
RUN pip install setuptools

RUN git clone https://joshuabico@bitbucket.org/icoteq-eng/arribada_python_tools.git
WORKDIR /arribada_python_tools
RUN python setup.py install
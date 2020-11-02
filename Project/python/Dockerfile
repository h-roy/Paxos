FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo iptables

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y software-properties-common python3.8 python3-pip

# Create work directory
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt

# Get the role and id of the process from env
ENV APP_ROLE ''
ENV ID ''

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
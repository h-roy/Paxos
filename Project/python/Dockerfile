FROM python:3.8

# Create work directory
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# Get the role and id of the process from env
ENV APP_ROLE ''
ENV ID ''

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
CMD python ./paxos.py ${APP_ROLE} ${ID}
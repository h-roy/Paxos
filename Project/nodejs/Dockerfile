FROM node:alpine

# Create work directory
WORKDIR /app

# copy the content of the local src directory to the working directory
COPY package.json .

# Install app dependencies
RUN yarn install

# Get the role of the process from env
ENV APP_ROLE ''
ENV ID ''

# copy the content of the local src directory to the working directory
COPY . .

# Build and run the app
CMD node paxos ${APP_ROLE} ${ID}
# CMD node ${APP_ROLE}.js ${ID}

# Use an official Node.js runtime as the base image for the build stage
FROM node:14 as build

# Set the working directory in the Docker image
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install the project dependencies
RUN npm install

# Copy the rest of the project files to the working directory
COPY . .

# Compile the TypeScript code
RUN npm run build

# Start a new stage for the production image
FROM node:14-alpine

LABEL org.opencontainers.image.source https://github.com/BelgianNoise/dl-utils

# Set the working directory
WORKDIR /usr/src/app

# Copy only the built application and the necessary production dependencies from the build stage
COPY --from=build /usr/src/app/dist ./dist
COPY --from=build /usr/src/app/node_modules ./node_modules

ENV POSTGRES_USERNAME=
ENV POSTGRES_PASSWORD=
ENV POSTGRES_HOST=
ENV POSTGRES_PORT=
ENV POSTGRES_DATABASE=

ENV AUTH_SECRET=

# Expose port 3000 for the application
EXPOSE 3000

# Start the application
CMD [ "node", "dist/index.js" ]
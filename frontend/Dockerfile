FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --only=production && npm install -D react-scripts

# Copy source code
COPY . .

# Build optimization
ENV REACT_APP_API_URL=http://localhost:8000
ENV GENERATE_SOURCEMAP=false

# Build app
RUN npm run build

# Serve with nginx
FROM node:18-alpine
RUN npm install -g serve
WORKDIR /app
COPY --from=0 /app/build .

EXPOSE 3000

CMD ["serve", "-s", ".", "-l", "3000"]

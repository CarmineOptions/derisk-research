FROM node:20-alpine

WORKDIR /app

COPY package*.json .
COPY tsconfig.json .
COPY tsconfig.node.json .
COPY tsconfig.app.json .


RUN npm install


COPY . .


EXPOSE 5173


CMD ["npm", "run", "dev"]
FROM node:20

WORKDIR /app

COPY backend/package*.json ./
RUN npm install

COPY backend/ .

EXPOSE 8000

CMD ["npm","start"]

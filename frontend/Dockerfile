FROM node:22

WORKDIR /app

# Dependencies
COPY package.json .
RUN npm install

# Copy code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
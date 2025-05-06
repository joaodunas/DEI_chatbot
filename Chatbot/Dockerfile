FROM node:22.14-alpine

WORKDIR /app

COPY package.json .

RUN npm install
RUN npm install gpt-tokenizer

RUN npm i -g serve

COPY . .

RUN npm run build  

EXPOSE 80

CMD [ "serve", "-s", "dist", "-l", "80" ]
FROM node:lts-alpine 

ARG ENV
ENV ENV=${ENV}

# install simple http server for serving static content 
RUN npm install -g http-server 
# make the 'app' folder the current working directory 
WORKDIR /app
# copy both 'package.json' and 'package-lock.json' (if available) 
COPY package*.json ./ 
# install project dependencies 
RUN npm install 
# copy project files and folders to the current working directory (i.e. 'app' folder) 
COPY . . 
# build app for production with minification 
RUN npm run build 
EXPOSE 8080
CMD echo VUE_APP_ENV=${ENV} > .env && npm run serve
#CMD [ "npm", "run", "serve"]

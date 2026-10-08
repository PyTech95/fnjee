FROM node:20-alpine AS build
WORKDIR /app

ARG SITE_URL
RUN test -n "$SITE_URL" || (echo "SITE_URL build arg is required (e.g. https://fnjee.com)" && exit 1)
ENV REACT_APP_BACKEND_URL=$SITE_URL CI=false GENERATE_SOURCEMAP=false

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --network-timeout 600000

COPY . .
RUN rm -f .env && \
    sed -i "s#https://hardened-quiz-app.preview.emergentagent.com#${SITE_URL}#g" \
      public/index.html public/sitemap.xml public/robots.txt && \
    yarn build

FROM caddy:2-alpine
COPY --from=build /app/build /srv
COPY Caddyfile /etc/caddy/Caddyfile

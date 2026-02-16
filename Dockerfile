FROM node:22-alpine
RUN corepack enable && corepack prepare pnpm@10.28.2 --activate
RUN apk add --no-cache git bash
WORKDIR /app
EXPOSE 9000
CMD ["/bin/bash"]

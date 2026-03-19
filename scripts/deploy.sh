#!/bin/bash
# Deploy latest main branch to EC2.
# Always does a --no-cache build so cached Docker layers never serve stale code.
set -e

EC2="ubuntu@18.191.229.137"
KEY="~/.ssh/rag-app-key.pem"

ssh -i $KEY $EC2 "
  cd ~/rag-article-app &&
  git pull origin main &&
  docker-compose down &&
  docker-compose build --no-cache &&
  docker-compose up -d
"

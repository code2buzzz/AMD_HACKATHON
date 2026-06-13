#!/bin/bash

set -e

echo "Starting Kafka broker..."

cd kafka/kafka_broker

docker rm -f kafka-fraud-broker || true
docker compose up -d

echo "Waiting for Kafka to initialize..."
sleep 20

echo "Starting producer..."

cd ../..

python3 -m kafka.producer
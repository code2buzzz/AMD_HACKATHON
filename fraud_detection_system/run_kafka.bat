@echo off

echo Starting Kafka broker...

cd kafka\kafka_broker
docker rm -f kafka-fraud-broker
docker compose up -d

echo Waiting for Kafka to initialize...
timeout /t 20 /nobreak > nul

echo Starting producer...

cd ..\..
python -m kafka.producer

pause
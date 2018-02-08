#!/bin/bash
docker build -f ./DockerfileU11 -t kdvn/ubuntu:o11 .
docker push kdvn/ubuntu:o11

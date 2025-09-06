#!/bin/bash

# This script starts the API service
cd src
uvicorn api_service:app --reload 
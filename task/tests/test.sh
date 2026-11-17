#!/bin/sh
set -eu
chmod 700 /tests
chmod 600 /tests/grade.py
chmod 644 /app/pipeline.py
python /tests/grade.py /app/pipeline.py

#!/bin/bash
# Apache Jena Fuseki setup and load script for EFO ontologies
#
# Prerequisites:
#   - Apache Jena Fuseki installed (https://jena.apache.org/download/)
#   - FUSEKI_HOME environment variable set, or Fuseki in PATH
#
# Usage:
#   ./run_fuseki.sh start     # Start Fuseki server
#   ./run_fuseki.sh load      # Load EFO ontologies into dataset
#   ./run_fuseki.sh stop      # Stop Fuseki server
#   ./run_fuseki.sh query     # Run validation queries

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$BASE_DIR/data"
IMPORTS_DIR="$BASE_DIR/imports"
SPARQL_DIR="$BASE_DIR/sparql"

DATASET_NAME="efo"
FUSEKI_PORT="${FUSEKI_PORT:-3030}"
FUSEKI_URL="http://localhost:$FUSEKI_PORT"

# Check if Fuseki is available
check_fuseki() {
    if command -v fuseki-server &> /dev/null; then
        return 0
    elif [ -n "$FUSEKI_HOME" ] && [ -x "$FUSEKI_HOME/fuseki-server" ]; then
        return 0
    else
        echo "Error: Apache Jena Fuseki not found."
        echo "Please install Fuseki or set FUSEKI_HOME environment variable."
        echo "Download: https://jena.apache.org/download/"
        exit 1
    fi
}

start_fuseki() {
    echo "Starting Fuseki server on port $FUSEKI_PORT..."
    if [ -n "$FUSEKI_HOME" ]; then
        "$FUSEKI_HOME/fuseki-server" --port=$FUSEKI_PORT --update --mem /$DATASET_NAME &
    else
        fuseki-server --port=$FUSEKI_PORT --update --mem /$DATASET_NAME &
    fi
    echo "Fuseki PID: $!"
    echo "Waiting for server to start..."
    sleep 3

    # Check if server is running
    if curl -s "$FUSEKI_URL/\$/ping" > /dev/null 2>&1; then
        echo "Fuseki server started successfully."
        echo "Web UI: $FUSEKI_URL"
        echo "SPARQL endpoint: $FUSEKI_URL/$DATASET_NAME/sparql"
        echo "Update endpoint: $FUSEKI_URL/$DATASET_NAME/update"
    else
        echo "Warning: Server may not be fully ready yet. Check manually."
    fi
}

load_data() {
    echo "Loading EFO ontologies into Fuseki..."

    # Load DUL.owl (dependency)
    echo "[1/3] Loading DUL.owl..."
    curl -X POST "$FUSEKI_URL/$DATASET_NAME/data" \
        -H "Content-Type: application/rdf+xml" \
        --data-binary "@$IMPORTS_DIR/DUL.owl" \
        && echo " OK" || echo " FAILED"

    # Load EmoCore
    echo "[2/3] Loading EmoCore_iswc.ttl..."
    curl -X POST "$FUSEKI_URL/$DATASET_NAME/data" \
        -H "Content-Type: text/turtle" \
        --data-binary "@$DATA_DIR/EmoCore_iswc.ttl" \
        && echo " OK" || echo " FAILED"

    # Load BasicEmotions (EFO-BE)
    echo "[3/3] Loading BE_iswc.ttl..."
    curl -X POST "$FUSEKI_URL/$DATASET_NAME/data" \
        -H "Content-Type: text/turtle" \
        --data-binary "@$DATA_DIR/BE_iswc.ttl" \
        && echo " OK" || echo " FAILED"

    echo ""
    echo "Data loading complete."
}

run_queries() {
    echo "Running validation SPARQL queries..."
    echo ""

    for query_file in "$SPARQL_DIR"/*.rq; do
        if [ -f "$query_file" ]; then
            echo "=== $(basename "$query_file") ==="
            curl -s -X POST "$FUSEKI_URL/$DATASET_NAME/sparql" \
                -H "Accept: text/csv" \
                --data-urlencode "query@$query_file"
            echo ""
            echo ""
        fi
    done
}

stop_fuseki() {
    echo "Stopping Fuseki server..."
    pkill -f "fuseki-server" 2>/dev/null || echo "No running Fuseki process found."
}

case "${1:-help}" in
    start)
        check_fuseki
        start_fuseki
        ;;
    load)
        load_data
        ;;
    query)
        run_queries
        ;;
    stop)
        stop_fuseki
        ;;
    *)
        echo "Usage: $0 {start|load|query|stop}"
        echo ""
        echo "Commands:"
        echo "  start  - Start Fuseki server with in-memory dataset"
        echo "  load   - Load EFO ontologies (EmoCore, BE) into Fuseki"
        echo "  query  - Run validation SPARQL queries"
        echo "  stop   - Stop Fuseki server"
        ;;
esac

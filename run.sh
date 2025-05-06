set -e

echo "🔧 Building and starting containers..."
docker compose up --build -d

echo "✅ Services are up!"
#!/bin/bash
# Ultimate StacksOrbit Deployment Script
# One-command deployment for any Stacks project

echo "🚀 StacksOrbit - Ultimate Deployment Tool"
echo "=========================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required but not installed. Aborting."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required but not installed. Aborting."; exit 1; }
command -v clarinet >/dev/null 2>&1 || { echo "❌ Clarinet required but not installed. Aborting."; exit 1; }

echo "✅ Prerequisites check passed"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pnpm install

echo "✅ Dependencies installed"

# Setup configuration
echo "⚙️  Running setup wizard..."
python stacksorbit_cli.py setup

# Run diagnostics
echo "🔍 Running comprehensive diagnostics..."
python stacksorbit_cli.py diagnose

# Deploy to testnet
echo "🚀 Deploying to testnet..."
python stacksorbit_cli.py deploy --dry-run

echo "🔍 Dry run complete. Ready for actual deployment?"
read -p "Deploy to testnet? (y/n): " confirm

if [ "$confirm" = "y" ]; then
    python stacksorbit_cli.py deploy --batch-size 5

    # Start monitoring
    echo "📊 Starting monitoring dashboard..."
    python stacksorbit_cli.py dashboard &
    DASHBOARD_PID=$!

    # Verify deployment
    echo "🔍 Verifying deployment..."
    python stacksorbit_cli.py verify --comprehensive

    echo "✅ Deployment complete!"
    echo "📊 Dashboard running in background (PID: $DASHBOARD_PID)"
    echo "🛑 Press Ctrl+C to stop dashboard"

    # Keep dashboard running
    wait $DASHBOARD_PID
else
    echo "✅ Setup complete! Run 'python ultimate_stacksorbit.py deploy' when ready"
fi

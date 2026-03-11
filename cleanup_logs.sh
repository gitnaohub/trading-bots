#!/bin/bash
# Clean up old log files (keep last 30 days)

LOG_DIR="$HOME/trading/logs"
DAYS_TO_KEEP=30

echo "🧹 Cleaning up old log files..."
echo "Directory: $LOG_DIR"
echo "Keeping logs from last $DAYS_TO_KEEP days"
echo ""

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Log directory not found: $LOG_DIR"
    exit 1
fi

# Find and delete log files older than DAYS_TO_KEEP
DELETED_COUNT=$(find "$LOG_DIR" -name "*.log" -type f -mtime +$DAYS_TO_KEEP -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo "✅ Deleted $DELETED_COUNT old log file(s)"
else
    echo "✓ No old log files to delete"
fi

# Show current log directory size
TOTAL_SIZE=$(du -sh "$LOG_DIR" | cut -f1)
echo ""
echo "Current log directory size: $TOTAL_SIZE"

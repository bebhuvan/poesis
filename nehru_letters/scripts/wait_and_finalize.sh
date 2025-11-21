#!/bin/bash
# Wait for processing to complete and then run finalization

echo "Monitoring OCR processing..."
echo "Waiting for completion..."

# Wait for the combined file to be created
COMBINED_FILE="../ocr_outputs/final_processed/all_pages_combined.txt"

while true; do
    if [ -f "$COMBINED_FILE" ]; then
        # File exists, wait a bit more to ensure writing is complete
        sleep 5
        
        # Check file size hasn't changed (writing is done)
        SIZE1=$(stat -f%z "$COMBINED_FILE" 2>/dev/null || stat -c%s "$COMBINED_FILE" 2>/dev/null)
        sleep 2
        SIZE2=$(stat -f%z "$COMBINED_FILE" 2>/dev/null || stat -c%s "$COMBINED_FILE" 2>/dev/null)
        
        if [ "$SIZE1" = "$SIZE2" ]; then
            echo ""
            echo "✓ Processing complete!"
            echo "Starting finalization..."
            python3 finalize_extraction.py
            exit 0
        fi
    fi
    
    sleep 5
done

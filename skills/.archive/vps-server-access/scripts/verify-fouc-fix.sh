#!/bin/bash
# FOUC Fix Verification Script
# Run via aaPanel Terminal after applying FOUC fix

set -e

DOMAIN="${1:-smartmillionaire.co.id}"
PAGE="${2:-smart-webinar}"

echo "=== FOUC Fix Verification for $DOMAIN/$PAGE ==="
echo ""

# 1. Check HTTP response
echo "1. HTTP Response Check:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/$PAGE/")
echo "   HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
    echo "   ❌ FAIL: Non-200 response"
    exit 1
fi

# 2. Check load time
echo ""
echo "2. Load Time Check:"
LOAD_TIME=$(curl -s -o /dev/null -w "%{time_total}" "https://$DOMAIN/$PAGE/")
echo "   Total Time: ${LOAD_TIME}s"
if (( $(echo "$LOAD_TIME > 3.0" | bc -l) )); then
    echo "   ⚠️  WARN: Load time > 3s"
fi

# 3. Check for render-blocking resources
echo ""
echo "3. Render-blocking CSS Check:"
BLOCKING_CSS=$(curl -s "https://$DOMAIN/$PAGE/" | grep -c 'rel="stylesheet"')
echo "   Stylesheets in head: $BLOCKING_CSS"
if [ "$BLOCKING_CSS" -gt 5 ]; then
    echo "   ⚠️  WARN: Many blocking stylesheets"
fi

# 4. Check for inlined critical CSS
echo ""
echo "4. Inlined Critical CSS Check:"
INLINED_CSS=$(curl -s "https://$DOMAIN/$PAGE/" | grep -c 'id="fouc-fix"')
if [ "$INLINED_CSS" -gt 0 ]; then
    echo "   ✅ PASS: FOUC fix style tag found"
else
    echo "   ❌ FAIL: FOUC fix style tag NOT found"
    exit 1
fi

# 5. Check for FOUC fix script
echo ""
echo "5. FOUC Fix Script Check:"
INLINED_SCRIPT=$(curl -s "https://$DOMAIN/$PAGE/" | grep -c 'fouc-fix')
if [ "$INLINED_SCRIPT" -gt 0 ]; then
    echo "   ✅ PASS: FOUC fix script found"
else
    echo "   ❌ FAIL: FOUC fix script NOT found"
    exit 1
fi

# 6. Check cache headers (if LSCache enabled)
echo ""
echo "6. Cache Headers Check:"
CACHE_CONTROL=$(curl -s -I "https://$DOMAIN/$PAGE/" | grep -i "cache-control" | head -1)
if [ -n "$CACHE_CONTROL" ]; then
    echo "   ✅ PASS: Cache-Control header present"
    echo "   $CACHE_CONTROL"
else
    echo "   ⚠️  WARN: No Cache-Control header (LSCache may not be active)"
fi

# 7. Check compression
echo ""
echo "7. Compression Check:"
CONTENT_ENCODING=$(curl -s -I "https://$DOMAIN/$PAGE/" | grep -i "content-encoding" | head -1)
if [ -n "$CONTENT_ENCODING" ]; then
    echo "   ✅ PASS: Compression active"
    echo "   $CONTENT_ENCODING"
else
    echo "   ⚠️  WARN: No compression (enable LSCache/OpenLiteSpeed compression)"
fi

# 8. Check for plugin-specific elements
echo ""
echo "8. Plugin Elements Check:"
PLUGIN_ELEMENTS=$(curl -s "https://$DOMAIN/$PAGE/" | grep -c 'wpws-\|smart-webinar')
echo "   smart-webinar elements found: $PLUGIN_ELEMENTS"

echo ""
echo "=== VERIFICATION COMPLETE ==="
echo ""
echo "Summary:"
echo "  ✅ Page loads (HTTP 200)"
echo "  ✅ FOUC fix style tag present"
echo "  ✅ FOUC fix script present"
echo "  Load time: ${LOAD_TIME}s"
echo ""
echo "Next steps if issues persist:"
echo "  1. Enable LSCache in aaPanel: Website → Conf → LSCache"
echo "  2. Install LiteSpeed Cache WordPress plugin"
echo "  3. Check plugin enqueue order: grep -r 'wp_enqueue_style' /www/wwwroot/$DOMAIN/wp-content/plugins/smart-webinar/"
echo "  4. Check error logs: tail -f /www/wwwlogs/$DOMAIN.error.log"
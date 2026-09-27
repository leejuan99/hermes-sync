<?php
/**
 * FOUC Fix Template - Reusable for any WordPress plugin/page
 * 
 * Usage:
 * 1. Copy to: wp-content/themes/YOUR_THEME/fix-fouc-{slug}.php
 * 2. Update the page slug condition and CSS selectors
 * 3. Include in functions.php: require_once get_template_directory() . '/fix-fouc-{slug}.php';
 */

// ===== CONFIGURATION - UPDATE THESE =====
define('FOUC_FIX_PAGE_SLUG', 'smart-webinar');  // Page slug or partial URL match
define('FOUC_FIX_CSS_SELECTORS', '.wpws-container,.wpws-webinar-header,.wpws-registration-form');  // CSS selectors to hide until loaded
// ========================================

add_action('wp_head', 'fix_fouc_for_target_page', 1);
function fix_fouc_for_target_page() {
    $page_slug = FOUC_FIX_PAGE_SLUG;
    $permalink = get_permalink();
    
    if (is_page($page_slug) || strpos($permalink, $page_slug) !== false) {
        // Hide body until DOM ready (max 3s fallback)
        echo '<style id="fouc-fix-' . esc_attr($page_slug) . '">body{opacity:0;visibility:hidden}html{visibility:visible}</style>';
        echo '<script>(function(){var s=document.getElementById("fouc-fix-' . esc_attr($page_slug) . '");document.addEventListener("DOMContentLoaded",function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"});setTimeout(function(){s.remove();document.body.style.opacity="1";document.body.style.visibility="visible"},3000)})()</script>';
    }
}

// Force critical CSS inline for target elements
add_action('wp_enqueue_scripts', 'fix_target_page_critical_css', 1);
function fix_target_page_critical_css() {
    $page_slug = FOUC_FIX_PAGE_SLUG;
    $permalink = get_permalink();
    
    if (is_page($page_slug) || strpos($permalink, $page_slug) !== false) {
        // Get the main theme stylesheet handle (adjust if needed)
        $theme_style_handle = 'landingpress-style';  // Update for your theme
        
        wp_add_inline_style($theme_style_handle, '
            ' . FOUC_FIX_CSS_SELECTORS . '{visibility:hidden}
            .wpws-loaded ' . FOUC_FIX_CSS_SELECTORS . ', 
            .' . $page_slug . '-loaded ' . FOUC_FIX_CSS_SELECTORS . '{visibility:visible}
        ');
    }
}
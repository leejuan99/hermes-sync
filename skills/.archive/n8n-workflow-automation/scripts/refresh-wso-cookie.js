const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const WSO_URL = 'https://www.wsodownloads.in/wp-login.php';
const COOKIE_FILE = path.join(__dirname, '..', '..', '..', '..', 'wso-cookies.json'); // Save to project root
const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

// Credentials - SET THESE AS ENV VARS
const WP_USER = process.env.WSO_WP_USER || 'your_username';
const WP_PASS = process.env.WSO_WP_PASS || 'your_password';

async function refreshCookies() {
  console.log('[INFO] Launching browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: USER_AGENT,
    viewport: { width: 1280, height: 720 }
  });

  const page = await context.newPage();

  try {
    // Navigate to login page
    console.log('[INFO] Navigating to login page...');
    await page.goto(WSO_URL, { waitUntil: 'networkidle', timeout: 30000 });

    // Fill login form
    console.log('[INFO] Filling credentials...');
    await page.fill('#user_login', WP_USER);
    await page.fill('#user_pass', WP_PASS);

    // Submit
    console.log('[INFO] Submitting login...');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
      page.click('#wp-submit')
    ]);

    // Verify login success
    const isLoggedIn = await page.$eval('body', el => 
      el.textContent.includes('Dashboard') || 
      el.textContent.includes('wp-admin') ||
      document.cookie.includes('wordpress_logged_in')
    ).catch(() => false);

    if (!isLoggedIn) {
      // Check for error message
      const errorText = await page.$eval('#login_error', el => el.textContent).catch(() => '');
      throw new Error(`Login failed: ${errorText || 'Unknown error'}`);
    }

    console.log('[INFO] Login successful!');

    // Get all cookies
    const cookies = await context.cookies();

    // Filter for WSO domain cookies
    const wsoCookies = cookies.filter(c => c.domain.includes('wsodownloads.in'));

    // Format for n8n HTTP Header Auth
    const cookieHeader = wsoCookies
      .map(c => `${c.name}=${c.value}`)
      .join('; ');

    // Save full cookie objects (for Playwright reuse)
    const cookieData = {
      updatedAt: new Date().toISOString(),
      cookieHeader: cookieHeader,
      cookies: wsoCookies
    };

    fs.writeFileSync(COOKIE_FILE, JSON.stringify(cookieData, null, 2));
    console.log(`[SUCCESS] Cookies saved to ${COOKIE_FILE}`);
    console.log(`[INFO] Cookie header length: ${cookieHeader.length} chars`);

    // Output for n8n credential update
    console.log('\n--- n8n Credential Update ---');
    console.log('Credential Type: HTTP Header Auth');
    console.log('Name: WSO Downloads Cookie');
    console.log('Header Name: Cookie');
    console.log('Header Value:');
    console.log(cookieHeader);

  } catch (error) {
    console.error('[ERROR]', error.message);
    // Take screenshot for debugging
    await page.screenshot({ path: path.join(__dirname, 'login-error.png'), fullPage: true });
    console.log('[INFO] Error screenshot saved to login-error.png');
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Run
refreshCookies();
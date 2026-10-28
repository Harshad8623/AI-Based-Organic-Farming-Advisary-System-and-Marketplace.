"""Browser regression check using an isolated temporary database and real CSRF.

Install requirements-browser.txt first. Uses the system Chromium when available.
No live services or payments are used; no application accounts are left behind.
"""
import argparse
from pathlib import Path
import os
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run_checks(base, executable, artifacts):
    errors, asset_errors = [], []
    with sync_playwright() as playwright:
        options = {'headless': True}
        if executable:
            options['executable_path'] = executable
        browser = playwright.chromium.launch(**options)
        contexts = []

        def new_page(mobile=False):
            context = browser.new_context(viewport={'width': 390 if mobile else 1440, 'height': 900},
                                          is_mobile=mobile, has_touch=mobile)
            contexts.append(context)
            page = context.new_page()
            page.set_default_timeout(10000)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: asset_errors.append(response.url)
                    if response.url.startswith(base + '/static/') and response.status >= 400 else None)
            page.on('dialog', lambda dialog: dialog.accept())
            return page

        def visit(page, path):
            response = page.goto(base + path, wait_until='networkidle')
            assert response and response.status == 200, f'{path}: {response.status if response else "no response"}'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), f'Overflow: {path} at {page.viewport_size}'

        def register(page, email, role):
            visit(page, '/auth/register')
            page.check('input[name="role"][value="' + role + '"]')
            page.fill('#name', 'Browser ' + role.title())
            page.fill('#email', email)
            page.fill('#location', 'Sambhajinagar, Maharashtra')
            page.fill('#password', 'Temporary-check-43!')
            page.fill('#confirm_password', 'Temporary-check-43!')
            page.locator('#registerForm button[type="submit"]').click()
            expect(page).to_have_url(base + '/auth/login')
            page.fill('#email', email)
            page.fill('#password', 'Temporary-check-43!')
            page.locator('form[action="/auth/login"] button[type="submit"]').click()
            expect(page).to_have_url(base + '/auth/' + role + '/dashboard')

        farmer = new_page()
        for width in (1440, 390, 320):
            farmer.set_viewport_size({'width': width, 'height': 900})
            for path in ('/', '/auth/register', '/auth/login', '/marketplace/', '/roadmap/', '/roadmap/tomato'):
                visit(farmer, path)
            visit(farmer, '/')
            if width < 768:
                farmer.locator('.mobile-menu-toggle').click()
                expect(farmer.locator('#main-navigation')).to_be_visible()
                expect(farmer.locator('.mobile-menu-toggle')).to_have_attribute('aria-expanded', 'true')
        for language in ('hi', 'mr', 'en'):
            farmer.locator('[data-lang="' + language + '"]').click()
            expect(farmer.locator('html')).to_have_attribute('lang', language)
            farmer.reload(wait_until='networkidle')
            expect(farmer.locator('html')).to_have_attribute('lang', language)
        farmer.set_viewport_size({'width': 1440, 'height': 1000})
        visit(farmer, '/')
        farmer.screenshot(path=str(artifacts / 'home-desktop.png'), full_page=True)
        register(farmer, 'farmer@browser.example', 'farmer')
        visit(farmer, '/marketplace/add')
        farmer.fill('#name', 'Browser organic tomatoes')
        farmer.fill('#price', '31.25')
        farmer.fill('#quantity', '10 kg')
        farmer.select_option('#category', 'Vegetables')
        farmer.fill('#description', 'Fresh tomatoes from the test farm.')
        farmer.locator('#addProductForm button[type="submit"]').click()
        expect(farmer).to_have_url(base + '/marketplace/my-products')
        expect(farmer.get_by_text('Browser organic tomatoes', exact=True)).to_be_visible()
        visit(farmer, '/farm-tools')
        farmer.fill('#task-title', 'Check drip irrigation')
        farmer.fill('#task-crop', 'Tomato field')
        farmer.locator('form[action="/farm-tools/tasks"] button[type="submit"]').click()
        expect(farmer.get_by_text('Check drip irrigation', exact=True)).to_be_visible()
        farmer.locator('[data-i18n="farm_mark_done"]').click()
        expect(farmer.locator('[data-i18n="farm_done"]')).to_be_visible()
        for kind, amount in [('expense','150.25'), ('income','500.50')]:
            farmer.select_option('#entry-kind', kind)
            farmer.fill('#entry-amount', amount)
            farmer.select_option('#entry-category', 'seeds' if kind == 'expense' else 'produce_sale')
            farmer.fill('#entry-note', 'Browser ' + kind)
            farmer.locator('form[action="/farm-tools/ledger"] button[type="submit"]').click()
        expect(farmer.get_by_text('₹350.25', exact=True)).to_be_visible()
        with farmer.expect_download() as download:
            farmer.locator('[data-i18n="farm_export"]').click()
        csv_path = artifacts / 'sample-ledger.csv'
        download.value.save_as(str(csv_path))
        assert '150.25' in csv_path.read_text(encoding='utf-8-sig')
        for width in (1440, 390, 320):
            farmer.set_viewport_size({'width':width, 'height':900})
            for path in ('/farm-tools','/auth/farmer/dashboard','/marketplace/my-products','/orders/farmer','/crop/','/disease/','/weather/','/chatbot/','/analytics/'):
                visit(farmer, path)
        visit(farmer, '/farm-tools')
        farmer.locator('[data-lang="mr"]').click()
        expect(farmer.locator('[data-i18n="farm_title"]')).to_have_text('माझ्या शेतीचे नियोजन')
        farmer.screenshot(path=str(artifacts / 'planner-mobile-marathi.png'), full_page=True)
        farmer.locator('[data-lang="en"]').click()
        visit(farmer, '/crop/')
        values = {'N':'80','P':'45','K':'40','temperature':'25','humidity':'65','ph':'6.5','rainfall':'150'}
        for key, value in values.items():
            farmer.fill('[name="' + key + '"]', value)
        farmer.locator('[data-i18n="crop_explore_button"]').click()
        expect(farmer.locator('[data-i18n="crop_demo_result"]')).to_be_visible()
        visit(farmer, '/weather/?city=Sambhajinagar')
        assert not farmer.locator('.display-4').count(), 'Unconfigured weather must not generate a temperature.'
        visit(farmer, '/chatbot/')
        farmer.select_option('#chatLanguage', 'mr')
        farmer.fill('#chatInput', '<img src=x onerror=alert(1)> पाणी')
        farmer.locator('#sendButton').click()
        expect(farmer.locator('#chatWindow')).to_contain_text('पाणी')
        expect(farmer.locator('#chatInput')).to_have_value('')
        assert farmer.locator('#chatWindow img').count() == 0
        farmer.route('**/chatbot/ask', lambda route: route.abort())
        farmer.fill('#chatInput', 'Keep this failed question')
        farmer.locator('#sendButton').click()
        expect(farmer.locator('#sendButton')).to_be_enabled()
        expect(farmer.locator('#chatInput')).to_have_value('Keep this failed question')
        farmer.unroute('**/chatbot/ask')

        buyer = new_page(mobile=True)
        register(buyer, 'buyer@browser.example', 'buyer')
        visit(buyer, '/marketplace/')
        form = buyer.locator('form[action^="/cart/add/"]').first
        form.locator('select[name="quantity"]').select_option('2')
        form.locator('button[type="submit"]').click()
        visit(buyer, '/cart/')
        expect(buyer.get_by_text('₹62.50', exact=True).first).to_be_visible()
        buyer.fill('#delivery-address', 'Test house, Sambhajinagar, Maharashtra 431001')
        buyer.locator('#cod-form button[type="submit"]').click()
        expect(buyer).to_have_url(base + '/orders/my')
        expect(buyer.locator('.badge-status')).to_contain_text('Pending')
        expect(buyer.locator('.order-body')).to_contain_text('2 kg')
        visit(farmer, '/orders/farmer')
        for status, label in [('accepted','farmer_orders_accept'),('shipped','farmer_orders_ship'),('delivered','farmer_orders_deliver')]:
            farmer.locator('[data-i18n="' + label + '"]').click()
            expect(farmer.locator('.badge-status.status-' + status)).to_be_visible()
        visit(buyer, '/orders/my')
        buyer.locator('a[href$="/rate"]').click()
        buyer.locator('label[for="star5"]').click()
        buyer.fill('textarea[name="review"]', 'Fresh produce and a clear order process.')
        buyer.locator('#submit-btn').click()
        expect(buyer).to_have_url(base + '/orders/my')
        expect(buyer.get_by_text('Fresh produce and a clear order process.')).to_be_visible()
        visit(farmer, '/marketplace/my-products')
        expect(farmer.get_by_text('8 kg', exact=True)).to_be_visible()
        for language in ('hi','mr','en'):
            buyer.locator('[data-lang="' + language + '"]').click()
            visit(buyer, '/orders/my')
            assert buyer.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        buyer.screenshot(path=str(artifacts / 'buyer-order-mobile.png'), full_page=True)
        assert not errors, f'Browser script errors: {errors}'
        assert not asset_errors, f'Missing assets: {asset_errors}'
        for context in contexts:
            context.close()
        browser.close()
    print('Browser checks passed: responsive pages at 320/390/1440px, EN/HI/MR persistence, real-CSRF accounts, planner/CSV, crop demo, safe chat + retry, buyer checkout → delivery → rating, exact stock, local assets.')
    print('Screenshots:', artifacts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser-executable', default=shutil.which('chromium'))
    parser.add_argument('--artifacts', type=Path, default=Path('/tmp/organic-farming-ui'))
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    python = ROOT / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        raise SystemExit('Create the project venv first (see README).')
    with tempfile.TemporaryDirectory(prefix='organic-farming-browser-') as directory:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        environment = dict(os.environ, APP_ENV='development', CHECK_DB=str(Path(directory)/'test.db'), CHECK_PORT=str(port))
        source = """import os
from app import create_app
app = create_app({'SQLALCHEMY_DATABASE_URI':'sqlite:///'+os.environ['CHECK_DB'],
 'SECRET_KEY':__import__('secrets').token_hex(32),'GEMINI_API_KEY':'','OPENWEATHER_API_KEY':'',
 'RAZORPAY_KEY_ID':'','RAZORPAY_KEY_SECRET':''})
app.run(host='127.0.0.1', port=int(os.environ['CHECK_PORT']), debug=False, use_reloader=False)
"""
        with open(Path(directory)/'server.log', 'w+') as log:
            process = subprocess.Popen([str(python), '-c', source], cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
            try:
                base = f'http://127.0.0.1:{port}'
                deadline = time.monotonic() + 30
                while True:
                    try:
                        with urlopen(base, timeout=2) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        if process.poll() is not None or time.monotonic() > deadline:
                            log.seek(0)
                            raise RuntimeError('Test server did not start:\n' + log.read())
                        time.sleep(.2)
                run_checks(base, args.browser_executable, args.artifacts)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()

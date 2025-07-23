from playwright.sync_api import sync_playwright
import os

EMAIL = "futuro.noob@gmail.com"
PASSWORD = "Psw141611@@"
LOGIN_URL = "https://netplay.sigma.vin/#/sign-in"
CUSTOMERS_URL = "https://netplay.sigma.vin/#/customers"
COOKIES_FILE = "auth.json"

def main(numero_usuario):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = load_or_create_context(browser)
        page = context.new_page()

        logar(page, context)
        irPageClient(page)
        pesquisar_usuario(page, numero_usuario)

        input("Pressione ENTER para fechar...")
        browser.close()

# ----------- FUNÇÕES FICAM ABAIXO, MINIMIZADAS -----------

def load_or_create_context(browser):
    if os.path.exists(COOKIES_FILE):
        return browser.new_context(storage_state=COOKIES_FILE)
    else:
        return browser.new_context()

def logar(page, context):
    page.goto(LOGIN_URL)
    if not page.url.endswith("/sign-in"):
        return
    page.fill('input[name="username"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button#kt_sign_in_submit')
    context.storage_state(path=COOKIES_FILE)
    page.wait_for_url(CUSTOMERS_URL, timeout=15000)

def irPageClient(page):
    page.wait_for_url(CUSTOMERS_URL, timeout=15000)

def pesquisar_usuario(page, numero_usuario):
    page.goto(CUSTOMERS_URL)
    page.fill('input[placeholder="Pesquisar"]', numero_usuario)
    # Se quiser extrair resultados, pode adicionar aqui

# ----------- CORPO PRINCIPAL -----------
if __name__ == "__main__":
    numero_usuario = input("Digite o número do usuário para pesquisar: ")
    main(numero_usuario)
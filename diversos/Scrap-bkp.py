from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class KiwifyScraper:
    def __init__(self):
        # === CONFIGURAÇÕES DO USUÁRIO ===
        self.USER_EMAIL = "arthur.diego7@gmail.com"
        self.USER_PASSWORD = "8@Dolar0081"
        self.URL_INICIAL = "https://dashboard.kiwify.com/course/premium/163d4f2c-3dab-4a0f-b541-df2165b786c2?mod=f790132f-a214-4fc3-baaf-0d5a533fbe49&sec=f3230053-3aed-4865-b766-7fc87b86666b"

        # Lista de padrões para identificar vídeos
        self.VIDEO_URL_PATTERNS = [
            re.compile(r"\.mp4($|\?)", re.I),
            re.compile(r"\.m3u8($|\?)", re.I),
            re.compile(r"cloudfront\.net", re.I),
            re.compile(r"amazonaws\.com", re.I),
            re.compile(r"s3\.amazonaws\.com", re.I),
            re.compile(r"videoplayback", re.I),
        ]

        # Seletor dos cards das aulas (ajuste conforme necessário)
        self.AULA_CARD_SELECTOR = "article[class*='cursor-pointer'], article.cursor-pointer"

        # Regex para identificar UUIDs em atributos/URLs
        self.UUID_REGEX = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

        # Inicializa o driver
        self.driver = self.iniciar_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.links_capturados = []

    # ================= MÉTODO 1 =================
    def iniciar_driver(self):
        print("🚀 Iniciando navegamaildor...")
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        seleniumwire_options = {}  # Pode adicionar configs de proxy se necessário

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
            seleniumwire_options=seleniumwire_options
        )
        return driver

    # ================= MÉTODO 2 =================
    def login(self):
        print("🔐 Acessando página de login...")
        self.driver.get(self.URL_INICIAL)
        time.sleep(2)

        # ================================
        # 1) Detectar se já está logado
        # ================================
        try:
            self.driver.find_element(By.CSS_SELECTOR, self.AULA_CARD_SELECTOR)
            print("✅ Já logado - área de aulas detectada.")
            return True
        except:
            print("ℹ️ Autenticação necessária. Iniciando login automático...")

        # ================================
        # 2) Possíveis seletores de campo de e-mail e senha
        # ================================
        POSSIBLE_EMAIL_SELECTORS = [
            'input[type="email"]',
            'input[name*="email"]',
            'input[id*="email"]',
            'input[placeholder*="e-mail"]',
            'input[placeholder*="email"]',
        ]
        POSSIBLE_PASSWORD_SELECTORS = [
            'input[type="password"]',
            'input[name*="password"]',
            'input[id*="password"]',
            'input[placeholder*="senha"]',
            'input[placeholder*="password"]',
        ]
        POSSIBLE_LOGIN_BUTTON_SELECTORS = [
            "button[type='submit']",
            "button[class*='login']",
            "button[class*='entrar']",
            ".chakra-button",  # botão comum na Kiwify
        ]

        # ================================
        # 3) Localizar e preencher e-mail
        # ================================
        email_input = None
        for selector in POSSIBLE_EMAIL_SELECTORS:
            try:
                email_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                if email_input.is_displayed():
                    break
            except:
                continue

        if email_input is None:
            raise Exception("❌ Não foi possível localizar o campo de e-mail")

        email_input.clear()
        email_input.send_keys(self.USER_EMAIL)
        print("✉️ E-mail inserido com sucesso")

        # ================================
        # 4) Localizar e preencher senha
        # ================================
        password_input = None
        for selector in POSSIBLE_PASSWORD_SELECTORS:
            try:
                password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                if password_input.is_displayed():
                    break
            except:
                continue

        if password_input is None:
            raise Exception("❌ Não foi possível localizar o campo de senha")

        password_input.clear()
        password_input.send_keys(self.USER_PASSWORD)
        print("🔒 Senha inserida com sucesso")

        # ================================
        # 5) Clicar no botão de login
        # ================================
        login_button = None
        for selector in POSSIBLE_LOGIN_BUTTON_SELECTORS:
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if login_button.is_displayed():
                    login_button.click()
                    print(f"▶ Clicando no botão de login: {selector}")
                    break
            except:
                continue

        if login_button is None:
            # Fallback: tentar ENTER no campo de senha
            password_input.send_keys("\n")
            print("▶ Botão não encontrado, tentando via ENTER no teclado...")

        # ================================
        # 6) Confirmar login
        # ================================
        time.sleep(3)
        try:
            self.driver.find_element(By.CSS_SELECTOR, self.AULA_CARD_SELECTOR)
            print("✅ Login realizado com sucesso!")
            return True
        except:
            print("⚠️ Login não confirmado. Pode haver CAPTCHA ou erro de credenciais.")
            return False

    # ================= MÉTODO 3 =================
    def navegar_para_aulas(self):
        print("📚 Aguardando página de aulas carregar...")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.AULA_CARD_SELECTOR)))
        time.sleep(2)  # Tempo extra para estabilidade

    # ================= MÉTODO 4 =================
    def capturar_links_de_aulas(self):
        print("🔎 Localizando cards de aulas...")
        return self.driver.find_elements(By.CSS_SELECTOR, self.AULA_CARD_SELECTOR)

    # ============== ADDED: extrair identificador da aula ==============
    def extrair_identificador_da_aula(self, card):
        """
        Tenta extrair um identificador único (UUID) do card da aula.
        Pesquisa em atributos data-*, hrefs internos, onclick, id, ou no texto.
        Retorna o UUID como string ou None se não encontrar.
        """
        try:
            # 1) checar atributos data-*
            attrs = self.driver.execute_script(
                "var items = {}; for (var i = 0; i < arguments[0].attributes.length; ++i) "
                "{ items[arguments[0].attributes[i].name] = arguments[0].attributes[i].value }; return items;",
                card)
            for k, v in attrs.items():
                if isinstance(v, str):
                    m = self.UUID_REGEX.search(v)
                    if m:
                        return m.group(0)

            # 2) checar elementos <a> internos (href)
            try:
                a_elem = card.find_element(By.TAG_NAME, "a")
                href = a_elem.get_attribute("href")
                if href:
                    m = self.UUID_REGEX.search(href)
                    if m:
                        return m.group(0)
            except Exception:
                pass

            # 3) checar atributo onclick
            try:
                onclick = attrs.get("onclick", "")
                if onclick:
                    m = self.UUID_REGEX.search(onclick)
                    if m:
                        return m.group(0)
            except Exception:
                pass

            # 4) checar id
            id_attr = attrs.get("id", "")
            if id_attr:
                m = self.UUID_REGEX.search(id_attr)
                if m:
                    return m.group(0)

            # 5) procurar UUID no texto do card
            text = card.text
            if text:
                m = self.UUID_REGEX.search(text)
                if m:
                    return m.group(0)
        except Exception:
            pass

        return None

    # ================= MÉTODO 5 =================
    def clicar_e_capturar_video(self, card, indice):
        print(f"\n➡️ Clicando na aula {indice + 1}...")
        # Tenta extrair identificador antes do clique
        lesson_id = self.extrair_identificador_da_aula(card)
        if lesson_id:
            print(f"🔎 Identificador extraído do card: {lesson_id}")
        else:
            print("⚠️ Não foi possível extrair identificador do card; usaremos heurística de rede.")

        # Limpa requests antigos
        self.driver.requests.clear()

        # Tenta clicar (com fallback)
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(3)
            card.click()
        except Exception as e:
            print(f"⚠️ Erro ao clicar: {e}. Tentando JavaScript.")
            self.driver.execute_script("arguments[0].click();", card)

        time.sleep(3)  # aguardar carregamento inicial

        # Capturar requisições de vídeo passando o lesson_id (pode ser None)
        self.capturar_url_do_video(lesson_id=lesson_id)

        print("↩️ Voltando para a lista de aulas...")
        self.driver.back()
        time.sleep(3)

    # ================= MÉTODO 6 =================
    def capturar_url_do_video(self, lesson_id=None):
        print("🎥 Iniciando captura da URL do vídeo...")

        # ===================== Clicar automaticamente no botão Play =====================
        play_selectors = [
            "button.plyr__control.plyr__control--overlaid",
            "button[aria-label='Play']",
            "button[data-plyr='play']"
        ]

        play_clicked = False
        for selector in play_selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(3)
                button.click()
                print(f"▶ Play clicado com sucesso usando seletor: {selector}")
                play_clicked = True
                break
            except:
                continue

        if not play_clicked:
            print("⚠️ Não foi possível encontrar o botão Play. Tentando iniciar o player via JavaScript direto...")
            try:
                self.driver.execute_script("document.querySelector('video').play();")
                play_clicked = True
                print("✅ Vídeo iniciado via JavaScript.")
            except:
                print("❌ Falha ao iniciar o vídeo.")

        # ===================== Aguardar o vídeo começar e carregar qualidades =====================
        max_wait = 12  # segundos totais para esperar resoluções maiores
        quality_priority = ["1080p.m3u8", "720p.m3u8", "480p.m3u8", "360p.m3u8", "240p.m3u8"]
        chosen = None

        waited = 0
        while waited < max_wait:
            hits = []

            # Coletar todas as requisições .m3u8 da rede
            for req in self.driver.requests:
                if req.response:
                    url = req.url
                    if url and ".m3u8" in url.lower():
                        hits.append(url)

            # Se encontramos algum m3u8, verificar por prioridade
            if hits:
                for quality in quality_priority:
                    filtered = [u for u in hits if quality in u.lower()]
                    if filtered:
                        chosen = filtered[-1]  # pega a última (mais recente)
                        print(f"🎯 Qualidade detectada ({quality}): {chosen}")
                        break

            if chosen:
                break  # saiu do loop quando encontrou a melhor qualidade disponível

            time.sleep(1)
            waited += 1
            print(f"⏳ Aguardando qualidades superiores... ({waited}/{max_wait}s)")

        # ===================== Fallback se nada encontrado =====================
        if not chosen:
            print(
                "⚠️ Nenhuma URL de alta qualidade encontrada. Usando a primeira .m3u8 detectada ou URL atual da página.")
            if hits:
                chosen = hits[-1]
            else:
                chosen = self.driver.current_url

        # ===================== Evitar duplicata =====================
        if chosen not in self.links_capturados:
            self.links_capturados.append(chosen)
        else:
            print(f"⚠️ URL já capturada anteriormente: {chosen}")

        print(f"✅ URL FINAL CAPTURADA: {chosen}")
        return True

    # ================= MÉTODO FINAL =================
    def executar(self):
        try:
            self.login()
            self.navegar_para_aulas()
            cards = self.capturar_links_de_aulas()
            print(f"✅ Total de aulas encontradas: {len(cards)}")

            for i in range(len(cards)):
                print(f"\n➡️ Preparando para clicar na aula {i+1}...")
                # Recarregar os cards a cada iteração (evita stale elements)
                cards = self.capturar_links_de_aulas()
                if i >= len(cards):
                    print("⚠️ Aula não encontrada após recarregar. Pulando.")
                    continue
                card = cards[i]
                self.clicar_e_capturar_video(card, i)

            print("\n==============================")
            print("📌 LINKS CAPTURADOS:")
            print("==============================")
            for link in self.links_capturados:
                print(link)

        finally:
            print("\n🛑 Encerrando navegador em 5 segundos...")
            time.sleep(5)
            self.driver.quit()

# ===================== PONTO DE ENTRADA =====================
if __name__ == "__main__":
    bot = KiwifyScraper()
    bot.executar()

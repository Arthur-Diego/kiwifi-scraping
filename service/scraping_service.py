import os
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@dataclass(frozen=True)
class KiwifyScraperConfig:
    url_inicial: str
    email: str
    password: str
    aula_card_selector: str = "article[class*='cursor-pointer'], article.cursor-pointer"
    wait_timeout_seconds: int = 20
    after_navigation_sleep_seconds: float = 2.0


class KiwifyScraper:
    """
    Scraper para capturar URLs de vídeo a partir da área de aulas da Kiwify.

    Observações:
    - Usa selenium-wire para acessar requests de rede e extrair URLs .m3u8.
    - Este serviço depende de credenciais; por segurança, elas devem vir de variáveis de ambiente.
    """

    _UUID_REGEX = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.I,
    )

    def __init__(self, url_inicial: str, *, email: Optional[str] = None, password: Optional[str] = None):
        # Credenciais por env; evita manter segredos no codebase.
        resolved_email = email or os.getenv("KIWIFY_EMAIL")
        resolved_password = password or os.getenv("KIWIFY_PASSWORD")
        if not resolved_email or not resolved_password:
            raise ValueError(
                "Credenciais ausentes. Defina KIWIFY_EMAIL e KIWIFY_PASSWORD (ou passe email/password no construtor)."
            )

        self.config = KiwifyScraperConfig(
            url_inicial=url_inicial,
            email=resolved_email,
            password=resolved_password,
        )

        self.driver = self.iniciar_driver()
        self.wait = WebDriverWait(self.driver, self.config.wait_timeout_seconds)
        self.links_capturados: list[str] = []
        self.aulas: list[dict[str, str]] = []  # {"titulo": ..., "link": ...}

    # ================= DRIVER =================
    def iniciar_driver(self):
        print("🚀 Iniciando navegador...")
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        seleniumwire_options: dict[str, Any] = {}
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
            seleniumwire_options=seleniumwire_options,
        )

    # ================= AUTH =================
    def _is_aulas_page_ready(self) -> bool:
        try:
            self.driver.find_element(By.CSS_SELECTOR, self.config.aula_card_selector)
            return True
        except Exception:
            return False

    @staticmethod
    def _first_visible_element(driver, selectors: Iterable[str]):
        for selector in selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el and el.is_displayed():
                    return el
            except Exception:
                continue
        return None

    def login(self) -> bool:
        print("🔐 Acessando página...")
        self.driver.get(self.config.url_inicial)
        time.sleep(self.config.after_navigation_sleep_seconds)

        if self._is_aulas_page_ready():
            print("✅ Já logado - área de aulas detectada.")
            return True

        print("ℹ️ Autenticação necessária. Iniciando login automático...")

        possible_email_selectors = [
            'input[type="email"]',
            'input[name*="email"]',
            'input[id*="email"]',
            'input[placeholder*="e-mail"]',
            'input[placeholder*="email"]',
        ]
        possible_password_selectors = [
            'input[type="password"]',
            'input[name*="password"]',
            'input[id*="password"]',
            'input[placeholder*="senha"]',
            'input[placeholder*="password"]',
        ]
        possible_login_button_selectors = [
            "button[type='submit']",
            "button[class*='login']",
            "button[class*='entrar']",
            ".chakra-button",
        ]

        email_input = self._first_visible_element(self.driver, possible_email_selectors)
        if email_input is None:
            raise RuntimeError("❌ Não foi possível localizar o campo de e-mail")
        email_input.clear()
        email_input.send_keys(self.config.email)
        print("✉️ E-mail inserido com sucesso")

        password_input = self._first_visible_element(self.driver, possible_password_selectors)
        if password_input is None:
            raise RuntimeError("❌ Não foi possível localizar o campo de senha")
        password_input.clear()
        password_input.send_keys(self.config.password)
        print("🔒 Senha inserida com sucesso")

        login_button = self._first_visible_element(self.driver, possible_login_button_selectors)
        if login_button is not None:
            login_button.click()
            print("▶ Botão de login clicado.")
        else:
            password_input.send_keys("\n")
            print("▶ Botão não encontrado, tentando via ENTER no teclado...")

        time.sleep(3)
        if self._is_aulas_page_ready():
            print("✅ Login realizado com sucesso!")
            return True

        print("⚠️ Login não confirmado. Pode haver CAPTCHA ou erro de credenciais.")
        return False

    # ================= NAVIGATION =================
    def navegar_para_aulas(self) -> None:
        print("📚 Aguardando página de aulas carregar...")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.config.aula_card_selector)))
        time.sleep(self.config.after_navigation_sleep_seconds)

    def capturar_links_de_aulas(self):
        print("🔎 Localizando cards de aulas...")
        return self.driver.find_elements(By.CSS_SELECTOR, self.config.aula_card_selector)

    # ============== Extrair identificador (UUID) ==============
    def extrair_identificador_da_aula(self, card) -> Optional[str]:
        """
        Tenta extrair um identificador único (UUID) do card da aula.
        Pesquisa em atributos, hrefs internos, onclick, id e texto.
        """
        try:
            attrs = self.driver.execute_script(
                "var items = {}; for (var i = 0; i < arguments[0].attributes.length; ++i) "
                "{ items[arguments[0].attributes[i].name] = arguments[0].attributes[i].value }; return items;",
                card,
            )
            for v in attrs.values():
                if isinstance(v, str):
                    m = self._UUID_REGEX.search(v)
                    if m:
                        return m.group(0)

            try:
                a_elem = card.find_element(By.TAG_NAME, "a")
                href = a_elem.get_attribute("href")
                if href:
                    m = self._UUID_REGEX.search(href)
                    if m:
                        return m.group(0)
            except Exception:
                pass

            onclick = attrs.get("onclick", "")
            if onclick:
                m = self._UUID_REGEX.search(onclick)
                if m:
                    return m.group(0)

            id_attr = attrs.get("id", "")
            if id_attr:
                m = self._UUID_REGEX.search(id_attr)
                if m:
                    return m.group(0)

            text = getattr(card, "text", "")
            if text:
                m = self._UUID_REGEX.search(text)
                if m:
                    return m.group(0)
        except Exception:
            return None

        return None

    # ================= Aula click + capture =================
    def clicar_e_capturar_video(self, card, indice: int) -> None:
        try:
            titulo = card.text.strip().split("\n")[0]
        except Exception:
            titulo = f"Aula {indice + 1}"
        print(f"\n➡️ Clicando na aula {indice + 1}: {titulo}")

        lesson_id = self.extrair_identificador_da_aula(card)
        if lesson_id:
            print(f"🔎 Identificador extraído do card: {lesson_id}")
        else:
            print("⚠️ Não foi possível extrair identificador do card; usaremos heurística de rede.")

        # Limpa requests antigos antes de abrir a aula.
        try:
            self.driver.requests.clear()
        except Exception:
            pass

        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(3)
            card.click()
        except Exception as e:
            print(f"⚠️ Erro ao clicar: {e}. Tentando JavaScript.")
            self.driver.execute_script("arguments[0].click();", card)

        time.sleep(3)

        link_video = self.capturar_url_do_video(lesson_id=lesson_id)
        self.aulas.append({"titulo": titulo, "link": link_video})

        print("↩️ Voltando para a lista de aulas...")
        self.driver.back()
        time.sleep(3)

    # ================= Capture m3u8 =================
    def capturar_url_do_video(self, lesson_id=None) -> str:
        # lesson_id mantido por compatibilidade; hoje a captura usa heurística via requests.
        _ = lesson_id

        print("🎥 Iniciando captura da URL do vídeo...")

        play_selectors = [
            "button.plyr__control.plyr__control--overlaid",
            "button[aria-label='Play']",
            "button[data-plyr='play']",
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
            except Exception:
                continue

        if not play_clicked:
            print("⚠️ Não foi possível encontrar o botão Play. Tentando iniciar via JavaScript...")
            try:
                self.driver.execute_script("document.querySelector('video').play();")
                print("✅ Vídeo iniciado via JavaScript.")
            except Exception:
                print("❌ Falha ao iniciar o vídeo.")

        max_wait_seconds = 12
        quality_priority = ["1080p.m3u8", "720p.m3u8", "480p.m3u8", "360p.m3u8", "240p.m3u8"]
        chosen: Optional[str] = None
        hits: list[str] = []

        waited = 0
        while waited < max_wait_seconds:
            hits = []
            for req in getattr(self.driver, "requests", []):
                try:
                    if not req.response:
                        continue
                    url = req.url
                    if url and ".m3u8" in url.lower():
                        hits.append(url)
                except Exception:
                    continue

            if hits:
                for quality in quality_priority:
                    filtered = [u for u in hits if quality in u.lower()]
                    if filtered:
                        chosen = filtered[-1]
                        print(f"🎯 Qualidade detectada ({quality}): {chosen}")
                        break

            if chosen:
                break

            time.sleep(1)
            waited += 1
            print(f"⏳ Aguardando qualidades superiores... ({waited}/{max_wait_seconds}s)")

        if not chosen:
            print("⚠️ Nenhuma URL de alta qualidade encontrada. Usando a última .m3u8 detectada ou URL atual.")
            chosen = hits[-1] if hits else self.driver.current_url

        if chosen not in self.links_capturados:
            self.links_capturados.append(chosen)
        else:
            print(f"⚠️ URL já capturada anteriormente: {chosen}")

        print(f"✅ URL FINAL CAPTURADA: {chosen}")
        return chosen

    # ================= Orquestração =================
    def executar(self):
        try:
            self.login()
            self.navegar_para_aulas()
            cards = self.capturar_links_de_aulas()

            for i in range(len(cards)):
                # Recaptura a cada loop para evitar stale references.
                cards = self.capturar_links_de_aulas()
                if i >= len(cards):
                    continue
                self.clicar_e_capturar_video(cards[i], i)

            print("\n==============================")
            print("📌 RESULTADO FINAL")
            print("==============================")
            for aula in self.aulas:
                print(f"{aula['titulo']} -> {aula['link']}")

            return self.aulas
        finally:
            time.sleep(5)
            try:
                self.driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    # Execução local via env para evitar hardcode de URLs e credenciais.
    url = os.getenv("KIWIFY_URL_INICIAL")
    if not url:
        raise SystemExit("Defina KIWIFY_URL_INICIAL para rodar este script diretamente.")
    bot = KiwifyScraper(url_inicial=url)
    resultado = bot.executar()
    print(resultado)


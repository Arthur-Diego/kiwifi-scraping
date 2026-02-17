from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.parse import parse_qs, unquote, urlparse as _urlparse

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def _build_driver(profile_dir: Path | None = None, headless: bool = False) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1400,1000")
    if headless:
        options.add_argument("--headless=new")
    if profile_dir is not None:
        profile_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")

    chrome_binary = _resolve_chrome_binary()
    if chrome_binary:
        options.binary_location = chrome_binary

    chromedriver_path = _resolve_chromedriver_binary()
    if chromedriver_path:
        return webdriver.Chrome(service=Service(chromedriver_path), options=options)

    try:
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception:
        # Last fallback: let Selenium Manager try to resolve the driver.
        return webdriver.Chrome(options=options)


def _resolve_chrome_binary() -> str | None:
    configured = os.getenv("SELENIUM_CHROME_BINARY", "").strip()
    if configured:
        return configured

    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _resolve_chromedriver_binary() -> str | None:
    configured = os.getenv("SELENIUM_CHROMEDRIVER_PATH", "").strip()
    if configured and Path(configured).exists():
        return configured

    candidates = [
        shutil.which("chromedriver"),
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/mnt/c/Program Files/Google/Chrome/Application/chromedriver.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _save_cookies(driver: webdriver.Chrome, cookie_file: Path) -> int:
    cookies = driver.get_cookies()
    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    cookie_file.write_text(json.dumps(cookies, ensure_ascii=True, indent=2), encoding="utf-8")
    return len(cookies)


def _load_cookies(driver: webdriver.Chrome, cookie_file: Path, domain_url: str) -> int:
    if not cookie_file.exists():
        return 0
    raw = json.loads(cookie_file.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return 0

    driver.get(domain_url)
    added = 0
    for cookie in raw:
        if not isinstance(cookie, dict):
            continue
        clean = dict(cookie)
        # Selenium expects expiry (int), not expires (float/str) in many drivers.
        if "expiry" in clean:
            try:
                clean["expiry"] = int(clean["expiry"])
            except Exception:
                clean.pop("expiry", None)
        clean.pop("sameSite", None)
        try:
            driver.add_cookie(clean)
            added += 1
        except WebDriverException:
            continue
    return added


def _base_domain_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    return f"{scheme}://{parsed.netloc}/"


def bootstrap_login_session(
    *,
    login_url: str,
    success_selector: str,
    success_url_contains: str | None,
    cookie_file: Path,
    profile_dir: Path | None,
    timeout_seconds: int,
    auto_login: bool,
    username: str | None,
    password: str | None,
    username_selector: str,
    password_selector: str,
    submit_selector: str,
) -> None:
    driver = _build_driver(profile_dir=profile_dir, headless=False)
    try:
        driver.get(login_url)
        print(f"Abra o navegador e conclua login manualmente em: {login_url}")
        print(f"Aguardando até {timeout_seconds}s pelo seletor de sucesso: {success_selector}")

        if auto_login:
            if not username or not password:
                raise SystemExit("Auto-login exige usuário e senha (via args ou env).")
            try:
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, username_selector)))
                user_el = driver.find_element(By.CSS_SELECTOR, username_selector)
                pass_el = driver.find_element(By.CSS_SELECTOR, password_selector)
                user_el.clear()
                user_el.send_keys(username)
                pass_el.clear()
                pass_el.send_keys(password)
                driver.find_element(By.CSS_SELECTOR, submit_selector).click()
                print("Auto-login enviado. Aguarde eventual 2FA/CAPTCHA manual.")
            except Exception as exc:
                raise SystemExit(f"Falha no auto-login com seletores informados: {exc}")

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            found = bool(driver.find_elements(By.CSS_SELECTOR, success_selector))
            url_ok = bool(success_url_contains and success_url_contains in driver.current_url) if success_url_contains else False
            if found or url_ok:
                count = _save_cookies(driver, cookie_file)
                print(f"Sessao salva com sucesso. cookies={count} arquivo={cookie_file}")
                return
            time.sleep(2)
        raise SystemExit("Timeout: login não confirmado pelo seletor informado.")
    finally:
        driver.quit()


def run_with_saved_session(
    *,
    target_url: str,
    success_selector: str,
    success_url_contains: str | None,
    cookie_file: Path,
    profile_dir: Path | None,
    headless: bool,
    open_affiliate_marketplace: bool,
    affiliate_marketplace_selector: str,
    marketplace_wait_seconds: int,
    scrape_marketplace: bool,
    marketplace_pages: int,
    marketplace_output_file: Path,
) -> None:
    driver = _build_driver(profile_dir=profile_dir, headless=headless)
    try:
        domain_url = _base_domain_url(target_url)
        loaded = _load_cookies(driver, cookie_file, domain_url)
        print(f"Cookies carregados: {loaded}")

        driver.get(target_url)
        time.sleep(2)
        ok_selector = bool(driver.find_elements(By.CSS_SELECTOR, success_selector))
        ok_url = bool(success_url_contains and success_url_contains in driver.current_url) if success_url_contains else False
        ok = ok_selector or ok_url
        print(f"Session valid: {ok}")
        print(f"Current URL: {driver.current_url}")
        if ok:
            _save_cookies(driver, cookie_file)
            if open_affiliate_marketplace:
                _open_affiliate_marketplace(
                    driver,
                    selector=affiliate_marketplace_selector,
                    timeout_seconds=marketplace_wait_seconds,
                )
                _save_cookies(driver, cookie_file)
            if scrape_marketplace:
                data = _scrape_marketplace_pages(
                    driver,
                    pages=max(1, marketplace_pages),
                    timeout_seconds=marketplace_wait_seconds,
                )
                marketplace_output_file.parent.mkdir(parents=True, exist_ok=True)
                marketplace_output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"Marketplace scrape saved: {marketplace_output_file} (offers={len(data.get('offers', []))})")
    finally:
        driver.quit()


def _open_affiliate_marketplace(driver: webdriver.Chrome, *, selector: str, timeout_seconds: int) -> None:
    try:
        WebDriverWait(driver, timeout_seconds).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        link = driver.find_element(By.CSS_SELECTOR, selector)
        href = (link.get_attribute("href") or "").strip()
        print(f"Affiliate Marketplace link found. href={href}")
        if href:
            # Some marketplace links open in a new tab (target=_blank). Force same-tab navigation.
            next_url = urljoin(driver.current_url, href)
            driver.get(next_url)
        else:
            link.click()
        WebDriverWait(driver, timeout_seconds).until(
            lambda d: "affiliate-marketplace" in d.current_url or "mktplace" in d.current_url
        )
        print(f"Affiliate Marketplace opened. current_url={driver.current_url}")
    except Exception as exc:
        raise SystemExit(f"Falha ao abrir Affiliate Marketplace: {exc}")


def _scrape_marketplace_pages(driver: webdriver.Chrome, *, pages: int, timeout_seconds: int) -> dict:
    _ensure_top_offers_view(driver, timeout_seconds=timeout_seconds)
    _wait_marketplace_loaded(driver, timeout_seconds=timeout_seconds)
    offers: list[dict] = []
    seen: set[str] = set()

    for page in range(1, pages + 1):
        _goto_marketplace_page(driver, page, timeout_seconds=timeout_seconds)
        _wait_marketplace_loaded(driver, timeout_seconds=timeout_seconds)
        page_offers = _extract_offers_from_current_page(driver)
        for item in page_offers:
            key = item.get("offer_id") or item.get("title") or f"page-{page}-{len(offers)}"
            if key in seen:
                continue
            seen.add(key)
            item["page"] = page
            offers.append(item)

    return {
        "source": "clickbank-affiliate-marketplace",
        "scraped_at": int(time.time()),
        "pages_requested": pages,
        "pages_scraped": pages,
        "offers_count": len(offers),
        "offers": offers,
    }


def _wait_marketplace_loaded(driver: webdriver.Chrome, *, timeout_seconds: int) -> None:
    def _loaded(drv: webdriver.Chrome) -> bool:
        # Explicit Top Offers widget from marketplace sidebar/menu.
        if drv.find_elements(
            By.XPATH,
            "//div[contains(@class,'marketplace-ui-jss20')]//h4[normalize-space()='Top Offers']",
        ):
            return True
        # Any of these indicates marketplace result UI is mounted.
        if drv.find_elements(By.CSS_SELECTOR, "a[href*='#/offer-details?offer=']"):
            return True
        if drv.find_elements(By.CSS_SELECTOR, "[data-cy='sort-by-dropdown']"):
            return True
        if drv.find_elements(By.CSS_SELECTOR, "button[aria-label^='Go to page'], button[aria-current='true']"):
            return True
        text = (drv.page_source or "").lower()
        return "top offers" in text and "sort results by" in text

    try:
        WebDriverWait(driver, timeout_seconds).until(_loaded)
    except Exception as exc:
        _dump_marketplace_debug(driver)
        raise SystemExit(
            "Timeout ao carregar Top Offers no marketplace. "
            "Arquivos de debug salvos em data/reports/selenium_marketplace_debug.*"
        ) from exc


def _ensure_top_offers_view(driver: webdriver.Chrome, *, timeout_seconds: int) -> None:
    current = driver.current_url
    if "affiliate-marketplace" not in current:
        return

    # Many accounts land on the marketplace shell first; force the known "Top Offers results" route.
    base = current.split("#", 1)[0]
    results_route = "#/results?sortField=rank&sortDescending=false"
    expected_suffix = "/results?sortField=rank&sortDescending=false"
    if expected_suffix not in current:
        driver.get(f"{base}{results_route}")
        time.sleep(2)

    if expected_suffix in (driver.current_url or ""):
        return

    # Preferred: Click explicit Top Offers nav item used by marketplace.
    try:
        nav_selector = "[data-cy='Top Offers-category-nav']"
        if driver.find_elements(By.CSS_SELECTOR, nav_selector):
            driver.find_element(By.CSS_SELECTOR, nav_selector).click()
            WebDriverWait(driver, timeout_seconds).until(
                lambda d: expected_suffix in (d.current_url or "")
                or bool(d.find_elements(By.CSS_SELECTOR, "a[href*='#/offer-details?offer=']"))
                or bool(d.find_elements(By.CSS_SELECTOR, "[data-cy='sort-by-dropdown']"))
                or bool(d.find_elements(By.CSS_SELECTOR, "button[aria-label^='Go to page']"))
            )
            return
    except Exception:
        pass

    # Fallback: click an in-page entry if available.
    try:
        exact_widget_links = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'marketplace-ui-jss20')][.//h4[normalize-space()='Top Offers']]",
        )
        if exact_widget_links:
            exact_widget_links[0].click()
            time.sleep(1)

        top_links = driver.find_elements(
            By.XPATH,
            "//*[self::a or self::button][contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'top offers')]",
        )
        if top_links:
            top_links[0].click()
            WebDriverWait(driver, timeout_seconds).until(
                lambda d: expected_suffix in (d.current_url or "")
                or bool(d.find_elements(By.CSS_SELECTOR, "a[href*='#/offer-details?offer=']"))
                or bool(d.find_elements(By.CSS_SELECTOR, "[data-cy='sort-by-dropdown']"))
                or bool(d.find_elements(By.CSS_SELECTOR, "button[aria-label^='Go to page']"))
                or "top-offers" in (d.current_url or "")
            )
    except Exception:
        # Final load check happens in _wait_marketplace_loaded.
        return


def _dump_marketplace_debug(driver: webdriver.Chrome) -> None:
    out_dir = Path("data/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "selenium_marketplace_debug.html"
    png_path = out_dir / "selenium_marketplace_debug.png"
    try:
        html_path.write_text(driver.page_source or "", encoding="utf-8")
    except Exception:
        pass
    try:
        driver.save_screenshot(str(png_path))
    except Exception:
        pass


def _goto_marketplace_page(driver: webdriver.Chrome, page: int, *, timeout_seconds: int) -> None:
    if page == 1:
        return
    selector = f"button[aria-label='Go to page {page}']"
    WebDriverWait(driver, timeout_seconds).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    btn = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.3)

    clicked = False
    for _ in range(3):
        try:
            WebDriverWait(driver, timeout_seconds).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            btn = driver.find_element(By.CSS_SELECTOR, selector)
            btn.click()
            clicked = True
            break
        except ElementClickInterceptedException:
            # Typical interceptors: floating chat widgets / sticky overlays.
            driver.execute_script("window.scrollBy(0, -180);")
            time.sleep(0.25)
        except Exception:
            time.sleep(0.25)

    if not clicked:
        btn = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].click();", btn)

    WebDriverWait(driver, timeout_seconds).until(
        lambda d: _is_page_active(d, page)
    )
    WebDriverWait(driver, timeout_seconds).until(
        lambda d: bool(d.find_elements(By.CSS_SELECTOR, "a[href*='#/offer-details?offer=']"))
    )


def _is_page_active(driver: webdriver.Chrome, page: int) -> bool:
    active = driver.find_elements(By.CSS_SELECTOR, "button[aria-current='true']")
    if not active:
        return False
    text = (active[0].text or "").strip()
    return text == str(page)


def _extract_offers_from_current_page(driver: webdriver.Chrome) -> list[dict]:
    anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='#/offer-details?offer=']")
    results: list[dict] = []
    for anchor in anchors:
        href = (anchor.get_attribute("href") or "").strip()
        title = (anchor.text or "").strip()
        offer_id = _extract_offer_id_from_href(href)
        card = _find_offer_card(anchor)

        category = ""
        description = ""
        cpa_available = False
        direct_tracking_available = False
        affiliate_page_url = ""
        sales_page_url = ""
        image_url = ""
        avg_per_conv_total = ""
        avg_per_conv_initial = ""
        avg_per_conv_future = ""
        cvr = ""
        epc = ""
        gravity = ""
        rank = ""

        if card is not None:
            category = _safe_text(card, "p a[href*='category=']")
            if not category:
                links = card.find_elements(By.CSS_SELECTOR, "p a[href*='category=']")
                if links:
                    category = "/".join((link.text or "").strip() for link in links if (link.text or "").strip())

            description = _extract_label_value(card, "Description")
            if not description:
                card_text = (card.text or "").strip()
                m_desc = re.search(r"Description\s*(.+?)(?:Avg\s*\$\s*Per\s*Conv|CVR|EPC|Gravity|Rank|$)", card_text, flags=re.IGNORECASE | re.DOTALL)
                if m_desc:
                    description = re.sub(r"\s+", " ", m_desc.group(1)).strip()
            cpa_available = bool(card.find_elements(By.XPATH, ".//*[contains(text(),'CPA Available')]"))
            direct_tracking_available = bool(card.find_elements(By.XPATH, ".//*[contains(text(),'Direct Tracking Available')]"))
            affiliate_page_url, sales_page_url = _extract_offer_action_links(card)
            image_url = _safe_attr(card, "img[alt='product image']", "src")

            avg_per_conv_total = _extract_metric_after_label(card, "Total")
            avg_per_conv_initial = _extract_metric_after_label(card, "Initial")
            avg_per_conv_future = _extract_metric_after_label(card, "Future")
            cvr = _extract_heading_after_label(card, "CVR")
            epc = _extract_heading_after_label(card, "EPC")
            gravity = _extract_heading_after_label(card, "Gravity")
            rank = _extract_heading_after_label(card, "Rank")

            if not avg_per_conv_total:
                avg_per_conv_total = _extract_value_with_regex(card, r"Total\s*\$?\s*([0-9][0-9\.,-]*)", prefix="$")
            if not avg_per_conv_initial:
                avg_per_conv_initial = _extract_value_with_regex(card, r"Initial\s*\$?\s*([0-9][0-9\.,-]*)", prefix="$")
            if not avg_per_conv_future:
                fut = _extract_value_with_regex(card, r"Future\s*([0-9\.,-]+|-)", prefix="$")
                avg_per_conv_future = fut or avg_per_conv_future
            if not cvr:
                cvr = _extract_value_with_regex(card, r"CVR\s*([0-9]+(?:[.,][0-9]+)?%)")
            if not epc:
                epc = _extract_value_with_regex(card, r"EPC\s*\$?\s*([0-9][0-9\.,]*)", prefix="$")
            if not gravity:
                gravity = _extract_value_with_regex(card, r"Gravity\s*([0-9]+(?:[.,][0-9]+)?)")
            if not rank:
                rank = _extract_value_with_regex(card, r"Rank\s*(#\d+)")

        if not sales_page_url:
            sales_page_url = _extract_click_url_from_offer_link(href)

        results.append(
            {
                "offer_id": offer_id,
                "title": title,
                "offer_link": href,
                "category": category,
                "description": description,
                "cpa_available": cpa_available,
                "direct_tracking_available": direct_tracking_available,
                "affiliate_page_url": affiliate_page_url,
                "sales_page_url": sales_page_url,
                "image_url": image_url,
                "avg_per_conv_total": avg_per_conv_total,
                "avg_per_conv_initial": avg_per_conv_initial,
                "avg_per_conv_future": avg_per_conv_future,
                "cvr": cvr,
                "epc": epc,
                "gravity": gravity,
                "rank": rank,
            }
        )
    return results


def _find_offer_card(anchor):
    # Marketplace is React/MUI; closest card root can vary. Try nearest meaningful container.
    attempts = [
        ".//ancestor::div[.//*[@id='stats-row'] and .//p[@id='title-offer-details']][1]",
        ".//ancestor::div[@id='stats-row']/ancestor::div[contains(@class,'MuiGrid-container')][1]",
        ".//ancestor::div[contains(@class,'MuiGrid-container') and .//p[@id='title-offer-details']][1]",
        ".//ancestor::div[contains(@class,'MuiGrid-item') and .//img[@alt='product image']][1]",
    ]
    for xp in attempts:
        found = anchor.find_elements(By.XPATH, xp)
        if found:
            return found[0]
    return None


def _extract_offer_id_from_href(href: str) -> str:
    if not href:
        return ""
    parsed = _urlparse(href)
    query = parse_qs(parsed.query)
    offer = query.get("offer", [""])[0]
    if offer:
        return offer
    m = re.search(r"offer=([A-Z0-9_\\-]+)", href, flags=re.IGNORECASE)
    return m.group(1) if m else ""


def _safe_text(root, css: str) -> str:
    els = root.find_elements(By.CSS_SELECTOR, css)
    if not els:
        return ""
    return (els[0].text or "").strip()


def _safe_href(root, css: str) -> str:
    els = root.find_elements(By.CSS_SELECTOR, css)
    if not els:
        return ""
    return (els[0].get_attribute("href") or "").strip()


def _safe_attr(root, css: str, attr: str) -> str:
    els = root.find_elements(By.CSS_SELECTOR, css)
    if not els:
        return ""
    return (els[0].get_attribute(attr) or "").strip()


def _extract_offer_action_links(root) -> tuple[str, str]:
    affiliate_page_url = ""
    sales_page_url = ""

    links = root.find_elements(By.CSS_SELECTOR, "a[data-cy='affiliate-tools-link']")
    for link in links:
        href = (link.get_attribute("href") or "").strip()
        text = (link.text or "").lower()
        if not href:
            continue
        if "affiliate" in text and not affiliate_page_url:
            affiliate_page_url = href
        elif "sales" in text and not sales_page_url:
            sales_page_url = href

    if not affiliate_page_url:
        affiliate_page_url = _safe_href(root, "a[href*='affiliates']")
    if not sales_page_url:
        sales_page_url = _safe_href(root, "a[href*='hop.clickbank.net/?affiliate=']")
    return affiliate_page_url, sales_page_url


def _extract_label_value(root, label: str) -> str:
    labels = root.find_elements(By.XPATH, f".//*[self::h6 or self::span or self::p][contains(normalize-space(text()),'{label}')]")
    for lb in labels:
        sib = lb.find_elements(By.XPATH, "./following-sibling::*[1]")
        if sib:
            text = (sib[0].text or "").strip()
            if text:
                return text
    return ""


def _extract_metric_after_label(root, label: str) -> str:
    labels = root.find_elements(By.XPATH, f".//*[self::p or self::span][normalize-space(text())='{label}']")
    for lb in labels:
        candidates = lb.find_elements(By.XPATH, "./following-sibling::*[1]")
        if candidates:
            txt = (candidates[0].text or "").strip()
            if txt:
                return txt
    return ""


def _extract_heading_after_label(root, label: str) -> str:
    labels = root.find_elements(By.XPATH, f".//*[self::span][normalize-space(text())='{label}']")
    for lb in labels:
        candidates = lb.find_elements(By.XPATH, "./following-sibling::*[1]")
        if candidates:
            txt = (candidates[0].text or "").strip()
            if txt:
                return txt
    return ""


def _extract_click_url_from_offer_link(href: str) -> str:
    if not href:
        return ""
    try:
        parsed = _urlparse(href)
        query = parse_qs(parsed.query)
        click_url = query.get("clickUrl", [""])[0]
        if click_url:
            return unquote(click_url)
    except Exception:
        return ""
    return ""


def _extract_value_with_regex(root, pattern: str, prefix: str = "") -> str:
    text = re.sub(r"\s+", " ", (root.text or "").strip())
    if not text:
        return ""
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return ""
    value = (m.group(1) or "").strip()
    if not value:
        return ""
    if prefix and value != "-" and not value.startswith(prefix):
        return f"{prefix}{value}"
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Selenium session bootstrap/reuse helper.")
    parser.add_argument("--mode", choices=["bootstrap", "run"], required=True)
    parser.add_argument("--login-url", default=os.getenv("SELENIUM_LOGIN_URL", ""))
    parser.add_argument("--target-url", default=os.getenv("SELENIUM_TARGET_URL", ""))
    parser.add_argument("--success-selector", default=os.getenv("SELENIUM_SUCCESS_SELECTOR", ""))
    parser.add_argument("--success-url-contains", default=os.getenv("SELENIUM_SUCCESS_URL_CONTAINS", ""))
    parser.add_argument("--cookie-file", default=os.getenv("SELENIUM_COOKIE_FILE", "data/reports/selenium_session_cookies.json"))
    parser.add_argument("--profile-dir", default=os.getenv("SELENIUM_PROFILE_DIR", "data/reports/selenium_profile"))
    parser.add_argument("--timeout-seconds", type=int, default=int(os.getenv("SELENIUM_LOGIN_TIMEOUT_SECONDS", "300")))
    parser.add_argument("--auto-login", action="store_true")
    parser.add_argument("--username", default=os.getenv("SELENIUM_LOGIN_USERNAME", ""))
    parser.add_argument("--password", default=os.getenv("SELENIUM_LOGIN_PASSWORD", ""))
    parser.add_argument("--username-selector", default=os.getenv("SELENIUM_USERNAME_SELECTOR", "input[name='username']"))
    parser.add_argument("--password-selector", default=os.getenv("SELENIUM_PASSWORD_SELECTOR", "input[name='password']"))
    parser.add_argument("--submit-selector", default=os.getenv("SELENIUM_SUBMIT_SELECTOR", "form#sign-in button[type='submit']"))
    parser.add_argument(
        "--open-affiliate-marketplace",
        action="store_true",
        default=os.getenv("SELENIUM_OPEN_AFFILIATE_MARKETPLACE", "0").strip() in {"1", "true", "TRUE", "yes", "YES"},
    )
    parser.add_argument(
        "--affiliate-marketplace-selector",
        default=os.getenv("SELENIUM_AFFILIATE_MARKETPLACE_SELECTOR", "a[title='Affiliate Marketplace']"),
    )
    parser.add_argument(
        "--marketplace-wait-seconds",
        type=int,
        default=int(os.getenv("SELENIUM_MARKETPLACE_WAIT_SECONDS", "20")),
    )
    parser.add_argument(
        "--scrape-marketplace",
        action="store_true",
        default=os.getenv("SELENIUM_SCRAPE_MARKETPLACE", "0").strip() in {"1", "true", "TRUE", "yes", "YES"},
    )
    parser.add_argument(
        "--marketplace-pages",
        type=int,
        default=int(os.getenv("SELENIUM_MARKETPLACE_PAGES", "5")),
    )
    parser.add_argument(
        "--marketplace-output-file",
        default=os.getenv("SELENIUM_MARKETPLACE_OUTPUT_FILE", "data/reports/clickbank_marketplace_top_offers.json"),
    )
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    cookie_file = Path(args.cookie_file)
    profile_dir = Path(args.profile_dir) if args.profile_dir else None

    if not args.success_selector:
        raise SystemExit("Defina --success-selector (ou SELENIUM_SUCCESS_SELECTOR) para confirmar login.")

    if args.mode == "bootstrap":
        if not args.login_url:
            raise SystemExit("Defina --login-url (ou SELENIUM_LOGIN_URL).")
        bootstrap_login_session(
            login_url=args.login_url,
            success_selector=args.success_selector,
            success_url_contains=args.success_url_contains or None,
            cookie_file=cookie_file,
            profile_dir=profile_dir,
            timeout_seconds=args.timeout_seconds,
            auto_login=args.auto_login,
            username=args.username or None,
            password=args.password or None,
            username_selector=args.username_selector,
            password_selector=args.password_selector,
            submit_selector=args.submit_selector,
        )
        return

    if not args.target_url:
        raise SystemExit("Defina --target-url (ou SELENIUM_TARGET_URL).")
    run_with_saved_session(
        target_url=args.target_url,
        success_selector=args.success_selector,
        success_url_contains=args.success_url_contains or None,
        cookie_file=cookie_file,
        profile_dir=profile_dir,
        headless=args.headless,
        open_affiliate_marketplace=args.open_affiliate_marketplace,
        affiliate_marketplace_selector=args.affiliate_marketplace_selector,
        marketplace_wait_seconds=args.marketplace_wait_seconds,
        scrape_marketplace=args.scrape_marketplace,
        marketplace_pages=args.marketplace_pages,
        marketplace_output_file=Path(args.marketplace_output_file),
    )


if __name__ == "__main__":
    main()

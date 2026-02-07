# ADR 0003 - Selenium Wire para scraping autenticado

Status: sugerido

Contexto:
- O scraper usa Selenium Wire para inspecionar requests e capturar URLs .m3u8.
- Ha login automatico e navegacao por cards de aulas.

Decisao:
- Manter Selenium + selenium-wire como base para scraping de aulas e captura de video.

Consequencias:
- Necessita ChromeDriver e ambiente com navegador.
- Pode ser fragil a mudancas de UI ou CAPTCHA.

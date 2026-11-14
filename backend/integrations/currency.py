"""Valutakurser fra Danmarks Nationalbank.

``rate(currency, date)`` giver kursen i DKK for 1 enhed af valutaen på datoen.
Nationalbanken offentliggør kurser på bankdage; for weekender og helligdage
bruges den seneste kurs før datoen (som i bogføringspraksis).

Adaptere (``CURRENCY_PROVIDER``):
  mock         – faste kurser (default)
  nationalbank – Nationalbankens XML-feed (kurser pr. 100 enheder)
"""

import xml.etree.ElementTree as ET
from datetime import date as date_cls, datetime, timedelta
from decimal import Decimal

from django.core.cache import cache

from .base import IntegrationError, select, setting, user_agent

BASE = "DKK"


def _to_date(value):
    if value is None:
        return date_cls.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date_cls):
        return value
    return date_cls.fromisoformat(str(value)[:10])


def parse_nationalbank_xml(xml_text):
    """{date: {currency: Decimal(DKK pr. 1 enhed)}} fra Nationalbankens XML.

    Formatet:
      <exchangerates refcur="DKK" refamt="1">
        <dailyrates id="2026-11-13">
          <currency code="EUR" desc="Euro" rate="746,02"/>
    Kursen er pr. 100 enheder og bruger decimalkomma.
    """
    root = ET.fromstring(xml_text)
    out = {}
    for daily in root.iter():
        if daily.tag.split("}")[-1] != "dailyrates":
            continue
        day = date_cls.fromisoformat(daily.attrib["id"][:10])
        rates = {}
        for cur in daily:
            if cur.tag.split("}")[-1] != "currency":
                continue
            raw = (cur.attrib.get("rate") or "").strip()
            if "," in raw:  # lang=da: "1.234,56"
                raw = raw.replace(".", "").replace(",", ".")
            if not raw or raw == "-":
                continue
            rates[cur.attrib["code"].upper()] = (Decimal(raw) / 100).quantize(Decimal("0.000001"))
        out[day] = rates
    if not out:
        raise IntegrationError("Nationalbankens kursfil indeholdt ingen kurser.")
    return out


def pick(rates_by_day, currency, day):
    """Kursen på dagen eller den seneste bankdag før."""
    for d in sorted((d for d in rates_by_day if d <= day), reverse=True):
        if currency in rates_by_day[d]:
            return rates_by_day[d][currency], d
    raise IntegrationError(f"Ingen kurs for {currency} på eller før {day.isoformat()}.")


class CurrencyClient:
    name = "base"

    def rates(self, day) -> dict:  # pragma: no cover - interface
        """{date: {currency: Decimal}} der dækker dagen (og gerne dagene før)."""
        raise NotImplementedError


class MockCurrencyClient(CurrencyClient):
    name = "mock"
    FIXED = {"EUR": Decimal("7.4600"), "USD": Decimal("6.9000"), "GBP": Decimal("8.6500"),
             "SEK": Decimal("0.6500"), "NOK": Decimal("0.6300"), "CHF": Decimal("7.8000")}

    def rates(self, day):
        return {day: dict(self.FIXED)}


class NationalbankClient(CurrencyClient):
    name = "nationalbank"
    LATEST_URL = "https://www.nationalbanken.dk/api/currencyratesxml?lang=da"
    HISTORY_URL = "https://www.nationalbanken.dk/api/currencyrateshistoryxml?lang=da"
    TIMEOUT = 15

    def _fetch(self, url):
        import requests

        key = f"dn-rates:{url}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        try:
            resp = requests.get(url, timeout=self.TIMEOUT, headers={"User-Agent": user_agent()})
            resp.raise_for_status()
        except requests.RequestException as e:
            raise IntegrationError(f"Kunne ikke hente valutakurser fra Nationalbanken: {e}") from e
        data = parse_nationalbank_xml(resp.content)
        cache.set(key, data, 60 * 60 * 6)
        return data

    def rates(self, day):
        latest = self._fetch(setting("CURRENCY_NATIONALBANK_URL", self.LATEST_URL))
        if latest and min(latest) <= day:
            return latest
        # Ældre dato: historikfilen.
        return self._fetch(setting("CURRENCY_NATIONALBANK_HISTORY_URL", self.HISTORY_URL))


CLIENTS = {"mock": MockCurrencyClient, "nationalbank": NationalbankClient}


def get_client():
    return select("CURRENCY_PROVIDER", CLIENTS)


def rate(currency, date=None):
    """DKK pr. 1 enhed af ``currency`` på ``date`` (Decimal). DKK → 1."""
    currency = (currency or BASE).upper()
    if currency == BASE:
        return Decimal("1")
    day = _to_date(date)
    if day > date_cls.today() + timedelta(days=1):
        raise IntegrationError("Der findes ingen kurs for en fremtidig dato.")
    value, _ = pick(get_client().rates(day), currency, day)
    return value


def convert(amount, currency, date=None):
    """Beløb i DKK, afrundet til øre."""
    return (Decimal(str(amount)) * rate(currency, date)).quantize(Decimal("0.01"))

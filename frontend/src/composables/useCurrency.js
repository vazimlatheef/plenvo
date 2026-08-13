import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'plenvo_currency'

const EURO_ZONE = new Set([
  'DE', 'FR', 'IT', 'ES', 'PT', 'NL', 'BE', 'AT', 'FI', 'GR', 'IE',
  'LU', 'MT', 'CY', 'SK', 'SI', 'EE', 'LV', 'LT',
])

const PRICE_MAP = {
  INR: {
    currency: 'INR',
    symbol: '₹',
    prices: { personal: '499', team: '1,999', enterprise: '3,999' },
  },
  GBP: {
    currency: 'GBP',
    symbol: '£',
    prices: { personal: '4.99', team: '19.99', enterprise: '39.99' },
  },
  EUR: {
    currency: 'EUR',
    symbol: '€',
    prices: { personal: '4.99', team: '19.99', enterprise: '39.99' },
  },
  USD: {
    currency: 'USD',
    symbol: '$',
    prices: { personal: '4.99', team: '19.99', enterprise: '39.99' },
  },
}

const CURRENCY_LABELS = {
  INR: 'INR (₹)',
  GBP: 'GBP (£)',
  EUR: 'EUR (€)',
  USD: 'USD ($)',
}

function resolveCurrency(countryCode) {
  const cc = (countryCode || '').toUpperCase()
  if (cc === 'IN') return PRICE_MAP.INR
  if (cc === 'GB' || cc === 'IE') return PRICE_MAP.GBP
  if (EURO_ZONE.has(cc)) return PRICE_MAP.EUR
  return PRICE_MAP.USD
}

export function useCurrency() {
  const currency = ref('USD')
  const symbol = ref('$')
  const prices = ref({ ...PRICE_MAP.USD.prices })
  const country = ref('')
  const loaded = ref(false)

  const currencyLabel = ref(CURRENCY_LABELS.USD)

  async function detect() {
    try {
      const cached = sessionStorage.getItem(STORAGE_KEY)
      if (cached) {
        const data = JSON.parse(cached)
        currency.value = data.currency
        symbol.value = data.symbol
        prices.value = data.prices
        country.value = data.country || ''
        currencyLabel.value = CURRENCY_LABELS[data.currency] || data.currency
        loaded.value = true
        return
      }

      const res = await fetch('https://ipapi.co/json/')
      if (!res.ok) throw new Error('geo lookup failed')
      const json = await res.json()
      const cc = json.country_code || ''
      country.value = cc
      const resolved = resolveCurrency(cc)
      currency.value = resolved.currency
      symbol.value = resolved.symbol
      prices.value = { ...resolved.prices }
      currencyLabel.value = CURRENCY_LABELS[resolved.currency] || resolved.currency

      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          currency: currency.value,
          symbol: symbol.value,
          prices: prices.value,
          country: country.value,
        }),
      )
    } catch {
      const resolved = resolveCurrency('US')
      currency.value = resolved.currency
      symbol.value = resolved.symbol
      prices.value = { ...resolved.prices }
      currencyLabel.value = CURRENCY_LABELS.USD
    } finally {
      loaded.value = true
    }
  }

  onMounted(detect)

  return { currency, symbol, prices, country, loaded, currencyLabel }
}

/**
 * Single source of truth for display pricing + IP-based currency detection.
 * Billing currency is frozen on Organisation.currency at signup (backend) —
 * this composable is for marketing/UI detection only.
 */

import { computed, onMounted, ref } from 'vue'

const STORAGE_KEY = 'plenvo_currency_v2'
export const DEFAULT_CURRENCY = 'USD'

/** Official Eurozone (ISO 3166-1 alpha-2), as of 2026. */
export const EUROZONE = new Set([
  'AT', // Austria
  'BE', // Belgium
  'HR', // Croatia
  'CY', // Cyprus
  'EE', // Estonia
  'FI', // Finland
  'FR', // France
  'DE', // Germany
  'GR', // Greece
  'IE', // Ireland
  'IT', // Italy
  'LV', // Latvia
  'LT', // Lithuania
  'LU', // Luxembourg
  'MT', // Malta
  'NL', // Netherlands
  'PT', // Portugal
  'SK', // Slovakia
  'SI', // Slovenia
  'ES', // Spain
])

export const PRICE_MAP = {
  GBP: {
    currency: 'GBP',
    symbol: '£',
    prices: { personal: '4.99', team: '19.99', enterprise: '49.99' },
  },
  EUR: {
    currency: 'EUR',
    symbol: '€',
    prices: { personal: '4.99', team: '19.99', enterprise: '49.99' },
  },
  USD: {
    currency: 'USD',
    symbol: '$',
    prices: { personal: '4.99', team: '19.99', enterprise: '49.99' },
  },
  INR: {
    currency: 'INR',
    symbol: '₹',
    prices: { personal: '499', team: '1,999', enterprise: '4,999' },
  },
}

export const CURRENCY_LABELS = {
  GBP: 'GBP (£)',
  EUR: 'EUR (€)',
  USD: 'USD ($)',
  INR: 'INR (₹)',
}

export const SUPPORTED_CURRENCIES = Object.keys(PRICE_MAP)

/**
 * Map ISO country code → billing/display currency.
 * GB → GBP, IN → INR, Eurozone → EUR, US + everything else → USD.
 */
export function resolveCurrencyFromCountry(countryCode) {
  const cc = String(countryCode || '').trim().toUpperCase()
  if (cc === 'GB') return PRICE_MAP.GBP
  if (cc === 'IN') return PRICE_MAP.INR
  if (EUROZONE.has(cc)) return PRICE_MAP.EUR
  return PRICE_MAP.USD
}

export function getCurrencyConfig(code) {
  const key = String(code || '').trim().toUpperCase()
  return PRICE_MAP[key] || PRICE_MAP[DEFAULT_CURRENCY]
}

export function formatPrice(symbol, amount) {
  return `${symbol}${amount}`
}

function applyConfig(target, config, countryCode = '') {
  target.currency.value = config.currency
  target.symbol.value = config.symbol
  target.prices.value = { ...config.prices }
  target.currencyLabel.value = CURRENCY_LABELS[config.currency] || config.currency
  if (countryCode !== undefined) target.country.value = countryCode || ''
}

export function useCurrency() {
  const currency = ref(DEFAULT_CURRENCY)
  const symbol = ref(PRICE_MAP[DEFAULT_CURRENCY].symbol)
  const prices = ref({ ...PRICE_MAP[DEFAULT_CURRENCY].prices })
  const country = ref('')
  const loaded = ref(false)
  const currencyLabel = ref(CURRENCY_LABELS[DEFAULT_CURRENCY])

  const state = { currency, symbol, prices, country, currencyLabel }

  const personalPrice = computed(() => formatPrice(symbol.value, prices.value.personal))
  const teamPrice = computed(() => formatPrice(symbol.value, prices.value.team))
  const enterprisePrice = computed(() => formatPrice(symbol.value, prices.value.enterprise))

  async function detect(options = {}) {
    const force = Boolean(options?.force)
    try {
      if (!force) {
        const cached = sessionStorage.getItem(STORAGE_KEY)
        if (cached) {
          const data = JSON.parse(cached)
          const config = getCurrencyConfig(data.currency)
          applyConfig(state, config, data.country || '')
          loaded.value = true
          return
        }
      }

      const res = await fetch('https://ipapi.co/json/')
      if (!res.ok) throw new Error('geo lookup failed')
      const json = await res.json()
      const cc = json.country_code || ''
      const resolved = resolveCurrencyFromCountry(cc)
      applyConfig(state, resolved, cc)

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
      applyConfig(state, PRICE_MAP[DEFAULT_CURRENCY], '')
    } finally {
      loaded.value = true
    }
  }

  onMounted(detect)

  return {
    currency,
    symbol,
    prices,
    country,
    loaded,
    currencyLabel,
    personalPrice,
    teamPrice,
    enterprisePrice,
    formatPrice: (amount) => formatPrice(symbol.value, amount),
    detect,
  }
}

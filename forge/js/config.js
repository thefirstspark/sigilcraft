/**
 * Sigil Forge — configuration
 * These values wire the app to Supabase (auth + grimoire) and Whop (checkout).
 */
window.SF_CONFIG = {
  SUPABASE_URL: 'https://qqlodxrzisbwapjcvjoj.supabase.co',
  SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_SPYW_M9_RCnKJOz8RhAIUA_CC2j3SSi',

  // Whop checkout for the Sigil Forge subscription ($11/mo plan, live).
  WHOP_CHECKOUT_URL: 'https://whop.com/checkout/plan_ujSn2WJvMazgD',

  // Annual ($88/yr) checkout — paste the plan link here once the yearly
  // plan exists in Whop and the Annual card on the landing page will appear.
  WHOP_CHECKOUT_URL_ANNUAL: '',

  // Where members manage/cancel their subscription
  WHOP_HUB_URL: 'https://whop.com/orders/',

  PRICE_MONTHLY: '$11',
  PRICE_ANNUAL: '$88',
};

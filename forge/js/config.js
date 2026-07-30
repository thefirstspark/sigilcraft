/**
 * Sigil Forge — configuration
 * These values wire the app to Supabase (auth + grimoire) and Whop (checkout).
 */
window.SF_CONFIG = {
  SUPABASE_URL: 'https://qqlodxrzisbwapjcvjoj.supabase.co',
  SUPABASE_PUBLISHABLE_KEY: 'sb_publishable_SPYW_M9_RCnKJOz8RhAIUA_CC2j3SSi',

  // Whop checkout for the Sigil Forge subscription.
  // Create the product in Whop named "Sigil Forge" and this slug will exist.
  WHOP_CHECKOUT_URL: 'https://whop.com/sparkverse-511c/sigil-forge/',

  // Where members manage/cancel their subscription
  WHOP_HUB_URL: 'https://whop.com/orders/',

  PRICE_MONTHLY: '$11',
  PRICE_ANNUAL: '$88',
};

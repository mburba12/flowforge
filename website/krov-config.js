// Address of the Krov WorkAgent app (the Cloudflare Tunnel public hostname).
// Change this one line if the app lives somewhere else.
window.KROV_APP_URL = "https://app.krovworkagent.com";

// Usage pricing (same formula as the app: docs/KROV_PRICING.md). Price of a cost:
//   (cost + card fixed fee) / (1 - margin - card percent). Keep in step with the server.
window.KROV_PRICING = { costStorageGbMonth: 2.00, costPer1kActions: 0.0245, margin: 0.70, cardPercent: 0.029, cardFixed: 0.30, actionsPerPersonMonth: 6300 };

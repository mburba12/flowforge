# Krov WorkAgent website (Cloudflare Pages)

The public marketing site at krovworkagent.pages.dev. It is static HTML: upload this
folder (or a zip of its contents) in Cloudflare → Workers & Pages → your project →
**Create deployment**.

* `krov-config.js` holds the two settings to keep current:
  * `KROV_APP_URL`: the app's address (the Cloudflare Tunnel hostname, for example
    `https://app.krovworkagent.com`). Log in, Sign up and Portal send people there.
  * `KROV_PRICING`: the same cost and margin numbers as the server
    (`docs/KROV_PRICING.md`), used by the pricing calculator.
* Passwords are never typed on the website. Log in and Sign up pass the email (and
  business name) to the app in the address fragment (`#email=…`), which browsers do not
  send to any server, and people type their password in the app.
* `enterprise-signup.html` only forwards to `signup.html`: every account includes
  everything and pays for usage.

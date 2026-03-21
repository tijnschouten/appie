# Authentication

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/authentication/)

## Login flow

The package uses a browser-assisted login flow exposed through `appie-login`.

The CLI:

- opens a Chrome window
- waits for the AH redirect to `appie://login-exit?code=...`
- exchanges that code for tokens
- stores tokens in `~/.config/appie/tokens.json`

## Token refresh

Access tokens are refreshed automatically when they are close to expiry. Under normal usage, you should only need to run `appie-login` again when the stored refresh token is no longer valid.

## Notes

- This is not an official AH integration.
- AH may change login requirements at any time.

Read next: [Products](products.md) for product search and product detail examples.

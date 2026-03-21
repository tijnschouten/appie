# Authenticatie

Taal: [English](https://tijnschouten.github.io/appie/authentication/) | **Nederlands**

## Loginflow

De package gebruikt een browser-ondersteunde loginflow via `appie-login`.

De CLI:

- opent een Chrome-venster
- wacht op de AH-redirect naar `appie://login-exit?code=...`
- wisselt die code om voor tokens
- slaat tokens op in `~/.config/appie/tokens.json`

## Token-refresh

Access tokens worden automatisch ververst vlak voor ze verlopen. Normaal gesproken hoef je `appie-login` alleen opnieuw te draaien als de refresh token niet meer geldig is.

## Opmerkingen

- Dit is geen officiële AH-integratie.
- AH kan de loginvereisten op elk moment aanpassen.

Lees verder: [Producten](products.md) voor productzoeken en productdetails.

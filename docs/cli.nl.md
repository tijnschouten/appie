# CLI

## `appie-login`

Authenticeer en sla tokens lokaal op:

```bash
uv run appie-login
```

De CLI is bedoeld als een eenmalige of incidentele setupstap. Daarna hoort normaal gebruik op opgeslagen tokens en automatische refresh te leunen.

Verwacht resultaat:
- er opent een Chrome-venster voor login
- de CLI vangt automatisch de redirectcode af
- na het opslaan van tokens verschijnt een succesmelding

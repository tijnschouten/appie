```
Initialize a new Python package called `python-appie` — an unofficial Python client for the Albert Heijn (Dutch supermarket) API.

## Package structure

Use `uv` for project management, `ruff` for linting/formatting, `pytest` for testing.

```
python-appie/
├── src/
│   └── appie/
│       ├── __init__.py
│       ├── auth.py
│       ├── client.py
│       ├── models.py
│       ├── receipts.py
│       ├── products.py
│       └── lists.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_client.py
├── pyproject.toml
├── README.md
└── .github/workflows/ci.yml
```

## pyproject.toml

- name: `python-appie`, import name: `appie`
- Python >= 3.11
- dependencies: `httpx`, `pydantic>=2`
- dev dependencies: `pytest`, `pytest-asyncio`, `respx` (for mocking httpx), `ruff`
- ruff: line-length 100, target py311

## Auth (`auth.py`)

AH uses OAuth2. Implement an `AHAuthClient` class using `httpx.AsyncClient`.

Base URL: `https://api.ah.nl`

### Anonymous token (needed to bootstrap login)
```
POST /mobile-auth/v1/auth/token/anonymous
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  client_id=appie
```
Returns: `{ access_token, refresh_token, expires_in }`

### User login (authorization code flow)
The login flow works as follows:
1. Open browser to: `https://login.ah.nl/secure/oauth/authorize?client_id=appie&redirect_uri=appie://login-exit&response_type=code`
2. User logs in, browser redirects to: `appie://login-exit?code=CODE`
3. Exchange code for tokens:
```
POST /mobile-auth/v1/auth/token
Headers:
  Content-Type: application/x-www-form-urlencoded
Body:
  client_id=appie&grant_type=authorization_code&code=CODE
```

### Token refresh
```
POST /mobile-auth/v1/auth/token
Body:
  client_id=appie&grant_type=refresh_token&refresh_token=REFRESH_TOKEN
```

Implement:
- `get_anonymous_token() -> TokenResponse`
- `login_with_code(code: str) -> TokenResponse`
- `refresh_token(refresh_token: str) -> TokenResponse`
- Auto-refresh logic: check expiry before each request, refresh if needed
- Persist tokens to `~/.config/appie/tokens.json` (create dir if not exists)

## Client (`client.py`)

`AHClient` — the main entry point users interact with.

```python
async with AHClient() as client:
    await client.login()               # handles full auth flow
    receipts = await client.receipts.list()
    products = await client.products.search("melk")
    await client.lists.add_item("Halfvolle melk", quantity=2)
```

- Wraps `AHAuthClient`
- All requests include:
  - `Authorization: Bearer <token>`
  - `User-Agent: Appie/8.22.3`
  - `Content-Type: application/json`
- GraphQL endpoint: `POST https://api.ah.nl/graphql`
- Has a `graphql(query, variables)` helper method

## Models (`models.py`)

Pydantic v2 models:

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"

class Product(BaseModel):
    id: int
    title: str
    brand: str | None = None
    price: float | None = None  # in euros
    unit_size: str | None = None
    image_url: str | None = None

class ReceiptProduct(BaseModel):
    id: int
    name: str
    quantity: float
    price_per_unit: float
    total_price: float

class Receipt(BaseModel):
    id: str
    datetime: datetime
    store_name: str | None = None
    total: float
    products: list[ReceiptProduct]

class ShoppingListItem(BaseModel):
    id: str
    description: str
    quantity: int = 1
    product_id: int | None = None
```

## Receipts (`receipts.py`)

Use GraphQL. Based on the known schema, receipts are split into:
- **In-store receipts** (POS): `posReceipts` query → list, then `posReceiptDetails(id)` for products
- **Online orders**: via order history

Implement `ReceiptsAPI` class:
- `list_pos_receipts(limit=50) -> list[Receipt]` — in-store bonuskaart receipts
- `get_pos_receipt(receipt_id: str) -> Receipt` — with products
- `list_all(limit=50) -> list[Receipt]` — combines both, sorted by date

GraphQL queries to use:

```graphql
# List in-store receipts
query PosReceipts($limit: Int!) {
  posReceipts(limit: $limit) {
    id
    transactionDate
    totalAmount { amount }
    store { name }
  }
}

# Receipt detail with products
query PosReceiptDetails($id: String!) {
  posReceiptDetails(id: $id) {
    id
    transactionDate
    totalAmount { amount }
    store { name }
    receiptLines {
      quantity
      description
      totalPrice { amount }
      unitPrice { amount }
      product { id }
    }
  }
}
```

## Products (`products.py`)

Use REST endpoint:
```
GET /mobile-services/product/search/v2?query=QUERY&sortOn=RELEVANCE&size=10&page=0
```

Implement `ProductsAPI`:
- `search(query: str, limit=10) -> list[Product]`
- `get(product_id: int) -> Product`

## Lists (`lists.py`)

Implement `ListsAPI`:
- `get_list() -> list[ShoppingListItem]` — fetch current shopping list
- `add_item(description: str, quantity=1, product_id=None) -> ShoppingListItem`
- `remove_item(item_id: str) -> None`
- `clear() -> None`

Note: the exact shopping list endpoint may be REST or GraphQL — use GraphQL as default and fall back gracefully. The mutation likely looks like:
```graphql
mutation AddToShoppingList($input: ShoppingListItemInput!) {
  addShoppingListItem(input: $input) {
    id
    description
    quantity
  }
}
```

## Login CLI helper

In `__init__.py`, expose a small CLI entry point `appie-login` that:
1. Prints the AH login URL
2. Asks the user to paste the redirect URL (`appie://login-exit?code=...`)
3. Extracts the code and calls `login_with_code`
4. Saves tokens to `~/.config/appie/tokens.json`
5. Prints "✓ Logged in successfully"

## Tests

- `conftest.py`: fixture with a mocked `AHClient` using `respx`
- `test_auth.py`: test anonymous token fetch, token refresh, token persistence
- `test_client.py`: test that requests include correct headers and Bearer token

## README.md

Include:
- Brief description (unofficial AH API client)
- Install: `uv add python-appie` (or `pip install python-appie`)
- Quick start with login flow + receipts example
- Disclaimer that this is unofficial and may break
- Reference to `gwillem/appie-go` as source for endpoint discovery
```


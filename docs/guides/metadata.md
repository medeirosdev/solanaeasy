# Custom Metadata

Attach arbitrary key-value pairs to payment sessions for your own tracking purposes.

## Usage

```python
session = sdk.create_payment(
    amount=99.90,
    order_id="order_456",
    description="Mechanical Keyboard",
    metadata={
        "user_id": "u_42",
        "sku": "KEYCHRON-Q1",
        "discount_code": "HACKATHON10",
        "campaign": "launch_2026",
    },
)

print(session.metadata)
# {"user_id": "u_42", "sku": "KEYCHRON-Q1", ...}
```

## Where Metadata Appears

Metadata is stored server-side and returned in:

| Method | Field |
|---|---|
| `create_payment()` | `session.metadata` |
| `list_payments()` | `session.metadata` |

## Use Cases

### Customer Tracking

```python
metadata={"user_id": "u_42", "email": "user@example.com"}
```

### Inventory Management

```python
metadata={"sku": "NIKE-AM-001", "warehouse": "SP-01"}
```

### Marketing Attribution

```python
metadata={"campaign": "black_friday", "source": "instagram"}
```

### A/B Testing

```python
metadata={"experiment": "checkout_v2", "variant": "B"}
```

## Constraints

- Keys and values must be **strings**
- Metadata is limited to reasonable size (< 4KB total)
- Metadata is stored as JSON in the backend database

## Filtering by Metadata

!!! note "Coming soon"
    Server-side filtering by metadata fields is planned for a future release. Currently, you can filter client-side:

    ```python
    payments = sdk.list_payments()
    vip = [p for p in payments if p.metadata and p.metadata.get("tier") == "vip"]
    ```

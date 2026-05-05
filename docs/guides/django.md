# Django Integration

Guide to integrating SolanaEasy with a Django application using the synchronous client.

## Setup

```bash
pip install solanaeasy django
```

## Configuration

Add to your `settings.py`:

```python title="settings.py"
SOLANAEASY_API_KEY = "sk_test_1234567890"
SOLANAEASY_WEBHOOK_SECRET = "whsec_test_secret"
SOLANAEASY_BASE_URL = "http://localhost:8000"
```

## Views

```python title="views.py"
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from solanaeasy import SolanaEasy

sdk = SolanaEasy(
    api_key=settings.SOLANAEASY_API_KEY,
    base_url=settings.SOLANAEASY_BASE_URL,
    webhook_secret=settings.SOLANAEASY_WEBHOOK_SECRET,
)


@sdk.on("payment.confirmed")
def handle_confirmed(event):
    from myapp.models import Order
    order = Order.objects.get(session_id=event.session_id)
    order.status = "paid"
    order.tx_hash = event.data.tx_hash
    order.save()


@require_POST
def create_checkout(request):
    """Create a payment session."""
    data = json.loads(request.body)
    session = sdk.create_payment(
        amount=data["amount"],
        order_id=data["order_id"],
        description=data.get("description", ""),
        metadata={"django_user": str(request.user.id)},
    )
    return JsonResponse({
        "session_id": session.session_id,
        "payment_url": session.payment_url,
        "wallet": session.wallet_public_key,
    })


@require_GET
def check_status(request, session_id):
    """Check payment status."""
    status = sdk.check_status(session_id)
    return JsonResponse({
        "state": status.state,
        "message": status.human_message,
    })


@csrf_exempt
@require_POST
def webhook(request):
    """Receive webhook events."""
    try:
        event = sdk.process_webhook(
            payload=request.body,
            signature=request.headers.get("X-SolanaEasy-Signature", ""),
        )
        return JsonResponse({"received": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
```

## URLs

```python title="urls.py"
from django.urls import path
from . import views

urlpatterns = [
    path("api/checkout/", views.create_checkout),
    path("api/status/<str:session_id>/", views.check_status),
    path("webhook/solana/", views.webhook),
]
```

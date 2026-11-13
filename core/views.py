"""Views for the starter page.

`home` is a normal Django view. The only Inertia-specific detail is the
decorator: whatever dict the view returns becomes the page props.
"""

import os
import platform
from datetime import datetime

import django
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from inertia import always, inertia, once, optional

_STARTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _stats() -> dict[str, object]:
    now = datetime.now()
    return {
        "modules": 4,
        "scenarios": 3,
        "methods": 13,
        "computedAt": now.strftime("%H:%M:%S"),
    }


@inertia("Home")
def home(request: HttpRequest) -> dict[str, object]:
    return {
        # always(): included even when a partial reload asks for other props.
        "appName": always(lambda: "SIMTELE Risk"),
        "serverTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": _stats(),
        # Optional props are not evaluated on the first load. They only
        # travel when the client explicitly asks for them with a partial
        # reload (see the button in Home.vue).
        "slowFact": optional(
            lambda: {
                "title": "Prop opcional",
                "body": (
                    "Este dato no viaja en la primera carga: se resolvió en el "
                    "servidor solo cuando Inertia lo pidió con only: ['slowFact']."
                ),
            }
        ),
        # once(): resolved on the first visit and cached by the client. Later
        # visits skip it unless the client asks for a fresh value.
        "serverInfo": once(
            lambda: {
                "python": platform.python_version(),
                "django": django.get_version(),
                "processStartedAt": _STARTED_AT,
                "pid": os.getpid(),
            },
            key="server-info",
        ),
    }


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """Liveness probe used by dev tooling and deployments."""
    return JsonResponse({"status": "ok"})


@require_POST
def greet(request: HttpRequest) -> HttpResponse:
    name = request.POST.get("name", "").strip()
    if name:
        messages.success(request, f"¡Hola, {name}! Tu saludo quedó registrado.")
    else:
        messages.error(request, "Escribe un nombre para enviar el saludo.")
    return redirect("core:home")

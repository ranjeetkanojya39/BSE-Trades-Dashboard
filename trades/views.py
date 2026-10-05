import json
import time
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import services
from .models import Trade

TEMPLATE = Path(__file__).parent / "templates" / "trades" / "dashboard.html"


@require_GET
def dashboard(request):
    return FileResponse(open(TEMPLATE, "rb"), content_type="text/html")


@require_GET
def api_trades(request):
    """DB se turant data - pull chal raha ho tab bhi."""
    limit = int(request.GET.get("limit", 5000))
    offset = int(request.GET.get("offset", 0))
    qs = Trade.objects.all()[offset:offset + limit]
    return JsonResponse({"state": services.snapshot(), "trades": [t.to_dict() for t in qs]})


@csrf_exempt            # demo/assignment: browser fetch POST bina CSRF token ke
@require_POST
def api_pull(request):
    job_id, already = services.start_pull()
    return JsonResponse({"job_id": job_id, "already_running": already,
                         "status_url": "/api/status"}, status=202)


@require_GET
def api_status(request):
    return JsonResponse(services.snapshot())


@csrf_exempt
@require_POST
def api_reset(request):
    """Demo helper: DB clear karo."""
    if services.STATE["status"] == "running":
        return JsonResponse({"error": "pull running"}, status=409)
    Trade.objects.all().delete()
    services.STATE.update(status="idle", page=0, total_pages=0, error=None)
    return JsonResponse({"ok": True})


@require_GET
def api_stream(request):
    """
    Server-Sent Events. ~25s baad stream khud band; browser EventSource auto-reconnect
    karta hai aur Last-Event-ID bhejta hai, jisse missed events replay ho jaate hain.
    """
    hdr = request.headers.get("Last-Event-ID", "")
    last_id = int(hdr) if hdr.isdigit() else services.latest_event_id()

    def gen():
        nonlocal last_id
        deadline = time.monotonic() + settings.STREAM_MAX_SECONDS
        yield f"retry: 500\nid: {last_id}\nevent: hello\ndata: {{}}\n\n"
        while time.monotonic() < deadline:
            events = services.wait_for_events(last_id, deadline - time.monotonic())
            for eid, name, data in events:
                last_id = eid
                yield f"id: {eid}\nevent: {name}\ndata: {json.dumps(data)}\n\n"

    resp = StreamingHttpResponse(gen(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp

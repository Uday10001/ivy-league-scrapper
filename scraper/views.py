from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from .models import Opportunity
from .logic import IvyScraper, SOURCES

UNIVERSITIES = list(SOURCES.keys())


def dashboard(request):
    query      = request.GET.get("q", "").strip()
    uni_filter = request.GET.get("university", "")
    type_filter = request.GET.get("source_type", "")

    qs = Opportunity.objects.all()
    if query:
        qs = qs.filter(title__icontains=query)
    if uni_filter:
        qs = qs.filter(university=uni_filter)
    if type_filter:
        qs = qs.filter(source_type=type_filter)

    opportunities = qs.order_by("-created_at")[:80]
    total_count = Opportunity.objects.count()

    stats = (
        Opportunity.objects.values("university")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "opportunities": opportunities,
        "total_count": total_count,
        "stats": list(stats),
        "universities": UNIVERSITIES,
        "query": query,
        "uni_filter": uni_filter,
        "type_filter": type_filter,
        "source_types": Opportunity.objects.values_list("source_type", flat=True).distinct(),
    }
    return render(request, "scraper/dashboard.html", context)


@require_POST
def trigger_scrape(request):
    university = request.POST.get("university", "").strip()
    scraper = IvyScraper()
    try:
        if university and university in UNIVERSITIES:
            count = scraper.scrape_one(university)
            msg = f"✓ {count} new items from {university}"
        else:
            results = scraper.scrape_all()
            total = sum(results.values())
            detail = ", ".join(f"{u}: {n}" for u, n in results.items() if n > 0) or "none"
            msg = f"✓ {total} new items — {detail}"
        return JsonResponse({"status": "ok", "message": msg})
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)

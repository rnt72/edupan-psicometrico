import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Institution
from .models import Region


class InstitutionsByRegionAPI(LoginRequiredMixin, View):
    """API AJAX: devuelve instituciones filtradas por región"""

    def get(self, request, region_pk):
        region = get_object_or_404(Region, pk=region_pk)
        institutions = region.institutions.order_by("name").values("id", "name", "code")
        return JsonResponse({
            "institutions": list(institutions),
        })


class InstitutionCreateAPI(LoginRequiredMixin, View):
    """API AJAX: crea institución on-the-fly"""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        name = data.get("name", "").strip()
        region_id = data.get("region_id")

        if not name:
            return JsonResponse({"error": "El nombre es obligatorio"}, status=400)
        if not region_id:
            return JsonResponse({"error": "La región es obligatoria"}, status=400)

        region = get_object_or_404(Region, pk=region_id)

        institution, created = Institution.objects.get_or_create(
            name=name,
            region=region,
            defaults={"code": ""},
        )

        return JsonResponse({
            "success": True,
            "institution": {
                "id": institution.id,
                "name": institution.name,
                "code": institution.code,
            },
            "created": created,
        })

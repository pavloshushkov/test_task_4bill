from django.conf import settings
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response

from . import models


class RequestView(APIView):
    http_method_names = ['get', ]

    def get(self, request, amount):
        time = timezone.now()
        find_last_request = models.Request.objects.last()
        max_limit = max(settings.AMOUNT_LIMITS_CONFIG.items())
        min_limit = min(settings.AMOUNT_LIMITS_CONFIG.items())

        if find_last_request:
            delta = (time - find_last_request.time).total_seconds()
            amount_limits = dict(sorted(settings.AMOUNT_LIMITS_CONFIG.items(), reverse=True))
            max_amount, seconds = 0, 0

            if delta > max_limit[0]:
                find_last_request = models.Request.objects.create(time=time)
                delta = (time - find_last_request.time).total_seconds()

            for k, v in amount_limits.items():
                if delta < k:
                    seconds, max_amount = k, v

            if max_amount and seconds:
                if find_last_request.amount + amount <= max_amount:
                    find_last_request.amount += amount
                    find_last_request.save()
                    return Response({"result": "OK"})
                return Response({"error": f"amount limit exeeded ({max_amount}/{seconds}sec)"})

        elif not find_last_request:
            if amount > min_limit[1]:
                return Response({"error": f"amount limit exeeded ({min_limit[1]}/{min_limit[0]}sec)"})
            created = models.Request.objects.create(amount=amount, time=time)
            if created:
                return Response({"result": "OK"})

        return Response({"error": "Ooops! Houston we have a problem!"})

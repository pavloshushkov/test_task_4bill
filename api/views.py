from django.conf import settings
from django.db.models import F, Sum
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response

from . import models
from datetime import timedelta


class RequestView(APIView):
    http_method_names = ['get', ]

    def get(self, request, amount):
        time = timezone.now()
        last_request = models.Request.objects.last()
        max_limit = max(settings.AMOUNT_LIMITS_CONFIG.items())
        min_limit = min(settings.AMOUNT_LIMITS_CONFIG.items())

        if last_request:
            delta = (time - last_request.time).total_seconds()
            max_amount, seconds = 0, 0

            if delta >= max_limit[0]:
                last_request = models.Request.objects.create(time=time)
                delta = 0

            for interval, limit in sorted(settings.AMOUNT_LIMITS_CONFIG.items()):
                if delta < interval:
                    seconds, max_amount = interval, limit
                    break

            if max_amount and seconds:
                if last_request.amount + amount <= max_amount:
                    last_request.amount = F('amount') + amount
                    last_request.save()
                    return Response({"result": "OK"})
                return Response({"error": f"amount limit exeeded ({max_amount}/{seconds}sec)"})

        elif not last_request:
            if amount > min_limit[1]:
                return Response({"error": f"amount limit exeeded ({min_limit[1]}/{min_limit[0]}sec)"})
            created = models.Request.objects.create(amount=amount, time=time)
            if created:
                return Response({"result": "OK"})

        return Response({"error": "Ooops! Houston we have a problem!"})


class RequestSecondView(APIView):
    http_method_names = ['get', ]

    def get(self, request, amount):
        time = timezone.now()
        for interval, limit in sorted(settings.AMOUNT_LIMITS_CONFIG.items(), reverse=True):
            rs_sum = models.Request.objects.filter(
                time__range=[time - timedelta(seconds=interval), time]
            ).aggregate(total=Sum('amount'))['total'] or 0
            if rs_sum + amount <= limit:
                continue
            return Response({"error": f"amount limit exeeded ({limit}/{interval}sec)"})
        created = models.Request.objects.create(amount=amount, time=time)
        if created:
            return Response({"result": "OK"})
        return Response({"error": "Ooops! Houston we have a problem!"})

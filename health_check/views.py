import time

from django.views.generic import TemplateView

from .checks import database_check, redis_check


class HealthCheckP1View(TemplateView):

    template_name = 'health-check.html'
    content_type = 'application/xml'

    CHECKS = [database_check, redis_check]

    def _do_checks(self):
        results = [check() for check in self.CHECKS]

        is_healthy = True if all(status for _, status in results) else False

        return is_healthy, results

    def get_context_data(self, **kwargs):
        start_time = time.time()

        context = super().get_context_data(**kwargs)

        is_healthy, results = self._do_checks()

        results_text = '\n'.join(f'{name}: {status}' for name, status in results)

        context['status'] = 'OK' if is_healthy else results_text
        context['response_time'] = time.time() - start_time

        return context

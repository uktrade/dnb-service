import json

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from dnb_api.client import api_request, DNB_COMPANY_SEARCH_ENDPOINT
from .forms import SearchForm


@method_decorator(login_required, name='dispatch')
class SearchView(FormView):
    form_class = SearchForm
    template_name = 'search.html'

    def form_valid(self, form):
        response = api_request('POST', DNB_COMPANY_SEARCH_ENDPOINT, json=form.cleaned_data)

        if response.status_code == 200:
            results = json.dumps(response.json()['searchCandidates'], indent=4)
        elif response.status_code == 404:
            results = 'No matching results. Try again.'

        context = self.get_context_data()
        context['results'] = results

        return self.render_to_response(context)

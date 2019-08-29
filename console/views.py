import requests
from json2html import json2html

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django.views.generic.base import TemplateView

from dnb_api.client import api_request, DNB_COMPANY_SEARCH_ENDPOINT
from .forms import SearchForm


@method_decorator(login_required, name='dispatch')
class SearchView(FormView):
    form_class = SearchForm
    template_name = 'search.html'

    def form_valid(self, form):

        try:
            response = api_request('POST', DNB_COMPANY_SEARCH_ENDPOINT, json=form.cleaned_data)

        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 404:
                results = 'No matching results. Try again.'
            else:
                raise
        else:
            results = [{'raw': result['organization'], 'html': json2html.convert(result['organization'])}
                       for result in response.json()['searchCandidates']]

        context = self.get_context_data()
        context['results'] = results

        return self.render_to_response(context)


@method_decorator(login_required, name='dispatch')
class DetailView(TemplateView):
    template_name = 'detail.html'

    def get(self, request, duns, *args, **kwargs):
        #api_endpoint = f'https://plus.dnb.com/v1/data/duns/{duns}?productId=cmptcs&versionId=v1'
        api_endpoint = f'https://plus.dnb.com/v1/data/duns/{duns}?productId=cmpelk&versionId=v2'

        try:
            response = api_request('GET', api_endpoint)

        except requests.exceptions.HTTPError as err:
            import pdb; pdb.set_trace()
            if err.response.status_code == 404:
                results = 'No matching results.'
            else:
                raise
        except Exception as ex:
            import pdb; pdb.set_trace()
        else:
            data = response.json()['organization']
            result = {
                'raw': data,
                'html': json2html.convert(data, clubbing=False)
            }

        context = self.get_context_data(**kwargs)
        context['result'] = result

        return self.render_to_response(context)




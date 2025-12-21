from rest_framework.pagination import PageNumberPagination


#  forcing the pagination not to overthrow the perfomance of the system in viewing items

class StandardResultsSetPagination (PageNumberPagination):

    page_size = 10 # default number of items to be rendered on the webpages
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        return page_size
    
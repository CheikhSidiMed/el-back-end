from rest_framework.pagination import PageNumberPagination

class EtudiantPagination(PageNumberPagination):
    page_size = 50                  # default
    page_size_query_param = 'page_size'  # ?page_size=20
    max_page_size = 100             # safety limit
    page_query_param = 'page'       # ?page=2

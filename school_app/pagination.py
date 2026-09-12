from rest_framework.pagination import PageNumberPagination

class EtudiantPagination(PageNumberPagination):
    page_size = 1000                  # default
    page_size_query_param = 'page_size'  # ?page_size=20
    max_page_size = 1100             # safety limit
    page_query_param = 'page'       # ?page=2

class AgentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

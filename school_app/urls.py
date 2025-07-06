from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'branches', BrancheViewSet)
router.register(r'classes', ClasseViewSet)
router.register(r'levels', NiveauViewSet)
router.register(r'agents', AgentViewSet)
router.register(r'etudiants', EtudiantViewSet)
router.register(r'activitys', ActivityViewSet)
router.register(r'mois', MoisViewSet)
router.register(r'paiements', PaiementViewSet)
router.register(r'academic-years', AcademicYearViewSet)



router.register(r'utilisateurs', UtilisateurViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

]

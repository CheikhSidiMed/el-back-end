from rest_framework import serializers
from .models import Branche, Classe, Niveau, Agent, Etudiant, Mois, Paiement, Utilisateur, Activity, AcademicYear, MonthlyReport, DailyAbsence
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class BrancheSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branche
        fields = '__all__'

class ClasseSerializer(serializers.ModelSerializer):
    # → visible UNIQUEMENT dans la réponse (GET)
    branche = BrancheSerializer(read_only=True)

    # → utilisé UNIQUEMENT à la création / mise à jour (POST / PATCH)
    branche_id = serializers.PrimaryKeyRelatedField(
        source='branche',                 # fait le lien avec le FK `branche`
        queryset=Branche.objects.all(),
        write_only=True
    )

    class Meta:
        model = Classe
        fields = ['id', 'nom', 'niveau', 'branche', 'branche_id']


class NiveauSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveau
        fields = '__all__'

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class EtudiantSerializer(serializers.ModelSerializer):
    level = NiveauSerializer(read_only=True)
    classe = ClasseSerializer(read_only=True)
    branche = BrancheSerializer(read_only=True)
    agent = AgentSerializer(read_only=True)

    level_id = serializers.PrimaryKeyRelatedField(
        queryset=Niveau.objects.all(), source='level', write_only=True, required=False
    )
    classe_id = serializers.PrimaryKeyRelatedField(
        queryset=Classe.objects.all(), source='classe', write_only=True
    )
    branche_id = serializers.PrimaryKeyRelatedField(
        queryset=Branche.objects.all(), source='branche', write_only=True
    )
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), source='agent', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Etudiant
        fields = '__all__'


class MoisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mois
        fields = '__all__'

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'


class MonthlyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReport
        fields = '__all__'

class DailyAbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAbsence
        fields = '__all__'



class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id', 'phone', 'role', 'first_name', 'password', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Utilisateur(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: Utilisateur):
        token = super().get_token(user)
        # you can add custom claims if you like:
        # token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Now inject the serialized user data into the response:
        data['user'] = UtilisateurSerializer(self.user).data
        return data

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AcademicYear
        fields = ("id", "year", "start_date", "end_date")
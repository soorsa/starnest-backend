from rest_framework import serializers
from django.db import transaction,models
from .models import *
from users.models import User

class SavingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingPlan
        # fields = '__all__'
        fields = ['id', 'name', 'image', 'description', 'benefits', 'video_link', 'amount_per_cycle', 'type', 'duration', 'interest_rate', 'total_savings', 'reward', 'expected_total_payment', 'created_at']
class UserSavingSerializer(serializers.ModelSerializer):
    plan_object = SavingPlanSerializer(source="plan", read_only=True)
    class Meta:
        model = UserSavings
        depth = 2
        fields = ['id', 'start_date', 'end_date', 'next_payment_date', 'total_paid', 'current_cycle', 'completed', 'completed_clearance', 'user', 'plan', 'plan_object', 'progress_percentage', 'amount_per_month', 'total_target', 'reward', 'hands', 'total_recieveable', 'payment_schedule']
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        depth = 2
        fields = '__all__'

class DetailedUserSerializer(serializers.ModelSerializer):
    plans = UserSavingSerializer(source="plan", many=True)
    # user_transactions = TransactionSerializer(source="transactions", many=True)
    total_plans = serializers.SerializerMethodField()
    total_hands = serializers.SerializerMethodField()
    total_savings = serializers.SerializerMethodField()
    total_recieveable = serializers.SerializerMethodField()
    deposits = serializers.SerializerMethodField()
    withdrawals = serializers.SerializerMethodField()

    def get_total_plans(self, obj):
        return obj.plan.count()
    def get_total_hands(self, obj):
        plans = obj.plan
        hands = plans.aggregate(total=models.Sum("hands"))["total"] or 0
        return hands
    def get_total_savings(self, obj):
        plans = obj.plan
        amount = plans.aggregate(total=models.Sum("total_paid"))["total"] or 0
        return amount
    def get_total_recieveable(self, obj):
        amount = 0
        plans = obj.plan
        for plan in plans.all():
            amount += plan.total_recieveable
        return amount
    def get_deposits(self,obj):
        transactions = obj.transactions.filter(type="deposit")
        return TransactionSerializer(transactions, many=True).data
    def get_withdrawals(self,obj):
        transactions = obj.transactions.filter(type="withdrawal")
        return TransactionSerializer(transactions, many=True).data

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'plans', 'total_plans', 'total_hands', 'total_savings',
                 'total_recieveable', 'phone_number', 'profile_picture', 'date_of_birth', 'state','city', 'address', 'country',
                 'is_verified', 'created_at', 'deposits', 'withdrawals' )
        read_only_fields = ('id', 'email', 'role', 'created_at', 'is_verified')

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

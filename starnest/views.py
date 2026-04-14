from django.shortcuts import render, get_object_or_404
from rest_framework import status, generics, views
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes,action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated,IsAdminUser

from .serializers import *
from .models import *
from users.serializers import *
from users.models import *
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncMonth
from django.db import transaction

# Create your views here.
class SavingPlanApiset(viewsets.ModelViewSet):
    queryset = SavingPlan.objects.all()
    serializer_class = SavingPlanSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name", "type", "duration"]
    ordering_fields = ["created_at", "duration", "interest_rate"]
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [AllowAny()]
    
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        plan = get_object_or_404(SavingPlan, id=pk)
        active_plans_qs = UserSavings.objects.filter(plan=plan)
        active_users = active_plans_qs.values("user").distinct().count()
        active_plans = active_plans_qs.count()
        total_hands = active_plans_qs.aggregate(total=models.Sum("hands"))["total"] or 0
        total_deposited_balance = active_plans_qs.aggregate(total=models.Sum("total_paid"))["total"] or 0
        data = {
            "active_plans":active_plans,
            "active_users":active_users,
            "total_hands":total_hands,
            "total_deposited_balance":total_deposited_balance,
        }
        return Response(data)

class UserSavingApiset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSavingSerializer
    filterset_fields = ["plan__name", "completed", "plan__duration", "user"]
    ordering_fields = ["start_date", "end_date", "completed","plan__duration"]
    def get_queryset(self):
        if self.request.user.is_staff:
            return UserSavings.objects.all().order_by("-start_date")
        return UserSavings.objects.filter(user=self.request.user).order_by("-start_date")
    
    @action(detail=False, methods=["post"])
    def join(self, request):
        with transaction.atomic():
            user = request.user
            id = request.data.get("plan_id")
            hands = request.data.get("hands")
            number_of_months = request.data.get("number_of_months")
            plan = get_object_or_404(SavingPlan, id=id)
            if plan.is_active:
                if plan.type == "monthly":
                    total_paid = (number_of_months * plan.amount_per_cycle)*hands
                    next_payment_date = date.today()+timedelta(days=30)
                else:
                    total_paid = plan.amount_per_cycle * hands
                    next_payment_date = date.today() + timedelta(days=30*number_of_months)
                user_savings = UserSavings.objects.create(user=user,plan=plan, hands=hands, current_cycle=number_of_months,next_payment_date=next_payment_date,total_paid=total_paid)
                Transaction.objects.create(user=user, user_savings=user_savings, amount=total_paid, ref="paymentRef", type="deposit", status="success")
                return Response({"message":f'You have successfully joined {plan.name}',"plan_id":user_savings.pk}, status=status.HTTP_201_CREATED)
            return Response({'message':f'This plan is not active'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'message':'unable to join plan at the moment'}, status=status.HTTP_409_CONFLICT)
    
    @action(detail=False, methods=["post"])
    def make_deposit(self, request):
        with transaction.atomic():
            user = request.user
            id = request.data.get("user_plan_id")
            number_of_months = request.data.get("number_of_months")
            user_plan = get_object_or_404(UserSavings, id=id)
            if user_plan.user == user:
                amount = number_of_months * user_plan.amount_per_month
                if user_plan.total_paid >= user_plan.total_target:
                    user_plan.completed=True
                    user_plan.save()
                    return Response({"message":"You have already reached your target savings"},status=status.HTTP_208_ALREADY_REPORTED)
                user_plan.total_paid += amount
                user_plan.next_payment_date += timedelta(days=30*number_of_months)
                user_plan.current_cycle += number_of_months
                user_plan.save()
                Transaction.objects.create(user=user, user_savings=user_plan, type="deposit", amount=amount, ref="paymentRef", status="success")

                if user_plan.total_paid >= user_plan.total_target:
                    user_plan.completed=True
                    user_plan.save()
                    return Response({"message":"you have successfully reached your target"}, status=status.HTTP_200_OK)
                return Response({"message":f'You have successfully made deposit for {user_plan.next_payment_date - timedelta(days=30)}'}, status=status.HTTP_200_OK)
            return Response({'message':f'You have not joined this plan'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'message':'unable to join plan at the moment'}, status=status.HTTP_409_CONFLICT)
    @action(detail=True, methods=["POST"])
    def clearance(self, request, pk=None):
        user = request.user
        user_plan = get_object_or_404(UserSavings, pk=pk)
        is_matured = date.today() >= user_plan.end_date.date()
        have_meet_target = user_plan.progress_percentage >= 100 and user_plan.completed
        if have_meet_target and is_matured:
            user_plan.completed_clearance = True
            user_plan.save()
            withdrawal_request = Transaction.objects.create(user=user, user_savings = user_plan, ref = "Withdrawal", amount = user_plan.plan.expected_total_payment, type="withdrawal", status= "pending")
            withdrawal = TransactionSerializer(withdrawal_request)
            return Response({"message":"Congrats!... you have completed clearance for this plan", "withdrawal":withdrawal.data}, status=status.HTTP_201_CREATED)
        return Response({"message":"You are not authorized to proceed with clearance at the moment"}, status=status.HTTP_400_BAD_REQUEST)
    
class TransactionApiset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "type", "amount"]
    ordering_fields = ["created_at", "status", "amount"]
    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all().order_by("-created_at")
        return Transaction.objects.filter(user_savings__user=self.request.user).order_by("-created_at")

class UsersApiset(viewsets.ModelViewSet):
    # permission_classes = [IsAdminUser]
    serializer_class = DetailedUserSerializer
    filterset_fields = ["email", "first_name", "last_name",]
    ordering_fields = ["first_name",]
    def get_permissions(self):
        if self.action in ['retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]
    def get_queryset(self):
        return User.objects.all()
    
class AdminStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        total_users = users.count()

        # Better way to count active users (users who have at least one plan)
        active_users = User.objects.filter(plan__isnull=False).distinct().count()

        plans = SavingPlan.objects.all()
        total_plans = plans.count()

        active_plans_qs = UserSavings.objects.all()   # or .filter(completed=False) if that's what "active" means

        total_active_plans = active_plans_qs.count()
        total_savings = active_plans_qs.aggregate(total=Sum("total_paid"))["total"] or 0

        transactions = Transaction.objects.all()
        deposits = transactions.filter(type="deposit")
        withdrawals = transactions.filter(type="withdrawal")

        monthly_deposits = (
            Transaction.objects.filter(type="deposit", status="success")
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )
        total_deposits = deposits.aggregate(total=Sum("amount"))["total"] or 0
        total_withdrawals = withdrawals.aggregate(total=Sum("amount"))["total"] or 0

        # ────────────────────────────────────────────────
        # Calculate total_recieveable in Python
        total_amount_of_active_plans = 0
        for plan in active_plans_qs.iterator():          # iterator() = lower memory usage
            total_amount_of_active_plans += plan.total_recieveable
        # ────────────────────────────────────────────────

        data = {
            "total_users": total_users,
            "active_users": active_users,
            "total_plans": total_plans,
            "active_plans": total_active_plans,
            "total_deposits": total_deposits,
            "monthly_deposits": monthly_deposits,
            "total_withdrawals": total_withdrawals,
            "total_savings": total_savings,
            "total_amount_of_active_plans": total_amount_of_active_plans,
        }
        return Response(data)
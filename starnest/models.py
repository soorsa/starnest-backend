from django.db import models
from datetime import date,timedelta
from users.models import User
STATUS_CHOICE =[
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed")
]
WITHDRAWAL_STATUS_CHOICE =[
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed")
]
PLAN_TYPE =[
        ("one time", "One Time"),
        ("monthly", "Monthly")
]
TRANSACTION_TYPE =[
        ("deposit", "Deposit"),
        ("withdrawal", "withdrawal")
]
# Create your models here.
class SavingPlan(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='plans', blank=True, null=True, default='plan.jpg')
    video_link = models.CharField(max_length=1000, blank=True, null=True)
    description = models.TextField(blank=True)
    amount_per_cycle = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=PLAN_TYPE)
    duration = models.IntegerField(help_text="Number of cycles")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    benefits = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_savings(self):
        if self.type == "one time":
            return self.amount_per_cycle
        return self.amount_per_cycle * self.duration
    @property
    def reward(self):
        return self.total_savings * (self.interest_rate/100)
    @property
    def expected_total_payment(self):
        return self.reward + self.total_savings

class UserSavings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plan")
    plan = models.ForeignKey(SavingPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    hands = models.PositiveIntegerField(default=1)
    next_payment_date = models.DateField()
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_cycle = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_clearance = models.BooleanField(default=False)

    @property
    def end_date(self):
        return self.start_date + timedelta(days=self.plan.duration*30)
    @property
    def amount_per_month(self):
        return self.plan.amount_per_cycle * self.hands
    @property
    def total_target(self):
        if self.plan.type == "one time":
            return self.amount_per_month
        return self.amount_per_month * self.plan.duration
    @property
    def progress_percentage(self):
        return (self.total_paid / self.total_target) * 100
    @property
    def reward(self):
        return self.plan.reward * self.hands
    @property
    def total_recieveable(self):
        return self.total_target + self.reward
    @property
    def payment_schedule(self):
        schedule = []
        payment_date = self.start_date.date()
        today = date.today()
        if self.plan.type == "monthly":
            duration = self.plan.duration +1
        else:
            duration = 2

        for cycle in range(1, duration):

            if cycle <= self.current_cycle:
                status = "paid"

            elif payment_date < today:
                status = "missed"

            else:
                status = "upcoming"

            schedule.append({
                "cycle": cycle,
                "date": payment_date,
                "status": status
            })
            payment_date += timedelta(days=30)
        return schedule
        
class Transaction(models.Model):
    user_savings = models.ForeignKey(UserSavings, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    ref = models.CharField(max_length=255)
    type = models.CharField(max_length=20, default="deposit", choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, default="pending", choices=STATUS_CHOICE)
    created_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
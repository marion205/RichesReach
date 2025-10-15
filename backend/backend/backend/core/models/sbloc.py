from django.db import models

class SblocBank(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField(blank=True)
    min_apr = models.FloatField(default=0.06)
    max_apr = models.FloatField(default=0.12)
    min_ltv = models.FloatField(default=0.30)
    max_ltv = models.FloatField(default=0.50)
    min_loan_usd = models.IntegerField(default=5000)
    regions = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

class SblocReferral(models.Model):
    user_id = models.IntegerField(null=True, blank=True)  # or FK to your User
    bank = models.ForeignKey(SblocBank, on_delete=models.PROTECT)
    amount_usd = models.IntegerField()
    status = models.CharField(max_length=32, default='DRAFT')
    external_ref = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SblocSession(models.Model):
    referral = models.ForeignKey(SblocReferral, on_delete=models.CASCADE)
    application_url = models.URLField()
    external_session_id = models.CharField(max_length=128)
    status = models.CharField(max_length=32, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)

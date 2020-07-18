from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def greylisted(address, ip):
    if not settings.GREYLIST_ENABLED:
        return None

    if ip in settings.WHITELISTED_IPS:
        return None

    qs = DonationRequest.objects.filter(address=address) | DonationRequest.objects.filter(ip=ip)
    cooldown = timedelta(seconds=settings.GREYLIST_COOLDOWN)
    cooldown_at = timezone.now() - cooldown
    latest_request = qs.filter(requested__gte=cooldown_at).order_by("-requested").first()
    return None if latest_request is None else (latest_request.requested + cooldown)


class Faucet(models.Model):

    asset_code = models.CharField(max_length=12)
    """ The short code of the asset type, eg 'BTC' """

    name = models.CharField(max_length=120)
    """ The display name for this asset """

    asset_id = models.UUIDField(unique=True)
    """ The ID of the asset in the Upvest API """

    sending_amount = models.DecimalField(max_digits=40, decimal_places=15)
    """ How much of the asset should sent on each sending request """

    fee = models.DecimalField(max_digits=40, decimal_places=15)
    """ How much to set as the sending fee """

    def send(self, wallet, receive_address, ip):
        # record the request first to prevent too many requests
        DonationRequest.objects.create(address=receive_address, ip=ip)

        balance = self.get_balance(wallet)
        # the internal representation is the more human-friendly decimal version
        # but the API accepts only whole integers
        quantity = int(self.sending_amount * (10 ** balance["exponent"]))
        fee = int(self.fee * (10 ** balance["exponent"]))
        return wallet.transactions.create(settings.UPVEST_PASSWORD, str(self.asset_id), quantity, fee, receive_address, asynchronous=True)

    def get_balance(self, wallet):
        for bal in wallet.balances:
            if bal["asset_id"] == str(self.asset_id):
                return bal
        raise ValueError("No balance for asset %s" % self.asset_id)

    def __str__(self):
        visible = "visible" if self.visible else "not visible"
        return "Sending %s %s (%s)" % (self.sending_amount, self.asset_code, visible)


class DonationRequest(models.Model):

    address = models.CharField(max_length=42)
    """ The wallet to send ETH to """

    ip = models.GenericIPAddressField()
    """ The IP address making the request """

    requested = models.DateTimeField(auto_now_add=True)
    """ When this was requested - for greylisting purposes """

    def __str__(self):
        return "%s requested by %s at %s" % (self.address, self.ip, self.requested)

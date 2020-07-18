import re
from django.conf import settings

from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.utils.timesince import timeuntil
from django.views import View
from decimal import Decimal

from .models import greylisted, Faucet
from upvest.clientele import UpvestClienteleAPI


WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{30,40}$")


def _get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class FaucetView(View):

    curl = False

    def get_api(self):
        """
        This method is a shorthand for getting an Upvest API client for a
        specific user. It uses first the OAuth ID and Secret for the application
        itself, and then uses the user's username and password.
        """
        return UpvestClienteleAPI(
            settings.UPVEST_OAUTH_CLIENT_ID,
            settings.UPVEST_OAUTH_CLIENT_SECRET,
            settings.UPVEST_USERNAME,
            settings.UPVEST_PASSWORD,
            # the playground API is the default, however if you are feeling
            # rich you could change it to use the main API and use mainnet tokens and coins
            base_url=settings.UPVEST_BACKEND,
            user_agent=settings.UPVEST_USER_AGENT,
        )

    def get_wallets(self):
        """
        Finds all the wallets that the Faucet user has then filters them into
        a list of wallets for the assets this Faucet serves.
        """
        asset_ids = {str(faucet.asset_id) for faucet in Faucet.objects.all()}
        wallets = {}
        for wallet in self.get_api().wallets.all():
            # wallets can have multiple balances if they have multiple assets
            # in them. For example, ETH and ECR20 tokens are all part of the same
            # wallet as they are generated from the same original private key.
            for balance in wallet.balances:
                if balance["asset_id"] in asset_ids:
                    wallets[balance["asset_id"]] = wallet
        return wallets

    def get_base_context(self):
        # first see if there is a specific asset requested in the URL
        asset_code = self.kwargs.get("asset")
        wallets = self.get_wallets()

        # also list other faucets to get links to other assets other than the chosen one
        faucets = Faucet.objects.filter(asset_id__in=wallets.keys()).order_by("asset_code")

        if asset_code is not None:
            # find the asset definition
            faucet = get_object_or_404(Faucet, asset_code__iexact=asset_code)
            wallet = wallets.get(str(faucet.asset_id))
        else:
            # otherwise find the first faucet the user has a wallet for
            for faucet in Faucet.objects.all():
                asset_id = str(faucet.asset_id)
                if asset_id in wallets:
                    wallet = wallets[asset_id]
                    break

        if wallet is None:
            # if this user does not have a wallet for that asset, then can't serve anything
            raise Http404

        balance_obj = faucet.get_balance(wallet)
        balance = Decimal(balance_obj["amount"]) / Decimal(10 ** balance_obj["exponent"])

        return {"faucet": faucet, "faucets": faucets, "wallet": wallet, "wallets": wallets, "balance": balance}

    def get(self, request, *args, **kwargs):
        ctx = self.get_base_context()

        if self.curl:
            # the "API" version
            ip = _get_client_ip(request)
            address = kwargs["address"]
            if kwargs.get("asset") is None:
                return JsonResponse({"message": "You must specify an asset code to send"}, status=400)

            for skip_header in settings.WHITELISTED_HEADERS:
                header = "HTTP_%s" % skip_header.replace("-", "_")
                if header in request.META:
                    cooldown_at = None
                    break
            else:
                cooldown_at = greylisted(address, ip)

            if cooldown_at:
                return JsonResponse(
                    {"message": "You are greylisted for another %s" % timeuntil(cooldown_at)}, status=403
                )
            else:
                tx = ctx["faucet"].send(ctx["wallet"], address, ip)
                amount = "%s%s" % (ctx["faucet"].sending_amount.normalize(), ctx["faucet"].asset_code)
                return JsonResponse(
                    {
                        "message": "Request received successfully. %s will be sent to %s" % (amount, address),
                        "tx": tx.id,
                    },
                    status=200,
                )

        return render(request, "faucet.html", context=ctx)

    def post(self, request, *args, **kwargs):
        address = request.POST.get("address")
        ctx = self.get_base_context()
        ctx["address"] = address

        if not address:
            messages.error(request, "You must supply a wallet address")
        elif not WALLET_RE.match(address):
            messages.error(request, "That does not seem to be a valid wallet address")
        else:
            ip = _get_client_ip(request)
            cooldown_at = greylisted(address, ip)
            if cooldown_at:
                messages.warning(request, "You are greylisted for another %s" % timeuntil(cooldown_at))
            else:
                tx = ctx["faucet"].send(ctx["wallet"], address, ip)

                amount = "%s%s" % (ctx["faucet"].sending_amount.normalize(), ctx["faucet"].asset_code)
                messages.info(request, "Request received successfully. %s will be sent to %s" % (amount, address))
                ctx["tx"] = tx

        return render(request, "faucet.html", context=ctx)

# Upvest Faucet

This is a demonstration project to show how to set up and run a very
simple application on the Upvest API.

With a few credentials, it will run as a simple faucet, dispensing tokens
or coins to whichever address requests it.

The purpose is to have an example of how to send from a wallet once it
has been created and funded on the Upvest API.

# Step 1 : Create a faucet user and wallet

First, [login to or create your Upvest account](http://login.upvest.co). After
that, you will have an application on the sandbox API to be able to use testnet
tokens and coins.

Using your API key, you will need to first create a user in your application.
This user will be the one used by the faucet to access wallets and create transactions.

Once you have a user, create one or more wallets for that user for the tokens or
coins you wish to serve from your faucet.

You can read up on how to create a user and wallet in [the quickstart guides](https://doc.upvest.co/docs/command-line-quickstart) in the documentation.

# Step 2 : Configure the faucet

Now that you have a user and a wallet, you need to configure the faucet to
use them.  This is done via setting the following environment variables:

```
# the OAuth values for your application:
export UPVEST_OAUTH_CLIENT_ID=...
export UPVEST_OAUTH_CLIENT_SECRET=...
# the username and password of the user you created in your application:
export UPVEST_USERNAME=<username>
export UPVEST_PASSWORD=<password>
```

When running, the faucet application will use these credentials to authenticate
as the application user, fetching the list of wallets. Note that every single
wallet is assumed to be a faucet!

# Step 3 : How to run

First, if you haven't already, you will probably want to fund your faucet wallets
from one of the public faucets, for example for Ethereum Ropsten: https://faucet.ropsten.be

## From dockerhub

If you just want to run your own faucet, you don't even need to check out the
repository. Add those environment variables to a docker envfile, so for example `env.list`:

```
UPVEST_OAUTH_CLIENT_ID=...
UPVEST_OAUTH_CLIENT_SECRET=...
UPVEST_USERNAME=<username>
UPVEST_PASSWORD=<password>
```

Then run:

`docker run --env-file env.list -p 80:8000 upvest/faucet`

Then you can visit the faucet at http://127.0.0.1.

## From the repository via docker-compose

If you have checked out this repository, simply run:

`docker-compose up`

Then you can visit http://127.0.0.1.

## Running Django directly

If you have checked out the repository, you can create a Python3 virtualenv
and install and run this Django project. This is the best way to run if you
want to experiment and edit the code too.

First install the dependencies:

`pip install -e .[dev]`

Then `cd` into the faucet application directory and setup the database:

```
python manage.py migrate
python manage.py loaddata faucets
```

By default this will create a local sqlite database, you can change this by
setting the `DATABASE_URL` environment variable. There is nothing useful in the
database except the greylist though: all wallet balance and transaction data is
from the Upvest API.

Now you can run the server:

`python manage.py runserver`

Then you can visit http://127.0.0.1:8000

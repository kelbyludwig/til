# the header text
BLOG_NAME = "til"

# where the sqlite db is stored
SQLITE_PATH = "sqlite:///til.sqlite"

# username for authentication
USERNAME = None  # change to e.g. "my_username" to enable authentication

# duo websdk integration credentials
# note: you probably want a webauthn/u2f-only policy since we aren't using a
# first-factor.
DUO_IKEY = "DI..."
DUO_SKEY = "this should be random"
DUO_AKEY = "this should also be random"
DUO_HOST = "api-stuff.duosecurity.com"

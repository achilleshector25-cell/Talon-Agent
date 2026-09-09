def test_token_vault_binding():
    from talon.gateway.token_vault import TokenVault
    from talon.gateway.mtls import Identity
    vault = TokenVault()
    ident = Identity(spiffe_id="spiffe://talon/owner/test", role="owner", channel="telegram", fingerprint="fp123")
    token = vault.mint(ident, ip="1.2.3.4", ttl=900)
    assert vault.validate(token, "fp123", "1.2.3.4") is not None
    assert vault.validate(token, "wrong", "1.2.3.4") is None

def test_token_budget_does_not_start_with_negative_balance():
    from talon.runtime.token_budget import TokenBucket

    budget = TokenBucket(daily_budget=100)
    assert budget.remaining == 100
    assert budget.consume(1) is True

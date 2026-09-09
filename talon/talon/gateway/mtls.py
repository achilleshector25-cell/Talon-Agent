"""mTLS identity derivation with strict SPIFFE validation.

Transport-level mTLS should be terminated by a trusted proxy.  This module
still validates the certificate shape and can additionally validate it against
an explicitly configured CA certificate.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, ed448, padding, rsa

@dataclass(frozen=True)
class Identity:
    spiffe_id: str
    role: Literal["owner","guest","system"]
    channel: str
    fingerprint: str
    is_owner: bool = field(default=False, init=False)  # SERVER-DERIVED

    def __post_init__(self) -> None:
        if self.role not in {"owner", "guest", "system"}:
            raise ValueError("unsupported identity role")
        object.__setattr__(self, "is_owner", self.role == "owner")


def _verify_signed_by(cert: x509.Certificate, ca: x509.Certificate) -> None:
    if cert.issuer != ca.subject:
        raise ValueError("client certificate issuer is not trusted")
    key = ca.public_key()
    if isinstance(key, rsa.RSAPublicKey):
        key.verify(cert.signature, cert.tbs_certificate_bytes, padding.PKCS1v15(), cert.signature_hash_algorithm)
    elif isinstance(key, ec.EllipticCurvePublicKey):
        key.verify(cert.signature, cert.tbs_certificate_bytes, ec.ECDSA(cert.signature_hash_algorithm))
    elif isinstance(key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
        key.verify(cert.signature, cert.tbs_certificate_bytes)
    else:
        raise ValueError("unsupported client CA key type")


def derive_identity_from_cert(
    pem_bytes: bytes,
    channel: str,
    trusted_ca_pem: bytes | None = None,
) -> Identity:
    if channel not in {"telegram", "discord", "slack", "whatsapp", "api"}:
        raise ValueError("unsupported channel")
    cert = x509.load_pem_x509_certificate(pem_bytes, default_backend())
    now = datetime.now(timezone.utc)
    if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
        raise ValueError("client certificate is not currently valid")
    try:
        eku = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    except x509.ExtensionNotFound as exc:
        raise ValueError("client certificate is missing clientAuth usage") from exc
    if x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH not in eku:
        raise ValueError("client certificate is not valid for client authentication")
    if trusted_ca_pem:
        ca = x509.load_pem_x509_certificate(trusted_ca_pem, default_backend())
        _verify_signed_by(cert, ca)

    # SAN URI must be exactly spiffe://talon/{role}/{stable-id}.
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    uris = san.get_values_for_type(x509.UniformResourceIdentifier)
    parsed = [
        urlsplit(uri)
        for uri in uris
        if uri.startswith("spiffe://") and urlsplit(uri).netloc == "talon"
    ]
    if not parsed:
        raise ValueError("No SPIFFE ID in cert")
    identity_uri = next(
        (
            item
            for item in parsed
            if item.scheme == "spiffe"
            and item.netloc == "talon"
            and len(item.path.split("/")) == 3
            and item.path.split("/")[1] in {"owner", "guest", "system"}
            and item.path.split("/")[2]
            and "/" not in item.path.split("/")[2]
        ),
        None,
    )
    if identity_uri is None:
        raise ValueError("invalid SPIFFE ID")
    role, stable_id = identity_uri.path.strip("/").split("/", 1)
    if any(char.isspace() for char in stable_id):
        raise ValueError("invalid SPIFFE ID")
    spiffe = identity_uri.geturl()
    # fingerprint binding prevents token theft
    fingerprint = cert.fingerprint(cert.signature_hash_algorithm).hex()[:16]
    return Identity(
        spiffe_id=spiffe,
        role=role,
        channel=channel,
        fingerprint=fingerprint,
    )

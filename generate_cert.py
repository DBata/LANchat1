from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

# Generate private key
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Certificate details (you can change these)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "KE"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Nairobi"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Juja"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "TIE@23 LANChat"),
    x509.NameAttribute(NameOID.COMMON_NAME, "LANChat Server"),
])

# Generate certificate
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(key, hashes.SHA256())
)

# Save private key
with open("server.key", "wb") as f:
    f.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# Save certificate
with open("server.crt", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("✅ SSL certificate and key generated successfully!")

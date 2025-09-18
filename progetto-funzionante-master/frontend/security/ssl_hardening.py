"""
HTTPS and SSL/TLS Hardening Framework
Production-ready SSL/TLS configuration and certificate management
"""

import os
import ssl
import socket
import subprocess
import time
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import logging
import aiohttp
import asyncio
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import OpenSSL

logger = logging.getLogger(__name__)

class SSLProtocol(Enum):
    """Supported SSL/TLS protocols"""
    TLS_1_3 = "TLSv1.3"
    TLS_1_2 = "TLSv1.2"
    TLS_1_1 = "TLSv1.1"
    TLS_1_0 = "TLSv1.0"

class CertificateType(Enum):
    """Certificate types"""
    LETSENCRYPT = "letsencrypt"
    SELF_SIGNED = "self_signed"
    COMMERCIAL = "commercial"
    INTERNAL = "internal"

class SecurityLevel(Enum):
    """SSL/TLS security levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    HIGH = "high"
    STRICT = "strict"

@dataclass
class SSLConfiguration:
    """SSL/TLS configuration"""
    protocol: SSLProtocol = SSLProtocol.TLS_1_2
    security_level: SecurityLevel = SecurityLevel.HIGH
    certificate_type: CertificateType = CertificateType.LETSENCRYPT
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    chain_path: Optional[str] = None
    domain: str = "localhost"
    additional_domains: List[str] = field(default_factory=list)
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    ocsp_stapling: bool = True
    session_tickets: bool = True
    session_timeout: int = 300  # 5 minutes
    cipher_suites: Optional[List[str]] = None
    curve_preferences: Optional[List[str]] = None
    early_data: bool = False
    compression: bool = False
    renegotiation: bool = False

class CertificateManager:
    """SSL/TLS certificate management"""

    def __init__(self, config: SSLConfiguration):
        self.config = config
        self.certificate_info = None
        self.last_check = None

    async def get_or_create_certificate(self) -> Tuple[bool, str, Optional[str]]:
        """Get existing certificate or create new one"""
        if self.config.certificate_path and os.path.exists(self.config.certificate_path):
            # Validate existing certificate
            is_valid, message = await self.validate_certificate()
            if is_valid:
                return True, "Using existing certificate", self.config.certificate_path

        # Create new certificate
        return await self.create_certificate()

    async def create_certificate(self) -> Tuple[bool, str, Optional[str]]:
        """Create new certificate based on configuration"""
        if self.config.certificate_type == CertificateType.SELF_SIGNED:
            return await self.create_self_signed_certificate()
        elif self.config.certificate_type == CertificateType.LETSENCRYPT:
            return await self.create_letsencrypt_certificate()
        elif self.config.certificate_type == CertificateType.INTERNAL:
            return await self.create_internal_certificate()
        else:
            return False, "Unsupported certificate type", None

    async def create_self_signed_certificate(self) -> Tuple[bool, str, Optional[str]]:
        """Create self-signed certificate"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Trading System"),
                x509.NameAttribute(NameOID.COMMON_NAME, self.config.domain),
            ])

            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(self.config.domain),
                    *[x509.DNSName(domain) for domain in self.config.additional_domains]
                ]),
                critical=False
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False
                ),
                critical=True
            ).add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH
                ]),
                critical=False
            ).sign(private_key, hashes.SHA256(), default_backend())

            # Save certificate and private key
            cert_path = self.config.certificate_path or f"certs/{self.config.domain}.crt"
            key_path = self.config.private_key_path or f"certs/{self.config.domain}.key"

            # Ensure directory exists
            os.makedirs(os.path.dirname(cert_path), exist_ok=True)

            # Write certificate
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            # Write private key
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            self.config.certificate_path = cert_path
            self.config.private_key_path = key_path

            logger.info(f"Self-signed certificate created: {cert_path}")
            return True, "Self-signed certificate created", cert_path

        except Exception as e:
            logger.error(f"Failed to create self-signed certificate: {e}")
            return False, f"Failed to create certificate: {e}", None

    async def create_letsencrypt_certificate(self) -> Tuple[bool, str, Optional[str]]:
        """Create Let's Encrypt certificate using certbot"""
        try:
            # Check if certbot is available
            result = subprocess.run(["certbot", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "certbot not installed", None

            # Prepare certbot command
            domains = [self.config.domain] + self.config.additional_domains
            domain_args = []
            for domain in domains:
                domain_args.extend(["-d", domain])

            certbot_command = [
                "certbot",
                "certonly",
                "--standalone",
                "--agree-tos",
                "--email", f"admin@{self.config.domain}",
                "--non-interactive",
                "--force-renewal"
            ] + domain_args

            # Run certbot
            result = subprocess.run(certbot_command, capture_output=True, text=True)

            if result.returncode == 0:
                cert_path = f"/etc/letsencrypt/live/{self.config.domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{self.config.domain}/privkey.pem"

                self.config.certificate_path = cert_path
                self.config.private_key_path = key_path

                logger.info(f"Let's Encrypt certificate created: {cert_path}")
                return True, "Let's Encrypt certificate created", cert_path
            else:
                logger.error(f"Certbot failed: {result.stderr}")
                return False, f"Certbot failed: {result.stderr}", None

        except Exception as e:
            logger.error(f"Failed to create Let's Encrypt certificate: {e}")
            return False, f"Failed to create certificate: {e}", None

    async def create_internal_certificate(self) -> Tuple[bool, str, Optional[str]]:
        """Create internal certificate for development/testing"""
        return await self.create_self_signed_certificate()

    async def validate_certificate(self) -> Tuple[bool, str]:
        """Validate existing certificate"""
        if not self.config.certificate_path or not os.path.exists(self.config.certificate_path):
            return False, "Certificate file not found"

        try:
            with open(self.config.certificate_path, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Check expiration
            if datetime.utcnow() > cert.not_valid_after:
                return False, "Certificate has expired"

            # Check if certificate is valid for domain
            domain_valid = False
            try:
                cert.get_extension_for_class(x509.SubjectAlternativeName)
            except x509.ExtensionNotFound:
                # Check common name if no SAN
                common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                domain_valid = self._validate_domain_match(common_name, self.config.domain)
            else:
                # Check SAN
                san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
                for name in san:
                    if isinstance(name, x509.DNSName):
                        if self._validate_domain_match(name.value, self.config.domain):
                            domain_valid = True
                            break

            if not domain_valid:
                return False, "Certificate not valid for domain"

            # Store certificate info
            self.certificate_info = {
                "issuer": cert.issuer.rfc4514_string(),
                "subject": cert.subject.rfc4514_string(),
                "serial_number": cert.serial_number,
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "version": cert.version.name,
                "signature_algorithm": cert.signature_algorithm_oid._name,
                "key_size": cert.public_key().key_size
            }

            self.last_check = datetime.utcnow()
            return True, "Certificate is valid"

        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return False, f"Certificate validation failed: {e}"

    def _validate_domain_match(self, cert_domain: str, requested_domain: str) -> bool:
        """Validate if certificate domain matches requested domain"""
        # Exact match
        if cert_domain.lower() == requested_domain.lower():
            return True

        # Wildcard match
        if cert_domain.startswith("*."):
            wildcard_domain = cert_domain[2:]
            if requested_domain.lower().endswith(wildcard_domain.lower()):
                return True

        return False

    async def renew_certificate(self) -> Tuple[bool, str]:
        """Renew certificate if needed"""
        if not self.certificate_info:
            is_valid, message = await self.validate_certificate()
            if not is_valid:
                return await self.create_certificate()

        # Check if certificate expires soon (within 30 days)
        expiry_date = datetime.fromisoformat(self.certificate_info["not_valid_after"])
        if expiry_date - datetime.utcnow() < timedelta(days=30):
            logger.info("Certificate expires soon, renewing...")
            return await self.create_certificate()

        return True, "Certificate is still valid"

class SSLContextBuilder:
    """Build SSL context with security hardening"""

    def __init__(self, config: SSLConfiguration):
        self.config = config

    def build_context(self) -> ssl.SSLContext:
        """Build SSL context with security configuration"""
        # Determine SSL protocol
        if self.config.protocol == SSLProtocol.TLS_1_3:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        elif self.config.protocol == SSLProtocol.TLS_1_2:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.minimum_version = ssl.TLSVersion.TLSv1_2  # Default to TLS 1.2

        # Configure cipher suites based on security level
        self._configure_cipher_suites(context)

        # Configure curve preferences
        self._configure_curves(context)

        # Configure security options
        self._configure_security_options(context)

        # Load certificate and private key
        if self.config.certificate_path and self.config.private_key_path:
            context.load_cert_chain(
                certfile=self.config.certificate_path,
                keyfile=self.config.private_key_path
            )

        return context

    def _configure_cipher_suites(self, context: ssl.SSLContext):
        """Configure cipher suites based on security level"""
        if self.config.cipher_suites:
            # Use custom cipher suites
            context.set_ciphers(":".join(self.config.cipher_suites))
        else:
            # Use predefined cipher suites based on security level
            if self.config.security_level == SecurityLevel.STRICT:
                ciphers = (
                    "TLS_AES_256_GCM_SHA384:"
                    "TLS_AES_128_GCM_SHA256:"
                    "TLS_CHACHA20_POLY1305_SHA256"
                )
            elif self.config.security_level == SecurityLevel.HIGH:
                ciphers = (
                    "TLS_AES_256_GCM_SHA384:"
                    "TLS_AES_128_GCM_SHA256:"
                    "TLS_CHACHA20_POLY1305_SHA256:"
                    "ECDHE-ECDSA-AES256-GCM-SHA384:"
                    "ECDHE-RSA-AES256-GCM-SHA384:"
                    "ECDHE-ECDSA-AES128-GCM-SHA256:"
                    "ECDHE-RSA-AES128-GCM-SHA256"
                )
            elif self.config.security_level == SecurityLevel.INTERMEDIATE:
                ciphers = (
                    "TLS_AES_256_GCM_SHA384:"
                    "TLS_AES_128_GCM_SHA256:"
                    "TLS_CHACHA20_POLY1305_SHA256:"
                    "ECDHE-ECDSA-AES256-GCM-SHA384:"
                    "ECDHE-RSA-AES256-GCM-SHA384:"
                    "ECDHE-ECDSA-AES128-GCM-SHA256:"
                    "ECDHE-RSA-AES128-GCM-SHA256:"
                    "DHE-RSA-AES256-GCM-SHA384:"
                    "DHE-RSA-AES128-GCM-SHA256"
                )
            else:  # BASIC
                ciphers = (
                    "TLS_AES_256_GCM_SHA384:"
                    "TLS_AES_128_GCM_SHA256:"
                    "TLS_CHACHA20_POLY1305_SHA256:"
                    "ECDHE-ECDSA-AES256-GCM-SHA384:"
                    "ECDHE-RSA-AES256-GCM-SHA384:"
                    "ECDHE-ECDSA-AES128-GCM-SHA256:"
                    "ECDHE-RSA-AES128-GCM-SHA256"
                )

            context.set_ciphers(ciphers)

    def _configure_curves(self, context: ssl.SSLContext):
        """Configure elliptic curve preferences"""
        if self.config.curve_preferences:
            context.set_ecdh_curve(":".join(self.config.curve_preferences))
        else:
            # Use secure curves
            curves = "X25519:P-256:P-384:P-521"
            context.set_ecdh_curve(curves)

    def _configure_security_options(self, context: ssl.SSLContext):
        """Configure security options"""
        # Enable session resumption
        if self.config.session_tickets:
            context.session_timeout = self.config.session_timeout

        # Disable compression (CRIME attack mitigation)
        if not self.config.compression:
            context.options |= ssl.OP_NO_COMPRESSION

        # Disable renegotiation
        if not self.config.renegotiation:
            context.options |= ssl.OP_NO_RENEGOTIATION

        # Enable server name indication
        context.sni_callback = self._sni_callback

    def _sni_callback(self, ssl_socket, server_name, ssl_context):
        """Server Name Indication callback"""
        # This can be used to handle multiple domains
        pass

class HTTPSMiddleware:
    """HTTPS middleware for FastAPI"""

    def __init__(self, config: SSLConfiguration):
        self.config = config
        self.ssl_context = SSLContextBuilder(config).build_context()
        self.certificate_manager = CertificateManager(config)

    async def __call__(self, app):
        """Apply HTTPS configuration to FastAPI app"""
        # Configure HTTPS redirects
        if self.config.hsts_enabled:
            app.add_middleware(HTTPSRedirectMiddleware)

        # Add HSTS headers
        app.add_middleware(
            HSTSMiddleware,
            max_age=self.config.hsts_max_age,
            include_subdomains=self.config.hsts_include_subdomains,
            preload=self.config.hsts_preload
        )

        # Add security headers
        app.add_middleware(
            SecurityHeadersMiddleware,
            ssl_config=self.config
        )

        # Configure SSL context for the app
        app.router.lifespan_context["ssl_context"] = self.ssl_context

class HSTSMiddleware:
    """HTTP Strict Transport Security middleware"""

    def __init__(
        self,
        max_age: int = 31536000,
        include_subdomains: bool = True,
        preload: bool = True
    ):
        self.max_age = max_age
        self.include_subdomains = include_subdomains
        self.preload = preload

    async def __call__(self, app, call_next):
        """Add HSTS headers to responses"""
        response = await call_next(app)

        hsts_value = f"max-age={self.max_age}"
        if self.include_subdomains:
            hsts_value += "; includeSubDomains"
        if self.preload:
            hsts_value += "; preload"

        response.headers["Strict-Transport-Security"] = hsts_value
        return response

class SecurityHeadersMiddleware:
    """Security headers middleware"""

    def __init__(self, ssl_config: SSLConfiguration):
        self.ssl_config = ssl_config

    async def __call__(self, app, call_next):
        """Add security headers to responses"""
        response = await call_next(app)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Remove server information
        response.headers["Server"] = "SecureServer"

        return response

class SSLMonitor:
    """SSL/TLS monitoring and health checks"""

    def __init__(self, config: SSLConfiguration):
        self.config = config
        self.certificate_manager = CertificateManager(config)

    async def check_ssl_health(self) -> Dict[str, Any]:
        """Check SSL/TLS health status"""
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "ssl_enabled": True,
            "protocol": self.config.protocol.value,
            "security_level": self.config.security_level.value,
            "certificate_status": "unknown",
            "certificate_expiry": None,
            "days_until_expiry": None,
            "hsts_enabled": self.config.hsts_enabled,
            "ocsp_stapling": self.config.ocsp_stapling,
            "security_score": 0
        }

        try:
            # Check certificate
            is_valid, message = await self.certificate_manager.validate_certificate()
            health["certificate_status"] = "valid" if is_valid else "invalid"
            health["certificate_message"] = message

            if self.certificate_manager.certificate_info:
                expiry_date = datetime.fromisoformat(
                    self.certificate_manager.certificate_info["not_valid_after"]
                )
                health["certificate_expiry"] = expiry_date.isoformat()
                health["days_until_expiry"] = (expiry_date - datetime.utcnow()).days

                # Calculate security score
                score = 0
                if is_valid:
                    score += 30

                if health["days_until_expiry"] and health["days_until_expiry"] > 30:
                    score += 20

                if self.config.security_level in [SecurityLevel.HIGH, SecurityLevel.STRICT]:
                    score += 20

                if self.config.hsts_enabled:
                    score += 15

                if self.config.ocsp_stapling:
                    score += 15

                health["security_score"] = score

        except Exception as e:
            health["certificate_status"] = "error"
            health["certificate_message"] = str(e)

        return health

    async def test_ssl_connection(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Test SSL connection to remote host"""
        try:
            # Create SSL context
            context = SSLContextBuilder(self.config).build_context()

            # Connect to host
            reader, writer = await asyncio.open_connection(
                host, port,
                ssl=context
            )

            # Send HTTP request
            writer.write(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
            await writer.drain()

            # Read response
            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()

            # Parse response
            response_text = response.decode('utf-8', errors='ignore')

            return {
                "success": True,
                "host": host,
                "port": port,
                "protocol": str(context.protocol),
                "cipher": writer.get_cipher()[0] if hasattr(writer, 'get_cipher') else "unknown",
                "response_size": len(response),
                "status": "connected"
            }

        except Exception as e:
            return {
                "success": False,
                "host": host,
                "port": port,
                "error": str(e),
                "status": "failed"
            }

# Global SSL configuration functions
def create_production_ssl_config(domain: str) -> SSLConfiguration:
    """Create production SSL configuration"""
    return SSLConfiguration(
        protocol=SSLProtocol.TLS_1_2,
        security_level=SecurityLevel.HIGH,
        certificate_type=CertificateType.LETSENCRYPT,
        domain=domain,
        additional_domains=[f"www.{domain}"],
        hsts_enabled=True,
        hsts_max_age=31536000,
        hsts_include_subdomains=True,
        hsts_preload=True,
        ocsp_stapling=True,
        session_tickets=True,
        session_timeout=300,
        early_data=False,
        compression=False,
        renegotiation=False
    )

def create_staging_ssl_config(domain: str) -> SSLConfiguration:
    """Create staging SSL configuration"""
    return SSLConfiguration(
        protocol=SSLProtocol.TLS_1_2,
        security_level=SecurityLevel.INTERMEDIATE,
        certificate_type=CertificateType.SELF_SIGNED,
        domain=domain,
        additional_domains=[f"staging.{domain}"],
        hsts_enabled=True,
        hsts_max_age=86400,  # 1 day
        hsts_include_subdomains=False,
        hsts_preload=False,
        ocsp_stapling=False,
        session_tickets=True,
        session_timeout=600,
        early_data=False,
        compression=False,
        renegotiation=False
    )

def create_development_ssl_config(domain: str = "localhost") -> SSLConfiguration:
    """Create development SSL configuration"""
    return SSLConfiguration(
        protocol=SSLProtocol.TLS_1_2,
        security_level=SecurityLevel.BASIC,
        certificate_type=CertificateType.SELF_SIGNED,
        domain=domain,
        hsts_enabled=False,
        hsts_max_age=0,
        hsts_include_subdomains=False,
        hsts_preload=False,
        ocsp_stapling=False,
        session_tickets=True,
        session_timeout=1200,
        early_data=False,
        compression=False,
        renegotiation=False
    )
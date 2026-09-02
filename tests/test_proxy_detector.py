"""Tests for Reverse Proxy and Port route detection."""

from watchdog_tui.core.proxy_detector import ProxyDetector
from watchdog_tui.models import ContainerInfo, ContainerPort


def test_proxy_detector_traefik_and_ports():
    container = ContainerInfo(
        id="c1234567890abcdef",
        short_id="c1234567890a",
        name="web_service",
        image="app:latest",
        status="running",
        state="running",
        ports=[
            ContainerPort(host_ip="0.0.0.0", host_port="8080", container_port="80", protocol="tcp")
        ],
        labels={
            "traefik.http.routers.myapp.rule": "Host(`app.mydomain.com`)",
            "traefik.http.routers.myapp.tls": "true",
            "traefik.http.services.myapp.loadbalancer.server.port": "8080",
        }
    )

    routes = ProxyDetector.detect_routes([container])
    assert len(routes) == 2

    # Check Traefik route
    traefik_route = next(r for r in routes if r.service_type == "Traefik")
    assert traefik_route.rule_or_domain == "Host(`app.mydomain.com`)"
    assert traefik_route.target_port == "8080"
    assert traefik_route.tls_enabled is True

    # Check Direct Port Forward route
    port_route = next(r for r in routes if r.service_type == "Port Forward")
    assert port_route.rule_or_domain == "Host :8080"
    assert port_route.target_port == "80/tcp"


def test_proxy_detector_caddy_and_nginx():
    caddy_container = ContainerInfo(
        id="caddy123",
        short_id="caddy123",
        name="caddy_service",
        image="caddy:alpine",
        status="running",
        state="running",
        labels={
            "caddy": "site.local, api.site.local",
            "caddy.reverse_proxy": "{{upstreams 3000}}"
        }
    )

    nginx_container = ContainerInfo(
        id="nginx123",
        short_id="nginx123",
        name="vhost_service",
        image="nginx:alpine",
        status="running",
        state="running",
        labels={
            "VIRTUAL_HOST": "app.local",
            "VIRTUAL_PORT": "5000",
            "LETSENCRYPT_HOST": "app.local"
        }
    )

    routes = ProxyDetector.detect_routes([caddy_container, nginx_container])
    service_types = [r.service_type for r in routes]

    assert "Caddy" in service_types
    assert "Nginx Proxy" in service_types

    nginx_route = next(r for r in routes if r.service_type == "Nginx Proxy")
    assert nginx_route.rule_or_domain == "app.local"
    assert nginx_route.target_port == "5000"
    assert nginx_route.tls_enabled is True

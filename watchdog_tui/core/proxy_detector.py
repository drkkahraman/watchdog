"""Reverse Proxy & Port Mapping detector."""

import re

from watchdog_tui.models import ContainerInfo, ProxyRoute


class ProxyDetector:
    """Discovers reverse proxy rules and port routings from container labels and ports."""

    @staticmethod
    def detect_routes(containers: list[ContainerInfo]) -> list[ProxyRoute]:
        routes: list[ProxyRoute] = []

        for container in containers:
            # 1. Traefik labels discovery
            traefik_routes = ProxyDetector._detect_traefik(container)
            routes.extend(traefik_routes)

            # 2. Caddy labels discovery
            caddy_routes = ProxyDetector._detect_caddy(container)
            routes.extend(caddy_routes)

            # 3. Nginx / VIRTUAL_HOST discovery
            nginx_routes = ProxyDetector._detect_nginx_proxy(container)
            routes.extend(nginx_routes)

            # 4. Standard Port Mappings (Host IP:Port -> Container Port)
            for port in container.ports:
                if port.host_port:
                    routes.append(
                        ProxyRoute(
                            container_name=container.name,
                            container_id=container.short_id,
                            service_type="Port Forward",
                            rule_or_domain=f"Host :{port.host_port}",
                            target_port=f"{port.container_port}/{port.protocol}",
                            entrypoint_or_host=port.host_ip or "0.0.0.0",
                            tls_enabled=port.host_port in ("443", "8443"),
                            details=f"Direct binding on {port.host_ip}:{port.host_port}"
                        )
                    )

        return routes

    @staticmethod
    def _detect_traefik(container: ContainerInfo) -> list[ProxyRoute]:
        routes = []
        labels = container.labels

        # Find router rules: traefik.http.routers.<router_name>.rule
        router_regex = re.compile(r"^traefik\.http\.routers\.([a-zA-Z0-9_-]+)\.rule$")
        for key, value in labels.items():
            match = router_regex.match(key)
            if match:
                router_name = match.group(1)
                tls_key = f"traefik.http.routers.{router_name}.tls"
                tls_cert_key = f"traefik.http.routers.{router_name}.tls.certresolver"
                tls_enabled = (
                    labels.get(tls_key, "").lower() == "true"
                    or tls_cert_key in labels
                )

                # Find entrypoints
                entrypoints = labels.get(
                    f"traefik.http.routers.{router_name}.entrypoints", "web/websecure"
                )

                # Find target service port
                service_port = labels.get(
                    f"traefik.http.services.{router_name}.loadbalancer.server.port",
                    labels.get("traefik.http.services.loadbalancer.server.port", "Auto")
                )

                routes.append(
                    ProxyRoute(
                        container_name=container.name,
                        container_id=container.short_id,
                        service_type="Traefik",
                        rule_or_domain=value,
                        target_port=str(service_port),
                        entrypoint_or_host=entrypoints,
                        tls_enabled=tls_enabled,
                        details=f"Router: {router_name}"
                    )
                )

        return routes

    @staticmethod
    def _detect_caddy(container: ContainerInfo) -> list[ProxyRoute]:
        routes = []
        labels = container.labels

        for key, value in labels.items():
            if key == "caddy" or key.startswith("caddy_"):
                domains = value.split(",")
                for domain in domains:
                    domain = domain.strip()
                    if domain:
                        routes.append(
                            ProxyRoute(
                                container_name=container.name,
                                container_id=container.short_id,
                                service_type="Caddy",
                                rule_or_domain=domain,
                                target_port=labels.get(f"{key}.reverse_proxy", "Auto"),
                                entrypoint_or_host="http/https",
                                tls_enabled=not domain.startswith("http://"),
                                details="Caddy label config"
                            )
                        )

        return routes

    @staticmethod
    def _detect_nginx_proxy(container: ContainerInfo) -> list[ProxyRoute]:
        routes = []
        labels = container.labels
        raw = container.raw_data or {}
        env_vars = {}

        # Extract environment variables from raw config
        config = raw.get("Config", {})
        env_list = config.get("Env", [])
        for item in env_list:
            if "=" in item:
                k, v = item.split("=", 1)
                env_vars[k] = v

        # Check VIRTUAL_HOST
        vhost = labels.get("VIRTUAL_HOST") or env_vars.get("VIRTUAL_HOST")
        if vhost:
            vport = labels.get("VIRTUAL_PORT") or env_vars.get("VIRTUAL_PORT", "80")
            letsencrypt = labels.get("LETSENCRYPT_HOST") or env_vars.get("LETSENCRYPT_HOST")
            routes.append(
                ProxyRoute(
                    container_name=container.name,
                    container_id=container.short_id,
                    service_type="Nginx Proxy",
                    rule_or_domain=vhost,
                    target_port=str(vport),
                    entrypoint_or_host="80/443",
                    tls_enabled=bool(letsencrypt),
                    details=f"LE Host: {letsencrypt}" if letsencrypt else "HTTP"
                )
            )

        return routes

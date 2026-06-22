"""Security assessment for discovered devices."""

from __future__ import annotations

from dataclasses import dataclass, field

from network_inventory.inventory.device import Device


@dataclass(slots=True)
class SecurityAssessment:
    """Security score and remediation guidance."""

    score: int
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def assess_device(device: Device) -> SecurityAssessment:
    """Assess common network exposure risks for a device."""
    score = 100
    findings: list[str] = []
    recommendations: list[str] = []
    ports = set(device.open_ports)

    if 23 in ports:
        score -= 20
        findings.append("Telnet aperto")
        recommendations.append(
            "Disabilitare Telnet e usare SSH con credenziali robuste."
        )
    if 21 in ports:
        score -= 12
        findings.append("FTP aperto")
        recommendations.append("Verificare accesso anonimo e preferire SFTP/FTPS.")
    if 161 in ports:
        score -= 10
        findings.append("SNMP esposto")
        recommendations.append("Usare SNMPv3 o community non predefinite e ACL.")
    if 80 in ports and 443 not in ports:
        score -= 8
        findings.append("HTTP senza HTTPS rilevato")
        recommendations.append(
            "Abilitare HTTPS o limitare l'interfaccia HTTP alla rete di gestione."
        )
    if 3389 in ports:
        score -= 15
        findings.append("RDP esposto")
        recommendations.append("Limitare RDP con firewall/VPN e abilitare NLA.")
    if 445 in ports:
        score -= 8
        findings.append("SMB esposto")
        recommendations.append("Verificare SMBv1, patch e segmentazione della rete.")
    if device.snmp_info.get("community") in {"public", "private"}:
        score -= 20
        findings.append("Community SNMP predefinita")
        recommendations.append("Rimuovere community public/private o migrare a SNMPv3.")

    return SecurityAssessment(max(score, 0), findings, recommendations)

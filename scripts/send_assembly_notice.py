from __future__ import annotations

import argparse
import csv
import json
import os
import re
import smtplib
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = Path(r"O:\agua\data\Llamado a Asamblea.pdf")
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs" / "assembly_notice"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Recipient:
    idcliente: int | None
    nombre: str
    email: str


@dataclass(frozen=True)
class SkippedRecipient:
    idcliente: int | None
    nombre: str
    email: str
    reason: str


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def clean_text(value: Any) -> str:
    return str(value or "").replace("\x00", "").strip()


def is_active(value: Any) -> bool:
    if isinstance(value, (bytes, bytearray)):
        value = int.from_bytes(value, byteorder="big")
    return str(value).strip().lower() not in {"0", "false", "n", "no", "inactivo", "baja", ""}


def normalize_email(value: Any) -> str:
    return clean_text(value).lower()


def require_env(keys: list[str]) -> None:
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise RuntimeError("Faltan variables en .env: " + ", ".join(missing))


def connect_coop() -> pymysql.connections.Connection:
    require_env(["COOP_MYSQL_HOST", "COOP_MYSQL_DATABASE", "COOP_MYSQL_USER", "COOP_MYSQL_PASSWORD"])
    ssl_mode = os.getenv("COOP_MYSQL_SSL_MODE", "preferred").lower()
    ssl: dict[str, Any] | None = None if ssl_mode in {"disabled", "disable", "false", "0", "none"} else {"check_hostname": False}
    return pymysql.connect(
        host=os.environ["COOP_MYSQL_HOST"],
        port=int(os.getenv("COOP_MYSQL_PORT", "3306")),
        user=os.environ["COOP_MYSQL_USER"],
        password=os.environ["COOP_MYSQL_PASSWORD"],
        database=os.environ["COOP_MYSQL_DATABASE"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl,
        connect_timeout=5,
        read_timeout=30,
        write_timeout=30,
    )


def fetch_recipients(active_only: bool) -> tuple[list[Recipient], list[SkippedRecipient]]:
    recipients: list[Recipient] = []
    skipped: list[SkippedRecipient] = []
    seen: set[str] = set()

    with connect_coop() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT idcliente, nombre, email, activo
                FROM clientes
                WHERE email IS NOT NULL AND TRIM(email) <> ''
                ORDER BY idcliente
                """
            )
            rows = list(cur.fetchall())

    for row in rows:
        idcliente = row.get("idcliente")
        nombre = clean_text(row.get("nombre"))
        email = normalize_email(row.get("email"))
        if active_only and not is_active(row.get("activo")):
            skipped.append(SkippedRecipient(idcliente, nombre, email, "cliente_inactivo"))
            continue
        if not EMAIL_RE.match(email):
            skipped.append(SkippedRecipient(idcliente, nombre, email, "email_invalido"))
            continue
        if email in seen:
            skipped.append(SkippedRecipient(idcliente, nombre, email, "email_duplicado"))
            continue
        seen.add(email)
        recipients.append(Recipient(idcliente, nombre, email))

    return recipients, skipped


def build_message(recipient: Recipient, subject: str, body: str, pdf_path: Path) -> EmailMessage:
    sender_email = os.getenv("SMTP_FROM_EMAIL", "info@vogelconsultoria.com.ar")
    sender_name = os.getenv("SMTP_FROM_NAME", "Vogel Consultoria")
    reply_to = os.getenv("SMTP_REPLY_TO", sender_email)

    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = formataddr((recipient.nombre, recipient.email))
    msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1])
    msg.set_content(body)

    payload = pdf_path.read_bytes()
    msg.add_attachment(payload, maintype="application", subtype="pdf", filename=pdf_path.name)
    return msg


def smtp_client() -> smtplib.SMTP:
    require_env(["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"])
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    timeout = int(os.getenv("SMTP_TIMEOUT", "30"))
    use_ssl = env_bool("SMTP_SSL", False)
    use_starttls = env_bool("SMTP_STARTTLS", not use_ssl)

    client: smtplib.SMTP
    if use_ssl:
        client = smtplib.SMTP_SSL(host, port, timeout=timeout)
    else:
        client = smtplib.SMTP(host, port, timeout=timeout)
        if use_starttls:
            client.starttls()
    client.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    return client


def is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "limite" in text or "limit" in text or "rate" in text


def write_csv(path: Path, rows: list[Recipient] | list[SkippedRecipient]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else ["idcliente", "nombre", "email"]
    if rows and isinstance(rows[0], SkippedRecipient):
        fieldnames = ["idcliente", "nombre", "email", "reason"]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def append_attempt(path: Path, recipient: Recipient, status: str, error: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "idcliente", "nombre", "email", "status", "error"])
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "idcliente": recipient.idcliente,
                "nombre": recipient.nombre,
                "email": recipient.email,
                "status": status,
                "error": error,
            }
        )


def write_report(log_dir: Path, report: dict[str, Any], recipients: list[Recipient], skipped: list[SkippedRecipient]) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = log_dir / f"assembly-notice-{stamp}.json"
    recipients_path = log_dir / f"assembly-notice-recipients-{stamp}.csv"
    skipped_path = log_dir / f"assembly-notice-skipped-{stamp}.csv"
    report["recipients_csv"] = str(recipients_path)
    report["skipped_csv"] = str(skipped_path)
    write_csv(recipients_path, recipients)
    write_csv(skipped_path, skipped)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return report_path


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    parser = argparse.ArgumentParser(description="Enviar llamado a asamblea a socios con email cargado.")
    parser.add_argument("--send", action="store_true", help="Envia correos reales. Sin esta bandera solo previsualiza.")
    parser.add_argument("--include-inactive", action="store_true", help="Incluye clientes inactivos si tienen email valido.")
    parser.add_argument("--limit", type=int, default=None, help="Limita la cantidad de destinatarios para prueba.")
    parser.add_argument("--offset", type=int, default=0, help="Salta los primeros N destinatarios validos para continuar otro lote.")
    parser.add_argument(
        "--max-per-run",
        type=int,
        default=int(os.getenv("SMTP_HOURLY_LIMIT", "100")),
        help="Cantidad maxima a enviar/previsualizar en esta corrida. Por defecto respeta SMTP_HOURLY_LIMIT o 200.",
    )
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="PDF a adjuntar.")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR, help="Carpeta de logs.")
    parser.add_argument("--subject", default="Llamado a Asamblea", help="Asunto del correo.")
    parser.add_argument(
        "--body",
        default=(
            "Estimado/a socio/a:\n\n"
            "Adjuntamos el llamado a asamblea correspondiente.\n\n"
            "Saludos cordiales.\n"
        ),
        help="Cuerpo del correo en texto plano.",
    )
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el PDF a adjuntar: {pdf_path}")

    recipients, skipped = fetch_recipients(active_only=not args.include_inactive)
    total_valid_recipients = len(recipients)
    if args.offset < 0:
        raise ValueError("--offset no puede ser negativo")
    recipients = recipients[args.offset :]
    if args.limit is not None:
        recipients = recipients[: args.limit]
    if args.max_per_run is not None:
        if args.max_per_run <= 0:
            raise ValueError("--max-per-run debe ser mayor a cero")
        recipients = recipients[: args.max_per_run]

    report: dict[str, Any] = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "send" if args.send else "dry_run",
        "source_database": os.getenv("COOP_MYSQL_DATABASE"),
        "pdf": str(pdf_path),
        "subject": args.subject,
        "from": os.getenv("SMTP_FROM_EMAIL", "info@vogelconsultoria.com.ar"),
        "total_valid_recipients": total_valid_recipients,
        "offset": args.offset,
        "max_per_run": args.max_per_run,
        "batch_recipients": len(recipients),
        "remaining_after_batch": max(total_valid_recipients - args.offset - len(recipients), 0),
        "total_skipped": len(skipped),
        "sent": 0,
        "errors": [],
    }
    attempts_path = args.log_dir / f"assembly-notice-attempts-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    report["attempts_csv"] = str(attempts_path)

    if args.send:
        with smtp_client() as smtp:
            for recipient in recipients:
                try:
                    smtp.send_message(build_message(recipient, args.subject, args.body, pdf_path))
                    report["sent"] += 1
                    append_attempt(attempts_path, recipient, "sent")
                except Exception as exc:  # Keep going and log per-recipient failures.
                    error = str(exc)
                    append_attempt(attempts_path, recipient, "error", error)
                    report["errors"].append({"idcliente": recipient.idcliente, "email": recipient.email, "error": error})
                    if is_rate_limit_error(exc):
                        report["stopped_reason"] = "smtp_rate_limit"
                        break

    report["finished_at"] = datetime.now().isoformat(timespec="seconds")
    report_path = write_report(args.log_dir, report, recipients, skipped)
    print(json.dumps({"report": str(report_path), **report}, indent=2, ensure_ascii=False))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

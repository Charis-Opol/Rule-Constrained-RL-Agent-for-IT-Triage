"""Tuition payments through the bank gateway."""
from portal import http

GATEWAY = "https://bank-gateway.example/pay"
GATEWAY_TIMEOUT_SECONDS = 10


class PaymentUnavailable(Exception):
    pass


def pay_tuition(student_id, amount):
    try:
        return http.post(GATEWAY, {"student": student_id, "amount": amount}, timeout=GATEWAY_TIMEOUT_SECONDS)
    except http.Timeout as error:
        raise PaymentUnavailable("The bank gateway did not answer in time; try again later") from error

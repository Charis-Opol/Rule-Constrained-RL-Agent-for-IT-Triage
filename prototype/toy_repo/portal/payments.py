"""Tuition payments through the bank gateway."""
from portal import http

GATEWAY = "https://bank-gateway.example/pay"


class PaymentUnavailable(Exception):
    pass


def pay_tuition(student_id, amount):
    return http.post(GATEWAY, {"student": student_id, "amount": amount})

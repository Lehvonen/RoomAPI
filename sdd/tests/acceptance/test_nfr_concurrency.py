"""NFR-005 / SC-002: simultaneous requests for one free slot create exactly one booking."""

import threading

from ..conftest import book, helsinki, register_and_login

REQUESTS = 20


def test_twenty_simultaneous_requests_create_exactly_one_booking(client, room):
    users = [register_and_login(client) for _ in range(REQUESTS)]
    start, end = helsinki(3, 10), helsinki(3, 11)
    barrier = threading.Barrier(REQUESTS)
    codes: list[int] = []
    lock = threading.Lock()

    def attempt(headers):
        barrier.wait()  # release all requests at the same moment
        status = book(client, headers, room["id"], start, end).status_code
        with lock:
            codes.append(status)

    threads = [threading.Thread(target=attempt, args=(h,)) for h in users]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert len(codes) == REQUESTS
    assert codes.count(201) == 1, codes
    assert codes.count(409) == REQUESTS - 1, codes

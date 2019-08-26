import krpc
import time
from kRPC_Automation.log_setup import logger
import operator

def log_and_print(message):
    logger.info(message)
    print(message)

expression_shorthand = {
    "<" : operator.lt,
    "<=": operator.le,
    ">" : operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
    "+" : operator.add,
    "-" : operator.sub,
    "*" : operator.mul,
    "/" : operator.truediv,
    "%" : operator.mod,
    "^" : operator.pow,
}


def stream_value(conn, obj, attr):

    func = conn.add_stream(getattr, obj, attr)
    return func

def wait_for(stream, expr_symbol, value_waiting_for, changing_value=False, factor=1):

    eval_func = expression_shorthand[expr_symbol]
    count = 0
    if changing_value:
        target_value = factor * value_waiting_for()
    else:
        target_value = factor * value_waiting_for

    while eval_func(stream(), target_value) is not True:
        if changing_value:
            count += 1
            time.sleep(.25)
            target_value = factor * value_waiting_for()
            log_and_print(f"Waiting for value: {target_value}")

    return True


if __name__ == "__main__":
    conn = krpc.connect(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001)
    vessel = conn.space_center.active_vessel
    flight_info = vessel.flight()

    surf_alt_stream = stream_value(conn, vessel.flight(), 'surface_altitude')
    mean_alt_stream = stream_value(conn, vessel.flight(), 'mean_altitude')

    while True:
        print(f"Surface Alt (m): {'{:.2f}'.format(surf_alt_stream())};    Mean Alt (m): {'{:.2f}'.format(mean_alt_stream())}")
        time.sleep(2)

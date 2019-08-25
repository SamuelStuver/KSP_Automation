import krpc
import time

def stream_value(conn, obj, value):

    func = conn.add_stream(getattr, obj, value)
    return func

if __name__ == "__main__":
    conn = krpc.connect(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001)
    vessel = conn.space_center.active_vessel
    flight_info = vessel.flight()

    surf_alt_stream = stream_value(conn, vessel.flight(), 'surface_altitude')
    mean_alt_stream = stream_value(conn, vessel.flight(), 'mean_altitude')

    while True:
        print(f"Surface Alt (m): {'{:.2f}'.format(surf_alt_stream())};    Mean Alt (m): {'{:.2f}'.format(mean_alt_stream())}")
        time.sleep(2)

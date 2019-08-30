import krpc
import time
import math
from kRPC_Automation.log_setup import logger
import operator

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

def log_and_print(message):
    logger.info(message)
    print(message)

def is_part_engine(part):
    for m in part.modules:
        if m.name == "ModuleEngines":
                return True
    return False

class Stage:
    def __init__(self, decouple_stage_number, conn, vessel):
        self.decouple_stage = decouple_stage_number
        self.parts = vessel.parts.in_decouple_stage(self.decouple_stage)
        self.engines = []
        for p in self.parts:
            if is_part_engine(p):
                self.engines.append(p.engine)

    def has_fuel(self):
        for eng in self.engines:
            if eng.has_fuel:
                return True

        return False

    def wait_for_no_fuel(self):
        while self.has_fuel():
            time.sleep(.25)
        return True



class MissionData:
    def __init__(self, conn, vessel):
        self.conn = conn
        self.vessel = vessel
        self.stages = []
        self.stage_has_fuel = []
        # Universal Time
        self.ut = conn.add_stream(getattr, conn.space_center, 'ut')

        # Flight Data
        self.surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
        self.mean_altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
        self.latitude = conn.add_stream(getattr, vessel.flight(), 'latitude')
        self.longitude = conn.add_stream(getattr, vessel.flight(), 'longitude')
        self.velocity = conn.add_stream(getattr, vessel.flight(), 'velocity')
        self.direction = conn.add_stream(getattr, vessel.flight(), 'direction')
        self.prograde = conn.add_stream(getattr, vessel.flight(), 'prograde')
        self.retrograde = conn.add_stream(getattr, vessel.flight(), 'retrograde')

        # Orbit Data
        self.apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
        self.periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
        self.semi_major_axis = conn.add_stream(getattr, vessel.orbit, 'semi_major_axis')
        self.orbital_speed = conn.add_stream(getattr, vessel.orbit, 'orbital_speed')
        self.orbital_period = conn.add_stream(getattr, vessel.orbit, 'period')
        self.time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
        self.time_to_periapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_periapsis')

        self.n_stages = self.vessel.control.current_stage

        for s in range(self.n_stages):
            stage = Stage(s, self.conn, self.vessel)
            self.stages.append(stage)

        self.current_stage_number = self.vessel.control.current_stage - 1
        self.current_stage = self.stages[self.current_stage_number]

        # Resource Data
        self.fuel_amount = {}
        self.fuel_amount['LiquidFuel'] = conn.add_stream(vessel.resources.amount, 'LiquidFuel')
        self.fuel_amount['SolidFuel'] = conn.add_stream(vessel.resources.amount, 'SolidFuel')


    def wait_for(self, stream_name, expr_symbol, value_waiting_for, changing_value=False, factor=1):
        try:
            stream = getattr(self, stream_name)
        except:
            log_and_print(f"{stream_name} data stream not available")
            return False
        eval_func = expression_shorthand[expr_symbol]
        count = 0
        if changing_value:
            target_value = factor * value_waiting_for()
        else:
            target_value = factor * value_waiting_for

        prev_value = target_value
        time_to_sleep = 1
        log_and_print(f"Waiting for {stream_name} {expr_symbol} {target_value} (changing: {changing_value}) (currently: {stream()})")
        while eval_func(stream(), target_value) is not True:
            if changing_value:
                log_and_print(f"Waiting for {stream_name} {expr_symbol} {target_value} (changing: {changing_value}) (currently: {stream()})")
                count += 1
                log_and_print(f"sleep for {time_to_sleep} second(s) and see change")
                time.sleep(time_to_sleep)
                target_value = factor * value_waiting_for()
                if count == 1:
                    time_to_sleep = .1 * math.fabs((target_value-stream()) / (target_value - prev_value))
                    log_and_print(f"set sleep interval to {time_to_sleep} seconds")

        return True

    def activate_stage(self):
        self.vessel.control.activate_next_stage()
        self.current_stage_number -= 1
        self.current_stage = self.stages[self.current_stage_number]



if __name__ == "__main__":
    pass
